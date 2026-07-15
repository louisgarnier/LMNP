"""Étape 5 Task 4 : champs d'affichage sur bank_accounts (account_name, currency, bank_balance). Idempotent."""
import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).parent.parent / "lmnp.db"


def _cols(conn, table):
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}


def migrate():
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.cursor()
        existing = _cols(conn, "bank_accounts")
        adds = [
            ("account_name", "VARCHAR(255)"),
            ("currency", "VARCHAR(3)"),
            ("bank_balance", "INTEGER"),
        ]
        for name, decl in adds:
            if name not in existing:
                cur.execute(f"ALTER TABLE bank_accounts ADD COLUMN {name} {decl}")
                print(f"   ✅ bank_accounts.{name} ajoutée")
            else:
                print(f"   ⏭️  bank_accounts.{name} déjà présente")
        conn.commit()
        print("✅ Migration add_bank_account_display_fields terminée")
    except Exception as e:
        conn.rollback()
        print(f"❌ Rollback: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
