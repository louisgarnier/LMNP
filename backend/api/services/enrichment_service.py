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


def find_best_mapping(transaction_name: str, mappings: list[Mapping]) -> Optional[Mapping]:
    """
    Trouve le meilleur mapping pour un nom de transaction donné.
    
    Logique de matching :
    1. Cas spécial PRLV SEPA : Recherche par préfixe avec "PRLV SEPA" dans le nom
    2. Cas spécial VIR STRIPE : Correspondance exacte si nom = "VIR STRIPE"
    3. Cas général : Recherche par préfixe le plus long qui correspond
    4. Matching "smart" : Recherche par pattern/contient (si le nom de la transaction
       contient le nom du mapping)
    
    Args:
        transaction_name: Nom de la transaction à mapper
        mappings: Liste des mappings disponibles
    
    Returns:
        Le meilleur mapping trouvé, ou None si aucun mapping ne correspond
    """
    best_match = None
    best_length = 0
    
    # Normaliser le nom de la transaction (supprimer espaces en début/fin)
    transaction_name = transaction_name.strip()
    
    for mapping in mappings:
        mapping_name = mapping.nom.strip()
        
        # Cas spécial pour PRLV SEPA
        if 'PRLV SEPA' in transaction_name and 'PRLV SEPA' in mapping_name:
            if transaction_name.startswith(mapping_name) and len(mapping_name) > best_length:
                best_match = mapping
                best_length = len(mapping_name)
        
        # Cas spécial pour VIR STRIPE (correspondance exacte)
        elif 'VIR STRIPE' in transaction_name and mapping_name == 'VIR STRIPE':
            best_match = mapping
            break
        
        # Cas général : recherche par préfixe (si is_prefix_match = True)
        elif mapping.is_prefix_match:
            if transaction_name.startswith(mapping_name) and len(mapping_name) > best_length:
                best_match = mapping
                best_length = len(mapping_name)
        
        # Matching "smart" : recherche par pattern/contient
        # Si le nom de la transaction contient le nom du mapping
        elif mapping_name in transaction_name and len(mapping_name) > best_length:
            best_match = mapping
            best_length = len(mapping_name)
    
    return best_match


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
        # Pas de mapping trouvé → valeurs NULL (affichées "à remplir" dans l'interface)
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

