"""
Migration Étape 2 Task 8 (Part C) : DROP TABLE enriched_transactions.

La classification vit désormais dans `transactions.category_id` (référentiel
category/category_groups). La table `enriched_transactions` n'est plus lue ni
écrite par aucun chemin applicatif (cf. task-8-report.md, grep control ZERO).

Sécurité :
1. Backup horodaté de la base de production.
2. VALIDATION Part B (invariant « config non vide → ≥1 nature ») via
   validate_bilan_config_natures.validate — ABORT si un échec.
3. VÉRIFICATION FINALE de cohérence AVANT drop : la classification portée par
   category_id doit correspondre EXACTEMENT à l'ex-enriched pour chaque
   transaction (présence/absence ET label level_1). La requête doit renvoyer 0 ;
   sinon ABORT (rollback), on ne drop jamais sur une incohérence.
4. DROP TABLE enriched_transactions.
Toute exception → rollback + re-raise (jamais d'état partiel silencieux).

Usage:
    python3 backend/database/migrations/drop_enriched_transactions.py          # confirmation
    python3 backend/database/migrations/drop_enriched_transactions.py --yes    # sans confirmation
"""

import os
import shutil
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from backend.database.connection import engine
from backend.database.migrations.validate_bilan_config_natures import validate

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lmnp.db'))
BACKUPS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backups'))

# Incohérences entre la classification category_id et l'ex-enriched :
#  - (enriched.level_1 NULL) XOR (transaction.category_id NULL) : présence/absence
#    de classification divergente ;
#  - category résolue mais son label != enriched.level_1 : classification différente.
COHERENCE_SQL = text("""
    SELECT COUNT(*)
    FROM transactions t
    JOIN enriched_transactions e ON e.transaction_id = t.id
    LEFT JOIN categories c ON c.id = t.category_id
    WHERE (e.level_1 IS NULL) != (t.category_id IS NULL)
       OR (c.id IS NOT NULL AND c.label != e.level_1)
""")


def backup_database() -> str:
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Base de production introuvable: {DB_PATH}")
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%F_%H%M%S")
    dest = os.path.join(BACKUPS_DIR, f"lmnp_{stamp}_avant-drop-enriched.db")
    shutil.copy2(DB_PATH, dest)
    return dest


def table_exists(conn, table: str) -> bool:
    row = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"),
        {"n": table},
    ).first()
    return row is not None


def main() -> int:
    if '--yes' not in sys.argv:
        print(
            "\n⚠️  Ce script va effectuer un backup puis DROP TABLE "
            "enriched_transactions sur la base de PRODUCTION."
        )
        response = input("Continuer ? (oui/non): ")
        if response.lower() not in ('oui', 'o', 'yes', 'y'):
            print("❌ Opération annulée")
            return 1
    else:
        print("\n⚠️  Exécution (--yes activé)")

    backup_path = backup_database()
    print(f"\n💾 Backup réalisé : {backup_path}")

    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        # --- Étape 0 : table déjà absente ? (idempotence) ---
        if not table_exists(session.connection(), "enriched_transactions"):
            print("🗄️  Table enriched_transactions déjà absente — rien à faire.")
            return 0

        # --- Étape 1 : validation Part B (invariant natures) ---
        ok, report = validate(session)
        for entry in report:
            marker = "❌" if entry["failed"] else "✅"
            print(f"   {marker} {entry['table']} property_id={entry['property_id']}: {entry['status']}")
        if not ok:
            session.rollback()
            print("\n❌ ABORT : validation Part B échouée (config non vide sans nature "
                  "traduisible). Aucun drop.", file=sys.stderr)
            return 2
        print("✅ Validation Part B OK (invariant natures vérifié).")

        # --- Étape 2 : vérification finale de cohérence category_id vs enriched ---
        incoherent = session.execute(COHERENCE_SQL).scalar()
        print(f"🔎 Vérification finale de cohérence (attendu 0) : {incoherent}")
        if incoherent != 0:
            session.rollback()
            print(f"\n❌ ABORT : {incoherent} transaction(s) incohérente(s) entre "
                  "category_id et enriched_transactions. Aucun drop.", file=sys.stderr)
            return 3

        # --- Étape 3 : DROP TABLE ---
        session.execute(text("DROP TABLE enriched_transactions"))
        session.commit()
        print("🗄️  DROP TABLE enriched_transactions exécuté.")
    except Exception:
        session.rollback()
        print(f"❌ Échec — rollback. Restaurer depuis le backup si besoin : {backup_path}",
              file=sys.stderr)
        raise
    finally:
        session.close()

    # Vérification post-drop
    with engine.connect() as conn:
        still_there = table_exists(conn, "enriched_transactions")
    if still_there:
        print("❌ La table est toujours présente après le drop.", file=sys.stderr)
        return 4

    print("\n✅ Migration terminée : enriched_transactions supprimée.")
    return 0


if __name__ == "__main__":
    print("=" * 60)
    print("DROP TABLE enriched_transactions (Étape 2 Task 8)")
    print("=" * 60)
    sys.exit(main())
