"""
Script pour afficher les statistiques de la base de données.

Affiche :
- Nombre de propriétés
- Nombre de transactions par propriété
- Nombre de mappings par propriété
- Nombre de transactions enrichies par propriété
- Autres statistiques utiles

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database.connection import SessionLocal
from backend.database.models import Property, Transaction, Mapping, EnrichedTransaction, FileImport, MappingImport
from sqlalchemy import func

def show_statistics():
    """Afficher les statistiques de la base de données."""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("STATISTIQUES DE LA BASE DE DONNÉES")
        print("=" * 80)
        print()
        
        # 1. Nombre total de propriétés
        total_properties = db.query(Property).count()
        print(f"📊 NOMBRE TOTAL DE PROPRIÉTÉS: {total_properties}")
        print()
        
        if total_properties == 0:
            print("⚠️  Aucune propriété dans la base de données")
            return
        
        # 2. Détails par propriété
        properties = db.query(Property).order_by(Property.id).all()
        
        print("=" * 80)
        print("DÉTAILS PAR PROPRIÉTÉ")
        print("=" * 80)
        print()
        
        total_transactions = 0
        total_mappings = 0
        total_enriched = 0
        total_file_imports = 0
        total_mapping_imports = 0
        
        for prop in properties:
            print(f"🏠 PROPRIÉTÉ ID={prop.id}: {prop.name}")
            print(f"   📍 Adresse: {prop.address or 'Non renseignée'}")
            print(f"   📅 Créée le: {prop.created_at.strftime('%d/%m/%Y %H:%M:%S') if prop.created_at else 'N/A'}")
            print()
            
            # Transactions
            transactions_count = db.query(Transaction).filter(Transaction.property_id == prop.id).count()
            total_transactions += transactions_count
            print(f"   💰 Transactions: {transactions_count}")
            
            # Transactions enrichies
            enriched_count = db.query(EnrichedTransaction).filter(EnrichedTransaction.property_id == prop.id).count()
            total_enriched += enriched_count
            print(f"   ✅ Transactions enrichies: {enriched_count}")
            
            # Transactions non enrichies
            non_enriched = transactions_count - enriched_count
            if non_enriched > 0:
                print(f"   ⚠️  Transactions non enrichies: {non_enriched}")
            
            # Mappings
            mappings_count = db.query(Mapping).filter(Mapping.property_id == prop.id).count()
            total_mappings += mappings_count
            print(f"   🗺️  Mappings: {mappings_count}")
            
            # File imports
            file_imports_count = db.query(FileImport).filter(FileImport.property_id == prop.id).count()
            total_file_imports += file_imports_count
            if file_imports_count > 0:
                print(f"   📥 Imports de transactions: {file_imports_count}")
            
            # Mapping imports
            mapping_imports_count = db.query(MappingImport).filter(MappingImport.property_id == prop.id).count()
            total_mapping_imports += mapping_imports_count
            if mapping_imports_count > 0:
                print(f"   📥 Imports de mappings: {mapping_imports_count}")
            
            # Statistiques sur les transactions enrichies
            if enriched_count > 0:
                # Level_1 uniques
                level1_count = db.query(func.count(func.distinct(EnrichedTransaction.level_1))).filter(
                    EnrichedTransaction.property_id == prop.id,
                    EnrichedTransaction.level_1.isnot(None)
                ).scalar()
                print(f"   📊 Level_1 uniques: {level1_count}")
                
                # Level_2 uniques
                level2_count = db.query(func.count(func.distinct(EnrichedTransaction.level_2))).filter(
                    EnrichedTransaction.property_id == prop.id,
                    EnrichedTransaction.level_2.isnot(None)
                ).scalar()
                print(f"   📊 Level_2 uniques: {level2_count}")
                
                # Level_3 uniques
                level3_count = db.query(func.count(func.distinct(EnrichedTransaction.level_3))).filter(
                    EnrichedTransaction.property_id == prop.id,
                    EnrichedTransaction.level_3.isnot(None)
                ).scalar()
                print(f"   📊 Level_3 uniques: {level3_count}")
                
                # Transactions non classées (sans level_1)
                unclassified = db.query(EnrichedTransaction).filter(
                    EnrichedTransaction.property_id == prop.id,
                    EnrichedTransaction.level_1.is_(None)
                ).count()
                if unclassified > 0:
                    print(f"   ⚠️  Transactions non classées: {unclassified}")
            
            print()
            print("-" * 80)
            print()
        
        # 3. Totaux globaux
        print("=" * 80)
        print("TOTAUX GLOBAUX")
        print("=" * 80)
        print()
        print(f"📊 Propriétés: {total_properties}")
        print(f"💰 Transactions: {total_transactions}")
        print(f"✅ Transactions enrichies: {total_enriched}")
        print(f"⚠️  Transactions non enrichies: {total_transactions - total_enriched}")
        print(f"🗺️  Mappings: {total_mappings}")
        print(f"📥 Imports de transactions: {total_file_imports}")
        print(f"📥 Imports de mappings: {total_mapping_imports}")
        print()
        
        # 4. Vérifications d'intégrité
        print("=" * 80)
        print("VÉRIFICATIONS D'INTÉGRITÉ")
        print("=" * 80)
        print()
        
        # Transactions sans property_id
        transactions_no_property = db.query(Transaction).filter(Transaction.property_id.is_(None)).count()
        if transactions_no_property > 0:
            print(f"❌ Transactions sans property_id: {transactions_no_property}")
        else:
            print(f"✅ Toutes les transactions ont un property_id")
        
        # Mappings sans property_id
        mappings_no_property = db.query(Mapping).filter(Mapping.property_id.is_(None)).count()
        if mappings_no_property > 0:
            print(f"❌ Mappings sans property_id: {mappings_no_property}")
        else:
            print(f"✅ Tous les mappings ont un property_id")
        
        # EnrichedTransactions sans property_id
        enriched_no_property = db.query(EnrichedTransaction).filter(EnrichedTransaction.property_id.is_(None)).count()
        if enriched_no_property > 0:
            print(f"❌ Transactions enrichies sans property_id: {enriched_no_property}")
        else:
            print(f"✅ Toutes les transactions enrichies ont un property_id")
        
        # FileImports sans property_id
        file_imports_no_property = db.query(FileImport).filter(FileImport.property_id.is_(None)).count()
        if file_imports_no_property > 0:
            print(f"❌ Imports de transactions sans property_id: {file_imports_no_property}")
        else:
            print(f"✅ Tous les imports de transactions ont un property_id")
        
        # MappingImports sans property_id
        mapping_imports_no_property = db.query(MappingImport).filter(MappingImport.property_id.is_(None)).count()
        if mapping_imports_no_property > 0:
            print(f"❌ Imports de mappings sans property_id: {mapping_imports_no_property}")
        else:
            print(f"✅ Tous les imports de mappings ont un property_id")
        
        # Transactions orphelines (property_id qui n'existe pas)
        orphan_transactions = db.query(Transaction).outerjoin(Property, Transaction.property_id == Property.id).filter(Property.id.is_(None)).count()
        if orphan_transactions > 0:
            print(f"❌ Transactions orphelines (property_id inexistant): {orphan_transactions}")
        else:
            print(f"✅ Toutes les transactions ont un property_id valide")
        
        # Mappings orphelins
        orphan_mappings = db.query(Mapping).outerjoin(Property, Mapping.property_id == Property.id).filter(Property.id.is_(None)).count()
        if orphan_mappings > 0:
            print(f"❌ Mappings orphelins (property_id inexistant): {orphan_mappings}")
        else:
            print(f"✅ Tous les mappings ont un property_id valide")
        
        print()
        print("=" * 80)
        print("✅ Statistiques terminées")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
    
    return True


if __name__ == "__main__":
    success = show_statistics()
    if not success:
        sys.exit(1)
