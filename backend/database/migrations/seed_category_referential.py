"""
Migration Étape 2 Task 2 : seed du référentiel global `category_groups` /
`categories` depuis les combos `(level_1, level_2, level_3)` hardcodées de
`allowed_mappings`.

Contexte : `allowed_mappings` contient 168 lignes = 56 combos identiques
(level_1, level_2, level_3) × 3 propriétés, 100% `is_hardcoded=1`. Ce script
déduplique ces 56 combos et les transpose en un référentiel GLOBAL
(sans property_id) : `CategoryGroup` (ex-level_2, avec `nature` = ex-level_3
traduit via `NATURE_BY_LABEL`) et `Category` (ex-level_1, rattachée à son
groupe). Additif : aucune table existante n'est modifiée.

Garde-fous avant toute écriture :
- chaque `level_3` doit être dans les 5 valeurs légales (Produits, Charges
  Déductibles, Emprunt, Actif, Passif) ;
- aucun `level_2` ne doit apparaître avec deux `level_3` différents parmi les
  56 combos (sinon `CategoryGroup.label` ne pourrait pas être UNIQUE) — abort
  explicite si détecté, sans forcer.

Idempotent : les groupes/catégories déjà présents (même label / même
(label, group)) ne sont pas recréés — le script peut être relancé sans
dupliquer.

⚠️ Ce script MODIFIE la base de production (backend/database/lmnp.db). Un
backup horodaté est réalisé AUTOMATIQUEMENT avant toute écriture, dans
backups/.

Usage:
    python3 backend/database/migrations/seed_category_referential.py          # demande confirmation
    python3 backend/database/migrations/seed_category_referential.py --yes    # sans confirmation
"""

import os
import shutil
import sys
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from backend.database.connection import engine
from backend.database.models import Base, CategoryGroup, Category
from backend.api.services.category_service import NATURE_BY_LABEL, resolve_category

ALLOWED_LEVEL_3_VALUES = set(NATURE_BY_LABEL.keys())

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lmnp.db'))
BACKUPS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backups'))


def backup_database() -> str:
    """Copie la base de production dans backups/ avec un nom horodaté."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Base de production introuvable: {DB_PATH}")
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%F_%H%M%S")
    dest = os.path.join(BACKUPS_DIR, f"lmnp_{stamp}_avant-seed-categories.db")
    shutil.copy2(DB_PATH, dest)
    return dest


def fetch_distinct_combos(conn):
    """Retourne la liste des combos distincts (level_1, level_2, level_3) de allowed_mappings."""
    rows = conn.execute(text(
        "SELECT DISTINCT level_1, level_2, level_3 FROM allowed_mappings"
    )).fetchall()
    return [(r[0], r[1], r[2]) for r in rows]


def validate_combos(combos):
    """
    Vérifie que chaque level_3 est légal et qu'aucun level_2 n'apparaît avec
    deux level_3 différents. Lève ValueError avec le détail si un problème
    est détecté (abort explicite, ne force jamais).
    """
    illegal = sorted({level_3 for (_, _, level_3) in combos if level_3 not in ALLOWED_LEVEL_3_VALUES})
    if illegal:
        raise ValueError(
            f"level_3 hors des 5 valeurs légales détecté(s) : {illegal}. "
            f"Valeurs légales : {sorted(ALLOWED_LEVEL_3_VALUES)}."
        )

    level_2_to_level_3 = defaultdict(set)
    for (_, level_2, level_3) in combos:
        level_2_to_level_3[level_2].add(level_3)

    collisions = {level_2: sorted(natures) for level_2, natures in level_2_to_level_3.items() if len(natures) > 1}
    if collisions:
        lines = "\n".join(f"   - {level_2!r} apparaît avec level_3 = {natures}" for level_2, natures in collisions.items())
        raise ValueError(
            "Collision détectée : au moins un level_2 apparaît avec plusieurs level_3 différents, "
            "donc CategoryGroup.label ne peut pas être UNIQUE :\n" + lines
        )


def seed_referential(session, combos):
    """
    Crée les CategoryGroup/Category distincts absents. Idempotent (INSERT
    seulement si absent). Retourne (n_groups_created, n_groups_existing,
    n_categories_created, n_categories_existing).
    """
    n_groups_created = n_groups_existing = 0
    n_categories_created = n_categories_existing = 0

    # Regroupement level_2 -> nature (déjà validé sans collision) puis level_1 par level_2
    level_2_nature = {}
    level_1_by_level_2 = defaultdict(set)
    for level_1, level_2, level_3 in combos:
        level_2_nature[level_2] = NATURE_BY_LABEL[level_3]
        level_1_by_level_2[level_2].add(level_1)

    groups_by_label = {}
    for level_2, nature in level_2_nature.items():
        existing_group = session.query(CategoryGroup).filter(CategoryGroup.label == level_2).first()
        if existing_group is not None:
            groups_by_label[level_2] = existing_group
            n_groups_existing += 1
        else:
            new_group = CategoryGroup(label=level_2, nature=nature)
            session.add(new_group)
            session.flush()
            groups_by_label[level_2] = new_group
            n_groups_created += 1

    for level_2, level_1_labels in level_1_by_level_2.items():
        group = groups_by_label[level_2]
        for level_1 in level_1_labels:
            existing_category = (
                session.query(Category)
                .filter(Category.label == level_1, Category.group_id == group.id)
                .first()
            )
            if existing_category is not None:
                n_categories_existing += 1
            else:
                session.add(Category(label=level_1, group_id=group.id, is_custom=False))
                n_categories_created += 1

    session.flush()
    return n_groups_created, n_groups_existing, n_categories_created, n_categories_existing


def verify_used_combos_resolve(session, conn):
    """Vérifie que chaque combo distinct de enriched_transactions résout vers une Category."""
    rows = conn.execute(text(
        "SELECT DISTINCT level_1, level_2, level_3 FROM enriched_transactions"
    )).fetchall()
    used_combos = [(r[0], r[1], r[2]) for r in rows]
    unresolved = []
    for level_1, level_2, level_3 in used_combos:
        if resolve_category(session, level_1, level_2, level_3) is None:
            unresolved.append((level_1, level_2, level_3))
    return len(used_combos), unresolved


def main() -> int:
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with engine.connect() as conn:
        combos = fetch_distinct_combos(conn)
    print(f"\n📊 Combos distincts trouvés dans allowed_mappings : {len(combos)}")

    try:
        validate_combos(combos)
    except ValueError as exc:
        print(f"\n❌ {exc}", file=sys.stderr)
        return 2
    print("✅ Validation OK : level_3 tous légaux, aucune collision level_2 → level_3.")

    if '--yes' not in sys.argv:
        print(
            "\n⚠️  Ce script va effectuer un backup puis créer/peupler les tables "
            "category_groups / categories sur la base de PRODUCTION."
        )
        response = input("Continuer ? (oui/non): ")
        if response.lower() not in ('oui', 'o', 'yes', 'y'):
            print("❌ Opération annulée")
            return 1
    else:
        print("\n⚠️  Exécution (--yes activé)")

    backup_path = backup_database()
    print(f"\n💾 Backup réalisé : {backup_path}")

    session = Session()
    try:
        Base.metadata.create_all(bind=engine, tables=[CategoryGroup.__table__, Category.__table__])
        print("🗄️  Tables category_groups / categories créées (ou déjà présentes).")

        n_groups_created, n_groups_existing, n_categories_created, n_categories_existing = seed_referential(session, combos)
        session.commit()
    except Exception:
        session.rollback()
        print(f"❌ Échec du seed. Restaurer depuis le backup si besoin : {backup_path}", file=sys.stderr)
        raise
    finally:
        session.close()

    print(f"\n📊 Rapport de seed :")
    print(f"   - category_groups : {n_groups_created} créé(s), {n_groups_existing} déjà présent(s)")
    print(f"   - categories      : {n_categories_created} créée(s), {n_categories_existing} déjà présente(s)")

    verify_session = Session()
    try:
        with engine.connect() as conn:
            n_used, unresolved = verify_used_combos_resolve(verify_session, conn)
    finally:
        verify_session.close()

    print(f"\n🔎 Vérification post-seed : {n_used} combos distincts utilisés dans enriched_transactions.")
    if unresolved:
        print(f"❌ {len(unresolved)} combo(s) non résolu(s) :", file=sys.stderr)
        for combo in unresolved:
            print(f"   - {combo}", file=sys.stderr)
        return 3
    print(f"✅ {n_used}/{n_used} combos utilisés résolvent vers une Category.")

    print("\n✅ Migration terminée : référentiel category_groups/categories seedé.")
    return 0


if __name__ == "__main__":
    print("=" * 60)
    print("SEED DU RÉFÉRENTIEL CATEGORY_GROUPS / CATEGORIES")
    print("=" * 60)
    sys.exit(main())
