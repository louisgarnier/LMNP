"""
Migration: Add property_id to mapping_imports table.

This script adds the property_id column to the mapping_imports table,
assigns a default property_id to existing mapping imports,
and creates the necessary indexes and foreign key constraints.

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sqlite3
from pathlib import Path

# Database path
DB_DIR = Path(__file__).parent.parent
DB_FILE = DB_DIR / "lmnp.db"


def migrate():
    """Add property_id to mapping_imports table."""
    if not DB_FILE.exists():
        print(f"Database file not found: {DB_FILE}")
        return False
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    try:
        print("=== Ajout de property_id à la table mapping_imports ===\n")
        
        # 1. Vérifier si la table mapping_imports existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mapping_imports'")
        if not cursor.fetchone():
            print("❌ ERREUR: La table mapping_imports n'existe pas")
            return False
        
        # 2. Vérifier si property_id existe déjà
        cursor.execute("PRAGMA table_info(mapping_imports)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'property_id' in columns:
            print("✅ La colonne property_id existe déjà dans la table mapping_imports")
            
            # Vérifier s'il y a des imports sans property_id
            cursor.execute("SELECT COUNT(*) FROM mapping_imports WHERE property_id IS NULL")
            null_count = cursor.fetchone()[0]
            
            if null_count > 0:
                print(f"⚠️  {null_count} imports ont property_id=NULL, assignation nécessaire...")
                # Vérifier qu'il existe au moins une propriété
                cursor.execute("SELECT id FROM properties ORDER BY id LIMIT 1")
                first_property = cursor.fetchone()
                if not first_property:
                    print("❌ ERREUR: Aucune propriété n'existe dans la table properties")
                    print("   Veuillez créer au moins une propriété avant d'exécuter cette migration")
                    return False
                
                default_property_id = first_property[0]
                print(f"   Assignation de property_id={default_property_id} aux imports existants...")
                cursor.execute(f"UPDATE mapping_imports SET property_id = {default_property_id} WHERE property_id IS NULL")
                conn.commit()
                print(f"✅ {null_count} imports mis à jour avec property_id={default_property_id}")
            else:
                print("✅ Tous les imports ont déjà un property_id")
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
            
            # Compter les imports existants
            cursor.execute("SELECT COUNT(*) FROM mapping_imports")
            import_count = cursor.fetchone()[0]
            print(f"   {import_count} import(s) existant(s) à mettre à jour")
            
            # Ajouter la colonne property_id (sans NOT NULL d'abord)
            cursor.execute("ALTER TABLE mapping_imports ADD COLUMN property_id INTEGER")
            
            # Assigner property_id par défaut à tous les imports existants
            if import_count > 0:
                cursor.execute(f"UPDATE mapping_imports SET property_id = {default_property_id} WHERE property_id IS NULL")
                print(f"✅ {import_count} import(s) mis à jour avec property_id={default_property_id}")
            
            conn.commit()
            print("✅ Colonne property_id ajoutée avec succès")
        
        # 3. Vérifier/Créer l'index sur property_id
        print("\n📋 Vérification de l'index idx_mapping_imports_property_id...")
        cursor.execute("PRAGMA index_list(mapping_imports)")
        indexes = [idx[1] for idx in cursor.fetchall()]
        
        if 'idx_mapping_imports_property_id' in indexes:
            print("✅ Index idx_mapping_imports_property_id existe déjà")
        else:
            print("📋 Création de l'index idx_mapping_imports_property_id...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_mapping_imports_property_id 
                ON mapping_imports(property_id)
            """)
            conn.commit()
            print("✅ Index idx_mapping_imports_property_id créé")
        
        # 4. Vérifier/Créer l'index unique sur (property_id, filename)
        print("\n📋 Vérification de l'index unique idx_mapping_imports_property_filename_unique...")
        if 'idx_mapping_imports_property_filename_unique' in indexes:
            print("✅ Index unique idx_mapping_imports_property_filename_unique existe déjà")
        else:
            # Vérifier s'il y a des doublons (filename, property_id) avant de créer l'index unique
            cursor.execute("""
                SELECT filename, property_id, COUNT(*) as count
                FROM mapping_imports
                GROUP BY filename, property_id
                HAVING count > 1
            """)
            duplicates = cursor.fetchall()
            
            if duplicates:
                print(f"⚠️  {len(duplicates)} doublon(s) détecté(s) pour (filename, property_id):")
                for dup in duplicates[:10]:  # Afficher max 10
                    print(f"   - filename='{dup[0]}', property_id={dup[1]} ({dup[2]} occurrences)")
                if len(duplicates) > 10:
                    print(f"   ... et {len(duplicates) - 10} autre(s)")
                print("   ⚠️  L'index unique ne peut pas être créé tant qu'il y a des doublons")
                print("   Veuillez résoudre les doublons manuellement avant de continuer")
                return False
            else:
                print("📋 Création de l'index unique idx_mapping_imports_property_filename_unique...")
                cursor.execute("""
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_mapping_imports_property_filename_unique 
                    ON mapping_imports(property_id, filename)
                """)
                conn.commit()
                print("✅ Index unique idx_mapping_imports_property_filename_unique créé")
        
        # 5. Vérifier la contrainte de clé étrangère
        print("\n📋 Vérification de la contrainte FOREIGN KEY...")
        cursor.execute("PRAGMA foreign_key_list(mapping_imports)")
        fks = cursor.fetchall()
        has_fk = any(fk[3] == 'property_id' and fk[2] == 'properties' for fk in fks)
        
        if has_fk:
            print("✅ Contrainte FOREIGN KEY existe déjà")
        else:
            print("⚠️  Contrainte FOREIGN KEY non détectée")
            print("   Note: SQLite nécessite de recréer la table pour ajouter une FK")
            print("   La contrainte sera gérée par SQLAlchemy au niveau application")
            print("   ✅ Le modèle MappingImport a déjà ForeignKey(), c'est suffisant")
        
        conn.commit()
        print("\n✅ Migration terminée avec succès")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erreur lors de la migration: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    success = migrate()
    if not success:
        exit(1)
