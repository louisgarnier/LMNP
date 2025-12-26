"""
Service for calculating amortizations using 30/360 convention.

⚠️ Before making changes, read: ../../../docs/workflow/BEST_PRACTICES.md
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from backend.database.models import (
    Transaction, EnrichedTransaction, AmortizationConfig, AmortizationResult, AmortizationType
)


def calculate_30_360_days(start_date: datetime, end_date: datetime) -> int:
    """
    Calculate number of days between two dates using 30/360 convention.
    
    Convention 30/360:
    - Each month has 30 days
    - Each year has 360 days
    - If day is 31, treat it as 30
    - If end day is 31 and start day >= 30, treat end day as 30
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        Number of days using 30/360 convention
    """
    y1, m1, d1 = start_date.year, start_date.month, start_date.day
    y2, m2, d2 = end_date.year, end_date.month, end_date.day
    
    # Adjust day 31 to 30
    if d1 == 31:
        d1 = 30
    if d2 == 31 and d1 >= 30:
        d2 = 30
        
    return (360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1))


def calculate_yearly_amounts(
    start_date: datetime, 
    total_amount: float, 
    duration_years: float
) -> Dict[int, float]:
    """
    Calculate the amortization amounts for each year ensuring the total equals the transaction amount.
    
    Uses 30/360 convention and proportional distribution:
    - Calculate daily amount (total_amount / total_days)
    - For each year, calculate days in that year using 30/360
    - Distribute amount proportionally
    - Last year gets remaining amount to ensure exact total
    
    Args:
        start_date: Start date of amortization
        total_amount: Total amount to amortize (positive value)
        duration_years: Duration in years (e.g., 10.0, 20.0)
        
    Returns:
        Dictionary mapping year -> amount (negative, as it's an expense)
    """
    yearly_amounts = {}
    total_days = int(duration_years * 360)  # Total days using 30/360 convention
    end_date = start_date + timedelta(days=total_days)
    daily_amount = total_amount / total_days
    
    # Process each year
    current_date = start_date
    remaining_amount = total_amount
    
    while current_date.year <= end_date.year:
        year = current_date.year
        year_end = min(datetime(year, 12, 31), end_date)
        
        # Calculate days in this year using 30/360
        if year not in yearly_amounts:
            yearly_amounts[year] = 0.0
            
        days_in_year = calculate_30_360_days(current_date, year_end)
        amount = days_in_year * daily_amount
        
        # For the last year, use remaining amount to ensure exact total
        if year == end_date.year:
            amount = remaining_amount
        
        yearly_amounts[year] = amount
        remaining_amount -= amount
        
        # Move to next year
        current_date = datetime(year + 1, 1, 1)
    
    return yearly_amounts


def get_amortization_category(
    level_1: Optional[str],
    config: AmortizationConfig
) -> Optional[str]:
    """
    Determine the amortization category (part_terrain, structure_go, mobilier, igt, agencements, facade_toiture, travaux) 
    based on level_1 value and configuration.
    
    Args:
        level_1: Value of level_1 field
        config: Amortization configuration
        
    Returns:
        Category name (part_terrain, structure_go, mobilier, igt, agencements, facade_toiture, travaux) or None
    """
    if not level_1:
        return None
    
    level_3_mapping = config.level_3_mapping  # Note: nom du champ JSON reste level_3_mapping pour compatibilité
    if not isinstance(level_3_mapping, dict):
        return None
    
    # Check each category's mapping (7 catégories)
    for category in ["part_terrain", "structure_go", "mobilier", "igt", "agencements", "facade_toiture", "travaux"]:
        if category in level_3_mapping:
            level_1_values = level_3_mapping[category]  # Les valeurs dans le mapping sont des level_1
            if isinstance(level_1_values, list) and level_1 in level_1_values:
                return category
    
    return None


def get_amortization_duration(category: str, config: AmortizationConfig) -> Optional[float]:
    """
    Get the amortization duration for a given category.
    
    Args:
        category: Category name (part_terrain, structure_go, mobilier, igt, agencements, facade_toiture, travaux)
        config: Amortization configuration
        
    Returns:
        Duration in years or None if category not found
    """
    duration_map = {
        "part_terrain": config.duration_part_terrain,
        "structure_go": config.duration_structure_go,
        "mobilier": config.duration_mobilier,
        "igt": config.duration_igt,
        "agencements": config.duration_agencements,
        "facade_toiture": config.duration_facade_toiture,
        "travaux": config.duration_travaux,
    }
    return duration_map.get(category)


def recalculate_transaction_amortization(
    transaction_id: int,
    db: Session
) -> List[AmortizationResult]:
    """
    Recalculate amortization for a single transaction using AmortizationType.
    
    Steps:
    1. Get transaction and enriched transaction
    2. Find matching AmortizationType (level_2 and level_1)
    3. Calculate yearly amounts using type's duration and annual_amount
    4. Delete old results and insert new ones
    
    Args:
        transaction_id: ID of the transaction
        db: Database session
        
    Returns:
        List of AmortizationResult objects created
    """
    # Get transaction
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        return []
    
    # Get enriched transaction
    enriched = db.query(EnrichedTransaction).filter(
        EnrichedTransaction.transaction_id == transaction_id
    ).first()
    
    if not enriched or not enriched.level_2 or not enriched.level_1:
        # No enriched data or missing level_2/level_1, delete any existing results
        db.query(AmortizationResult).filter(
            AmortizationResult.transaction_id == transaction_id
        ).delete()
        db.commit()
        return []
    
    # Find matching AmortizationType
    # Match: level_2 == type.level_2_value AND level_1 IN type.level_1_values
    amortization_types = db.query(AmortizationType).filter(
        AmortizationType.level_2_value == enriched.level_2
    ).all()
    
    matching_type = None
    for amort_type in amortization_types:
        if amort_type.level_1_values and enriched.level_1 in amort_type.level_1_values:
            matching_type = amort_type
            break
    
    if not matching_type:
        # No matching type, delete any existing results
        db.query(AmortizationResult).filter(
            AmortizationResult.transaction_id == transaction_id
        ).delete()
        db.commit()
        return []
    
    # Check duration
    if not matching_type.duration or matching_type.duration <= 0:
        # Durée non configurée ou invalide, ne pas calculer d'amortissement
        db.query(AmortizationResult).filter(
            AmortizationResult.transaction_id == transaction_id
        ).delete()
        db.commit()
        return []
    
    # Determine start date: use type.start_date if defined, otherwise transaction.date
    if matching_type.start_date:
        # Use override date from type
        if isinstance(matching_type.start_date, datetime):
            start_date = matching_type.start_date
        else:
            start_date = datetime.combine(matching_type.start_date, datetime.min.time())
    else:
        # Use transaction date
        if isinstance(transaction.date, datetime):
            start_date = transaction.date
        else:
            start_date = datetime.combine(transaction.date, datetime.min.time())
    
    # Calculate total amount (absolute value)
    total_amount = abs(transaction.quantite)
    
    # Determine annual amount: use type.annual_amount if set, otherwise calculate
    if matching_type.annual_amount and matching_type.annual_amount > 0:
        # Use override annual amount
        annual_amount = matching_type.annual_amount
        # Calculate yearly amounts using fixed annual amount
        yearly_amounts = {}
        current_year = start_date.year
        end_year = current_year + int(matching_type.duration) - 1
        remaining_amount = total_amount
        
        for year in range(current_year, end_year + 1):
            if remaining_amount <= 0:
                break
            amount = min(annual_amount, remaining_amount)
            yearly_amounts[year] = amount
            remaining_amount -= amount
    else:
        # Calculate proportional distribution
        yearly_amounts = calculate_yearly_amounts(start_date, total_amount, matching_type.duration)
    
    # Delete old results for this transaction
    db.query(AmortizationResult).filter(
        AmortizationResult.transaction_id == transaction_id
    ).delete()
    
    # Create new results
    results = []
    for year, amount in yearly_amounts.items():
        result = AmortizationResult(
            transaction_id=transaction_id,
            year=year,
            category=matching_type.name,  # Store type name in category field
            amount=-abs(amount)  # Negative as it's an expense
        )
        db.add(result)
        results.append(result)
    
    db.commit()
    
    return results


def recalculate_all_amortizations(db: Session) -> int:
    """
    Recalculate amortization for all transactions that match any AmortizationType.
    
    Args:
        db: Database session
        
    Returns:
        Number of transactions processed
    """
    # Get all AmortizationTypes
    amortization_types = db.query(AmortizationType).all()
    if not amortization_types:
        return 0
    
    # Get all unique level_2_values from types
    level_2_values = list(set([t.level_2_value for t in amortization_types]))
    
    # Get all transactions with matching level_2
    transactions = db.query(Transaction).join(
        EnrichedTransaction,
        Transaction.id == EnrichedTransaction.transaction_id
    ).filter(
        EnrichedTransaction.level_2.in_(level_2_values)
    ).all()
    
    count = 0
    for transaction in transactions:
        results = recalculate_transaction_amortization(transaction.id, db)
        if results:
            count += 1
    
    return count

