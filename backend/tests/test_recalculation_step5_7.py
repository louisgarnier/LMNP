"""
Test Step 5.7 : Vérification du recalcul automatique après mise à jour de classification

Ce test vérifie si les données calculées (compte de résultat, amortissements) 
sont automatiquement mises à jour après une modification de classification.
"""

import sys
from pathlib import Path
from datetime import date

# Ajouter le répertoire racine au path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal
from backend.database.models import Transaction, EnrichedTransaction, Amortization, FinancialStatement
from backend.api.services.enrichment_service import enrich_transaction
from backend.api.routes.enrichment import update_transaction_classifications


def test_recalculation_after_classification_update():
    """Test si le recalcul est automatique après mise à jour de classification"""
    
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("TEST : Vérification du recalcul automatique")
        print("=" * 60)
        
        # 1. Créer une transaction de test
        print("\n1. Création d'une transaction de test...")
        test_transaction = Transaction(
            date=date(2024, 1, 15),
            quantite=1000.0,
            nom="TEST RECALCULATION",
            solde=1000.0
        )
        db.add(test_transaction)
        db.commit()
        db.refresh(test_transaction)
        print(f"   ✓ Transaction créée : ID {test_transaction.id}")
        
        # 2. Enrichir la transaction avec un mapping initial
        print("\n2. Enrichissement initial de la transaction...")
        enriched = enrich_transaction(test_transaction, db)
        print(f"   État initial :")
        print(f"     - level_1: {enriched.level_1}")
        print(f"     - level_2: {enriched.level_2}")
        print(f"     - level_3: {enriched.level_3}")
        
        # 3. Vérifier l'état des données calculées AVANT modification
        print("\n3. État des données calculées AVANT modification...")
        
        # Compte de résultat
        compte_resultat_before = db.query(FinancialStatement).filter(
            FinancialStatement.statement_type == 'compte_resultat'
        ).all()
        print(f"   Compte de résultat : {len(compte_resultat_before)} lignes")
        
        # Amortissements
        amortizations_before = db.query(Amortization).all()
        print(f"   Amortissements : {len(amortizations_before)} lignes")
        
        # 4. Modifier la classification de la transaction
        print("\n4. Modification de la classification...")
        # Note: On ne peut pas appeler directement l'endpoint, donc on simule
        # en modifiant directement le mapping et en re-enrichissant
        from backend.database.models import Mapping
        from backend.api.services.enrichment_service import create_or_update_mapping_from_classification
        
        # Créer un mapping avec de nouvelles valeurs
        try:
            create_or_update_mapping_from_classification(
                db=db,
                transaction_name=test_transaction.nom,
                level_1="Charges",
                level_2="Charges Déductibles",
                level_3="Charges Déductibles"
            )
            print("   ✓ Mapping créé/mis à jour")
        except Exception as e:
            print(f"   ⚠ Erreur lors de la création du mapping : {e}")
        
        # Re-enrichir la transaction
        enriched_after = enrich_transaction(test_transaction, db)
        print(f"   État après modification :")
        print(f"     - level_1: {enriched_after.level_1}")
        print(f"     - level_2: {enriched_after.level_2}")
        print(f"     - level_3: {enriched_after.level_3}")
        
        # 5. Vérifier l'état des données calculées APRÈS modification
        print("\n5. État des données calculées APRÈS modification...")
        
        # Compte de résultat
        compte_resultat_after = db.query(FinancialStatement).filter(
            FinancialStatement.statement_type == 'compte_resultat'
        ).all()
        print(f"   Compte de résultat : {len(compte_resultat_after)} lignes")
        
        # Amortissements
        amortizations_after = db.query(Amortization).all()
        print(f"   Amortissements : {len(amortizations_after)} lignes")
        
        # 6. Analyse
        print("\n6. Analyse...")
        compte_resultat_changed = len(compte_resultat_after) != len(compte_resultat_before)
        amortizations_changed = len(amortizations_after) != len(amortizations_before)
        
        if compte_resultat_changed or amortizations_changed:
            print("   ⚠ Les données calculées ont changé (recalcul automatique détecté)")
        else:
            print("   ⚠ Les données calculées n'ont pas changé")
            print("   → Le recalcul automatique n'est peut-être pas implémenté")
            print("   → Les données sont peut-être calculées à la volée (pas de cache)")
        
        # 7. Nettoyage
        print("\n7. Nettoyage...")
        db.query(EnrichedTransaction).filter(
            EnrichedTransaction.transaction_id == test_transaction.id
        ).delete()
        db.query(Mapping).filter(
            Mapping.nom == test_transaction.nom
        ).delete()
        db.delete(test_transaction)
        db.commit()
        print("   ✓ Données de test supprimées")
        
        print("\n" + "=" * 60)
        print("CONCLUSION")
        print("=" * 60)
        print("Les données calculées semblent être calculées à la volée")
        print("ou mises en cache dans les tables financial_statements et amortizations.")
        print("Si elles sont mises en cache, il faudrait implémenter une invalidation")
        print("après chaque mise à jour de classification.")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERREUR DE TEST : {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()


if __name__ == "__main__":
    success = test_recalculation_after_classification_update()
    sys.exit(0 if success else 1)

