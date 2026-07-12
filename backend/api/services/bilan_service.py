"""
Service de calcul du bilan.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce service implémente la logique de calcul du bilan :
- Filtrage par level_3 (appliqué en premier)
- Mapping level_1 vers catégories comptables
- Calcul des catégories normales depuis transactions enrichies
- Calcul des catégories spéciales (amortissements cumulés, compte bancaire, résultat exercice, etc.)
- Calcul des totaux par niveau (A, B, C)
- Validation de l'équilibre ACTIF = PASSIF
"""

import json
import logging
from datetime import date
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, exists

from backend.database.models import (
    Transaction,
    Category,
    CategoryGroup,
    BilanMapping,
    BilanMappingCategory,
    BilanConfig,
    AmortizationResult,
    LoanPayment,
    LoanConfig,
    CompteResultatOverride
)
from backend.api.services.compte_resultat_service import calculate_compte_resultat
from backend.api.services.category_service import (
    NATURE_BY_LABEL,
    resolve_categories_for_labels,
)

logger = logging.getLogger(__name__)

# Étape 2 Task 6 : les lignes spéciales du bilan sont calculées par le service
# (amortissements cumulés, compte bancaire, résultat/report de l'exercice,
# capital restant dû) et dispatchées par un `line_code` stable. Le
# `special_source` legacy reste en fallback pendant la transition (colonne
# morte supprimée en Task 8). Codes ↔ sources historiques :
#   AMORT_CUMULES       ← amortizations | amortization_result
#   COMPTE_BANCAIRE     ← transactions
#   RESULTAT_EXERCICE   ← compte_resultat
#   REPORT_A_NOUVEAU    ← compte_resultat_cumul
#   CAPITAL_RESTANT_DU  ← loan_payments
LINE_CODE_AMORT_CUMULES = "AMORT_CUMULES"
LINE_CODE_COMPTE_BANCAIRE = "COMPTE_BANCAIRE"
LINE_CODE_RESULTAT_EXERCICE = "RESULTAT_EXERCICE"
LINE_CODE_REPORT_A_NOUVEAU = "REPORT_A_NOUVEAU"
LINE_CODE_CAPITAL_RESTANT_DU = "CAPITAL_RESTANT_DU"

# Correspondance special_source (legacy) → line_code stable. Utilisée par la
# migration pour poser les codes, et ici comme fallback de dispatch.
LINE_CODE_BY_SPECIAL_SOURCE = {
    "amortizations": LINE_CODE_AMORT_CUMULES,
    "amortization_result": LINE_CODE_AMORT_CUMULES,
    "transactions": LINE_CODE_COMPTE_BANCAIRE,
    "compte_resultat": LINE_CODE_RESULTAT_EXERCICE,
    "compte_resultat_cumul": LINE_CODE_REPORT_A_NOUVEAU,
    "loan_payments": LINE_CODE_CAPITAL_RESTANT_DU,
}

# Label `level_1` (référentiel) dont la SOMME des transactions cumulées définit
# le montant du crédit accordé (déblocage d'emprunt) pour le calcul du capital
# restant dû. Provenance : historiquement en dur dans
# calculate_capital_restant_du (magic string level_1 == ...). Résolu via le
# référentiel (category_id) — étape 2 Task 6. L'externalisation en config
# (fiscalité) n'interviendra, si nécessaire, qu'à l'étape 6.
CREDIT_DISBURSEMENT_CATEGORY_LABEL = "Dettes financières (emprunt bancaire)"


def line_code_for_mapping(mapping: BilanMapping) -> Optional[str]:
    """Code de ligne spéciale d'un mapping : `line_code` prioritaire (stable),
    dérivé de `special_source` en fallback (transition Task 6)."""
    code = getattr(mapping, "line_code", None)
    if code:
        return code
    return LINE_CODE_BY_SPECIAL_SOURCE.get(mapping.special_source)


def _natures_from_level_3_values(level_3_values: List[str]) -> List[str]:
    """Traduit les labels level_3 (ex: 'Actif') en natures de groupe (ex:
    'actif'). Les labels non traduisibles (ex: 'TEST_L3_VALUE') sont
    simplement absents du filtre — équivalent au comportement historique où
    un level_3 ne correspondant à aucune transaction ne filtrait rien."""
    return [NATURE_BY_LABEL[label] for label in level_3_values if label in NATURE_BY_LABEL]


def sync_bilan_mapping_categories(db: Session, mapping: BilanMapping,
                                  level_1_values_json: Optional[str]):
    """Reconstruit la liaison `bilan_mapping_categories` d'un mapping à partir
    des labels `level_1_values` (dual-write étape 2 Task 6).

    Idempotent : remplace intégralement les liaisons existantes par celles
    résolues depuis les labels. Les labels non résolus sont journalisés (jamais
    devinés) et absents de la liaison. Retourne (category_ids, unresolved)."""
    try:
        labels = json.loads(level_1_values_json) if level_1_values_json else []
    except (json.JSONDecodeError, TypeError):
        labels = []

    category_ids, unresolved = resolve_categories_for_labels(db, labels, mapping.property_id)
    if unresolved:
        logger.warning(
            f"[BilanService] sync_bilan_mapping_categories - labels non résolus "
            f"pour mapping {mapping.id} (property {mapping.property_id}): {unresolved}"
        )

    existing = {link.category_id: link for link in mapping.category_links}
    wanted = set(category_ids)
    for cat_id, link in list(existing.items()):
        if cat_id not in wanted:
            mapping.category_links.remove(link)
    for cat_id in wanted:
        if cat_id not in existing:
            mapping.category_links.append(BilanMappingCategory(category_id=cat_id))
    return category_ids, unresolved


def labels_from_bilan_mapping_categories(mapping: BilanMapping) -> Optional[str]:
    """Reconstruit le JSON de labels `level_1_values` depuis la liaison (source
    de vérité étape 2 Task 6) pour les réponses GET. Ordre déterministe (trié).
    Retourne None pour les lignes spéciales (aucune liaison, level_1_values
    historiquement NULL) afin de préserver la sérialisation existante."""
    if mapping.is_special:
        return None
    labels = sorted(link.category.label for link in mapping.category_links)
    return json.dumps(labels, ensure_ascii=False)


def get_mappings(db: Session, property_id: int) -> List[BilanMapping]:
    """
    Charger tous les mappings depuis la table pour une propriété.
    
    Args:
        db: Session de base de données
        property_id: ID de la propriété
    
    Returns:
        Liste des mappings configurés
    """
    logger.info(f"[BilanService] get_mappings - property_id={property_id}")
    return db.query(BilanMapping).filter(
        BilanMapping.property_id == property_id
    ).order_by(
        BilanMapping.type,
        BilanMapping.sub_category,
        BilanMapping.category_name
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
    logger.info(f"[BilanService] get_level_3_values - property_id={property_id}")
    config = db.query(BilanConfig).filter(BilanConfig.property_id == property_id).first()
    if not config or not config.level_3_values:
        return []
    
    try:
        return json.loads(config.level_3_values)
    except (json.JSONDecodeError, TypeError):
        return []


def calculate_normal_category(
    db: Session,
    year: int,
    mapping: BilanMapping,
    level_3_values: List[str],
    property_id: int
) -> float:
    """
    Calculer le montant cumulé d'une catégorie normale depuis les transactions enrichies.
    
    Logique :
    1. Filtrer par level_3 (seules les transactions avec level_3 dans level_3_values)
    2. Filtrer par date (toutes les transactions jusqu'à la fin de l'année - CUMUL)
    3. Filtrer par level_1 (selon level_1_values du mapping)
    4. Filtrer par property_id
    5. Sommer les montants (cumul depuis le début jusqu'à l'année)
    
    Pour les immobilisations et autres catégories normales, on calcule le cumul :
    - Année 2021 : somme de toutes les transactions jusqu'au 31/12/2021
    - Année 2022 : somme de toutes les transactions jusqu'au 31/12/2022 (inclut 2021)
    - etc.
    
    Args:
        db: Session de base de données
        year: Année jusqu'à laquelle cumuler
        mapping: Mapping de la catégorie
        level_3_values: Liste des valeurs level_3 à considérer
        property_id: ID de la propriété
    
    Returns:
        Montant cumulé pour cette catégorie jusqu'à l'année
    """
    logger.info(f"[BilanService] calculate_normal_category - year={year}, property_id={property_id}")
    
    if not level_3_values:
        return 0.0

    # Lecture par category_id (liaison bilan_mapping_categories) + filtre par
    # nature de groupe (ex-level_3), au lieu de enriched.level_1 + enriched.level_3
    # (étape 2 Task 7 ; même transformation que calculate_bilan, golden-vérifiée).
    # Note : cette fonction n'est plus appelée dans le chemin API (calculate_bilan
    # calcule les lignes normales en masse) — conservée pour le script d'analyse
    # de performance offline.
    natures = _natures_from_level_3_values(level_3_values)
    if not natures:
        return 0.0

    catids = {link.category_id for link in mapping.category_links}
    if not catids:
        return 0.0

    # Date de fin de l'année (cumul jusqu'à cette date)
    end_date = date(year, 12, 31)

    # Filtrer les transactions par nature (via category_id → groupe), category_id,
    # property_id et cumul jusqu'à la fin de l'année.
    query = db.query(
        func.sum(Transaction.quantite)
    ).join(
        Category, Category.id == Transaction.category_id
    ).join(
        CategoryGroup, CategoryGroup.id == Category.group_id
    ).filter(
        and_(
            Transaction.property_id == property_id,
            CategoryGroup.nature.in_(natures),
            Transaction.category_id.in_(catids),
            Transaction.date <= end_date  # Cumul jusqu'à la fin de l'année
        )
    )

    result = query.scalar()
    if result is None:
        return 0.0
    
    # Pour le bilan, les montants doivent être positifs (actifs/passifs)
    # 
    # Logique selon le type (ACTIF ou PASSIF) :
    # - Pour ACTIF : si la somme est négative, retourner 0 (on ne peut pas avoir un actif négatif)
    # - Pour PASSIF : si la somme est négative, retourner 0 (on ne peut pas avoir une dette négative)
    # - Sinon, retourner la valeur absolue pour s'assurer que c'est positif
    #
    # Cas particulier : certaines catégories ont des transactions avec signes mixtes :
    # - Exemple "Cautions reçues" : paiements (positifs) - remboursements (négatifs) = montant net dû
    # - Si le résultat est négatif, cela signifie qu'on a remboursé plus qu'on a reçu, donc la dette = 0
    
    if result < 0:
        # Si la somme est négative, on ne peut pas avoir un actif/passif négatif
        return 0.0
    
    # Si la somme est positive, retourner la valeur absolue (pour gérer les cas où les transactions
    # sont toutes négatives mais représentent un actif/passif positif, comme pour les immobilisations)
    return abs(result)


def calculate_amortizations_cumul(
    db: Session,
    year: int,
    property_id: int
) -> float:
    """
    Calculer le cumul des amortissements jusqu'à l'année en cours pour une propriété.
    
    Logique :
    - Récupérer tous les amortissements de toutes les années <= year
    - Filtrer par property_id via la transaction associée
    - Sommer les montants (qui sont déjà négatifs)
    - Retourner la valeur négative (diminution de l'actif)
    
    Args:
        db: Session de base de données
        year: Année jusqu'à laquelle cumuler
        property_id: ID de la propriété
    
    Returns:
        Cumul des amortissements (négatif, car diminution de l'actif)
    """
    logger.info(f"[BilanService] calculate_amortizations_cumul - year={year}, property_id={property_id}")
    
    # JOIN avec Transaction pour filtrer par property_id
    result = db.query(
        func.sum(AmortizationResult.amount)
    ).join(
        Transaction, AmortizationResult.transaction_id == Transaction.id
    ).filter(
        and_(
            AmortizationResult.year <= year,
            Transaction.property_id == property_id
        )
    ).scalar()
    
    return result if result is not None else 0.0


def calculate_compte_bancaire(
    db: Session,
    year: int,
    property_id: int
) -> float:
    """
    Calculer le solde bancaire au 31/12 de l'année pour une propriété.
    
    Logique :
    - Récupérer la dernière transaction de l'année (ou avant si aucune transaction en décembre)
    - Filtrer par property_id
    - Utiliser le solde de cette transaction
    
    Args:
        db: Session de base de données
        year: Année à calculer
        property_id: ID de la propriété
    
    Returns:
        Solde bancaire au 31/12 (positif)
    """
    logger.info(f"[BilanService] calculate_compte_bancaire - year={year}, property_id={property_id}")
    
    # Date de fin de l'année
    end_date = date(year, 12, 31)
    
    # Récupérer la dernière transaction jusqu'à la fin de l'année pour cette propriété
    last_transaction = db.query(Transaction).filter(
        and_(
            Transaction.property_id == property_id,
            Transaction.date <= end_date
        )
    ).order_by(
        Transaction.date.desc(),
        Transaction.id.desc()
    ).first()
    
    if not last_transaction:
        return 0.0
    
    return last_transaction.solde if last_transaction.solde is not None else 0.0


def calculate_resultat_exercice(
    db: Session,
    year: int,
    property_id: int,
    compte_resultat_view_id: Optional[int] = None,
    cr_cache: Optional[Dict[int, Dict]] = None
) -> float:
    """
    Calculer le résultat de l'exercice pour une année et une propriété.
    
    Logique :
    - Chercher un override pour l'année et la propriété (si existe, l'utiliser)
    - Sinon : utiliser le résultat net du compte de résultat
    
    Args:
        db: Session de base de données
        year: Année à calculer
        property_id: ID de la propriété
        compte_resultat_view_id: ID de la vue compte de résultat (optionnel, non utilisé pour l'instant)
    
    Returns:
        Résultat de l'exercice (bénéfice positif, perte négative)
    """
    logger.info(f"[BilanService] calculate_resultat_exercice - year={year}, property_id={property_id}")
    
    # Chercher un override pour l'année et la propriété
    override = db.query(CompteResultatOverride).filter(
        and_(
            CompteResultatOverride.year == year,
            CompteResultatOverride.property_id == property_id
        )
    ).first()
    
    if override:
        return override.override_value

    # Sinon, calculer depuis le compte de résultat (mémoïsé par année si dispo)
    if cr_cache is not None and year in cr_cache:
        compte_resultat = cr_cache[year]
    else:
        compte_resultat = calculate_compte_resultat(db, year, property_id=property_id)
        if cr_cache is not None:
            cr_cache[year] = compte_resultat
    return compte_resultat.get("resultat_net", 0.0)


def calculate_report_a_nouveau(
    db: Session,
    year: int,
    property_id: int,
    cr_cache: Optional[Dict[int, Dict]] = None
) -> float:
    """
    Calculer le report à nouveau (cumul des résultats des années précédentes) pour une propriété.
    
    Logique :
    - Cumuler les résultats de toutes les années < year qui ont des transactions
    - Première année : 0 (pas de report)
    
    Args:
        db: Session de base de données
        year: Année à calculer
        property_id: ID de la propriété
    
    Returns:
        Report à nouveau (cumul des résultats précédents)
    """
    logger.info(f"[BilanService] calculate_report_a_nouveau - year={year}, property_id={property_id}")
    
    # Trouver la première année avec des transactions pour cette propriété
    first_transaction = db.query(func.min(Transaction.date)).filter(
        Transaction.property_id == property_id
    ).scalar()
    if not first_transaction:
        return 0.0
    
    first_year = first_transaction.year if hasattr(first_transaction, 'year') else first_transaction
    
    if year <= first_year:
        return 0.0
    
    # OPTIMISATION: Calculer tous les résultats en une seule fois au lieu de boucler
    # Récupérer tous les overrides d'un coup pour cette propriété
    overrides = db.query(CompteResultatOverride).filter(
        and_(
            CompteResultatOverride.property_id == property_id,
            CompteResultatOverride.year >= first_year,
            CompteResultatOverride.year < year
        )
    ).all()
    override_dict = {o.year: o.override_value for o in overrides}
    
    # Calculer les années qui n'ont pas d'override
    total = 0.0
    years_to_calculate = []
    for prev_year in range(first_year, year):
        if prev_year in override_dict:
            total += override_dict[prev_year]
        else:
            years_to_calculate.append(prev_year)
    
    # Calculer les années sans override en une seule fois si possible
    if years_to_calculate:
        # Pour chaque année, calculer le compte de résultat
        # Note: On pourrait optimiser davantage en calculant toutes les années en une fois
        # mais pour l'instant, on garde la logique simple
        for prev_year in years_to_calculate:
            if cr_cache is not None and prev_year in cr_cache:
                compte_resultat = cr_cache[prev_year]
            else:
                compte_resultat = calculate_compte_resultat(db, prev_year, property_id=property_id)
                if cr_cache is not None:
                    cr_cache[prev_year] = compte_resultat
            total += compte_resultat.get("resultat_net", 0.0)
    
    return total


def calculate_capital_restant_du(
    db: Session,
    year: int,
    property_id: int
) -> float:
    """
    Calculer le capital restant dû au 31/12 de l'année pour une propriété.
    
    LOGIQUE :
    - Le montant du crédit accordé = somme des transactions avec level_1 = "Dettes financières (emprunt bancaire)" (cumul jusqu'au 31/12)
    - Le capital remboursé = cumul des remboursements de capital de TOUS les crédits actifs jusqu'au 31/12
    - Capital restant dû = Montant transactions - Capital remboursé
    
    IMPORTANT: 
    - On utilise les TRANSACTIONS comme source principale (pas LoanConfig.credit_amount)
    - On déduit le capital remboursé depuis les pages crédits (LoanPayment)
    - Si aucune transaction n'est trouvée, retourner 0
    
    Args:
        db: Session de base de données
        year: Année à calculer
        property_id: ID de la propriété
    
    Returns:
        Capital restant dû au 31/12 (positif, car dette)
    """
    logger.info(f"[BilanService] calculate_capital_restant_du - year={year}, property_id={property_id}")
    
    # Date de fin de l'année
    end_date = date(year, 12, 31)
    
    # Récupérer tous les crédits actifs pour cette propriété : un crédit est
    # considéré actif pour l'année N s'il a au moins un LoanPayment daté au
    # plus tard le 31/12/N. `LoanConfig.loan_start_date` n'est PAS fiable
    # (voir Tâche 4 : il peut être postérieur à l'échéancier réel, ex. Evry
    # où loan_start_date=2026-05-08 alors que les paiements démarrent en
    # 2021), donc on ne s'appuie plus dessus pour ce filtre.
    # On a besoin de cette liste pour filtrer les paiements
    active_loans = db.query(LoanConfig).filter(
        and_(
            LoanConfig.property_id == property_id,
            exists().where(
                and_(
                    LoanPayment.property_id == property_id,
                    LoanPayment.loan_name == LoanConfig.name,
                    LoanPayment.date <= end_date
                )
            )
        )
    ).all()
    
    # Calculer le montant du crédit accordé depuis les transactions réelles.
    # Étape 2 Task 6 : la catégorie de déblocage d'emprunt est résolue via le
    # référentiel (category_id) à partir du label stable
    # CREDIT_DISBURSEMENT_CATEGORY_LABEL, au lieu du filtre enriched.level_1.
    credit_category_ids, unresolved = resolve_categories_for_labels(
        db, [CREDIT_DISBURSEMENT_CATEGORY_LABEL], property_id
    )
    if unresolved:
        logger.warning(
            f"[BilanService] calculate_capital_restant_du - label de déblocage "
            f"d'emprunt non résolu: {unresolved}"
        )

    if credit_category_ids:
        credit_amount_from_transactions = db.query(
            func.sum(Transaction.quantite)
        ).filter(
            and_(
                Transaction.property_id == property_id,
                Transaction.category_id.in_(list(credit_category_ids)),
                Transaction.date <= end_date
            )
        ).scalar()
    else:
        credit_amount_from_transactions = None
    
    # Le montant est négatif dans les transactions (débit), donc on prend la valeur absolue
    credit_amount = abs(credit_amount_from_transactions) if credit_amount_from_transactions is not None else 0.0
    
    # Si aucune transaction, retourner 0
    if credit_amount == 0.0:
        logger.info(f"[BilanService] calculate_capital_restant_du - Aucune transaction trouvée pour {year}, property_id={property_id}. Retour de 0.00 €")
        return 0.0
    
    # Calculer le capital remboursé depuis les pages crédits (LoanPayment)
    # Filtrer par les crédits actifs et la propriété
    if active_loans:
        active_loan_names = [loan.name for loan in active_loans]
        
        # Capital remboursé total de tous les crédits actifs de cette propriété
        capital_paid = db.query(
            func.sum(LoanPayment.capital)
        ).filter(
            and_(
                LoanPayment.property_id == property_id,
                LoanPayment.date <= end_date,
                LoanPayment.loan_name.in_(active_loan_names)
            )
        ).scalar()
    else:
        # Si aucun crédit actif, ne pas inclure de paiements
        capital_paid = 0.0
    
    capital_paid = capital_paid if capital_paid is not None else 0.0
    
    # Capital restant dû = Montant transactions - Capital remboursé
    remaining = credit_amount - capital_paid
    
    # Debug: Afficher le calcul
    logger.info(f"[BilanService] calculate_capital_restant_du - Calcul pour {year}, property_id={property_id}:")
    logger.info(f"  - Montant transactions (catégorie '{CREDIT_DISBURSEMENT_CATEGORY_LABEL}'): {credit_amount:.2f} €")
    logger.info(f"  - Capital remboursé (tous crédits actifs): {capital_paid:.2f} €")
    logger.info(f"  - Capital restant dû: {remaining:.2f} €")
    
    # S'assurer que le résultat est positif (on ne peut pas avoir un capital restant négatif)
    return max(0.0, remaining)


def calculate_bilan(
    db: Session,
    year: int,
    property_id: int,
    mappings: Optional[List[BilanMapping]] = None,
    level_3_values: Optional[List[str]] = None,
    cr_cache: Optional[Dict[int, Dict]] = None
) -> Dict[str, any]:
    """
    Calculer le bilan complet pour une année et une propriété.
    
    Args:
        db: Session de base de données
        year: Année à calculer
        property_id: ID de la propriété
        mappings: Liste des mappings (optionnel, sera chargée depuis DB si non fournie)
        level_3_values: Liste des valeurs level_3 (optionnel, sera chargée depuis config si non fournie)
        cr_cache: Mémoïsation optionnelle {année: résultat compte de résultat}
            partagée sur une requête multi-années. Évite de recalculer le
            compte de résultat pour le résultat de l'exercice et le report à
            nouveau. Portée requête uniquement (ce n'est PAS un cache persistant).

    Returns:
        Dictionnaire avec :
        - categories: Dict[str, float] - Montants par catégorie
        - totals_by_sub_category: Dict[str, float] - Totaux par sous-catégorie
        - totals_by_type: Dict[str, float] - Totaux par type (ACTIF/PASSIF)
        - actif_total: float - Total ACTIF
        - passif_total: float - Total PASSIF
        - difference: float - Différence ACTIF - PASSIF
        - difference_percent: float - Pourcentage de différence
    """
    logger.info(f"[BilanService] calculate_bilan - year={year}, property_id={property_id}")
    
    # Charger les mappings si non fournis
    if mappings is None:
        mappings = get_mappings(db, property_id)
    
    # Charger les level_3_values si non fournis
    if level_3_values is None:
        level_3_values = get_level_3_values(db, property_id)
    
    # Dictionnaire pour stocker les montants par catégorie
    categories = {}
    
    # OPTIMISATION: Calculer toutes les catégories normales en une seule requête.
    # Étape 2 Task 6 : lecture par category_id (liaison) + filtre par nature de
    # groupe (ex-level_3), au lieu de enriched.level_1 + enriched.level_3. Les
    # transactions portent category_id (dual-write Task 4) et category → group →
    # nature reproduit exactement le triplet (level_1, level_2, level_3) : sortie
    # inchangée (garanti par le golden master).
    normal_mappings = [m for m in mappings if not m.is_special]
    if normal_mappings:
        # Date de fin de l'année (cumul jusqu'à cette date)
        end_date = date(year, 12, 31)

        # Natures de groupe issues du filtre level_3 (labels non traduisibles
        # simplement ignorés — ex. 'TEST_L3_VALUE', équivalent à l'ancien
        # level_3.in_ qui ne matchait rien).
        natures = _natures_from_level_3_values(level_3_values)

        # Construire un dictionnaire category_name -> set(category_id) depuis la
        # liaison (remplace level_1_values).
        category_to_catids = {}
        all_cat_ids = set()
        for mapping in normal_mappings:
            catids = {link.category_id for link in mapping.category_links}
            if not catids:
                continue
            category_to_catids[mapping.category_name] = catids
            all_cat_ids.update(catids)

        if all_cat_ids and natures:
            # Une seule requête pour toutes les catégories normales, filtrée par
            # property_id, nature de groupe et category_id (cumul jusqu'à fin d'année).
            query = db.query(
                Transaction.category_id,
                func.sum(Transaction.quantite).label('total')
            ).join(
                Category, Category.id == Transaction.category_id
            ).join(
                CategoryGroup, CategoryGroup.id == Category.group_id
            ).filter(
                and_(
                    Transaction.property_id == property_id,
                    CategoryGroup.nature.in_(natures),
                    Transaction.category_id.in_(list(all_cat_ids)),
                    Transaction.date <= end_date
                )
            ).group_by(Transaction.category_id)

            results = query.all()

            # Initialiser toutes les catégories normales à 0
            for mapping in normal_mappings:
                categories[mapping.category_name] = 0.0

            # Répartir les résultats par catégorie (chaque category_id peut appartenir à plusieurs catégories)
            # IMPORTANT: On additionne d'abord les montants bruts (avec leurs signes), puis on applique la logique
            # à la somme finale. Cela permet de gérer correctement les catégories avec transactions mixtes
            # (ex: "Cautions reçues" avec paiements positifs et remboursements négatifs)
            for cat_id, total in results:
                if cat_id is not None and total is not None:
                    # Trouver toutes les catégories qui utilisent ce category_id
                    for category_name, catid_set in category_to_catids.items():
                        if cat_id in catid_set:
                            # Additionner les montants bruts (avec leurs signes)
                            categories[category_name] += total

            # Appliquer la logique de signe à la somme finale de chaque catégorie
            # Construire un dictionnaire category_name -> type (ACTIF/PASSIF) pour déterminer la logique
            category_to_type = {}
            for mapping in normal_mappings:
                category_to_type[mapping.category_name] = mapping.type
            
            for category_name in categories:
                result = categories[category_name]
                category_type = category_to_type.get(category_name, "ACTIF")  # Par défaut ACTIF
                
                if category_type == "ACTIF":
                    # Pour les ACTIFS : toujours retourner la valeur absolue (positif)
                    # Les transactions sont souvent négatives (débits), mais l'actif doit être positif
                    categories[category_name] = abs(result) if result is not None else 0.0
                else:
                    # Pour les PASSIFS : si négatif → 0 (on ne peut pas avoir une dette négative)
                    # Sinon, valeur absolue pour garantir un montant positif
                    if result < 0:
                        categories[category_name] = 0.0
                    else:
                        categories[category_name] = abs(result) if result is not None else 0.0
    
    # Calculer les catégories spéciales (une par une, elles sont peu nombreuses).
    # Étape 2 Task 6 : dispatch par `line_code` stable, `special_source` en
    # fallback pendant la transition (cf. line_code_for_mapping).
    for mapping in mappings:
        if mapping.is_special:
            category_name = mapping.category_name
            code = line_code_for_mapping(mapping)
            if code == LINE_CODE_AMORT_CUMULES:
                amount = calculate_amortizations_cumul(db, year, property_id)
            elif code == LINE_CODE_COMPTE_BANCAIRE:
                amount = calculate_compte_bancaire(db, year, property_id)
            elif code == LINE_CODE_RESULTAT_EXERCICE:
                amount = calculate_resultat_exercice(
                    db, year, property_id, mapping.compte_resultat_view_id, cr_cache=cr_cache
                )
            elif code == LINE_CODE_REPORT_A_NOUVEAU:
                amount = calculate_report_a_nouveau(db, year, property_id, cr_cache=cr_cache)
            elif code == LINE_CODE_CAPITAL_RESTANT_DU:
                amount = calculate_capital_restant_du(db, year, property_id)
            else:
                amount = 0.0
            categories[category_name] = amount
    
    # Calculer les totaux par sous-catégorie
    totals_by_sub_category = {}
    for mapping in mappings:
        sub_category = mapping.sub_category
        if sub_category not in totals_by_sub_category:
            totals_by_sub_category[sub_category] = 0.0
        totals_by_sub_category[sub_category] += categories.get(mapping.category_name, 0.0)
    
    # Calculer les totaux par type (ACTIF/PASSIF)
    totals_by_type = {}
    for mapping in mappings:
        type_name = mapping.type
        if type_name not in totals_by_type:
            totals_by_type[type_name] = 0.0
        totals_by_type[type_name] += categories.get(mapping.category_name, 0.0)
    
    # Totaux ACTIF et PASSIF
    actif_total = totals_by_type.get("ACTIF", 0.0)
    passif_total = totals_by_type.get("PASSIF", 0.0)
    
    # Calculer la différence et le pourcentage
    difference = actif_total - passif_total
    if passif_total != 0:
        difference_percent = (difference / passif_total) * 100
    elif actif_total != 0:
        difference_percent = 100.0  # Si passif = 0 mais actif > 0
    else:
        difference_percent = 0.0  # Si les deux sont à 0
    
    return {
        "categories": categories,
        "totals_by_sub_category": totals_by_sub_category,
        "totals_by_type": totals_by_type,
        "actif_total": actif_total,
        "passif_total": passif_total,
        "difference": difference,
        "difference_percent": difference_percent
    }


