"""
API routes for compte de résultat.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func
from typing import List, Optional
from datetime import date

from backend.database import get_db
from backend.database.models import (
    CompteResultatMapping,
    CompteResultatData,
    CompteResultatConfig
)
from backend.api.models import (
    CompteResultatMappingCreate,
    CompteResultatMappingUpdate,
    CompteResultatMappingResponse,
    CompteResultatMappingListResponse,
    CompteResultatDataResponse,
    CompteResultatDataListResponse,
    CompteResultatConfigResponse
)
from backend.api.services.compte_resultat_service import (
    get_mappings,
    get_level_3_values,
    calculate_compte_resultat
)

router = APIRouter()


# ========== Mappings Endpoints ==========

@router.get("/compte-resultat/mappings", response_model=CompteResultatMappingListResponse)
async def get_compte_resultat_mappings(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'éléments à retourner"),
    db: Session = Depends(get_db)
):
    """
    Récupérer la liste des mappings pour le compte de résultat.
    
    - **skip**: Nombre d'éléments à sauter (pagination)
    - **limit**: Nombre d'éléments à retourner (max 1000)
    """
    query = db.query(CompteResultatMapping)
    total = query.count()
    
    mappings = query.offset(skip).limit(limit).all()
    
    mapping_responses = [
        CompteResultatMappingResponse(
            id=m.id,
            category_name=m.category_name,
            level_1_values=m.level_1_values,
            created_at=m.created_at,
            updated_at=m.updated_at
        )
        for m in mappings
    ]
    
    return CompteResultatMappingListResponse(
        items=mapping_responses,
        total=total
    )


@router.post("/compte-resultat/mappings", response_model=CompteResultatMappingResponse, status_code=201)
async def create_compte_resultat_mapping(
    mapping: CompteResultatMappingCreate,
    db: Session = Depends(get_db)
):
    """
    Créer un nouveau mapping pour le compte de résultat.
    """
    # Vérifier si un mapping avec le même category_name existe déjà
    existing = db.query(CompteResultatMapping).filter(
        CompteResultatMapping.category_name == mapping.category_name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Un mapping avec la catégorie '{mapping.category_name}' existe déjà"
        )
    
    new_mapping = CompteResultatMapping(
        category_name=mapping.category_name,
        level_1_values=mapping.level_1_values
    )
    db.add(new_mapping)
    db.commit()
    db.refresh(new_mapping)
    
    return CompteResultatMappingResponse(
        id=new_mapping.id,
        category_name=new_mapping.category_name,
        level_1_values=new_mapping.level_1_values,
        created_at=new_mapping.created_at,
        updated_at=new_mapping.updated_at
    )


@router.put("/compte-resultat/mappings/{mapping_id}", response_model=CompteResultatMappingResponse)
async def update_compte_resultat_mapping(
    mapping_id: int,
    mapping: CompteResultatMappingUpdate,
    db: Session = Depends(get_db)
):
    """
    Mettre à jour un mapping pour le compte de résultat.
    """
    existing_mapping = db.query(CompteResultatMapping).filter(
        CompteResultatMapping.id == mapping_id
    ).first()
    
    if not existing_mapping:
        raise HTTPException(status_code=404, detail="Mapping non trouvé")
    
    # Vérifier si le nouveau category_name n'est pas déjà utilisé par un autre mapping
    if mapping.category_name and mapping.category_name != existing_mapping.category_name:
        duplicate = db.query(CompteResultatMapping).filter(
            CompteResultatMapping.category_name == mapping.category_name,
            CompteResultatMapping.id != mapping_id
        ).first()
        
        if duplicate:
            raise HTTPException(
                status_code=400,
                detail=f"Un mapping avec la catégorie '{mapping.category_name}' existe déjà"
            )
    
    # Mettre à jour les champs
    if mapping.category_name is not None:
        existing_mapping.category_name = mapping.category_name
    if mapping.level_1_values is not None:
        existing_mapping.level_1_values = mapping.level_1_values
    
    db.commit()
    db.refresh(existing_mapping)
    
    return CompteResultatMappingResponse(
        id=existing_mapping.id,
        category_name=existing_mapping.category_name,
        level_1_values=existing_mapping.level_1_values,
        created_at=existing_mapping.created_at,
        updated_at=existing_mapping.updated_at
    )


@router.delete("/compte-resultat/mappings/{mapping_id}", status_code=204)
async def delete_compte_resultat_mapping(
    mapping_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprimer un mapping pour le compte de résultat.
    """
    mapping = db.query(CompteResultatMapping).filter(
        CompteResultatMapping.id == mapping_id
    ).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping non trouvé")
    
    db.delete(mapping)
    db.commit()
    
    return None


# ========== Calculate Endpoints ==========

@router.get("/compte-resultat/calculate")
async def calculate_compte_resultat_endpoint(
    years: str = Query(..., description="Années à calculer (séparées par des virgules, ex: '2021,2022,2023')"),
    db: Session = Depends(get_db)
):
    """
    Calculer les montants pour plusieurs années (basé sur les mappings configurés).
    
    - **years**: Années à calculer (séparées par des virgules, ex: '2021,2022,2023')
    
    Returns:
        Dictionnaire avec les montants par catégorie et année
    """
    try:
        year_list = [int(y.strip()) for y in years.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="Format d'années invalide. Utilisez des nombres séparés par des virgules.")
    
    results = {}
    mappings = get_mappings(db)
    level_3_values = get_level_3_values(db)
    
    for year in year_list:
        result = calculate_compte_resultat(db, year, mappings, level_3_values)
        results[year] = result
    
    return {
        "years": year_list,
        "results": results
    }


@router.post("/compte-resultat/generate")
async def generate_compte_resultat(
    year: int = Query(..., description="Année pour laquelle générer le compte de résultat"),
    db: Session = Depends(get_db)
):
    """
    Générer un compte de résultat pour une année et le stocker en base de données.
    
    - **year**: Année pour laquelle générer le compte de résultat
    
    Returns:
        Compte de résultat calculé et stocké
    """
    # Calculer le compte de résultat
    mappings = get_mappings(db)
    level_3_values = get_level_3_values(db)
    result = calculate_compte_resultat(db, year, mappings, level_3_values)
    
    # Supprimer les anciennes données pour cette année
    db.query(CompteResultatData).filter(
        CompteResultatData.annee == year
    ).delete()
    db.commit()
    
    # Stocker les produits
    for category_name, amount in result["produits"].items():
        data = CompteResultatData(
            annee=year,
            category_name=category_name,
            amount=amount
        )
        db.add(data)
    
    # Stocker les charges
    for category_name, amount in result["charges"].items():
        # Vérifier si la catégorie existe déjà (pour éviter les doublons)
        existing = db.query(CompteResultatData).filter(
            CompteResultatData.annee == year,
            CompteResultatData.category_name == category_name
        ).first()
        
        if existing:
            existing.amount = amount
        else:
            data = CompteResultatData(
                annee=year,
                category_name=category_name,
                amount=amount
            )
            db.add(data)
    
    db.commit()
    
    return {
        "year": year,
        "result": result,
        "message": f"Compte de résultat généré et stocké pour l'année {year}"
    }


# ========== Data Endpoints ==========

@router.get("/compte-resultat", response_model=CompteResultatDataListResponse)
async def get_compte_resultat(
    year: Optional[int] = Query(None, description="Année spécifique"),
    start_year: Optional[int] = Query(None, description="Année de début (pour plusieurs années)"),
    end_year: Optional[int] = Query(None, description="Année de fin (pour plusieurs années)"),
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'éléments à retourner"),
    db: Session = Depends(get_db)
):
    """
    Récupérer les comptes de résultat stockés.
    
    - **year**: Année spécifique (optionnel)
    - **start_year**: Année de début (pour plusieurs années, optionnel)
    - **end_year**: Année de fin (pour plusieurs années, optionnel)
    - **skip**: Nombre d'éléments à sauter (pagination)
    - **limit**: Nombre d'éléments à retourner (max 1000)
    """
    query = db.query(CompteResultatData)
    
    # Filtres par année
    if year:
        query = query.filter(CompteResultatData.annee == year)
    elif start_year and end_year:
        query = query.filter(
            CompteResultatData.annee >= start_year,
            CompteResultatData.annee <= end_year
        )
    elif start_year:
        query = query.filter(CompteResultatData.annee >= start_year)
    elif end_year:
        query = query.filter(CompteResultatData.annee <= end_year)
    
    total = query.count()
    
    # Tri par année puis par catégorie
    query = query.order_by(CompteResultatData.annee, CompteResultatData.category_name)
    
    # Pagination
    data_items = query.offset(skip).limit(limit).all()
    
    data_responses = [
        CompteResultatDataResponse(
            id=d.id,
            annee=d.annee,
            category_name=d.category_name,
            amount=d.amount,
            created_at=d.created_at,
            updated_at=d.updated_at
        )
        for d in data_items
    ]
    
    return CompteResultatDataListResponse(
        items=data_responses,
        total=total
    )


@router.get("/compte-resultat/data", response_model=CompteResultatDataListResponse)
async def get_compte_resultat_data(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'éléments à retourner"),
    db: Session = Depends(get_db)
):
    """
    Récupérer les données brutes du compte de résultat.
    
    - **skip**: Nombre d'éléments à sauter (pagination)
    - **limit**: Nombre d'éléments à retourner (max 1000)
    """
    query = db.query(CompteResultatData)
    total = query.count()
    
    query = query.order_by(CompteResultatData.annee, CompteResultatData.category_name)
    data_items = query.offset(skip).limit(limit).all()
    
    data_responses = [
        CompteResultatDataResponse(
            id=d.id,
            annee=d.annee,
            category_name=d.category_name,
            amount=d.amount,
            created_at=d.created_at,
            updated_at=d.updated_at
        )
        for d in data_items
    ]
    
    return CompteResultatDataListResponse(
        items=data_responses,
        total=total
    )


@router.delete("/compte-resultat/data/{data_id}", status_code=204)
async def delete_compte_resultat_data(
    data_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprimer une donnée du compte de résultat.
    """
    data = db.query(CompteResultatData).filter(
        CompteResultatData.id == data_id
    ).first()
    
    if not data:
        raise HTTPException(status_code=404, detail="Donnée non trouvée")
    
    db.delete(data)
    db.commit()
    
    return None


@router.delete("/compte-resultat/year/{year}", status_code=204)
async def delete_compte_resultat_by_year(
    year: int,
    db: Session = Depends(get_db)
):
    """
    Supprimer toutes les données du compte de résultat pour une année.
    """
    deleted_count = db.query(CompteResultatData).filter(
        CompteResultatData.annee == year
    ).delete()
    
    db.commit()
    
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Aucune donnée trouvée pour l'année {year}")
    
    return None
