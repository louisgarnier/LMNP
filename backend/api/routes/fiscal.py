from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database.models import FiscalSettings
from backend.api.models import (
    FiscalYearResponse, FiscalSettingsResponse, FiscalSettingsUpdate,
)
from backend.api.services.fiscal_service import (
    get_fiscal, get_fiscal_timeline, entity_year_range,
)

router = APIRouter()


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
