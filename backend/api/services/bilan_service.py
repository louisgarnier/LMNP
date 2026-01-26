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
from datetime import date
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from backend.database.models import (
    Transaction,
    EnrichedTransaction,
    BilanMapping,
    BilanData,
    BilanConfig,
    AmortizationResult,
    LoanPayment,
    LoanConfig,
    CompteResultatData,
    CompteResultatOverride
)
from backend.api.services.compte_resultat_service import calculate_compte_resultat


def get_mappings(db: Session) -> List[BilanMapping]:
    """
    Charger tous les mappings depuis la table.
    
    Args:
        db: Session de base de données
    
    Returns:
        Liste des mappings configurés
    """
    return db.query(BilanMapping).order_by(
        BilanMapping.type,
        BilanMapping.sub_category,
        BilanMapping.category_name
    ).all()


def get_level_3_values(db: Session) -> List[str]:
    """
    Récupérer les valeurs level_3 sélectionnées depuis la configuration.
    
    Args:
        db: Session de base de données
    
    Returns:
        Liste des valeurs level_3 sélectionnées (vide si aucune config)
    """
    config = db.query(BilanConfig).first()
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
    level_3_values: List[str]
) -> float:
    """
    Calculer le montant cumulé d'une catégorie normale depuis les transactions enrichies.
    
    Logique :
    1. Filtrer par level_3 (seules les transactions avec level_3 dans level_3_values)
    2. Filtrer par date (toutes les transactions jusqu'à la fin de l'année - CUMUL)
    3. Filtrer par level_1 (selon level_1_values du mapping)
    4. Sommer les montants (cumul depuis le début jusqu'à l'année)
    
    Pour les immobilisations et autres catégories normales, on calcule le cumul :
    - Année 2021 : somme de toutes les transactions jusqu'au 31/12/2021
    - Année 2022 : somme de toutes les transactions jusqu'au 31/12/2022 (inclut 2021)
    - etc.
    
    Args:
        db: Session de base de données
        year: Année jusqu'à laquelle cumuler
        mapping: Mapping de la catégorie
        level_3_values: Liste des valeurs level_3 à considérer
    
    Returns:
        Montant cumulé pour cette catégorie jusqu'à l'année
    """
    if not level_3_values:
        return 0.0
    
    if not mapping.level_1_values:
        return 0.0
    
    try:
        level_1_values = json.loads(mapping.level_1_values)
    except (json.JSONDecodeError, TypeError):
        return 0.0
    
    if not level_1_values:
        return 0.0
    
    # Date de fin de l'année (cumul jusqu'à cette date)
    end_date = date(year, 12, 31)
    
    # Filtrer les transactions par level_3, level_1 et cumul jusqu'à la fin de l'année
    query = db.query(
        func.sum(Transaction.quantite)
    ).join(
        EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
    ).filter(
        and_(
            EnrichedTransaction.level_3.in_(level_3_values),
            EnrichedTransaction.level_1.in_(level_1_values),
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
    year: int
) -> float:
    """
    Calculer le cumul des amortissements jusqu'à l'année en cours.
    
    Logique :
    - Récupérer tous les amortissements de toutes les années <= year
    - Sommer les montants (qui sont déjà négatifs)
    - Retourner la valeur négative (diminution de l'actif)
    
    Args:
        db: Session de base de données
        year: Année jusqu'à laquelle cumuler
    
    Returns:
        Cumul des amortissements (négatif, car diminution de l'actif)
    """
    result = db.query(
        func.sum(AmortizationResult.amount)
    ).filter(
        AmortizationResult.year <= year
    ).scalar()
    
    return result if result is not None else 0.0


def calculate_compte_bancaire(
    db: Session,
    year: int
) -> float:
    """
    Calculer le solde bancaire au 31/12 de l'année.
    
    Logique :
    - Récupérer la dernière transaction de l'année (ou avant si aucune transaction en décembre)
    - Utiliser le solde de cette transaction
    
    Args:
        db: Session de base de données
        year: Année à calculer
    
    Returns:
        Solde bancaire au 31/12 (positif)
    """
    # Date de fin de l'année
    end_date = date(year, 12, 31)
    
    # Récupérer la dernière transaction jusqu'à la fin de l'année
    last_transaction = db.query(Transaction).filter(
        Transaction.date <= end_date
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
    compte_resultat_view_id: Optional[int] = None
) -> float:
    """
    Calculer le résultat de l'exercice pour une année.
    
    Logique :
    - Chercher un override pour l'année (si existe, l'utiliser)
    - Sinon : utiliser le résultat net du compte de résultat
    
    Args:
        db: Session de base de données
        year: Année à calculer
        compte_resultat_view_id: ID de la vue compte de résultat (optionnel, non utilisé pour l'instant)
    
    Returns:
        Résultat de l'exercice (bénéfice positif, perte négative)
    """
    # Chercher un override pour l'année
    override = db.query(CompteResultatOverride).filter(
        CompteResultatOverride.year == year
    ).first()
    
    if override:
        return override.override_value
    
    # Sinon, calculer depuis le compte de résultat
    compte_resultat = calculate_compte_resultat(db, year)
    return compte_resultat.get("resultat_net", 0.0)


def calculate_report_a_nouveau(
    db: Session,
    year: int
) -> float:
    """
    Calculer le report à nouveau (cumul des résultats des années précédentes).
    
    Logique :
    - Cumuler les résultats de toutes les années < year qui ont des transactions
    - Première année : 0 (pas de report)
    
    Args:
        db: Session de base de données
        year: Année à calculer
    
    Returns:
        Report à nouveau (cumul des résultats précédents)
    """
    # Trouver la première année avec des transactions
    first_transaction = db.query(func.min(Transaction.date)).scalar()
    if not first_transaction:
        return 0.0
    
    first_year = first_transaction.year if hasattr(first_transaction, 'year') else first_transaction
    
    if year <= first_year:
        return 0.0
    
    # OPTIMISATION: Calculer tous les résultats en une seule fois au lieu de boucler
    # Récupérer tous les overrides d'un coup
    overrides = db.query(CompteResultatOverride).filter(
        CompteResultatOverride.year >= first_year,
        CompteResultatOverride.year < year
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
            compte_resultat = calculate_compte_resultat(db, prev_year)
            total += compte_resultat.get("resultat_net", 0.0)
    
    return total


def calculate_capital_restant_du(
    db: Session,
    year: int
) -> float:
    """
    Calculer le capital restant dû au 31/12 de l'année.
    
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
    
    Returns:
        Capital restant dû au 31/12 (positif, car dette)
    """
    # Date de fin de l'année
    end_date = date(year, 12, 31)
    
    # Récupérer tous les crédits actifs (qui ont commencé avant ou pendant l'année)
    # On a besoin de cette liste pour filtrer les paiements
    active_loans = db.query(LoanConfig).filter(
        or_(
            LoanConfig.loan_start_date.is_(None),
            LoanConfig.loan_start_date <= end_date
        )
    ).all()
    
    # Calculer le montant du crédit accordé depuis les transactions réelles
    # Utiliser level_1 = "Dettes financières (emprunt bancaire)"
    level_1_value = "Dettes financières (emprunt bancaire)"
    
    credit_amount_from_transactions = db.query(
        func.sum(Transaction.quantite)
    ).join(
        EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
    ).filter(
        and_(
            EnrichedTransaction.level_1 == level_1_value,
            Transaction.date <= end_date
        )
    ).scalar()
    
    # Le montant est négatif dans les transactions (débit), donc on prend la valeur absolue
    credit_amount = abs(credit_amount_from_transactions) if credit_amount_from_transactions is not None else 0.0
    
    # Si aucune transaction, retourner 0
    if credit_amount == 0.0:
        print(f"ℹ️ [calculate_capital_restant_du] Aucune transaction trouvée pour {year}. Retour de 0.00 €")
        return 0.0
    
    # Calculer le capital remboursé depuis les pages crédits (LoanPayment)
    # Filtrer par les crédits actifs uniquement
    if active_loans:
        active_loan_names = [loan.name for loan in active_loans]
        
        # Capital remboursé total de tous les crédits actifs
        capital_paid = db.query(
            func.sum(LoanPayment.capital)
        ).filter(
            and_(
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
    print(f"📊 [calculate_capital_restant_du] Calcul pour {year}:")
    print(f"  - Montant transactions (level_1 = \"Dettes financières (emprunt bancaire)\"): {credit_amount:.2f} €")
    print(f"  - Capital remboursé (tous crédits actifs): {capital_paid:.2f} €")
    print(f"  - Capital restant dû: {remaining:.2f} €")
    
    # S'assurer que le résultat est positif (on ne peut pas avoir un capital restant négatif)
    return max(0.0, remaining)


def calculate_bilan(
    db: Session,
    year: int,
    mappings: Optional[List[BilanMapping]] = None,
    level_3_values: Optional[List[str]] = None
) -> Dict[str, any]:
    """
    Calculer le bilan complet pour une année.
    
    Args:
        db: Session de base de données
        year: Année à calculer
        mappings: Liste des mappings (optionnel, sera chargée depuis DB si non fournie)
        level_3_values: Liste des valeurs level_3 (optionnel, sera chargée depuis config si non fournie)
    
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
    # Charger les mappings si non fournis
    if mappings is None:
        mappings = get_mappings(db)
    
    # Charger les level_3_values si non fournis
    if level_3_values is None:
        level_3_values = get_level_3_values(db)
    
    # Dictionnaire pour stocker les montants par catégorie
    categories = {}
    
    # OPTIMISATION: Calculer toutes les catégories normales en une seule requête
    normal_mappings = [m for m in mappings if not m.is_special]
    if normal_mappings:
        # Date de fin de l'année (cumul jusqu'à cette date)
        end_date = date(year, 12, 31)
        
        # Construire un dictionnaire category_name -> set(level_1_values)
        category_to_level_1 = {}
        all_level_1_values = set()
        for mapping in normal_mappings:
            if not mapping.level_1_values:
                continue
            try:
                level_1_values = json.loads(mapping.level_1_values)
                category_to_level_1[mapping.category_name] = set(level_1_values)
                all_level_1_values.update(level_1_values)
            except (json.JSONDecodeError, TypeError):
                continue
        
        if all_level_1_values:
            # Une seule requête pour toutes les catégories normales
            query = db.query(
                EnrichedTransaction.level_1,
                func.sum(Transaction.quantite).label('total')
            ).join(
                Transaction, Transaction.id == EnrichedTransaction.transaction_id
            ).filter(
                and_(
                    EnrichedTransaction.level_3.in_(level_3_values),
                    EnrichedTransaction.level_1.in_(list(all_level_1_values)),
                    Transaction.date <= end_date
                )
            ).group_by(EnrichedTransaction.level_1)
            
            results = query.all()
            
            # Initialiser toutes les catégories normales à 0
            for mapping in normal_mappings:
                categories[mapping.category_name] = 0.0
            
            # Répartir les résultats par catégorie (chaque level_1 peut appartenir à plusieurs catégories)
            # IMPORTANT: On additionne d'abord les montants bruts (avec leurs signes), puis on applique la logique
            # à la somme finale. Cela permet de gérer correctement les catégories avec transactions mixtes
            # (ex: "Cautions reçues" avec paiements positifs et remboursements négatifs)
            for level_1, total in results:
                if level_1 and total is not None:
                    # Trouver toutes les catégories qui utilisent ce level_1
                    for category_name, level_1_set in category_to_level_1.items():
                        if level_1 in level_1_set:
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
    
    # Calculer les catégories spéciales (une par une, elles sont peu nombreuses)
    for mapping in mappings:
        if mapping.is_special:
            category_name = mapping.category_name
            if mapping.special_source == "amortization_result" or mapping.special_source == "amortizations":
                amount = calculate_amortizations_cumul(db, year)
            elif mapping.special_source == "transactions":
                amount = calculate_compte_bancaire(db, year)
            elif mapping.special_source == "compte_resultat":
                amount = calculate_resultat_exercice(
                    db, year, mapping.compte_resultat_view_id
                )
            elif mapping.special_source == "compte_resultat_cumul":
                amount = calculate_report_a_nouveau(db, year)
            elif mapping.special_source == "loan_payments":
                amount = calculate_capital_restant_du(db, year)
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


def get_bilan_data(
    db: Session,
    year: Optional[int] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None
) -> List[BilanData]:
    """
    Récupérer les données du bilan depuis la table bilan_data.
    
    Args:
        db: Session de base de données
        year: Année spécifique (optionnel)
        start_year: Année de début (optionnel, pour plage)
        end_year: Année de fin (optionnel, pour plage)
    
    Returns:
        Liste des données du bilan
    """
    query = db.query(BilanData)
    
    if year is not None:
        query = query.filter(BilanData.annee == year)
    elif start_year is not None and end_year is not None:
        query = query.filter(
            and_(
                BilanData.annee >= start_year,
                BilanData.annee <= end_year
            )
        )
    
    return query.order_by(BilanData.annee, BilanData.category_name).all()


def invalidate_all_bilan(db: Session) -> None:
    """
    Marquer toutes les données du bilan comme invalides (supprimer toutes les données).
    
    Args:
        db: Session de base de données
    """
    db.query(BilanData).delete()
    db.commit()


def invalidate_bilan_for_year(year: int, db: Session) -> None:
    """
    Invalider une année spécifique (supprimer les données de cette année).
    
    Args:
        year: Année à invalider
        db: Session de base de données
    """
    db.query(BilanData).filter(BilanData.annee == year).delete()
    db.commit()
