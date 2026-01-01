"""
Service for managing allowed mapping combinations (level_1, level_2, level_3).

⚠️ Before making changes, read: ../../../docs/workflow/BEST_PRACTICES.md
"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import distinct
from backend.database.models import AllowedMapping


def get_allowed_level1_values(db: Session) -> List[str]:
    """
    Retourne toutes les valeurs level_1 autorisées (distinct).
    
    Args:
        db: Session de base de données
        
    Returns:
        Liste des valeurs level_1 distinctes, triées par ordre alphabétique
    """
    results = db.query(distinct(AllowedMapping.level_1)).order_by(AllowedMapping.level_1).all()
    return [row[0] for row in results if row[0] is not None]


def get_allowed_level2_values(db: Session, level_1: str) -> List[str]:
    """
    Retourne les valeurs level_2 autorisées pour un level_1 donné (distinct).
    
    Args:
        db: Session de base de données
        level_1: Valeur de level_1 pour filtrer
        
    Returns:
        Liste des valeurs level_2 distinctes pour ce level_1, triées par ordre alphabétique
    """
    results = db.query(distinct(AllowedMapping.level_2)).filter(
        AllowedMapping.level_1 == level_1
    ).order_by(AllowedMapping.level_2).all()
    return [row[0] for row in results if row[0] is not None]


def get_all_allowed_level2_values(db: Session) -> List[str]:
    """
    Retourne toutes les valeurs level_2 autorisées (distinct), sans filtre par level_1.
    
    Args:
        db: Session de base de données
        
    Returns:
        Liste de toutes les valeurs level_2 distinctes, triées par ordre alphabétique
    """
    results = db.query(distinct(AllowedMapping.level_2)).order_by(AllowedMapping.level_2).all()
    return [row[0] for row in results if row[0] is not None]


def get_allowed_level3_values(db: Session, level_1: str, level_2: str) -> List[str]:
    """
    Retourne les valeurs level_3 autorisées pour un couple (level_1, level_2) donné (distinct).
    
    Args:
        db: Session de base de données
        level_1: Valeur de level_1 pour filtrer
        level_2: Valeur de level_2 pour filtrer
        
    Returns:
        Liste des valeurs level_3 distinctes pour ce couple (level_1, level_2), triées par ordre alphabétique
        Retourne une liste vide si level_3 est None pour toutes les combinaisons
    """
    results = db.query(distinct(AllowedMapping.level_3)).filter(
        AllowedMapping.level_1 == level_1,
        AllowedMapping.level_2 == level_2
    ).order_by(AllowedMapping.level_3).all()
    # Filtrer les None
    return [row[0] for row in results if row[0] is not None]


def get_all_allowed_level3_values(db: Session) -> List[str]:
    """
    Retourne toutes les valeurs level_3 autorisées (distinct), sans filtre par level_1 ou level_2.
    
    Args:
        db: Session de base de données
        
    Returns:
        Liste de toutes les valeurs level_3 distinctes, triées par ordre alphabétique
    """
    results = db.query(distinct(AllowedMapping.level_3)).order_by(AllowedMapping.level_3).all()
    return [row[0] for row in results if row[0] is not None]


def validate_mapping(db: Session, level_1: str, level_2: str, level_3: Optional[str] = None) -> bool:
    """
    Valide qu'une combinaison (level_1, level_2, level_3) existe dans la table allowed_mappings.
    
    Args:
        db: Session de base de données
        level_1: Valeur de level_1
        level_2: Valeur de level_2
        level_3: Valeur de level_3 (optionnel)
        
    Returns:
        True si la combinaison est autorisée, False sinon
    """
    query = db.query(AllowedMapping).filter(
        AllowedMapping.level_1 == level_1,
        AllowedMapping.level_2 == level_2
    )
    
    if level_3 is None:
        # Si level_3 n'est pas fourni, vérifier qu'il existe une combinaison avec level_3 = None
        query = query.filter(AllowedMapping.level_3.is_(None))
    else:
        # Si level_3 est fourni, vérifier qu'il existe une combinaison avec cette valeur
        query = query.filter(AllowedMapping.level_3 == level_3)
    
    return query.first() is not None


def get_allowed_level2_for_level3(db: Session, level_3: str) -> List[str]:
    """
    Retourne les valeurs level_2 autorisées pour un level_3 donné (distinct).
    
    Args:
        db: Session de base de données
        level_3: Valeur de level_3 pour filtrer
        
    Returns:
        Liste des valeurs level_2 distinctes pour ce level_3, triées par ordre alphabétique
    """
    results = db.query(distinct(AllowedMapping.level_2)).filter(
        AllowedMapping.level_3 == level_3
    ).order_by(AllowedMapping.level_2).all()
    return [row[0] for row in results if row[0] is not None]


def get_allowed_level1_for_level2(db: Session, level_2: str) -> List[str]:
    """
    Retourne les valeurs level_1 autorisées pour un level_2 donné (distinct).
    
    Args:
        db: Session de base de données
        level_2: Valeur de level_2 pour filtrer
        
    Returns:
        Liste des valeurs level_1 distinctes pour ce level_2, triées par ordre alphabétique
    """
    results = db.query(distinct(AllowedMapping.level_1)).filter(
        AllowedMapping.level_2 == level_2
    ).order_by(AllowedMapping.level_1).all()
    return [row[0] for row in results if row[0] is not None]


def get_allowed_level1_for_level2_and_level3(db: Session, level_2: str, level_3: str) -> List[str]:
    """
    Retourne les valeurs level_1 autorisées pour un couple (level_2, level_3) donné (distinct).
    
    Args:
        db: Session de base de données
        level_2: Valeur de level_2 pour filtrer
        level_3: Valeur de level_3 pour filtrer
        
    Returns:
        Liste des valeurs level_1 distinctes pour ce couple (level_2, level_3), triées par ordre alphabétique
    """
    results = db.query(distinct(AllowedMapping.level_1)).filter(
        AllowedMapping.level_2 == level_2,
        AllowedMapping.level_3 == level_3
    ).order_by(AllowedMapping.level_1).all()
    return [row[0] for row in results if row[0] is not None]


def get_allowed_level1_for_level3(db: Session, level_3: str) -> List[str]:
    """
    Retourne les valeurs level_1 autorisées pour un level_3 donné (distinct), peu importe le level_2.
    
    Args:
        db: Session de base de données
        level_3: Valeur de level_3 pour filtrer
        
    Returns:
        Liste des valeurs level_1 distinctes pour ce level_3, triées par ordre alphabétique
    """
    results = db.query(distinct(AllowedMapping.level_1)).filter(
        AllowedMapping.level_3 == level_3
    ).order_by(AllowedMapping.level_1).all()
    return [row[0] for row in results if row[0] is not None]


def get_allowed_level1_for_level3_list(db: Session, level_3_list: List[str]) -> List[str]:
    """
    Retourne toutes les valeurs level_1 autorisées associées à au moins un des level_3 de la liste (distinct).
    
    Args:
        db: Session de base de données
        level_3_list: Liste des valeurs level_3 pour filtrer
        
    Returns:
        Liste des valeurs level_1 distinctes associées à au moins un level_3 de la liste, triées par ordre alphabétique
    """
    if not level_3_list:
        return []
    
    results = db.query(distinct(AllowedMapping.level_1)).filter(
        AllowedMapping.level_3.in_(level_3_list)
    ).order_by(AllowedMapping.level_1).all()
    return [row[0] for row in results if row[0] is not None]


def get_unique_combination_for_level1(db: Session, level_1: str) -> Optional[tuple]:
    """
    Retourne la combinaison unique (level_2, level_3) pour un level_1 donné.
    
    Comme chaque level_1 a une combinaison unique level_2/level_3, cette fonction
    retourne cette combinaison unique.
    
    Args:
        db: Session de base de données
        level_1: Valeur de level_1
        
    Returns:
        Tuple (level_2, level_3) ou None si aucune combinaison trouvée
    """
    mapping = db.query(AllowedMapping).filter(
        AllowedMapping.level_1 == level_1
    ).first()
    
    if mapping:
        return (mapping.level_2, mapping.level_3)
    return None


def get_unique_combination_for_level2(db: Session, level_2: str) -> Optional[tuple]:
    """
    Retourne la combinaison unique (level_1, level_3) pour un level_2 donné.
    
    Comme chaque level_2 a une combinaison unique level_1/level_3, cette fonction
    retourne cette combinaison unique.
    
    Args:
        db: Session de base de données
        level_2: Valeur de level_2
        
    Returns:
        Tuple (level_1, level_3) ou None si aucune combinaison trouvée
    """
    mapping = db.query(AllowedMapping).filter(
        AllowedMapping.level_2 == level_2
    ).first()
    
    if mapping:
        return (mapping.level_1, mapping.level_3)
    return None

