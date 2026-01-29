"""
Test Step 1 : Vérification des modèles SQLAlchemy avec property_id

Ce script vérifie que :
1. Les modèles Transaction et EnrichedTransaction se chargent correctement
2. Les colonnes property_id sont présentes
3. Les relations sont correctement définies
4. Les index sont définis
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database.models import Transaction, EnrichedTransaction, Property, Base
from sqlalchemy import inspect

print("=" * 60)
print("TEST STEP 1 : Modèles SQLAlchemy avec property_id")
print("=" * 60)
print()

# Vérifier que les modèles se chargent sans erreur
print("✅ Import des modèles réussi")

# Inspecter les modèles
inspector = inspect(Transaction)
enriched_inspector = inspect(EnrichedTransaction)
property_inspector = inspect(Property)

print("\n📋 Vérification du modèle Transaction:")
print(f"   - Table: {Transaction.__tablename__}")
columns = [col.name for col in inspector.columns]
print(f"   - Colonnes: {', '.join(columns)}")

if 'property_id' in columns:
    print("   ✅ property_id présent")
    # Vérifier la contrainte FK
    property_id_col = next(col for col in inspector.columns if col.name == 'property_id')
    if property_id_col.foreign_keys:
        fk = list(property_id_col.foreign_keys)[0]
        print(f"   ✅ ForeignKey vers: {fk.column.table.name}.{fk.column.name}")
        if 'CASCADE' in str(fk.ondelete):
            print("   ✅ ON DELETE CASCADE configuré")
        else:
            print("   ⚠️  ON DELETE CASCADE non trouvé")
    else:
        print("   ❌ ForeignKey non trouvé")
else:
    print("   ❌ property_id manquant")

# Vérifier les index
indexes = [idx.name for idx in Transaction.__table__.indexes]
print(f"   - Index: {', '.join(indexes)}")
if 'idx_transactions_property_id' in indexes:
    print("   ✅ idx_transactions_property_id présent")
else:
    print("   ❌ idx_transactions_property_id manquant")

# Vérifier les relations
if hasattr(Transaction, 'property'):
    print("   ✅ Relation 'property' présente")
else:
    print("   ❌ Relation 'property' manquante")

print("\n📋 Vérification du modèle EnrichedTransaction:")
print(f"   - Table: {EnrichedTransaction.__tablename__}")
columns = [col.name for col in enriched_inspector.columns]
print(f"   - Colonnes: {', '.join(columns)}")

if 'property_id' in columns:
    print("   ✅ property_id présent")
    # Vérifier la contrainte FK
    property_id_col = next(col for col in enriched_inspector.columns if col.name == 'property_id')
    if property_id_col.foreign_keys:
        fk = list(property_id_col.foreign_keys)[0]
        print(f"   ✅ ForeignKey vers: {fk.column.table.name}.{fk.column.name}")
        if 'CASCADE' in str(fk.ondelete):
            print("   ✅ ON DELETE CASCADE configuré")
        else:
            print("   ⚠️  ON DELETE CASCADE non trouvé")
    else:
        print("   ❌ ForeignKey non trouvé")
else:
    print("   ❌ property_id manquant")

# Vérifier les index
indexes = [idx.name for idx in EnrichedTransaction.__table__.indexes]
print(f"   - Index: {', '.join(indexes)}")
if 'idx_enriched_transactions_property_id' in indexes:
    print("   ✅ idx_enriched_transactions_property_id présent")
else:
    print("   ❌ idx_enriched_transactions_property_id manquant")

# Vérifier les relations
if hasattr(EnrichedTransaction, 'property'):
    print("   ✅ Relation 'property' présente")
else:
    print("   ❌ Relation 'property' manquante")

print("\n📋 Vérification du modèle Property:")
if hasattr(Property, 'transactions'):
    print("   ✅ Relation 'transactions' présente")
else:
    print("   ❌ Relation 'transactions' manquante")
if hasattr(Property, 'enriched_transactions'):
    print("   ✅ Relation 'enriched_transactions' présente")
else:
    print("   ❌ Relation 'enriched_transactions' manquante")

print("\n" + "=" * 60)
print("✅ Test Step 1 terminé - Vérifiez les résultats ci-dessus")
print("=" * 60)
