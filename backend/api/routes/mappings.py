"""
API routes for mappings.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import distinct, desc, asc, func, or_
from typing import List, Optional, Dict
import pandas as pd
import io
import json
import logging
from pathlib import Path
from datetime import datetime

from backend.database import get_db
from backend.database.models import Mapping, Transaction, EnrichedTransaction, MappingImport, AllowedMapping
from backend.api.models import (
    MappingCreate,
    MappingUpdate,
    MappingResponse,
    MappingListResponse,
    MappingPreviewResponse,
    MappingImportResponse,
    MappingImportHistory,
    ColumnMapping,
    MappingError,
    DuplicateMapping,
    AllowedMappingResponse,
    AllowedMappingListResponse
)
from backend.api.services.enrichment_service import enrich_transaction, transaction_matches_mapping_name
from backend.api.services.mapping_obligatoire_service import (
    get_allowed_level1_values,
    get_allowed_level2_values,
    get_all_allowed_level2_values,
    get_allowed_level3_values,
    get_allowed_level2_for_level3,
    get_allowed_level1_for_level2,
    get_allowed_level1_for_level2_and_level3,
    get_allowed_level3_for_level2,
    validate_mapping,
    validate_level3_value,
    get_all_allowed_mappings,
    create_allowed_mapping,
    delete_allowed_mapping,
    reset_allowed_mappings
)

router = APIRouter()
logger = logging.getLogger(__name__)


def detect_mapping_columns(df: pd.DataFrame) -> Dict[str, str]:
    """
    Détecte automatiquement les colonnes d'un fichier Excel de mappings.
    
    Cherche les colonnes correspondant à : nom, level_1, level_2, level_3
    
    Args:
        df: DataFrame pandas du fichier Excel
    
    Returns:
        Dictionnaire {nom_colonne_fichier: nom_colonne_bdd}
    """
    mapping = {}
    df_columns_lower = {col.lower().strip(): col for col in df.columns}
    
    # Détection nom (obligatoire)
    nom_variants = ['nom', 'name', 'libellé', 'libelle', 'description', 'desc', 'label', 'transaction', 'transac']
    for variant in nom_variants:
        if variant in df_columns_lower:
            mapping[df_columns_lower[variant]] = 'nom'
            break
    
    # Détection level_1 (obligatoire)
    level_1_variants = ['level_1', 'level1', 'level 1', 'l1', 'catégorie', 'categorie', 'category', 'cat', 'niveau 1', 'niveau1']
    for variant in level_1_variants:
        if variant in df_columns_lower:
            mapping[df_columns_lower[variant]] = 'level_1'
            break
    
    # Détection level_2 (obligatoire)
    level_2_variants = ['level_2', 'level2', 'level 2', 'l2', 'sous-catégorie', 'sous-categorie', 'subcategory', 'sub-cat', 'niveau 2', 'niveau2']
    for variant in level_2_variants:
        if variant in df_columns_lower:
            mapping[df_columns_lower[variant]] = 'level_2'
            break
    
    # Détection level_3 (optionnel)
    level_3_variants = ['level_3', 'level3', 'level 3', 'l3', 'détail', 'detail', 'niveau 3', 'niveau3']
    for variant in level_3_variants:
        if variant in df_columns_lower:
            mapping[df_columns_lower[variant]] = 'level_3'
            break
    
    # Si pas de détection automatique, essayer de deviner par position (si 3-4 colonnes)
    if len(df.columns) >= 3:
        if 'nom' not in mapping.values() and len(df.columns) >= 1:
            # Première colonne = nom (par défaut)
            mapping[df.columns[0]] = 'nom'
        if 'level_1' not in mapping.values() and len(df.columns) >= 2:
            # Deuxième colonne = level_1
            mapping[df.columns[1]] = 'level_1'
        if 'level_2' not in mapping.values() and len(df.columns) >= 3:
            # Troisième colonne = level_2
            mapping[df.columns[2]] = 'level_2'
        if 'level_3' not in mapping.values() and len(df.columns) >= 4:
            # Quatrième colonne = level_3
            mapping[df.columns[3]] = 'level_3'
    
    return mapping


@router.post("/mappings/preview", response_model=MappingPreviewResponse)
async def preview_mapping_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Prévisualise un fichier Excel de mappings et détecte le mapping des colonnes.
    
    - **file**: Fichier Excel (.xlsx ou .xls) à analyser
    - Retourne: Preview, mapping proposé, statistiques
    """
    # Vérifier l'extension du fichier
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant")
    
    filename_lower = file.filename.lower()
    if not (filename_lower.endswith('.xlsx') or filename_lower.endswith('.xls')):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être un fichier Excel (.xlsx ou .xls)"
        )
    
    # Lire le fichier
    file_content = await file.read()
    
    try:
        # Lire Excel avec pandas
        df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl' if filename_lower.endswith('.xlsx') else None)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Le fichier Excel est vide")
        
        # Détecter mapping colonnes
        detected_mapping = detect_mapping_columns(df)
        
        # Validation basique
        validation_errors = []
        required_columns = ['nom', 'level_1', 'level_2']
        mapped_db_columns = list(detected_mapping.values())
        
        for required_col in required_columns:
            if required_col not in mapped_db_columns:
                validation_errors.append(
                    f"Colonne '{required_col}' non détectée. Veuillez la mapper manuellement."
                )
        
        # Créer mapping formaté pour la réponse
        column_mapping = [
            ColumnMapping(file_column=file_col, db_column=db_col)
            for file_col, db_col in detected_mapping.items()
        ]
        
        # Preview des premières lignes (max 10)
        preview_rows = []
        num_preview = min(10, len(df))
        
        for idx in range(num_preview):
            row_dict = {}
            for col in df.columns:
                value = df.iloc[idx][col]
                # Convertir les valeurs en string pour l'affichage
                if pd.isna(value):
                    row_dict[col] = None
                elif isinstance(value, (int, float)):
                    row_dict[col] = str(value)
                else:
                    row_dict[col] = str(value)
            preview_rows.append(row_dict)
        
        # Statistiques
        stats = {
            "total_rows": len(df),
            "detected_columns": len(detected_mapping),
            "required_columns_detected": len([c for c in required_columns if c in mapped_db_columns])
        }
        
        return MappingPreviewResponse(
            filename=file.filename,
            total_rows=len(df),
            column_mapping=column_mapping,
            preview=preview_rows,
            validation_errors=validation_errors,
            stats=stats
        )
        
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="Le fichier Excel est vide ou invalide")
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Erreur lors de la lecture du fichier Excel: {str(e)}"
        )


@router.post("/mappings/import", response_model=MappingImportResponse)
async def import_mapping_file(
    file: UploadFile = File(...),
    mapping: str = Form(..., description="Mapping JSON string"),
    db: Session = Depends(get_db)
):
    """
    Importe un fichier Excel de mappings dans la base de données.
    
    - **file**: Fichier Excel (.xlsx ou .xls) à importer
    - **mapping**: Mapping des colonnes (JSON string)
    - Retourne: Statistiques d'import (imported, duplicates, errors)
    """
    try:
        # Parser le mapping
        mapping_data = json.loads(mapping)
        column_mapping = {item['file_column']: item['db_column'] for item in mapping_data}
        
        # Vérifier si fichier déjà chargé (avertissement mais on continue)
        filename = file.filename or "unknown.xlsx"
        existing_import = db.query(MappingImport).filter(MappingImport.filename == filename).first()
        warning_message = None
        
        if existing_import:
            warning_message = f"⚠️ Le fichier {filename} a déjà été chargé le {existing_import.imported_at.strftime('%d/%m/%Y %H:%M')}. Le traitement continue, les doublons seront détectés."
            # Mettre à jour l'enregistrement existant au lieu d'en créer un nouveau
            mapping_import = existing_import
        else:
            # Créer un nouvel enregistrement
            mapping_import = MappingImport(
                filename=filename,
                imported_count=0,
                duplicates_count=0,
                errors_count=0
            )
            db.add(mapping_import)
        
        # Lire le fichier
        file_content = await file.read()
        
        # Sauvegarder le fichier dans data/input/trades/ (archive)
        trades_dir = Path(__file__).parent.parent.parent / "data" / "input" / "trades"
        trades_dir.mkdir(parents=True, exist_ok=True)
        file_path = trades_dir / filename
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Lire Excel
        filename_lower = filename.lower()
        df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl' if filename_lower.endswith('.xlsx') else None)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Le fichier Excel est vide")
        
        # Récupérer les colonnes mappées
        nom_col = None
        level_1_col = None
        level_2_col = None
        level_3_col = None
        
        for file_col, db_col in column_mapping.items():
            if db_col == 'nom':
                nom_col = file_col
            elif db_col == 'level_1':
                level_1_col = file_col
            elif db_col == 'level_2':
                level_2_col = file_col
            elif db_col == 'level_3':
                level_3_col = file_col
        
        # Vérifier que les colonnes obligatoires sont présentes
        if not nom_col or not level_1_col or not level_2_col:
            raise HTTPException(
                status_code=400,
                detail="Mapping incomplet: nom, level_1 et level_2 requis"
            )
        
        # Valider et importer
        imported_count = 0
        duplicates_count = 0
        duplicates_list = []
        errors_count = 0
        errors_list = []
        
        # Liste en mémoire des noms déjà traités dans cette session (pour détecter doublons dans le fichier)
        processed_noms_in_session = set()
        
        for idx, row in df.iterrows():
            try:
                line_number = idx + 2  # +2 car 0-based + en-tête
                
                # Récupérer les valeurs
                nom_value = str(row[nom_col]).strip() if pd.notna(row[nom_col]) else ''
                level_1_value = str(row[level_1_col]).strip() if pd.notna(row[level_1_col]) else ''
                level_2_value = str(row[level_2_col]).strip() if pd.notna(row[level_2_col]) else ''
                level_3_value = str(row[level_3_col]).strip() if pd.notna(row[level_3_col]) else '' if level_3_col else None
                
                # Validation
                if not nom_value:
                    errors_count += 1
                    errors_list.append(MappingError(
                        line_number=line_number,
                        nom=None,
                        level_1=level_1_value if level_1_value else None,
                        level_2=level_2_value if level_2_value else None,
                        level_3=level_3_value if level_3_value else None,
                        error_message="Le champ 'nom' est obligatoire et ne peut pas être vide"
                    ))
                    continue
                
                if not level_1_value:
                    errors_count += 1
                    errors_list.append(MappingError(
                        line_number=line_number,
                        nom=nom_value,
                        level_1=None,
                        level_2=level_2_value if level_2_value else None,
                        level_3=level_3_value if level_3_value else None,
                        error_message="Le champ 'level_1' est obligatoire et ne peut pas être vide"
                    ))
                    continue
                
                if not level_2_value:
                    errors_count += 1
                    errors_list.append(MappingError(
                        line_number=line_number,
                        nom=nom_value,
                        level_1=level_1_value,
                        level_2=None,
                        level_3=level_3_value if level_3_value else None,
                        error_message="Le champ 'level_2' est obligatoire et ne peut pas être vide"
                    ))
                    continue
                
                # Validation contre allowed_mappings (Step 5.3)
                # Valider que level_3 est dans la liste fixe si fourni
                if level_3_value and not validate_level3_value(level_3_value):
                    errors_count += 1
                    errors_list.append(MappingError(
                        line_number=line_number,
                        nom=nom_value,
                        level_1=level_1_value,
                        level_2=level_2_value,
                        level_3=level_3_value,
                        error_message="erreur - mapping inconnu"
                    ))
                    # Logger l'erreur
                    logger.warning(f"Ligne {line_number}: erreur - mapping inconnu (level_3 invalide: '{level_3_value}')")
                    continue
                
                # Valider que la combinaison (level_1, level_2, level_3) existe dans allowed_mappings
                if not validate_mapping(db, level_1_value, level_2_value, level_3_value if level_3_value else None):
                    errors_count += 1
                    errors_list.append(MappingError(
                        line_number=line_number,
                        nom=nom_value,
                        level_1=level_1_value,
                        level_2=level_2_value,
                        level_3=level_3_value if level_3_value else None,
                        error_message="erreur - mapping inconnu"
                    ))
                    # Logger l'erreur
                    logger.warning(f"Ligne {line_number}: erreur - mapping inconnu (combinaison non autorisée: level_1='{level_1_value}', level_2='{level_2_value}', level_3='{level_3_value}')")
                    continue
                
                # Vérifier doublon dans le fichier (déjà traité dans cette session)
                if nom_value in processed_noms_in_session:
                    duplicates_count += 1
                    duplicates_list.append(DuplicateMapping(
                        nom=nom_value,
                        existing_id=None  # Pas encore en BDD, juste dans cette session
                    ))
                    continue
                
                # Vérifier doublon dans la base de données
                existing = db.query(Mapping).filter(Mapping.nom == nom_value).first()
                
                if existing:
                    duplicates_count += 1
                    duplicates_list.append(DuplicateMapping(
                        nom=nom_value,
                        existing_id=existing.id
                    ))
                    continue
                
                # Ajouter à la liste des noms traités dans cette session
                processed_noms_in_session.add(nom_value)
                
                # Créer le mapping
                db_mapping = Mapping(
                    nom=nom_value,
                    level_1=level_1_value,
                    level_2=level_2_value,
                    level_3=level_3_value if level_3_value else None,
                    is_prefix_match=True,  # Par défaut
                    priority=0  # Par défaut
                )
                
                db.add(db_mapping)
                imported_count += 1
                
                # Flush périodique pour que les objets soient visibles dans les requêtes suivantes
                # et éviter les erreurs UNIQUE constraint au commit final
                if imported_count % 50 == 0:
                    db.flush()
                
            except Exception as e:
                errors_count += 1
                errors_list.append(MappingError(
                    line_number=idx + 2,
                    nom=None,
                    level_1=None,
                    level_2=None,
                    level_3=None,
                    error_message=f"Erreur lors du traitement: {str(e)}"
                ))
                continue
        
        # Mettre à jour l'enregistrement MappingImport
        mapping_import.imported_count = imported_count
        mapping_import.duplicates_count = duplicates_count
        mapping_import.errors_count = errors_count
        mapping_import.imported_at = datetime.utcnow()
        
        db.commit()
        
        # Message de réponse
        message = f"Import terminé: {imported_count} mapping(s) importé(s)"
        if duplicates_count > 0:
            message += f", {duplicates_count} doublon(s) ignoré(s)"
        if errors_count > 0:
            message += f", {errors_count} erreur(s)"
        if warning_message:
            message = f"{warning_message} {message}"
        
        return MappingImportResponse(
            filename=filename,
            imported_count=imported_count,
            duplicates_count=duplicates_count,
            errors_count=errors_count,
            duplicates=duplicates_list,
            errors=errors_list[:100],  # Limiter à 100 erreurs pour ne pas surcharger
            message=message
        )
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Format JSON invalide pour le mapping")
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="Le fichier Excel est vide ou invalide")
    except Exception as e:
        db.rollback()
        # Gérer spécifiquement les erreurs SQLite IntegrityError
        error_str = str(e)
        if "UNIQUE constraint failed" in error_str or "IntegrityError" in error_str:
            # Extraire le nom du mapping en doublon si possible
            import re
            match = re.search(r"'([^']+)'", error_str)
            if match:
                nom_duplique = match.group(1)
                detail = f"Un mapping avec le nom '{nom_duplique}' existe déjà dans la base de données. Les doublons ont été détectés et ignorés, mais cette erreur indique qu'un doublon n'a pas été correctement détecté. Veuillez vérifier votre fichier."
            else:
                detail = f"Erreur de contrainte unique: un mapping avec ce nom existe déjà dans la base de données. {error_str}"
        else:
            detail = f"Erreur lors de l'import: {error_str}"
        raise HTTPException(
            status_code=400,
            detail=detail
        )


@router.get("/mappings/imports", response_model=List[MappingImportHistory])
async def get_mapping_imports_history(
    db: Session = Depends(get_db)
):
    """
    Récupère l'historique des imports de fichiers de mappings.
    
    Returns:
        Liste des imports de mappings triés par date (plus récent en premier)
    """
    imports = db.query(MappingImport).order_by(MappingImport.imported_at.desc()).all()
    
    return [MappingImportHistory.model_validate(imp) for imp in imports]


@router.delete("/mappings/imports", status_code=204)
async def delete_all_mapping_imports(
    db: Session = Depends(get_db)
):
    """
    Supprime tous les imports de mappings de l'historique.
    
    ⚠️ ATTENTION : Cette action est irréversible et supprime définitivement tous les historiques d'imports de mappings.
    """
    db.query(MappingImport).delete()
    db.commit()
    
    return None


@router.delete("/mappings/imports/{import_id}", status_code=204)
async def delete_mapping_import(
    import_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprime un import de mapping de l'historique.
    
    Args:
        import_id: ID de l'import à supprimer
        db: Session de base de données
    
    Raises:
        HTTPException: Si l'import n'existe pas
    """
    mapping_import = db.query(MappingImport).filter(MappingImport.id == import_id).first()
    if not mapping_import:
        raise HTTPException(
            status_code=404,
            detail=f"Import de mapping avec ID {import_id} non trouvé"
        )
    
    db.delete(mapping_import)
    db.commit()
    
    return None


@router.get("/mappings/count")
async def get_mappings_count(
    db: Session = Depends(get_db)
):
    """
    Récupère le nombre total de mappings dans la base de données.
    
    Returns:
        Dictionnaire avec le nombre total de mappings
    """
    count = db.query(Mapping).count()
    
    return {"count": count}


@router.get("/mappings", response_model=MappingListResponse)
async def get_mappings(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'éléments à retourner"),
    search: Optional[str] = Query(None, description="Recherche dans le nom"),
    sort_by: Optional[str] = Query(None, description="Colonne de tri (id, nom, level_1, level_2, level_3)"),
    sort_direction: Optional[str] = Query("asc", description="Direction du tri (asc, desc)"),
    filter_nom: Optional[str] = Query(None, description="Filtre sur le nom (contient, insensible à la casse)"),
    filter_level_1: Optional[str] = Query(None, description="Filtre sur level_1 (contient, insensible à la casse)"),
    filter_level_2: Optional[str] = Query(None, description="Filtre sur level_2 (contient, insensible à la casse)"),
    filter_level_3: Optional[str] = Query(None, description="Filtre sur level_3 (contient, insensible à la casse)"),
    db: Session = Depends(get_db)
):
    """
    Récupérer la liste des mappings.
    
    Args:
        skip: Nombre d'éléments à sauter (pagination)
        limit: Nombre d'éléments à retourner
        search: Terme de recherche dans le nom
        sort_by: Colonne de tri (id, nom, level_1, level_2, level_3)
        sort_direction: Direction du tri (asc, desc)
        filter_nom: Filtrer par nom (contient, insensible à la casse)
        filter_level_1: Filtrer par level_1 (contient, insensible à la casse)
        filter_level_2: Filtrer par level_2 (contient, insensible à la casse)
        filter_level_3: Filtrer par level_3 (contient, insensible à la casse)
        db: Session de base de données
    
    Returns:
        Liste des mappings avec pagination
    """
    query = db.query(Mapping)
    
    # Filtre de recherche (legacy, pour compatibilité)
    if search:
        query = query.filter(Mapping.nom.contains(search))
    
    # Filtres texte (contient, insensible à la casse)
    if filter_nom:
        query = query.filter(func.lower(Mapping.nom).contains(func.lower(filter_nom)))
    
    if filter_level_1:
        filter_normalized = filter_level_1.lower().strip()
        # Détecter "unassigned" ou préfixe de "unassigned" (ex: "un", "una", "unas")
        if filter_normalized == "unassigned":
            query = query.filter(Mapping.level_1.is_(None))
        elif "unassigned".startswith(filter_normalized):
            # Si le filtre est un préfixe de "unassigned", inclure les NULL ET les valeurs qui contiennent le filtre
            query = query.filter(
                or_(
                    Mapping.level_1.is_(None),
                    func.lower(Mapping.level_1).contains(func.lower(filter_level_1))
                )
            )
        else:
            query = query.filter(func.lower(Mapping.level_1).contains(func.lower(filter_level_1)))
    
    if filter_level_2:
        filter_normalized = filter_level_2.lower().strip()
        # Détecter "unassigned" ou préfixe de "unassigned" (ex: "un", "una", "unas")
        if filter_normalized == "unassigned":
            query = query.filter(Mapping.level_2.is_(None))
        elif "unassigned".startswith(filter_normalized):
            # Si le filtre est un préfixe de "unassigned", inclure les NULL ET les valeurs qui contiennent le filtre
            query = query.filter(
                or_(
                    Mapping.level_2.is_(None),
                    func.lower(Mapping.level_2).contains(func.lower(filter_level_2))
                )
            )
        else:
            query = query.filter(func.lower(Mapping.level_2).contains(func.lower(filter_level_2)))
    
    if filter_level_3:
        filter_normalized = filter_level_3.lower().strip()
        # Détecter "unassigned" ou préfixe de "unassigned" (ex: "un", "una", "unas")
        if filter_normalized == "unassigned":
            query = query.filter(Mapping.level_3.is_(None))
        elif "unassigned".startswith(filter_normalized):
            # Si le filtre est un préfixe de "unassigned", inclure les NULL ET les valeurs qui contiennent le filtre
            query = query.filter(
                or_(
                    Mapping.level_3.is_(None),
                    func.lower(Mapping.level_3).contains(func.lower(filter_level_3))
                )
            )
        else:
            query = query.filter(func.lower(Mapping.level_3).contains(func.lower(filter_level_3)))
    
    # Comptage total (avant tri)
    total = query.count()
    
    # Tri
    if sort_by:
        # Normaliser la direction
        sort_dir = sort_direction.lower() if sort_direction else "asc"
        if sort_dir not in ["asc", "desc"]:
            sort_dir = "asc"
        
        # Déterminer la colonne de tri
        if sort_by == "id":
            order_col = Mapping.id
        elif sort_by == "nom":
            order_col = Mapping.nom
        elif sort_by == "level_1":
            order_col = Mapping.level_1
        elif sort_by == "level_2":
            order_col = Mapping.level_2
        elif sort_by == "level_3":
            order_col = Mapping.level_3
        else:
            # Par défaut, trier par nom asc
            order_col = Mapping.nom
            sort_dir = "asc"
        
        # Appliquer le tri
        if sort_dir == "asc":
            query = query.order_by(asc(order_col))
        else:
            query = query.order_by(desc(order_col))
    else:
        # Par défaut, trier par nom asc
        query = query.order_by(asc(Mapping.nom))
    
    # Pagination
    mappings = query.offset(skip).limit(limit).all()
    
    return MappingListResponse(
        mappings=[MappingResponse.model_validate(m) for m in mappings],
        total=total
    )


@router.get("/mappings/unique-values")
async def get_mapping_unique_values(
    column: str = Query(..., description="Nom de la colonne (nom, level_1, level_2, level_3)"),
    db: Session = Depends(get_db)
):
    """
    Récupérer les valeurs uniques d'une colonne pour les filtres.
    
    - **column**: Nom de la colonne (nom, level_1, level_2, level_3)
    
    Returns:
        Liste des valeurs uniques (non null, triées)
    """
    query = db.query(Mapping)
    
    # Récupérer les valeurs uniques selon la colonne
    if column == "nom":
        values = query.with_entities(Mapping.nom).distinct().filter(Mapping.nom.isnot(None)).order_by(Mapping.nom).all()
        unique_values = [v[0] for v in values if v[0]]
    elif column == "level_1":
        values = query.with_entities(Mapping.level_1).distinct().filter(Mapping.level_1.isnot(None)).order_by(Mapping.level_1).all()
        unique_values = [v[0] for v in values if v[0]]
    elif column == "level_2":
        values = query.with_entities(Mapping.level_2).distinct().filter(Mapping.level_2.isnot(None)).order_by(Mapping.level_2).all()
        unique_values = [v[0] for v in values if v[0]]
    elif column == "level_3":
        values = query.with_entities(Mapping.level_3).distinct().filter(Mapping.level_3.isnot(None)).order_by(Mapping.level_3).all()
        unique_values = [v[0] for v in values if v[0]]
    else:
        raise HTTPException(status_code=400, detail=f"Colonne '{column}' non supportée. Colonnes supportées: nom, level_1, level_2, level_3")
    
    return {"column": column, "values": unique_values}


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
    Modifier un mapping existant et re-enrichir les transactions qui l'utilisaient.
    
    Lors de la modification d'un mapping :
    1. Trouve toutes les transactions dont le nom correspond au mapping (avant modification)
    2. Met à jour le mapping
    3. Re-enrichit ces transactions (elles utiliseront le nouveau mapping si elles correspondent toujours)
    
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
    
    # Sauvegarder le nom du mapping AVANT la mise à jour
    # pour trouver toutes les transactions qui correspondent à ce nom
    old_mapping_nom = mapping.nom
    
    # Trouver TOUTES les transactions dont le nom correspond au mapping
    # (peu importe leurs level_1/2/3 actuels)
    # Cela permet de re-enrichir toutes les transactions avec le même nom
    # même si elles n'avaient pas encore été enrichies ou avaient des valeurs différentes
    all_transactions = db.query(Transaction).all()
    
    transactions_to_re_enrich = []
    for transaction in all_transactions:
        # Utiliser la fonction utilitaire pour vérifier si la transaction correspond au mapping
        if transaction_matches_mapping_name(transaction.nom, old_mapping_nom):
            transactions_to_re_enrich.append(transaction)
    
    # Mettre à jour les champs
    update_data = mapping_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(mapping, field, value)
    
    db.commit()
    db.refresh(mapping)
    
    # Re-enrichir les transactions (elles utiliseront le nouveau mapping si elles correspondent toujours)
    for transaction in transactions_to_re_enrich:
        enrich_transaction(transaction, db)
    
    db.commit()
    
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


# Allowed mappings endpoints (doivent être définis AVANT /mappings/{mapping_id})

@router.get("/mappings/allowed-level1")
async def get_allowed_level1(
    db: Session = Depends(get_db)
):
    """
    Récupérer toutes les valeurs level_1 autorisées.
    
    Returns:
        Liste des valeurs level_1 uniques, triées
    """
    values = get_allowed_level1_values(db)
    return {"level_1": values}


@router.get("/mappings/allowed-level2")
async def get_allowed_level2(
    level_1: Optional[str] = Query(None, description="Valeur de level_1 (optionnel, si non fourni retourne tous les level_2)"),
    db: Session = Depends(get_db)
):
    """
    Récupérer les valeurs level_2 autorisées.
    
    Si level_1 est fourni, retourne les level_2 pour ce level_1.
    Si level_1 n'est pas fourni, retourne tous les level_2 autorisés (pour scénario 2).
    
    Args:
        level_1: Valeur de level_1 (optionnel)
        db: Session de base de données
    
    Returns:
        Liste des valeurs level_2 uniques, triées
    """
    if level_1:
        values = get_allowed_level2_values(db, level_1)
    else:
        values = get_all_allowed_level2_values(db)
    return {"level_2": values}


@router.get("/mappings/allowed-level3")
async def get_allowed_level3(
    level_1: str = Query(..., description="Valeur de level_1"),
    level_2: str = Query(..., description="Valeur de level_2"),
    db: Session = Depends(get_db)
):
    """
    Récupérer les valeurs level_3 autorisées pour un couple (level_1, level_2).
    
    Args:
        level_1: Valeur de level_1
        level_2: Valeur de level_2
        db: Session de base de données
    
    Returns:
        Liste des valeurs level_3 uniques pour ce couple, triées
    """
    values = get_allowed_level3_values(db, level_1, level_2)
    return {"level_3": values}


@router.get("/mappings/allowed-level2-for-level3")
async def get_allowed_level2_for_level3_endpoint(
    level_3: str = Query(..., description="Valeur de level_3"),
    db: Session = Depends(get_db)
):
    """
    Récupérer les valeurs level_2 autorisées pour un level_3 donné.
    
    Utilisé pour le filtrage bidirectionnel : quand level_3 est sélectionné en premier,
    on peut filtrer les level_2 possibles.
    
    Args:
        level_3: Valeur de level_3
        db: Session de base de données
    
    Returns:
        Liste des valeurs level_2 uniques pour ce level_3, triées
    """
    values = get_allowed_level2_for_level3(db, level_3)
    return {"level_2": values}


@router.get("/mappings/allowed-level1-for-level2")
async def get_allowed_level1_for_level2_endpoint(
    level_2: str = Query(..., description="Valeur de level_2"),
    db: Session = Depends(get_db)
):
    """
    Récupérer les valeurs level_1 autorisées pour un level_2 donné.
    
    Utilisé pour le filtrage bidirectionnel : quand level_2 est sélectionné en premier,
    on peut filtrer les level_1 possibles.
    
    Args:
        level_2: Valeur de level_2
        db: Session de base de données
    
    Returns:
        Liste des valeurs level_1 uniques pour ce level_2, triées
    """
    values = get_allowed_level1_for_level2(db, level_2)
    return {"level_1": values}


@router.get("/mappings/allowed-level1-for-level2-and-level3")
async def get_allowed_level1_for_level2_and_level3_endpoint(
    level_2: str = Query(..., description="Valeur de level_2"),
    level_3: str = Query(..., description="Valeur de level_3"),
    db: Session = Depends(get_db)
):
    """
    Récupérer les valeurs level_1 autorisées pour un couple (level_2, level_3).
    
    Utilisé pour le filtrage bidirectionnel : quand level_3 puis level_2 sont sélectionnés,
    on peut filtrer les level_1 possibles pour validation.
    
    Args:
        level_2: Valeur de level_2
        level_3: Valeur de level_3
        db: Session de base de données
    
    Returns:
        Liste des valeurs level_1 uniques pour ce couple, triées
    """
    values = get_allowed_level1_for_level2_and_level3(db, level_2, level_3)
    return {"level_1": values}


@router.get("/mappings/allowed-level3-for-level2")
async def get_allowed_level3_for_level2_endpoint(
    level_2: str = Query(..., description="Valeur de level_2"),
    db: Session = Depends(get_db)
):
    """
    Récupérer les valeurs level_3 autorisées pour un level_2 donné.
    
    Utilisé pour le filtrage bidirectionnel : quand level_2 est sélectionné en premier,
    on peut trouver le level_3 unique (si unique) pour pré-remplir automatiquement.
    
    Args:
        level_2: Valeur de level_2
        db: Session de base de données
    
    Returns:
        Liste des valeurs level_3 uniques pour ce level_2, triées
    """
    values = get_allowed_level3_for_level2(db, level_2)
    return {"level_3": values}


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



# Endpoints pour la gestion des allowed_mappings (Step 5.8)
# À ajouter à la fin de backend/api/routes/mappings.py

@router.get("/mappings/allowed", response_model=AllowedMappingListResponse)
async def get_allowed_mappings_endpoint(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'éléments à retourner"),
    db: Session = Depends(get_db)
):
    """
    Récupère tous les mappings autorisés avec pagination.
    
    Args:
        skip: Nombre d'éléments à sauter
        limit: Nombre d'éléments à retourner
        db: Session de base de données
    
    Returns:
        Liste des mappings autorisés avec total
    """
    mappings, total = get_all_allowed_mappings(db, skip, limit)
    return AllowedMappingListResponse(
        mappings=[AllowedMappingResponse.model_validate(m) for m in mappings],
        total=total
    )


@router.post("/mappings/allowed", response_model=AllowedMappingResponse, status_code=201)
async def create_allowed_mapping_endpoint(
    level_1: str = Query(..., description="Valeur de level_1"),
    level_2: str = Query(..., description="Valeur de level_2"),
    level_3: Optional[str] = Query(None, description="Valeur de level_3 (optionnel)"),
    db: Session = Depends(get_db)
):
    """
    Crée un nouveau mapping autorisé.
    
    Args:
        level_1: Valeur de level_1
        level_2: Valeur de level_2
        level_3: Valeur de level_3 (optionnel)
        db: Session de base de données
    
    Returns:
        Le mapping créé
    
    Raises:
        HTTPException: Si la combinaison existe déjà ou si level_3 n'est pas valide
    """
    try:
        mapping = create_allowed_mapping(db, level_1, level_2, level_3)
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

