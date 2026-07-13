"""
Service d'enrichissement des transactions avec classifications.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce service implémente la logique de mapping intelligent pour enrichir
les transactions avec des classifications hiérarchiques (level_1, level_2, level_3).
"""

from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import Optional, Tuple
import logging

from backend.database.models import Transaction, Mapping, ClassificationRule
from backend.api.services.classification_engine import find_matching_rule
from backend.api.services.mapping_obligatoire_service import (
    validate_mapping,
    validate_level3_value
)

logger = logging.getLogger(__name__)


def assign_category(db: Session, transaction: Transaction,
                    level_1: str | None, level_2: str | None,
                    level_3: str | None) -> None:
    """Écrit `transactions.category_id` depuis la classification texte.

    Étape 2 Task 8 : SEUL point d'écriture de la classification (la table
    `enriched_transactions` a disparu ; la classification vit désormais dans
    `transactions.category_id`, dérivée via le référentiel category).

    Garde défensive : si la classification est incomplète (level_2/level_3
    manquants) ou si level_3 n'est pas une des 5 natures autorisées,
    category_id est remis à NULL plutôt que de laisser
    `get_or_create_category` lever un KeyError. En pratique tous les sites
    d'appel valident déjà (level_1, level_2, level_3) contre
    `allowed_mappings` avant d'écrire, SAUF `update_transaction_classification`
    appelée avec un seul niveau fourni (level_2/level_3 restant None) — cas
    non exercé aujourd'hui par le frontend (qui envoie toujours les 3
    niveaux ensemble) mais possible via l'API brute.
    """
    from backend.api.services.category_service import get_or_create_category, NATURE_BY_LABEL
    if level_1 is None or level_2 is None or level_3 not in NATURE_BY_LABEL:
        transaction.category_id = None
    else:
        transaction.category_id = get_or_create_category(db, level_1, level_2, level_3).id


def find_best_mapping(transaction_name: str, mappings: list[Mapping]) -> Optional[Mapping]:
    """
    Trouve le meilleur mapping pour un nom de transaction donné.
    
    Logique de matching :
    1. Cas spécial PRLV SEPA : Recherche par préfixe avec "PRLV SEPA" dans le nom
    2. Cas spécial VIR STRIPE : Correspondance exacte si nom = "VIR STRIPE"
    3. Correspondance exacte : Si transaction_name == mapping_name → toujours utiliser
    4. Cas général : Recherche par préfixe (si is_prefix_match = True) avec seuil de similarité
       - Le ratio longueur_mapping / longueur_transaction doit être >= 70%
       - Cela évite qu'un mapping générique mappe des transactions spécifiques
    5. Matching "smart" : Recherche par pattern/contient (si le nom de la transaction
       contient le nom du mapping) - avec le même seuil de similarité
    
    **Règle importante** : Un mapping générique ne doit PAS mapper automatiquement une transaction
    spécifique. Si aucun mapping spécifique n'existe, la transaction reste non mappée (unassigned)
    pour que l'utilisateur puisse choisir manuellement.
    
    **Règle importante (Step 5.3 modifiée)** : Si plusieurs mappings correspondent à une transaction,
    choisir celui avec le nom le plus long (correspondance exacte ou préfixe le plus long).
    Si plusieurs mappings ont la même longueur et correspondent, retourner None pour éviter les conflits.
    
    Args:
        transaction_name: Nom de la transaction à mapper
        mappings: Liste des mappings disponibles
    
    Returns:
        Le meilleur mapping trouvé (le plus long qui correspond), ou None si aucun mapping ne correspond
        ou si plusieurs mappings de même longueur correspondent, ou si le mapping est trop générique
    """
    best_match = None
    best_length = 0
    matching_mappings = []
    
    # Normaliser le nom de la transaction (supprimer espaces en début/fin)
    transaction_name = transaction_name.strip()
    transaction_length = len(transaction_name)
    
    # Seuil minimum de similarité pour les mappings préfixes (70%)
    # Cela évite qu'un mapping générique comme "achat appart" (12 chars) 
    # mappe "achat appart (Immobilisation Facade/Toiture)" (47 chars)
    MIN_SIMILARITY_RATIO = 0.70
    
    for mapping in mappings:
        mapping_name = mapping.nom.strip()
        matches = False
        match_length = 0
        
        # Correspondance exacte → toujours utiliser (même si court)
        if transaction_name == mapping_name:
            matches = True
            match_length = len(mapping_name)
        
        # Cas spécial pour PRLV SEPA
        elif 'PRLV SEPA' in transaction_name and 'PRLV SEPA' in mapping_name:
            if transaction_name.startswith(mapping_name):
                matches = True
                match_length = len(mapping_name)
        
        # Cas spécial pour VIR STRIPE (correspondance exacte)
        elif 'VIR STRIPE' in transaction_name and mapping_name == 'VIR STRIPE':
            matches = True
            match_length = len(mapping_name)
        
        # Cas général : recherche par préfixe (si is_prefix_match = True)
        # MAIS seulement si le ratio de similarité est suffisant
        elif mapping.is_prefix_match:
            if transaction_name.startswith(mapping_name):
                mapping_length = len(mapping_name)
                similarity_ratio = mapping_length / transaction_length if transaction_length > 0 else 0
                # Utiliser le mapping seulement si le ratio est >= 70%
                if similarity_ratio >= MIN_SIMILARITY_RATIO:
                    matches = True
                    match_length = mapping_length
                else:
                    # Mapping trop générique → ignorer
                    logger.debug(
                        f"[find_best_mapping] Mapping générique ignoré: "
                        f"'{mapping_name}' ({mapping_length} chars) vs '{transaction_name}' ({transaction_length} chars) "
                        f"(ratio={similarity_ratio:.2%} < {MIN_SIMILARITY_RATIO:.2%})"
                    )
        
        # Matching "smart" : recherche par pattern/contient
        # Si le nom de la transaction contient le nom du mapping
        # MAIS seulement si le ratio de similarité est suffisant
        elif mapping_name in transaction_name:
            mapping_length = len(mapping_name)
            similarity_ratio = mapping_length / transaction_length if transaction_length > 0 else 0
            # Utiliser le mapping seulement si le ratio est >= 70%
            if similarity_ratio >= MIN_SIMILARITY_RATIO:
                matches = True
                match_length = mapping_length
            else:
                # Mapping trop générique → ignorer
                logger.debug(
                    f"[find_best_mapping] Mapping générique ignoré: "
                    f"'{mapping_name}' ({mapping_length} chars) vs '{transaction_name}' ({transaction_length} chars) "
                    f"(ratio={similarity_ratio:.2%} < {MIN_SIMILARITY_RATIO:.2%})"
                )
        
        if matches:
            matching_mappings.append((mapping, match_length))
            # Garder le meilleur (le plus long)
            if match_length > best_length:
                best_match = mapping
                best_length = match_length
    
    # Si aucun mapping ne correspond
    if len(matching_mappings) == 0:
        return None
    
    # Si plusieurs mappings correspondent avec la même longueur maximale, retourner None
    # (conflit réel - plusieurs mappings équivalents)
    max_length_mappings = [m for m, length in matching_mappings if length == best_length]
    if len(max_length_mappings) > 1:
        return None
    
    # Retourner le meilleur mapping (le plus long)
    return best_match


def transaction_matches_mapping_name(transaction_name: str, mapping_name: str, is_prefix_match: bool = True) -> bool:
    """
    Vérifie si une transaction correspond à un nom de mapping.
    
    Utilise la même logique que find_best_mapping pour déterminer si une transaction
    correspond à un mapping donné, avec le même seuil de similarité pour éviter
    les mappings génériques.
    
    Args:
        transaction_name: Nom de la transaction
        mapping_name: Nom du mapping
        is_prefix_match: Si True, utilise le matching par préfixe (défaut: True)
    
    Returns:
        True si la transaction correspond au mapping, False sinon
    """
    transaction_name = transaction_name.strip()
    mapping_name = mapping_name.strip()
    transaction_length = len(transaction_name)
    mapping_length = len(mapping_name)
    
    # Seuil minimum de similarité (70%)
    MIN_SIMILARITY_RATIO = 0.70
    
    # Correspondance exacte → toujours OK
    if transaction_name == mapping_name:
        return True
    
    # Cas spécial pour PRLV SEPA
    if 'PRLV SEPA' in transaction_name and 'PRLV SEPA' in mapping_name:
        return transaction_name.startswith(mapping_name)
    
    # Cas spécial pour VIR STRIPE (correspondance exacte)
    if 'VIR STRIPE' in transaction_name and mapping_name == 'VIR STRIPE':
        return True
    
    # Cas général : recherche par préfixe ou contient
    # MAIS seulement si le ratio de similarité est suffisant
    if is_prefix_match and transaction_name.startswith(mapping_name):
        similarity_ratio = mapping_length / transaction_length if transaction_length > 0 else 0
        return similarity_ratio >= MIN_SIMILARITY_RATIO
    elif mapping_name in transaction_name:
        similarity_ratio = mapping_length / transaction_length if transaction_length > 0 else 0
        return similarity_ratio >= MIN_SIMILARITY_RATIO
    
    return False


def _rules_for_property(db: Session, property_id: Optional[int]) -> list[ClassificationRule]:
    """Règles applicables à une propriété : celles du bien + les globales
    (`property_id IS NULL`)."""
    return (db.query(ClassificationRule)
            .filter(or_(ClassificationRule.property_id == property_id,
                        ClassificationRule.property_id.is_(None)))
            .all())


def enrich_transaction(transaction: Transaction, db: Session,
                       rules: Optional[list[ClassificationRule]] = None) -> Optional[ClassificationRule]:
    """
    Classe une transaction via la meilleure `ClassificationRule` et écrit
    `transaction.category_id`.

    Étape 3 Task 5 : remplace le moteur `mappings`/`find_best_mapping` par
    `classification_rules`/`find_matching_rule` (Task 3). Signature conservée
    (3e arg optionnel = liste de règles, ex-mappings) pour ne pas casser les
    appelants qui pré-chargent leurs règles en batch.

    Args:
        transaction: Transaction à classer
        db: Session de base de données
        rules: Liste de règles (optionnel, sera chargée depuis DB — bien +
            globales — si non fournie)

    Returns:
        La règle retenue, ou None si aucune règle ne correspond (transaction
        non classée, category_id NULL).
    """
    if rules is None:
        rules = _rules_for_property(db, transaction.property_id)
    else:
        # Filtrer les règles fournies pour ne garder que celles applicables à
        # cette propriété (règles du bien + règles globales), au cas où
        # l'appelant aurait chargé un lot couvrant plusieurs propriétés.
        rules = [r for r in rules
                 if r.property_id == transaction.property_id or r.property_id is None]

    match = find_matching_rule(transaction.nom, rules)
    transaction.category_id = match.category_id if match else None

    # Le commit est normalement fait par l'appelant en batch, mais on commit ici
    # pour garantir la persistance des appels isolés (création/édition unitaire).
    try:
        db.commit()
    except Exception as e:
        # Si le commit échoue (par exemple si déjà commité en amont), on continue.
        logger.debug(f"[enrich_transaction] Commit échoué (peut être normal): {e}")

    return match


def enrich_all_transactions(db: Session, property_id: Optional[int] = None) -> Tuple[int, int]:
    """
    Enrichit toutes les transactions qui n'ont pas encore été enrichies.

    Args:
        db: Session de base de données
        property_id: ID de la propriété (optionnel, si fourni, enrichit uniquement les transactions de cette propriété)

    Returns:
        Tuple (nombre de transactions enrichies, nombre de transactions déjà enrichies)
    """
    # Récupérer toutes les transactions (filtrées par property_id si fourni)
    if property_id:
        transactions = db.query(Transaction).filter(Transaction.property_id == property_id).all()
    else:
        # Mode legacy : toutes les transactions (pour compatibilité)
        transactions = db.query(Transaction).all()

    enriched_count = 0
    already_enriched_count = 0
    rules_cache: dict[Optional[int], list[ClassificationRule]] = {}

    for transaction in transactions:
        pid = transaction.property_id
        if pid not in rules_cache:
            rules_cache[pid] = _rules_for_property(db, pid)

        # « Déjà enrichi » = déjà classé (category_id non NULL) avant re-classification.
        # Étape 2 Task 8 : remplace le test d'existence d'une ligne
        # enriched_transactions par l'état de category_id (même sémantique de
        # comptage pour le message de l'endpoint re-enrich).
        was_classified = transaction.category_id is not None
        enrich_transaction(transaction, db, rules_cache[pid])
        if was_classified:
            already_enriched_count += 1
        else:
            enriched_count += 1

    return enriched_count, already_enriched_count


def update_transaction_classification(
    db: Session,
    transaction: Transaction,
    level_1: str | None = None,
    level_2: str | None = None,
    level_3: str | None = None
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Met à jour la classification d'une transaction (écriture de category_id).

    Sémantique « None = ne pas modifier ce niveau » : un argument None conserve
    la valeur courante (dérivée de `transaction.category_id` via le référentiel),
    et non « effacer ». Étape 2 Task 8 : la classification vit dans
    `transactions.category_id` (plus de ligne enriched_transactions).

    Args:
        db: Session de base de données
        transaction: Transaction à mettre à jour
        level_1: Nouvelle valeur pour level_1 (optionnel)
        level_2: Nouvelle valeur pour level_2 (optionnel)
        level_3: Nouvelle valeur pour level_3 (optionnel)

    Returns:
        Le triplet (level_1, level_2, level_3) final appliqué.
    """
    from backend.api.services.classification_read import levels_for_transaction

    # Valeurs courantes dérivées du référentiel (ex-lecture de la ligne enriched).
    cur_level_1, cur_level_2, cur_level_3 = levels_for_transaction(transaction)
    final_level_1 = level_1 if level_1 is not None else cur_level_1
    final_level_2 = level_2 if level_2 is not None else cur_level_2
    final_level_3 = level_3 if level_3 is not None else cur_level_3

    assign_category(db, transaction, final_level_1, final_level_2, final_level_3)

    db.commit()
    db.refresh(transaction)

    return (final_level_1, final_level_2, final_level_3)


def create_or_update_mapping_from_classification(
    db: Session,
    transaction_name: str,
    level_1: str,
    level_2: str,
    level_3: str | None = None,
    property_id: int | None = None
) -> Mapping:
    """
    Crée ou met à jour un mapping basé sur une classification manuelle.
    
    Le mapping est la source de vérité. Si un mapping existe déjà avec le même nom
    pour la même propriété, on le met à jour. Sinon, on en crée un nouveau.
    
    **Validation Step 5.4** : La combinaison (level_1, level_2, level_3) doit être validée
    contre allowed_mappings avant de créer/mettre à jour le mapping.
    
    Args:
        db: Session de base de données
        transaction_name: Nom de la transaction
        level_1: Catégorie principale
        level_2: Sous-catégorie
        level_3: Détail spécifique (optionnel)
        property_id: ID de la propriété (obligatoire pour l'isolation multi-propriétés)
    
    Returns:
        Le mapping créé ou mis à jour
    
    Raises:
        ValueError: Si la combinaison n'est pas autorisée ou si property_id n'est pas fourni
    """
    if property_id is None:
        raise ValueError("property_id est obligatoire pour créer/mettre à jour un mapping")
    
    # Validation contre allowed_mappings (Step 5.4)
    # Valider que level_3 est dans la liste fixe si fourni
    if level_3 and not validate_level3_value(level_3):
        raise ValueError(f"La valeur level_3 '{level_3}' n'est pas autorisée. Valeurs autorisées : Passif, Produits, Emprunt, Charges Déductibles, Actif")
    
    # Valider que la combinaison existe dans allowed_mappings pour cette propriété
    if not validate_mapping(db, level_1, level_2, level_3, property_id):
        raise ValueError(f"La combinaison (level_1='{level_1}', level_2='{level_2}', level_3='{level_3}') n'est pas autorisée pour cette propriété. Veuillez utiliser une combinaison valide depuis les mappings autorisés.")
    
    # Chercher un mapping existant avec le même nom ET la même propriété
    existing_mapping = db.query(Mapping).filter(
        Mapping.nom == transaction_name,
        Mapping.property_id == property_id
    ).first()
    
    if existing_mapping:
        # Mettre à jour le mapping existant
        existing_mapping.level_1 = level_1
        existing_mapping.level_2 = level_2
        existing_mapping.level_3 = level_3
        db.commit()
        db.refresh(existing_mapping)
        logger.info(f"[enrichment_service] Mapping mis à jour: id={existing_mapping.id}, nom={transaction_name}, property_id={property_id}")
        return existing_mapping
    else:
        # Créer un nouveau mapping
        new_mapping = Mapping(
            property_id=property_id,
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
        logger.info(f"[enrichment_service] Mapping créé: id={new_mapping.id}, nom={transaction_name}, property_id={property_id}")
        return new_mapping

