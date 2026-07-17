"""Supprime les colonnes fantômes `level_1_values` de compte_resultat_mappings
et bilan_mappings.

CONTEXTE
--------
Étape 2 Task 8 a retiré ces colonnes des modèles ORM (cf. models.py:364 et
models.py:463) : la source de vérité est désormais la table de liaison
(`compte_resultat_mapping_categories` / `bilan_mapping_categories`), et
`labels_from_mapping_categories` reconstruit les labels depuis la liaison.
SQLAlchemy ne lit ni n'écrit donc plus ces colonnes.

Mais les colonnes PHYSIQUES sont restées, figées à leur valeur du jour du
retrait. Elles MENTENT (constaté le 17/07/2026) :

    compte_resultat_mappings id=87 (Evry, « Impôts et taxes »)
        colonne  : ["Taxe foncière"]
        liaison  : ["Cotisation Foncière des Entreprises (CFE)", "Taxe foncière"]
    compte_resultat_mappings id=99 (Marseille, « Travaux et mobilier »)
        colonne  : ["Entretien et réparations"]
        liaison  : ["Entretien et réparations", "Mobilier et équipements"]

COÛT RÉEL : lors du débogage du bilan Evry le 17/07, la lecture SQL de cette
colonne a fait conclure à tort que la CFE n'était rattachée à aucune ligne du
compte de résultat, et envoyé l'investigation sur une fausse piste. La colonne
n'est pas seulement inutile : elle est piégeuse.

⚠️ NE PAS CONFONDRE avec `amortization_types.level_1_values` (models.py:256) qui
est BIEN VIVANT et lu pour du calcul (amortization_service.py:178-179, filtres
IN de routes/amortization_types.py). Cette migration n'y touche pas.

SÛRETÉ
------
- Aucun index ni vue ne référence ces colonnes (vérifié : sqlite_master).
- Aucun code ne les lit (vérifié : les seules occurrences `level_1_values` pour
  CR/Bilan sont des champs Pydantic d'API, alimentés depuis la liaison).
- Idempotent : marqueur `schema_migrations` + colonnes déjà absentes = no-op.
- Backup automatique avant toute écriture.

Usage:
    python3 backend/database/migrations/drop_level_1_values_legacy_columns.py        # demande confirmation
    python3 backend/database/migrations/drop_level_1_values_legacy_columns.py --yes  # sans confirmation
"""
import os
import shutil
import sys
from datetime import datetime

from sqlalchemy import text

from backend.database.connection import engine

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lmnp.db'))
BACKUPS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backups'))

MIGRATION_NAME = "drop_level_1_values_legacy_columns"

# (table, colonne) — amortization_types.level_1_values EXCLUE (vivante).
TARGETS = [
    ("compte_resultat_mappings", "level_1_values"),
    ("bilan_mappings", "level_1_values"),
]


def backup_database() -> str:
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Base de production introuvable: {DB_PATH}")
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%F_%H%M%S")
    dest = os.path.join(BACKUPS_DIR, f"lmnp_{stamp}_avant-drop-level1values.db")
    shutil.copy2(DB_PATH, dest)
    return dest


def already_applied(conn) -> bool:
    conn.execute(text(
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(name TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
    ))
    row = conn.execute(text(
        "SELECT 1 FROM schema_migrations WHERE name = :n"
    ), {"n": MIGRATION_NAME}).fetchone()
    return row is not None


def has_column(conn, table: str, col: str) -> bool:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return any(r[1] == col for r in rows)


def row_count(conn, table: str) -> int:
    return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()


def main() -> int:
    with engine.begin() as conn:
        if already_applied(conn):
            print("✅ Migration déjà appliquée (schema_migrations). Rien à faire.")
            return 0

    # État AVANT (lecture seule) + garde-fou : on ne touche pas amortization_types.
    with engine.connect() as conn:
        present = [(t, c) for t, c in TARGETS if has_column(conn, t, c)]
        counts = {t: row_count(conn, t) for t, _ in TARGETS}
        amort_ok = has_column(conn, "amortization_types", "level_1_values")

    if not present:
        print("✅ Colonnes déjà absentes. Rien à faire.")
        with engine.begin() as conn:
            conn.execute(text(
                "INSERT OR IGNORE INTO schema_migrations (name, applied_at) VALUES (:n, :t)"
            ), {"n": MIGRATION_NAME, "t": datetime.now().isoformat(timespec="seconds")})
        return 0

    print("📊 État AVANT :")
    for t, c in present:
        print(f"   - {t}.{c} présente ({counts[t]} lignes dans la table)")
    print(f"   - amortization_types.level_1_values présente : {amort_ok} (doit rester True)")

    if '--yes' not in sys.argv:
        print("\n⚠️  Ce script va effectuer un backup puis SUPPRIMER ces colonnes.")
        if input("Confirmer ? [oui/non] ").strip().lower() not in ("oui", "o", "yes", "y"):
            print("Abandon.")
            return 1

    dest = backup_database()
    print(f"💾 Backup : {dest}")

    with engine.begin() as conn:
        for t, c in present:
            conn.execute(text(f"ALTER TABLE {t} DROP COLUMN {c}"))
            print(f"🗑️  {t}.{c} supprimée")
        conn.execute(text(
            "INSERT OR IGNORE INTO schema_migrations (name, applied_at) VALUES (:n, :t)"
        ), {"n": MIGRATION_NAME, "t": datetime.now().isoformat(timespec="seconds")})

    # Vérification APRÈS : colonnes parties, lignes intactes, amortization_types intacte.
    ok = True
    with engine.connect() as conn:
        for t, c in TARGETS:
            if has_column(conn, t, c):
                print(f"❌ {t}.{c} TOUJOURS présente")
                ok = False
            after = row_count(conn, t)
            if after != counts[t]:
                print(f"❌ {t} : {counts[t]} lignes avant, {after} après")
                ok = False
            else:
                print(f"✅ {t} : {after} lignes (inchangé)")
        if not has_column(conn, "amortization_types", "level_1_values"):
            print("❌ amortization_types.level_1_values a été supprimée par erreur !")
            ok = False
        else:
            print("✅ amortization_types.level_1_values intacte (vivante)")

    print("\n✅ Migration terminée." if ok else "\n❌ Migration en échec — restaurer le backup.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
