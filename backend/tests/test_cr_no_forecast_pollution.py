"""
Régression (refonte « toggle Réel/Prévisionnel ») :

Le compte de résultat affiché doit TOUJOURS refléter les montants réels, même
quand les prévisions sont activées (prorata_enabled=True) et qu'un « objectif »
(AnnualForecastConfig) supérieur au réel est configuré pour l'année en cours.

Avant la refonte, `calculate_compte_resultat(..., skip_prorata=False)` appliquait
la règle cachée MAX(réel, prévu) : un loyer réellement encaissé de 6 000 € en
2026 s'affichait à hauteur de l'objectif (ex. 20 000 €) directement dans le vrai
compte de résultat, faussant le résultat de l'exercice. Ce bloc a été supprimé.

⚠️ Harnais isolé (fixtures `db_session` en mémoire) : ne touche jamais
backend/database/lmnp.db.
"""

from datetime import date, datetime

from backend.database.models import (
    Property,
    Transaction,
    Category,
    CategoryGroup,
    ProRataSettings,
    AnnualForecastConfig,
)
from backend.api.services.category_service import NATURE_BY_LABEL
from backend.api.services.enrichment_service import update_transaction_classification
from backend.api.services.compte_resultat_service import calculate_compte_resultat


CATEGORY_NAME = "Loyers hors charge encaissés"
REAL_RENT = 6000.0          # loyer réellement encaissé sur l'année en cours
OBJECTIVE = 20000.0         # objectif configuré, volontairement > réel


def _seed_rent_with_high_objective(client, db_session, year: int) -> int:
    """Propriété avec un loyer réel `REAL_RENT` classé pour `year`, prévisions
    activées et un objectif `OBJECTIVE` (> réel) sur la catégorie loyers.

    Le mapping CR et la config level_3 passent par l'API (table de liaison), le
    reste directement par l'ORM.
    """
    import json

    prop = Property(name="TEST_CR_NO_POLLUTION", address="1 rue du Test")
    db_session.add(prop)
    db_session.flush()
    pid = prop.id

    # Référentiel : groupe/catégorie pour le label "LOYERS" (nature "Produits")
    nature = NATURE_BY_LABEL["Produits"]
    group = CategoryGroup(label="Produits", nature=nature)
    db_session.add(group)
    db_session.flush()
    db_session.add(Category(label="LOYERS", group_id=group.id, is_custom=False))

    # Transaction de loyer réelle, classée via le moteur vivant
    tx = Transaction(
        property_id=pid, date=date(year, 1, 10), quantite=REAL_RENT,
        nom="Loyers année en cours", solde=REAL_RENT, source_file="test",
    )
    db_session.add(tx)
    db_session.flush()
    update_transaction_classification(
        db_session, tx, level_1="LOYERS", level_2="Produits", level_3="Produits"
    )

    # Prévisions activées + objectif élevé (le piège de l'ancien MAX)
    db_session.add(ProRataSettings(
        property_id=pid, prorata_enabled=True, forecast_enabled=True, forecast_years=3
    ))
    db_session.add(AnnualForecastConfig(
        property_id=pid, year=year, level_1=CATEGORY_NAME,
        target_type="compte_resultat",
        base_annual_amount=OBJECTIVE, annual_growth_rate=0.0,
    ))
    db_session.commit()

    # Config CR (natures autorisées) + mapping catégorie -> label LOYERS via API
    resp = client.put(
        "/api/compte-resultat/config",
        params={"property_id": pid},
        json={"level_3_values": json.dumps(["Produits"])},
    )
    assert resp.status_code == 200, resp.text
    resp = client.post(
        "/api/compte-resultat/mappings",
        json={
            "property_id": pid,
            "category_name": CATEGORY_NAME,
            "type": "Produits d'exploitation",
            "level_1_values": json.dumps(["LOYERS"]),
        },
    )
    assert resp.status_code == 201, resp.text
    return pid


def test_cr_shows_real_not_objective_current_year(client, db_session):
    """Année en cours, prévisions ON, objectif 20 000 € > réel 6 000 €.

    Le CALCUL affiché (skip_prorata=False, chemin de l'écran) doit renvoyer le
    réel 6 000 €, pas l'objectif 20 000 €.
    """
    year = datetime.now().year  # année « en cours » = celle où l'ancien MAX frappait
    pid = _seed_rent_with_high_objective(client, db_session, year)

    result = calculate_compte_resultat(db_session, year, pid)  # skip_prorata=False par défaut

    got = result["produits"].get(CATEGORY_NAME)
    assert got == REAL_RENT, (
        f"Le CR doit afficher le loyer réel {REAL_RENT:.0f} €, pas l'objectif "
        f"{OBJECTIVE:.0f} € — obtenu {got}. La règle MAX(réel, prévu) ne doit "
        "plus polluer le compte de résultat réel."
    )
    assert result["total_produits"] == REAL_RENT
    assert result["prorata_applied"] is False


def test_cr_identical_with_and_without_skip_prorata(client, db_session):
    """Les produits/charges sont identiques que skip_prorata soit True ou False :
    la bascule ne touche plus jamais les montants réels."""
    year = datetime.now().year
    pid = _seed_rent_with_high_objective(client, db_session, year)

    display = calculate_compte_resultat(db_session, year, pid, skip_prorata=False)
    reference = calculate_compte_resultat(db_session, year, pid, skip_prorata=True)

    assert display["produits"] == reference["produits"]
    assert display["charges"] == reference["charges"]
