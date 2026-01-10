"""
Script de test pour expliquer le calcul du montant cumulé d'amortissement.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce script affiche le calcul détaillé du montant cumulé pour chaque type d'amortissement :
- Pour chaque transaction du type
- Calcul année par année avec convention 30/360
- Prise en compte de la date de début (start_date du type ou date de transaction)
- Somme finale par type
"""

import sys
from pathlib import Path
import json
from datetime import date

# Ajouter le chemin du projet au PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.database.models import AmortizationType, Transaction, EnrichedTransaction
from backend.api.services.amortization_service import calculate_yearly_amounts, calculate_30_360_days
from sqlalchemy import and_


def calculate_cumulated_for_transaction(transaction, atype, today):
    """
    Calcule le montant cumulé pour une transaction donnée.
    
    Returns:
        dict avec les détails du calcul
    """
    # Déterminer la date de début
    start_date = atype.start_date if atype.start_date else transaction.date
    
    # Vérifier si la date de début est dans le futur
    if start_date > today:
        return {
            'transaction_id': transaction.id,
            'transaction_date': transaction.date,
            'start_date_used': start_date,
            'amount': abs(transaction.quantite),
            'cumulated': 0.0,
            'reason': 'Date de début dans le futur'
        }
    
    # Montant de la transaction
    transaction_amount = abs(transaction.quantite)
    
    # Calculer l'annuité
    if atype.annual_amount is not None and atype.annual_amount != 0:
        annual_amount = atype.annual_amount
    else:
        annual_amount = transaction_amount / atype.duration
    
    # Calculer les montants par année
    yearly_amounts = calculate_yearly_amounts(
        start_date=start_date,
        total_amount=-transaction_amount,  # Négatif car convention
        duration=atype.duration,
        annual_amount=annual_amount
    )
    
    # Calculer la date de fin de l'amortissement
    end_year = start_date.year + int(atype.duration) - 1
    end_date = date(end_year, 12, 31)
    
    # Calculer le montant cumulé jusqu'à l'année en cours (incluse)
    # Logique :
    # - Année d'achat : prorata (déjà calculé par calculate_yearly_amounts)
    # - Années complètes suivantes : annuité complète
    # - Année en cours : annuité complète (pas de prorata jusqu'à aujourd'hui)
    cumulated = 0.0
    for year, amount in yearly_amounts.items():
        if year <= today.year:
            # Prendre le montant complet de l'année
            cumulated += abs(amount)
    
    # Détails année par année pour l'affichage
    yearly_details = {}
    for year, amount in yearly_amounts.items():
        if year <= today.year:
            if year < today.year:
                yearly_details[year] = {
                    'amount': abs(amount),
                    'status': 'année complète'
                }
            elif year == today.year:
                # Pour l'année en cours, on prend le montant complet (pas de prorata)
                yearly_details[year] = {
                    'amount': abs(amount),
                    'amount_full_year': abs(amount),
                    'status': 'année en cours (montant complet)'
                }
    
    # Calculer la date de fin de l'amortissement
    end_year = start_date.year + int(atype.duration) - 1
    end_date = date(end_year, 12, 31)
    
    return {
        'transaction_id': transaction.id,
        'transaction_date': transaction.date,
        'start_date_used': start_date,
        'amount': transaction_amount,
        'annual_amount': annual_amount,
        'duration': atype.duration,
        'end_date': end_date,
        'cumulated': cumulated,
        'yearly_details': yearly_details,
        'yearly_amounts_full': {year: abs(amount) for year, amount in yearly_amounts.items()}
    }


def main():
    """Affiche le calcul détaillé du montant cumulé pour chaque type."""
    print("=" * 80)
    print("CALCUL DÉTAILLÉ DU MONTANT CUMULÉ D'AMORTISSEMENT")
    print("=" * 80)
    
    init_database()
    db = SessionLocal()
    
    try:
        today = date.today()
        print(f"\n📅 Date d'aujourd'hui : {today.strftime('%d/%m/%Y')}")
        print(f"📅 Année en cours : {today.year}\n")
        
        # Récupérer tous les types avec durée > 0
        types = db.query(AmortizationType).filter(
            AmortizationType.duration > 0
        ).order_by(AmortizationType.level_2_value, AmortizationType.name).all()
        
        if not types:
            print("Aucun type d'amortissement avec durée > 0 trouvé.")
            return 0
        
        print(f"📊 Types d'amortissement avec durée > 0 : {len(types)}\n")
        
        for atype in types:
            level_1_values = json.loads(atype.level_1_values or "[]")
            
            print("=" * 80)
            print(f"TYPE : {atype.name} (ID: {atype.id})")
            print("=" * 80)
            print(f"  - Level 2: {atype.level_2_value}")
            print(f"  - Level 1 values: {', '.join(level_1_values) if level_1_values else '(aucune)'}")
            print(f"  - Durée: {atype.duration} années")
            print(f"  - Annuité manuelle: {atype.annual_amount if atype.annual_amount is not None and atype.annual_amount != 0 else '(calcul automatique)'}")
            print(f"  - Date de début (start_date): {atype.start_date if atype.start_date else '(utilise date transaction)'}")
            print()
            
            if not level_1_values:
                print("  ⚠️  Aucune valeur Level 1 → Aucune transaction → Montant cumulé = 0,00 €\n")
                continue
            
            # Récupérer les transactions correspondantes
            transactions = db.query(Transaction).join(
                EnrichedTransaction, Transaction.id == EnrichedTransaction.transaction_id
            ).filter(
                and_(
                    EnrichedTransaction.level_2 == atype.level_2_value,
                    EnrichedTransaction.level_1.in_(level_1_values)
                )
            ).order_by(Transaction.date).all()
            
            if not transactions:
                print("  ⚠️  Aucune transaction trouvée → Montant cumulé = 0,00 €\n")
                continue
            
            print(f"  📋 Transactions trouvées : {len(transactions)}\n")
            
            total_cumulated = 0.0
            
            for idx, transaction in enumerate(transactions, 1):
                print(f"  {'-' * 76}")
                print(f"  TRANSACTION #{idx} (ID: {transaction.id})")
                print(f"  {'-' * 76}")
                
                calc_details = calculate_cumulated_for_transaction(transaction, atype, today)
                
                print(f"    Date transaction: {transaction.date.strftime('%d/%m/%Y')}")
                print(f"    Date de début utilisée: {calc_details['start_date_used'].strftime('%d/%m/%Y')}")
                if atype.start_date:
                    print(f"      → Utilise start_date du type (override)")
                else:
                    print(f"      → Utilise date de la transaction")
                
                print(f"    Montant transaction: {calc_details['amount']:,.2f} €")
                print(f"    Annuité: {calc_details['annual_amount']:,.2f} €/an")
                print(f"    Durée: {calc_details['duration']} années")
                print(f"    Date de fin amortissement: {calc_details['end_date'].strftime('%d/%m/%Y')}")
                
                if calc_details.get('reason'):
                    print(f"    ⚠️  {calc_details['reason']}")
                    print(f"    Montant cumulé: 0,00 €\n")
                    continue
                
                print(f"\n    📊 Détail année par année:")
                annee_label = "Montant de l'année"
                print(f"    {'Année':<8} {annee_label:<25} {'Montant cumulé':<20} {'Status':<30}")
                print(f"    {'-' * 8} {'-' * 25} {'-' * 20} {'-' * 30}")
                
                cumulated_so_far = 0.0
                for year in sorted(calc_details['yearly_details'].keys()):
                    detail = calc_details['yearly_details'][year]
                    # Pour l'année en cours, prendre le montant complet (pas de prorata)
                    if year == today.year and 'amount_full_year' in detail:
                        amount_to_add = detail['amount_full_year']
                    else:
                        amount_to_add = detail['amount']
                    
                    cumulated_so_far += amount_to_add
                    
                    if 'prorata' in detail:
                        if year == today.year:
                            # Année en cours : afficher le montant complet
                            print(f"    {year:<8} {detail['amount_full_year']:>20,.2f} €    {cumulated_so_far:>15,.2f} €    année en cours (montant complet)")
                        else:
                            # Année d'achat avec prorata
                            print(f"    {year:<8} {detail['amount']:>20,.2f} €    {cumulated_so_far:>15,.2f} €    année d'achat (prorata)")
                            print(f"      → Prorata: {detail['prorata']:.4f} ({detail['days_until_today']} jours / {detail['days_in_year']} jours)")
                    else:
                        print(f"    {year:<8} {amount_to_add:>20,.2f} €    {cumulated_so_far:>15,.2f} €    {detail['status']}")
                
                print(f"\n    ✅ Montant cumulé pour cette transaction: {calc_details['cumulated']:,.2f} €")
                print(f"       (Somme des montants jusqu'à l'année en cours incluse)\n")
                
                total_cumulated += calc_details['cumulated']
            
            print(f"  {'=' * 76}")
            print(f"  🎯 MONTANT CUMULÉ TOTAL POUR CE TYPE: {total_cumulated:,.2f} €")
            print(f"  {'=' * 76}\n\n")
        
        return 0
        
    except Exception as e:
        print(f'\n✗ ERREUR : {e}')
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())

