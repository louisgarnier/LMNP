"""
Service de gestion des mappings autorisés (combinaisons level_1, level_2, level_3).

⚠️ Before making changes, read: ../../../docs/workflow/BEST_PRACTICES.md

Étape 3 Task 9 : réduit aux 2 seules fonctions encore vivantes
(`enrichment_service` les importe). Le reste du module (CRUD allowed_mappings,
chargement Excel, filtres bidirectionnels, reset) a été retiré : ces surfaces
sont mortes depuis le passage au moteur unique `classification_rules`
(étape 3 §5). Le retrait des classes ORM correspondantes (`AllowedMapping`) est
fait séparément dans `database/models.py` — aucune table physique n'est
droppée ici (différé Task 10).
"""

from sqlalchemy.orm import Session
from typing import Optional

from backend.api.services.category_service import resolve_category


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


def validate_mapping(db: Session, level_1: str, level_2: str, level_3: Optional[str] = None, property_id: Optional[int] = None) -> bool:
    """
    Valide qu'un triplet existe dans le RÉFÉRENTIEL (categories/category_groups).
    Remplace l'ancienne interrogation de allowed_mappings (supprimée en étape 3).

    Args:
        db: Session de base de données
        level_1: Valeur de level_1
        level_2: Valeur de level_2
        level_3: Valeur de level_3 (obligatoire pour résoudre dans le référentiel)
        property_id: ID de la propriété (obligatoire, conservé pour compat signature)

    Returns:
        True si le triplet résout dans le référentiel, False sinon
    """
    if property_id is None:
        raise ValueError("property_id est obligatoire pour valider un mapping")
    if level_3 is None:
        return False  # le référentiel exige les 3 niveaux (nature)
    return resolve_category(db, level_1, level_2, level_3) is not None
