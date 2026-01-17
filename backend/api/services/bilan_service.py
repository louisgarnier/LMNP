"""
Service de calcul du bilan.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce service implémente la logique de calcul du bilan :
- Filtrage par level_3 (appliqué en premier)
- Mapping level_1 vers catégories comptables
- Calcul des catégories normales depuis transactions enrichies
- Calcul des catégories spéciales (amortissements cumulés, compte bancaire, résultat exercice, etc.)
- Calcul des totaux par niveau (A, B, C)
- Validation de l'équilibre ACTIF = PASSIF
"""

import json
from datetime import date
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from backend.database.models import (
    Transaction,
    EnrichedTransaction,
    BilanMapping,
    BilanData,
    BilanConfig,
    AmortizationResult,
    LoanPayment,
    LoanConfig,
    CompteResultatData,
    CompteResultatOverride
)
from backend.api.services.compte_resultat_service import calculate_compte_resultat


def get_mappings(db: Session) -> List[BilanMapping]:
    """
    Charger tous les mappings depuis la table.
    
    Args:
        db: Session de base de données
    
    Returns:
        Liste des mappings configurés
    """
    return db.query(BilanMapping).order_by(
        BilanMapping.type,
        BilanMapping.sub_category,
        BilanMapping.category_name
    ).all()


def get_level_3_values(db: Session) -> List[str]:
    """
    Récupérer les valeurs level_3 sélectionnées depuis la configuration.
    
    Args:
        db: Session de base de données
    
    Returns:
        Liste des valeurs level_3 sélectionnées (vide si aucune config)
    """
    config = db.query(BilanConfig).first()
    if not config or not config.level_3_values:
        return []
    
    try:
        return json.loads(config.level_3_values)
    except (json.JSONDecodeError, TypeError):
        return []


def calculate_normal_category(
    db: Session,
    year: int,
    mapping: BilanMapping,
    level_3_values: List[str]
) -> float:
    """
    Calculer le montant d'une catégorie normale depuis les transactions enrichies.
    
    Logique :
    1. Filtrer par level_3 (seules les transactions avec level_3 dans level_3_values)
    2. Filtrer par année (date entre 01/01/année et 31/12/année)
    3. Filtrer par level_1 (selon level_1_values du mapping)
    4. Sommer les montants
    
    Args:
        db: Session de base de données
        year: Année à calculer
        mapping: Mapping de la catégorie
        level_3_values: Liste des valeurs level_3 à considérer
    
    Returns:
        Montant total pour cette catégorie
    """
    if not level_3_values:
        return 0.0
    
    if not mapping.level_1_values:
        return 0.0
    
    try:
        level_1_values = json.loads(mapping.level_1_values)
    except (json.JSONDecodeError, TypeError):
        return 0.0
    
    if not level_1_values:
        return 0.0
    
    # Date de début et fin de l'année
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    # Filtrer les transactions par level_3, level_1 et par année
    query = db.query(
        func.sum(Transaction.quantite)
    ).join(
        EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
    ).filter(
        and_(
            EnrichedTransaction.level_3.in_(level_3_values),
            EnrichedTransaction.level_1.in_(level_1_values),
            Transaction.date >= start_date,
            Transaction.date <= end_date
        )
    )
    
    result = query.scalar()
    return result if result is not None else 0.0


def calculate_amortizations_cumul(
    db: Session,
    year: int
) -> float:
    """
    Calculer le cumul des amortissements jusqu'à l'année en cours.
    
    Logique :
    - Récupérer tous les amortissements de toutes les années <= year
    - Sommer les montants (qui sont déjà négatifs)
    - Retourner la valeur négative (diminution de l'actif)
    
    Args:
        db: Session de base de données
        year: Année jusqu'à laquelle cumuler
    
    Returns:
        Cumul des amortissements (négatif, car diminution de l'actif)
    """
    result = db.query(
        func.sum(AmortizationResult.amount)
    ).filter(
        AmortizationResult.year <= year
    ).scalar()
    
    return result if result is not None else 0.0


def calculate_compte_bancaire(
    db: Session,
    year: int
) -> float:
    """
    Calculer le solde bancaire au 31/12 de l'année.
    
    Logique :
    - Récupérer la dernière transaction de l'année (ou avant si aucune transaction en décembre)
    - Utiliser le solde de cette transaction
    
    Args:
        db: Session de base de données
        year: Année à calculer
    
    Returns:
        Solde bancaire au 31/12 (positif)
    """
    # Date de fin de l'année
    end_date = date(year, 12, 31)
    
    # Récupérer la dernière transaction jusqu'à la fin de l'année
    last_transaction = db.query(Transaction).filter(
        Transaction.date <= end_date
    ).order_by(
        Transaction.date.desc(),
        Transaction.id.desc()
    ).first()
    
    if not last_transaction:
        return 0.0
    
    return last_transaction.solde if last_transaction.solde is not None else 0.0


def calculate_resultat_exercice(
    db: Session,
    year: int,
    compte_resultat_view_id: Optional[int] = None
) -> float:
    """
    Calculer le résultat de l'exercice pour une année.
    
    Logique :
    - Chercher un override pour l'année (si existe, l'utiliser)
    - Sinon : utiliser le résultat net du compte de résultat
    
    Args:
        db: Session de base de données
        year: Année à calculer
        compte_resultat_view_id: ID de la vue compte de résultat (optionnel, non utilisé pour l'instant)
    
    Returns:
        Résultat de l'exercice (bénéfice positif, perte négative)
    """
    # Chercher un override pour l'année
    override = db.query(CompteResultatOverride).filter(
        CompteResultatOverride.year == year
    ).first()
    
    if override:
        return override.override_value
    
    # Sinon, calculer depuis le compte de résultat
    compte_resultat = calculate_compte_resultat(db, year)
    return compte_resultat.get("resultat_net", 0.0)


def calculate_report_a_nouveau(
    db: Session,
    year: int
) -> float:
    """
    Calculer le report à nouveau (cumul des résultats des années précédentes).
    
    Logique :
    - Cumuler les résultats de toutes les années < year
    - Première année : 0 (pas de report)
    
    Args:
        db: Session de base de données
        year: Année à calculer
    
    Returns:
        Report à nouveau (cumul des résultats précédents)
    """
    if year <= 1:
        return 0.0
    
    # Récupérer toutes les années précédentes
    total = 0.0
    for prev_year in range(1, year):
        resultat = calculate_resultat_exercice(db, prev_year)
        total += resultat
    
    return total


def calculate_capital_restant_du(
    db: Session,
    year: int
) -> float:
    """
    Calculer le capital restant dû au 31/12 de l'année.
    
    Logique :
    - Récupérer tous les crédits configurés
    - Pour chaque crédit : crédit accordé - cumul des remboursements de capital jusqu'au 31/12
    - Sommer tous les crédits
    
    Args:
        db: Session de base de données
        year: Année à calculer
    
    Returns:
        Capital restant dû au 31/12 (positif, car dette)
    """
    # Date de fin de l'année
    end_date = date(year, 12, 31)
    
    # Récupérer tous les crédits configurés
    loan_configs = db.query(LoanConfig).all()
    
    if not loan_configs:
        return 0.0
    
    total_remaining = 0.0
    
    for loan_config in loan_configs:
        # Montant du crédit accordé
        credit_amount = loan_config.credit_amount
        
        # Cumul des remboursements de capital jusqu'au 31/12
        capital_paid = db.query(
            func.sum(LoanPayment.capital)
        ).filter(
            and_(
                LoanPayment.loan_name == loan_config.name,
                LoanPayment.date <= end_date
            )
        ).scalar()
        
        capital_paid = capital_paid if capital_paid is not None else 0.0
        
        # Capital restant dû pour ce crédit
        remaining = credit_amount - capital_paid
        total_remaining += remaining
    
    return total_remaining


def calculate_bilan(
    db: Session,
    year: int,
    mappings: Optional[List[BilanMapping]] = None,
    level_3_values: Optional[List[str]] = None
) -> Dict[str, any]:
    """
    Calculer le bilan complet pour une année.
    
    Args:
        db: Session de base de données
        year: Année à calculer
        mappings: Liste des mappings (optionnel, sera chargée depuis DB si non fournie)
        level_3_values: Liste des valeurs level_3 (optionnel, sera chargée depuis config si non fournie)
    
    Returns:
        Dictionnaire avec :
        - categories: Dict[str, float] - Montants par catégorie
        - totals_by_sub_category: Dict[str, float] - Totaux par sous-catégorie
        - totals_by_type: Dict[str, float] - Totaux par type (ACTIF/PASSIF)
        - actif_total: float - Total ACTIF
        - passif_total: float - Total PASSIF
        - difference: float - Différence ACTIF - PASSIF
        - difference_percent: float - Pourcentage de différence
    """
    # Charger les mappings si non fournis
    if mappings is None:
        mappings = get_mappings(db)
    
    # Charger les level_3_values si non fournis
    if level_3_values is None:
        level_3_values = get_level_3_values(db)
    
    # Dictionnaire pour stocker les montants par catégorie
    categories = {}
    
    # Calculer chaque catégorie
    for mapping in mappings:
        category_name = mapping.category_name
        
        if mapping.is_special:
            # Catégorie spéciale
            if mapping.special_source == "amortization_result":
                amount = calculate_amortizations_cumul(db, year)
            elif mapping.special_source == "transactions":
                amount = calculate_compte_bancaire(db, year)
            elif mapping.special_source == "compte_resultat":
                amount = calculate_resultat_exercice(
                    db, year, mapping.compte_resultat_view_id
                )
            elif mapping.special_source == "compte_resultat_cumul":
                amount = calculate_report_a_nouveau(db, year)
            elif mapping.special_source == "loan_payments":
                amount = calculate_capital_restant_du(db, year)
            else:
                amount = 0.0
        else:
            # Catégorie normale
            amount = calculate_normal_category(db, year, mapping, level_3_values)
        
        categories[category_name] = amount
    
    # Calculer les totaux par sous-catégorie
    totals_by_sub_category = {}
    for mapping in mappings:
        sub_category = mapping.sub_category
        if sub_category not in totals_by_sub_category:
            totals_by_sub_category[sub_category] = 0.0
        totals_by_sub_category[sub_category] += categories.get(mapping.category_name, 0.0)
    
    # Calculer les totaux par type (ACTIF/PASSIF)
    totals_by_type = {}
    for mapping in mappings:
        type_name = mapping.type
        if type_name not in totals_by_type:
            totals_by_type[type_name] = 0.0
        totals_by_type[type_name] += categories.get(mapping.category_name, 0.0)
    
    # Totaux ACTIF et PASSIF
    actif_total = totals_by_type.get("ACTIF", 0.0)
    passif_total = totals_by_type.get("PASSIF", 0.0)
    
    # Calculer la différence et le pourcentage
    difference = actif_total - passif_total
    if passif_total != 0:
        difference_percent = (difference / passif_total) * 100
    elif actif_total != 0:
        difference_percent = 100.0  # Si passif = 0 mais actif > 0
    else:
        difference_percent = 0.0  # Si les deux sont à 0
    
    return {
        "categories": categories,
        "totals_by_sub_category": totals_by_sub_category,
        "totals_by_type": totals_by_type,
        "actif_total": actif_total,
        "passif_total": passif_total,
        "difference": difference,
        "difference_percent": difference_percent
    }


def get_bilan_data(
    db: Session,
    year: Optional[int] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None
) -> List[BilanData]:
    """
    Récupérer les données du bilan depuis la table bilan_data.
    
    Args:
        db: Session de base de données
        year: Année spécifique (optionnel)
        start_year: Année de début (optionnel, pour plage)
        end_year: Année de fin (optionnel, pour plage)
    
    Returns:
        Liste des données du bilan
    """
    query = db.query(BilanData)
    
    if year is not None:
        query = query.filter(BilanData.annee == year)
    elif start_year is not None and end_year is not None:
        query = query.filter(
            and_(
                BilanData.annee >= start_year,
                BilanData.annee <= end_year
            )
        )
    
    return query.order_by(BilanData.annee, BilanData.category_name).all()


def invalidate_all_bilan(db: Session) -> None:
    """
    Marquer toutes les données du bilan comme invalides (supprimer toutes les données).
    
    Args:
        db: Session de base de données
    """
    db.query(BilanData).delete()
    db.commit()


def invalidate_bilan_for_year(year: int, db: Session) -> None:
    """
    Invalider une année spécifique (supprimer les données de cette année).
    
    Args:
        year: Année à invalider
        db: Session de base de données
    """
    db.query(BilanData).filter(BilanData.annee == year).delete()
    db.commit()
