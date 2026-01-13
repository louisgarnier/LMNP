"""
Script pour nettoyer les mensualités avec toutes les valeurs à 0.

Usage: python3 backend/scripts/cleanup_empty_loan_payments.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database import init_database, SessionLocal
from backend.database.models import LoanPayment

def cleanup_empty_payments():
    """Supprime les mensualités avec toutes les valeurs à 0."""
    print("=" * 60)
    print("  NETTOYAGE DES MENSUALITÉS VIDES")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Trouver toutes les mensualités avec toutes les valeurs à 0
        empty_payments = db.query(LoanPayment).filter(
            LoanPayment.capital == 0.0,
            LoanPayment.interest == 0.0,
            LoanPayment.insurance == 0.0,
            LoanPayment.total == 0.0
        ).all()
        
        if not empty_payments:
            print("✅ Aucune mensualité vide trouvée")
            return
        
        print(f"\n📋 {len(empty_payments)} mensualité(s) vide(s) trouvée(s):\n")
        
        # Afficher les détails
        for payment in empty_payments:
            print(f"   ID {payment.id}: {payment.date.strftime('%d/%m/%Y')} - {payment.loan_name}")
        
        # Supprimer automatiquement
        print(f"\n🗑️  Suppression de {len(empty_payments)} mensualité(s) vide(s)...")
        
        # Supprimer
        deleted_count = db.query(LoanPayment).filter(
            LoanPayment.capital == 0.0,
            LoanPayment.interest == 0.0,
            LoanPayment.insurance == 0.0,
            LoanPayment.total == 0.0
        ).delete()
        
        db.commit()
        
        print(f"\n✅ {deleted_count} mensualité(s) supprimée(s)")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Erreur: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
    cleanup_empty_payments()
    print("\n" + "=" * 60)
    print("  ✅ NETTOYAGE TERMINÉ")
    print("=" * 60)
