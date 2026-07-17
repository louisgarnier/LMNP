"""Crée la table fiscal_settings et insère la ligne de réglages par défaut
(déficit reportable 10 ans, amortissements illimités).

Idempotent (marqueur schema_migrations). Backup automatique avant écriture.

Usage:
    python3 backend/database/migrations/add_fiscal_settings.py --yes
"""
import os
import shutil
import sys
from datetime import datetime

from sqlalchemy import text

from backend.database.connection import engine

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lmnp.db'))
BACKUPS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backups'))
MIGRATION_NAME = "add_fiscal_settings"


def backup_database():
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%F_%H%M%S")
    dest = os.path.join(BACKUPS_DIR, f"lmnp_{stamp}_avant-fiscal-settings.db")
    shutil.copy2(DB_PATH, dest)
    return dest


def already_applied(conn):
    conn.execute(text(
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(name TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"))
    return conn.execute(text(
        "SELECT 1 FROM schema_migrations WHERE name = :n"), {"n": MIGRATION_NAME}).fetchone() is not None


def main():
    with engine.begin() as conn:
        if already_applied(conn):
            print("✅ Déjà appliquée.")
            return 0
    if '--yes' not in sys.argv:
        print("⚠️ Crée fiscal_settings + ligne par défaut. Relancer avec --yes.")
        return 1
    dest = backup_database()
    print(f"💾 Backup : {dest}")
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS fiscal_settings ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "deficit_report_years INTEGER NOT NULL DEFAULT 10, "
            "amort_report_years INTEGER, "
            "created_at DATETIME, updated_at DATETIME)"))
        exists = conn.execute(text("SELECT COUNT(*) FROM fiscal_settings")).scalar()
        if exists == 0:
            now = datetime.now().isoformat(timespec="seconds")
            conn.execute(text(
                "INSERT INTO fiscal_settings (deficit_report_years, amort_report_years, created_at, updated_at) "
                "VALUES (10, NULL, :t, :t)"), {"t": now})
            print("➕ Ligne par défaut insérée (déficit 10 ans, amort illimité).")
        conn.execute(text(
            "INSERT OR IGNORE INTO schema_migrations (name, applied_at) VALUES (:n, :t)"),
            {"n": MIGRATION_NAME, "t": datetime.now().isoformat(timespec="seconds")})
    print("✅ Migration terminée.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
