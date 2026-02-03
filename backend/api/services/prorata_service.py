"""
Service Pro Rata & Forecast
Gère la logique de calcul MAX(réel, prévu) et les projections multi-années
"""

import logging
from typing import Dict, Optional, List, Any
from sqlalchemy.orm import Session
from datetime import datetime

from backend.database.models import ProRataSettings, AnnualForecastConfig
from backend.api.utils.logger_config import get_logger

logger = get_logger("prorata_service")

# Catégories calculées automatiquement (ne pas appliquer MAX)
# Compte de Résultat - noms exacts utilisés par compte_resultat_service.py
CALCULATED_CATEGORIES_CR = [
    "Charges d'amortissements",
    "Coût du financement (hors remboursement du capital)",
]

# Bilan - Actif (noms exacts depuis BilanMapping)
CALCULATED_CATEGORIES_BILAN_ACTIF = [
    "Amortissements cumulés",
    "Compte bancaire",
]

# Bilan - Passif (noms exacts depuis BilanMapping)
CALCULATED_CATEGORIES_BILAN_PASSIF = [
    "Résultat de l'exercice",
    "Report à nouveau / report du déficit",
    "Emprunt bancaire (capital restant dû)",
]


def get_calculated_categories(target_type: str) -> List[str]:
    """
    Retourne la liste des catégories calculées pour un type donné
    
    Args:
        target_type: "compte_resultat", "bilan_actif" ou "bilan_passif"
        
    Returns:
        Liste des noms de catégories calculées
    """
    if target_type == "compte_resultat":
        return CALCULATED_CATEGORIES_CR
    elif target_type == "bilan_actif":
        return CALCULATED_CATEGORIES_BILAN_ACTIF
    elif target_type == "bilan_passif":
        return CALCULATED_CATEGORIES_BILAN_PASSIF
    return []


def is_calculated_category(level_1: str, target_type: str) -> bool:
    """
    Vérifie si une catégorie est calculée automatiquement
    
    Args:
        level_1: Nom de la catégorie (niveau 1)
        target_type: Type de cible
        
    Returns:
        True si la catégorie est calculée, False sinon
    """
    calculated = get_calculated_categories(target_type)
    level_1_normalized = level_1.lower().strip()
    
    for calc in calculated:
        calc_normalized = calc.lower().strip()
        # Match exact ou si le nom calculé est contenu dans level_1
        # Mais pas l'inverse pour éviter que "Capital" match "Capital restant dû"
        if level_1_normalized == calc_normalized or calc_normalized in level_1_normalized:
            return True
    return False


def get_prorata_settings(db: Session, property_id: int) -> Optional[ProRataSettings]:
    """
    Récupère les settings Pro Rata pour une propriété
    
    Args:
        db: Session SQLAlchemy
        property_id: ID de la propriété
        
    Returns:
        ProRataSettings ou None si non configuré
    """
    logger.debug(f"[PRORATA] get_prorata_settings property_id={property_id}")
    
    settings = db.query(ProRataSettings).filter(
        ProRataSettings.property_id == property_id
    ).first()
    
    if settings:
        logger.debug(f"[PRORATA] Settings found: prorata_enabled={settings.prorata_enabled}, forecast_enabled={settings.forecast_enabled}")
    else:
        logger.debug(f"[PRORATA] No settings found for property {property_id}")
    
    return settings


def get_forecast_configs(
    db: Session, 
    property_id: int, 
    year: int, 
    target_type: str
) -> Dict[str, float]:
    """
    Récupère les configurations de prévision pour une propriété/année/type
    
    Args:
        db: Session SQLAlchemy
        property_id: ID de la propriété
        year: Année de base
        target_type: "compte_resultat", "bilan_actif" ou "bilan_passif"
        
    Returns:
        Dict[level_1, base_annual_amount] des prévisions configurées
    """
    logger.debug(f"[PRORATA] get_forecast_configs property_id={property_id}, year={year}, target_type={target_type}")
    
    configs = db.query(AnnualForecastConfig).filter(
        AnnualForecastConfig.property_id == property_id,
        AnnualForecastConfig.year == year,
        AnnualForecastConfig.target_type == target_type
    ).all()
    
    result = {config.level_1: config.base_annual_amount for config in configs}
    
    logger.debug(f"[PRORATA] Found {len(result)} forecast configs: {list(result.keys())}")
    
    return result


def apply_prorata(
    db: Session,
    property_id: int,
    year: int,
    target_type: str,
    real_amounts: Dict[str, float]
) -> Dict[str, Dict[str, Any]]:
    """
    Applique la logique MAX(réel, prévu) sur les montants réels
    
    Pour chaque catégorie :
    - Si calculée → retourne le montant réel tel quel
    - Si prévu est configuré et prorata_enabled → retourne MAX(abs(réel), abs(prévu)) avec le signe approprié
    - Sinon → retourne le montant réel
    
    Args:
        db: Session SQLAlchemy
        property_id: ID de la propriété
        year: Année
        target_type: "compte_resultat", "bilan_actif" ou "bilan_passif"
        real_amounts: Dict[level_1, montant_réel]
        
    Returns:
        Dict[level_1, {
            'amount': montant_final,
            'real': montant_réel,
            'planned': montant_prévu ou None,
            'is_calculated': bool,
            'source': 'real' | 'planned' | 'calculated'
        }]
    """
    logger.info(f"[PRORATA] apply_prorata property_id={property_id}, year={year}, target_type={target_type}")
    logger.debug(f"[PRORATA] Real amounts: {real_amounts}")
    
    result: Dict[str, Dict[str, Any]] = {}
    
    # Récupérer les settings
    settings = get_prorata_settings(db, property_id)
    prorata_enabled = settings.prorata_enabled if settings else False
    
    logger.debug(f"[PRORATA] prorata_enabled={prorata_enabled}")
    
    # Récupérer les prévisions configurées
    forecast_configs = {}
    if prorata_enabled:
        forecast_configs = get_forecast_configs(db, property_id, year, target_type)
    
    # Traiter chaque catégorie
    for level_1, real_amount in real_amounts.items():
        real_value = real_amount if real_amount is not None else 0.0
        is_calculated = is_calculated_category(level_1, target_type)
        planned_value = forecast_configs.get(level_1)
        
        if is_calculated:
            # Catégorie calculée → toujours utiliser le montant réel
            result[level_1] = {
                'amount': real_value,
                'real': real_value,
                'planned': None,
                'is_calculated': True,
                'source': 'calculated'
            }
            logger.debug(f"[PRORATA] {level_1}: CALCULATED → {real_value}")
            
        elif not prorata_enabled:
            # Pro rata désactivé → utiliser le montant réel
            result[level_1] = {
                'amount': real_value,
                'real': real_value,
                'planned': planned_value,
                'is_calculated': False,
                'source': 'real'
            }
            logger.debug(f"[PRORATA] {level_1}: DISABLED → {real_value}")
            
        elif planned_value is not None:
            # Pro rata activé et prévu configuré → MAX(|réel|, |prévu|)
            abs_real = abs(real_value)
            abs_planned = abs(planned_value)
            
            if abs_real >= abs_planned:
                # Le réel est plus grand → utiliser le réel
                final_amount = real_value
                source = 'real'
            else:
                # Le prévu est plus grand → utiliser le prévu avec le signe du prévu
                final_amount = planned_value
                source = 'planned'
            
            result[level_1] = {
                'amount': final_amount,
                'real': real_value,
                'planned': planned_value,
                'is_calculated': False,
                'source': source
            }
            logger.debug(f"[PRORATA] {level_1}: MAX(|{real_value}|, |{planned_value}|) → {final_amount} (source={source})")
            
        else:
            # Pro rata activé mais pas de prévu → utiliser le réel
            result[level_1] = {
                'amount': real_value,
                'real': real_value,
                'planned': None,
                'is_calculated': False,
                'source': 'real'
            }
            logger.debug(f"[PRORATA] {level_1}: NO_PLANNED → {real_value}")
    
    logger.info(f"[PRORATA] apply_prorata completed: {len(result)} categories processed")
    
    return result


def calculate_forecast_amount(
    base_amount: float,
    growth_rate: float,
    years_ahead: int
) -> float:
    """
    Calcule le montant projeté pour une année future
    
    Formule: base_amount × (1 + growth_rate)^years_ahead
    
    Args:
        base_amount: Montant de base (année de référence)
        growth_rate: Taux d'évolution annuel (ex: 0.02 pour +2%)
        years_ahead: Nombre d'années dans le futur (1, 2, 3...)
        
    Returns:
        Montant projeté
    """
    if years_ahead <= 0:
        return base_amount
    
    return base_amount * ((1 + growth_rate) ** years_ahead)


def get_forecast_for_year(
    db: Session,
    property_id: int,
    base_year: int,
    target_year: int,
    target_type: str
) -> Dict[str, float]:
    """
    Calcule les montants projetés pour une année future spécifique
    
    Args:
        db: Session SQLAlchemy
        property_id: ID de la propriété
        base_year: Année de base des configurations
        target_year: Année cible pour la projection
        target_type: "compte_resultat", "bilan_actif" ou "bilan_passif"
        
    Returns:
        Dict[level_1, montant_projeté]
    """
    logger.info(f"[PRORATA] get_forecast_for_year property_id={property_id}, base={base_year}, target={target_year}, type={target_type}")
    
    years_ahead = target_year - base_year
    
    if years_ahead <= 0:
        # Pas de projection nécessaire
        return get_forecast_configs(db, property_id, base_year, target_type)
    
    # Récupérer les configurations avec taux d'évolution
    configs = db.query(AnnualForecastConfig).filter(
        AnnualForecastConfig.property_id == property_id,
        AnnualForecastConfig.year == base_year,
        AnnualForecastConfig.target_type == target_type
    ).all()
    
    result = {}
    for config in configs:
        projected = calculate_forecast_amount(
            config.base_annual_amount,
            config.annual_growth_rate,
            years_ahead
        )
        result[config.level_1] = round(projected, 2)
        logger.debug(f"[PRORATA] {config.level_1}: {config.base_annual_amount} × (1 + {config.annual_growth_rate})^{years_ahead} = {projected:.2f}")
    
    logger.info(f"[PRORATA] Projected {len(result)} categories for year {target_year}")
    
    return result
