"""
Migration: Add property_id to allowed_mappings table.

This script adds the property_id column to the allowed_mappings table,
assigns a default property_id to existing allowed_mappings,
and creates the necessary indexes and foreign key constraints.

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sqlite3
from pathlib import Path

# Database path
DB_DIR = Path(__file__).parent.parent
DB_FILE = DB_DIR / "lmnp.db"


def migrate():
    """Add property_id to allowed_mappings table."""
    if not DB_FILE.exists():
        print(f"Database file not found: {DB_FILE}")
        return False
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    try:
        print("=== Ajout de property_id à la table allowed_mappings ===\n")
        
        # 1. Vérifier si la table allowed_mappings existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='allowed_mappings'")
        if not cursor.fetchone():
            print("❌ ERREUR: La table allowed_mappings n'existe pas")
            return False
        
        # 2. Vérifier si property_id existe déjà
        cursor.execute("PRAGMA table_info(allowed_mappings)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'property_id' in columns:
            print("✅ La colonne property_id existe déjà dans la table allowed_mappings")
            
            # Vérifier s'il y a des allowed_mappings sans property_id
            cursor.execute("SELECT COUNT(*) FROM allowed_mappings WHERE property_id IS NULL")
            null_count = cursor.fetchone()[0]
            
            if null_count > 0:
                print(f"⚠️  {null_count} allowed_mappings ont property_id=NULL, assignation nécessaire...")
                # Vérifier qu'il existe au moins une propriété
                cursor.execute("SELECT id FROM properties ORDER BY id LIMIT 1")
                first_property = cursor.fetchone()
                if first_property:
                    default_property_id = first_property[0]
                    print(f"✅ Assignation de property_id={default_property_id} aux allowed_mappings existants...")
                    cursor.execute("UPDATE allowed_mappings SET property_id = ? WHERE property_id IS NULL", (default_property_id,))
                    conn.commit()
                    print(f"✅ {null_count} allowed_mappings mis à jour avec property_id={default_property_id}")
                else:
                    print("❌ ERREUR: Aucune propriété trouvée dans la base de données")
                    return False
            else:
                print("✅ Tous les allowed_mappings ont déjà un property_id")
            
            # Vérifier les contraintes
            cursor.execute("PRAGMA foreign_key_list(allowed_mappings)")
            fk_list = cursor.fetchall()
            has_fk = any(fk[3] == 'properties' for fk in fk_list)
            
            if not has_fk:
                print("⚠️  La contrainte de clé étrangère n'existe pas, création...")
                # SQLite ne supporte pas ALTER TABLE ADD CONSTRAINT, on doit recréer la table
                # Mais d'abord, vérifier s'il y a des doublons avec le nouvel index unique
                cursor.execute("""
                    SELECT property_id, level_1, level_2, level_3, COUNT(*) as cnt
                    FROM allowed_mappings
                    GROUP BY property_id, level_1, level_2, level_3
                    HAVING cnt > 1
                """)
                duplicates = cursor.fetchall()
                if duplicates:
                    print(f"⚠️  {len(duplicates)} doublons détectés. Suppression des doublons...")
                    # Garder le premier de chaque groupe
                    for dup in duplicates:
                        cursor.execute("""
                            DELETE FROM allowed_mappings
                            WHERE property_id = ? AND level_1 = ? AND level_2 = ? AND level_3 = ?
                            AND id NOT IN (
                                SELECT id FROM allowed_mappings
                                WHERE property_id = ? AND level_1 = ? AND level_2 = ? AND level_3 = ?
                                ORDER BY id LIMIT 1
                            )
                        """, (dup[0], dup[1], dup[2], dup[3], dup[0], dup[1], dup[2], dup[3]))
                    conn.commit()
                    print("✅ Doublons supprimés")
            
            return True
        
        # 3. Ajouter la colonne property_id (nullable d'abord)
        print("📝 Ajout de la colonne property_id (nullable)...")
        cursor.execute("ALTER TABLE allowed_mappings ADD COLUMN property_id INTEGER")
        conn.commit()
        print("✅ Colonne property_id ajoutée")
        
        # 4. Vérifier qu'il existe au moins une propriété
        cursor.execute("SELECT id FROM properties ORDER BY id LIMIT 1")
        first_property = cursor.fetchone()
        if not first_property:
            print("❌ ERREUR: Aucune propriété trouvée dans la base de données")
            print("   Veuillez créer au moins une propriété avant d'exécuter cette migration")
            return False
        
        default_property_id = first_property[0]
        print(f"✅ Propriété par défaut trouvée: id={default_property_id}")
        
        # 5. Assigner property_id=1 à tous les allowed_mappings existants
        print(f"📝 Assignation de property_id={default_property_id} aux allowed_mappings existants...")
        cursor.execute("UPDATE allowed_mappings SET property_id = ? WHERE property_id IS NULL", (default_property_id,))
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM allowed_mappings")
        count = cursor.fetchone()[0]
        print(f"✅ {count} allowed_mappings mis à jour avec property_id={default_property_id}")
        
        # 6. Vérifier s'il y a des doublons avec le nouvel index unique (property_id, level_1, level_2, level_3)
        print("📝 Vérification des doublons...")
        cursor.execute("""
            SELECT property_id, level_1, level_2, level_3, COUNT(*) as cnt
            FROM allowed_mappings
            GROUP BY property_id, level_1, level_2, level_3
            HAVING cnt > 1
        """)
        duplicates = cursor.fetchall()
        if duplicates:
            print(f"⚠️  {len(duplicates)} doublons détectés. Suppression des doublons...")
            # Garder le premier de chaque groupe
            for dup in duplicates:
                cursor.execute("""
                    DELETE FROM allowed_mappings
                    WHERE property_id = ? AND level_1 = ? AND level_2 = ? AND level_3 = ?
                    AND id NOT IN (
                        SELECT id FROM allowed_mappings
                        WHERE property_id = ? AND level_1 = ? AND level_2 = ? AND level_3 = ?
                        ORDER BY id LIMIT 1
                    )
                """, (dup[0], dup[1], dup[2], dup[3], dup[0], dup[1], dup[2], dup[3]))
            conn.commit()
            print("✅ Doublons supprimés")
        else:
            print("✅ Aucun doublon détecté")
        
        # 7. Rendre property_id NOT NULL
        print("📝 Modification de property_id en NOT NULL...")
        # SQLite ne supporte pas ALTER COLUMN, on doit recréer la table
        # Mais d'abord, sauvegarder les données
        cursor.execute("SELECT * FROM allowed_mappings")
        data = cursor.fetchall()
        columns_info = cursor.execute("PRAGMA table_info(allowed_mappings)").fetchall()
        column_names = [col[1] for col in columns_info]
        
        # Créer la nouvelle table avec property_id NOT NULL
        cursor.execute("""
            CREATE TABLE allowed_mappings_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER NOT NULL,
                level_1 VARCHAR(100) NOT NULL,
                level_2 VARCHAR(100) NOT NULL,
                level_3 VARCHAR(100),
                is_hardcoded BOOLEAN DEFAULT 0 NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
            )
        """)
        
        # Insérer les données
        placeholders = ','.join(['?' for _ in column_names])
        cursor.executemany(f"INSERT INTO allowed_mappings_new ({','.join(column_names)}) VALUES ({placeholders})", data)
        
        # Supprimer l'ancienne table et renommer la nouvelle
        cursor.execute("DROP TABLE allowed_mappings")
        cursor.execute("ALTER TABLE allowed_mappings_new RENAME TO allowed_mappings")
        
        conn.commit()
        print("✅ property_id est maintenant NOT NULL")
        
        # 8. Créer les index
        print("📝 Création des index...")
        
        # Index unique sur (property_id, level_1, level_2, level_3)
        try:
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_allowed_mapping_unique 
                ON allowed_mappings(property_id, level_1, level_2, level_3)
            """)
            print("✅ Index unique créé: idx_allowed_mapping_unique")
        except sqlite3.OperationalError as e:
            if "already exists" not in str(e).lower():
                print(f"⚠️  Erreur lors de la création de l'index unique: {e}")
        
        # Index sur property_id
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_allowed_mapping_property_id ON allowed_mappings(property_id)")
            print("✅ Index créé: idx_allowed_mapping_property_id")
        except sqlite3.OperationalError as e:
            if "already exists" not in str(e).lower():
                print(f"⚠️  Erreur lors de la création de l'index property_id: {e}")
        
        # Index sur level_1, level_2, level_3 (si pas déjà existants)
        for level in ['level_1', 'level_2', 'level_3']:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_allowed_mapping_{level} ON allowed_mappings({level})")
                print(f"✅ Index créé: idx_allowed_mapping_{level}")
            except sqlite3.OperationalError as e:
                if "already exists" not in str(e).lower():
                    print(f"⚠️  Erreur lors de la création de l'index {level}: {e}")
        
        conn.commit()
        
        print("\n✅ Migration terminée avec succès!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR lors de la migration: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    success = migrate()
    exit(0 if success else 1)
