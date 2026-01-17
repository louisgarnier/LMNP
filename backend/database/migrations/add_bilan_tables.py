"""
Migration: Add bilan tables (bilan_mappings, bilan_data, bilan_config).

This script creates the tables needed for the Bilan feature:
- bilan_mappings: Mappings between level_1 values and accounting categories
- bilan_data: Calculated balance sheet data by year and category
- bilan_config: Global configuration (Level 3 filter)

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sqlite3
from pathlib import Path

# Database path
DB_DIR = Path(__file__).parent.parent
DB_FILE = DB_DIR / "lmnp.db"


def migrate():
    """Create bilan tables."""
    if not DB_FILE.exists():
        print(f"Database file not found: {DB_FILE}")
        return
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    try:
        # Create bilan_mappings table
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='bilan_mappings'
        """)
        
        if cursor.fetchone():
            print("ℹ️  Table bilan_mappings already exists")
        else:
            print("Creating bilan_mappings table...")
            
            cursor.execute("""
                CREATE TABLE bilan_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_name VARCHAR(255) NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    sub_category VARCHAR(100) NOT NULL,
                    level_1_values TEXT,
                    is_special BOOLEAN NOT NULL DEFAULT 0,
                    special_source VARCHAR(100),
                    compte_resultat_view_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for bilan_mappings
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bilan_mapping_category 
                ON bilan_mappings(category_name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bilan_mapping_type 
                ON bilan_mappings(type)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bilan_mapping_sub_category 
                ON bilan_mappings(sub_category)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bilan_mapping_type_sub_category 
                ON bilan_mappings(type, sub_category)
            """)
            
            print("✅ Table bilan_mappings created successfully")
        
        # Create bilan_data table
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='bilan_data'
        """)
        
        if cursor.fetchone():
            print("ℹ️  Table bilan_data already exists")
        else:
            print("Creating bilan_data table...")
            
            cursor.execute("""
                CREATE TABLE bilan_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    annee INTEGER NOT NULL,
                    category_name VARCHAR(255) NOT NULL,
                    amount REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for bilan_data
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bilan_data_year_category 
                ON bilan_data(annee, category_name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bilan_data_year 
                ON bilan_data(annee)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bilan_data_category 
                ON bilan_data(category_name)
            """)
            
            print("✅ Table bilan_data created successfully")
        
        # Create bilan_config table
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='bilan_config'
        """)
        
        if cursor.fetchone():
            print("ℹ️  Table bilan_config already exists")
        else:
            print("Creating bilan_config table...")
            
            cursor.execute("""
                CREATE TABLE bilan_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level_3_values TEXT NOT NULL DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert default config if none exists
            cursor.execute("SELECT COUNT(*) FROM bilan_config")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO bilan_config (level_3_values) 
                    VALUES ('[]')
                """)
                print("✅ Default bilan_config entry created")
            
            print("✅ Table bilan_config created successfully")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error during migration: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
