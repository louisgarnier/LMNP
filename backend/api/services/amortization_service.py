"""
Service de calcul des amortissements avec convention 30/360.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce service implémente la logique de calcul des amortissements :
- Convention 30/360 pour le calcul des jours
- Répartition proportionnelle par année
- Utilisation des AmortizationType pour le matching des transactions
"""

import json
from datetime import date, datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.database.models import (
    Transaction,
    EnrichedTransaction,
    AmortizationType,
    AmortizationResult
)


def calculate_30_360_days(start_date: date, end_date: date) -> int:
    """
    Calcule le nombre de jours entre deux dates selon la convention 30/360.
    
    Convention 30/360 :
    - Chaque mois compte 30 jours
    - Chaque année compte 360 jours
    - Formule : (année2 - année1) * 360 + (mois2 - mois1) * 30 + (jour2 - jour1)
    
    Args:
        start_date: Date de début
        end_date: Date de fin
    
    Returns:
        Nombre de jours selon la convention 30/360
    """
    days = (end_date.year - start_date.year) * 360
    days += (end_date.month - start_date.month) * 30
    days += end_date.day - start_date.day
    return days


def calculate_yearly_amounts(
    start_date: date,
    total_amount: float,
    duration: float,
    annual_amount: Optional[float] = None
) -> Dict[int, float]:
    """
    Calcule la répartition des montants d'amortissement par année.
    
    Logique :
    - Si annual_amount est fourni, l'utiliser directement
    - Sinon, calculer : annual_amount = abs(total_amount) / duration
    - Calculer le montant journalier : daily_amount = annual_amount / 360
    - Répartir proportionnellement par année selon la convention 30/360
    - Dernière année = solde restant pour garantir somme exacte
    
    Args:
        start_date: Date de début d'amortissement
        total_amount: Montant total à amortir (peut être négatif)
        duration: Durée d'amortissement en années
        annual_amount: Annuité d'amortissement (override, optionnel)
    
    Returns:
        Dictionnaire {année: montant} avec montants négatifs
    """
    if duration <= 0:
        return {}
    
    # Utiliser annual_amount si fourni, sinon calculer
    if annual_amount is None or annual_amount == 0:
        annual_amount = abs(total_amount) / duration
    else:
        annual_amount = abs(annual_amount)
    
    # Montant journalier selon convention 30/360
    daily_amount = annual_amount / 360
    
    # Calculer la date de fin (fin de la dernière année)
    # Si duration = 5 ans et start_date = 2024-01-01, alors on amortit jusqu'à 2028-12-31
    end_year = start_date.year + int(duration) - 1
    end_date = date(end_year, 12, 31)
    
    yearly_amounts = {}
    total_calculated = 0.0
    
    # Calculer pour chaque année concernée
    current_date = start_date
    current_year = start_date.year
    
    while current_year <= end_year:
        # Déterminer la fin de l'année courante
        year_end = date(current_year, 12, 31)
        period_end = min(end_date, year_end)
        
        # Calculer les jours pour cette période
        days_in_period = calculate_30_360_days(current_date, period_end)
        if days_in_period > 0:
            amount = daily_amount * days_in_period
            
            # Ajouter au total de l'année
            if current_year in yearly_amounts:
                yearly_amounts[current_year] += amount
            else:
                yearly_amounts[current_year] = amount
            
            total_calculated += amount
        
        # Passer à l'année suivante
        current_date = date(current_year + 1, 1, 1)
        current_year += 1
    
    # Convertir en montants négatifs et ajuster la dernière année
    if yearly_amounts:
        # Convertir en négatif
        for year in yearly_amounts:
            yearly_amounts[year] = -yearly_amounts[year]
        
        # Ajuster la dernière année pour garantir somme exacte
        last_year = max(yearly_amounts.keys())
        remaining = abs(total_amount) - total_calculated
        if remaining > 0:
            yearly_amounts[last_year] = -(abs(yearly_amounts[last_year]) + remaining)
    
    return yearly_amounts


def recalculate_transaction_amortization(
    db: Session,
    transaction_id: int
) -> int:
    """
    Recalcule les amortissements pour une transaction donnée.
    
    Logique :
    1. Récupérer la transaction et son EnrichedTransaction
    2. Trouver le AmortizationType correspondant (level_2 + level_1)
    3. Si type trouvé et duration > 0 :
       - Calculer les montants par année
       - Supprimer les anciens résultats
       - Créer les nouveaux résultats
    
    Args:
        db: Session de base de données
        transaction_id: ID de la transaction
    
    Returns:
        Nombre de résultats d'amortissement créés
    """
    # Récupérer la transaction
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        return 0
    
    # Récupérer l'enrichissement
    enriched = db.query(EnrichedTransaction).filter(
        EnrichedTransaction.transaction_id == transaction_id
    ).first()
    
    if not enriched or not enriched.level_2 or not enriched.level_1:
        # Pas d'enrichissement ou pas de level_2/level_1 → supprimer les résultats existants
        db.query(AmortizationResult).filter(
            AmortizationResult.transaction_id == transaction_id
        ).delete()
        db.commit()
        return 0
    
    # Trouver le type d'amortissement correspondant
    amortization_types = db.query(AmortizationType).filter(
        AmortizationType.level_2_value == enriched.level_2
    ).all()
    
    matching_type = None
    for atype in amortization_types:
        level_1_values = json.loads(atype.level_1_values or "[]")
        if enriched.level_1 in level_1_values:
            matching_type = atype
            break
    
    if not matching_type or matching_type.duration <= 0:
        # Pas de type correspondant ou durée = 0 → supprimer les résultats existants
        db.query(AmortizationResult).filter(
            AmortizationResult.transaction_id == transaction_id
        ).delete()
        db.commit()
        return 0
    
    # Déterminer la date de début
    start_date = matching_type.start_date if matching_type.start_date else transaction.date
    
    # Calculer les montants par année
    yearly_amounts = calculate_yearly_amounts(
        start_date=start_date,
        total_amount=transaction.quantite,
        duration=matching_type.duration,
        annual_amount=matching_type.annual_amount
    )
    
    # Supprimer les anciens résultats
    db.query(AmortizationResult).filter(
        AmortizationResult.transaction_id == transaction_id
    ).delete()
    
    # Créer les nouveaux résultats
    created_count = 0
    for year, amount in yearly_amounts.items():
        result = AmortizationResult(
            transaction_id=transaction_id,
            year=year,
            category=matching_type.name,
            amount=amount
        )
        db.add(result)
        created_count += 1
    
    db.commit()
    return created_count


def recalculate_all_amortizations(db: Session) -> int:
    """
    Recalcule tous les amortissements pour toutes les transactions.
    
    Args:
        db: Session de base de données
    
    Returns:
        Nombre total de résultats d'amortissement créés
    """
    # Récupérer toutes les transactions avec enrichissement
    transactions = db.query(Transaction).join(EnrichedTransaction).all()
    
    total_created = 0
    for transaction in transactions:
        created = recalculate_transaction_amortization(db, transaction.id)
        total_created += created
    
    return total_created


def validate_amortization_sum(
    db: Session,
    transaction_id: int,
    expected_total: float
) -> bool:
    """
    Valide que la somme des amortissements = montant initial.
    
    Args:
        db: Session de base de données
        transaction_id: ID de la transaction
        expected_total: Montant total attendu (absolu)
    
    Returns:
        True si la somme est correcte, False sinon
    """
    results = db.query(AmortizationResult).filter(
        AmortizationResult.transaction_id == transaction_id
    ).all()
    
    total = sum(abs(r.amount) for r in results)
    return abs(total - expected_total) < 0.01  # Tolérance de 1 centime

