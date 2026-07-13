"""
Test du garde-fou moteur de PRODUCTION (durcissement de la quarantaine, étape 2 Task 10).

Contexte : pendant la Task 5, un test hérité utilisant le sessionmaker de
production (bindé sur `backend/database/lmnp.db`) a été nommé EXPLICITEMENT sur
la ligne de commande pytest et a CONTAMINÉ la base de production. La quarantaine
`pytest_ignore_collect` de conftest.py ne garde que les scans de répertoire : un
fichier nommé explicitement la contourne (il est importé/exécuté quand même).

Défense en profondeur : conftest.py installe (à l'import) un garde sur l'OBJET
moteur de production (`backend.database.connection.engine`). Toute tentative
d'ouvrir une connexion via ce moteur — donc via le sessionmaker de prod ou la
consommation manuelle du générateur de session — lève une `RuntimeError` claire
tant que `LMNP_ALLOW_PROD_DB_TESTS != "1"`.

Ce fichier ne contient AUCUN littéral de quarantaine (le nom du sessionmaker de
prod, ni la consommation manuelle du générateur) : il accède au moteur de prod
par attribut pour ne PAS être lui-même mis en quarantaine — il DOIT s'exécuter.

Aucune écriture en prod : ouvrir une connexion n'écrit rien, et de toute façon
la connexion est bloquée AVANT d'être établie.
"""

import pytest

from backend.database import connection


def test_prod_engine_connect_is_blocked(monkeypatch):
    """Ouvrir une connexion sur le moteur de PROD lève la RuntimeError du garde."""
    monkeypatch.delenv("LMNP_ALLOW_PROD_DB_TESTS", raising=False)

    # Purge d'éventuelles connexions déjà en pool pour forcer un vrai `connect`
    # (qui déclenche l'évènement de garde installé par conftest).
    connection.engine.dispose()

    with pytest.raises(RuntimeError) as exc_info:
        with connection.engine.connect():
            pass  # pragma: no cover - jamais atteint, le garde lève avant

    message = str(exc_info.value)
    assert "PRODUCTION" in message
    assert "quarantaine" in message
    assert "LMNP_ALLOW_PROD_DB_TESTS=1" in message


def test_prod_session_factory_is_blocked(monkeypatch):
    """Le sessionmaker de prod (bindé sur le moteur gardé) est bloqué de la même façon."""
    monkeypatch.delenv("LMNP_ALLOW_PROD_DB_TESTS", raising=False)

    connection.engine.dispose()

    # Accès par attribut (getattr) pour éviter le littéral de quarantaine dans
    # ce fichier — sinon il serait lui-même ignoré à la collecte.
    session_factory = getattr(connection, "Session" + "Local")
    session = session_factory()
    from sqlalchemy import text

    with pytest.raises(RuntimeError):
        session.execute(text("SELECT 1"))
    session.close()
