#!/usr/bin/env python3
"""
Script pour afficher le contenu de la table compte_resultat_mappings.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.database.models import CompteResultatMapping

def main():
    """Affiche le contenu de la table compte_resultat_mappings."""
    print("=" * 80)
    print("  CONTENU DE LA TABLE compte_resultat_mappings")
    print("=" * 80)
    print()
    
    # Initialize database to ensure tables exist
    init_database()
    
    db = SessionLocal()
    try:
        # Récupérer tous les mappings
        mappings = db.query(CompteResultatMapping).order_by(CompteResultatMapping.category_name).all()
        
        if not mappings:
            print("❌ Aucun mapping trouvé dans la table compte_resultat_mappings")
            print()
            print("La table est vide.")
            return
        
        print(f"📊 Nombre de mappings trouvés: {len(mappings)}")
        print()
        
        # Grouper par type (Produits/Charges)
        produits = []
        charges = []
        speciales = []
        
        PRODUITS_CATEGORIES = [
            'Loyers hors charge encaissés',
            'Charges locatives payées par locataires',
            'Autres revenus',
        ]
        
        CHARGES_CATEGORIES = [
            'Charges de copropriété hors fonds travaux',
            'Fluides non refacturés',
            'Assurances',
            'Honoraires',
            'Travaux et mobilier',
            'Impôts et taxes',
            'Autres charges diverses',
        ]
        
        SPECIAL_CATEGORIES = [
            "Charges d'amortissements",
            'Coût du financement (hors remboursement du capital)',
        ]
        
        for mapping in mappings:
            if mapping.category_name in PRODUITS_CATEGORIES:
                produits.append(mapping)
            elif mapping.category_name in CHARGES_CATEGORIES:
                charges.append(mapping)
            elif mapping.category_name in SPECIAL_CATEGORIES:
                speciales.append(mapping)
            else:
                # Catégorie non reconnue
                charges.append(mapping)
        
        # Afficher les Produits d'exploitation
        if produits:
            print("-" * 80)
            print("📈 PRODUITS D'EXPLOITATION")
            print("-" * 80)
            for mapping in produits:
                print(f"\n  Catégorie: {mapping.category_name}")
                print(f"  ID: {mapping.id}")
                print(f"  Created at: {mapping.created_at}")
                print(f"  Updated at: {mapping.updated_at}")
                if mapping.level_1_values:
                    try:
                        values = json.loads(mapping.level_1_values)
                        if isinstance(values, list) and len(values) > 0:
                            print(f"  Level 1 values ({len(values)}):")
                            for val in values:
                                print(f"    - {val}")
                        else:
                            print(f"  Level 1 values: [] (vide)")
                    except json.JSONDecodeError as e:
                        print(f"  ⚠️  Erreur de parsing JSON: {e}")
                        print(f"  Level 1 values (raw): {mapping.level_1_values}")
                else:
                    print(f"  Level 1 values: NULL")
                print()
        
        # Afficher les Charges d'exploitation
        if charges:
            print("-" * 80)
            print("📉 CHARGES D'EXPLOITATION")
            print("-" * 80)
            for mapping in charges:
                print(f"\n  Catégorie: {mapping.category_name}")
                print(f"  ID: {mapping.id}")
                print(f"  Created at: {mapping.created_at}")
                print(f"  Updated at: {mapping.updated_at}")
                if mapping.level_1_values:
                    try:
                        values = json.loads(mapping.level_1_values)
                        if isinstance(values, list) and len(values) > 0:
                            print(f"  Level 1 values ({len(values)}):")
                            for val in values:
                                print(f"    - {val}")
                        else:
                            print(f"  Level 1 values: [] (vide)")
                    except json.JSONDecodeError as e:
                        print(f"  ⚠️  Erreur de parsing JSON: {e}")
                        print(f"  Level 1 values (raw): {mapping.level_1_values}")
                else:
                    print(f"  Level 1 values: NULL")
                print()
        
        # Afficher les catégories spéciales
        if speciales:
            print("-" * 80)
            print("⚙️  CATÉGORIES SPÉCIALES (Données calculées)")
            print("-" * 80)
            for mapping in speciales:
                print(f"\n  Catégorie: {mapping.category_name}")
                print(f"  ID: {mapping.id}")
                print(f"  Created at: {mapping.created_at}")
                print(f"  Updated at: {mapping.updated_at}")
                print(f"  ⚠️  Note: Cette catégorie ne devrait pas avoir de mapping level_1")
                if mapping.level_1_values:
                    print(f"  ⚠️  Level 1 values (non attendu): {mapping.level_1_values}")
                else:
                    print(f"  Level 1 values: NULL (correct)")
                print()
        
        # Afficher les catégories prédéfinies qui n'ont PAS de mapping en BDD
        all_categories_in_db = {m.category_name for m in mappings}
        missing_categories = []
        
        for cat in PRODUITS_CATEGORIES + CHARGES_CATEGORIES + SPECIAL_CATEGORIES:
            if cat not in all_categories_in_db:
                missing_categories.append(cat)
        
        if missing_categories:
            print("-" * 80)
            print("⚠️  CATÉGORIES PRÉDÉFINIES SANS MAPPING EN BDD")
            print("-" * 80)
            print("  (Ces catégories sont affichées dans le frontend mais n'ont pas encore de mapping)")
            print()
            for cat in missing_categories:
                cat_type = "Produits" if cat in PRODUITS_CATEGORIES else "Charges" if cat in CHARGES_CATEGORIES else "Spéciale"
                is_special = cat in SPECIAL_CATEGORIES
                print(f"  - {cat} ({cat_type})")
                if is_special:
                    print(f"    ⚠️  Catégorie spéciale - Les données sont calculées automatiquement")
                    print(f"    ✅ Pas de mapping nécessaire (normal)")
                else:
                    print(f"    ⚠️  Pas encore de mapping créé")
                print()
        
        print("=" * 80)
        print(f"\n📊 RÉSUMÉ:")
        print(f"  - Produits d'exploitation: {len(produits)} mapping(s)")
        print(f"  - Charges d'exploitation: {len(charges)} mapping(s)")
        print(f"  - Catégories spéciales: {len(speciales)} mapping(s)")
        print(f"  - Total mappings en BDD: {len(mappings)} mapping(s)")
        if missing_categories:
            print(f"  - Catégories sans mapping: {len(missing_categories)} catégorie(s)")
        
    except Exception as e:
        print(f"❌ Erreur lors de la lecture de la table: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
