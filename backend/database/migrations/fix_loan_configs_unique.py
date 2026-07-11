"""
Migration Étape 2 Task 1 : fix du drift d'index sur `loan_configs`.

Contexte : la base sur disque n'a AUCUNE contrainte unique sur le nom des
crédits (les index legacy `idx_loan_configs_name` / `ix_loan_configs_name`
sont non-uniques), alors que la spec veut l'unicité PAR propriété. Le modèle
SQLAlchemy déclarait à tort `idx_loan_config_name` unique GLOBAL (corrigé dans
backend/database/models.py dans le même commit). Cette migration aligne le
disque sur le modèle corrigé :

    DROP INDEX IF EXISTS idx_loan_config_name;      -- n'existe pas sur disque, sécurité
    DROP INDEX IF EXISTS idx_loan_configs_name;     -- non-unique legacy
    DROP INDEX IF EXISTS ix_loan_configs_name;      -- non-unique legacy
    CREATE UNIQUE INDEX IF NOT EXISTS idx_loan_config_property_name
      ON loan_configs (property_id, name);

Garde-fou : avant le CREATE, vérifie qu'aucun doublon (property_id, name)
n'existe ; s'il y en a, abort avec un message explicite (aucun DROP/CREATE
n'est alors appliqué, tout se joue dans une seule transaction).

⚠️ Ce script MODIFIE la base de production (backend/database/lmnp.db).
Un backup horodaté est réalisé AUTOMATIQUEMENT avant toute écriture, dans backups/.

Usage:
    python3 backend/database/migrations/fix_loan_configs_unique.py          # demande confirmation
    python3 backend/database/migrations/fix_loan_configs_unique.py --yes    # sans confirmation
"""

import os
import shutil
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from sqlalchemy import text

from backend.database.connection import engine

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lmnp.db'))
BACKUPS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backups'))

INDEXES_TO_DROP = [
    "idx_loan_config_name",   # unique global déclaré à tort par l'ancien modèle (absent sur disque, sécurité)
    "idx_loan_configs_name",  # non-unique legacy
    "ix_loan_configs_name",   # non-unique legacy
]
TARGET_INDEX = "idx_loan_config_property_name"


def index_report(conn):
    """Retourne la liste [(nom, unique)] des index de loan_configs."""
    rows = conn.execute(text("PRAGMA index_list(loan_configs)")).fetchall()
    # PRAGMA index_list: (seq, name, unique, origin, partial)
    return [(row[1], bool(row[2])) for row in rows]


def print_report(label, report):
    print(f"\n📊 Index de loan_configs ({label}):")
    if not report:
        print("   (aucun index)")
    for name, unique in report:
        print(f"   - {name}: unique={unique}")


def find_duplicates(conn):
    """Retourne les doublons (property_id, name) qui empêcheraient l'index unique."""
    return conn.execute(text(
        "SELECT property_id, name, COUNT(*) AS n FROM loan_configs "
        "GROUP BY property_id, name HAVING n > 1"
    )).fetchall()


def backup_database() -> str:
    """Copie la base de production dans backups/ avec un nom horodaté."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Base de production introuvable: {DB_PATH}")
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%F_%H%M%S")
    dest = os.path.join(BACKUPS_DIR, f"lmnp_{stamp}_avant-fix-loan-configs-unique.db")
    shutil.copy2(DB_PATH, dest)
    return dest


def main() -> int:
    with engine.connect() as conn:
        before = index_report(conn)
        duplicates = find_duplicates(conn)
        count = conn.execute(text("SELECT COUNT(*) FROM loan_configs")).scalar()
    print_report("AVANT", before)
    print(f"\n📊 loan_configs: {count} ligne(s)")

    if duplicates:
        print("\n❌ ABORT : doublons (property_id, name) détectés — l'index unique "
              "ne peut pas être créé. Nettoyer d'abord ces lignes :", file=sys.stderr)
        for property_id, name, n in duplicates:
            print(f"   - property_id={property_id}, name={name!r}: {n} occurrences", file=sys.stderr)
        return 3

    if '--yes' not in sys.argv:
        print(
            "\n⚠️  Ce script va effectuer un backup puis modifier les index de "
            "loan_configs sur la base de PRODUCTION (drop des index legacy + "
            f"création de l'index unique {TARGET_INDEX})."
        )
        response = input("Continuer ? (oui/non): ")
        if response.lower() not in ('oui', 'o', 'yes', 'y'):
            print("❌ Opération annulée")
            return 1
    else:
        print("\n⚠️  Exécution (--yes activé)")

    backup_path = backup_database()
    print(f"\n💾 Backup réalisé : {backup_path}")

    try:
        with engine.begin() as conn:
            for index in INDEXES_TO_DROP:
                conn.execute(text(f"DROP INDEX IF EXISTS {index}"))
                print(f"🗄️  DROP INDEX IF EXISTS {index} exécuté.")
            conn.execute(text(
                f"CREATE UNIQUE INDEX IF NOT EXISTS {TARGET_INDEX} "
                "ON loan_configs (property_id, name)"
            ))
            print(f"🗄️  CREATE UNIQUE INDEX {TARGET_INDEX} (property_id, name) exécuté.")
    except Exception:
        # Pas d'avalage silencieux : la trace complète est exposée, et le
        # backup ci-dessus permet une restauration manuelle si nécessaire.
        print(f"❌ Échec de la migration. Restaurer depuis le backup si besoin : {backup_path}", file=sys.stderr)
        raise

    with engine.connect() as conn:
        after = index_report(conn)
    print_report("APRÈS", after)

    after_dict = dict(after)
    if after_dict.get(TARGET_INDEX) is not True:
        print(f"\n❌ L'index unique {TARGET_INDEX} est absent ou non-unique après migration.", file=sys.stderr)
        return 2
    leftovers = [i for i in INDEXES_TO_DROP if i in after_dict]
    if leftovers:
        print(f"\n❌ Index legacy toujours présents : {', '.join(leftovers)}", file=sys.stderr)
        return 2

    print("\n✅ Migration terminée : unicité (property_id, name) réelle sur loan_configs.")
    return 0


if __name__ == "__main__":
    print("=" * 60)
    print("FIX UNICITÉ loan_configs : index unique (property_id, name)")
    print("=" * 60)
    sys.exit(main())
