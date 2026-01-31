"""
Service de calcul des amortissements avec convention 30/360.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce service implémente la logique de calcul des amortissements :
- Convention 30/360 pour le calcul des jours
- Répartition proportionnelle par année
- Utilisation des AmortizationType pour le matching des transactions
"""

import json
import logging
from datetime import date, datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from dateutil.relativedelta import relativedelta

from backend.database.models import (
    Transaction,
    EnrichedTransaction,
    AmortizationType,
    AmortizationResult
)

logger = logging.getLogger(__name__)


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
    
    Logique SIMPLE :
    1. Annuité = abs(total_amount) / duration (ou annual_amount si fourni)
    2. Année d'achat (première année) : prorata temporis avec convention 30/360
    3. Années complètes : annuité exacte
    4. Dernière année : solde restant (pour garantir somme exacte)
    
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
    
    # Calculer l'annuité
    if annual_amount is None or annual_amount == 0:
        annual_amount = abs(total_amount) / duration
    else:
        annual_amount = abs(annual_amount)
    
    # Calculer la date de fin exacte : start_date + duration années
    from dateutil.relativedelta import relativedelta
    exact_end_date = start_date + relativedelta(years=int(duration))
    end_year = exact_end_date.year
    
    yearly_amounts = {}
    daily_amount = annual_amount / 360
    
    # Cas spécial : tout dans une seule année
    if start_date.year == end_year:
        days_in_period = calculate_30_360_days(start_date, exact_end_date)
        if days_in_period > 0:
            yearly_amounts[start_date.year] = daily_amount * days_in_period
    else:
        # 1. PREMIÈRE ANNÉE (année d'achat) : partielle
        # Du start_date à la fin de l'année
        first_year_end = date(start_date.year, 12, 31)
        days_in_first_year = calculate_30_360_days(start_date, first_year_end)
        first_year_amount = daily_amount * days_in_first_year
        yearly_amounts[start_date.year] = first_year_amount
        
        # 2. ANNÉES COMPLÈTES : annuité exacte
        # Toutes les années entre la première et la dernière (années complètes)
        for year in range(start_date.year + 1, end_year):
            yearly_amounts[year] = annual_amount
        
        # 3. DERNIÈRE ANNÉE : partielle aussi !
        # Du début de l'année jusqu'à la date de fin exacte
        last_year_start = date(end_year, 1, 1)
        days_in_last_year = calculate_30_360_days(last_year_start, exact_end_date)
        last_year_amount = daily_amount * days_in_last_year
        yearly_amounts[end_year] = last_year_amount
        
        # 4. VÉRIFICATION : si le total ne correspond pas exactement, ajuster la dernière année
        total_calculated = sum(yearly_amounts.values())
        difference = abs(total_amount) - total_calculated
        if abs(difference) > 0.01:  # Tolérance de 0.01€ pour les arrondis
            # Ajuster la dernière année pour garantir la somme exacte
            yearly_amounts[end_year] += difference
    
    # Convertir toutes les années en négatif
    for year in yearly_amounts:
        yearly_amounts[year] = -yearly_amounts[year]
    
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
    
    # Trouver le type d'amortissement correspondant (filtré par property_id de la transaction)
    amortization_types = db.query(AmortizationType).filter(
        AmortizationType.property_id == transaction.property_id,
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


def recalculate_all_amortizations(db: Session, property_id: int) -> int:
    """
    Recalcule tous les amortissements pour toutes les transactions d'une propriété.
    
    Args:
        db: Session de base de données
        property_id: ID de la propriété (obligatoire)
    
    Returns:
        Nombre total de résultats d'amortissement créés
    """
    logger.info(f"[AmortizationService] Recalcul tous les amortissements pour property_id={property_id}")
    
    # Récupérer toutes les transactions avec enrichissement (filtrées par property_id)
    transactions = db.query(Transaction).join(EnrichedTransaction).filter(
        Transaction.property_id == property_id
    ).all()
    
    total_created = 0
    for transaction in transactions:
        created = recalculate_transaction_amortization(db, transaction.id)
        total_created += created
        if created > 0:
            logger.debug(f"[AmortizationService] Recalcul amortissement transaction {transaction.id} pour property_id={property_id}: {created} résultats créés")
    
    logger.info(f"[AmortizationService] Recalcul terminé pour property_id={property_id}: {total_created} résultats créés au total")
    
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

