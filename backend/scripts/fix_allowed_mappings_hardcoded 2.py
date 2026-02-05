"""
Script pour corriger les mappings hardcodés et s'assurer que toutes les propriétés
ont exactement les mêmes 49 mappings hardcodés depuis le fichier Excel.
"""

import sys
from pathlib import Path
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import get_db
from backend.database.models import Property, AllowedMapping

def fix_hardcoded_mappings():
    """Corriger les mappings hardcodés pour toutes les propriétés."""
    db = next(get_db())
    
    print("="*80)
    print("🔧 CORRECTION DES MAPPINGS HARDCODÉS")
    print("="*80 + "\n")
    
    # Charger le fichier Excel de référence
    excel_path = project_root / "scripts" / "mappings_obligatoires.xlsx"
    if not excel_path.exists():
        print(f"❌ Fichier Excel non trouvé: {excel_path}")
        return False
    
    df = pd.read_excel(excel_path)
    expected_mappings = []
    for idx, row in df.iterrows():
        level_1 = str(row['Level 1']).strip() if pd.notna(row['Level 1']) else None
        level_2 = str(row['Level 2']).strip() if pd.notna(row['Level 2']) else None
        level_3 = str(row['Level 3']).strip() if pd.notna(row['Level 3']) else None
        
        if level_1 and level_2:
            expected_mappings.append((level_1, level_2, level_3 if level_3 else None))
    
    print(f"📄 Fichier Excel: {len(expected_mappings)} mappings de référence\n")
    
    # Pour chaque propriété
    properties = db.query(Property).order_by(Property.id).all()
    total_fixed = 0
    
    for prop in properties:
        print(f"🏠 {prop.name} (ID: {prop.id})")
        print("-" * 80)
        
        # Récupérer tous les mappings hardcodés actuels
        current_hardcoded = db.query(AllowedMapping).filter(
            AllowedMapping.property_id == prop.id,
            AllowedMapping.is_hardcoded == True
        ).all()
        
        current_keys = set((m.level_1, m.level_2, m.level_3) for m in current_hardcoded)
        expected_keys = set(expected_mappings)
        
        # Supprimer les mappings hardcodés qui ne sont pas dans le fichier Excel
        to_remove = current_keys - expected_keys
        if to_remove:
            print(f"   🗑️  Suppression de {len(to_remove)} mappings hardcodés inattendus...")
            for key in to_remove:
                mapping = db.query(AllowedMapping).filter(
                    AllowedMapping.property_id == prop.id,
                    AllowedMapping.level_1 == key[0],
                    AllowedMapping.level_2 == key[1],
                    AllowedMapping.level_3 == key[2] if key[2] else None,
                    AllowedMapping.is_hardcoded == True
                ).first()
                if mapping:
                    db.delete(mapping)
                    print(f"      - Supprimé: {key[0]} > {key[1]} > {key[2]}")
            total_fixed += len(to_remove)
        
        # Ajouter les mappings manquants
        to_add = expected_keys - current_keys
        if to_add:
            print(f"   ➕ Ajout de {len(to_add)} mappings hardcodés manquants...")
            for key in to_add:
                # Vérifier si un mapping existe déjà (mais pas hardcodé)
                existing = db.query(AllowedMapping).filter(
                    AllowedMapping.property_id == prop.id,
                    AllowedMapping.level_1 == key[0],
                    AllowedMapping.level_2 == key[1],
                    AllowedMapping.level_3 == key[2] if key[2] else None
                ).first()
                
                if existing:
                    # Mettre à jour pour le marquer comme hardcodé
                    existing.is_hardcoded = True
                    print(f"      - Mis à jour (hardcodé): {key[0]} > {key[1]} > {key[2]}")
                else:
                    # Créer un nouveau mapping hardcodé
                    new_mapping = AllowedMapping(
                        property_id=prop.id,
                        level_1=key[0],
                        level_2=key[1],
                        level_3=key[2],
                        is_hardcoded=True
                    )
                    db.add(new_mapping)
                    print(f"      - Créé: {key[0]} > {key[1]} > {key[2]}")
            total_fixed += len(to_add)
        
        # Vérifier le résultat final
        final_count = db.query(AllowedMapping).filter(
            AllowedMapping.property_id == prop.id,
            AllowedMapping.is_hardcoded == True
        ).count()
        
        if final_count == len(expected_mappings):
            print(f"   ✅ Correction terminée: {final_count} mappings hardcodés (correct)")
        else:
            print(f"   ⚠️  Correction terminée: {final_count} mappings hardcodés (attendu: {len(expected_mappings)})")
        
        print()
    
    # Commit toutes les modifications
    try:
        db.commit()
        print("="*80)
        print(f"✅ Correction terminée: {total_fixed} modifications effectuées")
        print("="*80)
        return True
    except Exception as e:
        print(f"❌ Erreur lors du commit: {e}")
        db.rollback()
        return False

if __name__ == "__main__":
    success = fix_hardcoded_mappings()
    exit(0 if success else 1)
