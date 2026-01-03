"""
Service for calculating balance sheet (bilan).

⚠️ Before making changes, read: ../../../docs/workflow/BEST_PRACTICES.md
"""

from datetime import date, datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from backend.database.models import (
    BilanMapping,
    BilanData,
    Transaction,
    EnrichedTransaction,
    AmortizationResult,
    LoanPayment,
    LoanConfig,
    CompteResultatData,
    AmortizationView
)


def get_mappings(db: Session) -> List[BilanMapping]:
    """
    Charge tous les mappings depuis la table.
    
    Args:
        db: Session de base de données
        
    Returns:
        Liste des mappings
    """
    return db.query(BilanMapping).all()


def calculate_normal_category(
    year: int,
    mapping: BilanMapping,
    selected_level_3_values: Optional[List[str]],
    db: Session
) -> float:
    """
    Calcule le montant pour une catégorie normale depuis les transactions enrichies.
    
    Args:
        year: Année pour laquelle calculer
        mapping: Mapping de la catégorie
        selected_level_3_values: Liste des level_3 à inclure (optionnel)
        db: Session de base de données
        
    Returns:
        Montant pour cette catégorie
    """
    if not mapping.level_1_values:
        return 0.0
    
    # Pour le bilan, on calcule le solde cumulé jusqu'à la fin de l'année
    # Donc on prend toutes les transactions jusqu'au 31 décembre de l'année (pas seulement celles de l'année)
    end_date = date(year, 12, 31)
    
    # Condition pour level_1
    level_1_condition = EnrichedTransaction.level_1.in_(mapping.level_1_values)
    
    # Condition pour level_3 si selected_level_3_values est fourni
    # IMPORTANT: Filtrer les valeurs pour ne garder que celles qui existent réellement dans les transactions
    level_3_condition = None
    if selected_level_3_values:
        # Vérifier quelles valeurs level_3 existent réellement dans la base
        existing_level_3 = db.query(EnrichedTransaction.level_3).distinct().filter(
            EnrichedTransaction.level_3.in_(selected_level_3_values)
        ).all()
        valid_level_3_values = [v[0] for v in existing_level_3 if v[0] is not None]
        
        if valid_level_3_values:
            level_3_condition = EnrichedTransaction.level_3.in_(valid_level_3_values)
        # Si aucune valeur valide, on ignore le filtre level_3 (comme si selected_level_3_values était None)
    
    # Construire la condition finale
    # IMPORTANT: Ne pas utiliser if level_3_condition car c'est un objet SQLAlchemy, pas un booléen
    if level_3_condition is not None:
        condition = and_(level_1_condition, level_3_condition)
    else:
        condition = level_1_condition
    
    # Requête : somme des montants des transactions enrichies
    # Pour le bilan, on prend la somme algébrique (positif + négatif) de TOUTES les transactions jusqu'à la fin de l'année
    query = db.query(
        func.sum(Transaction.quantite).label('total')
    ).join(
        EnrichedTransaction,
        Transaction.id == EnrichedTransaction.transaction_id
    ).filter(
        and_(
            Transaction.date <= end_date,  # Toutes les transactions jusqu'à la fin de l'année
            condition
        )
    )
    
    result = query.scalar()
    
    # IMPORTANT: Dans un bilan, toutes les valeurs doivent être positives (valeur comptable)
    # Les transactions peuvent être négatives, mais dans le bilan on affiche la valeur absolue
    if result is None:
        return 0.0
    
    # Retourner la valeur absolue pour avoir une valeur comptable positive
    return abs(result)


def calculate_amortizations_cumul(
    year: int,
    amortization_view_id: Optional[int],
    db: Session
) -> float:
    """
    Calcule le cumul des amortissements jusqu'à l'année (inclus).
    
    Args:
        year: Année jusqu'à laquelle cumuler
        amortization_view_id: ID de la vue d'amortissement (optionnel)
        db: Session de base de données
        
    Returns:
        Cumul des amortissements (montant négatif pour diminuer l'actif)
    """
    if amortization_view_id:
        # Récupérer la vue d'amortissement
        view = db.query(AmortizationView).filter(AmortizationView.id == amortization_view_id).first()
        if not view:
            return 0.0
        
        # Filtrer les AmortizationResult par level_2_value de la vue
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
                AmortizationResult.year <= year,
                EnrichedTransaction.level_2 == view.level_2_value
            )
        ).scalar()
    else:
        # Sommer tous les AmortizationResult jusqu'à l'année
        result = db.query(
            func.sum(func.abs(AmortizationResult.amount))
        ).filter(
            AmortizationResult.year <= year
        ).scalar()
    
    # Retourner en négatif pour diminuer l'actif
    return -(result if result else 0.0)


def calculate_compte_bancaire(
    year: int,
    db: Session
) -> float:
    """
    Calcule le solde bancaire final de l'année (solde de la dernière transaction de l'année).
    
    Args:
        year: Année pour laquelle calculer
        db: Session de base de données
        
    Returns:
        Solde bancaire final de l'année
    """
    # Dernière transaction de l'année
    last_transaction = db.query(Transaction).filter(
        Transaction.date <= date(year, 12, 31)
    ).order_by(desc(Transaction.date), desc(Transaction.id)).first()
    
    if last_transaction:
        return last_transaction.solde
    return 0.0


def calculate_resultat_exercice(
    year: int,
    db: Session
) -> float:
    """
    Récupère le résultat de l'exercice depuis le compte de résultat.
    
    Args:
        year: Année pour laquelle récupérer
        db: Session de base de données
        
    Returns:
        Résultat de l'exercice (bénéfice positif, perte négative)
    """
    # Chercher dans CompteResultatData pour la catégorie "Résultat de l'exercice"
    result = db.query(CompteResultatData).filter(
        and_(
            CompteResultatData.annee == year,
            CompteResultatData.category_name == "Résultat de l'exercice"
        )
    ).first()
    
    if result:
        return result.amount
    
    # Sinon, chercher "Résultat net" ou calculer depuis les totaux
    result_net = db.query(CompteResultatData).filter(
        and_(
            CompteResultatData.annee == year,
            CompteResultatData.category_name == "Résultat net"
        )
    ).first()
    
    if result_net:
        return result_net.amount
    
    return 0.0


def calculate_report_a_nouveau(
    year: int,
    db: Session
) -> float:
    """
    Calcule le report à nouveau (cumul des résultats des années précédentes).
    
    Args:
        year: Année pour laquelle calculer
        db: Session de base de données
        
    Returns:
        Report à nouveau (cumul des résultats précédents)
    """
    # Première année : pas de report
    if year <= 1:
        return 0.0
    
    # Cumuler les résultats de toutes les années précédentes
    start_year = db.query(func.min(CompteResultatData.annee)).scalar()
    if not start_year:
        return 0.0
    
    # Calculer le cumul des résultats jusqu'à l'année précédente
    total = 0.0
    for y in range(start_year, year):
        resultat = calculate_resultat_exercice(y, db)
        total += resultat
    
    return total


def calculate_capital_restant_du(
    year: int,
    db: Session
) -> float:
    """
    Calcule le capital restant dû au 31/12 de l'année.
    
    Calcul : Crédit accordé - Cumulé des remboursements de capital (année par année)
    
    Args:
        year: Année pour laquelle calculer
        db: Session de base de données
        
    Returns:
        Capital restant dû (montant positif, dette)
    """
    # Récupérer tous les crédits configurés
    loan_configs = db.query(LoanConfig).all()
    
    if not loan_configs:
        return 0.0
    
    total_capital_restant = 0.0
    
    for loan_config in loan_configs:
        # Montant du crédit accordé
        credit_amount = loan_config.credit_amount
        
        # Cumul des remboursements de capital jusqu'à la fin de l'année
        cumul_capital = db.query(
            func.sum(LoanPayment.capital)
        ).filter(
            and_(
                LoanPayment.loan_name == loan_config.name,
                LoanPayment.date <= date(year, 12, 31)
            )
        ).scalar()
        
        cumul_capital = cumul_capital if cumul_capital else 0.0
        
        # Capital restant dû = Crédit accordé - Cumul remboursé
        capital_restant = credit_amount - cumul_capital
        total_capital_restant += capital_restant
    
    return total_capital_restant


def calculate_bilan(
    year: int,
    mappings: List[BilanMapping],
    selected_level_3_values: Optional[List[str]],
    db: Session
) -> Dict[str, any]:
    """
    Calcule le bilan complet pour une année donnée.
    
    Args:
        year: Année pour laquelle calculer
        mappings: Liste des mappings à utiliser
        selected_level_3_values: Liste des level_3 à inclure (optionnel)
        db: Session de base de données
        
    Returns:
        Dictionnaire avec:
        - categories: {category_name: amount}
        - sub_category_totals: {sub_category: total}
        - type_totals: {type: total}
        - equilibre: {"actif": total, "passif": total, "difference": diff, "percentage": pct}
    """
    categories = {}
    
    # Calculer chaque catégorie
    for mapping in mappings:
        if mapping.is_special:
            # Catégorie spéciale
            if mapping.special_source == "amortizations":
                amount = calculate_amortizations_cumul(year, mapping.amortization_view_id, db)
            elif mapping.special_source == "transactions":
                amount = calculate_compte_bancaire(year, db)
            elif mapping.special_source == "compte_resultat":
                amount = calculate_resultat_exercice(year, db)
            elif mapping.special_source == "compte_resultat_cumul":
                amount = calculate_report_a_nouveau(year, db)
            elif mapping.special_source == "loan_payments":
                amount = calculate_capital_restant_du(year, db)
            else:
                amount = 0.0
        else:
            # Catégorie normale
            amount = calculate_normal_category(year, mapping, selected_level_3_values, db)
        
        # IMPORTANT: Dans un bilan, toutes les valeurs doivent être positives (valeur comptable)
        # Appliquer la valeur absolue pour toutes les catégories
        categories[mapping.category_name] = abs(amount) if amount is not None else 0.0
    
    # Calculer les totaux par sous-catégorie (niveau B)
    sub_category_totals = {}
    for mapping in mappings:
        sub_cat = mapping.sub_category
        if sub_cat not in sub_category_totals:
            sub_category_totals[sub_cat] = 0.0
        sub_category_totals[sub_cat] += categories.get(mapping.category_name, 0.0)
    
    # Calculer les totaux par type (niveau A)
    type_totals = {"ACTIF": 0.0, "PASSIF": 0.0}
    for mapping in mappings:
        type_name = mapping.type
        if type_name in type_totals:
            type_totals[type_name] += categories.get(mapping.category_name, 0.0)
    
    # Calculer l'équilibre ACTIF = PASSIF
    total_actif = type_totals["ACTIF"]
    total_passif = type_totals["PASSIF"]
    difference = total_actif - total_passif
    
    # Pourcentage de différence
    if total_actif != 0:
        percentage = (difference / total_actif) * 100
    else:
        percentage = 0.0
    
    return {
        "categories": categories,
        "sub_category_totals": sub_category_totals,
        "type_totals": type_totals,
        "equilibre": {
            "actif": total_actif,
            "passif": total_passif,
            "difference": difference,
            "percentage": percentage
        }
    }


def invalidate_all_bilan(db: Session):
    """
    Marque toutes les données du bilan comme invalides (supprime toutes les données).
    """
    db.query(BilanData).delete()
    db.commit()


def invalidate_bilan_for_year(year: int, db: Session):
    """
    Marque les données du bilan pour une année spécifique comme invalides.
    
    Args:
        year: Année à invalider
        db: Session de base de données
    """
    db.query(BilanData).filter(BilanData.annee == year).delete()
    db.commit()


def get_bilan_data(
    db: Session,
    year: Optional[int] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None
) -> List[BilanData]:
    """
    Récupère les données du bilan avec filtres optionnels.
    
    Args:
        db: Session de base de données
        year: Année spécifique (optionnel)
        start_year: Année de début (optionnel)
        end_year: Année de fin (optionnel)
        
    Returns:
        Liste des données du bilan
    """
    query = db.query(BilanData)
    
    if year:
        query = query.filter(BilanData.annee == year)
    elif start_year and end_year:
        query = query.filter(
            and_(
                BilanData.annee >= start_year,
                BilanData.annee <= end_year
            )
        )
    elif start_year:
        query = query.filter(BilanData.annee >= start_year)
    elif end_year:
        query = query.filter(BilanData.annee <= end_year)
    
    return query.all()

