"""
Migration Étape 2 Task 9 : conversion des montants monétaires en centimes.

Convertit LES VALEURS des colonnes monétaires de "euros float" en "centimes
entiers" via un UPDATE en place :

    UPDATE table SET col = CAST(ROUND(col * 100) AS INTEGER) WHERE col IS NOT NULL

Le type SQLAlchemy `EuroCents` (backend/database/money.py), désormais posé sur
ces colonnes dans le modèle, gouverne l'interprétation : il relit les centimes
entiers et les expose en euros (float) aux services/API — contrat golden
inchangé.

── Choix de l'approche : UPDATE en place (et non rebuild complet des tables) ──
SQLite étant typé dynamiquement, une colonne déclarée FLOAT accepte sans
broncher des entiers ; c'est le décorateur `EuroCents` (côté modèle) qui fait
foi, pas le type déclaré sur disque. L'UPDATE en place NE TOUCHE À AUCUN index,
contrainte unique, ni clé étrangère (transactions : idx_transaction_unique +
index property_id ; loan_configs : unique (property_id, name) de la Task 1 ;
etc.) — c'est l'option la PLUS SÛRE, celle explicitement recommandée pour cette
migration à haut risque (6 tables). Conséquence assumée : le type DÉCLARÉ sur
disque reste FLOAT (cosmétique) alors que les valeurs stockées sont des entiers
de centimes — le décorateur est la source de vérité.

── Colonnes converties (11) sur 6 tables ──
  transactions           : quantite, solde
  amortization_types     : annual_amount
  loan_payments          : capital, interest, insurance, total
  loan_configs           : credit_amount, monthly_insurance
  compte_resultat_override : override_value
  annual_forecast_configs : base_annual_amount

── Colonne VOLONTAIREMENT NON convertie ──
  amortization_results.amount : montant d'amortissement DÉRIVÉ (total/durée), à
  décimales infinies (ex. -643.7569444...). L'arrondir au centime ferait dériver
  les lignes cumulées du bilan jusqu'à ~0,06 € (mesuré sur la base réelle),
  au-delà de la tolérance golden de 0,01 €. Elle reste donc en Float pour
  préserver la précision sub-centime et le golden. Voir task-9-report.md.

── Garde-fous ──
- Backup horodaté AVANT toute écriture (dans backups/).
- Idempotence : une table marqueur `schema_migrations` empêche un second passage
  (un double UPDATE multiplierait les valeurs par 100 → corruption).
- Préservation des montants : pour chaque colonne, SUM(avant) est comparé à
  SUM(après)/100 ; tout écart > 0,01 € fait AVORTER la migration (rollback
  complet dans la même transaction) — signe qu'une valeur réelle avait plus de
  2 décimales (à investiguer, ne pas forcer).

Usage:
    python3 backend/database/migrations/convert_money_to_cents.py          # demande confirmation
    python3 backend/database/migrations/convert_money_to_cents.py --yes    # sans confirmation
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

MIGRATION_NAME = "convert_money_to_cents"
SUM_TOLERANCE = 0.01

# (table, [colonnes monétaires converties]) — amortization_results.amount EXCLUE (Float délibéré).
MONEY_COLUMNS = [
    ("transactions", ["quantite", "solde"]),
    ("amortization_types", ["annual_amount"]),
    ("loan_payments", ["capital", "interest", "insurance", "total"]),
    ("loan_configs", ["credit_amount", "monthly_insurance"]),
    ("compte_resultat_override", ["override_value"]),
    ("annual_forecast_configs", ["base_annual_amount"]),
]


def backup_database() -> str:
    """Copie la base de production dans backups/ avec un nom horodaté."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Base de production introuvable: {DB_PATH}")
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%F_%H%M%S")
    dest = os.path.join(BACKUPS_DIR, f"lmnp_{stamp}_avant-convert-money-to-cents.db")
    shutil.copy2(DB_PATH, dest)
    return dest


def already_applied(conn) -> bool:
    """True si la migration a déjà tourné (table marqueur schema_migrations)."""
    conn.execute(text(
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(name TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
    ))
    row = conn.execute(text(
        "SELECT 1 FROM schema_migrations WHERE name = :n"
    ), {"n": MIGRATION_NAME}).fetchone()
    return row is not None


def column_sum(conn, table: str, col: str):
    """SUM brut (sans décorateur) de la colonne, ou 0.0 si vide/NULL."""
    return conn.execute(text(f"SELECT COALESCE(SUM({col}), 0) FROM {table}")).scalar()


def main() -> int:
    # Garde-fou idempotence (avant tout backup/écriture).
    with engine.begin() as conn:
        if already_applied(conn):
            print("✅ Migration déjà appliquée (schema_migrations). Rien à faire.")
            return 0

    # SUM AVANT (euros) — lecture seule.
    before_sums = {}
    with engine.connect() as conn:
        for table, cols in MONEY_COLUMNS:
            for col in cols:
                before_sums[(table, col)] = column_sum(conn, table, col)

    print("📊 SUM AVANT conversion (euros) :")
    for (table, col), s in before_sums.items():
        print(f"   - {table}.{col}: {s}")

    if '--yes' not in sys.argv:
        print(
            "\n⚠️  Ce script va effectuer un backup puis convertir les montants "
            "monétaires en centimes (UPDATE en place) sur la base de PRODUCTION."
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
        # Tout se joue dans une seule transaction : la vérification des SUM se
        # fait AVANT le commit ; le moindre écart lève et provoque un rollback.
        with engine.begin() as conn:
            if already_applied(conn):  # re-check sous transaction (course improbable)
                print("✅ Migration déjà appliquée entre-temps. Rien à faire.")
                return 0

            for table, cols in MONEY_COLUMNS:
                for col in cols:
                    # SQLite ROUND() arrondit au demi supérieur en valeur absolue
                    # (half-away-from-zero), alors que le TypeDecorator EuroCents
                    # arrondit au pair le plus proche (half-to-even, Python). L'écart
                    # n'apparaît qu'à un centième de centime exact (valeur en x.xx5) :
                    # aucune valeur de prod ne tombe sur ce cas, et la SUM est préservée
                    # (vérifiée plus bas dans la transaction).
                    conn.execute(text(
                        f"UPDATE {table} SET {col} = CAST(ROUND({col} * 100) AS INTEGER) "
                        f"WHERE {col} IS NOT NULL"
                    ))
                    print(f"🗄️  {table}.{col} converti en centimes.")

            # Vérification préservation des montants (dans la transaction).
            print("\n📊 Vérification SUM APRÈS (centimes/100) :")
            failures = []
            for (table, col), before in before_sums.items():
                after_cents = column_sum(conn, table, col)
                after_euros = after_cents / 100.0
                diff = abs(float(before) - after_euros)
                status = "OK" if diff <= SUM_TOLERANCE else "DIVERGE"
                print(f"   - {table}.{col}: avant={before} après={after_euros} "
                      f"(écart={diff:.6f}) [{status}]")
                if diff > SUM_TOLERANCE:
                    failures.append((table, col, before, after_euros, diff))

            if failures:
                lines = "; ".join(
                    f"{t}.{c}: {b} -> {a} (écart {d:.4f})"
                    for t, c, b, a, d in failures
                )
                raise RuntimeError(
                    "ABORT : préservation des montants violée (écart > "
                    f"{SUM_TOLERANCE} €) — rollback complet. Colonnes fautives : {lines}"
                )

            conn.execute(text(
                "INSERT INTO schema_migrations (name, applied_at) VALUES (:n, :t)"
            ), {"n": MIGRATION_NAME, "t": datetime.now().isoformat(timespec="seconds")})
    except Exception:
        # Pas d'avalage silencieux : la trace complète est exposée. La transaction
        # a été annulée ; en dernier recours, restaurer depuis le backup.
        print(f"❌ Échec de la migration (rollback effectué). "
              f"Restaurer depuis le backup si besoin : {backup_path}", file=sys.stderr)
        raise

    print("\n✅ Migration terminée : montants stockés en centimes "
          "(11 colonnes / 6 tables). amortization_results.amount reste en Float "
          "(valeur dérivée, précision sub-centime préservée pour le golden).")
    return 0


if __name__ == "__main__":
    print("=" * 60)
    print("CONVERSION DES MONTANTS EN CENTIMES (EuroCents)")
    print("=" * 60)
    sys.exit(main())
