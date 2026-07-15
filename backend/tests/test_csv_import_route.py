"""Test HTTP isolé de la route d'import CSV (POST /api/transactions/import).

⚠️ Utilise EXCLUSIVEMENT les fixtures isolées `client` / `db_session` de
backend/tests/conftest.py (base SQLite en mémoire, jamais SessionLocal/get_db
ni un serveur en clair sur BASE_URL) — sinon le module est mis en quarantaine
à la collecte (voir docstring de conftest.py).

Couvre :
- (a) import basique d'un petit CSV → transactions créées avec solde cumulé
  correct et source_file renseigné ;
- (b) verrou anti-régression : 3 lignes littéralement identiques dans un même
  fichier → les 3 sont insérées (pas dédoublonnées intra-lot) — ce sont de
  vraies transactions distinctes (ex. plusieurs encaissements de charges
  locatives de même montant, le même jour) ;
- (c) réimport du même fichier → 0 nouvelle insertion (dédoublonnage vs la
  base, idempotence des réimports).
"""
import io
import json
import os
from pathlib import Path

from backend.database.models import Property, Transaction

TRADES_DIR = Path(__file__).parent.parent / "data" / "input" / "trades"


def _cleanup(filename: str):
    path = TRADES_DIR / filename
    if path.exists():
        os.remove(path)


def _seed_property(db_session, name: str) -> Property:
    prop = Property(name=name)
    db_session.add(prop)
    db_session.flush()
    return prop


def test_import_route_creates_transactions_with_cumulative_balance_and_source_file(client, db_session):
    prop = _seed_property(db_session, "Import-Route-Basique")
    filename = "test_route_basic_import.csv"
    csv_content = "Date;amount;name\n05/01/2024;100;LOYER A\n10/01/2024;-20;CHARGE B"
    mapping = [
        {"file_column": "Date", "db_column": "date"},
        {"file_column": "amount", "db_column": "quantite"},
        {"file_column": "name", "db_column": "nom"},
    ]

    try:
        response = client.post(
            "/api/transactions/import",
            data={"property_id": prop.id, "mapping": json.dumps(mapping)},
            files={"file": (filename, io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["imported_count"] == 2
        assert data["duplicates_count"] == 0

        txs = (
            db_session.query(Transaction)
            .filter(Transaction.property_id == prop.id)
            .order_by(Transaction.date)
            .all()
        )
        assert len(txs) == 2
        assert txs[0].nom == "LOYER A" and txs[0].quantite == 100.0 and txs[0].solde == 100.0
        assert txs[1].nom == "CHARGE B" and txs[1].quantite == -20.0 and txs[1].solde == 80.0
        assert txs[0].source_file == filename
        assert txs[1].source_file == filename
    finally:
        _cleanup(filename)


def test_import_route_keeps_intra_batch_duplicates_then_idempotent_on_reimport(client, db_session):
    # Régression : 3 lignes STRICTEMENT identiques (même date/montant/nom) dans le même
    # fichier CSV — ex. 3 encaissements de charges locatives de 60€ le même jour pour 3
    # locataires différents. L'import ne doit PAS les dédoublonner entre elles.
    prop = _seed_property(db_session, "Import-Route-Doublons")
    filename = "test_route_intra_batch_duplicates.csv"
    csv_content = (
        "Date;amount;name\n"
        "15/02/2024;60;Encaissement charges locatives\n"
        "15/02/2024;60;Encaissement charges locatives\n"
        "15/02/2024;60;Encaissement charges locatives"
    )
    mapping = [
        {"file_column": "Date", "db_column": "date"},
        {"file_column": "amount", "db_column": "quantite"},
        {"file_column": "name", "db_column": "nom"},
    ]

    try:
        # (b) premier import : les 3 lignes identiques doivent TOUTES être insérées.
        response1 = client.post(
            "/api/transactions/import",
            data={"property_id": prop.id, "mapping": json.dumps(mapping)},
            files={"file": (filename, io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        )
        assert response1.status_code == 200, response1.text
        data1 = response1.json()
        assert data1["imported_count"] == 3
        assert data1["duplicates_count"] == 0
        assert db_session.query(Transaction).filter(Transaction.property_id == prop.id).count() == 3

        # (c) réimport du MÊME fichier : les 3 lignes existent déjà en base → 0 nouvelle
        # insertion, idempotence garantie par le dédoublonnage contre la base.
        response2 = client.post(
            "/api/transactions/import",
            data={"property_id": prop.id, "mapping": json.dumps(mapping)},
            files={"file": (filename, io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        )
        assert response2.status_code == 200, response2.text
        data2 = response2.json()
        assert data2["imported_count"] == 0
        assert data2["duplicates_count"] == 3
        assert db_session.query(Transaction).filter(Transaction.property_id == prop.id).count() == 3
    finally:
        _cleanup(filename)
