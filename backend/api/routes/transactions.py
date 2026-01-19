"""
API routes for transactions.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc, func
from typing import List, Optional
from datetime import date, datetime
import os
from pathlib import Path
import pandas as pd

from backend.database import get_db
from backend.database.models import Transaction, FileImport, EnrichedTransaction
from backend.api.services.enrichment_service import enrich_transaction
from backend.api.models import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionListResponse,
    FilePreviewResponse,
    FileImportRequest,
    FileImportResponse,
    FileImportHistory,
    ColumnMapping,
    DuplicateTransaction,
    TransactionError
)
from backend.api.utils.csv_utils import (
    read_csv_safely,
    detect_column_mapping,
    validate_transactions,
    preview_transactions
)

router = APIRouter()


@router.get("/transactions", response_model=TransactionListResponse)
async def get_transactions(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'éléments à retourner"),
    start_date: Optional[date] = Query(None, description="Date de début (filtre)"),
    end_date: Optional[date] = Query(None, description="Date de fin (filtre)"),
    sort_by: Optional[str] = Query(None, description="Colonne de tri (date, quantite, nom, solde, level_1, level_2, level_3)"),
    sort_direction: Optional[str] = Query("desc", description="Direction du tri (asc, desc)"),
    filter_nom: Optional[str] = Query(None, description="Filtre sur le nom (contient, insensible à la casse)"),
    filter_level_1: Optional[str] = Query(None, description="Filtre sur level_1 (contient, insensible à la casse)"),
    filter_level_2: Optional[str] = Query(None, description="Filtre sur level_2 (contient, insensible à la casse)"),
    filter_level_3: Optional[str] = Query(None, description="Filtre sur level_3 (contient, insensible à la casse)"),
    filter_quantite_min: Optional[float] = Query(None, description="Filtre quantité minimum"),
    filter_quantite_max: Optional[float] = Query(None, description="Filtre quantité maximum"),
    filter_solde_min: Optional[float] = Query(None, description="Filtre solde minimum"),
    filter_solde_max: Optional[float] = Query(None, description="Filtre solde maximum"),
    unclassified_only: Optional[bool] = Query(None, description="Filtrer uniquement les transactions non classées (level_1/2/3 = NULL)"),
    db: Session = Depends(get_db)
):
    """
    Récupérer la liste des transactions.
    
    - **skip**: Nombre d'éléments à sauter (pagination)
    - **limit**: Nombre d'éléments à retourner (max 1000)
    - **start_date**: Filtrer par date de début (optionnel)
    - **end_date**: Filtrer par date de fin (optionnel)
    - **sort_by**: Colonne de tri (date, quantite, nom, solde, level_1, level_2, level_3)
    - **sort_direction**: Direction du tri (asc, desc)
    - **filter_nom**: Filtrer par nom (contient, insensible à la casse)
    - **filter_level_1**: Filtrer par level_1 (contient, insensible à la casse)
    - **filter_level_2**: Filtrer par level_2 (contient, insensible à la casse)
    - **filter_level_3**: Filtrer par level_3 (contient, insensible à la casse)
    - **filter_quantite_min**: Filtrer par quantité minimum
    - **filter_quantite_max**: Filtrer par quantité maximum
    - **filter_solde_min**: Filtrer par solde minimum
    - **filter_solde_max**: Filtrer par solde maximum
    """
    # Base query - on va joindre avec EnrichedTransaction si nécessaire pour le tri ou les filtres
    base_query = db.query(Transaction)
    
    # Déterminer si on doit joindre avec EnrichedTransaction
    needs_join = (
        (sort_by and sort_by in ["level_1", "level_2", "level_3"]) or
        filter_level_1 or filter_level_2 or filter_level_3 or
        unclassified_only
    )
    
    if needs_join:
        query = base_query.outerjoin(EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id)
    else:
        query = base_query
    
    # Filtre pour transactions non classées (level_1/2/3 = NULL)
    if unclassified_only:
        if not needs_join:
            query = query.outerjoin(EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id)
        # Filtrer les transactions où level_1 est NULL (ou EnrichedTransaction n'existe pas)
        query = query.filter(
            or_(
                EnrichedTransaction.level_1.is_(None),
                EnrichedTransaction.transaction_id.is_(None)
            )
        )
    
    # Filtres par date
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    
    # Filtres texte (contient, insensible à la casse)
    if filter_nom:
        query = query.filter(func.lower(Transaction.nom).contains(func.lower(filter_nom)))
    
    if filter_level_1:
        if not needs_join:
            query = query.outerjoin(EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id)
        filter_normalized = filter_level_1.lower().strip()
        # Détecter "unassigned" ou préfixe de "unassigned" (ex: "un", "una", "unas")
        if filter_normalized == "unassigned":
            query = query.filter(EnrichedTransaction.level_1.is_(None))
        elif "unassigned".startswith(filter_normalized):
            # Si le filtre est un préfixe de "unassigned", inclure les NULL ET les valeurs qui contiennent le filtre
            query = query.filter(
                or_(
                    EnrichedTransaction.level_1.is_(None),
                    func.lower(EnrichedTransaction.level_1).contains(func.lower(filter_level_1))
                )
            )
        else:
            query = query.filter(func.lower(EnrichedTransaction.level_1).contains(func.lower(filter_level_1)))
    
    if filter_level_2:
        if not needs_join:
            query = query.outerjoin(EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id)
        filter_normalized = filter_level_2.lower().strip()
        # Détecter "unassigned" ou préfixe de "unassigned" (ex: "un", "una", "unas")
        if filter_normalized == "unassigned":
            query = query.filter(EnrichedTransaction.level_2.is_(None))
        elif "unassigned".startswith(filter_normalized):
            # Si le filtre est un préfixe de "unassigned", inclure les NULL ET les valeurs qui contiennent le filtre
            query = query.filter(
                or_(
                    EnrichedTransaction.level_2.is_(None),
                    func.lower(EnrichedTransaction.level_2).contains(func.lower(filter_level_2))
                )
            )
        else:
            query = query.filter(func.lower(EnrichedTransaction.level_2).contains(func.lower(filter_level_2)))
    
    if filter_level_3:
        if not needs_join:
            query = query.outerjoin(EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id)
        filter_normalized = filter_level_3.lower().strip()
        # Détecter "unassigned" ou préfixe de "unassigned" (ex: "un", "una", "unas")
        if filter_normalized == "unassigned":
            query = query.filter(EnrichedTransaction.level_3.is_(None))
        elif "unassigned".startswith(filter_normalized):
            # Si le filtre est un préfixe de "unassigned", inclure les NULL ET les valeurs qui contiennent le filtre
            query = query.filter(
                or_(
                    EnrichedTransaction.level_3.is_(None),
                    func.lower(EnrichedTransaction.level_3).contains(func.lower(filter_level_3))
                )
            )
        else:
            query = query.filter(func.lower(EnrichedTransaction.level_3).contains(func.lower(filter_level_3)))
    
    # Filtres numériques (quantité)
    if filter_quantite_min is not None:
        query = query.filter(Transaction.quantite >= filter_quantite_min)
    if filter_quantite_max is not None:
        query = query.filter(Transaction.quantite <= filter_quantite_max)
    
    # Filtres numériques (solde)
    if filter_solde_min is not None:
        query = query.filter(Transaction.solde >= filter_solde_min)
    if filter_solde_max is not None:
        query = query.filter(Transaction.solde <= filter_solde_max)
    
    # Compter le total (avant tri)
    total = query.count()
    
    # Tri
    if sort_by:
        # Normaliser la direction
        sort_dir = sort_direction.lower() if sort_direction else "desc"
        if sort_dir not in ["asc", "desc"]:
            sort_dir = "desc"
        
        # Déterminer la colonne de tri
        if sort_by == "date":
            order_col = Transaction.date
        elif sort_by == "quantite":
            order_col = Transaction.quantite
        elif sort_by == "nom":
            order_col = Transaction.nom
        elif sort_by == "solde":
            order_col = Transaction.solde
        elif sort_by == "level_1":
            if not needs_join:
                query = query.outerjoin(EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id)
            order_col = EnrichedTransaction.level_1
        elif sort_by == "level_2":
            if not needs_join:
                query = query.outerjoin(EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id)
            order_col = EnrichedTransaction.level_2
        elif sort_by == "level_3":
            if not needs_join:
                query = query.outerjoin(EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id)
            order_col = EnrichedTransaction.level_3
        else:
            # Par défaut, trier par date desc
            order_col = Transaction.date
            sort_dir = "desc"
        
        # Appliquer le tri
        if sort_dir == "asc":
            query = query.order_by(asc(order_col))
        else:
            query = query.order_by(desc(order_col))
    else:
        # Par défaut, trier par date desc
        query = query.order_by(desc(Transaction.date))
    
    # Pagination
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
    
    return TransactionListResponse(
        transactions=transaction_responses,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit
    )


@router.get("/transactions/unique-values")
async def get_transaction_unique_values(
    column: str = Query(..., description="Nom de la colonne (nom, level_1, level_2, level_3)"),
    start_date: Optional[date] = Query(None, description="Date de début (filtre optionnel)"),
    end_date: Optional[date] = Query(None, description="Date de fin (filtre optionnel)"),
    filter_level_2: Optional[str] = Query(None, description="Filtrer par level_2 (optionnel, pour filtrer les level_1 par level_2)"),
    filter_level_3: Optional[str] = Query(None, description="Filtrer par level_3 (optionnel, valeurs séparées par virgule, pour filtrer les level_1 par plusieurs level_3)"),
    db: Session = Depends(get_db)
):
    """
    Récupérer les valeurs uniques d'une colonne pour les filtres.
    
    - **column**: Nom de la colonne (nom, level_1, level_2, level_3)
    - **start_date**: Filtrer par date de début (optionnel)
    - **end_date**: Filtrer par date de fin (optionnel)
    - **filter_level_2**: Filtrer par level_2 (optionnel, utile pour filtrer les level_1 par level_2)
    - **filter_level_3**: Filtrer par level_3 (optionnel, valeurs séparées par virgule, pour filtrer les level_1 par plusieurs level_3)
    
    Returns:
        Liste des valeurs uniques (non null, triées)
    """
    # Optimisation: Pour level_1/2/3, on n'a besoin du JOIN que si on filtre par date
    needs_date_filter = start_date or end_date
    needs_join = needs_date_filter and column in ["level_1", "level_2", "level_3"]
    
    # Base query avec join seulement si nécessaire
    if column in ["level_1", "level_2", "level_3"]:
        if needs_join:
            query = db.query(EnrichedTransaction).join(Transaction, Transaction.id == EnrichedTransaction.transaction_id)
        else:
            # Pas besoin de JOIN si on ne filtre pas par date - beaucoup plus rapide
            query = db.query(EnrichedTransaction)
    else:
        query = db.query(Transaction)
    
    # Filtre par level_2 si fourni (utile pour filtrer les level_1 par level_2)
    if filter_level_2:
        if column in ["level_1", "level_2", "level_3"]:
            query = query.filter(EnrichedTransaction.level_2 == filter_level_2)
        # Note: pour les autres colonnes (nom, date, etc.), on ne filtre pas par level_2 car elles ne sont pas dans EnrichedTransaction
    
    # Filtre par level_3 si fourni (utile pour filtrer les level_1 par plusieurs level_3)
    if filter_level_3:
        if column in ["level_1", "level_2", "level_3"]:
            # Parser les valeurs séparées par virgule
            level_3_values = [v.strip() for v in filter_level_3.split(',') if v.strip()]
            if level_3_values:
                query = query.filter(EnrichedTransaction.level_3.in_(level_3_values))
        # Note: pour les autres colonnes (nom, date, etc.), on ne filtre pas par level_3 car elles ne sont pas dans EnrichedTransaction
    
    # Filtres par date si fournis
    if start_date:
        if column in ["level_1", "level_2", "level_3"]:
            if not needs_join:
                # Ajouter le JOIN si nécessaire
                query = query.join(Transaction, Transaction.id == EnrichedTransaction.transaction_id)
            query = query.filter(Transaction.date >= start_date)
        else:
            query = query.filter(Transaction.date >= start_date)
    if end_date:
        if column in ["level_1", "level_2", "level_3"]:
            if not needs_join and not start_date:
                # Ajouter le JOIN si nécessaire
                query = query.join(Transaction, Transaction.id == EnrichedTransaction.transaction_id)
            query = query.filter(Transaction.date <= end_date)
        else:
            query = query.filter(Transaction.date <= end_date)
    
    # Récupérer les valeurs uniques selon la colonne
    if column == "nom":
        values = query.with_entities(Transaction.nom).distinct().filter(Transaction.nom.isnot(None)).order_by(Transaction.nom).all()
        unique_values = [v[0] for v in values if v[0]]
    elif column == "level_1":
        # Utiliser distinct() directement sur la colonne pour optimiser
        values = query.with_entities(EnrichedTransaction.level_1).distinct().filter(EnrichedTransaction.level_1.isnot(None)).order_by(EnrichedTransaction.level_1).all()
        unique_values = [v[0] for v in values if v[0]]
    elif column == "level_2":
        values = query.with_entities(EnrichedTransaction.level_2).distinct().filter(EnrichedTransaction.level_2.isnot(None)).order_by(EnrichedTransaction.level_2).all()
        unique_values = [v[0] for v in values if v[0]]
    elif column == "level_3":
        values = query.with_entities(EnrichedTransaction.level_3).distinct().filter(EnrichedTransaction.level_3.isnot(None)).order_by(EnrichedTransaction.level_3).all()
        unique_values = [v[0] for v in values if v[0]]
    elif column == "date":
        values = query.with_entities(Transaction.date).distinct().filter(Transaction.date.isnot(None)).order_by(Transaction.date).all()
        unique_values = [v[0].strftime('%Y-%m-%d') if v[0] else None for v in values if v[0]]
        unique_values = [v for v in unique_values if v]
    elif column == "mois":
        query = db.query(EnrichedTransaction).join(Transaction, Transaction.id == EnrichedTransaction.transaction_id)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        values = query.with_entities(EnrichedTransaction.mois).distinct().filter(EnrichedTransaction.mois.isnot(None)).order_by(EnrichedTransaction.mois).all()
        unique_values = [str(v[0]) for v in values if v[0] is not None]
    elif column == "annee":
        query = db.query(EnrichedTransaction).join(Transaction, Transaction.id == EnrichedTransaction.transaction_id)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        values = query.with_entities(EnrichedTransaction.annee).distinct().filter(EnrichedTransaction.annee.isnot(None)).order_by(EnrichedTransaction.annee).all()
        unique_values = [str(v[0]) for v in values if v[0] is not None]
    else:
        raise HTTPException(status_code=400, detail=f"Colonne '{column}' non supportée. Colonnes supportées: nom, level_1, level_2, level_3, date, mois, annee")
    
    return {"column": column, "values": unique_values}


@router.get("/transactions/imports", response_model=List[FileImportHistory])
async def get_imports_history(
    db: Session = Depends(get_db)
):
    """
    Récupère l'historique des imports de fichiers.
    """
    imports = db.query(FileImport).order_by(FileImport.imported_at.desc()).all()
    
    return [FileImportHistory.model_validate(imp) for imp in imports]


@router.delete("/transactions/imports", status_code=204)
async def delete_all_imports(
    db: Session = Depends(get_db)
):
    """
    Supprime tous les imports de transactions de l'historique.
    
    ⚠️ ATTENTION : Cette action est irréversible et supprime définitivement tous les historiques d'imports.
    """
    db.query(FileImport).delete()
    db.commit()
    
    return None


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupérer une transaction par son ID.
    """
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction non trouvée")
    
    # Récupérer les données enrichies
    enriched = db.query(EnrichedTransaction).filter(
        EnrichedTransaction.transaction_id == transaction.id
    ).first()
    
    # Créer la réponse avec les données enrichies
    transaction_dict = {
        "id": transaction.id,
        "date": transaction.date,
        "quantite": transaction.quantite,
        "nom": transaction.nom,
        "solde": transaction.solde,
        "source_file": transaction.source_file,
        "created_at": transaction.created_at,
        "updated_at": transaction.updated_at,
        "level_1": enriched.level_1 if enriched else None,
        "level_2": enriched.level_2 if enriched else None,
        "level_3": enriched.level_3 if enriched else None,
    }
    
    return TransactionResponse(**transaction_dict)


@router.post("/transactions", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):
    """
    Créer une nouvelle transaction.
    Note: Enrichit automatiquement la transaction et recalcule les amortissements si applicable.
    """
    from backend.api.services.amortization_service import recalculate_transaction_amortization
    from backend.api.utils.balance_utils import recalculate_balances_from_date
    
    db_transaction = Transaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    
    # Enrichir automatiquement la transaction
    try:
        enriched = enrich_transaction(db_transaction, db)
        
        # Recalculer les amortissements après enrichissement
        # (gestion silencieuse des erreurs pour ne pas bloquer la création de transaction)
        # La fonction recalculate_transaction_amortization gère déjà le cas où il n'y a pas de level_2
        try:
            recalculate_transaction_amortization(db, db_transaction.id)
        except Exception as e:
            # Log l'erreur mais ne bloque pas la création de transaction
            import traceback
            error_details = traceback.format_exc()
            print(f"⚠️ [create_transaction] Erreur lors du recalcul des amortissements pour transaction {db_transaction.id}: {error_details}")
    except Exception as e:
        # Log l'erreur d'enrichissement mais ne bloque pas la création de transaction
        import traceback
        error_details = traceback.format_exc()
        print(f"⚠️ [create_transaction] Erreur lors de l'enrichissement de la transaction {db_transaction.id}: {error_details}")
        
        # Même si l'enrichissement échoue, essayer de recalculer les amortissements
        # (au cas où la transaction aurait déjà un enrichissement existant)
        try:
            recalculate_transaction_amortization(db, db_transaction.id)
        except Exception as e2:
            # Log l'erreur mais ne bloque pas la création de transaction
            import traceback
            error_details2 = traceback.format_exc()
            print(f"⚠️ [create_transaction] Erreur lors du recalcul des amortissements (après échec enrichissement) pour transaction {db_transaction.id}: {error_details2}")
    
    # Recalculer les soldes à partir de la date de la transaction
    try:
        recalculate_balances_from_date(db, db_transaction.date)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"⚠️ [create_transaction] Erreur lors du recalcul des soldes: {error_details}")
    
    # Invalider les comptes de résultat pour l'année de la transaction
    try:
        from backend.api.services.compte_resultat_service import invalidate_compte_resultat_for_transaction_date
        invalidate_compte_resultat_for_transaction_date(db, db_transaction.date)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"⚠️ [create_transaction] Erreur lors de l'invalidation des comptes de résultat: {error_details}")
    
    # Invalider le bilan pour l'année de la transaction
    try:
        from backend.api.services.bilan_service import invalidate_bilan_for_year
        invalidate_bilan_for_year(db_transaction.date.year, db)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"⚠️ [create_transaction] Erreur lors de l'invalidation du bilan: {error_details}")
    
    return TransactionResponse.from_orm(db_transaction)


@router.put("/transactions/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int,
    transaction_update: TransactionUpdate,
    db: Session = Depends(get_db)
):
    """
    Mettre à jour une transaction existante.
    Note: Recalcule automatiquement les soldes après modification.
    """
    from backend.api.utils.balance_utils import recalculate_balances_from_date
    
    db_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction non trouvée")
    
    # Sauvegarder la date avant modification pour recalculer les soldes
    old_date = db_transaction.date
    old_quantite = db_transaction.quantite
    
    # Mettre à jour uniquement les champs fournis
    update_data = transaction_update.dict(exclude_unset=True)
    
    # Convertir la date string en date object si présente
    new_date = old_date
    if 'date' in update_data and update_data['date'] is not None:
        if isinstance(update_data['date'], str):
            try:
                from datetime import datetime as dt
                new_date = dt.strptime(update_data['date'], '%Y-%m-%d').date()
                update_data['date'] = new_date
            except ValueError:
                raise HTTPException(status_code=400, detail="Format de date invalide (attendu: YYYY-MM-DD)")
        else:
            new_date = update_data['date']
    
    # Déterminer la date minimale pour recalculer les soldes
    min_date = min(old_date, new_date)
    
    # Détecter si les champs qui impactent les amortissements ont été modifiés
    # - quantite : impacte le montant d'immobilisation
    # - date : impacte la date de début si start_date n'est pas défini dans le type
    should_recalculate_amortization = False
    if 'quantite' in update_data and update_data['quantite'] != old_quantite:
        should_recalculate_amortization = True
    if 'date' in update_data and new_date != old_date:
        should_recalculate_amortization = True
    
    for field, value in update_data.items():
        setattr(db_transaction, field, value)
    
    db.commit()
    
    # Recalculer les soldes à partir de la date la plus ancienne
    try:
        recalculate_balances_from_date(db, min_date)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Erreur lors du recalcul des soldes: {error_details}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors du recalcul des soldes: {str(e)}")
    
    # Invalider les comptes de résultat pour l'ancienne et la nouvelle année si la date a changé
    try:
        from backend.api.services.compte_resultat_service import invalidate_compte_resultat_for_year
        invalidate_compte_resultat_for_year(db, old_date.year)
        if new_date != old_date:
            invalidate_compte_resultat_for_year(db, new_date.year)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"⚠️ [update_transaction] Erreur lors de l'invalidation des comptes de résultat: {error_details}")
    
    # Invalider le bilan pour l'ancienne et la nouvelle année si la date a changé
    try:
        from backend.api.services.bilan_service import invalidate_bilan_for_year
        invalidate_bilan_for_year(old_date.year, db)
        if new_date != old_date:
            invalidate_bilan_for_year(new_date.year, db)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"⚠️ [update_transaction] Erreur lors de l'invalidation du bilan: {error_details}")
    
    # Recalculer les amortissements si les champs impactants ont été modifiés
    # (gestion silencieuse des erreurs pour ne pas bloquer la modification)
    if should_recalculate_amortization:
        try:
            from backend.api.services.amortization_service import recalculate_transaction_amortization
            recalculate_transaction_amortization(db, transaction_id)
        except Exception as e:
            # Log l'erreur mais ne bloque pas la modification
            import traceback
            error_details = traceback.format_exc()
            print(f"⚠️ [update_transaction] Erreur lors du recalcul des amortissements pour transaction {transaction_id}: {error_details}")
    
    db.refresh(db_transaction)
    
    return TransactionResponse.model_validate(db_transaction)


@router.delete("/transactions/{transaction_id}", status_code=204)
async def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprimer une transaction.
    Note: Supprime également les données enrichies associées, les résultats d'amortissement et recalcule les soldes.
    """
    from backend.database.models import EnrichedTransaction, Amortization, AmortizationResult
    from backend.api.utils.balance_utils import recalculate_balances_from_date
    
    db_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction non trouvée")
    
    # Sauvegarder la date pour recalculer les soldes après
    transaction_date = db_transaction.date
    
    # Supprimer les données associées en cascade
    db.query(EnrichedTransaction).filter(
        EnrichedTransaction.transaction_id == transaction_id
    ).delete()
    
    db.query(Amortization).filter(
        Amortization.transaction_id == transaction_id
    ).delete()
    
    # Supprimer les résultats d'amortissement associés
    db.query(AmortizationResult).filter(
        AmortizationResult.transaction_id == transaction_id
    ).delete()
    
    # Supprimer la transaction
    db.delete(db_transaction)
    db.commit()
    
    # Recalculer les soldes des transactions suivantes
    recalculate_balances_from_date(db, transaction_date)
    
    # Invalider le bilan pour l'année de la transaction supprimée
    try:
        from backend.api.services.bilan_service import invalidate_bilan_for_year
        invalidate_bilan_for_year(transaction_date.year, db)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"⚠️ [delete_transaction] Erreur lors de l'invalidation du bilan: {error_details}")
    
    return None


# File upload endpoints

@router.post("/transactions/preview", response_model=FilePreviewResponse)
async def preview_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Prévisualise un fichier CSV et détecte le mapping des colonnes.
    
    - **file**: Fichier CSV à analyser
    - Retourne: Preview, mapping proposé, statistiques
    """
    # Lire le fichier
    file_content = await file.read()
    
    try:
        # Lire CSV avec détection automatique
        df, encoding, separator = read_csv_safely(file_content, file.filename)
        
        # Détecter mapping colonnes
        detected_mapping = detect_column_mapping(df)
        
        # Valider les données
        df_validated, validation_errors = validate_transactions(df, detected_mapping)
        
        # Créer mapping formaté pour la réponse
        column_mapping = [
            ColumnMapping(file_column=file_col, db_column=db_col)
            for file_col, db_col in detected_mapping.items()
        ]
        
        # Preview des premières lignes
        preview = preview_transactions(df_validated, detected_mapping, num_rows=10)
        
        # Statistiques
        date_col = None
        for col, db_col in detected_mapping.items():
            if db_col == 'date':
                date_col = col
                break
        
        stats = {
            "total_rows": len(df),
            "valid_rows": len(df_validated),
        }
        
        if date_col and len(df_validated) > 0:
            dates = df_validated[date_col]
            stats["date_min"] = dates.min().strftime('%d/%m/%Y') if pd.notna(dates.min()) else None
            stats["date_max"] = dates.max().strftime('%d/%m/%Y') if pd.notna(dates.max()) else None
        
        return FilePreviewResponse(
            filename=file.filename or "unknown.csv",
            encoding=encoding,
            separator=separator,
            total_rows=len(df),
            column_mapping=column_mapping,
            preview=preview,
            validation_errors=validation_errors,
            stats=stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de l'analyse du fichier: {str(e)}")


@router.get("/transactions/sum-by-level1")
async def get_transaction_sum_by_level1(
    level_1: str = Query(..., description="Valeur de level_1 à filtrer"),
    end_date: Optional[date] = Query(None, description="Date de fin (filtre optionnel, cumul jusqu'à cette date)"),
    db: Session = Depends(get_db)
):
    """
    Calculer la somme des transactions pour un level_1 donné.
    
    Utile pour valider que le montant du crédit configuré correspond aux transactions réelles.
    
    - **level_1**: Valeur de level_1 à filtrer (ex: "Dettes financières (emprunt bancaire)")
    - **end_date**: Date de fin optionnelle (cumul jusqu'à cette date, sinon toutes les transactions)
    
    Returns:
        Montant total (somme des quantite) pour ce level_1
    """
    query = db.query(
        func.sum(Transaction.quantite)
    ).join(
        EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
    ).filter(
        EnrichedTransaction.level_1 == level_1
    )
    
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    
    total = query.scalar()
    
    return {
        "level_1": level_1,
        "total": abs(total) if total is not None else 0.0,
        "end_date": end_date.isoformat() if end_date else None
    }


@router.post("/transactions/import", response_model=FileImportResponse)
async def import_file(
    file: UploadFile = File(...),
    mapping: str = Form(..., description="Mapping JSON string"),
    db: Session = Depends(get_db)
):
    """
    Importe un fichier CSV dans la base de données.
    
    - **file**: Fichier CSV à importer
    - **mapping**: Mapping des colonnes (JSON string)
    - Retourne: Statistiques d'import (imported, duplicates, errors)
    """
    import json
    
    try:
        # Parser le mapping
        mapping_data = json.loads(mapping)
        column_mapping = {item['file_column']: item['db_column'] for item in mapping_data}
        
        # Vérifier si fichier déjà chargé (avertissement mais on continue)
        filename = file.filename or "unknown.csv"
        existing_import = db.query(FileImport).filter(FileImport.filename == filename).first()
        warning_message = None
        
        if existing_import:
            warning_message = f"⚠️ Le fichier {filename} a déjà été chargé le {existing_import.imported_at.strftime('%d/%m/%Y %H:%M')}. Le traitement continue, les doublons seront détectés."
        
        # Lire le fichier
        file_content = await file.read()
        
        # Sauvegarder le fichier dans data/input/trades/
        trades_dir = Path(__file__).parent.parent.parent / "data" / "input" / "trades"
        trades_dir.mkdir(parents=True, exist_ok=True)
        file_path = trades_dir / filename
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Lire CSV
        df, encoding, separator = read_csv_safely(file_content, filename)
        
        # Si le mapping contient une colonne combinée (ex: "Col5_combined"), la recréer
        # car elle a été créée lors de la détection mais n'existe pas dans le nouveau DataFrame
        nom_col = None
        for file_col, db_col in column_mapping.items():
            if db_col == 'nom':
                nom_col = file_col
                break
        
        # Si la colonne nom est une colonne combinée (contient "_combined"), la recréer
        if nom_col and '_combined' in nom_col and nom_col not in df.columns:
            # Extraire la colonne de base (ex: "Col5_combined" → "Col5")
            base_col = nom_col.replace('_combined', '')
            
            # Chercher les colonnes non mappées qui pourraient être combinées
            # On cherche les colonnes qui ne sont pas déjà mappées et qui contiennent du texte
            other_text_cols = []
            for col in df.columns:
                if col not in column_mapping.keys() and col != base_col:
                    col_data = df[col].astype(str)
                    non_empty = col_data[col_data.str.strip() != '']
                    if len(non_empty) > len(df) * 0.1:  # Au moins 10% de valeurs non vides
                        # Vérifier que ce n'est pas une date ou un nombre
                        is_text = True
                        sample_size = min(10, len(non_empty))
                        for val in non_empty.head(sample_size):
                            val_str = str(val).strip()
                            if len(val_str) > 2:
                                try:
                                    # Utiliser l'import global datetime
                                    datetime.strptime(val_str, '%d/%m/%Y')
                                    is_text = False
                                    break
                                except:
                                    pass
                                try:
                                    float(val_str.replace(',', '.').replace(' ', ''))
                                    is_text = False
                                    break
                                except:
                                    pass
                        if is_text:
                            other_text_cols.append(col)
            
            # Si on trouve une autre colonne et que la colonne de base existe, les combiner
            if other_text_cols and base_col in df.columns:
                best_other_col = other_text_cols[0]
                def combine_cols(row):
                    val1 = str(row[base_col]) if pd.notna(row[base_col]) else ''
                    val2 = str(row[best_other_col]) if pd.notna(row[best_other_col]) else ''
                    val1 = val1.strip()
                    val2 = val2.strip()
                    if val1.lower() == 'none':
                        val1 = ''
                    if val2.lower() == 'none':
                        val2 = ''
                    if val1 and val2:
                        return (val1 + ' ' + val2).strip()
                    return val1 or val2
                
                df[nom_col] = df.apply(combine_cols, axis=1)
            elif base_col in df.columns:
                # Si on ne trouve pas d'autre colonne, utiliser juste la colonne de base
                df[nom_col] = df[base_col].astype(str).str.strip()
        
        # Valider les données
        df_validated, validation_errors = validate_transactions(df, column_mapping)
        
        # Détecter les doublons et insérer
        imported_count = 0
        duplicates_count = 0
        duplicates_list = []
        errors_count = len(validation_errors)
        errors_list = []
        
        # Ajouter les erreurs de validation à la liste des erreurs détaillées
        for validation_error in validation_errors:
            errors_list.append(TransactionError(
                line_number=0,  # Les erreurs de validation ne sont pas liées à une ligne spécifique
                date=None,
                quantite=None,
                nom=None,
                error_message=f"Erreur de validation: {validation_error}"
            ))
        
        # Récupérer les colonnes mappées
        date_col = None
        quantite_col = None
        nom_col = None
        
        for file_col, db_col in column_mapping.items():
            if db_col == 'date':
                date_col = file_col
            elif db_col == 'quantite':
                quantite_col = file_col
            elif db_col == 'nom':
                nom_col = file_col
        
        if not all([date_col, quantite_col, nom_col]):
            raise HTTPException(status_code=400, detail="Mapping incomplet: date, quantite et nom requis")
        
        # Convertir dates pour comparaison et tri
        df_validated['_date_parsed'] = pd.to_datetime(df_validated[date_col])
        
        # Sauvegarder l'index original pour les numéros de ligne (avant tri)
        # L'index correspond à la position dans le DataFrame original (après validation)
        df_validated['_original_index'] = df_validated.index
        
        # Trier par date avant insertion (pour calcul correct du solde)
        df_validated = df_validated.sort_values('_date_parsed')
        
        period_start = None
        period_end = None
        
        # Récupérer le solde actuel le plus récent en BDD (ou 0 si aucune transaction)
        last_transaction = db.query(Transaction).order_by(Transaction.date.desc(), Transaction.id.desc()).first()
        current_solde = last_transaction.solde if last_transaction else 0.0
        
        # Liste des transactions à insérer (pour calculer le solde en une fois)
        transactions_to_insert = []
        
        for idx, row in df_validated.iterrows():
            try:
                # Numéro de ligne dans le fichier original
                # Utiliser l'index original + 1 (car 0-based → 1-based)
                # On ajoute 1 pour compenser l'en-tête potentiel (mais la détection d'en-tête peut varier)
                original_idx = int(row.get('_original_index', idx))
                line_number = original_idx + 1  # +1 car 0-based → 1-based
                
                # Convertir date pour BDD (YYYY-MM-DD)
                if pd.isna(row['_date_parsed']):
                    errors_count += 1
                    errors_list.append(TransactionError(
                        line_number=line_number,
                        date=None,
                        quantite=float(row[quantite_col]) if pd.notna(row[quantite_col]) else None,
                        nom=str(row[nom_col]).strip() if pd.notna(row[nom_col]) else None,
                        error_message="Date invalide ou manquante"
                    ))
                    continue
                
                date_value = row['_date_parsed'].date()
                
                # Vérifier que la quantité est valide
                try:
                    quantite_value = float(row[quantite_col]) if pd.notna(row[quantite_col]) else None
                    if quantite_value is None:
                        raise ValueError("Quantité manquante ou invalide")
                except (ValueError, TypeError) as e:
                    errors_count += 1
                    errors_list.append(TransactionError(
                        line_number=line_number,
                        date=date_value.strftime('%d/%m/%Y'),
                        quantite=None,
                        nom=None,
                        error_message=f"Quantité invalide: {str(e)}"
                    ))
                    continue
                
                # Vérifier que le nom n'est pas vide
                nom_original = str(row[nom_col]).strip() if pd.notna(row[nom_col]) else ''
                nom_value = nom_original
                is_nom_generated = False
                
                # Si le nom est vide, vérifier d'abord les doublons sur (Date + Quantité) uniquement
                # car le nom généré changera à chaque import
                if not nom_value:
                    # Vérifier doublon sur (Date + Quantité) uniquement pour les transactions sans nom
                    existing_no_nom = db.query(Transaction).filter(
                        Transaction.date == date_value,
                        Transaction.quantite == quantite_value
                    ).first()
                    
                    if existing_no_nom:
                        # C'est un doublon, utiliser le nom existant pour l'affichage
                        duplicates_count += 1
                        duplicates_list.append(DuplicateTransaction(
                            date=date_value.strftime('%d/%m/%Y'),
                            quantite=quantite_value,
                            nom=existing_no_nom.nom,  # Utiliser le nom existant (peut être modifié)
                            existing_id=existing_no_nom.id
                        ))
                        continue
                    
                    # Pas de doublon, générer automatiquement un nom "nom_a_justifier_N"
                    existing_justify_count = db.query(Transaction).filter(
                        Transaction.nom.like('nom_a_justifier_%')
                    ).count()
                    nom_value = f"nom_a_justifier_{existing_justify_count + 1}"
                    is_nom_generated = True
                
                # Vérifier doublon (Date + Quantité + nom) pour les transactions avec nom
                if not is_nom_generated:
                    existing = db.query(Transaction).filter(
                        Transaction.date == date_value,
                        Transaction.quantite == quantite_value,
                        Transaction.nom == nom_value
                    ).first()
                    
                    if existing:
                        duplicates_count += 1
                        duplicates_list.append(DuplicateTransaction(
                            date=date_value.strftime('%d/%m/%Y'),
                            quantite=quantite_value,
                            nom=nom_value,
                            existing_id=existing.id
                        ))
                        continue
                
                # Calculer le solde : solde = solde précédent + quantité
                current_solde = current_solde + quantite_value
                
                # Créer la transaction avec solde calculé
                transaction = Transaction(
                    date=date_value,
                    quantite=quantite_value,
                    nom=nom_value,  # Utiliser la valeur déjà vérifiée (non vide)
                    solde=current_solde,  # Solde calculé automatiquement
                    source_file=filename
                )
                transactions_to_insert.append(transaction)
                imported_count += 1
                
                # Mettre à jour période
                if period_start is None or date_value < period_start:
                    period_start = date_value
                if period_end is None or date_value > period_end:
                    period_end = date_value
                    
            except Exception as e:
                errors_count += 1
                # Essayer d'extraire les informations de la ligne pour l'erreur
                try:
                    date_str = None
                    if pd.notna(row.get('_date_parsed')):
                        date_str = row['_date_parsed'].date().strftime('%d/%m/%Y')
                    elif date_col and pd.notna(row.get(date_col)):
                        date_str = str(row[date_col])
                    
                    quantite_val = None
                    if quantite_col and pd.notna(row.get(quantite_col)):
                        try:
                            quantite_val = float(row[quantite_col])
                        except:
                            pass
                    
                    nom_val = None
                    if nom_col and pd.notna(row.get(nom_col)):
                        nom_val = str(row[nom_col]).strip()
                except:
                    pass
                
                errors_list.append(TransactionError(
                    line_number=int(idx) + 1,
                    date=date_str,
                    quantite=quantite_val,
                    nom=nom_val,
                    error_message=f"Erreur lors du traitement: {str(e)}"
                ))
                continue
        
        # Insérer toutes les transactions en une fois
        for transaction in transactions_to_insert:
            db.add(transaction)
        db.flush()  # Flush pour obtenir les IDs sans commit
        
        # Recalculer tous les soldes après insertion
        # Si on a inséré des transactions, on doit recalculer depuis la date minimale
        # pour gérer le cas où des transactions sont insérées à des dates antérieures
        if transactions_to_insert:
            from backend.api.utils.balance_utils import recalculate_all_balances
            # Trouver la date minimale des transactions insérées
            min_inserted_date = min(t.date for t in transactions_to_insert)
            # Recalculer tous les soldes depuis le début pour garantir la cohérence
            # (plus simple et plus sûr que de recalculer depuis une date spécifique)
            recalculate_all_balances(db)
            
            # Enrichir automatiquement toutes les transactions insérées
            # Charger les mappings une seule fois pour optimiser
            from backend.database.models import Mapping
            from backend.api.services.amortization_service import recalculate_transaction_amortization
            mappings = db.query(Mapping).all()
            for transaction in transactions_to_insert:
                # Enrichir la transaction (elle a déjà un ID après flush)
                enrich_transaction(transaction, db, mappings)
                
                # Recalculer les amortissements après enrichissement
                # (gestion silencieuse des erreurs pour ne pas bloquer l'import)
                try:
                    recalculate_transaction_amortization(db, transaction.id)
                except Exception as e:
                    # Log l'erreur mais ne bloque pas l'import
                    import traceback
                    error_details = traceback.format_exc()
                    print(f"⚠️ [import_file] Erreur lors du recalcul des amortissements pour transaction {transaction.id}: {error_details}")
        
        db.commit()
        
        # Créer ou mettre à jour l'enregistrement FileImport
        if existing_import:
            # Mettre à jour l'enregistrement existant
            existing_import.imported_at = datetime.utcnow()
            existing_import.imported_count = imported_count
            existing_import.duplicates_count = duplicates_count
            existing_import.errors_count = errors_count
            existing_import.period_start = period_start
            existing_import.period_end = period_end
            db.commit()
        else:
            # Créer un nouvel enregistrement
            file_import = FileImport(
                filename=filename,
                imported_count=imported_count,
                duplicates_count=duplicates_count,
                errors_count=errors_count,
                period_start=period_start,
                period_end=period_end
            )
            db.add(file_import)
            db.commit()
        
        message = f"Import terminé: {imported_count} transactions importées, {duplicates_count} doublons détectés"
        if warning_message:
            message = f"{warning_message} {message}"
        
        # Invalider les comptes de résultat pour toutes les années des transactions importées
        if period_start and period_end:
            try:
                from backend.api.services.compte_resultat_service import invalidate_compte_resultat_for_date_range
                invalidate_compte_resultat_for_date_range(db, period_start, period_end)
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"⚠️ [import_file] Erreur lors de l'invalidation des comptes de résultat: {error_details}")
        
        return FileImportResponse(
            filename=filename,
            imported_count=imported_count,
            duplicates_count=duplicates_count,
            errors_count=errors_count,
            duplicates=duplicates_list[:50],  # Limiter à 50 doublons pour la réponse
            errors=errors_list[:100],  # Limiter à 100 erreurs pour la réponse
            period_start=period_start.strftime('%d/%m/%Y') if period_start else None,
            period_end=period_end.strftime('%d/%m/%Y') if period_end else None,
            message=message
        )
        
    except HTTPException:
        raise
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Format de mapping invalide (JSON requis)")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'import: {str(e)}")

