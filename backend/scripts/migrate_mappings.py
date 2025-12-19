"""
Script de migration des mappings depuis mapping.xlsx vers la table mappings.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce script lit le fichier scripts/mapping.xlsx et insère tous les mappings
dans la table mappings de la base de données.
"""

import sys
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.database.models import Mapping


def migrate_mappings():
    """
    Migre les mappings depuis mapping.xlsx vers la table mappings.
    """
    # Initialize database to ensure tables exist
    init_database()
    
    # Chemin vers le fichier Excel
    mapping_file = project_root / "scripts" / "mapping.xlsx"
    
    if not mapping_file.exists():
        print(f"❌ Erreur: Le fichier {mapping_file} n'existe pas")
        return
    
    print(f"📖 Lecture du fichier: {mapping_file}")
    
    # Lire le fichier Excel
    try:
        df = pd.read_excel(mapping_file)
        print(f"✅ Fichier lu avec succès: {len(df)} lignes trouvées")
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier Excel: {str(e)}")
        return
    
    # Vérifier les colonnes
    required_columns = ['nom', 'level 1', 'level 2', 'level 3']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"❌ Erreur: Colonnes manquantes dans le fichier Excel: {missing_columns}")
        print(f"   Colonnes trouvées: {list(df.columns)}")
        return
    
    # Normaliser les noms de colonnes (supprimer espaces)
    df.columns = df.columns.str.strip()
    
    # Détecter et supprimer les doublons dans le fichier Excel
    initial_count = len(df)
    df = df.drop_duplicates(subset=['nom'], keep='first')
    duplicates_in_file = initial_count - len(df)
    if duplicates_in_file > 0:
        print(f"⚠️  {duplicates_in_file} doublon(s) détecté(s) dans le fichier Excel - supprimés")
    
    db = SessionLocal()
    try:
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        print(f"\n🔄 Import des mappings...")
        
        for index, row in df.iterrows():
            nom = str(row['nom']).strip() if pd.notna(row['nom']) else None
            level_1 = str(row['level 1']).strip() if pd.notna(row['level 1']) else None
            level_2 = str(row['level 2']).strip() if pd.notna(row['level 2']) else None
            level_3 = str(row['level 3']).strip() if pd.notna(row['level 3']) else None
            
            # Validation
            if not nom or not level_1 or not level_2:
                print(f"⚠️  Ligne {index + 1}: Données incomplètes (nom, level_1 ou level_2 manquant) - ignorée")
                error_count += 1
                continue
            
            # Vérifier si le mapping existe déjà
            existing = db.query(Mapping).filter(Mapping.nom == nom).first()
            if existing:
                print(f"⏭️  Ligne {index + 1}: Mapping '{nom}' existe déjà - ignoré")
                skipped_count += 1
                continue
            
            # Créer le nouveau mapping
            try:
                mapping = Mapping(
                    nom=nom,
                    level_1=level_1,
                    level_2=level_2,
                    level_3=level_3 if level_3 else None,
                    is_prefix_match=True,  # Par défaut, matching par préfixe
                    priority=0
                )
                db.add(mapping)
                imported_count += 1
                
                # Commit après chaque mapping pour éviter les problèmes de doublons
                try:
                    db.commit()
                except Exception as commit_error:
                    db.rollback()
                    # Vérifier si c'est un doublon (peut arriver si plusieurs processus tournent en même temps)
                    existing = db.query(Mapping).filter(Mapping.nom == nom).first()
                    if existing:
                        print(f"⏭️  Ligne {index + 1}: Mapping '{nom}' existe maintenant - ignoré")
                        skipped_count += 1
                        imported_count -= 1
                    else:
                        print(f"❌ Ligne {index + 1}: Erreur lors du commit pour '{nom}': {str(commit_error)}")
                        error_count += 1
                        imported_count -= 1
                    continue
                
                if (imported_count + skipped_count + error_count) % 10 == 0:
                    print(f"   Progression: {imported_count} importés, {skipped_count} ignorés, {error_count} erreurs")
                    
            except Exception as e:
                db.rollback()
                print(f"❌ Ligne {index + 1}: Erreur lors de l'import de '{nom}': {str(e)}")
                error_count += 1
                continue
        
        print(f"\n📊 Statistiques de migration:")
        print(f"   ✅ {imported_count} mapping(s) importé(s)")
        print(f"   ⏭️  {skipped_count} mapping(s) ignoré(s) (déjà existants)")
        print(f"   ❌ {error_count} erreur(s)")
        print(f"   📝 Total traité: {len(df)} lignes")
        
        # Vérifier le nombre total de mappings dans la DB
        total_mappings = db.query(Mapping).count()
        print(f"\n📈 Total de mappings dans la base de données: {total_mappings}")
        
        if imported_count > 0:
            print(f"✅ Migration terminée avec succès!")
        else:
            print(f"ℹ️  Aucun nouveau mapping importé (tous existaient déjà ou avaient des erreurs)")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors de la migration: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🔄 Migration des mappings depuis mapping.xlsx...")
    print("=" * 60)
    migrate_mappings()
    print("=" * 60)
    print("✅ Migration terminée")

