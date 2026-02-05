"""
Script pour diagnostiquer pourquoi certaines propriétés ont plus de mappings hardcodés que prévu.
"""

import sys
from pathlib import Path
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import get_db
from backend.database.models import Property, AllowedMapping

def diagnose():
    """Diagnostiquer les problèmes avec les mappings autorisés."""
    db = next(get_db())
    
    print("="*80)
    print("🔍 DIAGNOSTIC DES MAPPINGS AUTORISÉS")
    print("="*80 + "\n")
    
    # Charger le fichier Excel de référence
    excel_path = project_root / "scripts" / "mappings_obligatoires.xlsx"
    if not excel_path.exists():
        print(f"❌ Fichier Excel non trouvé: {excel_path}")
        return
    
    df = pd.read_excel(excel_path)
    expected_mappings = set()
    for idx, row in df.iterrows():
        level_1 = str(row['Level 1']).strip() if pd.notna(row['Level 1']) else None
        level_2 = str(row['Level 2']).strip() if pd.notna(row['Level 2']) else None
        level_3 = str(row['Level 3']).strip() if pd.notna(row['Level 3']) else None
        
        if level_1 and level_2:
            key = (level_1, level_2, level_3 if level_3 else None)
            expected_mappings.add(key)
    
    print(f"📄 Fichier Excel de référence: {len(expected_mappings)} mappings attendus\n")
    
    # Pour chaque propriété
    properties = db.query(Property).order_by(Property.id).all()
    
    for prop in properties:
        print(f"🏠 {prop.name} (ID: {prop.id})")
        print("-" * 80)
        
        # Récupérer tous les mappings hardcodés
        hardcoded_mappings = db.query(AllowedMapping).filter(
            AllowedMapping.property_id == prop.id,
            AllowedMapping.is_hardcoded == True
        ).all()
        
        print(f"   Mappings hardcodés dans la DB: {len(hardcoded_mappings)}")
        print(f"   Mappings attendus (Excel): {len(expected_mappings)}")
        
        if len(hardcoded_mappings) != len(expected_mappings):
            print(f"   ⚠️  DIFFÉRENCE: {len(hardcoded_mappings) - len(expected_mappings)} mappings en trop/manquants")
        
        # Vérifier les doublons (même combinaison level_1, level_2, level_3)
        mapping_keys = {}
        duplicates = []
        for m in hardcoded_mappings:
            key = (m.level_1, m.level_2, m.level_3)
            if key in mapping_keys:
                duplicates.append((m.id, mapping_keys[key], key))
            else:
                mapping_keys[key] = m.id
        
        if duplicates:
            print(f"   ❌ DOUBLONS DÉTECTÉS: {len(duplicates)} combinaisons en double")
            for dup_id, original_id, key in duplicates[:5]:  # Afficher les 5 premiers
                print(f"      - ID {dup_id} duplique ID {original_id}: {key[0]} > {key[1]} > {key[2]}")
        else:
            print(f"   ✅ Aucun doublon détecté")
        
        # Vérifier les mappings qui ne sont pas dans le fichier Excel
        db_mapping_keys = set((m.level_1, m.level_2, m.level_3) for m in hardcoded_mappings)
        unexpected = db_mapping_keys - expected_mappings
        
        if unexpected:
            print(f"   ⚠️  MAPPINGS INATTENDUS (pas dans Excel): {len(unexpected)}")
            for key in list(unexpected)[:5]:  # Afficher les 5 premiers
                print(f"      - {key[0]} > {key[1]} > {key[2]}")
        
        # Vérifier les mappings manquants (dans Excel mais pas en DB)
        missing = expected_mappings - db_mapping_keys
        
        if missing:
            print(f"   ⚠️  MAPPINGS MANQUANTS (dans Excel mais pas en DB): {len(missing)}")
            for key in list(missing)[:5]:  # Afficher les 5 premiers
                print(f"      - {key[0]} > {key[1]} > {key[2]}")
        
        print()
    
    print("="*80)
    print("✅ Diagnostic terminé")
    print("="*80)

if __name__ == "__main__":
    diagnose()
