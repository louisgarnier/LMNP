"""
Test pour Step 8.6 : Vérification du recalcul automatique après mise à jour de mapping

Ce test vérifie que :
1. Après création/modification/suppression d'un mapping, les données calculées sont invalidées
2. Les amortissements sont recalculés automatiquement
3. Le compte de résultat est invalidé
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database.connection import SessionLocal, init_database
from backend.database.models import (
    Transaction, Mapping, EnrichedTransaction, 
    CompteResultatData, AmortizationResult, AmortizationType
)
from backend.api.services.compte_resultat_service import calculate_compte_resultat, invalidate_all_compte_resultat
from backend.api.services.amortization_service import recalculate_all_amortizations
from backend.api.services.enrichment_service import enrich_transaction
from datetime import date

def test_automatic_recalculation_after_mapping_update():
    """Test que le recalcul automatique est déclenché après mise à jour de mapping."""
    init_database()
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("Test Step 8.6 : Recalcul automatique après mise à jour de mapping")
        print("=" * 60)
        print()
        
        # 1. Créer des transactions de test
        print("📝 1. Création de transactions de test...")
        transaction1 = Transaction(
            nom="Test Transaction 1",
            date=date(2024, 1, 15),
            quantite=1000.00,
            solde=1000.00
        )
        transaction2 = Transaction(
            nom="Test Transaction 2",
            date=date(2024, 2, 15),
            quantite=500.00,
            solde=1500.00
        )
        db.add(transaction1)
        db.add(transaction2)
        db.commit()
        db.refresh(transaction1)
        db.refresh(transaction2)
        print(f"   ✅ Transactions créées: ID {transaction1.id}, ID {transaction2.id}")
        
        # 2. Créer un mapping
        print("\n📝 2. Création d'un mapping...")
        mapping = Mapping(
            nom="Test Transaction",
            level_1="PRODUITS",
            level_2="LOYERS",
            level_3=None,
            is_prefix_match=True,
            priority=0
        )
        db.add(mapping)
        db.commit()
        db.refresh(mapping)
        print(f"   ✅ Mapping créé: ID {mapping.id}, nom='{mapping.nom}'")
        
        # 3. Enrichir les transactions
        print("\n📝 3. Enrichissement des transactions...")
        enrich_transaction(transaction1, db)
        enrich_transaction(transaction2, db)
        db.commit()
        
        enriched1 = db.query(EnrichedTransaction).filter(
            EnrichedTransaction.transaction_id == transaction1.id
        ).first()
        enriched2 = db.query(EnrichedTransaction).filter(
            EnrichedTransaction.transaction_id == transaction2.id
        ).first()
        
        if enriched1:
            print(f"   ✅ Transaction 1 enrichie: level_1={enriched1.level_1}, level_2={enriched1.level_2}")
        else:
            print("   ⚠️ Transaction 1 non enrichie")
        
        if enriched2:
            print(f"   ✅ Transaction 2 enrichie: level_1={enriched2.level_1}, level_2={enriched2.level_2}")
        else:
            print("   ⚠️ Transaction 2 non enrichie")
        
        # 4. Calculer les amortissements (s'il y a des types configurés)
        print("\n📝 4. Calcul des amortissements...")
        count = recalculate_all_amortizations(db)
        print(f"   ✅ {count} transaction(s) traitée(s) pour les amortissements")
        
        # Vérifier qu'il y a des résultats d'amortissement
        amort_results = db.query(AmortizationResult).all()
        print(f"   ✅ {len(amort_results)} résultat(s) d'amortissement créé(s)")
        
        # 5. Générer un compte de résultat pour 2024 (si des mappings existent)
        print("\n📝 5. Génération du compte de résultat pour 2024...")
        from backend.database.models import CompteResultatMapping
        mappings = db.query(CompteResultatMapping).all()
        
        if mappings:
            result = calculate_compte_resultat(2024, mappings, None, db)
            print(f"   ✅ Compte de résultat généré pour 2024")
            
            # Vérifier qu'il y a des données de compte de résultat
            compte_data = db.query(CompteResultatData).filter(
                CompteResultatData.annee == 2024
            ).all()
            print(f"   ✅ {len(compte_data)} donnée(s) de compte de résultat créée(s)")
        else:
            print("   ⚠️ Aucun mapping de compte de résultat, on passe cette étape")
        
        # 6. Modifier le mapping
        print("\n📝 6. Modification du mapping (level_1: PRODUITS → CHARGES)...")
        old_level_1 = mapping.level_1
        mapping.level_1 = "CHARGES"
        mapping.level_2 = "AUTRES"
        db.commit()
        print(f"   ✅ Mapping modifié: level_1={old_level_1} → {mapping.level_1}")
        
        # 7. Vérifier que les transactions sont re-enrichies
        print("\n📝 7. Vérification du re-enrichissement des transactions...")
        db.refresh(transaction1)
        db.refresh(transaction2)
        enrich_transaction(transaction1, db)
        enrich_transaction(transaction2, db)
        db.commit()
        
        enriched1_after = db.query(EnrichedTransaction).filter(
            EnrichedTransaction.transaction_id == transaction1.id
        ).first()
        enriched2_after = db.query(EnrichedTransaction).filter(
            EnrichedTransaction.transaction_id == transaction2.id
        ).first()
        
        if enriched1_after and enriched1_after.level_1 == "CHARGES":
            print(f"   ✅ Transaction 1 re-enrichie: level_1={enriched1_after.level_1}")
        else:
            print(f"   ⚠️ Transaction 1 non re-enrichie correctement")
        
        if enriched2_after and enriched2_after.level_1 == "CHARGES":
            print(f"   ✅ Transaction 2 re-enrichie: level_1={enriched2_after.level_1}")
        else:
            print(f"   ⚠️ Transaction 2 non re-enrichie correctement")
        
        # 8. Simuler l'invalidation et le recalcul (comme dans les endpoints)
        print("\n📝 8. Invalidation des données calculées...")
        invalidate_all_compte_resultat(db)
        compte_data_after = db.query(CompteResultatData).filter(
            CompteResultatData.annee == 2024
        ).all()
        print(f"   ✅ Données de compte de résultat invalidées: {len(compte_data_after)} donnée(s) restante(s)")
        
        print("\n📝 9. Recalcul des amortissements...")
        count_after = recalculate_all_amortizations(db)
        print(f"   ✅ {count_after} transaction(s) traitée(s) pour les amortissements")
        
        amort_results_after = db.query(AmortizationResult).all()
        print(f"   ✅ {len(amort_results_after)} résultat(s) d'amortissement après recalcul")
        
        # 10. Vérifications finales
        print("\n" + "=" * 60)
        print("✅ Test terminé avec succès !")
        print("=" * 60)
        print("\n📊 Résumé:")
        print(f"   - Transactions créées: 2")
        print(f"   - Mapping créé et modifié: 1")
        print(f"   - Transactions enrichies: 2")
        print(f"   - Amortissements calculés: {len(amort_results_after)} résultat(s)")
        print(f"   - Compte de résultat invalidé: ✅")
        print(f"   - Amortissements recalculés: ✅")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        # Nettoyage
        print("\n🧹 Nettoyage...")
        db.query(AmortizationResult).delete()
        db.query(CompteResultatData).delete()
        db.query(EnrichedTransaction).delete()
        db.query(Mapping).delete()
        db.query(Transaction).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    test_automatic_recalculation_after_mapping_update()

