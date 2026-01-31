"""
Migration: Add property_id to amortization_types table.

This script adds the property_id column to the amortization_types table
to support multi-property isolation.

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sqlite3
from pathlib import Path

# Database path
DB_DIR = Path(__file__).parent.parent
DB_FILE = DB_DIR / "lmnp.db"


def migrate():
    """Add property_id to amortization_types table."""
    if not DB_FILE.exists():
        print(f"Database file not found: {DB_FILE}")
        return False
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    try:
        print("=== Ajout de property_id à amortization_types ===\n")
        
        # 1. Vérifier si la colonne existe déjà
        print("📋 Vérification de la colonne property_id...")
        cursor.execute("PRAGMA table_info(amortization_types)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'property_id' in columns:
            print("✅ La colonne property_id existe déjà")
            
            # Vérifier si tous les enregistrements ont un property_id
            cursor.execute("SELECT COUNT(*) FROM amortization_types WHERE property_id IS NULL")
            null_count = cursor.fetchone()[0]
            
            if null_count > 0:
                print(f"⚠️  {null_count} amortization_type(s) ont property_id=NULL")
                print("   Assignation à la propriété par défaut...")
                
                # Récupérer la première propriété
                cursor.execute("SELECT id FROM properties ORDER BY id LIMIT 1")
                first_property = cursor.fetchone()
                if not first_property:
                    print("❌ ERREUR: Aucune propriété n'existe dans la table properties")
                    print("   Veuillez créer au moins une propriété avant d'exécuter cette migration")
                    return False
                
                default_property_id = first_property[0]
                cursor.execute(f"UPDATE amortization_types SET property_id = {default_property_id} WHERE property_id IS NULL")
                conn.commit()
                print(f"✅ {null_count} amortization_type(s) mis à jour avec property_id={default_property_id}")
            else:
                print("✅ Tous les amortization_types ont déjà un property_id")
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
            
            # Compter les amortization_types existants
            cursor.execute("SELECT COUNT(*) FROM amortization_types")
            types_count = cursor.fetchone()[0]
            print(f"   {types_count} amortization_type(s) existant(s) à mettre à jour")
            
            # Ajouter la colonne property_id (sans NOT NULL d'abord)
            cursor.execute("ALTER TABLE amortization_types ADD COLUMN property_id INTEGER")
            
            # Assigner property_id par défaut à tous les amortization_types existants
            if types_count > 0:
                cursor.execute(f"UPDATE amortization_types SET property_id = {default_property_id} WHERE property_id IS NULL")
                print(f"✅ {types_count} amortization_type(s) mis à jour avec property_id={default_property_id}")
            
            conn.commit()
            print("✅ Colonne property_id ajoutée avec succès")
        
        # 2. Vérifier/Créer l'index sur property_id
        print("\n📋 Vérification de l'index idx_amortization_types_property_id...")
        cursor.execute("PRAGMA index_list(amortization_types)")
        indexes = [idx[1] for idx in cursor.fetchall()]
        
        if 'idx_amortization_types_property_id' in indexes:
            print("✅ Index idx_amortization_types_property_id présent")
        else:
            print("📋 Création de l'index idx_amortization_types_property_id...")
            cursor.execute("""
                CREATE INDEX idx_amortization_types_property_id 
                ON amortization_types(property_id)
            """)
            conn.commit()
            print("✅ Index créé")
        
        # 3. Vérifier/Créer la contrainte FOREIGN KEY
        print("\n📋 Vérification de la contrainte FOREIGN KEY...")
        # SQLite ne supporte pas ALTER TABLE ADD CONSTRAINT directement
        # La contrainte sera gérée par SQLAlchemy via le modèle
        print("ℹ️  La contrainte FOREIGN KEY sera gérée par SQLAlchemy via le modèle")
        
        # 4. Vérification finale
        print("\n📋 Vérification finale...")
        cursor.execute("SELECT COUNT(*) FROM amortization_types WHERE property_id IS NULL")
        null_count = cursor.fetchone()[0]
        if null_count > 0:
            print(f"❌ ERREUR: {null_count} amortization_type(s) ont encore property_id=NULL")
            return False
        
        cursor.execute("SELECT COUNT(*) FROM amortization_types")
        total = cursor.fetchone()[0]
        print(f"✅ Total amortization_types: {total}")
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
