"""
Service de gestion des mappings autorisés (combinaisons level_1, level_2, level_3).

⚠️ Before making changes, read: ../../../docs/workflow/BEST_PRACTICES.md
"""

from sqlalchemy.orm import Session
from sqlalchemy import distinct
from typing import List, Optional
from pathlib import Path
import pandas as pd

from backend.database.models import AllowedMapping, Transaction


# Liste fixe des valeurs level_3 autorisées
ALLOWED_LEVEL_3_VALUES = [
    "Passif",
    "Produits",
    "Emprunt",
    "Charges Déductibles",
    "Actif"
]


def validate_level3_value(level_3: str) -> bool:
    """
    Valide que level_3 est dans la liste fixe autorisée.
    
    Args:
        level_3: Valeur à valider
    
    Returns:
        True si la valeur est autorisée, False sinon
    """
    if level_3 is None:
        return True  # level_3 est nullable
    return level_3 in ALLOWED_LEVEL_3_VALUES


def load_allowed_mappings_from_excel(db: Session, property_id: int, excel_path: Optional[Path] = None) -> int:
    """
    Charge le fichier Excel et insère les combinaisons dans la table allowed_mappings pour une propriété spécifique.
    
    Les combinaisons sont marquées avec is_hardcoded = True (protégées).
    
    Args:
        db: Session de base de données
        property_id: ID de la propriété pour laquelle charger les mappings
        excel_path: Chemin vers le fichier Excel (par défaut: scripts/mappings_obligatoires.xlsx)
    
    Returns:
        Nombre de combinaisons chargées
    
    Raises:
        FileNotFoundError: Si le fichier Excel n'existe pas
        ValueError: Si le fichier Excel est invalide
    """
    if excel_path is None:
        # Chemin par défaut depuis la racine du projet
        project_root = Path(__file__).parent.parent.parent.parent
        excel_path = project_root / "scripts" / "mappings_obligatoires.xlsx"
    
    if not excel_path.exists():
        raise FileNotFoundError(f"Le fichier Excel n'existe pas : {excel_path}")
    
    # Lire le fichier Excel
    try:
        df = pd.read_excel(excel_path, engine='openpyxl')
    except Exception as e:
        raise ValueError(f"Erreur lors de la lecture du fichier Excel : {str(e)}")
    
    # Vérifier les colonnes attendues
    expected_columns = ['Level 1', 'Level 2', 'Level 3']
    if not all(col in df.columns for col in expected_columns):
        raise ValueError(f"Le fichier Excel doit contenir les colonnes : {expected_columns}")
    
    # Compter les combinaisons chargées
    loaded_count = 0
    
    # Parcourir les lignes et insérer les combinaisons
    for idx, row in df.iterrows():
        level_1 = str(row['Level 1']).strip() if pd.notna(row['Level 1']) else None
        level_2 = str(row['Level 2']).strip() if pd.notna(row['Level 2']) else None
        level_3 = str(row['Level 3']).strip() if pd.notna(row['Level 3']) else None
        
        # Validation : level_1 et level_2 sont obligatoires
        if not level_1 or not level_2:
            continue  # Ignorer les lignes invalides
        
        # Validation : level_3 doit être dans la liste fixe (si fourni)
        if level_3 and not validate_level3_value(level_3):
            continue  # Ignorer les lignes avec level_3 invalide
        
        # Vérifier si la combinaison existe déjà pour cette propriété
        query = db.query(AllowedMapping).filter(
            AllowedMapping.property_id == property_id,
            AllowedMapping.level_1 == level_1,
            AllowedMapping.level_2 == level_2
        )
        if level_3:
            query = query.filter(AllowedMapping.level_3 == level_3)
        else:
            query = query.filter(AllowedMapping.level_3.is_(None))
        
        existing = query.first()
        
        if existing:
            # Mettre à jour is_hardcoded si nécessaire
            if not existing.is_hardcoded:
                existing.is_hardcoded = True
                db.flush()
            continue
        
        # Créer la nouvelle combinaison
        try:
            allowed_mapping = AllowedMapping(
                property_id=property_id,
                level_1=level_1,
                level_2=level_2,
                level_3=level_3,
                is_hardcoded=True  # Marquer comme hard codé (protégé)
            )
            db.add(allowed_mapping)
            db.flush()  # Flush pour détecter les erreurs avant le commit final
            loaded_count += 1
        except Exception:
            # Ignorer les doublons (contrainte unique)
            db.rollback()
            continue
    
    db.commit()
    return loaded_count


def get_allowed_level1_values(db: Session, property_id: int) -> List[str]:
    """
    Retourne toutes les valeurs level_1 autorisées (distinct) pour une propriété.
    
    Args:
        db: Session de base de données
        property_id: ID de la propriété
    
    Returns:
        Liste des valeurs level_1 uniques, triées
    """
    values = db.query(distinct(AllowedMapping.level_1)).filter(
        AllowedMapping.property_id == property_id,
        AllowedMapping.level_1.isnot(None)
    ).order_by(AllowedMapping.level_1).all()
    return [v[0] for v in values if v[0]]


def get_allowed_level2_values(db: Session, level_1: str, property_id: int) -> List[str]:
    """
    Retourne les valeurs level_2 autorisées pour un level_1 donné (distinct) pour une propriété.
    
    Args:
        db: Session de base de données
        level_1: Valeur de level_1
        property_id: ID de la propriété
    
    Returns:
        Liste des valeurs level_2 uniques pour ce level_1, triées
    """
    values = db.query(distinct(AllowedMapping.level_2)).filter(
        AllowedMapping.property_id == property_id,
        AllowedMapping.level_1 == level_1,
        AllowedMapping.level_2.isnot(None)
    ).order_by(AllowedMapping.level_2).all()
    return [v[0] for v in values if v[0]]


def get_all_allowed_level2_values(db: Session, property_id: int) -> List[str]:
    """
    Retourne toutes les valeurs level_2 autorisées (distinct, sans filtre level_1) pour une propriété.
    
    Utilisé pour le scénario 2 : quand on peut sélectionner level_2 avant level_1.
    
    Args:
        db: Session de base de données
        property_id: ID de la propriété
    
    Returns:
        Liste de toutes les valeurs level_2 uniques, triées
    """
    values = db.query(distinct(AllowedMapping.level_2)).filter(
        AllowedMapping.property_id == property_id,
        AllowedMapping.level_2.isnot(None)
    ).order_by(AllowedMapping.level_2).all()
    return [v[0] for v in values if v[0]]


def get_allowed_level3_values(db: Session, level_1: str, level_2: str, property_id: int) -> List[str]:
    """
    Retourne les valeurs level_3 autorisées pour un couple (level_1, level_2) (distinct) pour une propriété.
    
    Args:
        db: Session de base de données
        level_1: Valeur de level_1
        level_2: Valeur de level_2
        property_id: ID de la propriété
    
    Returns:
        Liste des valeurs level_3 uniques pour ce couple, triées
    """
    values = db.query(distinct(AllowedMapping.level_3)).filter(
        AllowedMapping.property_id == property_id,
        AllowedMapping.level_1 == level_1,
        AllowedMapping.level_2 == level_2,
        AllowedMapping.level_3.isnot(None)
    ).order_by(AllowedMapping.level_3).all()
    return [v[0] for v in values if v[0]]


def validate_mapping(db: Session, level_1: str, level_2: str, level_3: Optional[str] = None, property_id: Optional[int] = None) -> bool:
    """
    Valide qu'une combinaison existe dans la table allowed_mappings.
    
    Args:
        db: Session de base de données
        level_1: Valeur de level_1
        level_2: Valeur de level_2
        level_3: Valeur de level_3 (optionnel)
        property_id: ID de la propriété (obligatoire pour l'isolation multi-propriétés)
    
    Returns:
        True si la combinaison existe, False sinon
    """
    if property_id is None:
        raise ValueError("property_id est obligatoire pour valider un mapping")
    
    query = db.query(AllowedMapping).filter(
        AllowedMapping.property_id == property_id,
        AllowedMapping.level_1 == level_1,
        AllowedMapping.level_2 == level_2
    )
    
    if level_3 is not None:
        query = query.filter(AllowedMapping.level_3 == level_3)
    else:
        query = query.filter(AllowedMapping.level_3.is_(None))
    
    return query.first() is not None


def reset_to_hardcoded_values(db: Session) -> int:
    """
    Supprime toutes les combinaisons où is_hardcoded = False, garde les 50 initiales.
    
    Args:
        db: Session de base de données
    
    Returns:
        Nombre de combinaisons supprimées
    """
    deleted_count = db.query(AllowedMapping).filter(
        AllowedMapping.is_hardcoded == False
    ).delete()
    db.commit()
    return deleted_count


def get_allowed_level2_for_level3(db: Session, level_3: str) -> List[str]:
    """
    Retourne les valeurs level_2 autorisées pour un level_3 donné (distinct).
    
    Utilisé pour le filtrage bidirectionnel : quand level_3 est sélectionné en premier,
    on peut filtrer les level_2 possibles.
    
    Args:
        db: Session de base de données
        level_3: Valeur de level_3
    
    Returns:
        Liste des valeurs level_2 uniques pour ce level_3, triées
    """
    values = db.query(distinct(AllowedMapping.level_2)).filter(
        AllowedMapping.level_3 == level_3,
        AllowedMapping.level_2.isnot(None)
    ).order_by(AllowedMapping.level_2).all()
    return [v[0] for v in values if v[0]]


def get_allowed_level1_for_level2(db: Session, level_2: str) -> List[str]:
    """
    Retourne les valeurs level_1 autorisées pour un level_2 donné (distinct).
    
    Utilisé pour le filtrage bidirectionnel : quand level_2 est sélectionné en premier,
    on peut filtrer les level_1 possibles.
    
    Args:
        db: Session de base de données
        level_2: Valeur de level_2
    
    Returns:
        Liste des valeurs level_1 uniques pour ce level_2, triées
    """
    values = db.query(distinct(AllowedMapping.level_1)).filter(
        AllowedMapping.level_2 == level_2,
        AllowedMapping.level_1.isnot(None)
    ).order_by(AllowedMapping.level_1).all()
    return [v[0] for v in values if v[0]]


def get_allowed_level1_for_level2_and_level3(db: Session, level_2: str, level_3: str) -> List[str]:
    """
    Retourne les valeurs level_1 autorisées pour un couple (level_2, level_3) (distinct).
    
    Utilisé pour le filtrage bidirectionnel : quand level_3 puis level_2 sont sélectionnés,
    on peut filtrer les level_1 possibles pour validation.
    
    Args:
        db: Session de base de données
        level_2: Valeur de level_2
        level_3: Valeur de level_3
    
    Returns:
        Liste des valeurs level_1 uniques pour ce couple, triées
    """
    values = db.query(distinct(AllowedMapping.level_1)).filter(
        AllowedMapping.level_2 == level_2,
        AllowedMapping.level_3 == level_3,
        AllowedMapping.level_1.isnot(None)
    ).order_by(AllowedMapping.level_1).all()
    return [v[0] for v in values if v[0]]


def get_allowed_level3_for_level2(db: Session, level_2: str) -> List[str]:
    """
    Retourne les valeurs level_3 autorisées pour un level_2 donné (distinct).
    
    Utilisé pour le filtrage bidirectionnel : quand level_2 est sélectionné en premier,
    on peut trouver le level_3 unique (si unique) pour pré-remplir automatiquement.
    
    Args:
        db: Session de base de données
        level_2: Valeur de level_2
    
    Returns:
        Liste des valeurs level_3 uniques pour ce level_2, triées
    """
    values = db.query(distinct(AllowedMapping.level_3)).filter(
        AllowedMapping.level_2 == level_2,
        AllowedMapping.level_3.isnot(None)
    ).order_by(AllowedMapping.level_3).all()
    return [v[0] for v in values if v[0]]


def get_all_allowed_mappings(db: Session, property_id: int, skip: int = 0, limit: int = 100) -> tuple[List[AllowedMapping], int]:
    """
    Récupère tous les mappings autorisés avec pagination pour une propriété.
    
    Args:
        db: Session de base de données
        property_id: ID de la propriété
        skip: Nombre d'éléments à sauter
        limit: Nombre d'éléments à retourner
    
    Returns:
        Tuple (liste des mappings, total)
    """
    total = db.query(AllowedMapping).filter(AllowedMapping.property_id == property_id).count()
    mappings = db.query(AllowedMapping).filter(AllowedMapping.property_id == property_id).order_by(
        AllowedMapping.is_hardcoded.desc(),  # Hard codés en premier
        AllowedMapping.level_1,
        AllowedMapping.level_2,
        AllowedMapping.level_3
    ).offset(skip).limit(limit).all()
    return mappings, total


def create_allowed_mapping(db: Session, level_1: str, level_2: str, property_id: int, level_3: Optional[str] = None) -> AllowedMapping:
    """
    Crée un nouveau mapping autorisé pour une propriété.
    
    Args:
        db: Session de base de données
        level_1: Valeur de level_1
        level_2: Valeur de level_2
        property_id: ID de la propriété
        level_3: Valeur de level_3 (optionnel)
    
    Returns:
        Le mapping créé
    
    Raises:
        ValueError: Si la combinaison existe déjà ou si level_3 n'est pas valide
    """
    # Valider level_3
    if level_3 is not None and not validate_level3_value(level_3):
        raise ValueError(f"level_3='{level_3}' n'est pas autorisé. Valeurs autorisées: {', '.join(ALLOWED_LEVEL_3_VALUES)}")
    
    # Vérifier si la combinaison existe déjà pour cette propriété
    if validate_mapping(db, level_1, level_2, level_3, property_id):
        raise ValueError(f"La combinaison (level_1='{level_1}', level_2='{level_2}', level_3={level_3}) existe déjà pour cette propriété")
    
    # Créer le mapping (is_hardcoded = False car ajouté manuellement)
    mapping = AllowedMapping(
        property_id=property_id,
        level_1=level_1,
        level_2=level_2,
        level_3=level_3,
        is_hardcoded=False
    )
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    return mapping


def delete_allowed_mapping(db: Session, mapping_id: int) -> bool:
    """
    Supprime un mapping autorisé (uniquement si is_hardcoded = False).
    
    Args:
        db: Session de base de données
        mapping_id: ID du mapping à supprimer
    
    Returns:
        True si supprimé, False si non trouvé
    
    Raises:
        ValueError: Si le mapping est hard codé (is_hardcoded = True)
    """
    mapping = db.query(AllowedMapping).filter(AllowedMapping.id == mapping_id).first()
    if not mapping:
        return False
    
    if mapping.is_hardcoded:
        raise ValueError("Impossible de supprimer un mapping hard codé (protégé)")
    
    db.delete(mapping)
    db.commit()
    return True


def reset_allowed_mappings(db: Session) -> dict:
    """
    Reset les mappings autorisés : supprime uniquement les combinaisons ajoutées manuellement.
    
    Supprime aussi les mappings invalides et marque les transactions associées comme non assignées.
    
    Args:
        db: Session de base de données
    
    Returns:
        Dictionnaire avec les statistiques (deleted_allowed, deleted_mappings, unassigned_transactions)
    """
    from backend.database.models import Mapping, EnrichedTransaction
    
    # 1. Supprimer les allowed_mappings non hard codés
    deleted_allowed = db.query(AllowedMapping).filter(
        AllowedMapping.is_hardcoded == False
    ).delete()
    db.commit()
    
    # 2. Supprimer les mappings invalides (combinaisons qui ne sont plus dans allowed_mappings)
    all_allowed = db.query(AllowedMapping).all()
    allowed_combinations = {
        (m.level_1, m.level_2, m.level_3) for m in all_allowed
    }
    
    all_mappings = db.query(Mapping).all()
    deleted_mappings = 0
    transactions_to_unassign = set()
    
    for mapping in all_mappings:
        combination = (mapping.level_1, mapping.level_2, mapping.level_3)
        if combination not in allowed_combinations:
            # Récupérer les transactions associées avant de supprimer
            transactions = db.query(Transaction).filter(
                Transaction.nom == mapping.nom
            ).all()
            transactions_to_unassign.update(t.id for t in transactions)
            
            db.delete(mapping)
            deleted_mappings += 1
    
    db.commit()
    
    # 3. Marquer les transactions associées comme non assignées (supprimer EnrichedTransaction)
    unassigned_count = 0
    for transaction_id in transactions_to_unassign:
        db.query(EnrichedTransaction).filter(
            EnrichedTransaction.transaction_id == transaction_id
        ).delete()
        unassigned_count += 1
    
    db.commit()
    
    return {
        "deleted_allowed": deleted_allowed,
        "deleted_mappings": deleted_mappings,
        "unassigned_transactions": unassigned_count
    }

