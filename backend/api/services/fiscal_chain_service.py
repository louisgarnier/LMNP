"""Assemble la « chaîne fiscale » année par année : valeurs App (moteur) +
Officiel (liasses déposées) + écart, pour les 3 étapes (résultat fiscal,
tirelire déficit, tirelire amortissements). Niveau entité."""
from backend.api.services.fiscal_service import get_fiscal_timeline
from backend.api.services.reconciliation_service import load_liasses

_EPS = 0.005


def build_chain(db, realized=True, imputation_choices=None):
    # realized=True (défaut) = Réel (coût financement à ce jour) ; False = Prévisionnel
    # (plein an). N'affecte que l'année en cours ; années closes identiques.
    # imputation_choices : None => lus en base ; dict explicite pour tests déterministes.
    tl = get_fiscal_timeline(db, realized=realized, imputation_choices=imputation_choices)
    liasses = load_liasses()
    years = sorted(tl.keys())

    chain = {}
    prev_deficit = 0.0
    prev_amort = 0.0
    cumul_amorti = 0.0
    for y in years:
        r = tl[y]
        cumul_amorti += r["amortissements"]
        beneficiaire = (r["imputation_deficits"] + r["imputation_amorts"]
                        + r["resultat_fiscal_imposable"]) > _EPS
        if beneficiaire:
            resultat_fiscal_app = (r["imputation_deficits"] + r["imputation_amorts"]
                                   + r["resultat_fiscal_imposable"])
        else:
            resultat_fiscal_app = -r["deficit_annee"]

        deficit_fin = r["stock_deficit_fin"]
        amort_fin = r["stock_amort_fin"]

        li = liasses.get(y)
        fisc = (li or {}).get("fiscal", {})
        deficit_off = fisc.get("stock_deficit_reportable_fin") if li else None
        amort_off = fisc.get("stock_amort_reporte_reconstitue") if li else None
        if li:
            rf_off = (li["compte_resultat"]["resultat_comptable"]
                      + fisc.get("amortissements_reintegres", 0.0))
        else:
            rf_off = None

        chain[y] = {
            "year": y,
            "brouillon": li is None,
            "profitable": beneficiaire,
            "mode": r.get("imputation_mode", "deficit"),
            "resultat_comptable": round(r["resultat_comptable"], 2),
            "amort_annee": round(r["amortissements"], 2),
            "r_ha": round(r["r_ha"], 2),
            "amort_deductible": round(r["amort_deductible"], 2),
            "amort_mis_de_cote": round(r["amort_differe_annee"], 2),
            "resultat_fiscal_app": round(resultat_fiscal_app, 2),
            # Base imposable de l'exercice (0 tant que les tirelires absorbent le
            # bénéfice). L'écran en fait un cumul : il n'a rien à écrire en dur.
            "resultat_fiscal_imposable": round(r["resultat_fiscal_imposable"], 2),
            "resultat_fiscal_officiel": (round(rf_off, 2) if rf_off is not None else None),
            "deficit_depart": round(prev_deficit, 2),
            "deficit_mouvement": round(deficit_fin - prev_deficit, 2),
            "deficit_fin_app": round(deficit_fin, 2),
            "deficit_fin_officiel": deficit_off,
            "deficit_ecart": (round(deficit_fin - deficit_off, 2) if deficit_off is not None else None),
            "amort_depart": round(prev_amort, 2),
            "amort_impute": round(r["amort_differe_annee"] - (amort_fin - prev_amort), 2),
            "amort_fin_app": round(amort_fin, 2),
            "amort_fin_officiel": amort_off,
            "amort_ecart": (round(amort_fin - amort_off, 2) if amort_off is not None else None),
            # Les trois chiffres de la tirelire amortissements : total amorti =
            # déjà déduit + encore en tirelire. Le « déjà déduit » est le chiffre
            # qui compte à la revente (cf. TIRELIRES-FISCALES-EXPLICATION.md).
            "amort_total_cumul": round(cumul_amorti, 2),
            "amort_deduit_cumul": round(r["amort_deduit_cumul"], 2),
            # Millésimes vivants + péremption, du plus urgent au plus lointain.
            "deficit_millesimes": [
                {"annee": m["annee"], "montant": round(m["montant"], 2),
                 "expire_fin": m["expire_fin"]}
                for m in r["deficit_millesimes"]
            ],
        }
        prev_deficit = deficit_fin
        prev_amort = amort_fin

    return {"years": years, "chain": chain}
