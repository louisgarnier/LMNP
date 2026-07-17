"""Tests des routes fiscales.

GET (lecture seule) : contre un moteur read-only ouvert directement sur la base
réelle (mode=ro), même motif sanctionné que test_fiscal_service_integration.py /
test_amortization_evry_golden.py — la garde de quarantaine ne vise que l'engine
de production, pas cet engine distinct. Les valeurs réelles (2024) sont ainsi
validées de bout en bout.
PUT (écriture) : contre une base isolée en mémoire — aucune écriture en prod.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.api.main import app
from backend.database.connection import get_db
from backend.database.models import Base, FiscalSettings

PROD_DB = (Path(__file__).parent.parent / "database" / "lmnp.db").resolve()
_ro_engine = create_engine(f"sqlite:///file:{PROD_DB}?mode=ro&uri=true",
                           connect_args={"uri": True})
_ROSession = sessionmaker(bind=_ro_engine)

client = TestClient(app)


def _ro_db():
    db = _ROSession()
    try:
        yield db
    finally:
        db.close()


def test_get_calculate_2024():
    app.dependency_overrides[get_db] = _ro_db
    try:
        r = client.get("/api/fiscal/calculate", params={"year": 2024})
        assert r.status_code == 200
        body = r.json()
        assert abs(body["deficit_annee"] - 5479.12) < 1.0
        assert abs(body["resultat_fiscal_imposable"]) < 0.1
    finally:
        app.dependency_overrides.clear()


def test_get_calculate_annee_hors_plage_404():
    app.dependency_overrides[get_db] = _ro_db
    try:
        r = client.get("/api/fiscal/calculate", params={"year": 1999})
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_get_settings_defaut():
    app.dependency_overrides[get_db] = _ro_db
    try:
        r = client.get("/api/fiscal/settings")
        assert r.status_code == 200
        assert r.json()["deficit_report_years"] == 10
    finally:
        app.dependency_overrides.clear()


def test_put_settings_modifie_la_duree():
    mem = create_engine("sqlite:///:memory:",
                        connect_args={"check_same_thread": False},
                        poolclass=StaticPool)
    Base.metadata.create_all(mem, tables=[FiscalSettings.__table__])
    MemSession = sessionmaker(bind=mem)
    seed = MemSession()
    seed.add(FiscalSettings(deficit_report_years=10, amort_report_years=None))
    seed.commit()
    seed.close()

    def _mem_db():
        db = MemSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _mem_db
    try:
        r = client.put("/api/fiscal/settings", json={"deficit_report_years": 8})
        assert r.status_code == 200
        assert r.json()["deficit_report_years"] == 8
        r = client.get("/api/fiscal/settings")
        assert r.json()["deficit_report_years"] == 8
    finally:
        app.dependency_overrides.clear()


def test_put_settings_amort_illimite():
    mem = create_engine("sqlite:///:memory:",
                        connect_args={"check_same_thread": False},
                        poolclass=StaticPool)
    Base.metadata.create_all(mem, tables=[FiscalSettings.__table__])
    MemSession = sessionmaker(bind=mem)
    seed = MemSession()
    seed.add(FiscalSettings(deficit_report_years=10, amort_report_years=15))
    seed.commit()
    seed.close()

    def _mem_db():
        db = MemSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _mem_db
    try:
        r = client.put("/api/fiscal/settings", json={"amort_illimite": True})
        assert r.status_code == 200
        assert r.json()["amort_report_years"] is None
    finally:
        app.dependency_overrides.clear()


def test_get_settings_cree_defaut_si_absent():
    mem = create_engine("sqlite:///:memory:",
                        connect_args={"check_same_thread": False},
                        poolclass=StaticPool)
    Base.metadata.create_all(mem, tables=[FiscalSettings.__table__])
    MemSession = sessionmaker(bind=mem)

    def _mem_db():
        db = MemSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _mem_db
    try:
        r = client.get("/api/fiscal/settings")
        assert r.status_code == 200
        assert r.json()["deficit_report_years"] == 10
        assert r.json()["amort_report_years"] is None
    finally:
        app.dependency_overrides.clear()
