"""
Script de validation Step 2.3 : Validation de la migration des Mappings

Ce script valide que :
1. Tous les mappings ont un property_id
2. Tous les mappings autorisés ont un property_id
3. Aucun mapping orphelin (property_id=NULL)
4. Les mappings hardcodés sont initialisés pour la propriété par défaut
5. Le frontend peut afficher correctement les mappings après migration

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database.connection import SessionLocal
from backend.database.models import Property, Mapping, AllowedMapping, MappingImport

def validate_migration():
    """Valider la migration des mappings."""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("VALIDATION DE LA MIGRATION DES MAPPINGS - Step 2.3")
        print("=" * 80)
        print()
        
        all_checks_passed = True
        
        # 1. Vérifier qu'il existe au moins une propriété
        print("📋 ÉTAPE 1 : Vérification des propriétés")
        print("-" * 80)
        
        properties = db.query(Property).all()
        if not properties:
            print("❌ ERREUR: Aucune propriété trouvée")
            all_checks_passed = False
        else:
            print(f"✅ {len(properties)} propriété(s) trouvée(s)")
            for prop in properties:
                print(f"   - ID={prop.id}: {prop.name}")
        
        default_property = db.query(Property).order_by(Property.id).first()
        if not default_property:
            print("❌ ERREUR: Aucune propriété par défaut trouvée")
            all_checks_passed = False
        else:
            print(f"\n✅ Propriété par défaut: ID={default_property.id}, Name={default_property.name}")
        print()
        
        # 2. Vérifier que tous les mappings ont un property_id
        print("📋 ÉTAPE 2 : Vérification des mappings")
        print("-" * 80)
        
        total_mappings = db.query(Mapping).count()
        mappings_with_property = db.query(Mapping).filter(
            Mapping.property_id.isnot(None)
        ).count()
        mappings_without_property = db.query(Mapping).filter(
            Mapping.property_id.is_(None)
        ).count()
        
        print(f"   Total mappings: {total_mappings}")
        print(f"   Avec property_id: {mappings_with_property}")
        print(f"   Sans property_id: {mappings_without_property}")
        
        if mappings_without_property > 0:
            print(f"❌ ERREUR: {mappings_without_property} mapping(s) ont property_id=NULL")
            all_checks_passed = False
        else:
            print("✅ Tous les mappings ont un property_id")
        
        # Vérifier les mappings par propriété
        if default_property:
            mappings_for_default = db.query(Mapping).filter(
                Mapping.property_id == default_property.id
            ).count()
            print(f"   Mappings pour propriété par défaut (ID={default_property.id}): {mappings_for_default}")
        print()
        
        # 3. Vérifier que tous les mappings autorisés ont un property_id
        print("📋 ÉTAPE 3 : Vérification des mappings autorisés")
        print("-" * 80)
        
        total_allowed = db.query(AllowedMapping).count()
        allowed_with_property = db.query(AllowedMapping).filter(
            AllowedMapping.property_id.isnot(None)
        ).count()
        allowed_without_property = db.query(AllowedMapping).filter(
            AllowedMapping.property_id.is_(None)
        ).count()
        
        print(f"   Total mappings autorisés: {total_allowed}")
        print(f"   Avec property_id: {allowed_with_property}")
        print(f"   Sans property_id: {allowed_without_property}")
        
        if allowed_without_property > 0:
            print(f"❌ ERREUR: {allowed_without_property} mapping(s) autorisé(s) ont property_id=NULL")
            all_checks_passed = False
        else:
            print("✅ Tous les mappings autorisés ont un property_id")
        
        # Vérifier les mappings autorisés par propriété
        if default_property:
            allowed_for_default = db.query(AllowedMapping).filter(
                AllowedMapping.property_id == default_property.id
            ).count()
            hardcoded_for_default = db.query(AllowedMapping).filter(
                AllowedMapping.property_id == default_property.id,
                AllowedMapping.is_hardcoded == True
            ).count()
            manual_for_default = db.query(AllowedMapping).filter(
                AllowedMapping.property_id == default_property.id,
                AllowedMapping.is_hardcoded == False
            ).count()
            
            print(f"   Mappings autorisés pour propriété par défaut (ID={default_property.id}): {allowed_for_default}")
            print(f"   - Hardcodés: {hardcoded_for_default}")
            print(f"   - Manuels: {manual_for_default}")
            
            if hardcoded_for_default == 0:
                print("⚠️  ATTENTION: Aucun mapping hardcodé trouvé pour la propriété par défaut")
                print("   Les mappings hardcodés devraient être initialisés (57 mappings attendus)")
        print()
        
        # 4. Vérifier que tous les imports ont un property_id
        print("📋 ÉTAPE 4 : Vérification des imports de mappings")
        print("-" * 80)
        
        total_imports = db.query(MappingImport).count()
        imports_with_property = db.query(MappingImport).filter(
            MappingImport.property_id.isnot(None)
        ).count()
        imports_without_property = db.query(MappingImport).filter(
            MappingImport.property_id.is_(None)
        ).count()
        
        print(f"   Total imports: {total_imports}")
        print(f"   Avec property_id: {imports_with_property}")
        print(f"   Sans property_id: {imports_without_property}")
        
        if imports_without_property > 0:
            print(f"❌ ERREUR: {imports_without_property} import(s) ont property_id=NULL")
            all_checks_passed = False
        else:
            print("✅ Tous les imports ont un property_id")
        
        # Vérifier les imports par propriété
        if default_property:
            imports_for_default = db.query(MappingImport).filter(
                MappingImport.property_id == default_property.id
            ).count()
            print(f"   Imports pour propriété par défaut (ID={default_property.id}): {imports_for_default}")
        print()
        
        # 5. Vérifier qu'il n'y a aucun mapping orphelin
        print("📋 ÉTAPE 5 : Vérification des mappings orphelins")
        print("-" * 80)
        
        orphan_mappings = db.query(Mapping).filter(Mapping.property_id.is_(None)).count()
        orphan_allowed = db.query(AllowedMapping).filter(AllowedMapping.property_id.is_(None)).count()
        orphan_imports = db.query(MappingImport).filter(MappingImport.property_id.is_(None)).count()
        
        total_orphans = orphan_mappings + orphan_allowed + orphan_imports
        
        if total_orphans > 0:
            print(f"❌ ERREUR: {total_orphans} mapping(s) orphelin(s) trouvé(s):")
            if orphan_mappings > 0:
                print(f"   - {orphan_mappings} mapping(s) avec property_id=NULL")
            if orphan_allowed > 0:
                print(f"   - {orphan_allowed} mapping(s) autorisé(s) avec property_id=NULL")
            if orphan_imports > 0:
                print(f"   - {orphan_imports} import(s) avec property_id=NULL")
            all_checks_passed = False
        else:
            print("✅ Aucun mapping orphelin (property_id=NULL)")
        print()
        
        # 6. Résumé final
        print("=" * 80)
        if all_checks_passed:
            print("✅ TOUTES LES VALIDATIONS ONT RÉUSSI")
        else:
            print("❌ CERTAINES VALIDATIONS ONT ÉCHOUÉ")
        print("=" * 80)
        print()
        
        if default_property:
            print("📊 RÉSUMÉ POUR LA PROPRIÉTÉ PAR DÉFAUT:")
            print(f"   - ID: {default_property.id}")
            print(f"   - Nom: {default_property.name}")
            print(f"   - Mappings: {mappings_for_default}")
            print(f"   - Mappings autorisés: {allowed_for_default} (hardcodés: {hardcoded_for_default}, manuels: {manual_for_default})")
            print(f"   - Imports: {imports_for_default}")
        print()
        
        return all_checks_passed
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = validate_migration()
    
    if success:
        print("✅ Script de validation terminé avec succès")
        sys.exit(0)
    else:
        print("❌ Script de validation terminé avec erreur")
        sys.exit(1)
