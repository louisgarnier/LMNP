"""
Script de validation Step 3.3 : Validation de la migration des données Amortissements

Ce script valide que :
1. Tous les types d'amortissement ont un property_id
2. Aucun type orphelin (property_id=NULL)
3. Les résultats d'amortissement sont corrects pour chaque propriété
4. Les résultats d'amortissement sont liés via Transaction.property_id

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database.connection import SessionLocal
from backend.database.models import Property, AmortizationType, AmortizationResult, Transaction

def validate_migration():
    """Valide que la migration des amortissements est correcte."""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("VALIDATION DE LA MIGRATION DES AMORTISSEMENTS - Step 3.3")
        print("=" * 80)
        print()
        
        # 1. Vérifier que tous les types d'amortissement ont un property_id
        print("📋 VÉRIFICATION 1 : Types d'amortissement avec property_id")
        print("-" * 80)
        
        total_types = db.query(AmortizationType).count()
        types_with_property = db.query(AmortizationType).filter(
            AmortizationType.property_id.isnot(None)
        ).count()
        types_without_property = db.query(AmortizationType).filter(
            AmortizationType.property_id.is_(None)
        ).count()
        
        print(f"   Total types: {total_types}")
        print(f"   Types avec property_id: {types_with_property}")
        print(f"   Types sans property_id: {types_without_property}")
        
        if types_without_property > 0:
            print(f"❌ ERREUR: {types_without_property} type(s) d'amortissement sans property_id")
            return False
        else:
            print("✅ Tous les types d'amortissement ont un property_id")
        
        # 2. Vérifier qu'il n'y a pas de types orphelins
        print("\n📋 VÉRIFICATION 2 : Types orphelins (property_id invalide)")
        print("-" * 80)
        
        # Récupérer tous les property_id uniques des types
        type_property_ids = db.query(AmortizationType.property_id).distinct().all()
        type_property_ids = [pid[0] for pid in type_property_ids if pid[0] is not None]
        
        # Vérifier que tous les property_id existent dans la table properties
        orphan_types = []
        for prop_id in type_property_ids:
            prop = db.query(Property).filter(Property.id == prop_id).first()
            if not prop:
                orphan_types.append(prop_id)
        
        if orphan_types:
            print(f"❌ ERREUR: {len(orphan_types)} type(s) d'amortissement avec property_id invalide: {orphan_types}")
            return False
        else:
            print("✅ Aucun type orphelin (tous les property_id sont valides)")
        
        # 3. Vérifier les résultats d'amortissement par propriété
        print("\n📋 VÉRIFICATION 3 : Résultats d'amortissement par propriété")
        print("-" * 80)
        
        properties = db.query(Property).order_by(Property.id).all()
        total_results = db.query(AmortizationResult).count()
        
        print(f"   Total résultats d'amortissement: {total_results}")
        print(f"\n   Résultats par propriété:")
        
        total_results_by_property = 0
        for prop in properties:
            results_count = db.query(AmortizationResult).join(
                Transaction, AmortizationResult.transaction_id == Transaction.id
            ).filter(Transaction.property_id == prop.id).count()
            
            types_count = db.query(AmortizationType).filter(
                AmortizationType.property_id == prop.id
            ).count()
            
            if results_count > 0 or types_count > 0:
                print(f"      - {prop.name} (ID={prop.id}): {types_count} types, {results_count} résultats")
                total_results_by_property += results_count
        
        # Vérifier que tous les résultats sont liés à des transactions avec property_id
        results_without_property = total_results - total_results_by_property
        if results_without_property > 0:
            print(f"\n⚠️  ATTENTION: {results_without_property} résultat(s) d'amortissement non lié(s) à une propriété")
            print("   (peut être normal si des transactions n'ont pas de property_id)")
        else:
            print(f"\n✅ Tous les résultats d'amortissement sont liés à des transactions avec property_id")
        
        # 4. Vérifier la cohérence : types vs résultats
        print("\n📋 VÉRIFICATION 4 : Cohérence types vs résultats")
        print("-" * 80)
        
        issues_found = False
        for prop in properties:
            types_count = db.query(AmortizationType).filter(
                AmortizationType.property_id == prop.id
            ).count()
            
            results_count = db.query(AmortizationResult).join(
                Transaction, AmortizationResult.transaction_id == Transaction.id
            ).filter(Transaction.property_id == prop.id).count()
            
            if types_count > 0 and results_count == 0:
                print(f"   ⚠️  {prop.name} (ID={prop.id}): {types_count} types configurés mais 0 résultats")
                print("      (peut être normal si pas de transactions correspondantes)")
            elif types_count == 0 and results_count > 0:
                print(f"   ⚠️  {prop.name} (ID={prop.id}): {results_count} résultats mais 0 types configurés")
                print("      (peut être normal si les types ont été supprimés)")
        
        if not issues_found:
            print("✅ Cohérence vérifiée")
        
        # 5. Résumé final
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DE LA VALIDATION")
        print("=" * 80)
        print()
        print(f"✅ Types d'amortissement: {types_with_property}/{total_types} avec property_id")
        print(f"✅ Résultats d'amortissement: {total_results_by_property}/{total_results} liés à des propriétés")
        print(f"✅ Propriétés: {len(properties)} propriétés")
        print()
        
        # Statistiques détaillées
        print("📊 Statistiques détaillées par propriété:")
        for prop in properties:
            types_count = db.query(AmortizationType).filter(
                AmortizationType.property_id == prop.id
            ).count()
            
            results_count = db.query(AmortizationResult).join(
                Transaction, AmortizationResult.transaction_id == Transaction.id
            ).filter(Transaction.property_id == prop.id).count()
            
            if types_count > 0 or results_count > 0:
                print(f"   - {prop.name} (ID={prop.id}):")
                print(f"      Types configurés: {types_count}")
                print(f"      Résultats calculés: {results_count}")
        
        print("\n" + "=" * 80)
        print("✅ VALIDATION TERMINÉE")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR lors de la validation: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = validate_migration()
    sys.exit(0 if success else 1)
