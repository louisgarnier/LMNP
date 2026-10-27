"""Ventile la tirelire amortissements appartement par appartement.

Le moteur fiscal raisonne au niveau ENTITÉ : il sait combien d'amortissement a
été réellement déduit une année donnée, mais pas sur quel bien. Or c'est
exactement la maille dont on a besoin le jour d'une cession, depuis que la loi
de finances 2025 réintègre les amortissements ADMIS EN DÉDUCTION dans le calcul
de la plus-value.

Règle d'attribution retenue :
  - un seul bien amortissait l'année de la déduction  -> attribution EXACTE
  - plusieurs biens                                    -> prorata de leur
    amortissement de l'année, signalé comme conventionnel (`exact: False`)

Le cas de Louis tombe entièrement dans le premier : les seules déductions ont eu
lieu en 2022 et 2023, quand un seul bien existait. Aucune convention n'est donc
nécessaire aujourd'hui — mais elle le deviendra au premier exercice bénéficiaire
comptant plusieurs biens, et il faudra la faire valider.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

_EPS = 0.005


def repartir_par_bien(amort_par_bien, deduit_par_an, jusqua=None):
    """Découpe total / déduit / tirelire par appartement.

    Args:
        amort_par_bien: {property_id: {annee: montant amorti cette année}}
        deduit_par_an: {annee: amortissement réellement déduit au niveau entité}
        jusqua: n'agréger que les exercices <= cette année (None = tous)

    Returns:
        {
          "total": float, "deduit": float, "tirelire": float,
          "exact": bool, "annees_au_prorata": [int],
          "biens": {property_id: {"total":…, "deduit":…, "tirelire":…}},
        }
    """
    biens = {pid: {"total": 0.0, "deduit": 0.0, "tirelire": 0.0} for pid in amort_par_bien}

    def retenue(annee):
        return jusqua is None or annee <= jusqua

    # 1. Total amorti par bien.
    for pid, par_annee in amort_par_bien.items():
        biens[pid]["total"] = sum(m for a, m in par_annee.items() if retenue(a))

    # 2. Déduit : attribué aux biens qui amortissaient l'année de la déduction.
    annees_au_prorata = []
    for annee, deduit in sorted(deduit_par_an.items()):
        if not retenue(annee) or deduit <= _EPS:
            continue

        actifs = {pid: par_annee.get(annee, 0.0)
                  for pid, par_annee in amort_par_bien.items()
                  if par_annee.get(annee, 0.0) > _EPS}
        if not actifs:
            # Déduction sur un exercice où aucun bien n'amortissait : rien à
            # attribuer. Ne doit pas arriver, mais ne doit pas non plus planter.
            continue

        if len(actifs) == 1:
            biens[next(iter(actifs))]["deduit"] += deduit
        else:
            annees_au_prorata.append(annee)
            base = sum(actifs.values())
            for pid, part in actifs.items():
                biens[pid]["deduit"] += deduit * part / base

    # 3. Ce qui reste en tirelire, bien par bien.
    for b in biens.values():
        b["tirelire"] = b["total"] - b["deduit"]

    return {
        "total": sum(b["total"] for b in biens.values()),
        "deduit": sum(b["deduit"] for b in biens.values()),
        "tirelire": sum(b["tirelire"] for b in biens.values()),
        "exact": not annees_au_prorata,
        "annees_au_prorata": annees_au_prorata,
        "biens": biens,
    }


# ─────────────────────── Accès base ───────────────────────

def amort_par_bien_depuis_base(db):
    """{property_id: {annee: amortissement de l'année}} pour tous les biens.

    Aucun bien codé en dur : on parcourt la table properties, comme le moteur.
    """
    from sqlalchemy import func
    from backend.database.models import AmortizationResult, Transaction, Property

    lignes = (
        db.query(
            Transaction.property_id,
            AmortizationResult.year,
            func.sum(AmortizationResult.amount),
        )
        .join(Transaction, Transaction.id == AmortizationResult.transaction_id)
        .group_by(Transaction.property_id, AmortizationResult.year)
        .all()
    )

    out = {p.id: {} for p in db.query(Property).all()}
    for pid, annee, montant in lignes:
        if pid in out:
            out[pid][annee] = abs(montant or 0.0)
    return out


def repartition(db, jusqua=None, realized=True):
    """Découpage par bien, alimenté par le moteur fiscal et les amortissements."""
    from backend.api.services.fiscal_service import get_fiscal_timeline
    from backend.database.models import Property

    tl = get_fiscal_timeline(db, realized=realized)
    deduit_par_an = {
        y: r["amort_deductible"] + r["imputation_amorts"] for y, r in tl.items()
    }
    amort = amort_par_bien_depuis_base(db)
    res = repartir_par_bien(amort, deduit_par_an, jusqua=jusqua)

    noms = {p.id: p.name for p in db.query(Property).all()}
    res["biens"] = [
        {
            "property_id": pid,
            "nom": noms.get(pid, f"Bien {pid}"),
            "premiere_annee": min(amort[pid]) if amort.get(pid) else None,
            "total": round(v["total"], 2),
            "deduit": round(v["deduit"], 2),
            "tirelire": round(v["tirelire"], 2),
        }
        for pid, v in res["biens"].items()
    ]
    res["biens"].sort(key=lambda b: (b["premiere_annee"] is None, b["premiere_annee"] or 0))
    for k in ("total", "deduit", "tirelire"):
        res[k] = round(res[k], 2)
    res["annees"] = sorted(tl.keys())
    return res
