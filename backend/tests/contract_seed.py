"""
Seed minimal et déterministe pour les tests de contrat des états financiers
(compte de résultat & bilan) — Tâche 7.

Ce module ne touche JAMAIS la base de production : il attend une `Session`
SQLAlchemy déjà connectée à une base isolée (typiquement la fixture
`db_session` en mémoire de conftest.py) et y insère un jeu de données
minimal mais complet :

- 1 propriété
- 1 config Level 3 (CR + bilan)
- 2 mappings compte de résultat (1 produit, 1 charge)
- des mappings bilan (1 normal + toutes les catégories spéciales)
- 6 transactions classées réparties sur 2 années (2023, 2024)
- 1 crédit + ses paiements (intérêts/assurance/capital)
- 1 type d'amortissement + ses résultats annuels

Le but est d'exercer produits, charges, amortissements, coût du financement
et toutes les catégories spéciales du bilan, afin que la comparaison
« cache vs calcul live » soit significative.
"""

from datetime import date

from backend.database.models import (
    Property,
    Transaction,
    EnrichedTransaction,
    CompteResultatMapping,
    CompteResultatConfig,
    BilanMapping,
    BilanConfig,
    LoanConfig,
    LoanPayment,
    AmortizationType,
    AmortizationResult,
)

LEVEL_3 = "LOC"
YEARS = (2023, 2024)

# Compte de résultat (étape 2 Task 5) : le calcul CR filtre désormais par
# category_id -> nature du groupe. La config CR liste des labels de nature
# (traduits en natures), et non plus le label synthétique "LOC" (qui reste la
# valeur enriched.level_3 pour le chemin bilan, inchangé cette étape).
CR_NATURES = ("Produits", "Charges Déductibles")


def _add_transaction(db, property_id, d, quantite, nom, solde, level_1,
                     category_group=None, category_nature=None):
    """Ajoute une transaction + sa ligne enrichie (level_3 = LOC, inchangé pour
    le bilan). Si (category_group, category_nature) sont fournis, renseigne
    aussi `transactions.category_id` via le référentiel (comme le fait la
    double-écriture Task 4 en production), ce que le calcul CR lit désormais."""
    tx = Transaction(
        property_id=property_id,
        date=d,
        quantite=quantite,
        nom=nom,
        solde=solde,
        source_file="contract_seed",
    )
    db.add(tx)
    db.flush()  # pour obtenir tx.id
    enriched = EnrichedTransaction(
        transaction_id=tx.id,
        property_id=property_id,
        mois=d.month,
        annee=d.year,
        level_1=level_1,
        level_2="detail",
        level_3=LEVEL_3,
    )
    db.add(enriched)
    db.flush()
    if category_group is not None and category_nature is not None:
        from backend.api.services.category_service import get_or_create_category
        tx.category_id = get_or_create_category(
            db, level_1, category_group, category_nature
        ).id
        db.flush()
    return tx


def seed_contract_data(db) -> int:
    """Insère le jeu de données de contrat et retourne le property_id."""
    prop = Property(name="TEST_CONTRACT_T7", address="1 rue du Test")
    db.add(prop)
    db.flush()
    pid = prop.id

    # --- Configs Level 3 ---
    # CR : labels de nature (traduits en natures par le service). Bilan (étape 2
    # Task 6) : idem, le calcul des lignes normales du bilan filtre désormais
    # par nature de groupe (via category_id), plus par enriched.level_3.
    cr_level_3 = ", ".join(f'"{n}"' for n in CR_NATURES)
    db.add(CompteResultatConfig(property_id=pid, level_3_values=f'[{cr_level_3}]'))
    db.add(BilanConfig(property_id=pid, level_3_values='["Actif", "Passif"]'))

    # --- Mappings compte de résultat ---
    cr_mapping_loyers = CompteResultatMapping(
        property_id=pid,
        category_name="Loyers hors charge encaissés",
        type="Produits d'exploitation",
        level_1_values='["LOYERS"]',
    )
    cr_mapping_entretien = CompteResultatMapping(
        property_id=pid,
        category_name="Charges d'entretien et de réparation",
        type="Charges d'exploitation",
        level_1_values='["ENTRETIEN"]',
    )
    db.add(cr_mapping_loyers)
    db.add(cr_mapping_entretien)

    # --- Mappings bilan ---
    bilan_mapping_immo = BilanMapping(
        property_id=pid, category_name="Immobilisations corporelles",
        type="ACTIF", sub_category="Actif immobilisé",
        level_1_values='["IMMO"]', is_special=False,
    )
    db.add(bilan_mapping_immo)
    db.add(BilanMapping(
        property_id=pid, category_name="Amortissements cumulés",
        type="ACTIF", sub_category="Actif immobilisé",
        is_special=True, special_source="amortization_result",
    ))
    db.add(BilanMapping(
        property_id=pid, category_name="Compte bancaire",
        type="ACTIF", sub_category="Actif circulant",
        is_special=True, special_source="transactions",
    ))
    db.add(BilanMapping(
        property_id=pid, category_name="Résultat de l'exercice",
        type="PASSIF", sub_category="Capitaux propres",
        is_special=True, special_source="compte_resultat",
    ))
    db.add(BilanMapping(
        property_id=pid, category_name="Report à nouveau",
        type="PASSIF", sub_category="Capitaux propres",
        is_special=True, special_source="compte_resultat_cumul",
    ))
    db.add(BilanMapping(
        property_id=pid, category_name="Capital restant dû",
        type="PASSIF", sub_category="Dettes financières",
        is_special=True, special_source="loan_payments",
    ))

    # --- Transactions 2023 (immobilisation, emprunt, loyer, entretien) ---
    # LOYERS/ENTRETIEN sont classées (category_id) sous les natures produits/
    # charges_deductibles : c'est ce que lit le calcul CR. IMMO/emprunt restent
    # non classées (category_id NULL) : hors périmètre CR, seulement bilan.
    _add_transaction(db, pid, date(2023, 1, 5), -100000.0, "Achat immobilisation",
                     -100000.0, "IMMO",
                     category_group="Immobilisations (contrat)", category_nature="Actif")
    _add_transaction(db, pid, date(2023, 1, 6), -80000.0, "Deblocage emprunt",
                     -20000.0, "Dettes financières (emprunt bancaire)",
                     category_group="Dettes (contrat)", category_nature="Passif")
    _add_transaction(db, pid, date(2023, 6, 15), 6000.0, "Loyers 2023",
                     -14000.0, "LOYERS",
                     category_group="Produits (contrat)", category_nature="Produits")
    _add_transaction(db, pid, date(2023, 7, 10), -800.0, "Entretien 2023",
                     -14800.0, "ENTRETIEN",
                     category_group="Charges (contrat)", category_nature="Charges Déductibles")

    # --- Transactions 2024 (loyer, entretien) ---
    _add_transaction(db, pid, date(2024, 6, 15), 7200.0, "Loyers 2024",
                     -7600.0, "LOYERS",
                     category_group="Produits (contrat)", category_nature="Produits")
    _add_transaction(db, pid, date(2024, 7, 10), -500.0, "Entretien 2024",
                     -8100.0, "ENTRETIEN",
                     category_group="Charges (contrat)", category_nature="Charges Déductibles")

    # --- Liaison CR (source de lecture du calcul CR, étape 2 Task 5) ---
    # Les categories LOYERS/ENTRETIEN existent maintenant : on résout la liaison.
    from backend.api.services.compte_resultat_service import sync_mapping_categories
    db.flush()
    sync_mapping_categories(db, cr_mapping_loyers, cr_mapping_loyers.level_1_values)
    sync_mapping_categories(db, cr_mapping_entretien, cr_mapping_entretien.level_1_values)

    # --- Liaison bilan (source de lecture des lignes normales, étape 2 Task 6) ---
    # La category "IMMO" existe maintenant (classification ci-dessus) : on
    # résout la liaison de la ligne normale "Immobilisations corporelles".
    from backend.api.services.bilan_service import sync_bilan_mapping_categories
    sync_bilan_mapping_categories(db, bilan_mapping_immo, bilan_mapping_immo.level_1_values)

    # --- Crédit + paiements ---
    loan = LoanConfig(
        property_id=pid, name="Prêt Test", credit_amount=80000.0,
        interest_rate=1.5, duration_years=20, initial_deferral_months=0,
        loan_start_date=date(2023, 1, 6), monthly_insurance=25.0,
    )
    db.add(loan)
    for y in YEARS:
        db.add(LoanPayment(
            property_id=pid, date=date(y, 1, 1), capital=2000.0,
            interest=1500.0, insurance=300.0, total=3800.0, loan_name="Prêt Test",
        ))

    # --- Type d'amortissement + résultats ---
    db.add(AmortizationType(
        property_id=pid, name="Immobilisation", level_2_value="ammortissements",
        level_1_values='["IMMO"]', duration=25.0,
    ))
    # Le résultat d'amortissement est rattaché à la transaction d'immobilisation
    immo_tx = db.query(Transaction).filter(
        Transaction.property_id == pid,
        Transaction.nom == "Achat immobilisation",
    ).first()
    for y in YEARS:
        db.add(AmortizationResult(
            transaction_id=immo_tx.id, year=y,
            category="Immobilisation", amount=-4000.0,
        ))

    db.commit()
    return pid
