"""
Migration Tâche 7 : suppression des tables de cache des états financiers.

Contexte : le compte de résultat et le bilan sont désormais calculés EN TEMPS
RÉEL (voir backend/api/routes/compte_resultat.py & bilan.py). Les tables de
cache `compte_resultat_data` et `bilan_data` — ainsi que tout le code
d'invalidation associé (bug B1) — n'ont plus de raison d'être :
- `bilan_data` n'était en réalité JAMAIS peuplée (aucun writer).
- `compte_resultat_data` n'était peuplée que par l'ancien endpoint /generate,
  lui aussi supprimé.
Les modèles SQLAlchemy correspondants ont été retirés de
backend/database/models.py, donc `init_database()` (create_all au démarrage)
ne les recréera plus : ce DROP est définitif.

⚠️ Ce script MODIFIE la base de production (backend/database/lmnp.db).
Un backup horodaté est réalisé AUTOMATIQUEMENT avant tout DROP, dans backups/.

Usage:
    python3 backend/scripts/drop_cache_tables.py          # demande confirmation
    python3 backend/scripts/drop_cache_tables.py --yes    # sans confirmation
"""

import os
import shutil
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import text

from backend.database.connection import engine

CACHE_TABLES = ["compte_resultat_data", "bilan_data"]
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database', 'lmnp.db'))
BACKUPS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backups'))


def table_report(conn):
    """Retourne {table: nb_lignes ou None si la table n'existe pas}."""
    report = {}
    for table in CACHE_TABLES:
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
    print(f"\n📊 Tables de cache ({label}):")
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
    dest = os.path.join(BACKUPS_DIR, f"lmnp_{stamp}_avant-drop-caches.db")
    shutil.copy2(DB_PATH, dest)
    return dest


def main() -> int:
    with engine.connect() as conn:
        before = table_report(conn)
    print_report("AVANT", before)

    if all(v is None for v in before.values()):
        print("\n✅ Rien à faire : les deux tables de cache sont déjà absentes.")
        return 0

    if '--yes' not in sys.argv:
        print(
            "\n⚠️  Ce script va effectuer un backup puis DROP TABLE "
            f"{', '.join(CACHE_TABLES)} sur la base de PRODUCTION."
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
            for table in CACHE_TABLES:
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

    print("\n✅ Migration terminée : tables de cache supprimées.")
    return 0


if __name__ == "__main__":
    print("=" * 60)
    print("SUPPRESSION DES TABLES DE CACHE (compte_resultat_data, bilan_data)")
    print("=" * 60)
    sys.exit(main())
