"""Moteur fiscal LMNP.

Calcule, au niveau de l'ENTITÉ (tous les biens agrégés), la réintégration des
amortissements, le déficit reportable, les amortissements reportés et leurs
cumuls d'une année sur l'autre. Reproduit la mécanique des liasses déposées.

Règle (art. 39 C CGI, LMNP) : un amortissement n'est déductible que dans la
limite du résultat AVANT amortissement (R_ha) ; l'excédent est reporté sans
limite de durée. Un déficit hors-amortissement est reportable N ans (10 par
défaut). Imputation d'un bénéfice : amortissement de l'année d'abord, puis
déficits antérieurs (plus anciens en premier), puis amortissements reportés.
"""
import logging

logger = logging.getLogger(__name__)

_EPS = 0.005  # seuil de purge des lignes de stock résiduelles (< 0,5 centime)


def compute_fiscal_timeline(years_data, deficit_report_years, amort_report_years):
    """Déroule l'algorithme fiscal sur une suite chronologique d'exercices.

    Args:
        years_data: liste ORDONNÉE par année croissante de dicts
            {"year": int, "resultat_comptable": float, "amortissements": float}.
            `amortissements` ≥ 0 (valeur absolue de la charge d'amortissement).
        deficit_report_years: durée de report du déficit (années). Un déficit
            millésimé Y est imputable jusqu'à Y + deficit_report_years inclus.
        amort_report_years: durée de report des amortissements, ou None = illimité.

    Returns:
        dict {year: résultat de l'exercice} — voir clés ci-dessous.
    """
    deficits = []  # [ [year, remaining], ... ] millésimés, FIFO
    amorts = []    # [ [year, remaining], ... ] millésimés, FIFO
    results = {}

    for row in years_data:
        year = row["year"]
        amort_annee = abs(row["amortissements"])
        r_ha = row["resultat_comptable"] + amort_annee  # résultat avant amortissement

        # Purge des stocks expirés (au titre de l'exercice courant).
        deficits = [d for d in deficits if (year - d[0]) <= deficit_report_years]
        if amort_report_years is not None:
            amorts = [a for a in amorts if (year - a[0]) <= amort_report_years]

        # Amortissement de l'année : déductible dans la limite de R_ha positif.
        deductible = min(amort_annee, max(0.0, r_ha))
        amort_differe_annee = amort_annee - deductible
        result_after = r_ha - deductible  # >= 0 si R_ha > 0, sinon = R_ha (< 0)

        imputation_deficits = 0.0
        imputation_amorts = 0.0
        deficit_annee = 0.0

        if result_after > _EPS:
            profit = result_after
            # 1) imputer les déficits antérieurs, plus anciens d'abord
            for d in sorted(deficits, key=lambda x: x[0]):
                if profit <= _EPS:
                    break
                take = min(d[1], profit)
                d[1] -= take
                profit -= take
                imputation_deficits += take
            # 2) imputer les amortissements reportés antérieurs, plus anciens d'abord
            for a in sorted(amorts, key=lambda x: x[0]):
                if profit <= _EPS:
                    break
                take = min(a[1], profit)
                a[1] -= take
                profit -= take
                imputation_amorts += take
            resultat_fiscal_imposable = max(0.0, profit)
        else:
            # Déficit de l'exercice (hors amortissement de l'année déjà écarté).
            deficit_annee = -result_after if result_after < 0 else 0.0
            if deficit_annee > _EPS:
                deficits.append([year, deficit_annee])
            resultat_fiscal_imposable = 0.0

        # Amortissement différé de l'année rejoint le stock.
        if amort_differe_annee > _EPS:
            amorts.append([year, amort_differe_annee])

        # Purge des lignes soldées.
        deficits = [d for d in deficits if d[1] > _EPS]
        amorts = [a for a in amorts if a[1] > _EPS]

        results[year] = {
            "year": year,
            "resultat_comptable": row["resultat_comptable"],
            "amortissements": amort_annee,
            "r_ha": r_ha,
            "amort_deductible": deductible,
            "amort_differe_annee": amort_differe_annee,
            "deficit_annee": deficit_annee,
            "imputation_deficits": imputation_deficits,
            "imputation_amorts": imputation_amorts,
            "resultat_fiscal_imposable": resultat_fiscal_imposable,
            "stock_deficit_fin": sum(d[1] for d in deficits),
            "stock_amort_fin": sum(a[1] for a in amorts),
        }

    return results
