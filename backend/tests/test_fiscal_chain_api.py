"""Contrat des routes chaîne + imputation (validation d'entrée).

Le brief d'origine proposait `TestClient(app)` au niveau module (base de
PRODUCTION via `get_db`) : à l'exécution, la garde de quarantaine prod de
`conftest.py` (event `connect` attaché à `backend.database.connection.engine`)
bloque cet accès avec une `RuntimeError` explicite — la dépendance `get_db`
est résolue par FastAPI avant même le corps de la route, donc même le test
« PUT mode invalide » (qui n'écrit rien) déclenchait la garde.

On utilise donc les fixtures isolées `client`/`db_session` de `conftest.py`
(base SQLite en mémoire, schéma complet, jetable par test) : aucun accès à
`backend/database/lmnp.db`, conformément à la garde de quarantaine et à la
consigne de ne pas persister de choix d'imputation en base réelle. Le
recalcul de la chaîne sur un mode valide est déjà couvert au niveau service
par `test_fiscal_chain_service.py` (Task 3) — non re-testé ici.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_get_chaine_expose_years_et_chain(client):
    r = client.get("/api/fiscal/chaine")
    assert r.status_code == 200
    body = r.json()
    assert "years" in body and "chain" in body and "reprise" in body


def test_put_imputation_rejette_mode_invalide(client):
    r = client.put("/api/fiscal/imputation/2023", json={"mode": "n_importe_quoi"})
    assert r.status_code == 400
