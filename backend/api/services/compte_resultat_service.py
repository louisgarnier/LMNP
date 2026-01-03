"""
Service for calculating income statement (compte de résultat).

⚠️ Before making changes, read: ../../../docs/workflow/BEST_PRACTICES.md
"""

from datetime import date, datetime
from typing import Dict, List, Optional
import json
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from backend.database.models import (
    CompteResultatMapping,
    CompteResultatData,
    Transaction,
    EnrichedTransaction,
    AmortizationResult,
    LoanPayment,
    AmortizationView,
    LoanConfig
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
        
        # Pour les charges : dépenses (négatifs) - remboursements/crédits (positifs)
        # Dépenses (négatifs) : somme des valeurs absolues
        query_negatifs = db.query(
            func.sum(func.abs(Transaction.quantite)).label('total_negatifs')
        ).join(
            EnrichedTransaction,
            Transaction.id == EnrichedTransaction.transaction_id
        ).filter(
            and_(
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.quantite < 0,
                combined_condition
            )
        )
        total_negatifs = query_negatifs.scalar() or 0.0
        
        # Remboursements/crédits (positifs) : somme
        query_positifs = db.query(
            func.sum(Transaction.quantite).label('total_positifs')
        ).join(
            EnrichedTransaction,
            Transaction.id == EnrichedTransaction.transaction_id
        ).filter(
            and_(
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.quantite > 0,
                combined_condition
            )
        )
        total_positifs = query_positifs.scalar() or 0.0
        
        # Total : dépenses - remboursements (cohérent avec calculate_amounts_by_category_and_year)
        result = total_negatifs - total_positifs
        results[category_name] = result if result else 0.0
    
    return results


def get_amortissements(
    year: int,
    amortization_view_id: Optional[int],
    db: Session
) -> float:
    """
    Récupère le total d'amortissement pour l'année depuis les résultats d'amortissement.
    
    Si amortization_view_id est fourni, filtre par la vue d'amortissement (via level_2_value).
    Sinon, somme tous les résultats pour l'année.
    
    Args:
        year: Année pour laquelle récupérer les amortissements
        amortization_view_id: ID de la vue d'amortissement (optionnel)
        db: Session de base de données
        
    Returns:
        Total des amortissements pour l'année (montant positif)
    """
    if amortization_view_id:
        # Récupérer la vue d'amortissement
        view = db.query(AmortizationView).filter(AmortizationView.id == amortization_view_id).first()
        if not view:
            return 0.0
        
        # Filtrer les AmortizationResult par year et level_2_value de la vue
        # via les transactions enrichies
        result = db.query(
            func.sum(func.abs(AmortizationResult.amount))
        ).join(
            Transaction,
            AmortizationResult.transaction_id == Transaction.id
        ).join(
            EnrichedTransaction,
            Transaction.id == EnrichedTransaction.transaction_id
        ).filter(
            and_(
                AmortizationResult.year == year,
                EnrichedTransaction.level_2 == view.level_2_value
            )
        ).scalar()
    else:
        # Sommer tous les AmortizationResult pour l'année
        result = db.query(
            func.sum(func.abs(AmortizationResult.amount))
        ).filter(
            AmortizationResult.year == year
        ).scalar()
    
    return result if result else 0.0


def get_cout_financement(year: int, selected_loan_ids: Optional[List[int]], db: Session) -> float:
    """
    Calcule le coût du financement (intérêts + assurance) pour une année donnée.
    
    Si selected_loan_ids est fourni, filtre par les crédits sélectionnés (via loan_name).
    Sinon, somme tous les crédits.
    
    Args:
        year: Année pour laquelle calculer
        selected_loan_ids: Liste des IDs de crédits à inclure (optionnel)
        db: Session de base de données
        
    Returns:
        Total des intérêts + assurance pour l'année
    """
    # Filtrer les loan_payments pour l'année
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    query = db.query(LoanPayment).filter(
        and_(
            LoanPayment.date >= start_date,
            LoanPayment.date <= end_date
        )
    )
    
    # Si des crédits sont sélectionnés, filtrer par leurs noms
    if selected_loan_ids:
        # Récupérer les noms des crédits sélectionnés
        loan_configs = db.query(LoanConfig).filter(LoanConfig.id.in_(selected_loan_ids)).all()
        loan_names = [config.name for config in loan_configs]
        
        if loan_names:
            query = query.filter(LoanPayment.loan_name.in_(loan_names))
        else:
            # Aucun crédit trouvé, retourner 0
            return 0.0
    
    payments = query.all()
    
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
    
    # Ajouter les amortissements (chercher dans les mappings)
    amortization_mapping = next(
        (m for m in mappings if m.category_name == "Charges d'amortissements"),
        None
    )
    if amortization_mapping and amortization_mapping.amortization_view_id:
        amortissements = get_amortissements(year, amortization_mapping.amortization_view_id, db)
    else:
        amortissements = get_amortissements(year, amortization_view_id, db)
    charges["Charges d'amortissements"] = amortissements
    
    # Ajouter le coût du financement (chercher dans les mappings)
    financement_mapping = next(
        (m for m in mappings if m.category_name == "Coût du financement (hors remboursement du capital)"),
        None
    )
    if financement_mapping and financement_mapping.selected_loan_ids:
        loan_ids = financement_mapping.selected_loan_ids
        if isinstance(loan_ids, str):
            loan_ids = json.loads(loan_ids)
        cout_financement = get_cout_financement(year, loan_ids, db)
    else:
        cout_financement = get_cout_financement(year, None, db)
    charges["Coût du financement (hors remboursement du capital)"] = cout_financement
    
    # Calculer les totaux (AVANT d'ajouter le résultat dans categories_dict)
    total_produits = sum(produits.values())
    total_charges = sum(charges.values())
    resultat_exploitation = total_produits - total_charges
    resultat_net = resultat_exploitation  # Pour l'instant, résultat net = résultat d'exploitation
    
    # Construire le dictionnaire des catégories (produits + charges + résultat)
    # IMPORTANT: Le résultat n'est PAS dans charges, il est calculé séparément (Step 10.8.4.3)
    categories_dict = {**produits, **charges}
    categories_dict["Résultat de l'exercice"] = resultat_net
    
    return {
        "categories": categories_dict,
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


def calculate_amounts_by_category_and_year(
    years: List[int],
    db: Session
) -> Dict[int, Dict[str, float]]:
    """
    Calcule les montants par catégorie et année en utilisant les mappings configurés.
    
    Cette fonction utilise exclusivement les mappings configurés dans CompteResultatMapping.
    Pour chaque catégorie :
    - Si mapping level_1/level_2 : calcule depuis les transactions
    - Si "Charges d'amortissements" : utilise amortization_view_id du mapping
    - Si "Coût du financement" : utilise selected_loan_ids du mapping
    
    Args:
        years: Liste des années pour lesquelles calculer
        db: Session de base de données
        
    Returns:
        Dictionnaire {year: {category_name: amount}}
    """
    # Récupérer tous les mappings configurés
    mappings = get_mappings(db)
    
    if not mappings:
        return {year: {} for year in years}
    
    # Séparer les catégories spéciales
    special_categories = {
        "Charges d'amortissements": None,
        "Coût du financement (hors remboursement du capital)": None
    }
    
    # Trouver les mappings pour les catégories spéciales
    for mapping in mappings:
        if mapping.category_name == "Charges d'amortissements":
            special_categories["Charges d'amortissements"] = mapping
        elif mapping.category_name == "Coût du financement (hors remboursement du capital)":
            special_categories["Coût du financement (hors remboursement du capital)"] = mapping
    
    # Filtrer les mappings normaux (hors catégories spéciales)
    normal_mappings = [
        m for m in mappings
        if m.category_name not in special_categories
    ]
    
    # Grouper les mappings par catégorie (plusieurs mappings peuvent avoir la même catégorie)
    mappings_by_category: Dict[str, List[CompteResultatMapping]] = {}
    for mapping in normal_mappings:
        if mapping.category_name not in mappings_by_category:
            mappings_by_category[mapping.category_name] = []
        mappings_by_category[mapping.category_name].append(mapping)
    
    # Calculer les montants pour chaque année
    results: Dict[int, Dict[str, float]] = {}
    
    for year in years:
        year_results: Dict[str, float] = {}
        
        # Calculer les montants pour les catégories normales
        for category_name, category_mappings in mappings_by_category.items():
            # Déterminer si c'est un produit ou une charge
            produits_categories = [
                "Loyers hors charge encaissés",
                "Charges locatives payées par locataires",
                "Autres revenus"
            ]
            is_produit = category_name in produits_categories
            
            # Dates de début et fin d'année
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
            
            # Construire toutes les conditions pour cette catégorie
            conditions_list = []
            
            for mapping in category_mappings:
                # Construire les conditions pour ce mapping
                if mapping.level_1_values:
                    level_1_condition = EnrichedTransaction.level_1.in_(mapping.level_1_values)
                else:
                    level_1_condition = None
                
                level_2_condition = EnrichedTransaction.level_2.in_(mapping.level_2_values)
                
                if mapping.level_3_values:
                    level_3_condition = EnrichedTransaction.level_3.in_(mapping.level_3_values)
                else:
                    level_3_condition = None
                
                # Construire la condition : level_1 OU level_2 (si level_1 défini), ET level_3 si défini
                if level_1_condition is not None:
                    base_condition = or_(level_1_condition, level_2_condition)
                else:
                    base_condition = level_2_condition
                
                if level_3_condition is not None:
                    condition = and_(base_condition, level_3_condition)
                else:
                    condition = base_condition
                
                conditions_list.append(condition)
            
            # Combiner toutes les conditions pour cette catégorie avec OR
            # Cela évite de compter plusieurs fois les mêmes transactions
            if len(conditions_list) > 1:
                combined_condition = or_(*conditions_list)
            elif len(conditions_list) == 1:
                combined_condition = conditions_list[0]
            else:
                # Pas de mapping, skip
                year_results[category_name] = 0.0
                continue
            
            # Requête : transactions enrichies avec date dans l'année et correspondant aux conditions
            # Pour toutes les catégories, on doit prendre en compte les transactions positives ET négatives
            
            if is_produit:
                # Produits : revenus (positifs) - remboursements/annulations (négatifs)
                # Revenus (positifs) : somme
                query_positifs = db.query(
                    func.sum(Transaction.quantite).label('total_positifs')
                ).join(
                    EnrichedTransaction,
                    Transaction.id == EnrichedTransaction.transaction_id
                ).filter(
                    and_(
                        Transaction.date >= start_date,
                        Transaction.date <= end_date,
                        Transaction.quantite > 0,
                        combined_condition
                    )
                )
                total_positifs = query_positifs.scalar() or 0.0
                
                # Remboursements/annulations (négatifs) : somme des valeurs absolues
                query_negatifs = db.query(
                    func.sum(func.abs(Transaction.quantite)).label('total_negatifs')
                ).join(
                    EnrichedTransaction,
                    Transaction.id == EnrichedTransaction.transaction_id
                ).filter(
                    and_(
                        Transaction.date >= start_date,
                        Transaction.date <= end_date,
                        Transaction.quantite < 0,
                        combined_condition
                    )
                )
                total_negatifs = query_negatifs.scalar() or 0.0
                
                # Total : revenus - remboursements
                result = total_positifs - total_negatifs
            else:
                # Charges : dépenses (négatifs) - remboursements/crédits (positifs)
                # Dépenses (négatifs) : somme des valeurs absolues
                query_negatifs = db.query(
                    func.sum(func.abs(Transaction.quantite)).label('total_negatifs')
                ).join(
                    EnrichedTransaction,
                    Transaction.id == EnrichedTransaction.transaction_id
                ).filter(
                    and_(
                        Transaction.date >= start_date,
                        Transaction.date <= end_date,
                        Transaction.quantite < 0,
                        combined_condition
                    )
                )
                total_negatifs = query_negatifs.scalar() or 0.0
                
                # Remboursements/crédits (positifs) : somme
                query_positifs = db.query(
                    func.sum(Transaction.quantite).label('total_positifs')
                ).join(
                    EnrichedTransaction,
                    Transaction.id == EnrichedTransaction.transaction_id
                ).filter(
                    and_(
                        Transaction.date >= start_date,
                        Transaction.date <= end_date,
                        Transaction.quantite > 0,
                        combined_condition
                    )
                )
                total_positifs = query_positifs.scalar() or 0.0
                
                # Total : dépenses - remboursements
                result = total_negatifs - total_positifs
            
            
            year_results[category_name] = result if result else 0.0
        
        # Calculer les montants pour les catégories spéciales
        # Charges d'amortissements
        amortization_mapping = special_categories["Charges d'amortissements"]
        if amortization_mapping and amortization_mapping.amortization_view_id:
            amortissements = get_amortissements(year, amortization_mapping.amortization_view_id, db)
            year_results["Charges d'amortissements"] = amortissements
        elif amortization_mapping:
            # Mapping existe mais pas de vue sélectionnée
            year_results["Charges d'amortissements"] = 0.0
        
        # Coût du financement
        financement_mapping = special_categories["Coût du financement (hors remboursement du capital)"]
        if financement_mapping and financement_mapping.selected_loan_ids:
            # Parser selected_loan_ids (peut être une liste JSON)
            loan_ids = financement_mapping.selected_loan_ids
            if isinstance(loan_ids, str):
                loan_ids = json.loads(loan_ids)
            cout_financement = get_cout_financement(year, loan_ids, db)
            year_results["Coût du financement (hors remboursement du capital)"] = cout_financement
        elif financement_mapping:
            # Mapping existe mais pas de crédits sélectionnés
            year_results["Coût du financement (hors remboursement du capital)"] = 0.0
        
        results[year] = year_results
    
    return results

