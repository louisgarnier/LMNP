from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database.models import FiscalSettings, FiscalImputationChoice
from backend.api.models import (
    FiscalYearResponse, FiscalSettingsResponse, FiscalSettingsUpdate,
    ImputationChoiceUpdate,
)
from backend.api.services.fiscal_service import (
    get_fiscal, get_fiscal_timeline, entity_year_range,
)
from backend.api.services.fiscal_chain_service import build_chain
from backend.api.services.fiscal_repartition_service import repartition
from backend.api.services.bilan_entite_service import bilan_cerfa

router = APIRouter()

# Pas de constante de « reprise » : l'application chaîne depuis le premier
# exercice à partir des transactions. Cf. ADR « L'application est la source de
# vérité fiscale ; la liasse est un contrôle » (2026-07-29).
_MODES = {"deficit", "amort"}


@router.get("/fiscal/calculate", response_model=FiscalYearResponse)
def calculate_fiscal(year: int = Query(...), db: Session = Depends(get_db)):
    try:
        return get_fiscal(db, year)
    except KeyError:
        raise HTTPException(404, f"Aucune donnée fiscale pour l'exercice {year}")


@router.get("/fiscal/timeline")
def fiscal_timeline(db: Session = Depends(get_db)):
    tl = get_fiscal_timeline(db)
    return {"years": entity_year_range(db), "results": tl}


@router.get("/fiscal/settings", response_model=FiscalSettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    s = db.query(FiscalSettings).order_by(FiscalSettings.id).first()
    if s is None:
        s = FiscalSettings(deficit_report_years=10, amort_report_years=None)
        db.add(s); db.commit(); db.refresh(s)
    return s


@router.put("/fiscal/settings", response_model=FiscalSettingsResponse)
def put_settings(body: FiscalSettingsUpdate, db: Session = Depends(get_db)):
    s = db.query(FiscalSettings).order_by(FiscalSettings.id).first()
    if s is None:
        s = FiscalSettings(); db.add(s)
    if body.deficit_report_years is not None:
        s.deficit_report_years = body.deficit_report_years
    if body.amort_illimite is True:
        s.amort_report_years = None
    elif body.amort_report_years is not None:
        s.amort_report_years = body.amort_report_years
    db.commit(); db.refresh(s)
    return s


@router.get("/fiscal/chaine")
def fiscal_chaine(
    realized: bool = Query(True, description="True = Réel (défaut) ; False = Prévisionnel (plein an). N'affecte que l'année en cours."),
    db: Session = Depends(get_db),
):
    return build_chain(db, realized=realized)


@router.put("/fiscal/imputation/{year}")
def put_imputation(
    year: int,
    body: ImputationChoiceUpdate,
    realized: bool = Query(True, description="Base du recalcul renvoyé (True = Réel, défaut ; False = Prévisionnel)."),
    db: Session = Depends(get_db),
):
    if body.mode not in _MODES:
        raise HTTPException(400, f"mode invalide: {body.mode}")
    row = db.query(FiscalImputationChoice).filter_by(year=year).first()
    if row is None:
        row = FiscalImputationChoice(year=year, mode=body.mode)
        db.add(row)
    else:
        row.mode = body.mode
    db.commit()
    return build_chain(db, realized=realized)


@router.get("/fiscal/repartition")
def fiscal_repartition(
    jusqua: int = Query(None, description="N'agréger que les exercices <= cette année (défaut : tous)."),
    realized: bool = Query(True, description="True = Réel (défaut) ; False = Prévisionnel."),
    db: Session = Depends(get_db),
):
    """Ventile total amorti / déjà déduit / encore en tirelire, appartement par appartement."""
    return repartition(db, jusqua=jusqua, realized=realized)


@router.get("/fiscal/bilan-cerfa")
def fiscal_bilan_cerfa(
    year: int = Query(..., description="Exercice à présenter."),
    realized: bool = Query(True, description="True = Réel (défaut) ; False = Prévisionnel."),
    db: Session = Depends(get_db),
):
    """Bilan 2033-A de l'entité : ce que l'application calcule, face à la liasse déposée."""
    return bilan_cerfa(db, year, realized=realized)
