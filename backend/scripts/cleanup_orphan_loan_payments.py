"""
Script de nettoyage pour supprimer les mensualités orphelines.

Les mensualités orphelines sont des mensualités dont le loan_name n'existe pas
dans la table loan_configs (crédit supprimé ou jamais créé).

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database import init_database, SessionLocal
from backend.database.models import LoanConfig, LoanPayment
from sqlalchemy import func

def cleanup_orphan_payments():
    """Supprime toutes les mensualités orphelines (sans configuration associée)."""
    db = SessionLocal()
    try:
        # Récupérer tous les noms de crédits uniques dans loan_payments
        payment_loans = db.query(LoanPayment.loan_name).distinct().all()
        payment_loan_names = [row[0] for row in payment_loans]
        
        # Récupérer tous les noms de crédits dans loan_configs
        config_loans = db.query(LoanConfig.name).all()
        config_loan_names = [row[0] for row in config_loans]
        
        # Trouver les orphelins
        orphan_loans = set(payment_loan_names) - set(config_loan_names)
        
        if not orphan_loans:
            print("✅ Aucune mensualité orpheline trouvée. La base de données est propre.")
            return
        
        print(f"⚠️  {len(orphan_loans)} crédit(s) orphelin(s) détecté(s):")
        total_orphan_payments = 0
        
        for loan_name in orphan_loans:
            count = db.query(LoanPayment).filter(LoanPayment.loan_name == loan_name).count()
            total_orphan_payments += count
            print(f"   - '{loan_name}': {count} mensualité(s)")
        
        print(f"\n📊 Total: {total_orphan_payments} mensualité(s) orpheline(s) à supprimer")
        
        # Demander confirmation
        confirm = input(f"\n❓ Voulez-vous supprimer ces {total_orphan_payments} mensualité(s) orpheline(s) ? (oui/non): ")
        
        if confirm.lower() not in ['oui', 'o', 'yes', 'y']:
            print("❌ Suppression annulée.")
            return
        
        # Supprimer toutes les mensualités orphelines
        deleted_count = 0
        for loan_name in orphan_loans:
            payments = db.query(LoanPayment).filter(LoanPayment.loan_name == loan_name).all()
            for payment in payments:
                db.delete(payment)
                deleted_count += 1
        
        db.commit()
        print(f"\n✅ {deleted_count} mensualité(s) orpheline(s) supprimée(s) avec succès.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors du nettoyage: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("  NETTOYAGE DES MENSUALITÉS ORPHELINES")
    print("=" * 60)
    print()
    
    init_database()
    cleanup_orphan_payments()
    
    print("\n" + "=" * 60)
    print("  ✅ NETTOYAGE TERMINÉ")
    print("=" * 60)
