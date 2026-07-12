"""Migration Étape 2 Task 6 : config du BILAN par category_id + line codes.

Ce script migre la configuration du bilan depuis les labels `level_1_values`
(JSON) vers la table de liaison `bilan_mapping_categories(mapping_id,
category_id)` — qui devient la source de LECTURE du calcul des lignes normales
du bilan. Il ajoute aussi la colonne `bilan_mappings.line_code` (String(30),
nullable) et y pose les codes stables des lignes SPÉCIALES, dérivés de
`special_source` :
    amortizations | amortization_result → AMORT_CUMULES
    transactions                        → COMPTE_BANCAIRE
    compte_resultat                     → RESULTAT_EXERCICE
    compte_resultat_cumul               → REPORT_A_NOUVEAU
    loan_payments                       → CAPITAL_RESTANT_DU

⚠️ Les colonnes `level_1_values` et `special_source` restent en place (lecture
legacy/fallback jusqu'au commit de cette tâche, puis lettre morte) — leur
suppression est prévue en Task 8.

Résolution des labels (cf. category_service.resolve_categories_for_labels) :
  1. par label seul s'il est unique dans le référentiel ;
  2. sinon désambiguïsation via le combo (level_2, level_3) réellement utilisé
     dans `enriched_transactions` de la propriété du mapping ;
  3. sinon → non résolu. Si AU MOINS un label reste non résolu, le script
     ABORTE (rollback) et liste les cas — jamais de migration partielle.

Les lignes normales sans level_1_values (NULL ou []) donnent simplement 0
liaison — c'est légitime (ex. lignes vides configurées mais non alimentées).

Idempotent : les liaisons déjà présentes (mapping_id, category_id) sont
préservées ; seules les manquantes sont insérées. Les line_code déjà posés ne
sont pas réécrits.

Usage:
    python3 backend/database/migrations/migrate_bilan_config_to_ids.py          # demande confirmation
    python3 backend/database/migrations/migrate_bilan_config_to_ids.py --yes    # sans confirmation
"""

import json
import os
import shutil
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from backend.database.connection import engine
from backend.database.models import (
    Base,
    BilanMapping,
    BilanMappingCategory,
)
from backend.api.services.category_service import resolve_categories_for_labels
from backend.api.services.bilan_service import LINE_CODE_BY_SPECIAL_SOURCE

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lmnp.db'))
BACKUPS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backups'))


def backup_database() -> str:
    """Copie la base de production dans backups/ avec un nom horodaté."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Base de production introuvable: {DB_PATH}")
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%F_%H%M%S")
    dest = os.path.join(BACKUPS_DIR, f"lmnp_{stamp}_avant-bilan-config-ids.db")
    shutil.copy2(DB_PATH, dest)
    return dest


def column_exists(conn, table: str, column: str) -> bool:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return any(row[1] == column for row in rows)


def apply_ddl(conn) -> bool:
    """Crée la table de liaison (create_all) et la colonne line_code si absente.
    Retourne True si line_code a été créée par cet appel."""
    Base.metadata.create_all(bind=conn, tables=[BilanMappingCategory.__table__])
    created = False
    if not column_exists(conn, "bilan_mappings", "line_code"):
        conn.execute(text(
            "ALTER TABLE bilan_mappings ADD COLUMN line_code VARCHAR(30)"
        ))
        created = True
    return created


def _migrate(db):
    """Construit la liaison depuis level_1_values pour les lignes normales et
    pose les line_code des lignes spéciales. Retourne (stats, unresolved_details).

    stats = {"mappings", "specials", "links_created", "links_existing", "line_codes_set"}
    unresolved_details = liste de (mapping_id, property_id, label).
    """
    stats = {
        "mappings": 0,
        "specials": 0,
        "links_created": 0,
        "links_existing": 0,
        "line_codes_set": 0,
    }
    unresolved_details = []

    mappings = db.query(BilanMapping).all()
    for mapping in mappings:
        stats["mappings"] += 1

        if mapping.is_special:
            stats["specials"] += 1
            # line_code des lignes spéciales : dérivé de special_source.
            code = LINE_CODE_BY_SPECIAL_SOURCE.get(mapping.special_source)
            if code and mapping.line_code != code:
                mapping.line_code = code
                stats["line_codes_set"] += 1
            # Les lignes spéciales n'ont pas de level_1_values -> pas de liaison.
            continue

        # Ligne normale : liaison depuis level_1_values.
        try:
            labels = json.loads(mapping.level_1_values) if mapping.level_1_values else []
        except (json.JSONDecodeError, TypeError):
            labels = []

        category_ids, unresolved = resolve_categories_for_labels(
            db, labels, mapping.property_id
        )
        for label in unresolved:
            unresolved_details.append((mapping.id, mapping.property_id, label))

        existing_ids = {link.category_id for link in mapping.category_links}
        for cat_id in category_ids:
            if cat_id in existing_ids:
                stats["links_existing"] += 1
            else:
                mapping.category_links.append(
                    BilanMappingCategory(category_id=cat_id)
                )
                stats["links_created"] += 1

    db.flush()
    return stats, unresolved_details


def main() -> int:
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    if '--yes' not in sys.argv:
        print(
            "\n⚠️  Ce script va effectuer un backup puis migrer la config du "
            "bilan (liaison category_id + colonne line_code) sur la base de "
            "PRODUCTION."
        )
        response = input("Continuer ? (oui/non): ")
        if response.lower() not in ('oui', 'o', 'yes', 'y'):
            print("❌ Opération annulée")
            return 1
    else:
        print("\n⚠️  Exécution (--yes activé)")

    backup_path = backup_database()
    print(f"\n💾 Backup réalisé : {backup_path}")

    with engine.begin() as conn:
        created = apply_ddl(conn)
    print(
        "🗄️  Table bilan_mapping_categories prête + colonne line_code "
        + ("créée." if created else "déjà présente (rien fait).")
    )

    session = Session()
    try:
        stats, unresolved_details = _migrate(session)
        if unresolved_details:
            session.rollback()
            print(
                f"\n❌ {len(unresolved_details)} label(s) non résolu(s) — ABORT (rollback) :",
                file=sys.stderr,
            )
            for mapping_id, property_id, label in unresolved_details:
                print(
                    f"   - mapping_id={mapping_id} (property {property_id}) : {label!r}",
                    file=sys.stderr,
                )
            return 3
        session.commit()
    except Exception:
        session.rollback()
        print(
            f"❌ Échec de la migration. Restaurer depuis le backup si besoin : {backup_path}",
            file=sys.stderr,
        )
        raise
    finally:
        session.close()

    print("\n📊 Rapport de migration :")
    print(f"   - mappings traités  : {stats['mappings']}")
    print(f"   - lignes spéciales  : {stats['specials']}")
    print(f"   - liaisons créées   : {stats['links_created']}")
    print(f"   - liaisons déjà là  : {stats['links_existing']}")
    print(f"   - line_codes posés  : {stats['line_codes_set']}")
    print("\n✅ Migration terminée : config bilan migrée vers category_id (0 label non résolu).")
    return 0


if __name__ == "__main__":
    print("=" * 60)
    print("MIGRATION CONFIG BILAN -> category_id + line_code")
    print("=" * 60)
    sys.exit(main())
