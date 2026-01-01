"""
Script pour charger les mappings autorisés depuis le fichier Excel mappings_default.xlsx.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python3 backend/scripts/load_allowed_mappings_from_excel.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pandas as pd
from pathlib import Path
from backend.database import SessionLocal
from backend.database.models import AllowedMapping


def load_allowed_mappings_from_excel(excel_path: str = None):
    """
    Charge les mappings autorisés depuis le fichier Excel.
    
    Args:
        excel_path: Chemin vers le fichier Excel (par défaut: scripts/mappings_default.xlsx)
    """
    if excel_path is None:
        # Chemin par défaut
        project_root = Path(__file__).parent.parent.parent
        excel_path = project_root / "scripts" / "mappings_default.xlsx"
    
    if not os.path.exists(excel_path):
        print(f"❌ Fichier Excel non trouvé: {excel_path}")
        print("   Veuillez créer le fichier mappings_default.xlsx avec les colonnes: level_1, level_2, level_3")
        return False
    
    print(f"📂 Chargement du fichier: {excel_path}")
    
    try:
        # Lire le fichier Excel
        df = pd.read_excel(excel_path)
        
        # Normaliser les noms de colonnes (supprimer espaces, convertir en minuscules)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Vérifier les colonnes requises
        required_columns = ['level_1', 'level_2']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"❌ Colonnes manquantes dans le fichier Excel: {missing_columns}")
            print(f"   Colonnes trouvées: {list(df.columns)}")
            return False
        
        # Vérifier si level_3 existe (optionnel)
        has_level3 = 'level_3' in df.columns
        
        print(f"✅ Fichier Excel chargé: {len(df)} lignes")
        print(f"   Colonnes: {list(df.columns)}")
        print()
        
        db = SessionLocal()
        try:
            # Compter les doublons qui seront ignorés
            duplicates_count = 0
            inserted_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                level_1 = str(row['level_1']).strip() if pd.notna(row['level_1']) else None
                level_2 = str(row['level_2']).strip() if pd.notna(row['level_2']) else None
                level_3 = str(row['level_3']).strip() if has_level3 and pd.notna(row['level_3']) else None
                
                # Convertir les chaînes vides en None
                if level_3 == '':
                    level_3 = None
                
                # Validation
                if not level_1 or not level_2:
                    print(f"⚠️  Ligne {index + 2}: level_1 ou level_2 manquant, ignorée")
                    error_count += 1
                    continue
                
                # Vérifier si le mapping existe déjà
                existing = db.query(AllowedMapping).filter(
                    AllowedMapping.level_1 == level_1,
                    AllowedMapping.level_2 == level_2,
                    AllowedMapping.level_3 == level_3 if level_3 else AllowedMapping.level_3.is_(None)
                ).first()
                
                if existing:
                    duplicates_count += 1
                    continue
                
                # Créer le nouveau mapping
                new_mapping = AllowedMapping(
                    level_1=level_1,
                    level_2=level_2,
                    level_3=level_3
                )
                db.add(new_mapping)
                inserted_count += 1
            
            # Commit toutes les insertions
            db.commit()
            
            print("=" * 60)
            print("📊 Résultats du chargement:")
            print(f"   ✅ Mappings insérés: {inserted_count}")
            print(f"   ⚠️  Doublons ignorés: {duplicates_count}")
            print(f"   ❌ Erreurs: {error_count}")
            print(f"   📈 Total en BDD: {db.query(AllowedMapping).count()}")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            db.rollback()
            print(f"❌ Erreur lors de l'insertion en BDD: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier Excel: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Chargement des mappings autorisés depuis Excel")
    print("=" * 60)
    print()
    
    success = load_allowed_mappings_from_excel()
    
    print()
    if success:
        print("=" * 60)
        print("✅ Terminé avec succès !")
        print("=" * 60)
    else:
        print("=" * 60)
        print("❌ Échec du chargement")
        print("=" * 60)
        sys.exit(1)

