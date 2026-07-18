"""Migration: table fiscal_imputation_choices (choix d'imputation par année).

⚠️ Avant de lancer, lire : ../../docs/workflow/BEST_PRACTICES.md
"""
import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).parent.parent / "lmnp.db"


def migrate():
    if not DB_FILE.exists():
        print(f"Database file not found: {DB_FILE}")
        return
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fiscal_imputation_choices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL UNIQUE,
                mode VARCHAR(10) NOT NULL DEFAULT 'deficit',
                updated_at DATETIME
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS ix_fic_year ON fiscal_imputation_choices (year)")
        conn.commit()
        print("✅ Table fiscal_imputation_choices prête")
    except Exception as e:
        conn.rollback()
        print(f"❌ {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
