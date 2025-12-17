"""
Test complet de la base de données avec données réelles.

Ce test valide que toutes les fonctionnalités de base de données fonctionnent
avec des données similaires à celles qui seront utilisées en production.

Run with: python3 backend/tests/test_database_complete.py
"""

import sys
from pathlib import Path
from datetime import date, datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database import init_database, get_db
from backend.database.models import (
    Transaction,
    EnrichedTransaction,
    Mapping,
    Parameter,
    Amortization,
    FinancialStatement,
    ConsolidatedFinancialStatement
)


def test_complete_workflow():
    """Test un workflow complet avec données réelles."""
    print("=" * 60)
    print("Test Complet Base de Données - Workflow Réel")
    print("=" * 60)
    
    # Initialiser la base de données
    print("\n1. Initialisation de la base de données...")
    init_database()
    print("✓ Base de données initialisée")
    
    db = next(get_db())
    
    try:
        # Nettoyer la base de données avant de commencer
        print("\n1.5. Nettoyage de la base de données...")
        db.query(ConsolidatedFinancialStatement).delete()
        db.query(FinancialStatement).delete()
        db.query(Amortization).delete()
        db.query(EnrichedTransaction).delete()
        db.query(Transaction).delete()
        db.query(Mapping).delete()
        db.query(Parameter).delete()
        db.commit()
        print("✓ Base de données nettoyée")
        
        # 2. Créer des transactions réelles
        print("\n2. Création de transactions réelles...")
        transactions = [
            Transaction(
                date=date(2024, 1, 15),
                quantite=850.0,
                nom="VIR STRIPE PAYMENTS",
                solde=5000.0,
                source_file="trades_evry_2024.csv"
            ),
            Transaction(
                date=date(2024, 1, 20),
                quantite=-120.0,
                nom="PRLV SEPA CHARGES COPRO",
                solde=4880.0,
                source_file="trades_evry_2024.csv"
            ),
            Transaction(
                date=date(2024, 2, 1),
                quantite=850.0,
                nom="VIR STRIPE PAYMENTS",
                solde=5730.0,
                source_file="trades_evry_2024.csv"
            ),
            Transaction(
                date=date(2024, 2, 5),
                quantite=-500.0,
                nom="ACHAT MEUBLES IKEA",
                solde=5230.0,
                source_file="trades_evry_2024.csv"
            ),
        ]
        
        for t in transactions:
            db.add(t)
        db.commit()
        
        # Vérifier insertion
        count = db.query(Transaction).count()
        assert count == 4, f"Attendu 4 transactions, trouvé {count}"
        print(f"✓ {count} transactions créées")
        
        # 3. Créer des mappings
        print("\n3. Création de mappings...")
        mappings = [
            Mapping(
                nom="VIR STRIPE PAYMENTS",
                level_1="loyers recu",
                level_2="Produit",
                level_3="Loyers",
                is_prefix_match=True,
                priority=10
            ),
            Mapping(
                nom="PRLV SEPA CHARGES COPRO",
                level_1="charges",
                level_2="Charges",
                level_3="Charges copropriété",
                is_prefix_match=True,
                priority=10
            ),
            Mapping(
                nom="ACHAT MEUBLES",
                level_1="ammortissements",
                level_2="ammortissements",
                level_3="Meubles",
                is_prefix_match=True,
                priority=5
            ),
        ]
        
        for m in mappings:
            db.add(m)
        db.commit()
        
        count = db.query(Mapping).count()
        assert count == 3, f"Attendu 3 mappings, trouvé {count}"
        print(f"✓ {count} mappings créés")
        
        # 4. Enrichir les transactions
        print("\n4. Enrichissement des transactions...")
        for transaction in transactions:
            db.refresh(transaction)
            
            # Trouver le mapping correspondant
            mapping = None
            for m in mappings:
                if transaction.nom.startswith(m.nom) or m.nom in transaction.nom:
                    mapping = m
                    break
            
            if mapping:
                enriched = EnrichedTransaction(
                    transaction_id=transaction.id,
                    mois=transaction.date.month,
                    annee=transaction.date.year,
                    level_1=mapping.level_1,
                    level_2=mapping.level_2,
                    level_3=mapping.level_3
                )
                db.add(enriched)
        
        db.commit()
        
        count = db.query(EnrichedTransaction).count()
        assert count == 4, f"Attendu 4 transactions enrichies, trouvé {count}"
        print(f"✓ {count} transactions enrichies")
        
        # Vérifier les classifications
        enriched = db.query(EnrichedTransaction).filter(
            EnrichedTransaction.level_1 == "loyers recu"
        ).all()
        assert len(enriched) == 2, "Devrait avoir 2 transactions de loyers"
        print("✓ Classifications correctes")
        
        # 5. Créer des paramètres
        print("\n5. Création de paramètres...")
        parameters = [
            Parameter(
                key="ammortissement meubles",
                value="5",
                value_type="int",
                description="Durée d'amortissement des meubles en années"
            ),
            Parameter(
                key="ammortissement travaux",
                value="10",
                value_type="int",
                description="Durée d'amortissement des travaux en années"
            ),
            Parameter(
                key="loyer",
                value="850.0",
                value_type="float",
                description="Montant du loyer mensuel"
            ),
        ]
        
        for p in parameters:
            db.add(p)
        db.commit()
        
        count = db.query(Parameter).count()
        assert count == 3, f"Attendu 3 paramètres, trouvé {count}"
        print(f"✓ {count} paramètres créés")
        
        # 6. Créer des amortissements
        print("\n6. Création d'amortissements...")
        # Trouver la transaction d'achat de meubles
        meubles_transaction = db.query(Transaction).filter(
            Transaction.nom.like("%MEUBLES%")
        ).first()
        
        assert meubles_transaction is not None, "Transaction meubles non trouvée"
        
        # Créer amortissement pour 2024 (proportionnel)
        amort = Amortization(
            type_amortissement="meubles",
            annee=2024,
            montant=-100.0,  # Amortissement annuel proportionnel
            transaction_id=meubles_transaction.id
        )
        db.add(amort)
        db.commit()
        
        count = db.query(Amortization).count()
        assert count == 1, f"Attendu 1 amortissement, trouvé {count}"
        print(f"✓ {count} amortissement créé")
        
        # 7. Créer des états financiers
        print("\n7. Création d'états financiers...")
        statements = [
            FinancialStatement(
                statement_type="compte_resultat",
                annee=2024,
                ligne="TRAVAUX ET PRESTATIONS DE SERV",
                montant=1700.0  # 2 loyers de 850
            ),
            FinancialStatement(
                statement_type="compte_resultat",
                annee=2024,
                ligne="Charges",
                montant=-120.0
            ),
            FinancialStatement(
                statement_type="compte_resultat",
                annee=2024,
                ligne="ammortissement meubles",
                montant=-100.0
            ),
            FinancialStatement(
                statement_type="bilan_actif",
                annee=2024,
                ligne="actifs",
                montant=500.0  # Achat meubles
            ),
            FinancialStatement(
                statement_type="bilan_actif",
                annee=2024,
                ligne="Actif circulant",
                montant=5230.0  # Dernier solde
            ),
        ]
        
        for s in statements:
            db.add(s)
        db.commit()
        
        count = db.query(FinancialStatement).count()
        assert count == 5, f"Attendu 5 états financiers, trouvé {count}"
        print(f"✓ {count} états financiers créés")
        
        # 8. Créer consolidation
        print("\n8. Création de consolidation...")
        consolidation = ConsolidatedFinancialStatement(
            annee=2024,
            total_actif=5630.0,  # 500 + 5230 - 100 (amortissement)
            total_passif=5630.0,
            difference=0.0,
            pourcentage_ecart=0.0
        )
        db.add(consolidation)
        db.commit()
        
        count = db.query(ConsolidatedFinancialStatement).count()
        assert count == 1, f"Attendu 1 consolidation, trouvé {count}"
        print(f"✓ Consolidation créée")
        
        # 9. Tests de requêtes complexes
        print("\n9. Tests de requêtes complexes...")
        
        # Requête transactions par mois
        transactions_janvier = db.query(Transaction).filter(
            Transaction.date >= date(2024, 1, 1),
            Transaction.date < date(2024, 2, 1)
        ).count()
        assert transactions_janvier == 2, "Devrait avoir 2 transactions en janvier"
        print("✓ Requête par mois fonctionne")
        
        # Requête transactions enrichies par catégorie
        produits = db.query(EnrichedTransaction).filter(
            EnrichedTransaction.level_2 == "Produit"
        ).count()
        assert produits == 2, "Devrait avoir 2 produits"
        print("✓ Requête par catégorie fonctionne")
        
        # Requête amortissements par type
        amort_meubles = db.query(Amortization).filter(
            Amortization.type_amortissement == "meubles"
        ).count()
        assert amort_meubles == 1, "Devrait avoir 1 amortissement meubles"
        print("✓ Requête amortissements fonctionne")
        
        # 10. Tests de relations
        print("\n10. Tests de relations entre tables...")
        
        # Transaction → EnrichedTransaction
        trans = db.query(Transaction).first()
        # La relation backref crée une liste, on prend le premier élément
        enriched_list = db.query(EnrichedTransaction).filter(
            EnrichedTransaction.transaction_id == trans.id
        ).all()
        assert len(enriched_list) > 0, "Transaction devrait avoir une enriched"
        assert enriched_list[0].level_1 is not None, "Enriched devrait avoir level_1"
        print("✓ Relation Transaction → EnrichedTransaction fonctionne")
        
        # Amortization → Transaction
        amort = db.query(Amortization).first()
        assert amort.transaction_id is not None, "Amortization devrait avoir transaction_id"
        print("✓ Relation Amortization → Transaction fonctionne")
        
        print("\n" + "=" * 60)
        print("✓ TOUS LES TESTS SONT PASSÉS!")
        print("=" * 60)
        print("\nRésumé:")
        print(f"  - {db.query(Transaction).count()} transactions")
        print(f"  - {db.query(EnrichedTransaction).count()} transactions enrichies")
        print(f"  - {db.query(Mapping).count()} mappings")
        print(f"  - {db.query(Parameter).count()} paramètres")
        print(f"  - {db.query(Amortization).count()} amortissements")
        print(f"  - {db.query(FinancialStatement).count()} états financiers")
        print(f"  - {db.query(ConsolidatedFinancialStatement).count()} consolidations")
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Nettoyage (optionnel - commenter pour garder les données)
        # db.query(ConsolidatedFinancialStatement).delete()
        # db.query(FinancialStatement).delete()
        # db.query(Amortization).delete()
        # db.query(EnrichedTransaction).delete()
        # db.query(Transaction).delete()
        # db.query(Mapping).delete()
        # db.query(Parameter).delete()
        # db.commit()
        db.close()


if __name__ == "__main__":
    success = test_complete_workflow()
    sys.exit(0 if success else 1)

