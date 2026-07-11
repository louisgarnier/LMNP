"""
Migration Étape 2 Task 3 : ajoute `transactions.category_id` (FK nullable
vers `categories.id`, indexée) et la remplit par backfill depuis
`enriched_transactions` (source de LECTURE, non modifiée) via
`resolve_category(db, level_1, level_2, level_3)` (Task 2).

Ce script ne change AUCUN chemin de lecture/écriture existant : il ajoute
une colonne et la remplit. `enriched_transactions` reste la source de
vérité pour les classifications partout ailleurs dans l'app.

`backfill(db) -> dict` est une fonction PURE (aucun accès disque/DDL), donc
testable sur une session isolée (SQLite en mémoire, voir
backend/tests/test_category_backfill.py). Elle suppose que la colonne
`transactions.category_id` existe déjà dans le schéma de la session (c'est
le cas dans les tests car `Base.metadata.create_all` recrée tout le schéma
à jour, colonne comprise).

`main()` est le CLI qui s'applique à la vraie base :
1. Backup horodaté de `backend/database/lmnp.db` dans `backups/`.
2. DDL idempotente : `ALTER TABLE transactions ADD COLUMN category_id ...`
   seulement si la colonne est absente (vérifié via `PRAGMA table_info`),
   puis `CREATE INDEX IF NOT EXISTS`.
3. `backfill(session)` sur la vraie base.
4. ABORT (rollback) si au moins une transaction enrichie ne résout vers
   aucune Category (`unmatched > 0`) — ne force jamais un état partiel.

Usage:
    python3 backend/database/migrations/backfill_transaction_categories.py          # demande confirmation
    python3 backend/database/migrations/backfill_transaction_categories.py --yes    # sans confirmation
"""

import os
import shutil
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from backend.database.connection import engine
from backend.database.models import Transaction, EnrichedTransaction
from backend.api.services.category_service import resolve_category

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lmnp.db'))
BACKUPS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backups'))


def backup_database() -> str:
    """Copie la base de production dans backups/ avec un nom horodaté."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Base de production introuvable: {DB_PATH}")
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%F_%H%M%S")
    dest = os.path.join(BACKUPS_DIR, f"lmnp_{stamp}_avant-backfill-categories.db")
    shutil.copy2(DB_PATH, dest)
    return dest


def column_exists(conn, table: str, column: str) -> bool:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return any(row[1] == column for row in rows)


def apply_ddl(conn) -> bool:
    """Ajoute la colonne `category_id` et son index si absents. Retourne True
    si la colonne a été créée par cet appel (False si déjà présente)."""
    created = False
    if not column_exists(conn, "transactions", "category_id"):
        conn.execute(text(
            "ALTER TABLE transactions ADD COLUMN category_id INTEGER REFERENCES categories(id)"
        ))
        created = True
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_transactions_category_id ON transactions(category_id)"
    ))
    return created


def _backfill_with_details(db):
    """
    Pour chaque EnrichedTransaction avec level_1 IS NOT NULL, résout la
    Category via resolve_category et met à jour Transaction.category_id.

    Retourne (stats, unmatched_details) où stats = {"total", "matched",
    "unmatched"} et unmatched_details = liste de (transaction_id, level_1,
    level_2, level_3) pour les cas non résolus (rapport CLI).
    """
    total = matched = unmatched = 0
    unmatched_details = []

    enriched_rows = (
        db.query(EnrichedTransaction)
        .filter(EnrichedTransaction.level_1.isnot(None))
        .all()
    )

    for enriched in enriched_rows:
        total += 1
        category = resolve_category(db, enriched.level_1, enriched.level_2, enriched.level_3)
        transaction = (
            db.query(Transaction).filter(Transaction.id == enriched.transaction_id).first()
            if category is not None else None
        )
        if category is None or transaction is None:
            unmatched += 1
            unmatched_details.append(
                (enriched.transaction_id, enriched.level_1, enriched.level_2, enriched.level_3)
            )
            continue
        transaction.category_id = category.id
        matched += 1

    db.flush()

    stats = {"total": total, "matched": matched, "unmatched": unmatched}
    return stats, unmatched_details


def backfill(db) -> dict:
    """Fonction pure testable : {"total", "matched", "unmatched"}."""
    stats, _unmatched_details = _backfill_with_details(db)
    return stats


def main() -> int:
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    if '--yes' not in sys.argv:
        print(
            "\n⚠️  Ce script va effectuer un backup puis ajouter/remplir la colonne "
            "transactions.category_id sur la base de PRODUCTION."
        )
        response = input("Continuer ? (oui/non): ")
        if response.lower() not in ('oui', 'o', 'yes', 'y'):
            print("❌ Opération annulée")
            return 1
    else:
        print("\n⚠️  Exécution (--yes activé)")

    backup_path = backup_database()
    print(f"\n💾 Backup réalisé : {backup_path}")

    with engine.begin() as conn:
        created = apply_ddl(conn)
    if created:
        print("🗄️  Colonne transactions.category_id créée + index idx_transactions_category_id.")
    else:
        print("🗄️  Colonne transactions.category_id déjà présente (DDL idempotente, rien fait).")

    session = Session()
    try:
        stats, unmatched_details = _backfill_with_details(session)
        if stats["unmatched"] > 0:
            session.rollback()
            print(f"\n❌ {stats['unmatched']} transaction(s) enrichie(s) non résolue(s) — ABORT (rollback) :", file=sys.stderr)
            for transaction_id, level_1, level_2, level_3 in unmatched_details:
                print(f"   - transaction_id={transaction_id} : ({level_1!r}, {level_2!r}, {level_3!r})", file=sys.stderr)
            return 3
        session.commit()
    except Exception:
        session.rollback()
        print(f"❌ Échec du backfill. Restaurer depuis le backup si besoin : {backup_path}", file=sys.stderr)
        raise
    finally:
        session.close()

    print(f"\n📊 Rapport de backfill :")
    print(f"   - total   : {stats['total']}")
    print(f"   - matched : {stats['matched']}")
    print(f"   - unmatched : {stats['unmatched']}")
    print(f"\n✅ Migration terminée : {stats['matched']}/{stats['total']} transactions.category_id renseignés.")
    return 0


if __name__ == "__main__":
    print("=" * 60)
    print("BACKFILL TRANSACTIONS.CATEGORY_ID DEPUIS ENRICHED_TRANSACTIONS")
    print("=" * 60)
    sys.exit(main())
