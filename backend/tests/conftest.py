"""
Harnais de tests pytest isolé de la base de production.

⚠️ Avant de modifier ce fichier, lire : ../../docs/workflow/BEST_PRACTICES.md

Ce module fournit deux fixtures pour les tests FUTURS (voir Tâches 4-7) :

- `db_session` : une session SQLAlchemy connectée à une base SQLite en
  mémoire (`sqlite:///:memory:`), avec le schéma complet créé via
  `Base.metadata.create_all`. Une nouvelle base en mémoire est créée pour
  CHAQUE test (scope="function"), et détruite à la fin du test.

- `client` : un `fastapi.testclient.TestClient` pour l'app FastAPI dont la
  dépendance `get_db` est surchargée pour utiliser la MÊME session en
  mémoire que `db_session`. La surcharge est retirée en fin de test.

Ces fixtures ne touchent JAMAIS `backend/database/lmnp.db` (la base de
production). Les 46 fichiers de tests existants qui importent directement
`SessionLocal` / `init_database` continuent de fonctionner tels quels : ces
fixtures sont opt-in (il faut déclarer `db_session` ou `client` en argument
du test) et n'activent aucun patch global (pas d'autouse).

⚠️ QUARANTAINE : les modules de tests hérités qui utilisent la base de
production directement (`SessionLocal` / `next(get_db())`) sont SKIPPÉS à la
collecte — le 2026-07-10, `test_database_complete.py` a effacé la table
`transactions` de production (880 → 4 lignes, restaurée depuis backup, voir
docs/workflow/ERROR_INVESTIGATION.md). Pour les exécuter malgré tout (après
backup !) : LMNP_ALLOW_PROD_DB_TESTS=1 pytest ...

⚠️ QUARANTAINE (bis) : même skip, même variable d'override, pour les scripts
« manuels » hérités qui appellent un serveur en clair sur
`http://localhost:8000` (souvent la même base de production, via l'API HTTP
plutôt que via `SessionLocal`, ex. `test_loan_configs_endpoints_manual.py` qui
peut créer/modifier/supprimer de vrais `loan_configs`). Leur propre docstring
dit explicitement qu'il faut les lancer à la main (« Le serveur backend doit
être démarré / Usage: python backend/tests/xxx.py »), pas via `pytest`. Bloc A
Task 8 (2026-07-10) a aussi constaté que leur signal est trompeur sous pytest :
la plupart de leurs fonctions attrapent leurs propres erreurs et font
`return False` au lieu de `assert`/`raise`, donc pytest les compte PASSED même
quand l'appel réel échoue (ex. `test_generate_compte_resultat` reste "PASSED"
alors que l'endpoint `/compte-resultat/generate` a été supprimé en Task 7).
Voir docs/workflow/ERROR_INVESTIGATION.md pour le détail.
"""

import os
import re
import sys
from pathlib import Path

# Permet d'importer le package `backend` quand pytest est lancé depuis la
# racine du repo (comme le fait le reste de la suite de tests existante).
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.models import Base
from backend.database.connection import get_db
from backend.api.main import app

# Motif des accès directs à la base de production dans un module de test :
# import/usage de SessionLocal ou consommation manuelle du générateur get_db.
_PROD_DB_PATTERN = re.compile(r"\bSessionLocal\b|next\(get_db\(\)\)")

# Motif des scripts « manuels » hérités qui tapent en dur sur un serveur local
# (généralement adossé à la base de production, hors harnais isolé), écrits
# pour être lancés à la main (`python backend/tests/xxx.py`) et non via pytest.
_MANUAL_LIVE_SERVER_PATTERN = re.compile(r'BASE_URL\s*=\s*[\'"]http://localhost:8000')


def pytest_collection_modifyitems(config, items):
    """
    Skippe à la collecte tout module de test qui accède directement à la base
    de production, soit via SQLAlchemy (`SessionLocal`/`get_db()`), soit via
    un appel HTTP en dur sur un serveur local (scripts "manuels" hérités) —
    voir quarantaine dans le docstring du module. Le contenu de chaque
    fichier n'est lu qu'une fois par session pytest.
    """
    if os.environ.get("LMNP_ALLOW_PROD_DB_TESTS") == "1":
        return

    verdict_by_file = {}
    for item in items:
        path = str(item.fspath)
        if path not in verdict_by_file:
            try:
                source = Path(path).read_text(encoding="utf-8", errors="ignore")
            except OSError:
                source = ""
            if _PROD_DB_PATTERN.search(source):
                verdict_by_file[path] = (
                    "Test hérité utilisant la base de PRODUCTION "
                    "(SessionLocal/get_db direct) — quarantaine du "
                    "2026-07-10, voir docs/workflow/ERROR_INVESTIGATION.md. "
                    "Forcer avec LMNP_ALLOW_PROD_DB_TESTS=1 (backup d'abord !)."
                )
            elif _MANUAL_LIVE_SERVER_PATTERN.search(source):
                verdict_by_file[path] = (
                    "Script manuel hérité appelant un serveur local en dur "
                    "(http://localhost:8000, souvent la base de PRODUCTION) — "
                    "prévu pour être lancé à la main, pas via pytest ; "
                    "quarantaine du 2026-07-10 (Bloc A Task 8), voir "
                    "docs/workflow/ERROR_INVESTIGATION.md. Forcer avec "
                    "LMNP_ALLOW_PROD_DB_TESTS=1 (backup d'abord !)."
                )
            else:
                verdict_by_file[path] = None
        if verdict_by_file[path]:
            item.add_marker(pytest.mark.skip(reason=verdict_by_file[path]))


@pytest.fixture
def db_session():
    """
    Fournit une session SQLAlchemy connectée à une base SQLite en mémoire,
    isolée de la base de production. Une base neuve (schéma complet) est
    créée pour chaque test et détruite à la fin de celui-ci.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Activer les foreign keys pour SQLite, comme le fait get_db() en production
    with engine.connect() as connection:
        connection.execute(text("PRAGMA foreign_keys = ON"))

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def client(db_session):
    """
    Fournit un TestClient FastAPI dont la dépendance `get_db` est surchargée
    pour utiliser la session en mémoire de `db_session`, garantissant que
    l'app ne touche jamais backend/database/lmnp.db pendant les tests.

    IMPORTANT: `TestClient(app)` est utilisé SANS context manager (`with`)
    volontairement. Utiliser `with TestClient(app) as client:` déclenche les
    évènements `lifespan`/`startup` de FastAPI, et `main.py` enregistre un
    handler `@app.on_event("startup")` qui appelle `init_database()` — une
    fonction liée au moteur SQLAlchemy de PRODUCTION (`backend/database/
    connection.py::engine`, bindé sur `lmnp.db`), pas à la session en
    mémoire de ce test. Ne pas utiliser le context manager évite tout accès
    (même en lecture/`CREATE TABLE IF NOT EXISTS`) au fichier de production.
    """
    from fastapi.testclient import TestClient

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass  # Le nettoyage/fermeture est géré par la fixture db_session

    app.dependency_overrides[get_db] = _override_get_db

    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        test_client.close()
        app.dependency_overrides.pop(get_db, None)
