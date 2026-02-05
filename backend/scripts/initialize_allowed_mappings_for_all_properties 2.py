"""
Script pour initialiser les mappings autorisés hardcodés pour toutes les propriétés.

Ce script charge les mappings autorisés depuis le fichier Excel et les crée pour chaque propriété.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import get_db
from backend.database.models import Property, AllowedMapping
from backend.api.services.mapping_obligatoire_service import load_allowed_mappings_from_excel

def initialize_allowed_mappings_for_all_properties():
    """Initialiser les mappings autorisés pour toutes les propriétés."""
    db = next(get_db())
    
    print("=== INITIALISATION DES MAPPINGS AUTORISÉS ===\n")
    
    # Lister toutes les propriétés
    properties = db.query(Property).all()
    print(f"📋 Propriétés trouvées: {len(properties)}")
    for prop in properties:
        print(f"  - ID: {prop.id}, Nom: {prop.name}")
    
    print("\n" + "="*60 + "\n")
    
    # Chemin vers le fichier Excel des mappings obligatoires
    excel_path = project_root / "scripts" / "mappings_obligatoires.xlsx"
    
    if not excel_path.exists():
        print(f"❌ ERREUR: Fichier Excel non trouvé: {excel_path}")
        print("   Veuillez vous assurer que le fichier existe.")
        return False
    
    print(f"📄 Fichier Excel: {excel_path}\n")
    
    # Pour chaque propriété, charger les mappings autorisés
    total_created = 0
    for prop in properties:
        print(f"🏠 Traitement de la propriété: {prop.name} (ID: {prop.id})")
        
        # Vérifier combien de mappings existent déjà
        existing_count = db.query(AllowedMapping).filter(
            AllowedMapping.property_id == prop.id
        ).count()
        
        print(f"   Mappings existants: {existing_count}")
        
        if existing_count > 0:
            print(f"   ⚠️  Des mappings existent déjà. Voulez-vous les recréer ?")
            print(f"   (Pour l'instant, on skip cette propriété)")
            continue
        
        # Charger les mappings depuis le fichier Excel
        try:
            created_count = load_allowed_mappings_from_excel(db, property_id=prop.id, excel_path=excel_path)
            print(f"   ✅ {created_count} mappings créés")
            total_created += created_count
            
        except Exception as e:
            print(f"   ❌ ERREUR lors du traitement: {e}")
            import traceback
            traceback.print_exc()
            db.rollback()
            continue
    
    print("\n" + "="*60)
    print(f"✅ Initialisation terminée: {total_created} mappings créés au total")
    
    return True

if __name__ == "__main__":
    success = initialize_allowed_mappings_for_all_properties()
    exit(0 if success else 1)
