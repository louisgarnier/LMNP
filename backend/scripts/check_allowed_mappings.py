"""
Script de diagnostic pour vérifier les mappings autorisés par propriété.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import get_db
from backend.database.models import AllowedMapping, Property

def check_allowed_mappings():
    """Vérifier les mappings autorisés par propriété."""
    db = next(get_db())
    
    print("=== DIAGNOSTIC DES MAPPINGS AUTORISÉS ===\n")
    
    # Lister toutes les propriétés
    properties = db.query(Property).all()
    print(f"📋 Propriétés trouvées: {len(properties)}")
    for prop in properties:
        print(f"  - ID: {prop.id}, Nom: {prop.name}")
    
    print("\n" + "="*60 + "\n")
    
    # Pour chaque propriété, compter les mappings autorisés
    for prop in properties:
        mappings = db.query(AllowedMapping).filter(
            AllowedMapping.property_id == prop.id
        ).all()
        
        hardcoded = [m for m in mappings if m.is_hardcoded]
        manual = [m for m in mappings if not m.is_hardcoded]
        
        print(f"🏠 Propriété: {prop.name} (ID: {prop.id})")
        print(f"   Total mappings autorisés: {len(mappings)}")
        print(f"   - Hardcodés (protégés): {len(hardcoded)}")
        print(f"   - Manuels (ajoutés): {len(manual)}")
        
        if len(mappings) > 0:
            print(f"\n   Exemples (5 premiers):")
            for m in mappings[:5]:
                level_3_str = m.level_3 if m.level_3 else "NULL"
                print(f"   - ID {m.id}: {m.level_1} > {m.level_2} > {level_3_str} (hardcoded={m.is_hardcoded})")
        else:
            print(f"   ⚠️  AUCUN MAPPING AUTORISÉ pour cette propriété!")
        
        print()
    
    # Vérifier s'il y a des mappings sans property_id
    mappings_without_property = db.query(AllowedMapping).filter(
        AllowedMapping.property_id.is_(None)
    ).count()
    
    if mappings_without_property > 0:
        print(f"⚠️  ATTENTION: {mappings_without_property} mappings autorisés sans property_id!")
    
    # Vérifier s'il y a des mappings avec property_id invalide
    invalid_property_ids = db.query(AllowedMapping.property_id).distinct().all()
    valid_property_ids = [p.id for p in properties]
    
    invalid_count = 0
    for prop_id_tuple in invalid_property_ids:
        prop_id = prop_id_tuple[0]
        if prop_id not in valid_property_ids:
            invalid_count += db.query(AllowedMapping).filter(
                AllowedMapping.property_id == prop_id
            ).count()
    
    if invalid_count > 0:
        print(f"⚠️  ATTENTION: {invalid_count} mappings autorisés avec property_id invalide!")
    
    print("\n" + "="*60)
    print("✅ Diagnostic terminé")

if __name__ == "__main__":
    check_allowed_mappings()
