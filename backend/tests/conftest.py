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
"""

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
