"""
Script de nettoyage des données de test de la base de données.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce script supprime toutes les transactions de test créées lors des tests précédents.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.database.models import Transaction, EnrichedTransaction, FileImport

def cleanup_test_data():
    """
    Supprime toutes les transactions de test de la base de données.
    """
    # Initialize database to ensure tables exist
    init_database()
    
    db = SessionLocal()
    try:
        # Compter les transactions avant nettoyage
        count_before = db.query(Transaction).count()
        print(f"📊 Nombre de transactions avant nettoyage: {count_before}")
        
        # Supprimer toutes les transactions enrichies associées
        enriched_count = db.query(EnrichedTransaction).count()
        if enriched_count > 0:
            db.query(EnrichedTransaction).delete()
            print(f"🗑️  Supprimé {enriched_count} transactions enrichies")
        
        # Supprimer toutes les transactions
        transactions_deleted = db.query(Transaction).delete()
        print(f"🗑️  Supprimé {transactions_deleted} transactions")
        
        # Supprimer tous les imports de fichiers (pour repartir à zéro)
        imports_deleted = db.query(FileImport).delete()
        if imports_deleted > 0:
            print(f"🗑️  Supprimé {imports_deleted} enregistrements d'imports")
        
        # Commit les changements
        db.commit()
        
        # Vérifier après nettoyage
        count_after = db.query(Transaction).count()
        print(f"✅ Nombre de transactions après nettoyage: {count_after}")
        
        if count_after == 0:
            print("✅ Base de données nettoyée avec succès - 0 transactions restantes")
        else:
            print(f"⚠️  Attention: {count_after} transactions restantes")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors du nettoyage: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🧹 Nettoyage des données de test...")
    cleanup_test_data()
    print("✅ Nettoyage terminé")

