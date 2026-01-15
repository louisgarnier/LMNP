"""
Service de calcul du compte de résultat.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce service implémente la logique de calcul du compte de résultat :
- Filtrage par level_3 (appliqué en premier)
- Mapping level_1 vers catégories comptables
- Calcul des produits et charges d'exploitation
- Récupération des amortissements depuis amortization_result
- Calcul du coût du financement depuis loan_payments
"""

import json
from datetime import date
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from backend.database.models import (
    Transaction,
    EnrichedTransaction,
    CompteResultatMapping,
    CompteResultatData,
    CompteResultatConfig,
    AmortizationResult,
    LoanPayment,
    LoanConfig
)


def get_mappings(db: Session) -> List[CompteResultatMapping]:
    """
    Charger tous les mappings depuis la table.
    
    Args:
        db: Session de base de données
    
    Returns:
        Liste des mappings configurés
    """
    return db.query(CompteResultatMapping).all()


def get_level_3_values(db: Session) -> List[str]:
    """
    Récupérer les valeurs level_3 sélectionnées depuis la configuration.
    
    Args:
        db: Session de base de données
    
    Returns:
        Liste des valeurs level_3 sélectionnées (vide si aucune config)
    """
    config = db.query(CompteResultatConfig).first()
    if not config or not config.level_3_values:
        return []
    
    try:
        return json.loads(config.level_3_values)
    except (json.JSONDecodeError, TypeError):
        return []


def calculate_produits_exploitation(
    db: Session,
    year: int,
    mappings: List[CompteResultatMapping],
    level_3_values: List[str]
) -> Dict[str, float]:
    """
    Calculer les produits d'exploitation pour une année donnée.
    
    Logique :
    1. Filtrer d'abord par level_3 (seules les transactions avec level_3 dans level_3_values)
    2. Filtrer par année (date entre 01/01/année et 31/12/année)
    3. Grouper par catégorie selon les mappings level_1
    4. Sommer les montants par catégorie
    5. Prendre en compte transactions positives ET négatives (revenus positifs - remboursements négatifs)
    
    Args:
        db: Session de base de données
        year: Année à calculer
        mappings: Liste des mappings configurés
        level_3_values: Liste des valeurs level_3 à considérer
    
    Returns:
        Dictionnaire {category_name: amount} pour les produits d'exploitation
    """
    if not level_3_values:
        # Si aucune valeur level_3 sélectionnée, retourner des montants vides
        return {}
    
    # Date de début et fin de l'année
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    # Filtrer les transactions par level_3 et par année
    query = db.query(
        EnrichedTransaction.level_1,
        Transaction.quantite
    ).join(
        Transaction, Transaction.id == EnrichedTransaction.transaction_id
    ).filter(
        and_(
            EnrichedTransaction.level_3.in_(level_3_values),
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            EnrichedTransaction.level_1.isnot(None)  # Uniquement les transactions avec level_1
        )
    )
    
    # Récupérer toutes les transactions filtrées
    transactions = query.all()
    
    # Grouper par catégorie selon les mappings
    # IMPORTANT : Regrouper tous les mappings d'une même catégorie avec OR pour éviter les doublons
    results = {}
    
    # Grouper les mappings par catégorie
    mappings_by_category = {}
    for mapping in mappings:
        category_name = mapping.category_name
        
        # Ignorer les catégories spéciales (amortissements, coût financement)
        if category_name in ["Charges d'amortissements", "Coût du financement (hors remboursement du capital)"]:
            continue
        
        if category_name not in mappings_by_category:
            mappings_by_category[category_name] = []
        mappings_by_category[category_name].append(mapping)
    
    # Pour chaque catégorie, regrouper tous les level_1_values avec OR
    for category_name, category_mappings in mappings_by_category.items():
        # Collecter tous les level_1_values de tous les mappings de cette catégorie (OR)
        all_level_1_values = set()
        for mapping in category_mappings:
            if mapping.level_1_values:
                try:
                    level_1_values = json.loads(mapping.level_1_values)
                    all_level_1_values.update(level_1_values)
                except (json.JSONDecodeError, TypeError):
                    continue
        
        if not all_level_1_values:
            # Pas de level_1_values configuré pour cette catégorie
            continue
        
        # Filtrer les transactions dont le level_1 est dans la liste (OR de tous les mappings)
        category_amount = 0.0
        for level_1, quantite in transactions:
            if level_1 in all_level_1_values:
                # Pour les produits : revenus positifs - remboursements négatifs
                category_amount += quantite
        
        if category_amount != 0.0:
            results[category_name] = category_amount
    
    return results


def calculate_charges_exploitation(
    db: Session,
    year: int,
    mappings: List[CompteResultatMapping],
    level_3_values: List[str]
) -> Dict[str, float]:
    """
    Calculer les charges d'exploitation pour une année donnée.
    
    Logique :
    1. Filtrer d'abord par level_3 (seules les transactions avec level_3 dans level_3_values)
    2. Filtrer par année (date entre 01/01/année et 31/12/année)
    3. Grouper par catégorie selon les mappings level_1
    4. Sommer les montants par catégorie
    5. Prendre en compte transactions positives ET négatives (dépenses négatives - remboursements/crédits positifs)
    
    Args:
        db: Session de base de données
        year: Année à calculer
        mappings: Liste des mappings configurés
        level_3_values: Liste des valeurs level_3 à considérer
    
    Returns:
        Dictionnaire {category_name: amount} pour les charges d'exploitation
    """
    if not level_3_values:
        # Si aucune valeur level_3 sélectionnée, retourner des montants vides
        return {}
    
    # Date de début et fin de l'année
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    # Filtrer les transactions par level_3 et par année
    query = db.query(
        EnrichedTransaction.level_1,
        Transaction.quantite
    ).join(
        Transaction, Transaction.id == EnrichedTransaction.transaction_id
    ).filter(
        and_(
            EnrichedTransaction.level_3.in_(level_3_values),
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            EnrichedTransaction.level_1.isnot(None)  # Uniquement les transactions avec level_1
        )
    )
    
    # Récupérer toutes les transactions filtrées
    transactions = query.all()
    
    # Grouper par catégorie selon les mappings
    # IMPORTANT : Regrouper tous les mappings d'une même catégorie avec OR pour éviter les doublons
    results = {}
    
    # Grouper les mappings par catégorie
    mappings_by_category = {}
    for mapping in mappings:
        category_name = mapping.category_name
        
        # Ignorer les catégories spéciales (amortissements, coût financement)
        if category_name in ["Charges d'amortissements", "Coût du financement (hors remboursement du capital)"]:
            continue
        
        if category_name not in mappings_by_category:
            mappings_by_category[category_name] = []
        mappings_by_category[category_name].append(mapping)
    
    # Pour chaque catégorie, regrouper tous les level_1_values avec OR
    for category_name, category_mappings in mappings_by_category.items():
        # Collecter tous les level_1_values de tous les mappings de cette catégorie (OR)
        all_level_1_values = set()
        for mapping in category_mappings:
            if mapping.level_1_values:
                try:
                    level_1_values = json.loads(mapping.level_1_values)
                    all_level_1_values.update(level_1_values)
                except (json.JSONDecodeError, TypeError):
                    continue
        
        if not all_level_1_values:
            # Pas de level_1_values configuré pour cette catégorie
            continue
        
        # Filtrer les transactions dont le level_1 est dans la liste (OR de tous les mappings)
        category_amount = 0.0
        for level_1, quantite in transactions:
            if level_1 in all_level_1_values:
                # Pour les charges : dépenses négatives - remboursements/crédits positifs
                category_amount += quantite
        
        if category_amount != 0.0:
            results[category_name] = category_amount
    
    return results


def get_amortissements(db: Session, year: int) -> float:
    """
    Récupérer le total d'amortissement pour une année depuis la table amortization_result.
    
    Args:
        db: Session de base de données
        year: Année à calculer
    
    Returns:
        Total des amortissements pour l'année (somme de toutes les catégories)
    """
    result = db.query(
        func.sum(AmortizationResult.amount)
    ).filter(
        AmortizationResult.year == year
    ).scalar()
    
    return result if result is not None else 0.0


def get_cout_financement(db: Session, year: int) -> float:
    """
    Calculer le coût du financement (intérêts + assurance) pour une année.
    
    Logique :
    - Récupérer tous les crédits configurés
    - Filtrer loan_payments par année
    - Gérer le cas d'un seul crédit ou plusieurs crédits
    - Sommer interest + insurance de tous les crédits
    
    Args:
        db: Session de base de données
        year: Année à calculer
    
    Returns:
        Total du coût du financement (interest + insurance) pour l'année
    """
    # Date de début et fin de l'année
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    # Récupérer tous les crédits configurés
    loan_configs = db.query(LoanConfig).all()
    
    if not loan_configs:
        return 0.0
    
    # Récupérer les noms des crédits configurés
    loan_names = [config.name for config in loan_configs]
    
    # Récupérer uniquement les loan_payments pour l'année qui correspondent aux crédits configurés
    payments = db.query(LoanPayment).filter(
        and_(
            LoanPayment.date >= start_date,
            LoanPayment.date <= end_date,
            LoanPayment.loan_name.in_(loan_names)  # Filtrer par les noms des crédits configurés
        )
    ).all()
    
    # Sommer interest + insurance uniquement des crédits configurés
    total_cost = 0.0
    for payment in payments:
        total_cost += payment.interest + payment.insurance
    
    return total_cost


def calculate_compte_resultat(
    db: Session,
    year: int,
    mappings: Optional[List[CompteResultatMapping]] = None,
    level_3_values: Optional[List[str]] = None
) -> Dict[str, any]:
    """
    Calculer le compte de résultat complet pour une année.
    
    Args:
        db: Session de base de données
        year: Année à calculer
        mappings: Liste des mappings (optionnel, sera chargée depuis DB si non fournie)
        level_3_values: Liste des valeurs level_3 (optionnel, sera chargée depuis config si non fournie)
    
    Returns:
        Dictionnaire avec :
        - produits: Dict[str, float] - Produits d'exploitation par catégorie
        - charges: Dict[str, float] - Charges d'exploitation par catégorie
        - amortissements: float - Total des amortissements
        - cout_financement: float - Coût du financement
        - resultat_exploitation: float - Résultat d'exploitation (produits - charges)
        - resultat_net: float - Résultat net (égal au résultat d'exploitation)
    """
    # Charger les mappings si non fournis
    if mappings is None:
        mappings = get_mappings(db)
    
    # Charger les level_3_values si non fournis
    if level_3_values is None:
        level_3_values = get_level_3_values(db)
    
    # Calculer les produits d'exploitation
    produits = calculate_produits_exploitation(db, year, mappings, level_3_values)
    
    # Calculer les charges d'exploitation
    charges = calculate_charges_exploitation(db, year, mappings, level_3_values)
    
    # Ajouter les catégories spéciales
    amortissements = get_amortissements(db, year)
    if amortissements != 0.0:
        charges["Charges d'amortissements"] = amortissements
    
    cout_financement = get_cout_financement(db, year)
    if cout_financement != 0.0:
        charges["Coût du financement (hors remboursement du capital)"] = cout_financement
    
    # Calculer les totaux
    total_produits = sum(produits.values())
    total_charges = sum(charges.values())
    
    resultat_exploitation = total_produits - total_charges
    resultat_net = resultat_exploitation
    
    return {
        "produits": produits,
        "charges": charges,
        "amortissements": amortissements,
        "cout_financement": cout_financement,
        "total_produits": total_produits,
        "total_charges": total_charges,
        "resultat_exploitation": resultat_exploitation,
        "resultat_net": resultat_net
    }


# ========== Invalidation Functions ==========

def invalidate_compte_resultat_for_year(db: Session, year: int) -> int:
    """
    Supprimer les comptes de résultat pour une année donnée.
    
    Args:
        db: Session de base de données
        year: Année pour laquelle invalider les comptes de résultat
    
    Returns:
        Nombre de données supprimées
    """
    deleted_count = db.query(CompteResultatData).filter(
        CompteResultatData.annee == year
    ).delete()
    db.commit()
    return deleted_count


def invalidate_compte_resultat_for_date_range(
    db: Session,
    start_date: date,
    end_date: date
) -> int:
    """
    Supprimer les comptes de résultat pour une plage de dates.
    
    Args:
        db: Session de base de données
        start_date: Date de début
        end_date: Date de fin
    
    Returns:
        Nombre de données supprimées
    """
    start_year = start_date.year
    end_year = end_date.year
    
    deleted_count = db.query(CompteResultatData).filter(
        CompteResultatData.annee >= start_year,
        CompteResultatData.annee <= end_year
    ).delete()
    db.commit()
    return deleted_count


def invalidate_all_compte_resultat(db: Session) -> int:
    """
    Supprimer tous les comptes de résultat.
    
    Args:
        db: Session de base de données
    
    Returns:
        Nombre de données supprimées
    """
    deleted_count = db.query(CompteResultatData).delete()
    db.commit()
    return deleted_count


def invalidate_compte_resultat_for_transaction_date(db: Session, transaction_date: date) -> int:
    """
    Invalider les comptes de résultat pour l'année d'une transaction.
    
    Args:
        db: Session de base de données
        transaction_date: Date de la transaction
    
    Returns:
        Nombre de données supprimées
    """
    year = transaction_date.year
    return invalidate_compte_resultat_for_year(db, year)
