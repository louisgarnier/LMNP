"""
Script de réconciliation du solde Marseille (property_id=15) avec la banque.

Contexte (2026-07-17) : le solde affiché pour Marseille était de 1 702,63 €
alors que le compte Crédit Mutuel affichait 2 900,21 €. Écart : 1 197,58 €.

Règle métier (Louis) : « le solde doit toujours venir des transactions… une
après l'autre ça somme, puis il doit au final matcher avec la banque… en aucun
cas être importé ». `balance_utils.recalculate_all_balances` implémente déjà
exactement cela et n'est PAS en cause. Les deux anomalies étaient dans les
DONNÉES.

--- ANOMALIE 1 : contrepartie compte courant manquante (850,30 €) -------------

Le 11/07/2024, cinq achats d'équipement ont été payés par Louis de sa poche
(jamais passés par le compte bancaire) :

    boitié clefs     -26,01      mr bricolage  -48,90
    electro depot   -563,00      bricorama    -118,50
                                 bricorama     -93,89   => -850,30

Toute écriture hors banque doit avoir sa contrepartie en compte courant
d'associé, faute de quoi le cumul décroche du relevé pour toujours. C'est la
convention appliquée partout ailleurs dans le fichier de Louis : le bloc
d'ouverture 18/01 + 12/03/2024 (achat notaire, immobilisations) nette
exactement à zéro (+4 915 / -4 915) via « cash apport achat notaire » et
« pret verse a Louis ». Ce bloc-ci est le SEUL sans contrepartie.

Preuve : en sommant toutes les lignes du CSV source et en comparant à la
colonne Solde tenue par Louis, sur 79 points de contrôle de l'année 2024, 78
tombent au centime et un seul décroche — de -850,30 €, au 16/07/2024.

=> On ajoute l'apport en compte courant d'associé de +850,30 € au 11/07/2024.
   Effet comptable : les 5 achats restent des immobilisations amortissables
   (inchangés), et la créance de Louis sur le bien apparaît enfin au passif.

--- ANOMALIE 2 : doublon au recouvrement CSV / Enable Banking (347,28 €) ------

`VIR INST VIREMENT GESTION DEC25`, -347,28 €, compté deux fois le 19/01/2026 :
    - id 1787, source 'csv', export-202601191420.csv (exporté le 19/01 à 14h20)
    - id 1996, source 'api', porteuse d'un external_id

L'export CSV contenait déjà les opérations du 19/01 et la synchro Enable
Banking a démarré le 19/01 : les deux fenêtres se recouvrent d'une journée.
L'index anti-doublon `idx_tx_account_external_unique` ne porte que sur
(account_id, external_id) — les lignes CSV n'ont ni l'un ni l'autre, donc la
collision passe au travers. Evry (CSV -> 15/01, API -> 16/01) et Marseille
colloc (CSV -> 16/04, API -> 04/05) ne se recouvrent pas : seul Marseille est
touché.

=> On supprime la ligne CSV (1787) et on garde la ligne API (1996), porteuse de
   l'external_id donc protégée contre un futur re-doublon, en lui reportant la
   catégorie de la ligne supprimée.

--- VÉRIFICATION -------------------------------------------------------------

Golden : backend/tests/test_solde_marseille_golden.py réconcilie le cumul avec
8 relevés bancaires réels entre 2024 et 2026.

Usage (idempotent — relançable sans effet de bord) :
    python3 backend/scripts/fix_solde_marseille.py [--dry-run]
"""

import argparse
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend.database.connection import SessionLocal  # noqa: E402
from backend.database.models import Transaction  # noqa: E402
from backend.api.utils.balance_utils import recalculate_all_balances  # noqa: E402

MARSEILLE_PROPERTY_ID = 15
CCA_CATEGORY_ID = 18  # « Compte courant d’associé » (group 6, nature=passif)

# Anomalie 1 — la contrepartie manquante.
# ⚠️ Unités : la colonne est stockée en centimes mais le type EuroCents
# (backend/database/money.py) expose des EUROS à l'ORM. On manipule donc des
# euros ici, alors qu'une requête SQL brute sur la même colonne verrait 85030.
APPORT_DATE = date(2024, 7, 11)
APPORT_NOM = "apport compte courant - achats equipement"
APPORT_EUROS = 850.30

# Anomalie 2 — le doublon.
DOUBLON_CSV_ID = 1787
DOUBLON_API_ID = 1996


def fix_apport_manquant(db, dry_run):
    """Ajoute la contrepartie compte courant des 850,30 € payés hors banque."""
    existant = (
        db.query(Transaction)
        .filter(
            Transaction.property_id == MARSEILLE_PROPERTY_ID,
            Transaction.date == APPORT_DATE,
            Transaction.nom == APPORT_NOM,
        )
        .one_or_none()
    )
    if existant is not None:
        print(f"  ⏭️  Apport déjà présent (id {existant.id}) — rien à faire")
        return False

    tx = Transaction(
        date=APPORT_DATE,
        quantite=APPORT_EUROS,
        nom=APPORT_NOM,
        solde=0,  # recalculé en fin de script par recalculate_all_balances
        property_id=MARSEILLE_PROPERTY_ID,
        category_id=CCA_CATEGORY_ID,
        source="csv",
        source_file="trades_Mars_abnb_2024.csv",
    )
    print(f"  ➕ Ajout: {APPORT_DATE} {APPORT_EUROS:+.2f} € « {APPORT_NOM} » (cat {CCA_CATEGORY_ID})")
    if not dry_run:
        db.add(tx)
        db.flush()
        print(f"     -> id {tx.id}")
    return True


def fix_doublon(db, dry_run):
    """Supprime la ligne CSV en double, garde la ligne API (external_id)."""
    csv_tx = db.query(Transaction).filter(Transaction.id == DOUBLON_CSV_ID).one_or_none()
    api_tx = db.query(Transaction).filter(Transaction.id == DOUBLON_API_ID).one_or_none()

    if csv_tx is None:
        print(f"  ⏭️  Ligne CSV {DOUBLON_CSV_ID} déjà supprimée — rien à faire")
        return False
    if api_tx is None:
        print(f"  ❌ Ligne API {DOUBLON_API_ID} introuvable — ABANDON (on ne supprime pas la seule copie restante)")
        raise SystemExit(1)

    # Garde-fou : ne supprimer que si les deux lignes sont bien le même mouvement.
    if not (csv_tx.date == api_tx.date and csv_tx.quantite == api_tx.quantite):
        print(f"  ❌ {DOUBLON_CSV_ID} et {DOUBLON_API_ID} ne sont pas le même mouvement — ABANDON")
        print(f"     csv: {csv_tx.date} {csv_tx.quantite}  |  api: {api_tx.date} {api_tx.quantite}")
        raise SystemExit(1)

    if api_tx.category_id is None and csv_tx.category_id is not None:
        print(f"  🏷️  Report de la catégorie {csv_tx.category_id} sur la ligne API {DOUBLON_API_ID}")
        if not dry_run:
            api_tx.category_id = csv_tx.category_id

    print(f"  ➖ Suppression du doublon: id {DOUBLON_CSV_ID} {csv_tx.date} {csv_tx.quantite:+.2f} € « {csv_tx.nom[:45]} » [csv]")
    print(f"     conservée: id {DOUBLON_API_ID} [api, external_id={api_tx.external_id[:24]}…]")
    if not dry_run:
        db.delete(csv_tx)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="n'écrit rien, affiche seulement")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        def cumul():
            rows = (
                db.query(Transaction)
                .filter(
                    Transaction.property_id == MARSEILLE_PROPERTY_ID,
                    Transaction.is_split_parent == False,  # noqa: E712
                )
                .all()
            )
            return sum(r.quantite for r in rows)  # euros (cf. EuroCents)

        print(f"🚀 [FixSoldeMarseille] début — cumul avant: {cumul():.2f} €  (banque: 2 900,21 €)")
        if args.dry_run:
            print("   (--dry-run : aucune écriture)")

        print("\n1) Contrepartie compte courant manquante (850,30 €)")
        fix_apport_manquant(db, args.dry_run)

        print("\n2) Doublon au recouvrement CSV / Enable Banking (347,28 €)")
        fix_doublon(db, args.dry_run)

        if args.dry_run:
            db.rollback()
            print("\n⏭️  [FixSoldeMarseille] --dry-run : rollback, rien n'a été écrit")
            return

        db.commit()
        print("\n3) Recalcul des soldes cumulés")
        recalculate_all_balances(db, MARSEILLE_PROPERTY_ID)

        final = cumul()
        print(f"\n✅ [FixSoldeMarseille] terminé — cumul après: {final:.2f} €  (banque: 2 900,21 €)")
        if abs(final - 2900.21) >= 0.005:
            print(f"❌ ATTENTION: écart résiduel de {final - 2900.21:+.2f} € avec la banque")
            raise SystemExit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
