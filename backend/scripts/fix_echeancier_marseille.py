"""
Remet à jour l'échéancier du prêt Marseille (property_id=15) après la MODULATION
de février 2026, et rééquilibre le bilan 2026.

--- CE QUI S'EST PASSÉ -------------------------------------------------------

Le prêt « mars » est un PRET MODULIMMO — un prêt modulable. En février 2026, la
mensualité est passée de 931,22 € à 892,71 € puis 892,48 €, soit 38,50 € de
moins par mois. Ce n'est PAS une renégociation : le PDF Crédit Mutuel du
17/07/2026 confirme « Taux fixe actuel (hors assurance) : 4,35 % » — le taux
d'origine, inchangé. Louis a modulé sa mensualité à la baisse ; le prêt
s'allonge et le capital s'amortit moins vite.

L'app ne l'a jamais su : elle a continué d'appliquer l'ancien tableau
(fichier docs/files/appartements/Marseille/Tableau_Ammort_Crédit_Mars_ABNB.xlsx,
daté du 13/01/2026, donc antérieur à la modulation). Pendant 6 mois elle a
amorti 217,71 € de capital de trop, ce qui déséquilibrait le bilan 2026 de
231,18 € — l'écart entre l'échéancier théorique (6 517,74 €) et les
prélèvements réels (6 286,56 €) sur janvier→juillet.

--- SOURCES ------------------------------------------------------------------

1) Août 2026 → mars 2039 : extraction directe du PDF fourni par Louis
   (~/Downloads/credit mars airbnb.pdf), 152 échéances. Extraction VALIDÉE :
   les 4 totaux recalculés retombent au centime sur les totaux imprimés par le
   Crédit Mutuel (capital 102 709,81 / intérêts 31 063,30 / assurance 1 528,08
   / total 135 301,19).

2) Février → juillet 2026 : ABSENTS du PDF (qui ne liste que le futur), donc
   RECONSTRUITS. La reconstruction n'est pas une estimation : elle est contrainte
   aux deux bouts et vérifiée.
   - point de départ : capital dû avant le 05/02/2026 = 105 718,12 € (l'ancien
     échéancier était encore exact en janvier — le prélèvement de janvier,
     931,22 €, correspond au centime),
   - taux 4,35 % (confirmé par le PDF),
   - mensualités réellement débitées en banque (892,71 ×2 puis 892,48 ×4),
   - point d'arrivée : capital dû au 05/08/2026 = 102 709,81 €, soit l'« Encours »
     imprimé sur le PDF — une donnée indépendante que la reconstruction doit
     retrouver, et qu'elle retrouve exactement.

   La répartition de l'assurance sur ces 6 mois n'est pas déterminée de façon
   unique (88 combinaisons retombent sur l'encours), MAIS c'est sans effet sur
   la comptabilité : sur ces 88 solutions, le capital remboursé est invariant
   (3 008,31 € au centime) et les intérêts — le déductible fiscal — varient de
   6 centimes (2 272,19 → 2 272,25 €). On retient la combinaison la plus proche
   des 12,39 €/mois annoncés par le PDF à partir d'août.

--- PORTÉE -------------------------------------------------------------------

Remplace toutes les échéances du prêt « mars » à partir du 2026-02-05. Les
échéances antérieures (2024-04 → 2026-01) sont EXACTES (vérifiées contre les
prélèvements bancaires) et ne sont pas touchées.

Usage (idempotent) :
    python3 backend/scripts/fix_echeancier_marseille.py [--dry-run]
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend.database.connection import SessionLocal  # noqa: E402
from backend.database.models import LoanPayment  # noqa: E402

MARSEILLE = 15
LOAN_NAME = "mars"
PDF = Path.home() / "Downloads" / "credit mars airbnb.pdf"
CUTOVER = date(2026, 2, 5)  # 1re échéance modulée

TAUX_MENSUEL = 0.0435 / 12
CAPITAL_DU_AVANT_FEVRIER = 105718.12
ENCOURS_PDF = 102709.81  # capital dû au 05/08/2026, imprimé sur le PDF
PRELEVEMENTS_REELS = {2: 892.71, 3: 892.71, 4: 892.48, 5: 892.48, 6: 892.48, 7: 892.48}

# Totaux imprimés sur le PDF — servent de contrôle de l'extraction.
PDF_TOTAUX = {"capital": 102709.81, "interets": 31063.30, "assurance": 1528.08, "total": 135301.19}


def extraire_pdf():
    """Échéances août 2026 → mars 2039, lues dans le PDF. Validées par leurs totaux."""
    txt = subprocess.run(
        ["pdftotext", "-layout", str(PDF), "-"], capture_output=True, text=True, check=True
    ).stdout
    rx = re.compile(
        r"^\s*(\d{2}/\d{2}/\d{4})\s+([\d ]+,\d{2})\s+([\d ]+,\d{2})\s+"
        r"([\d ]+,\d{2})\s+([\d ]+,\d{2})\s+([\d ]+,\d{2})\s*$"
    )
    def n(s):
        return float(s.replace(" ", "").replace(",", "."))

    rows = []
    for ligne in txt.splitlines():
        m = rx.match(ligne)
        if m:
            rows.append({
                "date": datetime.strptime(m.group(1), "%d/%m/%Y").date(),
                "capital": n(m.group(3)),
                "interets": n(m.group(4)),
                "assurance": n(m.group(5)),
                "total": n(m.group(6)),
            })
    # Contrôle : l'extraction doit reproduire les totaux imprimés par la banque.
    for cle, attendu in PDF_TOTAUX.items():
        k = {"interets": "interets", "assurance": "assurance", "capital": "capital", "total": "total"}[cle]
        calc = round(sum(r[k] for r in rows), 2)
        if abs(calc - attendu) > 0.02:
            raise SystemExit(f"❌ extraction PDF invalide : {cle} = {calc} au lieu de {attendu}")
    return rows


def reconstruire_fev_juillet():
    """Février → juillet 2026, contraints par l'encours du PDF."""
    def simule(a, b):
        C = CAPITAL_DU_AVANT_FEVRIER
        out = []
        for m in (2, 3, 4, 5, 6, 7):
            ins = a if m in (2, 3) else b
            interets = round(C * TAUX_MENSUEL, 2)
            capital = round(PRELEVEMENTS_REELS[m] - ins - interets, 2)
            out.append({"date": date(2026, m, 5), "capital": capital, "interets": interets,
                        "assurance": ins, "total": PRELEVEMENTS_REELS[m]})
            C = round(C - capital, 2)
        return C, out

    # Toutes les combinaisons d'assurance qui retrouvent l'encours du PDF.
    sols = [(a / 100, b / 100)
            for a in range(1100, 1450) for b in range(1100, 1450)
            if abs(simule(a / 100, b / 100)[0] - ENCOURS_PDF) < 0.005]
    if not sols:
        raise SystemExit("❌ aucune reconstruction ne retrouve l'encours du PDF — hypothèses à revoir")

    # Invariants : le capital doit être identique partout, les intérêts à ~1 centime.
    interets = [round(sum(l["interets"] for l in simule(a, b)[1]), 2) for a, b in sols]
    capitaux = [round(sum(l["capital"] for l in simule(a, b)[1]), 2) for a, b in sols]
    if max(capitaux) - min(capitaux) > 0.005:
        raise SystemExit(f"❌ capital non déterminé ({min(capitaux)}..{max(capitaux)}) — refus d'inventer")
    if max(interets) - min(interets) > 0.50:
        raise SystemExit(f"❌ intérêts non déterminés ({min(interets)}..{max(interets)}) — refus d'inventer")

    a, b = min(sols, key=lambda s: abs(s[0] - 12.39) + abs(s[1] - 12.39))
    fin, lignes = simule(a, b)
    print(f"  reconstruction fév→juil : {len(sols)} solutions retrouvent l'encours ; "
          f"capital invariant ({capitaux[0]:.2f} €), intérêts à {max(interets)-min(interets):.2f} € près")
    print(f"  assurance retenue : {a:.2f} (fév-mars) / {b:.2f} (avr-juil) — PDF : 12,39 à partir d'août")
    print(f"  capital dû reconstruit au 05/08/2026 : {fin:.2f}  |  encours PDF : {ENCOURS_PDF:.2f}  "
          f"écart {fin - ENCOURS_PDF:+.2f}")
    return lignes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not PDF.exists():
        raise SystemExit(f"❌ PDF introuvable : {PDF}")

    print("🚀 [FixEcheancierMarseille] modulation MODULIMMO de février 2026\n")
    futur = extraire_pdf()
    print(f"  PDF : {len(futur)} échéances {futur[0]['date']} → {futur[-1]['date']} "
          f"— 4 totaux conformes aux totaux imprimés ✅")
    passe = reconstruire_fev_juillet()

    nouvelles = passe + futur
    db = SessionLocal()
    try:
        anciennes = (
            db.query(LoanPayment)
            .filter(LoanPayment.property_id == MARSEILLE, LoanPayment.date >= CUTOVER)
            .all()
        )
        print(f"\n  remplacement : {len(anciennes)} anciennes échéances (≥ {CUTOVER}) "
              f"→ {len(nouvelles)} nouvelles")
        # Contrôle : ne jamais toucher l'historique antérieur, vérifié contre la banque.
        avant = (
            db.query(LoanPayment)
            .filter(LoanPayment.property_id == MARSEILLE, LoanPayment.date < CUTOVER)
            .count()
        )
        print(f"  intactes : {avant} échéances antérieures à {CUTOVER}")

        if not args.dry_run:
            for e in anciennes:
                db.delete(e)
            db.flush()
            for l in nouvelles:
                db.add(LoanPayment(
                    property_id=MARSEILLE, date=l["date"], capital=l["capital"],
                    interest=l["interets"], insurance=l["assurance"], total=l["total"],
                    loan_name=LOAN_NAME,
                ))
            db.commit()
            print("\n✅ [FixEcheancierMarseille] échéancier remplacé")
        else:
            db.rollback()
            print("\n⏭️  --dry-run : rien n'a été écrit")
    finally:
        db.close()


if __name__ == "__main__":
    main()
