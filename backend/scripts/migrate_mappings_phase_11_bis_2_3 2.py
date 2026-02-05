"""
Script de migration Step 2.3 : Migration des données Mappings existantes

Ce script :
1. Récupère ou crée la propriété par défaut
2. Assigne tous les mappings existants à cette propriété
3. Assigne tous les mappings autorisés existants à cette propriété
4. Initialise les mappings hardcodés pour la propriété par défaut
5. Vérifie qu'aucun mapping n'a property_id=NULL après migration

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
import os
from pathlib import Path

# Ajouter le chemin du projet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database.connection import SessionLocal
from backend.database.models import Property, Mapping, AllowedMapping, MappingImport
from backend.api.services.mapping_obligatoire_service import load_allowed_mappings_from_excel

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

def migrate_mappings(property_id: int):
    """Migrer tous les mappings vers la propriété par défaut."""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("MIGRATION DES MAPPINGS - Step 2.3")
        print("=" * 80)
        print()
        
        # 1. Récupérer ou créer la propriété par défaut
        default_property = get_or_create_default_property(db)
        property_id = default_property.id
        
        # 2. Assigner tous les mappings existants à la propriété par défaut
        print("\n📋 ÉTAPE 1 : Assignation des mappings existants")
        print("-" * 80)
        
        mappings_without_property = db.query(Mapping).filter(
            Mapping.property_id.is_(None)
        ).count()
        
        if mappings_without_property > 0:
            print(f"   {mappings_without_property} mapping(s) sans property_id trouvé(s)")
            updated = db.query(Mapping).filter(
                Mapping.property_id.is_(None)
            ).update({Mapping.property_id: property_id}, synchronize_session=False)
            db.commit()
            print(f"✅ {updated} mapping(s) assigné(s) à property_id={property_id}")
        else:
            print("✅ Tous les mappings ont déjà un property_id")
        
        # Vérifier qu'il n'y a plus de mappings sans property_id
        remaining = db.query(Mapping).filter(Mapping.property_id.is_(None)).count()
        if remaining > 0:
            print(f"❌ ERREUR: {remaining} mapping(s) ont encore property_id=NULL")
            return False
        
        # 3. Assigner tous les mappings autorisés existants à la propriété par défaut
        print("\n📋 ÉTAPE 2 : Assignation des mappings autorisés existants")
        print("-" * 80)
        
        allowed_without_property = db.query(AllowedMapping).filter(
            AllowedMapping.property_id.is_(None)
        ).count()
        
        if allowed_without_property > 0:
            print(f"   {allowed_without_property} mapping(s) autorisé(s) sans property_id trouvé(s)")
            updated = db.query(AllowedMapping).filter(
                AllowedMapping.property_id.is_(None)
            ).update({AllowedMapping.property_id: property_id}, synchronize_session=False)
            db.commit()
            print(f"✅ {updated} mapping(s) autorisé(s) assigné(s) à property_id={property_id}")
        else:
            print("✅ Tous les mappings autorisés ont déjà un property_id")
        
        # Vérifier qu'il n'y a plus de mappings autorisés sans property_id
        remaining = db.query(AllowedMapping).filter(AllowedMapping.property_id.is_(None)).count()
        if remaining > 0:
            print(f"❌ ERREUR: {remaining} mapping(s) autorisé(s) ont encore property_id=NULL")
            return False
        
        # 4. Assigner tous les imports de mappings existants à la propriété par défaut
        print("\n📋 ÉTAPE 3 : Assignation des imports de mappings existants")
        print("-" * 80)
        
        imports_without_property = db.query(MappingImport).filter(
            MappingImport.property_id.is_(None)
        ).count()
        
        if imports_without_property > 0:
            print(f"   {imports_without_property} import(s) sans property_id trouvé(s)")
            updated = db.query(MappingImport).filter(
                MappingImport.property_id.is_(None)
            ).update({MappingImport.property_id: property_id}, synchronize_session=False)
            db.commit()
            print(f"✅ {updated} import(s) assigné(s) à property_id={property_id}")
        else:
            print("✅ Tous les imports ont déjà un property_id")
        
        # 5. Initialiser les mappings hardcodés pour la propriété par défaut
        print("\n📋 ÉTAPE 4 : Initialisation des mappings hardcodés")
        print("-" * 80)
        
        # Vérifier si des mappings hardcodés existent déjà pour cette propriété
        existing_hardcoded = db.query(AllowedMapping).filter(
            AllowedMapping.property_id == property_id,
            AllowedMapping.is_hardcoded == True
        ).count()
        
        if existing_hardcoded > 0:
            print(f"✅ {existing_hardcoded} mapping(s) hardcodé(s) existent déjà pour cette propriété")
        else:
            print("   Initialisation des mappings hardcodés depuis le fichier Excel...")
            
            # Chemin du fichier Excel
            project_root = Path(__file__).parent.parent.parent
            excel_path = project_root / "scripts" / "mappings_obligatoires.xlsx"
            
            if not excel_path.exists():
                print(f"⚠️  Fichier Excel non trouvé: {excel_path}")
                print("   Les mappings hardcodés ne seront pas initialisés automatiquement")
                print("   Vous pouvez les initialiser manuellement via l'interface ou le script d'initialisation")
            else:
                try:
                    loaded_count = load_allowed_mappings_from_excel(db, property_id, excel_path)
                    print(f"✅ {loaded_count} mapping(s) hardcodé(s) initialisé(s) pour property_id={property_id}")
                except Exception as e:
                    print(f"❌ ERREUR lors de l'initialisation des mappings hardcodés: {e}")
                    return False
        
        # 6. Vérification finale
        print("\n📋 ÉTAPE 5 : Vérification finale")
        print("-" * 80)
        
        mappings_count = db.query(Mapping).filter(Mapping.property_id == property_id).count()
        allowed_count = db.query(AllowedMapping).filter(AllowedMapping.property_id == property_id).count()
        imports_count = db.query(MappingImport).filter(MappingImport.property_id == property_id).count()
        
        print(f"✅ Mappings pour property_id={property_id}: {mappings_count}")
        print(f"✅ Mappings autorisés pour property_id={property_id}: {allowed_count}")
        print(f"✅ Imports pour property_id={property_id}: {imports_count}")
        
        # Vérifier qu'il n'y a aucun mapping orphelin
        orphan_mappings = db.query(Mapping).filter(Mapping.property_id.is_(None)).count()
        orphan_allowed = db.query(AllowedMapping).filter(AllowedMapping.property_id.is_(None)).count()
        orphan_imports = db.query(MappingImport).filter(MappingImport.property_id.is_(None)).count()
        
        if orphan_mappings > 0 or orphan_allowed > 0 or orphan_imports > 0:
            print(f"\n❌ ERREUR: Des mappings orphelins existent encore:")
            if orphan_mappings > 0:
                print(f"   - {orphan_mappings} mapping(s) avec property_id=NULL")
            if orphan_allowed > 0:
                print(f"   - {orphan_allowed} mapping(s) autorisé(s) avec property_id=NULL")
            if orphan_imports > 0:
                print(f"   - {orphan_imports} import(s) avec property_id=NULL")
            return False
        
        print("\n✅ Aucun mapping orphelin (property_id=NULL)")
        print("\n" + "=" * 80)
        print("✅ MIGRATION TERMINÉE AVEC SUCCÈS")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    # Demander confirmation (sauf si --yes en argument)
    if '--yes' not in sys.argv:
        print("⚠️  Ce script va migrer tous les mappings existants vers la propriété par défaut")
        print("   et initialiser les mappings hardcodés pour cette propriété.")
        response = input("\nContinuer ? (oui/non): ")
        
        if response.lower() not in ['oui', 'o', 'yes', 'y']:
            print("❌ Opération annulée")
            sys.exit(0)
    
    success = migrate_mappings(None)  # property_id sera déterminé dans la fonction
    
    if success:
        print("\n✅ Script terminé avec succès")
        sys.exit(0)
    else:
        print("\n❌ Script terminé avec erreur")
        sys.exit(1)
