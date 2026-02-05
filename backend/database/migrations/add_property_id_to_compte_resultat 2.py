"""
Migration pour ajouter property_id aux tables du compte de résultat.

Tables modifiées :
- compte_resultat_mappings : ajout property_id avec FK vers properties
- compte_resultat_data : ajout property_id avec FK vers properties
- compte_resultat_config : ajout property_id avec FK vers properties
- compte_resultat_override : ajout property_id avec FK vers properties, modification contrainte unique

⚠️ Before making changes, read: ../../../docs/workflow/BEST_PRACTICES.md
"""

import sqlite3
import logging
from pathlib import Path

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Chemin vers la base de données
DB_PATH = Path(__file__).parent.parent / "lmnp.db"


def run_migration():
    """Exécuter la migration pour ajouter property_id aux tables du compte de résultat."""
    logger.info(f"[Migration] Début de la migration - Base de données: {DB_PATH}")
    
    if not DB_PATH.exists():
        logger.error(f"[Migration] ERREUR: Base de données non trouvée: {DB_PATH}")
        return False
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # Récupérer la première propriété comme valeur par défaut
        cursor.execute("SELECT id FROM properties ORDER BY id LIMIT 1")
        result = cursor.fetchone()
        
        if not result:
            logger.warning("[Migration] Aucune propriété trouvée - création d'une propriété par défaut")
            cursor.execute("""
                INSERT INTO properties (name, address, created_at, updated_at) 
                VALUES ('Default Property', '', datetime('now'), datetime('now'))
            """)
            conn.commit()
            cursor.execute("SELECT id FROM properties ORDER BY id LIMIT 1")
            result = cursor.fetchone()
        
        default_property_id = result[0]
        logger.info(f"[Migration] Propriété par défaut: id={default_property_id}")
        
        # ========== Migration compte_resultat_mappings ==========
        logger.info("[Migration] Traitement de compte_resultat_mappings...")
        
        # Vérifier si la colonne existe déjà
        cursor.execute("PRAGMA table_info(compte_resultat_mappings)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'property_id' not in columns:
            # Ajouter la colonne property_id
            cursor.execute("""
                ALTER TABLE compte_resultat_mappings 
                ADD COLUMN property_id INTEGER REFERENCES properties(id) ON DELETE CASCADE
            """)
            logger.info("[Migration] Colonne property_id ajoutée à compte_resultat_mappings")
            
            # Mettre à jour les enregistrements existants avec la propriété par défaut
            cursor.execute(f"""
                UPDATE compte_resultat_mappings 
                SET property_id = {default_property_id} 
                WHERE property_id IS NULL
            """)
            count = cursor.rowcount
            logger.info(f"[Migration] {count} enregistrements mis à jour dans compte_resultat_mappings")
            
            # Créer l'index
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_compte_resultat_mapping_property_id 
                ON compte_resultat_mappings(property_id)
            """)
            logger.info("[Migration] Index créé sur compte_resultat_mappings(property_id)")
        else:
            logger.info("[Migration] Colonne property_id déjà présente dans compte_resultat_mappings")
        
        # ========== Migration compte_resultat_data ==========
        logger.info("[Migration] Traitement de compte_resultat_data...")
        
        cursor.execute("PRAGMA table_info(compte_resultat_data)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'property_id' not in columns:
            cursor.execute("""
                ALTER TABLE compte_resultat_data 
                ADD COLUMN property_id INTEGER REFERENCES properties(id) ON DELETE CASCADE
            """)
            logger.info("[Migration] Colonne property_id ajoutée à compte_resultat_data")
            
            cursor.execute(f"""
                UPDATE compte_resultat_data 
                SET property_id = {default_property_id} 
                WHERE property_id IS NULL
            """)
            count = cursor.rowcount
            logger.info(f"[Migration] {count} enregistrements mis à jour dans compte_resultat_data")
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_compte_resultat_data_property_id 
                ON compte_resultat_data(property_id)
            """)
            logger.info("[Migration] Index créé sur compte_resultat_data(property_id)")
        else:
            logger.info("[Migration] Colonne property_id déjà présente dans compte_resultat_data")
        
        # ========== Migration compte_resultat_config ==========
        logger.info("[Migration] Traitement de compte_resultat_config...")
        
        cursor.execute("PRAGMA table_info(compte_resultat_config)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'property_id' not in columns:
            cursor.execute("""
                ALTER TABLE compte_resultat_config 
                ADD COLUMN property_id INTEGER REFERENCES properties(id) ON DELETE CASCADE
            """)
            logger.info("[Migration] Colonne property_id ajoutée à compte_resultat_config")
            
            cursor.execute(f"""
                UPDATE compte_resultat_config 
                SET property_id = {default_property_id} 
                WHERE property_id IS NULL
            """)
            count = cursor.rowcount
            logger.info(f"[Migration] {count} enregistrements mis à jour dans compte_resultat_config")
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_compte_resultat_config_property_id 
                ON compte_resultat_config(property_id)
            """)
            logger.info("[Migration] Index créé sur compte_resultat_config(property_id)")
        else:
            logger.info("[Migration] Colonne property_id déjà présente dans compte_resultat_config")
        
        # ========== Migration compte_resultat_override ==========
        logger.info("[Migration] Traitement de compte_resultat_override...")
        
        cursor.execute("PRAGMA table_info(compte_resultat_override)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'property_id' not in columns:
            # Note: SQLite ne supporte pas la modification de contraintes directement
            # On ajoute juste la colonne et l'index composite
            cursor.execute("""
                ALTER TABLE compte_resultat_override 
                ADD COLUMN property_id INTEGER REFERENCES properties(id) ON DELETE CASCADE
            """)
            logger.info("[Migration] Colonne property_id ajoutée à compte_resultat_override")
            
            cursor.execute(f"""
                UPDATE compte_resultat_override 
                SET property_id = {default_property_id} 
                WHERE property_id IS NULL
            """)
            count = cursor.rowcount
            logger.info(f"[Migration] {count} enregistrements mis à jour dans compte_resultat_override")
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_compte_resultat_override_property_id 
                ON compte_resultat_override(property_id)
            """)
            logger.info("[Migration] Index créé sur compte_resultat_override(property_id)")
            
            # Créer l'index unique composite (year, property_id)
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_compte_resultat_override_year_property 
                ON compte_resultat_override(year, property_id)
            """)
            logger.info("[Migration] Index unique créé sur compte_resultat_override(year, property_id)")
        else:
            logger.info("[Migration] Colonne property_id déjà présente dans compte_resultat_override")
        
        # Commit des changements
        conn.commit()
        logger.info("[Migration] Migration terminée avec succès!")
        
        # Validation
        logger.info("[Migration] Validation des modifications...")
        for table in ['compte_resultat_mappings', 'compte_resultat_data', 'compte_resultat_config', 'compte_resultat_override']:
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE property_id IS NULL")
            null_count = cursor.fetchone()[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            total_count = cursor.fetchone()[0]
            
            if null_count > 0:
                logger.warning(f"[Migration] ATTENTION: {null_count}/{total_count} enregistrements sans property_id dans {table}")
            else:
                logger.info(f"[Migration] ✅ {table}: {total_count} enregistrements, tous avec property_id")
        
        return True
        
    except Exception as e:
        logger.error(f"[Migration] ERREUR: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


if __name__ == "__main__":
    success = run_migration()
    exit(0 if success else 1)
