"""
Script pour assigner un property_id aux transactions existantes qui n'en ont pas.

⚠️ À utiliser AVANT d'ajouter la contrainte NOT NULL sur property_id
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database.connection import SessionLocal
from backend.database.models import Transaction, EnrichedTransaction, Property

def assign_property_id_to_transactions(property_id: int):
    """Assigner un property_id à toutes les transactions existantes."""
    db = SessionLocal()
    
    try:
        # Vérifier que la propriété existe
        property_obj = db.query(Property).filter(Property.id == property_id).first()
        if not property_obj:
            print(f"❌ Erreur: Property ID {property_id} n'existe pas")
            return False
        
        print(f"✅ Property trouvée: {property_obj.name} (ID={property_id})")
        
        # Compter les transactions sans property_id
        transactions_without_property = db.query(Transaction).filter(
            Transaction.property_id.is_(None)
        ).count()
        
        enriched_without_property = db.query(EnrichedTransaction).filter(
            EnrichedTransaction.property_id.is_(None)
        ).count()
        
        print(f"\n📊 Transactions à mettre à jour:")
        print(f"   - Transactions: {transactions_without_property}")
        print(f"   - EnrichedTransactions: {enriched_without_property}")
        
        if transactions_without_property == 0 and enriched_without_property == 0:
            print("\n✅ Toutes les transactions ont déjà un property_id")
            return True
        
        # Demander confirmation (sauf si --yes en argument)
        if '--yes' not in sys.argv:
            print(f"\n⚠️  Vous allez assigner property_id={property_id} à toutes les transactions existantes")
            response = input("Continuer ? (oui/non): ")
            
            if response.lower() not in ['oui', 'o', 'yes', 'y']:
                print("❌ Opération annulée")
                return False
        else:
            print(f"\n⚠️  Assignation de property_id={property_id} à toutes les transactions existantes (--yes activé)")
        
        # Mettre à jour les transactions
        updated_transactions = db.query(Transaction).filter(
            Transaction.property_id.is_(None)
        ).update({Transaction.property_id: property_id}, synchronize_session=False)
        
        # Mettre à jour les enriched_transactions
        updated_enriched = db.query(EnrichedTransaction).filter(
            EnrichedTransaction.property_id.is_(None)
        ).update({EnrichedTransaction.property_id: property_id}, synchronize_session=False)
        
        db.commit()
        
        print(f"\n✅ Mise à jour réussie:")
        print(f"   - {updated_transactions} transactions mises à jour")
        print(f"   - {updated_enriched} enriched_transactions mises à jour")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("ASSIGNATION DE PROPERTY_ID AUX TRANSACTIONS EXISTANTES")
    print("=" * 60)
    print()
    
    # Lister les propriétés disponibles
    db = SessionLocal()
    properties = db.query(Property).all()
    db.close()
    
    if not properties:
        print("❌ Aucune propriété trouvée. Créez d'abord une propriété.")
        sys.exit(1)
    
    print("📋 Propriétés disponibles:")
    for prop in properties:
        print(f"   - ID={prop.id}: {prop.name} ({prop.address})")
    
    print()
    
    # Accepter property_id en argument ou demander
    if len(sys.argv) > 1:
        try:
            property_id = int(sys.argv[1])
        except ValueError:
            print("❌ ID invalide en argument")
            sys.exit(1)
    else:
        property_id = input("Entrez l'ID de la propriété à assigner: ")
        try:
            property_id = int(property_id)
        except ValueError:
            print("❌ ID invalide")
            sys.exit(1)
    
    success = assign_property_id_to_transactions(property_id)
    
    if success:
        print("\n✅ Script terminé avec succès")
    else:
        print("\n❌ Script terminé avec erreur")
        sys.exit(1)
