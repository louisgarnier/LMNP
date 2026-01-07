"""
Service d'enrichissement des transactions avec classifications.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce service implémente la logique de mapping intelligent pour enrichir
les transactions avec des classifications hiérarchiques (level_1, level_2, level_3).
"""

from sqlalchemy.orm import Session
from typing import Optional, Tuple
from datetime import date

from backend.database.models import Transaction, Mapping, EnrichedTransaction
from backend.api.services.mapping_obligatoire_service import (
    validate_mapping,
    validate_level3_value
)


def find_best_mapping(transaction_name: str, mappings: list[Mapping]) -> Optional[Mapping]:
    """
    Trouve le meilleur mapping pour un nom de transaction donné.
    
    Logique de matching :
    1. Cas spécial PRLV SEPA : Recherche par préfixe avec "PRLV SEPA" dans le nom
    2. Cas spécial VIR STRIPE : Correspondance exacte si nom = "VIR STRIPE"
    3. Cas général : Recherche par préfixe le plus long qui correspond
    4. Matching "smart" : Recherche par pattern/contient (si le nom de la transaction
       contient le nom du mapping)
    
    **Règle importante (Step 5.3)** : Si plusieurs mappings correspondent à une transaction,
    retourner None pour éviter les conflits. La transaction restera non classée (unassigned).
    
    Args:
        transaction_name: Nom de la transaction à mapper
        mappings: Liste des mappings disponibles
    
    Returns:
        Le meilleur mapping trouvé, ou None si aucun mapping ne correspond ou si plusieurs mappings correspondent
    """
    matching_mappings = []
    
    # Normaliser le nom de la transaction (supprimer espaces en début/fin)
    transaction_name = transaction_name.strip()
    
    for mapping in mappings:
        mapping_name = mapping.nom.strip()
        matches = False
        
        # Cas spécial pour PRLV SEPA
        if 'PRLV SEPA' in transaction_name and 'PRLV SEPA' in mapping_name:
            if transaction_name.startswith(mapping_name):
                matches = True
        
        # Cas spécial pour VIR STRIPE (correspondance exacte)
        elif 'VIR STRIPE' in transaction_name and mapping_name == 'VIR STRIPE':
            matches = True
        
        # Cas général : recherche par préfixe (si is_prefix_match = True)
        elif mapping.is_prefix_match:
            if transaction_name.startswith(mapping_name):
                matches = True
        
        # Matching "smart" : recherche par pattern/contient
        # Si le nom de la transaction contient le nom du mapping
        elif mapping_name in transaction_name:
            matches = True
        
        if matches:
            matching_mappings.append(mapping)
    
    # Si aucun mapping ne correspond
    if len(matching_mappings) == 0:
        return None
    
    # **Règle Step 5.3** : Si plusieurs mappings correspondent, retourner None
    # pour éviter les conflits. La transaction restera non classée.
    if len(matching_mappings) > 1:
        return None
    
    # Un seul mapping correspond → le retourner
    return matching_mappings[0]


def transaction_matches_mapping_name(transaction_name: str, mapping_name: str) -> bool:
    """
    Vérifie si une transaction correspond à un nom de mapping.
    
    Utilise la même logique que find_best_mapping pour déterminer si une transaction
    correspond à un mapping donné.
    
    Args:
        transaction_name: Nom de la transaction
        mapping_name: Nom du mapping
    
    Returns:
        True si la transaction correspond au mapping, False sinon
    """
    transaction_name = transaction_name.strip()
    mapping_name = mapping_name.strip()
    
    # Cas spécial pour PRLV SEPA
    if 'PRLV SEPA' in transaction_name and 'PRLV SEPA' in mapping_name:
        return transaction_name.startswith(mapping_name)
    
    # Cas spécial pour VIR STRIPE (correspondance exacte)
    if 'VIR STRIPE' in transaction_name and mapping_name == 'VIR STRIPE':
        return True
    
    # Cas général : recherche par préfixe ou contient
    if mapping_name in transaction_name or transaction_name.startswith(mapping_name):
        return True
    
    return False


def enrich_transaction(transaction: Transaction, db: Session, mappings: Optional[list[Mapping]] = None) -> EnrichedTransaction:
    """
    Enrichit une transaction avec des classifications basées sur le mapping.
    
    Args:
        transaction: Transaction à enrichir
        db: Session de base de données
        mappings: Liste des mappings (optionnel, sera chargée depuis DB si non fournie)
    
    Returns:
        L'objet EnrichedTransaction créé ou mis à jour
    """
    # Calculer l'année depuis la date
    annee = transaction.date.year
    mois = transaction.date.month
    
    # Récupérer tous les mappings depuis la DB si non fournis
    if mappings is None:
        mappings = db.query(Mapping).all()
    
    # Trouver le meilleur mapping
    best_mapping = find_best_mapping(transaction.nom, mappings)
    
    # Déterminer les valeurs de level_1, level_2, level_3
    if best_mapping:
        level_1 = best_mapping.level_1
        level_2 = best_mapping.level_2
        level_3 = best_mapping.level_3
    else:
        # Pas de mapping trouvé → valeurs NULL (affichées "unassigned" dans l'interface)
        level_1 = None
        level_2 = None
        level_3 = None
    
    # Vérifier si une ligne enriched_transaction existe déjà
    enriched = db.query(EnrichedTransaction).filter(
        EnrichedTransaction.transaction_id == transaction.id
    ).first()
    
    if enriched:
        # Mettre à jour l'enregistrement existant
        enriched.annee = annee
        enriched.mois = mois
        enriched.level_1 = level_1
        enriched.level_2 = level_2
        enriched.level_3 = level_3
    else:
        # Créer un nouvel enregistrement
        enriched = EnrichedTransaction(
            transaction_id=transaction.id,
            annee=annee,
            mois=mois,
            level_1=level_1,
            level_2=level_2,
            level_3=level_3
        )
        db.add(enriched)
    
    db.commit()
    db.refresh(enriched)
    
    return enriched


def enrich_all_transactions(db: Session) -> Tuple[int, int]:
    """
    Enrichit toutes les transactions qui n'ont pas encore été enrichies.
    
    Args:
        db: Session de base de données
    
    Returns:
        Tuple (nombre de transactions enrichies, nombre de transactions déjà enrichies)
    """
    # Récupérer toutes les transactions
    transactions = db.query(Transaction).all()
    
    # Récupérer tous les mappings une seule fois
    mappings = db.query(Mapping).all()
    
    enriched_count = 0
    already_enriched_count = 0
    
    for transaction in transactions:
        # Vérifier si déjà enrichi
        existing = db.query(EnrichedTransaction).filter(
            EnrichedTransaction.transaction_id == transaction.id
        ).first()
        
        if existing:
            already_enriched_count += 1
            # Re-enrichir quand même pour mettre à jour si le mapping a changé
            enrich_transaction(transaction, db)
        else:
            enrich_transaction(transaction, db)
            enriched_count += 1
    
    return enriched_count, already_enriched_count


def update_transaction_classification(
    db: Session,
    transaction: Transaction,
    level_1: str | None = None,
    level_2: str | None = None,
    level_3: str | None = None
) -> EnrichedTransaction:
    """
    Met à jour les classifications d'une transaction.
    
    Args:
        db: Session de base de données
        transaction: Transaction à mettre à jour
        level_1: Nouvelle valeur pour level_1 (optionnel)
        level_2: Nouvelle valeur pour level_2 (optionnel)
        level_3: Nouvelle valeur pour level_3 (optionnel)
    
    Returns:
        L'objet EnrichedTransaction mis à jour
    """
    # Calculer l'année et le mois depuis la date
    annee = transaction.date.year
    mois = transaction.date.month
    
    # Vérifier si une ligne enriched_transaction existe déjà
    enriched = db.query(EnrichedTransaction).filter(
        EnrichedTransaction.transaction_id == transaction.id
    ).first()
    
    if enriched:
        # Mettre à jour l'enregistrement existant
        if level_1 is not None:
            enriched.level_1 = level_1
        if level_2 is not None:
            enriched.level_2 = level_2
        if level_3 is not None:
            enriched.level_3 = level_3
        # Toujours mettre à jour annee et mois
        enriched.annee = annee
        enriched.mois = mois
    else:
        # Créer un nouvel enregistrement
        enriched = EnrichedTransaction(
            transaction_id=transaction.id,
            annee=annee,
            mois=mois,
            level_1=level_1,
            level_2=level_2,
            level_3=level_3
        )
        db.add(enriched)
    
    db.commit()
    db.refresh(enriched)
    
    return enriched


def create_or_update_mapping_from_classification(
    db: Session,
    transaction_name: str,
    level_1: str,
    level_2: str,
    level_3: str | None = None
) -> Mapping:
    """
    Crée ou met à jour un mapping basé sur une classification manuelle.
    
    Le mapping est la source de vérité. Si un mapping existe déjà avec le même nom,
    on le met à jour. Sinon, on en crée un nouveau.
    
    **Validation Step 5.4** : La combinaison (level_1, level_2, level_3) doit être validée
    contre allowed_mappings avant de créer/mettre à jour le mapping.
    
    Args:
        db: Session de base de données
        transaction_name: Nom de la transaction
        level_1: Catégorie principale
        level_2: Sous-catégorie
        level_3: Détail spécifique (optionnel)
    
    Returns:
        Le mapping créé ou mis à jour
    
    Raises:
        ValueError: Si la combinaison n'est pas autorisée
    """
    # Validation contre allowed_mappings (Step 5.4)
    # Valider que level_3 est dans la liste fixe si fourni
    if level_3 and not validate_level3_value(level_3):
        raise ValueError(f"La valeur level_3 '{level_3}' n'est pas autorisée. Valeurs autorisées : Passif, Produits, Emprunt, Charges Déductibles, Actif")
    
    # Valider que la combinaison existe dans allowed_mappings
    if not validate_mapping(db, level_1, level_2, level_3):
        raise ValueError(f"La combinaison (level_1='{level_1}', level_2='{level_2}', level_3='{level_3}') n'est pas autorisée. Veuillez utiliser une combinaison valide depuis les mappings autorisés.")
    
    # Chercher un mapping existant avec le même nom
    existing_mapping = db.query(Mapping).filter(Mapping.nom == transaction_name).first()
    
    if existing_mapping:
        # Mettre à jour le mapping existant
        existing_mapping.level_1 = level_1
        existing_mapping.level_2 = level_2
        existing_mapping.level_3 = level_3
        db.commit()
        db.refresh(existing_mapping)
        return existing_mapping
    else:
        # Créer un nouveau mapping
        new_mapping = Mapping(
            nom=transaction_name,
            level_1=level_1,
            level_2=level_2,
            level_3=level_3,
            is_prefix_match=True,  # Par défaut, on utilise le préfixe
            priority=0
        )
        db.add(new_mapping)
        db.commit()
        db.refresh(new_mapping)
        return new_mapping

