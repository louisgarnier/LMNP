"""
Tests pour `calculate_capital_restant_du` (backend/api/services/bilan_service.py).

⚠️ Utilise le harnais isolé de la Tâche 3 (fixtures `db_session` / base SQLite
en mémoire) : ne touche jamais backend/database/lmnp.db.

Bug reproduit (Tâche 4) : un `LoanConfig.loan_start_date` postérieur à
l'année calculée (ex: 2026-05-08) faisait sortir le prêt du filtre des
"crédits actifs" de `calculate_capital_restant_du`, même si son échéancier
(`LoanPayment`) démarrait bien avant (ex: 2021) et avait déjà des paiements
enregistrés jusqu'à l'année demandée. Résultat : le capital remboursé
n'était jamais déduit avant l'année de `loan_start_date`, et le capital
restant dû restait égal au montant du crédit accordé au lieu de diminuer.

Comportement attendu : un prêt est "actif" pour l'année N s'il a au moins un
`LoanPayment` daté au plus tard le 31/12/N — indépendamment de
`loan_start_date`.
"""

from datetime import date

from backend.database.models import (
    Property,
    Transaction,
    LoanConfig,
    LoanPayment,
)
from backend.api.services.bilan_service import calculate_capital_restant_du


LEVEL_1_DETTES = "Dettes financières (emprunt bancaire)"


def _setup_loan_with_late_start_date(db_session):
    """Construit un prêt dont `loan_start_date` (2026-05-08) est postérieure
    à l'échéancier réel (paiements depuis 2021), reproduisant le bug Evry."""
    prop = Property(name="Evry test")
    db_session.add(prop)
    db_session.flush()

    credit_amount = 231815.0

    # Transaction du déblocage du crédit (montant négatif = débit), datée
    # avant la première année testée (2021) pour que la source du montant
    # du crédit soit bien trouvée par calculate_capital_restant_du.
    transaction = Transaction(
        property_id=prop.id,
        date=date(2020, 12, 15),
        quantite=-credit_amount,
        nom="Déblocage crédit Evry",
        solde=0.0,
    )
    db_session.add(transaction)
    db_session.flush()

    # Étape 2 Task 6/8 : calculate_capital_restant_du résout la catégorie de
    # déblocage d'emprunt par label (référentiel) et filtre par category_id.
    # On classe donc la transaction (classification = category_id, plus de ligne
    # enriched_transactions).
    from backend.api.services.category_service import get_or_create_category
    transaction.category_id = get_or_create_category(
        db_session, LEVEL_1_DETTES, "Dettes", "Passif"
    ).id
    db_session.flush()

    # LoanConfig avec une loan_start_date manifestement postérieure à
    # l'échéancier réel des paiements (bug reproduit : 2026 vs 2021).
    loan_config = LoanConfig(
        property_id=prop.id,
        name="Nouveau crédit",
        credit_amount=credit_amount,
        interest_rate=1.1,
        duration_years=20,
        loan_start_date=date(2026, 5, 8),
    )
    db_session.add(loan_config)

    # Échéancier réel : paiements mensuels dès 2021, capital remboursé
    # cumulé connu pour vérifier le calcul.
    capital_paid_2021 = 0.0
    capital_paid_up_to_2023 = 0.0
    for year in (2021, 2022, 2023):
        for month in range(1, 13):
            capital_installment = 900.0
            payment = LoanPayment(
                property_id=prop.id,
                date=date(year, month, 1),
                capital=capital_installment,
                interest=200.0,
                insurance=22.0,
                total=capital_installment + 200.0 + 22.0,
                loan_name="Nouveau crédit",
            )
            db_session.add(payment)
            if year == 2021:
                capital_paid_2021 += capital_installment
            capital_paid_up_to_2023 += capital_installment

    db_session.commit()

    return prop.id, credit_amount, capital_paid_up_to_2023


def test_capital_restant_du_deduces_payments_before_loan_start_date(db_session):
    """RED (avant fix) / GREEN (après fix) :

    Un prêt dont l'échéancier (LoanPayment) démarre en 2021 doit voir son
    capital remboursé déduit dès 2021, MÊME SI `loan_start_date` (2026-05-08)
    est postérieure à l'année calculée. Avant la correction, le prêt était
    exclu des "crédits actifs" pour 2023 (loan_start_date > 31/12/2023), donc
    capital_paid=0.0 et le capital restant dû restait égal au montant plein
    du crédit — alors qu'il doit refléter les 36 mensualités déjà payées.
    """
    property_id, credit_amount, capital_paid_up_to_2023 = (
        _setup_loan_with_late_start_date(db_session)
    )

    remaining = calculate_capital_restant_du(db_session, 2023, property_id)

    expected_remaining = credit_amount - capital_paid_up_to_2023

    assert remaining == expected_remaining, (
        f"Capital restant dû attendu {expected_remaining:.2f} € "
        f"(credit_amount {credit_amount:.2f} € - capital remboursé "
        f"{capital_paid_up_to_2023:.2f} €), obtenu {remaining:.2f} € — "
        "les paiements de l'échéancier réel (dès 2021) doivent être déduits "
        "même si loan_start_date est postérieure à l'année calculée."
    )
