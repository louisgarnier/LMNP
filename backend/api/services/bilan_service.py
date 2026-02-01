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
import logging
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

logger = logging.getLogger(__name__)


def get_mappings(db: Session, property_id: int) -> List[BilanMapping]:
    """
    Charger tous les mappings depuis la table pour une propriété.
    
    Args:
        db: Session de base de données
        property_id: ID de la propriété
    
    Returns:
        Liste des mappings configurés
    """
    logger.info(f"[BilanService] get_mappings - property_id={property_id}")
    return db.query(BilanMapping).filter(
        BilanMapping.property_id == property_id
    ).order_by(
        BilanMapping.type,
        BilanMapping.sub_category,
        BilanMapping.category_name
    ).all()


def get_level_3_values(db: Session, property_id: int) -> List[str]:
    """
    Récupérer les valeurs level_3 sélectionnées depuis la configuration pour une propriété.
    
    Args:
        db: Session de base de données
        property_id: ID de la propriété
    
    Returns:
        Liste des valeurs level_3 sélectionnées (vide si aucune config)
    """
    logger.info(f"[BilanService] get_level_3_values - property_id={property_id}")
    config = db.query(BilanConfig).filter(BilanConfig.property_id == property_id).first()
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
    level_3_values: List[str],
    property_id: int
) -> float:
    """
    Calculer le montant cumulé d'une catégorie normale depuis les transactions enrichies.
    
    Logique :
    1. Filtrer par level_3 (seules les transactions avec level_3 dans level_3_values)
    2. Filtrer par date (toutes les transactions jusqu'à la fin de l'année - CUMUL)
    3. Filtrer par level_1 (selon level_1_values du mapping)
    4. Filtrer par property_id
    5. Sommer les montants (cumul depuis le début jusqu'à l'année)
    
    Pour les immobilisations et autres catégories normales, on calcule le cumul :
    - Année 2021 : somme de toutes les transactions jusqu'au 31/12/2021
    - Année 2022 : somme de toutes les transactions jusqu'au 31/12/2022 (inclut 2021)
    - etc.
    
    Args:
        db: Session de base de données
        year: Année jusqu'à laquelle cumuler
        mapping: Mapping de la catégorie
        level_3_values: Liste des valeurs level_3 à considérer
        property_id: ID de la propriété
    
    Returns:
        Montant cumulé pour cette catégorie jusqu'à l'année
    """
    logger.info(f"[BilanService] calculate_normal_category - year={year}, property_id={property_id}")
    
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
    
    # Date de fin de l'année (cumul jusqu'à cette date)
    end_date = date(year, 12, 31)
    
    # Filtrer les transactions par level_3, level_1, property_id et cumul jusqu'à la fin de l'année
    query = db.query(
        func.sum(Transaction.quantite)
    ).join(
        EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
    ).filter(
        and_(
            Transaction.property_id == property_id,
            EnrichedTransaction.level_3.in_(level_3_values),
            EnrichedTransaction.level_1.in_(level_1_values),
            Transaction.date <= end_date  # Cumul jusqu'à la fin de l'année
        )
    )
    
    result = query.scalar()
    if result is None:
        return 0.0
    
    # Pour le bilan, les montants doivent être positifs (actifs/passifs)
    # 
    # Logique selon le type (ACTIF ou PASSIF) :
    # - Pour ACTIF : si la somme est négative, retourner 0 (on ne peut pas avoir un actif négatif)
    # - Pour PASSIF : si la somme est négative, retourner 0 (on ne peut pas avoir une dette négative)
    # - Sinon, retourner la valeur absolue pour s'assurer que c'est positif
    #
    # Cas particulier : certaines catégories ont des transactions avec signes mixtes :
    # - Exemple "Cautions reçues" : paiements (positifs) - remboursements (négatifs) = montant net dû
    # - Si le résultat est négatif, cela signifie qu'on a remboursé plus qu'on a reçu, donc la dette = 0
    
    if result < 0:
        # Si la somme est négative, on ne peut pas avoir un actif/passif négatif
        return 0.0
    
    # Si la somme est positive, retourner la valeur absolue (pour gérer les cas où les transactions
    # sont toutes négatives mais représentent un actif/passif positif, comme pour les immobilisations)
    return abs(result)


def calculate_amortizations_cumul(
    db: Session,
    year: int,
    property_id: int
) -> float:
    """
    Calculer le cumul des amortissements jusqu'à l'année en cours pour une propriété.
    
    Logique :
    - Récupérer tous les amortissements de toutes les années <= year
    - Filtrer par property_id via la transaction associée
    - Sommer les montants (qui sont déjà négatifs)
    - Retourner la valeur négative (diminution de l'actif)
    
    Args:
        db: Session de base de données
        year: Année jusqu'à laquelle cumuler
        property_id: ID de la propriété
    
    Returns:
        Cumul des amortissements (négatif, car diminution de l'actif)
    """
    logger.info(f"[BilanService] calculate_amortizations_cumul - year={year}, property_id={property_id}")
    
    # JOIN avec Transaction pour filtrer par property_id
    result = db.query(
        func.sum(AmortizationResult.amount)
    ).join(
        Transaction, AmortizationResult.transaction_id == Transaction.id
    ).filter(
        and_(
            AmortizationResult.year <= year,
            Transaction.property_id == property_id
        )
    ).scalar()
    
    return result if result is not None else 0.0


def calculate_compte_bancaire(
    db: Session,
    year: int,
    property_id: int
) -> float:
    """
    Calculer le solde bancaire au 31/12 de l'année pour une propriété.
    
    Logique :
    - Récupérer la dernière transaction de l'année (ou avant si aucune transaction en décembre)
    - Filtrer par property_id
    - Utiliser le solde de cette transaction
    
    Args:
        db: Session de base de données
        year: Année à calculer
        property_id: ID de la propriété
    
    Returns:
        Solde bancaire au 31/12 (positif)
    """
    logger.info(f"[BilanService] calculate_compte_bancaire - year={year}, property_id={property_id}")
    
    # Date de fin de l'année
    end_date = date(year, 12, 31)
    
    # Récupérer la dernière transaction jusqu'à la fin de l'année pour cette propriété
    last_transaction = db.query(Transaction).filter(
        and_(
            Transaction.property_id == property_id,
            Transaction.date <= end_date
        )
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
    property_id: int,
    compte_resultat_view_id: Optional[int] = None
) -> float:
    """
    Calculer le résultat de l'exercice pour une année et une propriété.
    
    Logique :
    - Chercher un override pour l'année et la propriété (si existe, l'utiliser)
    - Sinon : utiliser le résultat net du compte de résultat
    
    Args:
        db: Session de base de données
        year: Année à calculer
        property_id: ID de la propriété
        compte_resultat_view_id: ID de la vue compte de résultat (optionnel, non utilisé pour l'instant)
    
    Returns:
        Résultat de l'exercice (bénéfice positif, perte négative)
    """
    logger.info(f"[BilanService] calculate_resultat_exercice - year={year}, property_id={property_id}")
    
    # Chercher un override pour l'année et la propriété
    override = db.query(CompteResultatOverride).filter(
        and_(
            CompteResultatOverride.year == year,
            CompteResultatOverride.property_id == property_id
        )
    ).first()
    
    if override:
        return override.override_value
    
    # Sinon, calculer depuis le compte de résultat
    compte_resultat = calculate_compte_resultat(db, year, property_id=property_id)
    return compte_resultat.get("resultat_net", 0.0)


def calculate_report_a_nouveau(
    db: Session,
    year: int,
    property_id: int
) -> float:
    """
    Calculer le report à nouveau (cumul des résultats des années précédentes) pour une propriété.
    
    Logique :
    - Cumuler les résultats de toutes les années < year qui ont des transactions
    - Première année : 0 (pas de report)
    
    Args:
        db: Session de base de données
        year: Année à calculer
        property_id: ID de la propriété
    
    Returns:
        Report à nouveau (cumul des résultats précédents)
    """
    logger.info(f"[BilanService] calculate_report_a_nouveau - year={year}, property_id={property_id}")
    
    # Trouver la première année avec des transactions pour cette propriété
    first_transaction = db.query(func.min(Transaction.date)).filter(
        Transaction.property_id == property_id
    ).scalar()
    if not first_transaction:
        return 0.0
    
    first_year = first_transaction.year if hasattr(first_transaction, 'year') else first_transaction
    
    if year <= first_year:
        return 0.0
    
    # OPTIMISATION: Calculer tous les résultats en une seule fois au lieu de boucler
    # Récupérer tous les overrides d'un coup pour cette propriété
    overrides = db.query(CompteResultatOverride).filter(
        and_(
            CompteResultatOverride.property_id == property_id,
            CompteResultatOverride.year >= first_year,
            CompteResultatOverride.year < year
        )
    ).all()
    override_dict = {o.year: o.override_value for o in overrides}
    
    # Calculer les années qui n'ont pas d'override
    total = 0.0
    years_to_calculate = []
    for prev_year in range(first_year, year):
        if prev_year in override_dict:
            total += override_dict[prev_year]
        else:
            years_to_calculate.append(prev_year)
    
    # Calculer les années sans override en une seule fois si possible
    if years_to_calculate:
        # Pour chaque année, calculer le compte de résultat
        # Note: On pourrait optimiser davantage en calculant toutes les années en une fois
        # mais pour l'instant, on garde la logique simple
        for prev_year in years_to_calculate:
            compte_resultat = calculate_compte_resultat(db, prev_year, property_id=property_id)
            total += compte_resultat.get("resultat_net", 0.0)
    
    return total


def calculate_capital_restant_du(
    db: Session,
    year: int,
    property_id: int
) -> float:
    """
    Calculer le capital restant dû au 31/12 de l'année pour une propriété.
    
    LOGIQUE :
    - Le montant du crédit accordé = somme des transactions avec level_1 = "Dettes financières (emprunt bancaire)" (cumul jusqu'au 31/12)
    - Le capital remboursé = cumul des remboursements de capital de TOUS les crédits actifs jusqu'au 31/12
    - Capital restant dû = Montant transactions - Capital remboursé
    
    IMPORTANT: 
    - On utilise les TRANSACTIONS comme source principale (pas LoanConfig.credit_amount)
    - On déduit le capital remboursé depuis les pages crédits (LoanPayment)
    - Si aucune transaction n'est trouvée, retourner 0
    
    Args:
        db: Session de base de données
        year: Année à calculer
        property_id: ID de la propriété
    
    Returns:
        Capital restant dû au 31/12 (positif, car dette)
    """
    logger.info(f"[BilanService] calculate_capital_restant_du - year={year}, property_id={property_id}")
    
    # Date de fin de l'année
    end_date = date(year, 12, 31)
    
    # Récupérer tous les crédits actifs pour cette propriété (qui ont commencé avant ou pendant l'année)
    # On a besoin de cette liste pour filtrer les paiements
    active_loans = db.query(LoanConfig).filter(
        and_(
            LoanConfig.property_id == property_id,
            or_(
                LoanConfig.loan_start_date.is_(None),
                LoanConfig.loan_start_date <= end_date
            )
        )
    ).all()
    
    # Calculer le montant du crédit accordé depuis les transactions réelles
    # Utiliser level_1 = "Dettes financières (emprunt bancaire)"
    level_1_value = "Dettes financières (emprunt bancaire)"
    
    credit_amount_from_transactions = db.query(
        func.sum(Transaction.quantite)
    ).join(
        EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
    ).filter(
        and_(
            Transaction.property_id == property_id,
            EnrichedTransaction.level_1 == level_1_value,
            Transaction.date <= end_date
        )
    ).scalar()
    
    # Le montant est négatif dans les transactions (débit), donc on prend la valeur absolue
    credit_amount = abs(credit_amount_from_transactions) if credit_amount_from_transactions is not None else 0.0
    
    # Si aucune transaction, retourner 0
    if credit_amount == 0.0:
        logger.info(f"[BilanService] calculate_capital_restant_du - Aucune transaction trouvée pour {year}, property_id={property_id}. Retour de 0.00 €")
        return 0.0
    
    # Calculer le capital remboursé depuis les pages crédits (LoanPayment)
    # Filtrer par les crédits actifs et la propriété
    if active_loans:
        active_loan_names = [loan.name for loan in active_loans]
        
        # Capital remboursé total de tous les crédits actifs de cette propriété
        capital_paid = db.query(
            func.sum(LoanPayment.capital)
        ).filter(
            and_(
                LoanPayment.property_id == property_id,
                LoanPayment.date <= end_date,
                LoanPayment.loan_name.in_(active_loan_names)
            )
        ).scalar()
    else:
        # Si aucun crédit actif, ne pas inclure de paiements
        capital_paid = 0.0
    
    capital_paid = capital_paid if capital_paid is not None else 0.0
    
    # Capital restant dû = Montant transactions - Capital remboursé
    remaining = credit_amount - capital_paid
    
    # Debug: Afficher le calcul
    logger.info(f"[BilanService] calculate_capital_restant_du - Calcul pour {year}, property_id={property_id}:")
    logger.info(f"  - Montant transactions (level_1 = 'Dettes financières (emprunt bancaire)'): {credit_amount:.2f} €")
    logger.info(f"  - Capital remboursé (tous crédits actifs): {capital_paid:.2f} €")
    logger.info(f"  - Capital restant dû: {remaining:.2f} €")
    
    # S'assurer que le résultat est positif (on ne peut pas avoir un capital restant négatif)
    return max(0.0, remaining)


def calculate_bilan(
    db: Session,
    year: int,
    property_id: int,
    mappings: Optional[List[BilanMapping]] = None,
    level_3_values: Optional[List[str]] = None
) -> Dict[str, any]:
    """
    Calculer le bilan complet pour une année et une propriété.
    
    Args:
        db: Session de base de données
        year: Année à calculer
        property_id: ID de la propriété
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
    logger.info(f"[BilanService] calculate_bilan - year={year}, property_id={property_id}")
    
    # Charger les mappings si non fournis
    if mappings is None:
        mappings = get_mappings(db, property_id)
    
    # Charger les level_3_values si non fournis
    if level_3_values is None:
        level_3_values = get_level_3_values(db, property_id)
    
    # Dictionnaire pour stocker les montants par catégorie
    categories = {}
    
    # OPTIMISATION: Calculer toutes les catégories normales en une seule requête
    normal_mappings = [m for m in mappings if not m.is_special]
    if normal_mappings:
        # Date de fin de l'année (cumul jusqu'à cette date)
        end_date = date(year, 12, 31)
        
        # Construire un dictionnaire category_name -> set(level_1_values)
        category_to_level_1 = {}
        all_level_1_values = set()
        for mapping in normal_mappings:
            if not mapping.level_1_values:
                continue
            try:
                level_1_values_list = json.loads(mapping.level_1_values)
                category_to_level_1[mapping.category_name] = set(level_1_values_list)
                all_level_1_values.update(level_1_values_list)
            except (json.JSONDecodeError, TypeError):
                continue
        
        if all_level_1_values:
            # Une seule requête pour toutes les catégories normales, filtrée par property_id
            query = db.query(
                EnrichedTransaction.level_1,
                func.sum(Transaction.quantite).label('total')
            ).join(
                Transaction, Transaction.id == EnrichedTransaction.transaction_id
            ).filter(
                and_(
                    Transaction.property_id == property_id,
                    EnrichedTransaction.level_3.in_(level_3_values),
                    EnrichedTransaction.level_1.in_(list(all_level_1_values)),
                    Transaction.date <= end_date
                )
            ).group_by(EnrichedTransaction.level_1)
            
            results = query.all()
            
            # Initialiser toutes les catégories normales à 0
            for mapping in normal_mappings:
                categories[mapping.category_name] = 0.0
            
            # Répartir les résultats par catégorie (chaque level_1 peut appartenir à plusieurs catégories)
            # IMPORTANT: On additionne d'abord les montants bruts (avec leurs signes), puis on applique la logique
            # à la somme finale. Cela permet de gérer correctement les catégories avec transactions mixtes
            # (ex: "Cautions reçues" avec paiements positifs et remboursements négatifs)
            for level_1, total in results:
                if level_1 and total is not None:
                    # Trouver toutes les catégories qui utilisent ce level_1
                    for category_name, level_1_set in category_to_level_1.items():
                        if level_1 in level_1_set:
                            # Additionner les montants bruts (avec leurs signes)
                            categories[category_name] += total
            
            # Appliquer la logique de signe à la somme finale de chaque catégorie
            # Construire un dictionnaire category_name -> type (ACTIF/PASSIF) pour déterminer la logique
            category_to_type = {}
            for mapping in normal_mappings:
                category_to_type[mapping.category_name] = mapping.type
            
            for category_name in categories:
                result = categories[category_name]
                category_type = category_to_type.get(category_name, "ACTIF")  # Par défaut ACTIF
                
                if category_type == "ACTIF":
                    # Pour les ACTIFS : toujours retourner la valeur absolue (positif)
                    # Les transactions sont souvent négatives (débits), mais l'actif doit être positif
                    categories[category_name] = abs(result) if result is not None else 0.0
                else:
                    # Pour les PASSIFS : si négatif → 0 (on ne peut pas avoir une dette négative)
                    # Sinon, valeur absolue pour garantir un montant positif
                    if result < 0:
                        categories[category_name] = 0.0
                    else:
                        categories[category_name] = abs(result) if result is not None else 0.0
    
    # Calculer les catégories spéciales (une par une, elles sont peu nombreuses)
    for mapping in mappings:
        if mapping.is_special:
            category_name = mapping.category_name
            if mapping.special_source == "amortization_result" or mapping.special_source == "amortizations":
                amount = calculate_amortizations_cumul(db, year, property_id)
            elif mapping.special_source == "transactions":
                amount = calculate_compte_bancaire(db, year, property_id)
            elif mapping.special_source == "compte_resultat":
                amount = calculate_resultat_exercice(
                    db, year, property_id, mapping.compte_resultat_view_id
                )
            elif mapping.special_source == "compte_resultat_cumul":
                amount = calculate_report_a_nouveau(db, year, property_id)
            elif mapping.special_source == "loan_payments":
                amount = calculate_capital_restant_du(db, year, property_id)
            else:
                amount = 0.0
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
    property_id: int,
    year: Optional[int] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None
) -> List[BilanData]:
    """
    Récupérer les données du bilan depuis la table bilan_data pour une propriété.
    
    Args:
        db: Session de base de données
        property_id: ID de la propriété
        year: Année spécifique (optionnel)
        start_year: Année de début (optionnel, pour plage)
        end_year: Année de fin (optionnel, pour plage)
    
    Returns:
        Liste des données du bilan
    """
    logger.info(f"[BilanService] get_bilan_data - property_id={property_id}, year={year}")
    
    query = db.query(BilanData).filter(BilanData.property_id == property_id)
    
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


def invalidate_all_bilan(db: Session, property_id: int) -> None:
    """
    Marquer toutes les données du bilan comme invalides pour une propriété (supprimer toutes les données).
    
    Args:
        db: Session de base de données
        property_id: ID de la propriété
    """
    logger.info(f"[BilanService] invalidate_all_bilan - property_id={property_id}")
    db.query(BilanData).filter(BilanData.property_id == property_id).delete()
    db.commit()


def invalidate_bilan_for_year(year: int, db: Session, property_id: int) -> None:
    """
    Invalider une année spécifique pour une propriété (supprimer les données de cette année).
    
    Args:
        year: Année à invalider
        db: Session de base de données
        property_id: ID de la propriété
    """
    logger.info(f"[BilanService] invalidate_bilan_for_year - year={year}, property_id={property_id}")
    db.query(BilanData).filter(
        and_(
            BilanData.annee == year,
            BilanData.property_id == property_id
        )
    ).delete()
    db.commit()
