"""Corrige la FK fantôme de amortization_results.

Contexte : la table `amortization_results` porte une colonne morte
`amortization_view_id INTEGER REFERENCES amortization_views(id)`, mais la table
`amortization_views` a été supprimée pendant la refonte (drop_orphan_tables).
Avec `PRAGMA foreign_keys = ON`, TOUTE suppression d'une ligne d'amortissement
(donc toute suppression de transaction amortie) plante :
    sqlite3.OperationalError: no such table: main.amortization_views

La colonne est intégralement NULL (aucune donnée). On reconstruit donc la table
SANS cette colonne/FK, en conservant la bonne FK
`transaction_id REFERENCES transactions(id) ON DELETE CASCADE` et les index.

Idempotent : ne fait rien si la colonne a déjà disparu.
"""
import sqlite3
import sys
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parents[2] / "database" / "lmnp.db"


def migrate(db_path: str | Path = DEFAULT_DB) -> bool:
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cols = [r[1] for r in cur.execute("PRAGMA table_info(amortization_results)").fetchall()]
    if "amortization_view_id" not in cols:
        print("✅ Déjà migré (colonne amortization_view_id absente).")
        conn.close()
        return False

    nn = cur.execute(
        "SELECT COUNT(*) FROM amortization_results WHERE amortization_view_id IS NOT NULL"
    ).fetchone()[0]
    if nn:
        conn.close()
        raise RuntimeError(f"❌ Abandon : {nn} lignes ont amortization_view_id non NULL (données à préserver).")

    cur.execute("PRAGMA foreign_keys = OFF")
    conn.execute("BEGIN")
    try:
        cur.execute(
            """
            CREATE TABLE amortization_results_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER NOT NULL,
                year INTEGER NOT NULL,
                category VARCHAR(50) NOT NULL,
                amount FLOAT NOT NULL,
                created_at DATETIME,
                updated_at DATETIME,
                property_id INTEGER,
                FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE
            )
            """
        )
        cur.execute(
            """
            INSERT INTO amortization_results_new
                (id, transaction_id, year, category, amount, created_at, updated_at, property_id)
            SELECT id, transaction_id, year, category, amount, created_at, updated_at, property_id
            FROM amortization_results
            """
        )
        cur.execute("DROP TABLE amortization_results")
        cur.execute("ALTER TABLE amortization_results_new RENAME TO amortization_results")
        cur.execute("CREATE INDEX idx_amortization_result_year_category ON amortization_results(year, category)")
        cur.execute("CREATE INDEX idx_amortization_result_transaction ON amortization_results(transaction_id)")
        cur.execute("CREATE INDEX idx_amortization_results_transaction_id ON amortization_results(transaction_id)")
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        raise

    # Vérif intégrité FK après reconstruction
    problems = cur.execute("PRAGMA foreign_key_check").fetchall()
    conn.close()
    if problems:
        raise RuntimeError(f"❌ foreign_key_check a signalé des problèmes : {problems}")
    print("✅ amortization_results reconstruite sans la FK fantôme amortization_views.")
    return True


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB
    migrate(path)
