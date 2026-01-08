"""
Test pour comprendre pourquoi certaines transactions ne sont pas classées
alors qu'elles ont un mapping défini.

Exemple : "VIR MANGOPAY D64E8E716D144BFD99C45E0C6B9FF431 MASTEOS 6911163C LOYER 1 HOMEGA"
"""

import sys
from pathlib import Path
from datetime import date

# Ajouter le répertoire racine au path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal
from backend.database.models import Transaction, Mapping, EnrichedTransaction
from backend.api.services.enrichment_service import (
    find_best_mapping,
    enrich_transaction,
    transaction_matches_mapping_name
)


def test_transaction_not_classified():
    """Test pourquoi une transaction n'est pas classée"""
    
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("TEST : Transaction non classée alors qu'un mapping existe")
        print("=" * 60)
        
        transaction_name = "VIR MANGOPAY D64E8E716D144BFD99C45E0C6B9FF431 MASTEOS 6911163C LOYER 1 HOMEGA"
        
        # 1. Vérifier si un mapping existe pour ce nom
        print(f"\n1. Recherche de mappings pour : '{transaction_name}'")
        all_mappings = db.query(Mapping).all()
        print(f"   Nombre total de mappings : {len(all_mappings)}")
        
        # Chercher les mappings qui correspondent
        matching_mappings = []
        for mapping in all_mappings:
            if transaction_matches_mapping_name(transaction_name, mapping.nom):
                matching_mappings.append(mapping)
                print(f"   ✓ Mapping correspondant trouvé :")
                print(f"     - ID: {mapping.id}")
                print(f"     - Nom: '{mapping.nom}'")
                print(f"     - level_1: {mapping.level_1}")
                print(f"     - level_2: {mapping.level_2}")
                print(f"     - level_3: {mapping.level_3}")
                print(f"     - is_prefix_match: {mapping.is_prefix_match}")
        
        if len(matching_mappings) == 0:
            print(f"   ✗ Aucun mapping correspondant trouvé")
            print(f"\n   Recherche de mappings avec 'VIR MANGOPAY' ou 'MANGOPAY' dans le nom...")
            mangopay_mappings = db.query(Mapping).filter(
                Mapping.nom.contains('MANGOPAY')
            ).all()
            if mangopay_mappings:
                print(f"   Mappings trouvés avec 'MANGOPAY':")
                for m in mangopay_mappings:
                    print(f"     - ID: {m.id}, Nom: '{m.nom}'")
            else:
                print(f"   Aucun mapping avec 'MANGOPAY' trouvé")
        elif len(matching_mappings) == 1:
            print(f"\n   ✓ Un seul mapping correspondant trouvé")
        else:
            print(f"\n   ⚠ {len(matching_mappings)} mappings correspondent (c'est pour ça qu'elle reste non classée)")
            print(f"   C'est le comportement attendu depuis Step 5.3 : si plusieurs mappings correspondent,")
            print(f"   la transaction reste non classée pour éviter les conflits.")
        
        # 2. Tester find_best_mapping
        print(f"\n2. Test de find_best_mapping()")
        best_mapping = find_best_mapping(transaction_name, all_mappings)
        if best_mapping:
            print(f"   ✓ find_best_mapping() retourne un mapping:")
            print(f"     - Nom: '{best_mapping.nom}'")
            print(f"     - level_1: {best_mapping.level_1}")
            print(f"     - level_2: {best_mapping.level_2}")
            print(f"     - level_3: {best_mapping.level_3}")
        else:
            print(f"   ✗ find_best_mapping() retourne None")
            if len(matching_mappings) > 1:
                print(f"   → Raison : {len(matching_mappings)} mappings correspondent (Step 5.3)")
            else:
                print(f"   → Raison : Aucun mapping ne correspond")
        
        # 3. Vérifier si la transaction existe et son état
        print(f"\n3. Recherche de la transaction dans la base")
        transaction = db.query(Transaction).filter(
            Transaction.nom == transaction_name
        ).first()
        
        if transaction:
            print(f"   ✓ Transaction trouvée : ID {transaction.id}")
            enriched = db.query(EnrichedTransaction).filter(
                EnrichedTransaction.transaction_id == transaction.id
            ).first()
            
            if enriched:
                print(f"   État actuel de l'enrichissement :")
                print(f"     - level_1: {enriched.level_1}")
                print(f"     - level_2: {enriched.level_2}")
                print(f"     - level_3: {enriched.level_3}")
                
                if enriched.level_1 is None and enriched.level_2 is None and enriched.level_3 is None:
                    print(f"   ✗ Transaction est non classée (unassigned)")
                else:
                    print(f"   ✓ Transaction est classée")
            else:
                print(f"   ✗ Aucun EnrichedTransaction trouvé (transaction non enrichie)")
        else:
            print(f"   ⚠ Transaction non trouvée dans la base")
            print(f"   Création d'une transaction de test pour tester l'enrichissement...")
            
            test_transaction = Transaction(
                date=date(2024, 1, 15),
                quantite=100.0,
                nom=transaction_name,
                solde=1000.0
            )
            db.add(test_transaction)
            db.commit()
            db.refresh(test_transaction)
            
            print(f"   ✓ Transaction de test créée : ID {test_transaction.id}")
            
            # Tester l'enrichissement
            print(f"\n4. Test de l'enrichissement de la transaction")
            enriched = enrich_transaction(test_transaction, db)
            
            print(f"   Résultat de l'enrichissement :")
            print(f"     - level_1: {enriched.level_1}")
            print(f"     - level_2: {enriched.level_2}")
            print(f"     - level_3: {enriched.level_3}")
            
            if enriched.level_1 is None and enriched.level_2 is None and enriched.level_3 is None:
                print(f"   ✗ Transaction reste non classée après enrichissement")
                if len(matching_mappings) > 1:
                    print(f"   → Cause : {len(matching_mappings)} mappings correspondent (Step 5.3)")
                else:
                    print(f"   → Cause : find_best_mapping() retourne None")
            else:
                print(f"   ✓ Transaction a été classée")
            
            # Nettoyer
            db.query(EnrichedTransaction).filter(
                EnrichedTransaction.transaction_id == test_transaction.id
            ).delete()
            db.delete(test_transaction)
            db.commit()
        
        print("\n" + "=" * 60)
        print("FIN DU TEST")
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
    success = test_transaction_not_classified()
    sys.exit(0 if success else 1)

