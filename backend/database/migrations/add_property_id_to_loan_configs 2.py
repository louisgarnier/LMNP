"""
Migration: Add property_id to loan_configs table.

This script adds the property_id column to the loan_configs table
to support multi-property isolation.

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sqlite3
from pathlib import Path

# Database path
DB_DIR = Path(__file__).parent.parent
DB_FILE = DB_DIR / "lmnp.db"


def migrate():
    """Add property_id to loan_configs table."""
    if not DB_FILE.exists():
        print(f"Database file not found: {DB_FILE}")
        return False
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    try:
        print("=== Ajout de property_id à loan_configs ===\n")
        
        # 1. Vérifier si la colonne existe déjà
        print("📋 Vérification de la colonne property_id...")
        cursor.execute("PRAGMA table_info(loan_configs)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'property_id' in columns:
            print("✅ La colonne property_id existe déjà")
            
            # Vérifier si tous les enregistrements ont un property_id
            cursor.execute("SELECT COUNT(*) FROM loan_configs WHERE property_id IS NULL")
            null_count = cursor.fetchone()[0]
            
            if null_count > 0:
                print(f"⚠️  {null_count} loan_config(s) ont property_id=NULL")
                print("   Assignation à la propriété par défaut...")
                
                # Récupérer la première propriété
                cursor.execute("SELECT id FROM properties ORDER BY id LIMIT 1")
                first_property = cursor.fetchone()
                if not first_property:
                    print("❌ ERREUR: Aucune propriété n'existe dans la table properties")
                    print("   Veuillez créer au moins une propriété avant d'exécuter cette migration")
                    return False
                
                default_property_id = first_property[0]
                cursor.execute(f"UPDATE loan_configs SET property_id = {default_property_id} WHERE property_id IS NULL")
                conn.commit()
                print(f"✅ {null_count} loan_config(s) mis à jour avec property_id={default_property_id}")
            else:
                print("✅ Tous les loan_configs ont déjà un property_id")
        else:
            print("📋 Ajout de la colonne property_id...")
            
            # Vérifier qu'il existe au moins une propriété
            cursor.execute("SELECT id FROM properties ORDER BY id LIMIT 1")
            first_property = cursor.fetchone()
            if not first_property:
                print("❌ ERREUR: Aucune propriété n'existe dans la table properties")
                print("   Veuillez créer au moins une propriété avant d'exécuter cette migration")
                return False
            
            default_property_id = first_property[0]
            print(f"   Propriété par défaut: property_id={default_property_id}")
            
            # Compter les loan_configs existants
            cursor.execute("SELECT COUNT(*) FROM loan_configs")
            configs_count = cursor.fetchone()[0]
            print(f"   {configs_count} loan_config(s) existant(s) à mettre à jour")
            
            # Ajouter la colonne property_id (sans NOT NULL d'abord)
            cursor.execute("ALTER TABLE loan_configs ADD COLUMN property_id INTEGER")
            
            # Assigner property_id par défaut à tous les loan_configs existants
            if configs_count > 0:
                cursor.execute(f"UPDATE loan_configs SET property_id = {default_property_id} WHERE property_id IS NULL")
                print(f"✅ {configs_count} loan_config(s) mis à jour avec property_id={default_property_id}")
            
            conn.commit()
            print("✅ Colonne property_id ajoutée avec succès")
        
        # 2. Vérifier/Créer l'index sur property_id
        print("\n📋 Vérification de l'index idx_loan_configs_property_id...")
        cursor.execute("PRAGMA index_list(loan_configs)")
        indexes = [idx[1] for idx in cursor.fetchall()]
        
        if 'idx_loan_configs_property_id' in indexes:
            print("✅ Index idx_loan_configs_property_id présent")
        else:
            print("📋 Création de l'index idx_loan_configs_property_id...")
            cursor.execute("""
                CREATE INDEX idx_loan_configs_property_id 
                ON loan_configs(property_id)
            """)
            conn.commit()
            print("✅ Index créé")
        
        # 3. Vérifier/Créer l'index unique sur (property_id, name)
        print("\n📋 Vérification de l'index idx_loan_config_property_name...")
        if 'idx_loan_config_property_name' in indexes:
            print("✅ Index idx_loan_config_property_name présent")
        else:
            print("📋 Création de l'index idx_loan_config_property_name...")
            cursor.execute("""
                CREATE UNIQUE INDEX idx_loan_config_property_name 
                ON loan_configs(property_id, name)
            """)
            conn.commit()
            print("✅ Index unique créé")
        
        # 4. Supprimer l'ancien index unique sur name seul (si existe)
        print("\n📋 Vérification de l'ancien index unique sur name...")
        if 'idx_loan_config_name' in indexes:
            print("⚠️  Ancien index unique idx_loan_config_name trouvé")
            print("   Note: L'index sera recréé par SQLAlchemy si nécessaire")
        
        # 5. Vérifier/Créer la contrainte FOREIGN KEY
        print("\n📋 Vérification de la contrainte FOREIGN KEY...")
        # SQLite ne supporte pas ALTER TABLE ADD CONSTRAINT directement
        # La contrainte sera gérée par SQLAlchemy via le modèle
        print("ℹ️  La contrainte FOREIGN KEY sera gérée par SQLAlchemy via le modèle")
        
        # 6. Vérification finale
        print("\n📋 Vérification finale...")
        cursor.execute("SELECT COUNT(*) FROM loan_configs WHERE property_id IS NULL")
        null_count = cursor.fetchone()[0]
        if null_count > 0:
            print(f"❌ ERREUR: {null_count} loan_config(s) ont encore property_id=NULL")
            return False
        
        cursor.execute("SELECT COUNT(*) FROM loan_configs")
        total = cursor.fetchone()[0]
        print(f"✅ Total loan_configs: {total}")
        print(f"✅ Tous ont un property_id")
        
        print("\n" + "=" * 80)
        print("✅ MIGRATION TERMINÉE AVEC SUCCÈS")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    success = migrate()
    if not success:
        exit(1)
