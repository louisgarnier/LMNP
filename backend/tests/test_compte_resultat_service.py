"""
Tests unitaires pour le service compte de résultat.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Run with: python -m pytest backend/tests/test_compte_resultat_service.py -v
Or: python backend/tests/test_compte_resultat_service.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from datetime import date
from backend.database import SessionLocal
from backend.database.models import (
    CompteResultatMapping,
    Transaction,
    EnrichedTransaction,
    AmortizationResult,
    LoanPayment
)
from backend.api.services.compte_resultat_service import (
    get_mappings,
    calculate_produits_exploitation,
    calculate_charges_exploitation,
    get_amortissements,
    get_cout_financement,
    calculate_compte_resultat
)


def cleanup_db():
    """Nettoie la base de données avant les tests."""
    db = SessionLocal()
    try:
        db.query(AmortizationResult).delete()
        db.query(LoanPayment).delete()
        db.query(EnrichedTransaction).delete()
        db.query(Transaction).delete()
        db.query(CompteResultatMapping).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"⚠️ Erreur lors du nettoyage: {e}")
    finally:
        db.close()


def test_get_mappings():
    """Test de récupération des mappings."""
    cleanup_db()
    db = SessionLocal()
    try:
        # Créer des mappings de test
        mapping1 = CompteResultatMapping(
            category_name="Loyers hors charge encaissés",
            level_1_values=["PRODUITS"],
            level_2_values=["LOYERS"]
        )
        mapping2 = CompteResultatMapping(
            category_name="Charges de copropriété hors fonds travaux",
            level_1_values=None,
            level_2_values=["CHARGES_COPROPRIETE"]
        )
        
        db.add(mapping1)
        db.add(mapping2)
        db.commit()
        
        # Récupérer les mappings
        mappings = get_mappings(db)
        
        assert len(mappings) >= 2
        assert any(m.category_name == "Loyers hors charge encaissés" for m in mappings)
        assert any(m.category_name == "Charges de copropriété hors fonds travaux" for m in mappings)
        
        print("✅ Test get_mappings : PASSÉ")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
        raise
    finally:
        db.close()


def test_calculate_produits_exploitation():
    """Test de calcul des produits d'exploitation."""
    cleanup_db()
    db = SessionLocal()
    try:
        # Créer un mapping
        mapping = CompteResultatMapping(
            category_name="Loyers hors charge encaissés",
            level_1_values=["PRODUITS"],
            level_2_values=["LOYERS"]
        )
        db.add(mapping)
        db.commit()
        
        # Créer des transactions enrichies pour 2024
        transaction1 = Transaction(
            date=date(2024, 3, 15),
            quantite=1000.0,
            nom="Loyer mars",
            solde=1000.0
        )
        transaction2 = Transaction(
            date=date(2024, 4, 15),
            quantite=1000.0,
            nom="Loyer avril",
            solde=2000.0
        )
        db.add(transaction1)
        db.add(transaction2)
        db.commit()
        
        enriched1 = EnrichedTransaction(
            transaction_id=transaction1.id,
            mois=3,
            annee=2024,
            level_1="PRODUITS",
            level_2="LOYERS"
        )
        enriched2 = EnrichedTransaction(
            transaction_id=transaction2.id,
            mois=4,
            annee=2024,
            level_1="PRODUITS",
            level_2="LOYERS"
        )
        db.add(enriched1)
        db.add(enriched2)
        db.commit()
        
        # Calculer les produits
        mappings = get_mappings(db)
        produits = calculate_produits_exploitation(2024, mappings, db)
        
        assert "Loyers hors charge encaissés" in produits
        assert produits["Loyers hors charge encaissés"] == 2000.0
        
        print("✅ Test calculate_produits_exploitation : PASSÉ")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
        raise
    finally:
        db.close()


def test_calculate_charges_exploitation():
    """Test de calcul des charges d'exploitation."""
    cleanup_db()
    db = SessionLocal()
    try:
        # Créer un mapping
        mapping = CompteResultatMapping(
            category_name="Charges de copropriété hors fonds travaux",
            level_1_values=None,
            level_2_values=["CHARGES_COPROPRIETE"]
        )
        db.add(mapping)
        db.commit()
        
        # Créer des transactions enrichies pour 2024 (montants négatifs = charges)
        transaction1 = Transaction(
            date=date(2024, 2, 1),
            quantite=-500.0,
            nom="Charges copropriété février",
            solde=-500.0
        )
        transaction2 = Transaction(
            date=date(2024, 3, 1),
            quantite=-500.0,
            nom="Charges copropriété mars",
            solde=-1000.0
        )
        db.add(transaction1)
        db.add(transaction2)
        db.commit()
        
        enriched1 = EnrichedTransaction(
            transaction_id=transaction1.id,
            mois=2,
            annee=2024,
            level_1="CHARGES",
            level_2="CHARGES_COPROPRIETE"
        )
        enriched2 = EnrichedTransaction(
            transaction_id=transaction2.id,
            mois=3,
            annee=2024,
            level_1="CHARGES",
            level_2="CHARGES_COPROPRIETE"
        )
        db.add(enriched1)
        db.add(enriched2)
        db.commit()
        
        # Calculer les charges
        mappings = get_mappings(db)
        charges = calculate_charges_exploitation(2024, mappings, db)
        
        assert "Charges de copropriété hors fonds travaux" in charges
        assert charges["Charges de copropriété hors fonds travaux"] == 1000.0
        
        print("✅ Test calculate_charges_exploitation : PASSÉ")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
        raise
    finally:
        db.close()


def test_get_amortissements():
    """Test de récupération des amortissements."""
    cleanup_db()
    db = SessionLocal()
    try:
        # Créer des résultats d'amortissement pour 2024
        # Note: Les montants sont négatifs dans AmortizationResult
        amort1 = AmortizationResult(
            transaction_id=1,
            year=2024,
            category="mobilier",
            amount=-2000.0
        )
        amort2 = AmortizationResult(
            transaction_id=2,
            year=2024,
            category="travaux",
            amount=-3000.0
        )
        db.add(amort1)
        db.add(amort2)
        db.commit()
        
        # Récupérer les amortissements
        total = get_amortissements(2024, None, db)
        
        assert total == 5000.0  # Valeur absolue des montants négatifs
        
        print("✅ Test get_amortissements : PASSÉ")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
        raise
    finally:
        db.close()


def test_get_cout_financement():
    """Test de calcul du coût du financement."""
    cleanup_db()
    db = SessionLocal()
    try:
        # Créer des loan_payments pour 2024
        payment1 = LoanPayment(
            date=date(2024, 1, 1),
            capital=500.0,
            interest=200.0,
            insurance=50.0,
            total=750.0,
            loan_name="Prêt principal"
        )
        payment2 = LoanPayment(
            date=date(2024, 1, 1),
            capital=300.0,
            interest=150.0,
            insurance=30.0,
            total=480.0,
            loan_name="Prêt construction"
        )
        db.add(payment1)
        db.add(payment2)
        db.commit()
        
        # Calculer le coût du financement
        total = get_cout_financement(2024, db)
        
        # interest + insurance pour les deux prêts
        expected = (200.0 + 50.0) + (150.0 + 30.0)  # 250 + 180 = 430
        assert total == expected
        
        print("✅ Test get_cout_financement : PASSÉ")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
        raise
    finally:
        db.close()


def test_calculate_compte_resultat():
    """Test de calcul complet du compte de résultat."""
    cleanup_db()
    db = SessionLocal()
    try:
        # Créer des mappings
        mapping_produit = CompteResultatMapping(
            category_name="Loyers hors charge encaissés",
            level_1_values=["PRODUITS"],
            level_2_values=["LOYERS"]
        )
        mapping_charge = CompteResultatMapping(
            category_name="Charges de copropriété hors fonds travaux",
            level_1_values=None,
            level_2_values=["CHARGES_COPROPRIETE"]
        )
        db.add(mapping_produit)
        db.add(mapping_charge)
        db.commit()
        
        # Créer des transactions
        transaction_produit = Transaction(
            date=date(2024, 3, 15),
            quantite=10000.0,
            nom="Loyer",
            solde=10000.0
        )
        transaction_charge = Transaction(
            date=date(2024, 2, 1),
            quantite=-2000.0,
            nom="Charges copropriété",
            solde=-2000.0
        )
        db.add(transaction_produit)
        db.add(transaction_charge)
        db.commit()
        
        enriched_produit = EnrichedTransaction(
            transaction_id=transaction_produit.id,
            mois=3,
            annee=2024,
            level_1="PRODUITS",
            level_2="LOYERS"
        )
        enriched_charge = EnrichedTransaction(
            transaction_id=transaction_charge.id,
            mois=2,
            annee=2024,
            level_1="CHARGES",
            level_2="CHARGES_COPROPRIETE"
        )
        db.add(enriched_produit)
        db.add(enriched_charge)
        db.commit()
        
        # Créer des amortissements
        amort = AmortizationResult(
            transaction_id=1,
            year=2024,
            category="mobilier",
            amount=-1000.0
        )
        db.add(amort)
        db.commit()
        
        # Créer un loan_payment
        payment = LoanPayment(
            date=date(2024, 1, 1),
            capital=500.0,
            interest=200.0,
            insurance=50.0,
            total=750.0,
            loan_name="Prêt principal"
        )
        db.add(payment)
        db.commit()
        
        # Calculer le compte de résultat
        mappings = get_mappings(db)
        result = calculate_compte_resultat(2024, mappings, None, db)
        
        # Vérifier les résultats
        assert "Loyers hors charge encaissés" in result["categories"]
        assert result["categories"]["Loyers hors charge encaissés"] == 10000.0
        assert "Charges de copropriété hors fonds travaux" in result["categories"]
        assert result["categories"]["Charges de copropriété hors fonds travaux"] == 2000.0
        assert "Charges d'amortissements" in result["categories"]
        assert result["categories"]["Charges d'amortissements"] == 1000.0
        assert "Coût du financement (hors remboursement du capital)" in result["categories"]
        assert result["categories"]["Coût du financement (hors remboursement du capital)"] == 250.0
        
        assert result["total_produits"] == 10000.0
        assert result["total_charges"] == 3250.0  # 2000 + 1000 + 250
        assert result["resultat_exploitation"] == 6750.0  # 10000 - 3250
        assert result["resultat_net"] == 6750.0
        
        print("✅ Test calculate_compte_resultat : PASSÉ")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Tests du service compte de résultat")
    print("=" * 60)
    print()
    
    test_get_mappings()
    print()
    test_calculate_produits_exploitation()
    print()
    test_calculate_charges_exploitation()
    print()
    test_get_amortissements()
    print()
    test_get_cout_financement()
    print()
    test_calculate_compte_resultat()
    print()
    print("=" * 60)
    print("✅ Tous les tests sont passés !")
    print("=" * 60)

