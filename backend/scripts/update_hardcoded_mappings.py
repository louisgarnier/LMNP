"""
Script pour mettre à jour les mappings hardcodés depuis le fichier Excel.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce script :
1. Supprime tous les mappings hardcodés (is_hardcoded = True) qui ne sont plus dans le fichier Excel
2. Ajoute/marque comme hardcodés les mappings du fichier Excel
3. Conserve les mappings avec is_hardcoded = False (ajoutés manuellement)

Usage:
    python backend/scripts/update_hardcoded_mappings.py
"""

import sys
from pathlib import Path
import pandas as pd

# Ajouter le chemin du projet au PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.database.models import AllowedMapping
from backend.api.services.mapping_obligatoire_service import validate_level3_value


def load_mappings_from_excel(excel_path: Path) -> list:
    """
    Charge les mappings depuis le fichier Excel.
    
    Returns:
        Liste de tuples (level_1, level_2, level_3)
    """
    if not excel_path.exists():
        raise FileNotFoundError(f"Le fichier Excel n'existe pas : {excel_path}")
    
    # Lire le fichier Excel
    try:
        df = pd.read_excel(excel_path, engine='openpyxl')
    except Exception as e:
        raise ValueError(f"Erreur lors de la lecture du fichier Excel : {str(e)}")
    
    # Vérifier les colonnes attendues
    expected_columns = ['Level 1', 'Level 2', 'Level 3']
    if not all(col in df.columns for col in expected_columns):
        raise ValueError(f"Le fichier Excel doit contenir les colonnes : {expected_columns}")
    
    mappings = []
    for _, row in df.iterrows():
        level_1 = str(row['Level 1']).strip() if pd.notna(row['Level 1']) else None
        level_2 = str(row['Level 2']).strip() if pd.notna(row['Level 2']) else None
        level_3 = str(row['Level 3']).strip() if pd.notna(row['Level 3']) else None
        
        # Validation : level_1 et level_2 sont obligatoires
        if not level_1 or not level_2:
            continue  # Ignorer les lignes invalides
        
        # Validation : level_3 doit être dans la liste fixe (si fourni)
        if level_3 and not validate_level3_value(level_3):
            print(f"⚠️  Ignoré : level_3 invalide '{level_3}' pour ({level_1}, {level_2})")
            continue  # Ignorer les lignes avec level_3 invalide
        
        # Normaliser level_3 : None si vide
        level_3 = level_3 if level_3 else None
        
        mappings.append((level_1, level_2, level_3))
    
    return mappings


def update_hardcoded_mappings(db, excel_mappings: list):
    """
    Met à jour les mappings hardcodés :
    1. Supprime les mappings hardcodés qui ne sont plus dans le fichier Excel
    2. Ajoute/marque comme hardcodés les mappings du fichier Excel
    3. Conserve les mappings avec is_hardcoded = False
    
    Args:
        db: Session de base de données
        excel_mappings: Liste de tuples (level_1, level_2, level_3) depuis Excel
    """
    # Créer un set pour faciliter les recherches
    excel_mappings_set = set(excel_mappings)
    
    # 1. Récupérer tous les mappings hardcodés actuels
    hardcoded_mappings = db.query(AllowedMapping).filter(
        AllowedMapping.is_hardcoded == True
    ).all()
    
    deleted_count = 0
    added_count = 0
    updated_count = 0
    
    # 2. Supprimer les mappings hardcodés qui ne sont plus dans le fichier Excel
    for mapping in hardcoded_mappings:
        mapping_tuple = (mapping.level_1, mapping.level_2, mapping.level_3)
        if mapping_tuple not in excel_mappings_set:
            print(f"🗑️  Suppression : {mapping_tuple}")
            db.delete(mapping)
            deleted_count += 1
    
    # 3. Ajouter/mettre à jour les mappings du fichier Excel
    for level_1, level_2, level_3 in excel_mappings:
        # Chercher si le mapping existe déjà
        query = db.query(AllowedMapping).filter(
            AllowedMapping.level_1 == level_1,
            AllowedMapping.level_2 == level_2
        )
        if level_3:
            query = query.filter(AllowedMapping.level_3 == level_3)
        else:
            query = query.filter(AllowedMapping.level_3.is_(None))
        
        existing = query.first()
        
        if existing:
            # Mettre à jour is_hardcoded si nécessaire
            if not existing.is_hardcoded:
                existing.is_hardcoded = True
                print(f"✅ Mis à jour (hardcodé) : ({level_1}, {level_2}, {level_3})")
                updated_count += 1
            # else: déjà hardcodé, rien à faire
        else:
            # Créer le nouveau mapping
            try:
                new_mapping = AllowedMapping(
                    level_1=level_1,
                    level_2=level_2,
                    level_3=level_3,
                    is_hardcoded=True
                )
                db.add(new_mapping)
                print(f"➕ Ajouté : ({level_1}, {level_2}, {level_3})")
                added_count += 1
            except Exception as e:
                # Ignorer les doublons (contrainte unique)
                print(f"⚠️  Erreur lors de l'ajout de ({level_1}, {level_2}, {level_3}): {e}")
                db.rollback()
                continue
    
    return deleted_count, added_count, updated_count


def main():
    """Met à jour les mappings hardcodés depuis le fichier Excel."""
    print("=" * 60)
    print("Mise à jour des mappings hardcodés depuis Excel")
    print("=" * 60)
    
    # Initialiser la base de données (créer les tables si nécessaire)
    print("\n1. Initialisation de la base de données...")
    init_database()
    print("   ✓ Base de données initialisée")
    
    # Chemin du fichier Excel
    excel_path = project_root / "scripts" / "mappings_obligatoires.xlsx"
    
    if not excel_path.exists():
        print(f"\n✗ ERREUR : Le fichier n'existe pas : {excel_path}")
        print("   Veuillez vérifier que le fichier est présent dans scripts/")
        return 1
    
    print(f"\n2. Lecture du fichier Excel...")
    print(f"   Fichier : {excel_path}")
    
    try:
        excel_mappings = load_mappings_from_excel(excel_path)
        print(f"   ✓ {len(excel_mappings)} combinaisons trouvées dans le fichier Excel")
    except Exception as e:
        print(f"\n✗ ERREUR lors de la lecture du fichier Excel : {e}")
        return 1
    
    # Créer une session
    db = SessionLocal()
    
    try:
        print(f"\n3. Mise à jour de la base de données...")
        
        # Compter les mappings manuels avant la mise à jour
        manual_mappings_count = db.query(AllowedMapping).filter(
            AllowedMapping.is_hardcoded == False
        ).count()
        
        deleted_count, added_count, updated_count = update_hardcoded_mappings(db, excel_mappings)
        
        db.commit()
        
        print(f"\n4. Résultat :")
        print(f"   ✓ {deleted_count} mappings hardcodés supprimés (absents du fichier Excel)")
        print(f"   ✓ {added_count} nouveaux mappings hardcodés ajoutés")
        print(f"   ✓ {updated_count} mappings existants marqués comme hardcodés")
        print(f"   ✓ {manual_mappings_count} mappings manuels conservés (is_hardcoded = False)")
        
        # Compter les mappings hardcodés après la mise à jour
        hardcoded_count = db.query(AllowedMapping).filter(
            AllowedMapping.is_hardcoded == True
        ).count()
        print(f"\n   Total mappings hardcodés après mise à jour : {hardcoded_count}")
        print(f"   Total mappings manuels : {manual_mappings_count}")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ ERREUR : {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        db.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
