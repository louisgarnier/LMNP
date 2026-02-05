"""
Script de migration Step 3.3 : Migration des données Amortissements existantes

Ce script :
1. Récupère ou crée la propriété par défaut
2. Assigne tous les types d'amortissement existants sans property_id à cette propriété
3. Vérifie que les résultats d'amortissement sont liés via Transaction.property_id
4. Recalcule tous les amortissements pour la propriété par défaut si nécessaire
5. Vérifie qu'aucun type n'a property_id=NULL après migration

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
import os
from pathlib import Path

# Ajouter le chemin du projet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database.connection import SessionLocal
from backend.database.models import Property, AmortizationType, AmortizationResult, Transaction
from backend.api.services.amortization_service import recalculate_all_amortizations

def get_or_create_default_property(db):
    """Récupère ou crée la propriété par défaut."""
    # Chercher une propriété existante (la première par ordre d'ID)
    default_property = db.query(Property).order_by(Property.id).first()
    
    if default_property:
        print(f"✅ Propriété par défaut trouvée: ID={default_property.id}, Name={default_property.name}")
        return default_property
    
    # Créer une propriété par défaut
    print("📋 Création de la propriété par défaut...")
    default_property = Property(
        name="Appartement 1",
        address="Adresse par défaut"
    )
    db.add(default_property)
    db.commit()
    db.refresh(default_property)
    print(f"✅ Propriété par défaut créée: ID={default_property.id}, Name={default_property.name}")
    return default_property

def migrate_amortizations():
    """Migrer tous les types d'amortissement vers la propriété par défaut."""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("MIGRATION DES AMORTISSEMENTS - Step 3.3")
        print("=" * 80)
        print()
        
        # 1. Récupérer ou créer la propriété par défaut
        default_property = get_or_create_default_property(db)
        property_id = default_property.id
        
        # 2. Assigner tous les types d'amortissement existants sans property_id à la propriété par défaut
        print("\n📋 ÉTAPE 1 : Assignation des types d'amortissement existants")
        print("-" * 80)
        
        types_without_property = db.query(AmortizationType).filter(
            AmortizationType.property_id.is_(None)
        ).count()
        
        if types_without_property > 0:
            print(f"   {types_without_property} type(s) d'amortissement sans property_id trouvé(s)")
            updated = db.query(AmortizationType).filter(
                AmortizationType.property_id.is_(None)
            ).update({AmortizationType.property_id: property_id}, synchronize_session=False)
            db.commit()
            print(f"✅ {updated} type(s) d'amortissement assigné(s) à property_id={property_id}")
        else:
            print("✅ Tous les types d'amortissement ont déjà un property_id")
        
        # Vérifier qu'il n'y a plus de types sans property_id
        remaining = db.query(AmortizationType).filter(AmortizationType.property_id.is_(None)).count()
        if remaining > 0:
            print(f"❌ ERREUR: {remaining} type(s) d'amortissement ont encore property_id=NULL")
            return False
        
        # 3. Vérifier que les résultats d'amortissement sont liés via Transaction.property_id
        print("\n📋 ÉTAPE 2 : Vérification des résultats d'amortissement")
        print("-" * 80)
        
        # Compter les résultats d'amortissement par propriété
        total_results = db.query(AmortizationResult).count()
        print(f"   Total résultats d'amortissement: {total_results}")
        
        # Vérifier que tous les résultats sont liés à des transactions avec property_id
        results_without_property = db.query(AmortizationResult).join(
            Transaction, AmortizationResult.transaction_id == Transaction.id
        ).filter(Transaction.property_id.is_(None)).count()
        
        if results_without_property > 0:
            print(f"⚠️  {results_without_property} résultat(s) d'amortissement lié(s) à des transactions sans property_id")
            print("   Note: Les résultats d'amortissement sont liés via Transaction.property_id")
            print("   Si des transactions n'ont pas de property_id, elles doivent être migrées d'abord")
        else:
            print("✅ Tous les résultats d'amortissement sont liés à des transactions avec property_id")
        
        # Compter les résultats par propriété
        properties = db.query(Property).all()
        print(f"\n   Résultats par propriété:")
        for prop in properties:
            count = db.query(AmortizationResult).join(
                Transaction, AmortizationResult.transaction_id == Transaction.id
            ).filter(Transaction.property_id == prop.id).count()
            if count > 0:
                print(f"      - {prop.name} (ID={prop.id}): {count} résultats")
        
        # 4. Recalculer tous les amortissements pour la propriété par défaut si nécessaire
        print("\n📋 ÉTAPE 3 : Recalcul des amortissements pour la propriété par défaut")
        print("-" * 80)
        
        # Compter les types d'amortissement pour la propriété par défaut
        types_count = db.query(AmortizationType).filter(
            AmortizationType.property_id == property_id
        ).count()
        
        if types_count > 0:
            print(f"   {types_count} type(s) d'amortissement pour property_id={property_id}")
            print("   Recalcul des amortissements...")
            
            try:
                results_created = recalculate_all_amortizations(db, property_id=property_id)
                db.commit()
                print(f"✅ Recalcul terminé: {results_created} résultat(s) créé(s)")
            except Exception as e:
                print(f"⚠️  Erreur lors du recalcul (peut être normal si pas de transactions): {e}")
        else:
            print("   Aucun type d'amortissement pour la propriété par défaut, pas de recalcul nécessaire")
        
        # 5. Vérification finale
        print("\n📋 ÉTAPE 4 : Vérification finale")
        print("-" * 80)
        
        total_types = db.query(AmortizationType).count()
        types_with_property = db.query(AmortizationType).filter(
            AmortizationType.property_id.isnot(None)
        ).count()
        
        print(f"✅ Types d'amortissement: {types_with_property}/{total_types} avec property_id")
        
        if types_with_property == total_types:
            print("✅ Migration réussie: Tous les types d'amortissement ont un property_id")
        else:
            print(f"❌ ERREUR: {total_types - types_with_property} type(s) sans property_id")
            return False
        
        # Statistiques par propriété
        print(f"\n📊 Statistiques par propriété:")
        for prop in properties:
            types_count = db.query(AmortizationType).filter(
                AmortizationType.property_id == prop.id
            ).count()
            results_count = db.query(AmortizationResult).join(
                Transaction, AmortizationResult.transaction_id == Transaction.id
            ).filter(Transaction.property_id == prop.id).count()
            if types_count > 0 or results_count > 0:
                print(f"   - {prop.name} (ID={prop.id}): {types_count} types, {results_count} résultats")
        
        print("\n" + "=" * 80)
        print("✅ MIGRATION TERMINÉE AVEC SUCCÈS")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR lors de la migration: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = migrate_amortizations()
    sys.exit(0 if success else 1)
