"""
Service for calculating income statement (compte de résultat).

⚠️ Before making changes, read: ../../../docs/workflow/BEST_PRACTICES.md
"""

from datetime import date, datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from backend.database.models import (
    CompteResultatMapping,
    CompteResultatData,
    Transaction,
    EnrichedTransaction,
    AmortizationResult,
    LoanPayment
)


def get_mappings(db: Session) -> List[CompteResultatMapping]:
    """
    Charge tous les mappings depuis la table.
    
    Args:
        db: Session de base de données
        
    Returns:
        Liste des mappings
    """
    return db.query(CompteResultatMapping).all()


def calculate_produits_exploitation(
    year: int,
    mappings: List[CompteResultatMapping],
    db: Session
) -> Dict[str, float]:
    """
    Calcule les produits d'exploitation pour une année donnée.
    
    Filtre les transactions par année (date entre 01/01/année et 31/12/année),
    groupe par catégorie selon les mappings level_1 OU level_2 (logique OR),
    et somme les montants par catégorie.
    
    Args:
        year: Année pour laquelle calculer
        mappings: Liste des mappings à utiliser
        db: Session de base de données
        
    Returns:
        Dictionnaire {category_name: amount} pour les produits d'exploitation
    """
    # Filtrer les mappings pour les produits d'exploitation uniquement
    produits_categories = [
        "Loyers hors charge encaissés",
        "Charges locatives payées par locataires",
        "Autres revenus"
    ]
    
    produits_mappings = [
        m for m in mappings
        if m.category_name in produits_categories
    ]
    
    if not produits_mappings:
        return {}
    
    # Dates de début et fin d'année
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    # Construire les conditions de filtrage pour chaque mapping
    conditions = []
    category_conditions = {}  # {category_name: [conditions]}
    
    for mapping in produits_mappings:
        category_conditions[mapping.category_name] = []
        
        # Condition pour level_1 (si défini)
        if mapping.level_1_values:
            level_1_condition = EnrichedTransaction.level_1.in_(mapping.level_1_values)
        else:
            level_1_condition = None  # NULL = tous les level_1
        
        # Condition pour level_2 (obligatoire)
        level_2_condition = EnrichedTransaction.level_2.in_(mapping.level_2_values)
        
        # Condition pour level_3 (si défini)
        if mapping.level_3_values:
            level_3_condition = EnrichedTransaction.level_3.in_(mapping.level_3_values)
        else:
            level_3_condition = None  # NULL = tous les level_3
        
        # Construire la condition : level_1 OU level_2 (si level_1 défini), ET level_3 si défini
        # Si level_1 est défini, on fait (level_1 OU level_2), sinon juste level_2
        if level_1_condition is not None:
            base_condition = or_(level_1_condition, level_2_condition)
        else:
            base_condition = level_2_condition
        
        # Si level_3 est défini, on combine avec AND
        if level_3_condition is not None:
            condition = and_(base_condition, level_3_condition)
        else:
            condition = base_condition
        
        category_conditions[mapping.category_name].append(condition)
    
    # Calculer les montants par catégorie
    results = {}
    
    for category_name, conditions_list in category_conditions.items():
        # Combiner toutes les conditions pour cette catégorie avec OR
        combined_condition = or_(*conditions_list) if len(conditions_list) > 1 else conditions_list[0]
        
        # Requête : transactions enrichies avec date dans l'année et correspondant aux conditions
        query = db.query(
            func.sum(Transaction.quantite).label('total')
        ).join(
            EnrichedTransaction,
            Transaction.id == EnrichedTransaction.transaction_id
        ).filter(
            and_(
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.quantite > 0,  # Produits = montants positifs
                combined_condition
            )
        )
        
        result = query.scalar()
        results[category_name] = result if result else 0.0
    
    return results


def calculate_charges_exploitation(
    year: int,
    mappings: List[CompteResultatMapping],
    db: Session
) -> Dict[str, float]:
    """
    Calcule les charges d'exploitation pour une année donnée.
    
    Filtre les transactions par année,
    groupe par catégorie selon les mappings level_1 OU level_2 (logique OR),
    et somme les montants par catégorie.
    
    Args:
        year: Année pour laquelle calculer
        mappings: Liste des mappings à utiliser
        db: Session de base de données
        
    Returns:
        Dictionnaire {category_name: amount} pour les charges d'exploitation
    """
    # Filtrer les mappings pour les charges d'exploitation uniquement
    charges_categories = [
        "Charges de copropriété hors fonds travaux",
        "Fluides non refacturés",
        "Assurances",
        "Honoraires",
        "Travaux et mobilier",
        "Impôts et taxes",
        "Autres charges diverses"
    ]
    
    charges_mappings = [
        m for m in mappings
        if m.category_name in charges_categories
    ]
    
    if not charges_mappings:
        return {}
    
    # Dates de début et fin d'année
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    # Construire les conditions de filtrage pour chaque mapping
    category_conditions = {}  # {category_name: [conditions]}
    
    for mapping in charges_mappings:
        category_conditions[mapping.category_name] = []
        
        # Condition pour level_1 (si défini)
        if mapping.level_1_values:
            level_1_condition = EnrichedTransaction.level_1.in_(mapping.level_1_values)
        else:
            level_1_condition = None
        
        # Condition pour level_2 (obligatoire)
        level_2_condition = EnrichedTransaction.level_2.in_(mapping.level_2_values)
        
        # Condition pour level_3 (si défini)
        if mapping.level_3_values:
            level_3_condition = EnrichedTransaction.level_3.in_(mapping.level_3_values)
        else:
            level_3_condition = None
        
        # Construire la condition : level_1 OU level_2 (si level_1 défini), ET level_3 si défini
        # Si level_1 est défini, on fait (level_1 OU level_2), sinon juste level_2
        if level_1_condition is not None:
            base_condition = or_(level_1_condition, level_2_condition)
        else:
            base_condition = level_2_condition
        
        # Si level_3 est défini, on combine avec AND
        if level_3_condition is not None:
            condition = and_(base_condition, level_3_condition)
        else:
            condition = base_condition
        
        category_conditions[mapping.category_name].append(condition)
    
    # Calculer les montants par catégorie
    results = {}
    
    for category_name, conditions_list in category_conditions.items():
        # Combiner toutes les conditions pour cette catégorie avec OR
        combined_condition = or_(*conditions_list) if len(conditions_list) > 1 else conditions_list[0]
        
        # Requête : transactions enrichies avec date dans l'année et correspondant aux conditions
        # Pour les charges, on prend la valeur absolue car les montants sont négatifs
        query = db.query(
            func.sum(func.abs(Transaction.quantite)).label('total')
        ).join(
            EnrichedTransaction,
            Transaction.id == EnrichedTransaction.transaction_id
        ).filter(
            and_(
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.quantite < 0,  # Charges = montants négatifs
                combined_condition
            )
        )
        
        result = query.scalar()
        results[category_name] = result if result else 0.0
    
    return results


def get_amortissements(
    year: int,
    amortization_view_id: Optional[int],
    db: Session
) -> float:
    """
    Récupère le total d'amortissement pour l'année depuis les résultats d'amortissement.
    
    Note: Les vues d'amortissement sont des configurations. Les résultats réels
    sont stockés dans AmortizationResult. On somme tous les résultats pour l'année.
    
    Args:
        year: Année pour laquelle récupérer les amortissements
        amortization_view_id: ID de la vue d'amortissement (non utilisé pour l'instant, 
                             car les résultats sont calculés globalement)
        db: Session de base de données
        
    Returns:
        Total des amortissements pour l'année (montant positif)
    """
    # Sommer tous les AmortizationResult pour l'année
    # Les montants sont négatifs dans AmortizationResult, donc on prend la valeur absolue
    result = db.query(
        func.sum(func.abs(AmortizationResult.amount))
    ).filter(
        AmortizationResult.year == year
    ).scalar()
    
    return result if result else 0.0


def get_cout_financement(year: int, db: Session) -> float:
    """
    Calcule le coût du financement (intérêts + assurance) pour une année donnée.
    
    Filtre les loan_payments par année (date = 01/01/année),
    et somme interest + insurance de tous les crédits.
    
    Args:
        year: Année pour laquelle calculer
        db: Session de base de données
        
    Returns:
        Total des intérêts + assurance pour l'année
    """
    # Filtrer les loan_payments pour l'année (date = 01/01/année)
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    payments = db.query(LoanPayment).filter(
        and_(
            LoanPayment.date >= start_date,
            LoanPayment.date <= end_date
        )
    ).all()
    
    # Sommer interest + insurance
    total = sum(payment.interest + payment.insurance for payment in payments)
    
    return total


def calculate_compte_resultat(
    year: int,
    mappings: List[CompteResultatMapping],
    amortization_view_id: Optional[int],
    db: Session
) -> Dict[str, any]:
    """
    Calcule le compte de résultat complet pour une année donnée.
    
    Args:
        year: Année pour laquelle calculer
        mappings: Liste des mappings à utiliser
        amortization_view_id: ID de la vue d'amortissement à utiliser
        db: Session de base de données
        
    Returns:
        Dictionnaire avec:
        - categories: {category_name: amount}
        - total_produits: Total des produits d'exploitation
        - total_charges: Total des charges d'exploitation
        - resultat_exploitation: Résultat d'exploitation
        - resultat_net: Résultat net de l'exercice
    """
    # Calculer les produits d'exploitation
    produits = calculate_produits_exploitation(year, mappings, db)
    
    # Calculer les charges d'exploitation (hors amortissements et coût financement)
    charges = calculate_charges_exploitation(year, mappings, db)
    
    # Ajouter les amortissements
    amortissements = get_amortissements(year, amortization_view_id, db)
    charges["Charges d'amortissements"] = amortissements
    
    # Ajouter le coût du financement
    cout_financement = get_cout_financement(year, db)
    charges["Coût du financement (hors remboursement du capital)"] = cout_financement
    
    # Calculer les totaux
    total_produits = sum(produits.values())
    total_charges = sum(charges.values())
    resultat_exploitation = total_produits - total_charges
    resultat_net = resultat_exploitation  # Pour l'instant, résultat net = résultat d'exploitation
    
    return {
        "categories": {**produits, **charges},
        "total_produits": total_produits,
        "total_charges": total_charges,
        "resultat_exploitation": resultat_exploitation,
        "resultat_net": resultat_net
    }


def invalidate_compte_resultat_for_year(year: int, db: Session):
    """
    Invalide (supprime) les données de compte de résultat pour une année donnée.
    
    Args:
        year: Année à invalider
        db: Session de base de données
    """
    db.query(CompteResultatData).filter(
        CompteResultatData.annee == year
    ).delete()
    db.commit()


def invalidate_compte_resultat_for_date_range(start_date: date, end_date: date, db: Session):
    """
    Invalide (supprime) les données de compte de résultat pour une plage de dates.
    Supprime toutes les années entre start_date et end_date (inclus).
    
    Args:
        start_date: Date de début
        end_date: Date de fin
        db: Session de base de données
    """
    start_year = start_date.year
    end_year = end_date.year
    
    db.query(CompteResultatData).filter(
        and_(
            CompteResultatData.annee >= start_year,
            CompteResultatData.annee <= end_year
        )
    ).delete()
    db.commit()


def invalidate_all_compte_resultat(db: Session):
    """
    Invalide (supprime) toutes les données de compte de résultat.
    
    Args:
        db: Session de base de données
    """
    db.query(CompteResultatData).delete()
    db.commit()

