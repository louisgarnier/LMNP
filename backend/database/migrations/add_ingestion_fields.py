"""Étape 4 : colonnes d'ingestion sur transactions + table bank_accounts. Idempotent."""
import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).parent.parent / "lmnp.db"


def _cols(conn, table):
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}


def migrate():
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.cursor()
        existing = _cols(conn, "transactions")
        adds = [
            ("account_id", "INTEGER"),
            ("external_id", "VARCHAR(255)"),
            ("source", "VARCHAR(10) NOT NULL DEFAULT 'csv'"),
            ("parent_transaction_id", "INTEGER"),
            ("is_split_parent", "BOOLEAN NOT NULL DEFAULT 0"),
        ]
        for name, decl in adds:
            if name not in existing:
                cur.execute(f"ALTER TABLE transactions ADD COLUMN {name} {decl}")
                print(f"   ✅ transactions.{name} ajoutée")
            else:
                print(f"   ⏭️  transactions.{name} déjà présente")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS bank_accounts (
                id INTEGER PRIMARY KEY,
                property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
                bank_name VARCHAR(255),
                iban_masked VARCHAR(64),
                eb_account_uid VARCHAR(255),
                eb_session_id VARCHAR(255),
                session_valid_until DATE,
                last_sync_at DATETIME,
                last_tx_cursor VARCHAR(255)
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_bank_accounts_property_id ON bank_accounts(property_id)")
        cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS idx_tx_account_external_unique
                       ON transactions(account_id, external_id) WHERE external_id IS NOT NULL""")
        # backfill de sûreté (les lignes existantes n'ont pas de source explicite)
        cur.execute("UPDATE transactions SET source='csv' WHERE source IS NULL OR source=''")
        conn.commit()
        print("✅ Migration add_ingestion_fields terminée")
    except Exception as e:
        conn.rollback()
        print(f"❌ Rollback: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
