"""
Service de gestion des mappings autorisés (combinaisons level_1, level_2, level_3).

⚠️ Before making changes, read: ../../../docs/workflow/BEST_PRACTICES.md
"""

from sqlalchemy.orm import Session
from sqlalchemy import distinct
from typing import List, Optional
from pathlib import Path
import pandas as pd

from backend.database.models import AllowedMapping


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


def load_allowed_mappings_from_excel(db: Session, excel_path: Optional[Path] = None) -> int:
    """
    Charge le fichier Excel et insère les combinaisons dans la table allowed_mappings.
    
    Les combinaisons sont marquées avec is_hardcoded = True (protégées).
    
    Args:
        db: Session de base de données
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
        
        # Vérifier si la combinaison existe déjà
        query = db.query(AllowedMapping).filter(
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
                db.commit()
            continue
        
        # Créer la nouvelle combinaison
        try:
            allowed_mapping = AllowedMapping(
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


def get_allowed_level1_values(db: Session) -> List[str]:
    """
    Retourne toutes les valeurs level_1 autorisées (distinct).
    
    Args:
        db: Session de base de données
    
    Returns:
        Liste des valeurs level_1 uniques, triées
    """
    values = db.query(distinct(AllowedMapping.level_1)).filter(
        AllowedMapping.level_1.isnot(None)
    ).order_by(AllowedMapping.level_1).all()
    return [v[0] for v in values if v[0]]


def get_allowed_level2_values(db: Session, level_1: str) -> List[str]:
    """
    Retourne les valeurs level_2 autorisées pour un level_1 donné (distinct).
    
    Args:
        db: Session de base de données
        level_1: Valeur de level_1
    
    Returns:
        Liste des valeurs level_2 uniques pour ce level_1, triées
    """
    values = db.query(distinct(AllowedMapping.level_2)).filter(
        AllowedMapping.level_1 == level_1,
        AllowedMapping.level_2.isnot(None)
    ).order_by(AllowedMapping.level_2).all()
    return [v[0] for v in values if v[0]]


def get_allowed_level3_values(db: Session, level_1: str, level_2: str) -> List[str]:
    """
    Retourne les valeurs level_3 autorisées pour un couple (level_1, level_2) (distinct).
    
    Args:
        db: Session de base de données
        level_1: Valeur de level_1
        level_2: Valeur de level_2
    
    Returns:
        Liste des valeurs level_3 uniques pour ce couple, triées
    """
    values = db.query(distinct(AllowedMapping.level_3)).filter(
        AllowedMapping.level_1 == level_1,
        AllowedMapping.level_2 == level_2,
        AllowedMapping.level_3.isnot(None)
    ).order_by(AllowedMapping.level_3).all()
    return [v[0] for v in values if v[0]]


def validate_mapping(db: Session, level_1: str, level_2: str, level_3: Optional[str] = None) -> bool:
    """
    Valide qu'une combinaison existe dans la table allowed_mappings.
    
    Args:
        db: Session de base de données
        level_1: Valeur de level_1
        level_2: Valeur de level_2
        level_3: Valeur de level_3 (optionnel)
    
    Returns:
        True si la combinaison existe, False sinon
    """
    query = db.query(AllowedMapping).filter(
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

