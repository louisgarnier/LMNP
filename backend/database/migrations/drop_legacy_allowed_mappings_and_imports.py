"""Supprime les tables physiques orphelines `allowed_mappings` et
`mapping_imports`.

CONTEXTE
--------
Étape 3 a migré `mappings` → `classification_rules`. Les classes ORM
`AllowedMapping` et `MappingImport` ont DÉJÀ été retirées de
`backend/database/models.py` — vérifié : `grep -cE "class (AllowedMapping|
MappingImport)\b" backend/database/models.py` → 0. Les tables physiques sont
restées : ce sont des orphelines sans mapper, que plus aucun code ne lit ni
n'écrit.

Comme les classes ORM sont absentes, `init_database()` (create_all au
démarrage) ne les recréera pas : ce DROP est DÉFINITIF.

L'ADR (docs/workflow/ADR.md:355-358) différait ce drop au motif que
« `allowed_mappings` reste une whitelist de validation VIVANTE
(`validate_mapping` interroge la table) ». Cette justification était fausse sur
ses deux moitiés (constaté le 17/07/2026) :
  1. `validate_mapping` n'interrogeait plus `allowed_mappings` depuis l'étape 3
     (il déléguait à `resolve_category`) ;
  2. `validate_mapping` n'avait aucun appelant en production.
Le module `mapping_obligatoire_service` qui la portait a été supprimé.

PÉRIMÈTRE — CE QUI N'EST PAS TOUCHÉ
------------------------------------
`mappings` (366 lignes) et sa classe ORM `Mapping` sont VOLONTAIREMENT
CONSERVÉES. `models.py:118-130` documente ce choix : le script
`backend/scripts/migrate_mappings_to_rules.py` (« script étape-3 protégé,
jamais à supprimer ») et son test `test_migrate_mappings_to_rules.py` (live)
lisent cette table comme source de migration. Tant que ce consommateur vit, la
table et son modèle restent cohérents. Leur drop reste différé (Task 10) et
relève d'une décision produit, pas d'un nettoyage technique.

SÛRETÉ
------
- Backup automatique avant tout DROP.
- Idempotent : marqueur `schema_migrations` + tables déjà absentes = no-op.
- Vérifie explicitement que `mappings` SURVIT.

Usage:
    python3 backend/database/migrations/drop_legacy_allowed_mappings_and_imports.py        # confirmation
    python3 backend/database/migrations/drop_legacy_allowed_mappings_and_imports.py --yes  # sans confirmation
"""
import os
import shutil
import sys
from datetime import datetime

from sqlalchemy import text

from backend.database.connection import engine

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lmnp.db'))
BACKUPS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backups'))

MIGRATION_NAME = "drop_legacy_allowed_mappings_and_imports"

ORPHAN_TABLES = ["allowed_mappings", "mapping_imports"]
MUST_SURVIVE = ["mappings", "classification_rules"]


def backup_database() -> str:
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Base de production introuvable: {DB_PATH}")
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%F_%H%M%S")
    dest = os.path.join(BACKUPS_DIR, f"lmnp_{stamp}_avant-drop-allowed-mappings.db")
    shutil.copy2(DB_PATH, dest)
    return dest


def already_applied(conn) -> bool:
    conn.execute(text(
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(name TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
    ))
    return conn.execute(text(
        "SELECT 1 FROM schema_migrations WHERE name = :n"
    ), {"n": MIGRATION_NAME}).fetchone() is not None


def table_exists(conn, table: str) -> bool:
    return conn.execute(text(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = :t"
    ), {"t": table}).fetchone() is not None


def row_count(conn, table: str) -> int:
    return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()


def main() -> int:
    with engine.begin() as conn:
        if already_applied(conn):
            print("✅ Migration déjà appliquée (schema_migrations). Rien à faire.")
            return 0

    with engine.connect() as conn:
        present = [t for t in ORPHAN_TABLES if table_exists(conn, t)]
        counts = {t: row_count(conn, t) for t in present}
        survivors = {t: (row_count(conn, t) if table_exists(conn, t) else None)
                     for t in MUST_SURVIVE}

    if not present:
        print("✅ Tables déjà absentes. Rien à faire.")
        with engine.begin() as conn:
            conn.execute(text(
                "INSERT OR IGNORE INTO schema_migrations (name, applied_at) VALUES (:n, :t)"
            ), {"n": MIGRATION_NAME, "t": datetime.now().isoformat(timespec="seconds")})
        return 0

    print("📊 État AVANT :")
    for t in present:
        print(f"   - {t}: {counts[t]} lignes  -> SERA SUPPRIMÉE")
    for t, n in survivors.items():
        print(f"   - {t}: {n} lignes  -> doit survivre")

    if '--yes' not in sys.argv:
        print("\n⚠️  Ce script va effectuer un backup puis DROPper ces tables (définitif).")
        if input("Confirmer ? [oui/non] ").strip().lower() not in ("oui", "o", "yes", "y"):
            print("Abandon.")
            return 1

    dest = backup_database()
    print(f"💾 Backup : {dest}")

    with engine.begin() as conn:
        for t in present:
            conn.execute(text(f"DROP TABLE IF EXISTS {t}"))
            print(f"🗑️  {t} supprimée ({counts[t]} lignes)")
        conn.execute(text(
            "INSERT OR IGNORE INTO schema_migrations (name, applied_at) VALUES (:n, :t)"
        ), {"n": MIGRATION_NAME, "t": datetime.now().isoformat(timespec="seconds")})

    ok = True
    with engine.connect() as conn:
        for t in ORPHAN_TABLES:
            if table_exists(conn, t):
                print(f"❌ {t} TOUJOURS présente")
                ok = False
            else:
                print(f"✅ {t} supprimée")
        for t, before in survivors.items():
            if not table_exists(conn, t):
                print(f"❌ {t} a été supprimée par erreur !")
                ok = False
            elif row_count(conn, t) != before:
                print(f"❌ {t} : {before} lignes avant, {row_count(conn, t)} après")
                ok = False
            else:
                print(f"✅ {t} intacte ({before} lignes)")

    print("\n✅ Migration terminée." if ok else "\n❌ Migration en échec — restaurer le backup.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
