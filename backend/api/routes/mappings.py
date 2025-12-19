"""
API routes for mappings.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import distinct
from typing import List, Optional, Dict

from backend.database import get_db
from backend.database.models import Mapping, Transaction, EnrichedTransaction
from backend.api.models import (
    MappingCreate,
    MappingUpdate,
    MappingResponse,
    MappingListResponse
)
from backend.api.services.enrichment_service import enrich_transaction

router = APIRouter()


@router.get("/mappings", response_model=MappingListResponse)
async def get_mappings(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'éléments à retourner"),
    search: Optional[str] = Query(None, description="Recherche dans le nom"),
    db: Session = Depends(get_db)
):
    """
    Récupérer la liste des mappings.
    
    Args:
        skip: Nombre d'éléments à sauter (pagination)
        limit: Nombre d'éléments à retourner
        search: Terme de recherche dans le nom
        db: Session de base de données
    
    Returns:
        Liste des mappings avec pagination
    """
    query = db.query(Mapping)
    
    # Filtre de recherche
    if search:
        query = query.filter(Mapping.nom.contains(search))
    
    # Comptage total
    total = query.count()
    
    # Pagination
    mappings = query.order_by(Mapping.nom).offset(skip).limit(limit).all()
    
    return MappingListResponse(
        mappings=[MappingResponse.model_validate(m) for m in mappings],
        total=total
    )


@router.post("/mappings", response_model=MappingResponse, status_code=201)
async def create_mapping(
    mapping: MappingCreate,
    db: Session = Depends(get_db)
):
    """
    Créer un nouveau mapping.
    
    Args:
        mapping: Données du mapping à créer
        db: Session de base de données
    
    Returns:
        Mapping créé
    
    Raises:
        HTTPException: Si un mapping avec le même nom existe déjà
    """
    # Vérifier si un mapping avec le même nom existe déjà
    existing = db.query(Mapping).filter(Mapping.nom == mapping.nom).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Un mapping avec le nom '{mapping.nom}' existe déjà"
        )
    
    # Créer le nouveau mapping
    db_mapping = Mapping(
        nom=mapping.nom,
        level_1=mapping.level_1,
        level_2=mapping.level_2,
        level_3=mapping.level_3,
        is_prefix_match=mapping.is_prefix_match,
        priority=mapping.priority
    )
    
    db.add(db_mapping)
    db.commit()
    db.refresh(db_mapping)
    
    return MappingResponse.model_validate(db_mapping)


@router.put("/mappings/{mapping_id}", response_model=MappingResponse)
async def update_mapping(
    mapping_id: int,
    mapping_update: MappingUpdate,
    db: Session = Depends(get_db)
):
    """
    Modifier un mapping existant.
    
    Args:
        mapping_id: ID du mapping à modifier
        mapping_update: Données à mettre à jour
        db: Session de base de données
    
    Returns:
        Mapping mis à jour
    
    Raises:
        HTTPException: Si le mapping n'existe pas ou si le nouveau nom existe déjà
    """
    mapping = db.query(Mapping).filter(Mapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail=f"Mapping avec ID {mapping_id} non trouvé")
    
    # Vérifier si le nouveau nom (si modifié) existe déjà
    if mapping_update.nom and mapping_update.nom != mapping.nom:
        existing = db.query(Mapping).filter(Mapping.nom == mapping_update.nom).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Un mapping avec le nom '{mapping_update.nom}' existe déjà"
            )
    
    # Mettre à jour les champs
    update_data = mapping_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(mapping, field, value)
    
    db.commit()
    db.refresh(mapping)
    
    return MappingResponse.model_validate(mapping)


@router.delete("/mappings/{mapping_id}", status_code=204)
async def delete_mapping(
    mapping_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprimer un mapping et re-enrichir les transactions qui l'utilisaient.
    
    Lors de la suppression d'un mapping :
    1. Trouve toutes les transactions dont le nom correspond au mapping
    2. Re-enrichit ces transactions (elles seront remises à NULL si aucun autre mapping ne correspond)
    3. Supprime le mapping
    
    Args:
        mapping_id: ID du mapping à supprimer
        db: Session de base de données
    
    Raises:
        HTTPException: Si le mapping n'existe pas
    """
    mapping = db.query(Mapping).filter(Mapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail=f"Mapping avec ID {mapping_id} non trouvé")
    
    # Sauvegarder les informations du mapping avant suppression
    mapping_nom = mapping.nom
    mapping_level_1 = mapping.level_1
    mapping_level_2 = mapping.level_2
    mapping_level_3 = mapping.level_3
    
    # Trouver toutes les transactions enrichies qui utilisent ce mapping
    # On cherche les transactions qui ont les mêmes level_1, level_2, level_3
    # ET dont le nom correspond au mapping
    enriched_transactions = db.query(EnrichedTransaction).join(Transaction).filter(
        EnrichedTransaction.level_1 == mapping_level_1,
        EnrichedTransaction.level_2 == mapping_level_2,
        EnrichedTransaction.level_3 == mapping_level_3
    ).all()
    
    # Filtrer pour ne garder que celles dont le nom correspond au mapping
    transactions_to_re_enrich = []
    for enriched in enriched_transactions:
        transaction = db.query(Transaction).filter(Transaction.id == enriched.transaction_id).first()
        if transaction:
            # Vérifier si le nom de la transaction correspond au mapping
            transaction_name = transaction.nom.strip()
            mapping_name = mapping_nom.strip()
            
            # Utiliser la même logique que find_best_mapping
            matches = False
            if 'PRLV SEPA' in transaction_name and 'PRLV SEPA' in mapping_name:
                matches = transaction_name.startswith(mapping_name)
            elif 'VIR STRIPE' in transaction_name and mapping_name == 'VIR STRIPE':
                matches = True
            elif mapping_name in transaction_name or transaction_name.startswith(mapping_name):
                matches = True
            
            if matches:
                transactions_to_re_enrich.append(transaction)
    
    # Supprimer le mapping
    db.delete(mapping)
    db.commit()
    
    # Re-enrichir les transactions (elles seront remises à NULL si aucun autre mapping ne correspond)
    for transaction in transactions_to_re_enrich:
        enrich_transaction(transaction, db)
    
    db.commit()
    
    return None


@router.get("/mappings/combinations")
async def get_mapping_combinations(
    level_1: Optional[str] = Query(None, description="Filtrer par level_1"),
    level_2: Optional[str] = Query(None, description="Filtrer par level_2 (nécessite level_1)"),
    all_level_2: Optional[bool] = Query(False, description="Retourner tous les level_2 (ignorer le filtre level_1)"),
    all_level_3: Optional[bool] = Query(False, description="Retourner tous les level_3 (ignorer les filtres)"),
    db: Session = Depends(get_db)
):
    """
    Récupérer toutes les combinaisons possibles de level_1, level_2, level_3.
    
    Utilisé pour les dropdowns intelligents dans l'interface :
    - Si level_1 est fourni, retourne uniquement les level_2 possibles pour ce level_1
    - Si level_1 et level_2 sont fournis, retourne uniquement les level_3 possibles
    - Si all_level_2=True, retourne tous les level_2 disponibles (ignorer level_1)
    - Si all_level_3=True, retourne tous les level_3 disponibles (ignorer level_1 et level_2)
    - Sinon, retourne tous les level_1 disponibles
    
    Args:
        level_1: Filtrer par level_1 (optionnel)
        level_2: Filtrer par level_2 (optionnel, nécessite level_1)
        all_level_2: Si True, retourner tous les level_2 (ignorer level_1)
        all_level_3: Si True, retourner tous les level_3 (ignorer level_1 et level_2)
        db: Session de base de données
    
    Returns:
        Dictionnaire avec les combinaisons possibles :
        {
            "level_1": ["valeur1", "valeur2", ...],
            "level_2": ["valeur1", "valeur2", ...],
            "level_3": ["valeur1", "valeur2", ...]
        }
    """
    result: Dict[str, List[str]] = {}
    
    if all_level_3:
        # Retourner tous les level_3 disponibles (sans filtre)
        level_3_values = db.query(distinct(Mapping.level_3)).filter(
            Mapping.level_3.isnot(None)
        ).all()
        result["level_3"] = [v[0] for v in level_3_values if v[0] is not None]
    elif all_level_2:
        # Retourner tous les level_2 disponibles (sans filtre level_1)
        level_2_values = db.query(distinct(Mapping.level_2)).all()
        result["level_2"] = [v[0] for v in level_2_values if v[0] is not None]
    elif level_1 and level_2:
        # Récupérer tous les level_3 possibles pour cette combinaison level_1 + level_2
        level_3_values = db.query(distinct(Mapping.level_3)).filter(
            Mapping.level_1 == level_1,
            Mapping.level_2 == level_2,
            Mapping.level_3.isnot(None)
        ).all()
        result["level_3"] = [v[0] for v in level_3_values if v[0] is not None]
    elif level_1:
        # Récupérer tous les level_2 possibles pour ce level_1
        level_2_values = db.query(distinct(Mapping.level_2)).filter(
            Mapping.level_1 == level_1
        ).all()
        result["level_2"] = [v[0] for v in level_2_values if v[0] is not None]
    else:
        # Récupérer tous les level_1 disponibles
        level_1_values = db.query(distinct(Mapping.level_1)).all()
        # Extraire les valeurs (distinct retourne des tuples)
        result["level_1"] = [v[0] for v in level_1_values if v[0] is not None]
    
    return result


@router.get("/mappings/{mapping_id}", response_model=MappingResponse)
async def get_mapping(
    mapping_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupérer un mapping par son ID.
    
    Args:
        mapping_id: ID du mapping
        db: Session de base de données
    
    Returns:
        Détails du mapping
    
    Raises:
        HTTPException: Si le mapping n'existe pas
    """
    mapping = db.query(Mapping).filter(Mapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail=f"Mapping avec ID {mapping_id} non trouvé")
    
    return MappingResponse.model_validate(mapping)

