"""Migration Étape 2 Task 5 : config du COMPTE DE RÉSULTAT par category_id.

Ce script migre la configuration du compte de résultat depuis les labels
`level_1_values` (JSON) vers la table de liaison
`compte_resultat_mapping_categories(mapping_id, category_id)` — qui devient la
source de LECTURE du calcul CR. Il ajoute aussi la colonne
`compte_resultat_mappings.line_code` (String(30), nullable) et y pose
`AMORT`/`COUT_FINANCEMENT` si des lignes de config portent exactement les noms
des 2 lignes calculées (aujourd'hui elles n'existent PAS en config : la colonne
reste NULL partout et le service garde ses injections).

⚠️ La colonne `level_1_values` reste en place (lecture legacy jusqu'au commit
de cette tâche, puis lettre morte) — sa suppression est prévue en Task 8.

Résolution des labels (cf. category_service.resolve_categories_for_labels) :
  1. par label seul s'il est unique dans le référentiel ;
  2. sinon désambiguïsation via le combo (level_2, level_3) réellement utilisé
     dans `enriched_transactions` de la propriété du mapping ;
  3. sinon → non résolu. Si AU MOINS un label reste non résolu, le script
     ABORTE (rollback) et liste les cas — jamais de migration partielle.

Idempotent : les liaisons déjà présentes (mapping_id, category_id) sont
préservées ; seules les manquantes sont insérées.

Usage:
    python3 backend/database/migrations/migrate_cr_config_to_ids.py          # demande confirmation
    python3 backend/database/migrations/migrate_cr_config_to_ids.py --yes    # sans confirmation
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
    CompteResultatMapping,
    CompteResultatMappingCategory,
)
from backend.api.services.category_service import resolve_categories_for_labels

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lmnp.db'))
BACKUPS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backups'))

# Noms français des 2 lignes calculées (voir compte_resultat_service).
LINE_CODE_BY_NAME = {
    "Charges d'amortissements": "AMORT",
    "Coût du financement (hors remboursement du capital)": "COUT_FINANCEMENT",
}


def backup_database() -> str:
    """Copie la base de production dans backups/ avec un nom horodaté."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Base de production introuvable: {DB_PATH}")
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%F_%H%M%S")
    dest = os.path.join(BACKUPS_DIR, f"lmnp_{stamp}_avant-cr-config-ids.db")
    shutil.copy2(DB_PATH, dest)
    return dest


def column_exists(conn, table: str, column: str) -> bool:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return any(row[1] == column for row in rows)


def apply_ddl(conn) -> bool:
    """Crée la table de liaison (create_all) et la colonne line_code si absente.
    Retourne True si line_code a été créée par cet appel."""
    # Table de liaison (idempotent : create_all ignore les tables existantes).
    Base.metadata.create_all(bind=conn, tables=[
        CompteResultatMappingCategory.__table__
    ])
    created = False
    if not column_exists(conn, "compte_resultat_mappings", "line_code"):
        conn.execute(text(
            "ALTER TABLE compte_resultat_mappings ADD COLUMN line_code VARCHAR(30)"
        ))
        created = True
    return created


def _migrate(db):
    """Construit la liaison depuis level_1_values pour tous les mappings et pose
    les line_code. Retourne (stats, unresolved_details).

    stats = {"mappings", "links_created", "links_existing", "line_codes_set"}
    unresolved_details = liste de (mapping_id, property_id, label).
    """
    stats = {"mappings": 0, "links_created": 0, "links_existing": 0, "line_codes_set": 0}
    unresolved_details = []

    mappings = db.query(CompteResultatMapping).all()
    for mapping in mappings:
        stats["mappings"] += 1

        # line_code : posé uniquement si une ligne de config porte un des 2 noms
        # spéciaux (cas non observé aujourd'hui — laissé NULL sinon).
        code = LINE_CODE_BY_NAME.get(mapping.category_name)
        if code and mapping.line_code != code:
            mapping.line_code = code
            stats["line_codes_set"] += 1

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
                    CompteResultatMappingCategory(category_id=cat_id)
                )
                stats["links_created"] += 1

    db.flush()
    return stats, unresolved_details


def main() -> int:
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    if '--yes' not in sys.argv:
        print(
            "\n⚠️  Ce script va effectuer un backup puis migrer la config du "
            "compte de résultat (liaison category_id + colonne line_code) sur la "
            "base de PRODUCTION."
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
        "🗄️  Table compte_resultat_mapping_categories prête + colonne line_code "
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
    print(f"   - liaisons créées   : {stats['links_created']}")
    print(f"   - liaisons déjà là  : {stats['links_existing']}")
    print(f"   - line_codes posés  : {stats['line_codes_set']}")
    print("\n✅ Migration terminée : config CR migrée vers category_id (0 label non résolu).")
    return 0


if __name__ == "__main__":
    print("=" * 60)
    print("MIGRATION CONFIG COMPTE DE RÉSULTAT -> category_id + line_code")
    print("=" * 60)
    sys.exit(main())
