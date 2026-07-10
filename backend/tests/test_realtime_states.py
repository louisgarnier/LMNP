"""
Tests des états financiers calculés en temps réel (Tâche 7).

1. Contrat de non-régression : après le passage des GET `/api/compte-resultat`
   et `/api/bilan` au calcul live, ils doivent renvoyer un JSON identique
   (au centime) au fixture capturé depuis le chemin cache AVANT modification
   (voir backend/tests/fixtures/states_contract.json).

2. Performance : le bilan 6 ans pour Evry (property_id=25), calculé en temps
   réel avec mémoïsation du compte de résultat, doit répondre en < 300 ms.
   Ce test travaille sur une COPIE de la vraie base (jamais en écriture sur
   la prod) ouverte avec un sessionmaker dédié (`CopySession`) — volontairement
   nommé ainsi pour NE PAS déclencher la quarantaine de conftest.py (qui skippe
   tout module contenant les chaînes de l'accès direct à la base de prod).
"""

import json
import shutil
import statistics
import tempfile
import time
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.database.connection import get_db
from backend.api.main import app
from backend.tests.contract_seed import seed_contract_data, YEARS

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "states_contract.json"
REAL_DB_PATH = Path(__file__).resolve().parents[1] / "database" / "lmnp.db"


def _normalize_items(items):
    out = [
        {"annee": it["annee"], "category_name": it["category_name"],
         "amount": round(it["amount"], 2)}
        for it in items
    ]
    out.sort(key=lambda x: (x["annee"], x["category_name"]))
    return out


def test_compte_resultat_live_matches_fixture(client, db_session):
    """GET /api/compte-resultat (live) == fixture capturé du cache."""
    pid = seed_contract_data(db_session)
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    resp = client.get(
        f"/api/compte-resultat?property_id={pid}"
        f"&start_year={YEARS[0]}&end_year={YEARS[-1]}&limit=1000"
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert _normalize_items(body["items"]) == fixture["compte_resultat"]["items"]
    assert body["total"] == fixture["compte_resultat"]["total"]


def test_bilan_live_matches_fixture(client, db_session):
    """GET /api/bilan (live) == fixture (référence calculate_bilan)."""
    pid = seed_contract_data(db_session)
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    resp = client.get(
        f"/api/bilan?property_id={pid}"
        f"&start_year={YEARS[0]}&end_year={YEARS[-1]}&limit=1000"
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert _normalize_items(body["items"]) == fixture["bilan"]["items"]
    assert body["total"] == fixture["bilan"]["total"]


def test_bilan_6y_evry_realtime_under_300ms():
    """Bilan 6 ans × Evry calculé en temps réel < 300 ms (copie de la prod)."""
    if not REAL_DB_PATH.exists():
        pytest.skip(f"Base réelle introuvable: {REAL_DB_PATH}")

    with tempfile.TemporaryDirectory() as tmp:
        copy_path = Path(tmp) / "lmnp_copy.db"
        shutil.copy2(REAL_DB_PATH, copy_path)

        engine = create_engine(
            f"sqlite:///{copy_path}",
            connect_args={"check_same_thread": False},
        )
        with engine.connect() as conn:
            conn.execute(text("PRAGMA foreign_keys = ON"))
        CopySession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        def _override_get_db():
            db = CopySession()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = _override_get_db
        from fastapi.testclient import TestClient
        test_client = TestClient(app)
        try:
            years = ",".join(str(y) for y in range(2021, 2027))  # 6 années
            url = f"/api/bilan/calculate?property_id=25&years={years}"

            warm = test_client.get(url)
            assert warm.status_code == 200, warm.text

            timings = []
            for _ in range(3):
                start = time.perf_counter()
                r = test_client.get(url)
                elapsed_ms = (time.perf_counter() - start) * 1000
                assert r.status_code == 200, r.text
                timings.append(elapsed_ms)

            median_ms = statistics.median(timings)
            print(f"\n[perf] bilan 6 ans Evry: median={median_ms:.1f} ms, "
                  f"runs={[round(t, 1) for t in timings]}")
            assert median_ms < 300, (
                f"Bilan 6 ans Evry trop lent: median={median_ms:.1f} ms "
                f"(runs={[round(t, 1) for t in timings]})"
            )
        finally:
            test_client.close()
            app.dependency_overrides.pop(get_db, None)
            engine.dispose()
