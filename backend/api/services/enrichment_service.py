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

from backend.database.models import Transaction, ClassificationRule
from backend.api.services.classification_engine import find_matching_rule

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

