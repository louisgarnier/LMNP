"""Assemble la « chaîne fiscale » année par année : valeurs App (moteur) +
Officiel (liasses déposées) + écart, pour les 3 étapes (résultat fiscal,
tirelire déficit, tirelire amortissements). Niveau entité."""
from backend.api.services.fiscal_service import get_fiscal_timeline, entity_year_range
from backend.api.services.reconciliation_service import load_liasses

_EPS = 0.005


def build_chain(db):
    tl = get_fiscal_timeline(db)
    liasses = load_liasses()
    years = sorted(tl.keys())

    chain = {}
    prev_deficit = 0.0
    prev_amort = 0.0
    for y in years:
        r = tl[y]
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
            drl = fisc.get("deficit_reportable_de_lannee", 0.0)
            rf_off = -drl if drl else 0.0
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
        }
        prev_deficit = deficit_fin
        prev_amort = amort_fin

    return {"years": years, "chain": chain}
