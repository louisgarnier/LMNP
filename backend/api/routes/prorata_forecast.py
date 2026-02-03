"""
API routes for Pro Rata & Forecast configuration.

⚠️ Before making changes, read: ../../../docs/workflow/BEST_PRACTICES.md
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import logging

from backend.database.connection import get_db
from backend.database.models import AnnualForecastConfig, ProRataSettings, Property
from backend.api.models import (
    AnnualForecastConfigCreate,
    AnnualForecastConfigUpdate,
    AnnualForecastConfigResponse,
    AnnualForecastConfigListResponse,
    ProRataSettingsCreate,
    ProRataSettingsUpdate,
    ProRataSettingsResponse,
    CategoryReferenceData,
    ReferenceDataResponse,
)
from backend.api.utils.validation import validate_property_id
from backend.api.utils.logger_config import get_logger
from backend.api.services.prorata_service import is_calculated_category
from backend.api.services.compte_resultat_service import calculate_compte_resultat, get_mappings as get_cr_mappings
from backend.api.services.bilan_service import calculate_bilan, get_mappings as get_bilan_mappings
from backend.database.models import CompteResultatMapping, BilanMapping

router = APIRouter()
logger = get_logger("prorata_forecast")


# ========================================
# Pro Rata Settings endpoints
# ========================================

@router.get("/prorata-settings", response_model=ProRataSettingsResponse)
async def get_prorata_settings(
    property_id: int = Query(..., description="ID de la propriété"),
    db: Session = Depends(get_db)
):
    """
    Récupérer les paramètres Pro Rata d'une propriété.
    Crée des paramètres par défaut si non existants.
    """
    logger.info(f"[ProRata] GET settings for property_id={property_id}")
    validate_property_id(db, property_id, "ProRata")
    
    settings = db.query(ProRataSettings).filter(
        ProRataSettings.property_id == property_id
    ).first()
    
    if not settings:
        logger.info(f"[ProRata] Creating default settings for property_id={property_id}")
        settings = ProRataSettings(
            property_id=property_id,
            prorata_enabled=False,
            forecast_enabled=False,
            forecast_years=3
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    logger.info(f"[ProRata] Returning settings: prorata_enabled={settings.prorata_enabled}, forecast_enabled={settings.forecast_enabled}")
    return settings


@router.put("/prorata-settings", response_model=ProRataSettingsResponse)
async def update_prorata_settings(
    property_id: int = Query(..., description="ID de la propriété"),
    settings_data: ProRataSettingsUpdate = None,
    db: Session = Depends(get_db)
):
    """
    Mettre à jour les paramètres Pro Rata d'une propriété.
    """
    logger.info(f"[ProRata] PUT settings for property_id={property_id}, data={settings_data}")
    validate_property_id(db, property_id, "ProRata")
    
    settings = db.query(ProRataSettings).filter(
        ProRataSettings.property_id == property_id
    ).first()
    
    if not settings:
        logger.info(f"[ProRata] Creating settings for property_id={property_id}")
        settings = ProRataSettings(property_id=property_id)
        db.add(settings)
    
    if settings_data:
        if settings_data.prorata_enabled is not None:
            settings.prorata_enabled = settings_data.prorata_enabled
        if settings_data.forecast_enabled is not None:
            settings.forecast_enabled = settings_data.forecast_enabled
        if settings_data.forecast_years is not None:
            settings.forecast_years = settings_data.forecast_years
    
    db.commit()
    db.refresh(settings)
    
    logger.info(f"[ProRata] Updated settings: prorata_enabled={settings.prorata_enabled}, forecast_enabled={settings.forecast_enabled}")
    return settings


# ========================================
# Annual Forecast Configs endpoints
# ========================================

@router.get("/forecast-configs", response_model=List[AnnualForecastConfigResponse])
async def get_forecast_configs(
    property_id: int = Query(..., description="ID de la propriété"),
    year: int = Query(..., description="Année"),
    target_type: str = Query(..., description="Type: compte_resultat, bilan_actif, bilan_passif"),
    db: Session = Depends(get_db)
):
    """
    Récupérer les configurations forecast d'une propriété pour une année et un type.
    """
    logger.info(f"[ProRata] GET forecast configs for property_id={property_id}, year={year}, target_type={target_type}")
    validate_property_id(db, property_id, "ProRata")
    
    configs = db.query(AnnualForecastConfig).filter(
        AnnualForecastConfig.property_id == property_id,
        AnnualForecastConfig.year == year,
        AnnualForecastConfig.target_type == target_type
    ).all()
    
    logger.info(f"[ProRata] Found {len(configs)} forecast configs")
    return configs


@router.post("/forecast-configs", response_model=AnnualForecastConfigResponse, status_code=201)
async def create_forecast_config(
    config: AnnualForecastConfigCreate,
    db: Session = Depends(get_db)
):
    """
    Créer une configuration forecast.
    """
    logger.info(f"[ProRata] POST forecast config: property_id={config.property_id}, year={config.year}, level_1={config.level_1}")
    validate_property_id(db, config.property_id, "ProRata")
    
    # Vérifier si existe déjà
    existing = db.query(AnnualForecastConfig).filter(
        AnnualForecastConfig.property_id == config.property_id,
        AnnualForecastConfig.year == config.year,
        AnnualForecastConfig.level_1 == config.level_1,
        AnnualForecastConfig.target_type == config.target_type
    ).first()
    
    if existing:
        logger.warning(f"[ProRata] Config already exists for {config.level_1}")
        raise HTTPException(status_code=400, detail=f"Configuration existe déjà pour '{config.level_1}'")
    
    db_config = AnnualForecastConfig(**config.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    logger.info(f"[ProRata] Created forecast config id={db_config.id}")
    return db_config


@router.put("/forecast-configs/{config_id}", response_model=AnnualForecastConfigResponse)
async def update_forecast_config(
    config_id: int,
    property_id: int = Query(..., description="ID de la propriété"),
    config_data: AnnualForecastConfigUpdate = None,
    db: Session = Depends(get_db)
):
    """
    Mettre à jour une configuration forecast.
    """
    logger.info(f"[ProRata] PUT forecast config id={config_id} for property_id={property_id}")
    validate_property_id(db, property_id, "ProRata")
    
    config = db.query(AnnualForecastConfig).filter(
        AnnualForecastConfig.id == config_id,
        AnnualForecastConfig.property_id == property_id
    ).first()
    
    if not config:
        logger.warning(f"[ProRata] Config not found id={config_id}")
        raise HTTPException(status_code=404, detail="Configuration non trouvée")
    
    if config_data:
        if config_data.base_annual_amount is not None:
            config.base_annual_amount = config_data.base_annual_amount
        if config_data.annual_growth_rate is not None:
            config.annual_growth_rate = config_data.annual_growth_rate
    
    db.commit()
    db.refresh(config)
    
    logger.info(f"[ProRata] Updated forecast config id={config.id}")
    return config


@router.delete("/forecast-configs/{config_id}", status_code=204)
async def delete_forecast_config(
    config_id: int,
    property_id: int = Query(..., description="ID de la propriété"),
    db: Session = Depends(get_db)
):
    """
    Supprimer une configuration forecast.
    """
    logger.info(f"[ProRata] DELETE forecast config id={config_id} for property_id={property_id}")
    validate_property_id(db, property_id, "ProRata")
    
    config = db.query(AnnualForecastConfig).filter(
        AnnualForecastConfig.id == config_id,
        AnnualForecastConfig.property_id == property_id
    ).first()
    
    if not config:
        logger.warning(f"[ProRata] Config not found id={config_id}")
        raise HTTPException(status_code=404, detail="Configuration non trouvée")
    
    db.delete(config)
    db.commit()
    
    logger.info(f"[ProRata] Deleted forecast config id={config_id}")
    return None


@router.post("/forecast-configs/bulk", response_model=List[AnnualForecastConfigResponse])
async def bulk_upsert_forecast_configs(
    property_id: int = Query(..., description="ID de la propriété"),
    configs: List[AnnualForecastConfigCreate] = None,
    db: Session = Depends(get_db)
):
    """
    Créer ou mettre à jour plusieurs configurations en une fois.
    """
    logger.info(f"[ProRata] POST bulk upsert for property_id={property_id}, count={len(configs) if configs else 0}")
    validate_property_id(db, property_id, "ProRata")
    
    if not configs:
        return []
    
    results = []
    for config in configs:
        if config.property_id != property_id:
            logger.warning(f"[ProRata] Skipping config with mismatched property_id: {config.property_id} != {property_id}")
            continue
        
        existing = db.query(AnnualForecastConfig).filter(
            AnnualForecastConfig.property_id == config.property_id,
            AnnualForecastConfig.year == config.year,
            AnnualForecastConfig.level_1 == config.level_1,
            AnnualForecastConfig.target_type == config.target_type
        ).first()
        
        if existing:
            existing.base_annual_amount = config.base_annual_amount
            existing.annual_growth_rate = config.annual_growth_rate
            db.commit()
            db.refresh(existing)
            results.append(existing)
            logger.debug(f"[ProRata] Updated config for {config.level_1}")
        else:
            db_config = AnnualForecastConfig(**config.model_dump())
            db.add(db_config)
            db.commit()
            db.refresh(db_config)
            results.append(db_config)
            logger.debug(f"[ProRata] Created config for {config.level_1}")
    
    logger.info(f"[ProRata] Bulk upsert completed: {len(results)} configs processed")
    return results


# ========================================
# Reference Data endpoint (for UI display)
# ========================================

def _get_compte_resultat_categories(db: Session, property_id: int, year: int) -> dict:
    """
    Récupère TOUTES les catégories du Compte de Résultat depuis les mappings,
    avec leurs montants RÉELS (0 si pas de transactions).
    Synchronisé avec la carte de configuration.
    
    Note: skip_prorata=True pour toujours retourner les valeurs réelles,
    pas les valeurs ajustées par le prorata.
    """
    # 1. Récupérer tous les mappings configurés
    mappings = get_cr_mappings(db, property_id)
    
    # 2. Calculer les montants RÉELS (sans prorata)
    cr_data = calculate_compte_resultat(db, year, property_id, skip_prorata=True)
    produits_amounts = cr_data.get("produits", {})
    charges_amounts = cr_data.get("charges", {})
    
    # 3. Construire le dictionnaire avec TOUTES les catégories des mappings
    categories = {}
    
    for mapping in mappings:
        cat_name = mapping.category_name
        # Chercher le montant dans produits ou charges
        if cat_name in produits_amounts:
            categories[cat_name] = produits_amounts[cat_name]
        elif cat_name in charges_amounts:
            categories[cat_name] = charges_amounts[cat_name]
        else:
            # Catégorie sans transactions = 0
            categories[cat_name] = 0.0
    
    # 4. Ajouter les catégories spéciales (amortissements, coût financement) si présentes
    for cat_name, amount in charges_amounts.items():
        if cat_name not in categories:
            categories[cat_name] = amount
    
    return categories


def _get_bilan_categories(db: Session, property_id: int, year: int, is_actif: bool) -> dict:
    """
    Récupère TOUTES les catégories du Bilan depuis les mappings,
    avec leurs montants réels (0 si pas de transactions).
    Synchronisé avec la carte de configuration.
    """
    # 1. Récupérer tous les mappings configurés
    mappings = get_bilan_mappings(db, property_id)
    
    # 2. Filtrer par type (ACTIF ou PASSIF)
    target_type = "ACTIF" if is_actif else "PASSIF"
    filtered_mappings = [m for m in mappings if m.type == target_type]
    
    # 3. Calculer les montants réels
    bilan_data = calculate_bilan(db, year, property_id)
    # calculate_bilan retourne {"categories": {...}, "totals_by_sub_category": {...}, ...}
    all_amounts = bilan_data.get("categories", {})
    
    # 4. Construire le dictionnaire avec TOUTES les catégories des mappings filtrés
    categories = {}
    
    for mapping in filtered_mappings:
        cat_name = mapping.category_name
        categories[cat_name] = all_amounts.get(cat_name, 0.0)
    
    return categories


@router.get("/forecast-configs/reference-data", response_model=ReferenceDataResponse)
async def get_reference_data(
    property_id: int = Query(..., description="ID de la propriété"),
    year: int = Query(..., description="Année"),
    target_type: str = Query(..., description="Type: compte_resultat, bilan_actif, bilan_passif"),
    db: Session = Depends(get_db)
):
    """
    Récupérer les données de référence pour aide à la saisie.
    Retourne les montants réels de l'année en cours et de l'année précédente.
    
    Pour chaque catégorie:
    - level_1: Nom de la catégorie
    - real_current_year: Montant réel de l'année demandée
    - real_previous_year: Montant réel de l'année précédente
    - is_calculated: True si la catégorie est calculée automatiquement
    """
    logger.info(f"[ProRata] GET reference data for property_id={property_id}, year={year}, target_type={target_type}")
    validate_property_id(db, property_id, "ProRata")
    
    previous_year = year - 1
    categories_result = []
    
    try:
        if target_type == "compte_resultat":
            # Récupérer les données du Compte de Résultat
            current_year_data = _get_compte_resultat_categories(db, property_id, year)
            previous_year_data = _get_compte_resultat_categories(db, property_id, previous_year)
            
            # Fusionner toutes les catégories (année en cours + année précédente)
            all_categories = set(current_year_data.keys()) | set(previous_year_data.keys())
            
            for cat_name in sorted(all_categories):
                real_current = current_year_data.get(cat_name, 0.0)
                real_previous = previous_year_data.get(cat_name, 0.0)
                is_calc = is_calculated_category(cat_name, target_type)
                
                categories_result.append(CategoryReferenceData(
                    level_1=cat_name,
                    real_current_year=real_current,
                    real_previous_year=real_previous,
                    is_calculated=is_calc
                ))
                
        elif target_type == "bilan_actif":
            # Récupérer les données de l'Actif
            current_year_data = _get_bilan_categories(db, property_id, year, is_actif=True)
            previous_year_data = _get_bilan_categories(db, property_id, previous_year, is_actif=True)
            
            all_categories = set(current_year_data.keys()) | set(previous_year_data.keys())
            
            for cat_name in sorted(all_categories):
                real_current = current_year_data.get(cat_name, 0.0)
                real_previous = previous_year_data.get(cat_name, 0.0)
                is_calc = is_calculated_category(cat_name, target_type)
                
                categories_result.append(CategoryReferenceData(
                    level_1=cat_name,
                    real_current_year=real_current,
                    real_previous_year=real_previous,
                    is_calculated=is_calc
                ))
                
        elif target_type == "bilan_passif":
            # Récupérer les données du Passif
            current_year_data = _get_bilan_categories(db, property_id, year, is_actif=False)
            previous_year_data = _get_bilan_categories(db, property_id, previous_year, is_actif=False)
            
            all_categories = set(current_year_data.keys()) | set(previous_year_data.keys())
            
            for cat_name in sorted(all_categories):
                real_current = current_year_data.get(cat_name, 0.0)
                real_previous = previous_year_data.get(cat_name, 0.0)
                is_calc = is_calculated_category(cat_name, target_type)
                
                categories_result.append(CategoryReferenceData(
                    level_1=cat_name,
                    real_current_year=real_current,
                    real_previous_year=real_previous,
                    is_calculated=is_calc
                ))
        else:
            logger.warning(f"[ProRata] Unknown target_type: {target_type}")
            raise HTTPException(status_code=400, detail=f"Type inconnu: {target_type}")
            
    except Exception as e:
        logger.error(f"[ProRata] Error getting reference data: {str(e)}")
        # En cas d'erreur, retourner une liste vide plutôt que faire échouer
        categories_result = []
    
    logger.info(f"[ProRata] Returning {len(categories_result)} reference data categories")
    return ReferenceDataResponse(
        categories=categories_result,
        year=year,
        target_type=target_type
    )
