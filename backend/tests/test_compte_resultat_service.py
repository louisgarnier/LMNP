"""
Tests unitaires pour le service compte_resultat_service.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path

# Ajouter le répertoire racine au path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from datetime import date
import json
from sqlalchemy.orm import Session

from backend.database import init_database, SessionLocal
from backend.database.models import (
    Transaction,
    EnrichedTransaction,
    CompteResultatMapping,
    CompteResultatData,
    CompteResultatConfig,
    AmortizationResult,
    LoanPayment,
    LoanConfig
)
from backend.api.services.compte_resultat_service import (
    get_mappings,
    get_level_3_values,
    calculate_produits_exploitation,
    calculate_charges_exploitation,
    get_amortissements,
    get_cout_financement,
    calculate_compte_resultat
)


def test_get_mappings():
    """Test récupération des mappings."""
    print("\nTesting get_mappings()...")
    db = SessionLocal()
    try:
        mappings = get_mappings(db)
        print(f"✓ Found {len(mappings)} mappings")
    finally:
        db.close()


def test_get_level_3_values():
    """Test récupération des valeurs level_3 depuis la config."""
    print("\nTesting get_level_3_values()...")
    db = SessionLocal()
    try:
        # Créer une config de test
        config = db.query(CompteResultatConfig).first()
        if not config:
            config = CompteResultatConfig(level_3_values='["Produits", "Charges Déductibles"]')
            db.add(config)
            db.commit()
        
        level_3_values = get_level_3_values(db)
        print(f"✓ Level 3 values: {level_3_values}")
        assert isinstance(level_3_values, list)
    finally:
        db.close()


def test_calculate_produits_exploitation():
    """Test calcul des produits d'exploitation."""
    print("\nTesting calculate_produits_exploitation()...")
    db = SessionLocal()
    try:
        # Créer des données de test
        year = 2024
        
        # Créer une transaction de test
        transaction = Transaction(
            date=date(year, 6, 15),
            quantite=1000.0,
            nom="Loyer encaissé",
            solde=1000.0
        )
        db.add(transaction)
        db.flush()
        
        enriched = EnrichedTransaction(
            transaction_id=transaction.id,
            annee=year,
            mois=6,
            level_1="LOYERS",
            level_2=None,
            level_3="Produits"
        )
        db.add(enriched)
        db.commit()
        
        # Créer un mapping
        mapping = CompteResultatMapping(
            category_name="Loyers hors charge encaissés",
            level_1_values='["LOYERS"]'
        )
        db.add(mapping)
        db.commit()
        
        # Tester le calcul
        level_3_values = ["Produits"]
        produits = calculate_produits_exploitation(db, year, [mapping], level_3_values)
        print(f"✓ Produits calculés: {produits}")
        assert "Loyers hors charge encaissés" in produits
        assert produits["Loyers hors charge encaissés"] == 1000.0
        
        # Nettoyer
        db.delete(enriched)
        db.delete(transaction)
        db.delete(mapping)
        db.commit()
    finally:
        db.close()


def test_calculate_charges_exploitation():
    """Test calcul des charges d'exploitation."""
    print("\nTesting calculate_charges_exploitation()...")
    db = SessionLocal()
    try:
        # Créer des données de test
        year = 2024
        
        # Créer une transaction de test (charge négative)
        transaction = Transaction(
            date=date(year, 6, 15),
            quantite=-500.0,
            nom="Charge déductible",
            solde=-500.0
        )
        db.add(transaction)
        db.flush()
        
        enriched = EnrichedTransaction(
            transaction_id=transaction.id,
            annee=year,
            mois=6,
            level_1="CHARGES",
            level_2=None,
            level_3="Charges Déductibles"
        )
        db.add(enriched)
        db.commit()
        
        # Créer un mapping
        mapping = CompteResultatMapping(
            category_name="Charges d'exploitation",
            level_1_values='["CHARGES"]'
        )
        db.add(mapping)
        db.commit()
        
        # Tester le calcul
        level_3_values = ["Charges Déductibles"]
        charges = calculate_charges_exploitation(db, year, [mapping], level_3_values)
        print(f"✓ Charges calculées: {charges}")
        assert "Charges d'exploitation" in charges
        assert charges["Charges d'exploitation"] == -500.0
        
        # Nettoyer
        db.delete(enriched)
        db.delete(transaction)
        db.delete(mapping)
        db.commit()
    finally:
        db.close()


def test_get_amortissements():
    """Test récupération des amortissements depuis amortization_result."""
    print("\nTesting get_amortissements()...")
    db = SessionLocal()
    try:
        # Utiliser une année qui n'a probablement pas de données (2099)
        year = 2099
        
        # Créer un résultat d'amortissement de test
        amort_result = AmortizationResult(
            transaction_id=1,
            year=year,
            category="Test Category",
            amount=1000.0
        )
        db.add(amort_result)
        db.commit()
        
        # Tester la récupération
        amortissements = get_amortissements(db, year)
        print(f"✓ Amortissements récupérés: {amortissements}")
        assert amortissements == 1000.0
        
        # Tester avec une année sans amortissements
        amortissements_2025 = get_amortissements(db, 2025)
        print(f"✓ Amortissements pour 2025 (sans données): {amortissements_2025}")
        # Peut être 0.0 ou une valeur existante dans la base
        
        # Nettoyer
        db.delete(amort_result)
        db.commit()
    finally:
        db.close()


def test_get_cout_financement():
    """Test calcul du coût du financement depuis loan_payments."""
    print("\nTesting get_cout_financement()...")
    db = SessionLocal()
    try:
        # Utiliser une année qui n'a probablement pas de données (2099)
        year = 2099
        
        # Créer des mensualités de test
        payment1 = LoanPayment(
            date=date(year, 1, 1),
            capital=400.0,
            interest=200.0,
            insurance=50.0,
            total=650.0,
            loan_name="Prêt test"
        )
        payment2 = LoanPayment(
            date=date(year, 6, 1),
            capital=400.0,
            interest=200.0,
            insurance=50.0,
            total=650.0,
            loan_name="Prêt test"
        )
        db.add(payment1)
        db.add(payment2)
        db.commit()
        
        # Tester le calcul
        cout_financement = get_cout_financement(db, year)
        print(f"✓ Coût du financement calculé: {cout_financement}")
        # (200 + 50) * 2 = 500
        assert cout_financement == 500.0
        
        # Tester avec une année sans données
        cout_financement_2025 = get_cout_financement(db, 2025)
        print(f"✓ Coût du financement pour 2025: {cout_financement_2025}")
        # Peut être 0.0 ou une valeur existante dans la base
        
        # Nettoyer
        db.delete(payment1)
        db.delete(payment2)
        db.commit()
    finally:
        db.close()


def test_calculate_compte_resultat():
    """Test calcul complet du compte de résultat."""
    print("\nTesting calculate_compte_resultat()...")
    db = SessionLocal()
    try:
        year = 2024
        
        # Créer des données de test
        # Transaction produit
        transaction1 = Transaction(
            date=date(year, 6, 15),
            quantite=1000.0,
            nom="Loyer encaissé",
            solde=1000.0
        )
        db.add(transaction1)
        db.flush()
        
        enriched1 = EnrichedTransaction(
            transaction_id=transaction1.id,
            annee=year,
            mois=6,
            level_1="LOYERS",
            level_2=None,
            level_3="Produits"
        )
        db.add(enriched1)
        
        # Transaction charge
        transaction2 = Transaction(
            date=date(year, 6, 15),
            quantite=-500.0,
            nom="Charge déductible",
            solde=-500.0
        )
        db.add(transaction2)
        db.flush()
        
        enriched2 = EnrichedTransaction(
            transaction_id=transaction2.id,
            annee=year,
            mois=6,
            level_1="CHARGES",
            level_2=None,
            level_3="Charges Déductibles"
        )
        db.add(enriched2)
        db.commit()
        
        # Créer des mappings
        mapping1 = CompteResultatMapping(
            category_name="Loyers hors charge encaissés",
            level_1_values='["LOYERS"]'
        )
        mapping2 = CompteResultatMapping(
            category_name="Charges d'exploitation",
            level_1_values='["CHARGES"]'
        )
        db.add(mapping1)
        db.add(mapping2)
        db.commit()
        
        # Créer config level_3
        config = db.query(CompteResultatConfig).first()
        if not config:
            config = CompteResultatConfig(level_3_values='["Produits", "Charges Déductibles"]')
            db.add(config)
            db.commit()
        
        # Tester le calcul complet
        result = calculate_compte_resultat(db, year)
        print(f"✓ Résultat complet: {result}")
        assert "produits" in result
        assert "charges" in result
        assert "resultat_exploitation" in result
        assert "resultat_net" in result
        
        # Nettoyer
        db.delete(enriched1)
        db.delete(enriched2)
        db.delete(transaction1)
        db.delete(transaction2)
        db.delete(mapping1)
        db.delete(mapping2)
        db.commit()
    finally:
        db.close()


def test_regroupement_mappings():
    """Test regroupement des mappings d'une même catégorie avec OR."""
    print("\nTesting regroupement des mappings (OR)...")
    db = SessionLocal()
    try:
        year = 2024
        
        # Créer des transactions avec différents level_1
        transaction1 = Transaction(
            date=date(year, 6, 15),
            quantite=1000.0,
            nom="Loyer 1",
            solde=1000.0
        )
        transaction2 = Transaction(
            date=date(year, 6, 15),
            quantite=500.0,
            nom="Loyer 2",
            solde=500.0
        )
        db.add(transaction1)
        db.add(transaction2)
        db.flush()
        
        enriched1 = EnrichedTransaction(
            transaction_id=transaction1.id,
            annee=year,
            mois=6,
            level_1="LOYERS",
            level_2=None,
            level_3="Produits"
        )
        enriched2 = EnrichedTransaction(
            transaction_id=transaction2.id,
            annee=year,
            mois=6,
            level_1="REVENUS",
            level_2=None,
            level_3="Produits"
        )
        db.add(enriched1)
        db.add(enriched2)
        db.commit()
        
        # Créer deux mappings pour la même catégorie (OR)
        mapping1 = CompteResultatMapping(
            category_name="Loyers hors charge encaissés",
            level_1_values='["LOYERS"]'
        )
        mapping2 = CompteResultatMapping(
            category_name="Loyers hors charge encaissés",
            level_1_values='["REVENUS"]'
        )
        db.add(mapping1)
        db.add(mapping2)
        db.commit()
        
        # Tester le calcul (les deux transactions doivent être regroupées)
        level_3_values = ["Produits"]
        produits = calculate_produits_exploitation(db, year, [mapping1, mapping2], level_3_values)
        print(f"✓ Produits avec regroupement OR: {produits}")
        assert "Loyers hors charge encaissés" in produits
        # Les deux transactions doivent être comptées (1000 + 500 = 1500)
        assert produits["Loyers hors charge encaissés"] == 1500.0
        
        # Nettoyer
        db.delete(enriched1)
        db.delete(enriched2)
        db.delete(transaction1)
        db.delete(transaction2)
        db.delete(mapping1)
        db.delete(mapping2)
        db.commit()
    finally:
        db.close()


def main():
    """Exécuter tous les tests."""
    print("=" * 60)
    print("Testing Compte Resultat Service")
    print("=" * 60)
    
    # Initialiser la base de données
    init_database()
    
    try:
        test_get_mappings()
        test_get_level_3_values()
        test_calculate_produits_exploitation()
        test_calculate_charges_exploitation()
        test_get_amortissements()
        test_get_cout_financement()
        test_calculate_compte_resultat()
        test_regroupement_mappings()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
