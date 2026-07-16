"""
Service de calcul du compte de résultat.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce service implémente la logique de calcul du compte de résultat :
- Filtrage par level_3 (appliqué en premier)
- Mapping level_1 vers catégories comptables
- Calcul des produits et charges d'exploitation
- Récupération des amortissements depuis amortization_result
- Calcul du coût du financement depuis loan_payments
- Application du Pro Rata (MAX réel/prévu) si activé (Phase 11bis)

Phase 11 : Toutes les fonctions acceptent property_id pour l'isolation multi-propriétés.
Phase 11bis : Support Pro Rata & Forecast pour les prévisions annuelles.
"""

import json
import logging
from datetime import date
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from backend.database.models import (
    Transaction,
    Category,
    CategoryGroup,
    CompteResultatMapping,
    CompteResultatMappingCategory,
    CompteResultatConfig,
    AmortizationResult,
    LoanPayment,
    LoanConfig
)
from backend.api.services.category_service import NATURE_BY_LABEL

# Logger configuration
logger = logging.getLogger(__name__)

# Étape 2 Task 5 : les 2 lignes calculées (amortissements + coût du
# financement) sont INJECTÉES par le service (get_amortissements /
# get_cout_financement) et non lues depuis la config. Elles sont exclues des
# lignes de config lors du calcul produits/charges. Détection par `line_code`
# d'abord (stable), nom français en fallback (aucune ligne de config ne porte
# ces codes aujourd'hui — la colonne line_code reste NULL, cf. migration).
SPECIAL_LINE_CODES = ("AMORT", "COUT_FINANCEMENT")
SPECIAL_LINE_NAMES = (
    "Charges d'amortissements",
    "Coût du financement (hors remboursement du capital)",
)


def _is_special_line(mapping: CompteResultatMapping) -> bool:
    """True si le mapping est une des 2 lignes calculées (à exclure du calcul
    produits/charges). line_code prioritaire, nom français en fallback."""
    if getattr(mapping, "line_code", None) in SPECIAL_LINE_CODES:
        return True
    return mapping.category_name in SPECIAL_LINE_NAMES


def _natures_from_level_3_values(level_3_values: List[str]) -> List[str]:
    """Traduit les labels level_3 (ex: 'Charges Déductibles') en natures de
    groupe (ex: 'charges_deductibles'). Les labels non traduisibles sont
    simplement absents du filtre (équivalent au comportement historique : un
    label ne correspondant à rien ne filtre rien en entrée)."""
    return [NATURE_BY_LABEL[label] for label in level_3_values if label in NATURE_BY_LABEL]


def _category_ids_for_mappings(category_mappings: List[CompteResultatMapping]) -> set:
    """Union des category_id liés (liaison) de tous les mappings d'une ligne CR."""
    ids = set()
    for mapping in category_mappings:
        for link in mapping.category_links:
            ids.add(link.category_id)
    return ids


def sync_mapping_categories(db: Session, mapping: CompteResultatMapping,
                            level_1_values_json: Optional[str]):
    """Reconstruit la liaison `compte_resultat_mapping_categories` d'un mapping
    à partir des labels `level_1_values` (dual-write étape 2 Task 5).

    Idempotent : remplace intégralement les liaisons existantes par celles
    résolues depuis les labels. Les labels non résolus sont journalisés (jamais
    devinés) et absents de la liaison. Retourne (category_ids, unresolved)."""
    from backend.api.services.category_service import resolve_categories_for_labels

    try:
        labels = json.loads(level_1_values_json) if level_1_values_json else []
    except (json.JSONDecodeError, TypeError):
        labels = []

    category_ids, unresolved = resolve_categories_for_labels(db, labels, mapping.property_id)
    if unresolved:
        logger.warning(
            f"[CompteResultatService] sync_mapping_categories - labels non résolus "
            f"pour mapping {mapping.id} (property {mapping.property_id}): {unresolved}"
        )

    existing = {link.category_id: link for link in mapping.category_links}
    wanted = set(category_ids)
    for cat_id, link in list(existing.items()):
        if cat_id not in wanted:
            mapping.category_links.remove(link)
    for cat_id in wanted:
        if cat_id not in existing:
            mapping.category_links.append(
                CompteResultatMappingCategory(category_id=cat_id)
            )
    return category_ids, unresolved


def labels_from_mapping_categories(mapping: CompteResultatMapping) -> str:
    """Reconstruit le JSON de labels `level_1_values` depuis la liaison (source
    de vérité étape 2 Task 5) pour les réponses GET. Ordre déterministe (trié)."""
    labels = sorted(link.category.label for link in mapping.category_links)
    return json.dumps(labels, ensure_ascii=False)


def get_mappings(db: Session, property_id: int) -> List[CompteResultatMapping]:
    """
    Charger tous les mappings depuis la table pour une propriété.
    
    Args:
        db: Session de base de données
        property_id: ID de la propriété
    
    Returns:
        Liste des mappings configurés pour la propriété
    """
    logger.info(f"[CompteResultatService] get_mappings - property_id={property_id}")
    return db.query(CompteResultatMapping).filter(
        CompteResultatMapping.property_id == property_id
    ).all()


def get_level_3_values(db: Session, property_id: int) -> List[str]:
    """
    Récupérer les valeurs level_3 sélectionnées depuis la configuration pour une propriété.
    
    Args:
        db: Session de base de données
        property_id: ID de la propriété
    
    Returns:
        Liste des valeurs level_3 sélectionnées (vide si aucune config)
    """
    logger.info(f"[CompteResultatService] get_level_3_values - property_id={property_id}")
    config = db.query(CompteResultatConfig).filter(
        CompteResultatConfig.property_id == property_id
    ).first()
    if not config or not config.level_3_values:
        return []
    
    try:
        return json.loads(config.level_3_values)
    except (json.JSONDecodeError, TypeError):
        return []


def calculate_produits_exploitation(
    db: Session,
    year: int,
    mappings: List[CompteResultatMapping],
    level_3_values: List[str],
    property_id: int
) -> Dict[str, float]:
    """
    Calculer les produits d'exploitation pour une année donnée.
    
    Logique :
    1. Filtrer d'abord par level_3 (seules les transactions avec level_3 dans level_3_values)
    2. Filtrer par année (date entre 01/01/année et 31/12/année)
    3. Filtrer par property_id
    4. Grouper par catégorie selon les mappings level_1
    5. Sommer les montants par catégorie
    6. Prendre en compte transactions positives ET négatives (revenus positifs - remboursements négatifs)
    
    Args:
        db: Session de base de données
        year: Année à calculer
        mappings: Liste des mappings configurés
        level_3_values: Liste des valeurs level_3 à considérer
        property_id: ID de la propriété
    
    Returns:
        Dictionnaire {category_name: amount} pour les produits d'exploitation
    """
    logger.info(f"[CompteResultatService] calculate_produits_exploitation - year={year}, property_id={property_id}")
    
    if not level_3_values:
        # Si aucune valeur level_3 sélectionnée, retourner des montants vides
        return {}

    # INVARIANT (étape 2 Task 8, validé par
    # migrations/validate_bilan_config_natures.py) : toute config CR non vide a
    # ≥1 label traduisible → `natures` non vide dès que `level_3_values` l'est.
    # Une catégorie sans montant n'apparaît pas dans le résultat de toute façon,
    # donc « natures vide » (config non vide non traduisible, impossible sur
    # données réelles) et « aucune transaction » donnent le même dict vide.
    natures = _natures_from_level_3_values(level_3_values)
    if not natures:
        # Aucun label level_3 traduisible en nature -> aucun filtre positif
        return {}

    # Date de début et fin de l'année
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    # Filtrer les transactions par nature (via category_id -> categories ->
    # category_groups), année ET property_id. category_id remplace
    # enriched.level_1 ; la nature du groupe remplace enriched.level_3
    # (bijection sur les 5 natures ; sortie byte-identique — étape 2 Task 5).
    query = db.query(
        Transaction.category_id,
        Transaction.quantite
    ).join(
        Category, Category.id == Transaction.category_id
    ).join(
        CategoryGroup, CategoryGroup.id == Category.group_id
    ).filter(
        and_(
            Transaction.property_id == property_id,  # Filtre par property_id
            CategoryGroup.nature.in_(natures),
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.category_id.isnot(None)  # Uniquement les transactions classées
        )
    )

    # Récupérer toutes les transactions filtrées
    transactions = query.all()

    # Grouper par catégorie selon les mappings
    # IMPORTANT : Regrouper tous les mappings d'une même catégorie avec OR pour éviter les doublons
    results = {}

    # Catégories prédéfinies de produits
    PRODUITS_CATEGORIES = [
        'Loyers hors charge encaissés',
        'Charges locatives payées par locataires',
        'Autres revenus',
    ]

    # Déterminer le type si None
    def get_type_for_category(category_name, mapping_type):
        if mapping_type:
            return mapping_type
        # Déterminer automatiquement selon la catégorie
        if category_name in PRODUITS_CATEGORIES:
            return "Produits d'exploitation"
        return "Charges d'exploitation"

    # Grouper les mappings par catégorie
    # IMPORTANT : Filtrer uniquement les mappings de type "Produits d'exploitation"
    mappings_by_category = {}
    for mapping in mappings:
        category_name = mapping.category_name

        # Ignorer les catégories spéciales (amortissements, coût financement)
        if _is_special_line(mapping):
            continue

        # Déterminer le type (automatiquement si None)
        mapping_type = get_type_for_category(category_name, mapping.type)

        # Filtrer uniquement les produits d'exploitation
        if mapping_type != "Produits d'exploitation":
            continue

        if category_name not in mappings_by_category:
            mappings_by_category[category_name] = []
        mappings_by_category[category_name].append(mapping)

    # Pour chaque catégorie, regrouper tous les category_id liés (OR)
    for category_name, category_mappings in mappings_by_category.items():
        all_category_ids = _category_ids_for_mappings(category_mappings)

        if not all_category_ids:
            # Pas de liaison configurée pour cette catégorie
            continue

        # Filtrer les transactions dont le category_id est dans la liste (OR de tous les mappings)
        category_amount = 0.0
        for cat_id, quantite in transactions:
            if cat_id in all_category_ids:
                # Pour les produits : revenus positifs - remboursements négatifs
                category_amount += quantite

        if category_amount != 0.0:
            results[category_name] = category_amount

    return results


def calculate_charges_exploitation(
    db: Session,
    year: int,
    mappings: List[CompteResultatMapping],
    level_3_values: List[str],
    property_id: int
) -> Dict[str, float]:
    """
    Calculer les charges d'exploitation pour une année donnée.
    
    Logique :
    1. Filtrer d'abord par level_3 (seules les transactions avec level_3 dans level_3_values)
    2. Filtrer par année (date entre 01/01/année et 31/12/année)
    3. Filtrer par property_id
    4. Grouper par catégorie selon les mappings level_1
    5. Sommer les montants par catégorie
    6. Prendre en compte transactions positives ET négatives (dépenses négatives - remboursements/crédits positifs)
    
    Args:
        db: Session de base de données
        year: Année à calculer
        mappings: Liste des mappings configurés
        level_3_values: Liste des valeurs level_3 à considérer
        property_id: ID de la propriété
    
    Returns:
        Dictionnaire {category_name: amount} pour les charges d'exploitation
    """
    logger.info(f"[CompteResultatService] calculate_charges_exploitation - year={year}, property_id={property_id}")
    
    if not level_3_values:
        # Si aucune valeur level_3 sélectionnée, retourner des montants vides
        return {}

    # INVARIANT (étape 2 Task 8, validé par
    # migrations/validate_bilan_config_natures.py) : toute config CR non vide a
    # ≥1 label traduisible → `natures` non vide dès que `level_3_values` l'est.
    # Une catégorie sans montant n'apparaît pas dans le résultat de toute façon,
    # donc « natures vide » (config non vide non traduisible, impossible sur
    # données réelles) et « aucune transaction » donnent le même dict vide.
    natures = _natures_from_level_3_values(level_3_values)
    if not natures:
        # Aucun label level_3 traduisible en nature -> aucun filtre positif
        return {}

    # Date de début et fin de l'année
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    # Filtrer les transactions par nature (via category_id -> categories ->
    # category_groups), année ET property_id. category_id remplace
    # enriched.level_1 ; la nature du groupe remplace enriched.level_3
    # (bijection sur les 5 natures ; sortie byte-identique — étape 2 Task 5).
    query = db.query(
        Transaction.category_id,
        Transaction.quantite
    ).join(
        Category, Category.id == Transaction.category_id
    ).join(
        CategoryGroup, CategoryGroup.id == Category.group_id
    ).filter(
        and_(
            Transaction.property_id == property_id,  # Filtre par property_id
            CategoryGroup.nature.in_(natures),
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.category_id.isnot(None)  # Uniquement les transactions classées
        )
    )

    # Récupérer toutes les transactions filtrées
    transactions = query.all()

    # Grouper par catégorie selon les mappings
    # IMPORTANT : Regrouper tous les mappings d'une même catégorie avec OR pour éviter les doublons
    results = {}

    # Catégories prédéfinies de produits
    PRODUITS_CATEGORIES = [
        'Loyers hors charge encaissés',
        'Charges locatives payées par locataires',
        'Autres revenus',
    ]

    # Déterminer le type si None
    def get_type_for_category(category_name, mapping_type):
        if mapping_type:
            return mapping_type
        # Déterminer automatiquement selon la catégorie
        if category_name in PRODUITS_CATEGORIES:
            return "Produits d'exploitation"
        return "Charges d'exploitation"

    # Grouper les mappings par catégorie
    # IMPORTANT : Filtrer uniquement les mappings de type "Charges d'exploitation"
    mappings_by_category = {}
    for mapping in mappings:
        category_name = mapping.category_name

        # Ignorer les catégories spéciales (amortissements, coût financement)
        if _is_special_line(mapping):
            continue

        # Déterminer le type (automatiquement si None)
        mapping_type = get_type_for_category(category_name, mapping.type)

        # Filtrer uniquement les charges d'exploitation
        if mapping_type != "Charges d'exploitation":
            continue

        if category_name not in mappings_by_category:
            mappings_by_category[category_name] = []
        mappings_by_category[category_name].append(mapping)

    # Pour chaque catégorie, regrouper tous les category_id liés (OR)
    for category_name, category_mappings in mappings_by_category.items():
        all_category_ids = _category_ids_for_mappings(category_mappings)

        if not all_category_ids:
            # Pas de liaison configurée pour cette catégorie
            continue

        # Filtrer les transactions dont le category_id est dans la liste (OR de tous les mappings)
        category_amount = 0.0
        for cat_id, quantite in transactions:
            if cat_id in all_category_ids:
                # Pour les charges : dépenses négatives - remboursements/crédits positifs
                category_amount += quantite

        if category_amount != 0.0:
            results[category_name] = category_amount

    return results


def get_amortissements(db: Session, year: int, property_id: int) -> float:
    """
    Récupérer le total d'amortissement pour une année depuis la table amortization_result.
    
    Note: AmortizationResult n'a pas property_id directement, on fait un JOIN via Transaction.
    
    Args:
        db: Session de base de données
        year: Année à calculer
        property_id: ID de la propriété
    
    Returns:
        Total des amortissements pour l'année (somme de toutes les catégories)
    """
    logger.info(f"[CompteResultatService] get_amortissements - year={year}, property_id={property_id}")
    
    # JOIN avec Transaction pour filtrer par property_id
    result = db.query(
        func.sum(AmortizationResult.amount)
    ).join(
        Transaction, Transaction.id == AmortizationResult.transaction_id
    ).filter(
        AmortizationResult.year == year,
        Transaction.property_id == property_id
    ).scalar()
    
    return result if result is not None else 0.0


def get_cout_financement(db: Session, year: int, property_id: int, realized: bool = False) -> float:
    """
    Calculer le coût du financement (intérêts + assurance) pour une année.

    Logique :
    - Récupérer tous les crédits configurés pour la propriété
    - Filtrer loan_payments par année et property_id
    - Gérer le cas d'un seul crédit ou plusieurs crédits
    - Sommer interest + insurance de tous les crédits

    Args:
        db: Session de base de données
        year: Année à calculer
        property_id: ID de la propriété
        realized: si True (bilan = photo réelle), plafonne au dernier vrai
            mouvement bancaire (n'inclut pas les échéances théoriques futures de
            l'année en cours). Si False (CR prévisionnel), année pleine.

    Returns:
        Total du coût du financement (interest + insurance) pour l'année
    """
    logger.info(f"[CompteResultatService] get_cout_financement - year={year}, property_id={property_id}, realized={realized}")

    # Date de début et fin de l'année
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    if realized:
        last_tx_date = db.query(func.max(Transaction.date)).filter(
            Transaction.property_id == property_id
        ).scalar()
        if last_tx_date is not None and last_tx_date < end_date:
            end_date = last_tx_date
    
    # Récupérer les crédits configurés pour la propriété
    loan_configs = db.query(LoanConfig).filter(
        LoanConfig.property_id == property_id
    ).all()
    
    if not loan_configs:
        return 0.0
    
    # Récupérer les noms des crédits configurés
    loan_names = [config.name for config in loan_configs]
    
    # Récupérer uniquement les loan_payments pour l'année, la propriété, et les crédits configurés
    payments = db.query(LoanPayment).filter(
        and_(
            LoanPayment.property_id == property_id,  # Filtre par property_id
            LoanPayment.date >= start_date,
            LoanPayment.date <= end_date,
            LoanPayment.loan_name.in_(loan_names)  # Filtrer par les noms des crédits configurés
        )
    ).all()
    
    # Sommer interest + insurance uniquement des crédits configurés
    total_cost = 0.0
    for payment in payments:
        total_cost += payment.interest + payment.insurance
    
    return total_cost


def calculate_compte_resultat(
    db: Session,
    year: int,
    property_id: int,
    mappings: Optional[List[CompteResultatMapping]] = None,
    level_3_values: Optional[List[str]] = None,
    skip_prorata: bool = False
) -> Dict[str, any]:
    """
    Calculer le compte de résultat complet pour une année et une propriété.
    
    Le compte de résultat est TOUJOURS réel : aucune prévision n'est injectée
    dans les montants (plus de règle MAX(réel, prévu)). Les prévisions sont
    gérées côté affichage. `skip_prorata` ne pilote plus que le mode réalisé
    vs prévisionnel du coût du financement (get_cout_financement).
    
    Args:
        db: Session de base de données
        year: Année à calculer
        property_id: ID de la propriété
        mappings: Liste des mappings (optionnel, sera chargée depuis DB si non fournie)
        level_3_values: Liste des valeurs level_3 (optionnel, sera chargée depuis config si non fournie)
        skip_prorata: pilote uniquement get_cout_financement (réalisé si True). N'affecte plus les produits/charges (toujours réels).
    
    Returns:
        Dictionnaire avec :
        - produits: Dict[str, float] - Produits d'exploitation par catégorie
        - charges: Dict[str, float] - Charges d'exploitation par catégorie
        - amortissements: float - Total des amortissements
        - cout_financement: float - Coût du financement
        - resultat_exploitation: float - Résultat d'exploitation (produits - charges)
        - total_charges_exploitation: float - Total des charges d'exploitation (sans charges d'intérêt)
        - resultat_net: float - Résultat net (résultat d'exploitation - charges d'intérêt)
        - prorata_applied: bool - Indique si le prorata a été appliqué
    """
    logger.info(f"[CompteResultatService] calculate_compte_resultat - year={year}, property_id={property_id}, skip_prorata={skip_prorata}")
    
    # Charger les mappings si non fournis
    if mappings is None:
        mappings = get_mappings(db, property_id)
    
    # Charger les level_3_values si non fournis
    if level_3_values is None:
        level_3_values = get_level_3_values(db, property_id)
    
    # Calculer les produits d'exploitation (valeurs réelles)
    produits = calculate_produits_exploitation(db, year, mappings, level_3_values, property_id)
    
    # Calculer les charges d'exploitation (valeurs réelles)
    charges = calculate_charges_exploitation(db, year, mappings, level_3_values, property_id)
    
    # Ajouter les catégories spéciales (calculées automatiquement)
    amortissements = get_amortissements(db, year, property_id)
    if amortissements != 0.0:
        charges["Charges d'amortissements"] = amortissements
    
    cout_financement = get_cout_financement(db, year, property_id, realized=skip_prorata)
    if cout_financement != 0.0:
        # Affiché en NÉGATIF (c'est une charge), comme les autres charges.
        # La variable cout_financement reste positive pour le calcul du résultat net (soustraite plus bas).
        charges["Coût du financement (hors remboursement du capital)"] = -abs(cout_financement)
    
    # ========== Prévisions (refonte) ==========
    # Le compte de résultat est TOUJOURS réel : on n'injecte plus jamais de
    # "prévu" dans les montants (fini la règle MAX(réel, prévu) qui polluait
    # l'année en cours). Les prévisions — objectif de l'année en cours (badge)
    # et années futures — sont ajoutées côté affichage (frontend), sans jamais
    # modifier une valeur réelle. Le paramètre `skip_prorata` ne sert plus qu'à
    # `get_cout_financement` (réalisé vs prévisionnel du coût du financement).
    prorata_applied = False

    # ========== Calcul des totaux ==========
    # IMPORTANT : Le frontend exclut les charges d'intérêt du total des charges d'exploitation
    total_produits = sum(produits.values())
    
    # Total des charges d'exploitation (exclut les charges d'intérêt)
    # Note: Les charges sont négatives (sorties d'argent), les crédits/remboursements sont positifs
    # On prend abs(sum()) pour que les crédits réduisent correctement le total des charges
    charges_exploitation = {k: v for k, v in charges.items() 
                            if k != "Coût du financement (hors remboursement du capital)"}
    total_charges_exploitation = abs(sum(v for v in charges_exploitation.values() if v))
    
    # Résultat d'exploitation = Produits - Charges d'exploitation (sans charges d'intérêt)
    resultat_exploitation = total_produits - total_charges_exploitation
    
    # Résultat de l'exercice = Résultat d'exploitation - Charges d'intérêt
    resultat_net = resultat_exploitation - cout_financement
    
    # total_charges pour compatibilité (inclut tout, mais ne pas utiliser pour resultat_exploitation)
    total_charges = sum(charges.values())
    
    return {
        "produits": produits,
        "charges": charges,
        "amortissements": amortissements,
        "cout_financement": cout_financement,
        "total_produits": total_produits,
        "total_charges": total_charges,  # Pour compatibilité (inclut tout)
        "total_charges_exploitation": total_charges_exploitation,  # Sans charges d'intérêt
        "resultat_exploitation": resultat_exploitation,
        "resultat_net": resultat_net,
        "prorata_applied": prorata_applied  # Indique si prorata a été appliqué
    }
