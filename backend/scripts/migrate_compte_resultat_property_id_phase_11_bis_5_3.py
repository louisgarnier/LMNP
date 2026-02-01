"""
Migration des données du Compte de Résultat - Phase 11 bis 5.3

Ce script assigne les données existantes à une propriété par défaut.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
import os

# Ajouter le chemin parent pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Chemin vers la base de données
DB_PATH = Path(__file__).parent.parent / "database" / "lmnp.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

def log_info(message):
    print(f"[INFO] {message}")

def log_success(message):
    print(f"✅ {message}")

def log_error(message):
    print(f"❌ {message}")

def log_warning(message):
    print(f"⚠️ {message}")

def main():
    print("\n" + "="*60)
    print("MIGRATION DONNÉES COMPTE DE RÉSULTAT - PHASE 11 bis 5.3")
    print("="*60 + "\n")
    
    log_info(f"Base de données: {DB_PATH}")
    
    if not DB_PATH.exists():
        log_error(f"Base de données non trouvée: {DB_PATH}")
        return 1
    
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Récupérer la première propriété
        result = session.execute(text("SELECT id, name FROM properties ORDER BY id LIMIT 1"))
        prop = result.fetchone()
        
        if not prop:
            log_error("Aucune propriété trouvée")
            return 1
        
        default_property_id = prop[0]
        log_info(f"Propriété par défaut: {default_property_id} - {prop[1]}")
        
        tables = [
            'compte_resultat_mappings',
            'compte_resultat_data', 
            'compte_resultat_config',
            'compte_resultat_override'
        ]
        
        for table in tables:
            log_info(f"=== Migration de {table} ===")
            
            # Compter les enregistrements sans property_id
            result = session.execute(text(f"SELECT COUNT(*) FROM {table} WHERE property_id IS NULL"))
            null_count = result.fetchone()[0]
            
            if null_count > 0:
                # Assigner la propriété par défaut
                session.execute(
                    text(f"UPDATE {table} SET property_id = :prop_id WHERE property_id IS NULL"),
                    {"prop_id": default_property_id}
                )
                session.commit()
                log_success(f"{null_count} enregistrement(s) mis à jour avec property_id={default_property_id}")
            else:
                log_info(f"Aucun enregistrement sans property_id dans {table}")
            
            # Vérification
            result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            total = result.fetchone()[0]
            result = session.execute(text(f"SELECT COUNT(*) FROM {table} WHERE property_id IS NOT NULL"))
            with_prop = result.fetchone()[0]
            
            if total == with_prop:
                log_success(f"{table}: {total} enregistrement(s), tous avec property_id")
            else:
                log_warning(f"{table}: {with_prop}/{total} avec property_id")
        
        print("\n" + "="*60)
        log_success("MIGRATION TERMINÉE AVEC SUCCÈS")
        return 0
        
    except Exception as e:
        log_error(f"Erreur lors de la migration: {e}")
        session.rollback()
        return 1
        
    finally:
        session.close()

if __name__ == "__main__":
    sys.exit(main())
