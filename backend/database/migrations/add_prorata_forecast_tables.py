"""
Migration script to add Pro Rata & Forecast tables.

Tables created:
- prorata_settings: Global settings per property
- annual_forecast_configs: Forecast configurations per property/year/category

Usage:
    python backend/database/migrations/add_prorata_forecast_tables.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from backend.database.connection import engine, get_db
from backend.database.models import Base, ProRataSettings, AnnualForecastConfig
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_table_exists(eng, table_name: str) -> bool:
    """Check if a table exists in the database."""
    with eng.connect() as conn:
        result = conn.execute(text(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
        ))
        return result.fetchone() is not None


def run_migration():
    """Run the migration to create Pro Rata & Forecast tables."""
    logger.info("="*60)
    logger.info("🚀 Starting Pro Rata & Forecast tables migration")
    logger.info("="*60)
    
    # Check if tables already exist
    prorata_exists = check_table_exists(engine, "prorata_settings")
    forecast_exists = check_table_exists(engine, "annual_forecast_configs")
    
    if prorata_exists:
        logger.info("✅ Table 'prorata_settings' already exists")
    else:
        logger.info("📦 Creating table 'prorata_settings'...")
    
    if forecast_exists:
        logger.info("✅ Table 'annual_forecast_configs' already exists")
    else:
        logger.info("📦 Creating table 'annual_forecast_configs'...")
    
    # Create tables using SQLAlchemy models
    # This will only create tables that don't exist
    Base.metadata.create_all(engine)
    
    # Verify tables were created
    prorata_exists_after = check_table_exists(engine, "prorata_settings")
    forecast_exists_after = check_table_exists(engine, "annual_forecast_configs")
    
    if prorata_exists_after and forecast_exists_after:
        logger.info("="*60)
        logger.info("✅ Migration completed successfully!")
        logger.info("="*60)
        
        # Show table structure
        with engine.connect() as conn:
            logger.info("\n📋 Table 'prorata_settings' structure:")
            result = conn.execute(text("PRAGMA table_info(prorata_settings)"))
            for row in result:
                logger.info(f"   - {row[1]} ({row[2]})")
            
            logger.info("\n📋 Table 'annual_forecast_configs' structure:")
            result = conn.execute(text("PRAGMA table_info(annual_forecast_configs)"))
            for row in result:
                logger.info(f"   - {row[1]} ({row[2]})")
        
        return True
    else:
        logger.error("❌ Migration failed - tables not created")
        return False


def verify_migration():
    """Verify the migration by checking table structures and constraints."""
    logger.info("\n" + "="*60)
    logger.info("🔍 Verifying migration...")
    logger.info("="*60)
    
    with engine.connect() as conn:
        # Check indexes on prorata_settings
        logger.info("\n📊 Indexes on 'prorata_settings':")
        result = conn.execute(text("PRAGMA index_list(prorata_settings)"))
        for row in result:
            logger.info(f"   - {row[1]} (unique={row[2]})")
        
        # Check indexes on annual_forecast_configs
        logger.info("\n📊 Indexes on 'annual_forecast_configs':")
        result = conn.execute(text("PRAGMA index_list(annual_forecast_configs)"))
        for row in result:
            logger.info(f"   - {row[1]} (unique={row[2]})")
        
        # Count records
        result = conn.execute(text("SELECT COUNT(*) FROM prorata_settings"))
        count = result.fetchone()[0]
        logger.info(f"\n📈 Records in 'prorata_settings': {count}")
        
        result = conn.execute(text("SELECT COUNT(*) FROM annual_forecast_configs"))
        count = result.fetchone()[0]
        logger.info(f"📈 Records in 'annual_forecast_configs': {count}")
    
    logger.info("\n✅ Verification completed")


if __name__ == "__main__":
    success = run_migration()
    if success:
        verify_migration()
    sys.exit(0 if success else 1)
