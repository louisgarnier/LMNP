#!/usr/bin/env python3
"""
Script de test pour générer des AmortizationResult en base de données.

Ce script permet de :
1. Créer des transactions de test avec enrichissement
2. Créer des AmortizationType avec des paramètres valides
3. Recalculer les amortissements pour générer des AmortizationResult
4. Afficher un résumé des résultats créés

Usage:
    python3 backend/scripts/generate_test_amortization_results.py
"""

import sys
import os
from datetime import date, datetime
import json

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database.connection import SessionLocal
from backend.database.models import Transaction, EnrichedTransaction, AmortizationType, AmortizationResult
from backend.api.services.amortization_service import recalculate_all_amortizations, recalculate_transaction_amortization

def create_test_data(db):
    """Crée des données de test pour les amortissements."""
    print("📝 Création des données de test...")
    
    # Vérifier si des types d'amortissement existent déjà pour "Immobilisations"
    existing_types = db.query(AmortizationType).filter(
        AmortizationType.level_2_value == "Immobilisations"
    ).all()
    
    if not existing_types:
        print("⚠️  Aucun type d'amortissement trouvé pour 'Immobilisations'")
        print("   Création de 3 types de test...")
        
        # Créer 3 types de test
        test_types = [
            {
                "name": "Immobilisation terrain",
                "level_1_values": ["Terrain"],
                "duration": 5.0,
                "annual_amount": None
            },
            {
                "name": "Immobilisation structure/GO",
                "level_1_values": ["Construction"],
                "duration": 20.0,
                "annual_amount": None
            },
            {
                "name": "Immobilisation mobilier",
                "level_1_values": ["Mobilier"],
                "duration": 10.0,
                "annual_amount": None
            }
        ]
        
        for type_data in test_types:
            amort_type = AmortizationType(
                name=type_data["name"],
                level_2_value="Immobilisations",
                level_1_values=json.dumps(type_data["level_1_values"]),
                duration=type_data["duration"],
                annual_amount=type_data["annual_amount"],
                start_date=None
            )
            db.add(amort_type)
        
        db.commit()
        print("   ✓ 3 types créés")
    else:
        print(f"   ✓ {len(existing_types)} types existants trouvés")
    
    # Vérifier si des transactions de test existent déjà
    test_transactions = db.query(Transaction).join(EnrichedTransaction).filter(
        EnrichedTransaction.level_2 == "Immobilisations"
    ).limit(5).all()
    
    if len(test_transactions) < 3:
        print("   Création de transactions de test...")
        
        # Créer 3 transactions de test
        test_data = [
            {
                "date": date(2021, 3, 15),
                "quantite": -50000.0,
                "nom": "Achat terrain",
                "level_1": "Terrain",
                "level_2": "Immobilisations"
            },
            {
                "date": date(2022, 6, 1),
                "quantite": -200000.0,
                "nom": "Construction bâtiment",
                "level_1": "Construction",
                "level_2": "Immobilisations"
            },
            {
                "date": date(2023, 9, 10),
                "quantite": -30000.0,
                "nom": "Achat mobilier",
                "level_1": "Mobilier",
                "level_2": "Immobilisations"
            }
        ]
        
        for data in test_data:
            # Créer la transaction
            transaction = Transaction(
                date=data["date"],
                quantite=data["quantite"],
                nom=data["nom"],
                solde=0.0
            )
            db.add(transaction)
            db.flush()
            
            # Créer l'enrichissement
            enriched = EnrichedTransaction(
                transaction_id=transaction.id,
                mois=data["date"].month,
                annee=data["date"].year,
                level_1=data["level_1"],
                level_2=data["level_2"]
            )
            db.add(enriched)
        
        db.commit()
        print("   ✓ 3 transactions créées")
    else:
        print(f"   ✓ {len(test_transactions)} transactions existantes trouvées")
    
    return True

def main():
    """Fonction principale."""
    print("=" * 60)
    print("🧪 Script de génération de données de test pour amortissements")
    print("=" * 60)
    print()
    
    db = SessionLocal()
    
    try:
        # Étape 1: Créer les données de test
        create_test_data(db)
        print()
        
        # Étape 2: Compter les résultats existants
        existing_count = db.query(AmortizationResult).count()
        print(f"📊 Résultats d'amortissement existants: {existing_count}")
        print()
        
        # Étape 3: Recalculer tous les amortissements
        print("🔄 Recalcul de tous les amortissements...")
        total_created = recalculate_all_amortizations(db)
        print(f"   ✓ {total_created} résultats créés/mis à jour")
        print()
        
        # Étape 4: Afficher un résumé
        final_count = db.query(AmortizationResult).count()
        print("📈 Résumé final:")
        print(f"   - Total de résultats: {final_count}")
        
        # Grouper par catégorie
        from sqlalchemy import func
        category_counts = db.query(
            AmortizationResult.category,
            func.count(AmortizationResult.id).label('count')
        ).group_by(AmortizationResult.category).all()
        
        print(f"   - Par catégorie:")
        for category, count in category_counts:
            print(f"     • {category}: {count} résultats")
        
        # Grouper par année
        year_counts = db.query(
            AmortizationResult.year,
            func.count(AmortizationResult.id).label('count')
        ).group_by(AmortizationResult.year).order_by(AmortizationResult.year).all()
        
        print(f"   - Par année:")
        for year, count in year_counts:
            print(f"     • {year}: {count} résultats")
        
        print()
        print("✅ Génération terminée avec succès!")
        print()
        print("💡 Vous pouvez maintenant vérifier l'affichage du tableau dans le navigateur.")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return 1
    finally:
        db.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

