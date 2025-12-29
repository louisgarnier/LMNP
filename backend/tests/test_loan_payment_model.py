"""
Test unitaire pour le modèle LoanPayment.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python -m pytest backend/tests/test_loan_payment_model.py -v
Or: python backend/tests/test_loan_payment_model.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database import SessionLocal
from backend.database.models import LoanPayment
from datetime import date, datetime


def test_loan_payment_model():
    """Test que le modèle LoanPayment peut être créé et récupéré."""
    db = SessionLocal()
    try:
        # Test 1: Créer une mensualité
        payment = LoanPayment(
            date=date(2024, 1, 15),
            capital=500.0,
            interest=200.0,
            insurance=50.0,
            total=750.0,
            loan_name="Prêt principal"
        )
        
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        print(f"✅ Test 1: Mensualité créée avec ID {payment.id}")
        assert payment.id is not None
        assert payment.date == date(2024, 1, 15)
        assert payment.capital == 500.0
        assert payment.interest == 200.0
        assert payment.insurance == 50.0
        assert payment.total == 750.0
        assert payment.loan_name == "Prêt principal"
        assert payment.capital + payment.interest + payment.insurance == payment.total
        
        # Test 2: Récupérer la mensualité
        retrieved_payment = db.query(LoanPayment).filter(LoanPayment.id == payment.id).first()
        assert retrieved_payment is not None
        assert retrieved_payment.date == date(2024, 1, 15)
        assert retrieved_payment.total == 750.0
        print(f"✅ Test 2: Mensualité récupérée avec succès")
        
        # Test 3: Filtrer par loan_name
        payments_for_loan = db.query(LoanPayment).filter(
            LoanPayment.loan_name == "Prêt principal"
        ).all()
        assert len(payments_for_loan) >= 1
        print(f"✅ Test 3: Filtrage par loan_name fonctionne ({len(payments_for_loan)} mensualité(s) trouvée(s))")
        
        # Test 4: Filtrer par date
        payments_for_date = db.query(LoanPayment).filter(
            LoanPayment.date == date(2024, 1, 15)
        ).all()
        assert len(payments_for_date) >= 1
        print(f"✅ Test 4: Filtrage par date fonctionne ({len(payments_for_date)} mensualité(s) trouvée(s))")
        
        # Test 5: Mettre à jour une mensualité
        payment.capital = 600.0
        payment.total = 850.0
        db.commit()
        db.refresh(payment)
        assert payment.capital == 600.0
        assert payment.total == 850.0
        print(f"✅ Test 5: Mise à jour de la mensualité fonctionne")
        
        # Test 6: Supprimer une mensualité
        payment_id = payment.id
        db.delete(payment)
        db.commit()
        deleted_payment = db.query(LoanPayment).filter(LoanPayment.id == payment_id).first()
        assert deleted_payment is None
        print(f"✅ Test 6: Suppression de la mensualité fonctionne")
        
        print("\n✅ Tous les tests du modèle LoanPayment sont passés !")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors des tests: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    test_loan_payment_model()

