# Endpoints pour la gestion des allowed_mappings (Step 5.8)
# À ajouter à la fin de backend/api/routes/mappings.py

@router.get("/mappings/allowed", response_model=AllowedMappingListResponse)
async def get_allowed_mappings_endpoint(
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'éléments à retourner"),
    db: Session = Depends(get_db)
):
    """
    Récupère tous les mappings autorisés avec pagination pour une propriété.
    
    Args:
        property_id: ID de la propriété (obligatoire)
        skip: Nombre d'éléments à sauter
        limit: Nombre d'éléments à retourner
        db: Session de base de données
    
    Returns:
        Liste des mappings autorisés avec total
    """
    from backend.api.utils.validation import validate_property_id
    validate_property_id(db, property_id, "AllowedMappings")
    mappings, total = get_all_allowed_mappings(db, property_id, skip, limit)
    return AllowedMappingListResponse(
        mappings=[AllowedMappingResponse.model_validate(m) for m in mappings],
        total=total
    )


@router.post("/mappings/allowed", response_model=AllowedMappingResponse, status_code=201)
async def create_allowed_mapping_endpoint(
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    level_1: str = Query(..., description="Valeur de level_1"),
    level_2: str = Query(..., description="Valeur de level_2"),
    level_3: Optional[str] = Query(None, description="Valeur de level_3 (optionnel)"),
    db: Session = Depends(get_db)
):
    """
    Crée un nouveau mapping autorisé pour une propriété.
    
    Args:
        property_id: ID de la propriété (obligatoire)
        level_1: Valeur de level_1
        level_2: Valeur de level_2
        level_3: Valeur de level_3 (optionnel)
        db: Session de base de données
    
    Returns:
        Le mapping créé
    
    Raises:
        HTTPException: Si la combinaison existe déjà ou si level_3 n'est pas valide
    """
    from backend.api.utils.validation import validate_property_id
    validate_property_id(db, property_id, "AllowedMappings")
    try:
        mapping = create_allowed_mapping(db, level_1, level_2, property_id, level_3)
        return AllowedMappingResponse.model_validate(mapping)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/mappings/allowed/{mapping_id}", status_code=204)
async def delete_allowed_mapping_endpoint(
    mapping_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprime un mapping autorisé (uniquement si is_hardcoded = False).
    
    Args:
        mapping_id: ID du mapping à supprimer
        db: Session de base de données
    
    Raises:
        HTTPException: Si le mapping n'existe pas ou s'il est hard codé (403)
    """
    try:
        deleted = delete_allowed_mapping(db, mapping_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Mapping autorisé avec ID {mapping_id} non trouvé")
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/mappings/allowed/reset")
async def reset_allowed_mappings_endpoint(
    db: Session = Depends(get_db)
):
    """
    Reset les mappings autorisés : supprime uniquement les combinaisons ajoutées manuellement.
    
    Supprime aussi les mappings invalides et marque les transactions associées comme non assignées.
    
    Args:
        db: Session de base de données
    
    Returns:
        Statistiques de l'opération
    """
    try:
        stats = reset_allowed_mappings(db)
        return {
            "message": "Reset effectué avec succès",
            "deleted_allowed": stats["deleted_allowed"],
            "deleted_mappings": stats["deleted_mappings"],
            "unassigned_transactions": stats["unassigned_transactions"]
        }
    except Exception as e:
        logger.error(f"Erreur lors du reset des mappings autorisés: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du reset: {str(e)}")

