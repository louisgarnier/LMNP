"""
API routes for analytics and pivot tables.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import date
import logging

from backend.database import get_db
from backend.database.models import Transaction, EnrichedTransaction
from backend.api.models import TransactionResponse, TransactionListResponse
from backend.api.utils.validation import validate_property_id

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()


def get_field_column(field: str, transaction_alias=None, enriched_alias=None):
    """
    Retourne la colonne SQLAlchemy correspondant au champ demandé.
    
    Args:
        field: Nom du champ (date, mois, annee, level_1, level_2, level_3, nom)
        transaction_alias: Alias SQLAlchemy pour Transaction (optionnel)
        enriched_alias: Alias SQLAlchemy pour EnrichedTransaction (optionnel)
    
    Returns:
        Colonne SQLAlchemy
    """
    if transaction_alias is None:
        transaction_alias = Transaction
    if enriched_alias is None:
        enriched_alias = EnrichedTransaction
    
    field_mapping = {
        'date': transaction_alias.date,
        'mois': enriched_alias.mois,
        'annee': enriched_alias.annee,
        'level_1': enriched_alias.level_1,
        'level_2': enriched_alias.level_2,
        'level_3': enriched_alias.level_3,
        'nom': transaction_alias.nom,
    }
    
    if field not in field_mapping:
        raise ValueError(f"Champ '{field}' non supporté. Champs supportés: {list(field_mapping.keys())}")
    
    return field_mapping[field]


def apply_filters(query, filters: Dict[str, Any], property_id: int, transaction_alias=None, enriched_alias=None):
    """
    Applique les filtres à la requête.
    
    Args:
        query: Requête SQLAlchemy
        filters: Dictionnaire de filtres {field: value}
        property_id: ID de la propriété pour filtrer les transactions
        transaction_alias: Alias SQLAlchemy pour Transaction
        enriched_alias: Alias SQLAlchemy pour EnrichedTransaction
    
    Returns:
        Requête filtrée
    """
    logger.info(f"[PivotService] apply_filters - property_id={property_id}")
    
    if transaction_alias is None:
        transaction_alias = Transaction
    if enriched_alias is None:
        enriched_alias = EnrichedTransaction
    
    # Always filter by property_id first
    query = query.filter(transaction_alias.property_id == property_id)
    
    if not filters:
        return query
    
    for field, value in filters.items():
        if value is None:
            continue
        
        column = get_field_column(field, transaction_alias, enriched_alias)
        
        # Gérer les arrays de valeurs (OR pour le même champ)
        if isinstance(value, list):
            if len(value) == 0:
                continue
            # OR : au moins une des valeurs doit correspondre
            conditions = []
            for val in value:
                if val is None:
                    continue
                if field in ['nom', 'level_1', 'level_2', 'level_3']:
                    conditions.append(func.lower(column).contains(func.lower(str(val))))
                elif field == 'date':
                    conditions.append(column == val)
                else:  # mois, annee
                    conditions.append(column == val)
            
            if conditions:
                query = query.filter(or_(*conditions))
        else:
            # Valeur unique (compatibilité avec l'ancien format)
            # Pour les champs texte, utiliser LIKE (contient)
            if field in ['nom', 'level_1', 'level_2', 'level_3']:
                query = query.filter(func.lower(column).contains(func.lower(str(value))))
            # Pour les champs date, utiliser égalité
            elif field == 'date':
                query = query.filter(column == value)
            # Pour les champs numériques (mois, annee), utiliser égalité
            else:
                query = query.filter(column == value)
    
    return query


@router.get("/analytics/pivot")
async def get_pivot_data(
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    rows: Optional[str] = Query(None, description="Champs pour les lignes (séparés par virgule, ex: 'level_1,level_2')"),
    columns: Optional[str] = Query(None, description="Champs pour les colonnes (séparés par virgule, ex: 'mois')"),
    data_field: str = Query("quantite", description="Champ pour les données (quantite uniquement pour l'instant)"),
    data_operation: str = Query("sum", description="Opération sur les données (sum uniquement pour l'instant)"),
    filters: Optional[str] = Query(None, description="Filtres au format JSON (ex: '{\"level_1\": \"CHARGES\"}')"),
    db: Session = Depends(get_db)
):
    """
    Calcule les données pour un tableau croisé dynamique.
    
    Paramètres:
    - property_id: ID de la propriété (obligatoire)
    - rows: Champs pour les lignes (séparés par virgule)
    - columns: Champs pour les colonnes (séparés par virgule)
    - data_field: Champ pour les données (quantite uniquement)
    - data_operation: Opération (sum uniquement)
    - filters: Filtres au format JSON
    
    Retourne:
    - Structure de données pour tableau croisé (lignes, colonnes, valeurs, totaux)
    """
    import json
    
    logger.info(f"[Pivot] GET /api/analytics/pivot - property_id={property_id}")
    
    # Validate property_id
    validate_property_id(db, property_id, "Pivot")
    
    # Parser les paramètres
    row_fields = [f.strip() for f in rows.split(',')] if rows else []
    column_fields = [f.strip() for f in columns.split(',')] if columns else []
    
    # Valider data_field et data_operation
    if data_field != "quantite":
        raise HTTPException(status_code=400, detail=f"Champ data '{data_field}' non supporté. Seul 'quantite' est supporté.")
    if data_operation != "sum":
        raise HTTPException(status_code=400, detail=f"Opération '{data_operation}' non supportée. Seule 'sum' est supportée.")
    
    # Parser les filtres
    filter_dict = {}
    if filters:
        try:
            filter_dict = json.loads(filters)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Format de filtres invalide. Attendu: JSON")
    
    # Valider les champs
    all_fields = row_fields + column_fields + list(filter_dict.keys())
    valid_fields = ['date', 'mois', 'annee', 'level_1', 'level_2', 'level_3', 'nom']
    for field in all_fields:
        if field not in valid_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Champ '{field}' non supporté. Champs supportés: {valid_fields}"
            )
    
    # Construire la requête de base avec jointure EnrichedTransaction
    query = db.query(Transaction).outerjoin(
        EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
    )
    
    # Appliquer les filtres (includes property_id filtering)
    query = apply_filters(query, filter_dict, property_id)
    
    # Construire le groupby
    group_by_columns = []
    for field in row_fields:
        group_by_columns.append(get_field_column(field))
    for field in column_fields:
        group_by_columns.append(get_field_column(field))
    
    # Si pas de groupby, on retourne juste le total
    if not group_by_columns:
        total = query.with_entities(func.sum(Transaction.quantite)).scalar() or 0.0
        logger.info(f"[Pivot] Pivot data calculé pour property_id={property_id} - total={total}")
        return {
            "rows": [],
            "columns": [],
            "data": {"total": total},
            "row_totals": {},
            "column_totals": {},
            "grand_total": total
        }
    
    # Ajouter la somme de quantite
    select_columns = group_by_columns + [func.sum(Transaction.quantite).label('total_quantite')]
    
    # Appliquer groupby
    query = query.with_entities(*select_columns).group_by(*group_by_columns)
    
    # Exécuter la requête
    results = query.all()
    
    # Construire la structure de données pour le tableau croisé
    # Structure: {row_key: {column_key: value}}
    pivot_data = {}
    row_totals = {}
    column_totals = {}
    grand_total = 0.0
    
    for row in results:
        # Extraire les valeurs des lignes et colonnes
        row_values = []
        column_values = []
        total_quantite = row[-1]  # Dernière valeur = somme
        
        for i, field in enumerate(row_fields):
            row_values.append(row[i] if row[i] is not None else None)
        
        for i, field in enumerate(column_fields):
            column_values.append(row[len(row_fields) + i] if row[len(row_fields) + i] is not None else None)
        
        # Créer les clés (toujours des tuples pour être hashables)
        if len(row_values) > 1:
            row_key = tuple(row_values)
        elif len(row_values) == 1:
            row_key = row_values[0]
        else:
            row_key = None
        
        if len(column_values) > 1:
            column_key = tuple(column_values)
        elif len(column_values) == 1:
            column_key = column_values[0]
        else:
            column_key = None
        
        # Initialiser les structures si nécessaire
        if row_key not in pivot_data:
            pivot_data[row_key] = {}
            row_totals[row_key] = 0.0
        
        # Stocker la valeur
        pivot_data[row_key][column_key] = total_quantite or 0.0
        
        # Calculer les totaux
        row_totals[row_key] += total_quantite or 0.0
        if column_key not in column_totals:
            column_totals[column_key] = 0.0
        column_totals[column_key] += total_quantite or 0.0
        grand_total += total_quantite or 0.0
    
    # Convertir les tuples en listes pour la sérialisation JSON
    # Les clés de dictionnaire doivent être sérialisables (pas de listes, mais on peut utiliser des tuples convertis en strings ou créer une structure différente)
    def make_key_serializable(key):
        """Convertit une clé (tuple, int, str, None) en une clé sérialisable (string pour tuples)."""
        if isinstance(key, tuple):
            # Convertir le tuple en string pour la clé du dict (JSON ne supporte pas les listes comme clés)
            return str(list(key))
        elif key is None:
            return None
        else:
            return key
    
    def convert_dict_for_json(d):
        """Convertit un dictionnaire avec des clés tuples en dictionnaire avec des clés sérialisables."""
        new_dict = {}
        for k, v in d.items():
            serializable_key = make_key_serializable(k)
            if isinstance(v, dict):
                new_dict[serializable_key] = convert_dict_for_json(v)
            else:
                new_dict[serializable_key] = v
        return new_dict
    
    # Convertir pour JSON
    pivot_data_json = convert_dict_for_json(pivot_data)
    row_totals_json = convert_dict_for_json(row_totals)
    column_totals_json = convert_dict_for_json(column_totals)
    
    # Récupérer les valeurs uniques pour les lignes et colonnes (pour l'affichage)
    # Convertir les tuples en listes pour la sérialisation
    def make_serializable_list(items):
        """Convertit une liste d'items (peut contenir des tuples) en liste sérialisable."""
        result = []
        for item in items:
            if isinstance(item, tuple):
                result.append(list(item))
            else:
                result.append(item)
        return result
    
    unique_rows = sorted(set(pivot_data.keys()), key=lambda x: (x if isinstance(x, (str, int, type(None))) else str(x)))
    unique_columns = sorted(set(
        col for row_data in pivot_data.values() for col in row_data.keys()
    ), key=lambda x: (x if isinstance(x, (str, int, type(None))) else str(x)))
    
    # Convertir en listes sérialisables pour JSON
    unique_rows = make_serializable_list(unique_rows)
    unique_columns = make_serializable_list(unique_columns)
    
    logger.info(f"[Pivot] Pivot data calculé pour property_id={property_id} - {len(unique_rows)} lignes, {len(unique_columns)} colonnes")
    
    return {
        "rows": unique_rows,
        "columns": unique_columns,
        "data": pivot_data_json,
        "row_totals": row_totals_json,
        "column_totals": column_totals_json,
        "grand_total": grand_total,
        "row_fields": row_fields,
        "column_fields": column_fields
    }


@router.get("/analytics/pivot/details", response_model=TransactionListResponse)
async def get_pivot_details(
    property_id: int = Query(..., description="ID de la propriété (obligatoire)"),
    rows: Optional[str] = Query(None, description="Champs pour les lignes (séparés par virgule, ex: 'level_1,level_2')"),
    columns: Optional[str] = Query(None, description="Champs pour les colonnes (séparés par virgule, ex: 'mois')"),
    row_values: Optional[str] = Query(None, description="Valeurs spécifiques de la ligne (JSON array, ex: '[\"CHARGES\", \"Énergie\"]')"),
    column_values: Optional[str] = Query(None, description="Valeurs spécifiques de la colonne (JSON array, ex: '[1]')"),
    filters: Optional[str] = Query(None, description="Filtres au format JSON (ex: '{\"level_1\": \"CHARGES\"}')"),
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'éléments à retourner"),
    db: Session = Depends(get_db)
):
    """
    Récupère les transactions détaillées correspondant à une cellule du tableau croisé.
    
    Paramètres:
    - property_id: ID de la propriété (obligatoire)
    - rows: Champs pour les lignes (séparés par virgule)
    - columns: Champs pour les colonnes (séparés par virgule)
    - row_values: Valeurs spécifiques de la ligne (JSON array)
    - column_values: Valeurs spécifiques de la colonne (JSON array)
    - filters: Filtres au format JSON
    - skip: Pagination - nombre d'éléments à sauter
    - limit: Pagination - nombre d'éléments à retourner
    
    Retourne:
    - Liste des transactions correspondantes avec pagination
    """
    import json
    
    logger.info(f"[Pivot] GET /api/analytics/pivot/details - property_id={property_id}")
    
    # Validate property_id
    validate_property_id(db, property_id, "Pivot")
    
    # Parser les paramètres
    row_fields = [f.strip() for f in rows.split(',')] if rows else []
    column_fields = [f.strip() for f in columns.split(',')] if columns else []
    
    # Parser les valeurs de ligne et colonne
    row_vals = []
    column_vals = []
    if row_values:
        try:
            row_vals = json.loads(row_values)
            if not isinstance(row_vals, list):
                raise HTTPException(status_code=400, detail="row_values doit être un array JSON")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Format de row_values invalide. Attendu: JSON array")
    
    if column_values:
        try:
            column_vals = json.loads(column_values)
            if not isinstance(column_vals, list):
                raise HTTPException(status_code=400, detail="column_values doit être un array JSON")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Format de column_values invalide. Attendu: JSON array")
    
    # Parser les filtres
    filter_dict = {}
    if filters:
        try:
            filter_dict = json.loads(filters)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Format de filtres invalide. Attendu: JSON")
    
    # Valider que le nombre de valeurs correspond au nombre de champs
    if len(row_vals) != len(row_fields):
        raise HTTPException(
            status_code=400,
            detail=f"Nombre de row_values ({len(row_vals)}) ne correspond pas au nombre de row_fields ({len(row_fields)})"
        )
    
    if len(column_vals) != len(column_fields):
        raise HTTPException(
            status_code=400,
            detail=f"Nombre de column_values ({len(column_vals)}) ne correspond pas au nombre de column_fields ({len(column_fields)})"
        )
    
    # Construire la requête de base avec jointure EnrichedTransaction
    query = db.query(Transaction).outerjoin(
        EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
    )
    
    # Appliquer les filtres globaux (includes property_id filtering)
    query = apply_filters(query, filter_dict, property_id)
    
    # Appliquer les filtres pour les valeurs de ligne
    for i, field in enumerate(row_fields):
        value = row_vals[i] if i < len(row_vals) else None
        if value is not None:
            column = get_field_column(field)
            # Pour les champs texte, utiliser égalité exacte (pas LIKE car on veut une correspondance exacte)
            if field in ['nom', 'level_1', 'level_2', 'level_3']:
                query = query.filter(func.lower(column) == func.lower(str(value)))
            # Pour les autres champs, utiliser égalité
            else:
                query = query.filter(column == value)
    
    # Appliquer les filtres pour les valeurs de colonne
    for i, field in enumerate(column_fields):
        value = column_vals[i] if i < len(column_vals) else None
        if value is not None:
            column = get_field_column(field)
            # Pour les champs texte, utiliser égalité exacte
            if field in ['nom', 'level_1', 'level_2', 'level_3']:
                query = query.filter(func.lower(column) == func.lower(str(value)))
            # Pour les autres champs, utiliser égalité
            else:
                query = query.filter(column == value)
    
    # Compter le total
    total = query.count()
    
    # Appliquer la pagination
    transactions = query.offset(skip).limit(limit).all()
    
    # Récupérer les données enrichies pour chaque transaction
    transaction_responses = []
    for t in transactions:
        # Récupérer les données enrichies
        enriched = db.query(EnrichedTransaction).filter(
            EnrichedTransaction.transaction_id == t.id
        ).first()
        
        # Créer la réponse avec les données enrichies
        transaction_dict = {
            "id": t.id,
            "date": t.date,
            "quantite": t.quantite,
            "nom": t.nom,
            "solde": t.solde,
            "source_file": t.source_file,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
            "level_1": enriched.level_1 if enriched else None,
            "level_2": enriched.level_2 if enriched else None,
            "level_3": enriched.level_3 if enriched else None,
        }
        transaction_responses.append(TransactionResponse(**transaction_dict))
    
    logger.info(f"[Pivot] Pivot details retournés pour property_id={property_id} - {len(transaction_responses)} transactions")
    
    return TransactionListResponse(
        transactions=transaction_responses,
        total=total,
        page=(skip // limit) + 1 if limit > 0 else 1,
        page_size=limit
    )
