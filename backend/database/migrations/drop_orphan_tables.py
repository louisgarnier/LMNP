"""
Migration Étape 2 Task 1 : suppression des 8 tables orphelines.

Contexte : ces tables n'ont AUCUNE référence dans le code vivant (vérifié le
2026-07-11 ; la seule référence restante, `db.query(Amortization)` dans le
DELETE /api/transactions, a été retirée dans le même commit — la table
`amortizations` n'a jamais eu de writer et contient 0 ligne). Les modèles
SQLAlchemy correspondants (`Parameter`, `Amortization`, `FinancialStatement`,
`ConsolidatedFinancialStatement`) ont été retirés de
backend/database/models.py, donc `init_database()` (create_all au démarrage)
ne les recréera plus : ce DROP est définitif.

Tables supprimées (lignes au moment de l'écriture) :
- parameters (3), amortizations (0), financial_statements (5),
  consolidated_financial_statements (1), compte_resultat_mapping_views (1),
  bilan_mapping_views (1), amortization_views (6), amortization_config (1).

⚠️ Ce script MODIFIE la base de production (backend/database/lmnp.db).
Un backup horodaté est réalisé AUTOMATIQUEMENT avant tout DROP, dans backups/.

Usage:
    python3 backend/database/migrations/drop_orphan_tables.py          # demande confirmation
    python3 backend/database/migrations/drop_orphan_tables.py --yes    # sans confirmation
"""

import os
import shutil
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from sqlalchemy import text

from backend.database.connection import engine

ORPHAN_TABLES = [
    "parameters",
    "amortizations",
    "financial_statements",
    "consolidated_financial_statements",
    "compte_resultat_mapping_views",
    "bilan_mapping_views",
    "amortization_views",
    "amortization_config",
]
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lmnp.db'))
BACKUPS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backups'))


def table_report(conn):
    """Retourne {table: nb_lignes ou None si la table n'existe pas}."""
    report = {}
    for table in ORPHAN_TABLES:
        exists = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=:n"
        ), {"n": table}).first()
        if exists is None:
            report[table] = None
        else:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            report[table] = count
    return report


def print_report(label, report):
    print(f"\n📊 Tables orphelines ({label}):")
    for table, count in report.items():
        if count is None:
            print(f"   - {table}: absente")
        else:
            print(f"   - {table}: présente ({count} ligne(s))")


def backup_database() -> str:
    """Copie la base de production dans backups/ avec un nom horodaté."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Base de production introuvable: {DB_PATH}")
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%F_%H%M%S")
    dest = os.path.join(BACKUPS_DIR, f"lmnp_{stamp}_avant-drop-orphelines.db")
    shutil.copy2(DB_PATH, dest)
    return dest


def main() -> int:
    with engine.connect() as conn:
        before = table_report(conn)
    print_report("AVANT", before)

    if all(v is None for v in before.values()):
        print("\n✅ Rien à faire : les 8 tables orphelines sont déjà absentes.")
        return 0

    if '--yes' not in sys.argv:
        print(
            "\n⚠️  Ce script va effectuer un backup puis DROP TABLE "
            f"{', '.join(ORPHAN_TABLES)} sur la base de PRODUCTION."
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
            for table in ORPHAN_TABLES:
                conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
                print(f"🗄️  DROP TABLE {table} exécuté.")
    except Exception:
        # Pas d'avalage silencieux : la trace complète est exposée, et le
        # backup ci-dessus permet une restauration manuelle si nécessaire.
        print(f"❌ Échec du DROP. Restaurer depuis le backup si besoin : {backup_path}", file=sys.stderr)
        raise

    with engine.connect() as conn:
        after = table_report(conn)
    print_report("APRÈS", after)

    if any(v is not None for v in after.values()):
        print("\n❌ Certaines tables sont toujours présentes après le DROP.", file=sys.stderr)
        return 2

    print("\n✅ Migration terminée : tables orphelines supprimées.")
    return 0


if __name__ == "__main__":
    print("=" * 60)
    print("SUPPRESSION DES 8 TABLES ORPHELINES")
    print("=" * 60)
    sys.exit(main())
