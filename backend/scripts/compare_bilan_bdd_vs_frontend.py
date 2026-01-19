"""
Script pour comparer les données BACKEND (Base de données) vs FRONTEND (Affiché dans l'app) pour le Bilan.

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
import json
from pathlib import Path
from datetime import date

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal
from backend.database.models import Transaction, BilanMapping, BilanConfig
from backend.api.services.bilan_service import (
    get_mappings,
    get_level_3_values,
    calculate_bilan
)
from fastapi.testclient import TestClient
from backend.api.main import app


def get_years_to_display(db):
    """Récupère les années à afficher (comme le fait le frontend)."""
    first_transaction = db.query(Transaction).order_by(Transaction.date.asc()).first()
    current_year = date.today().year
    start_year = 2020
    
    if first_transaction and first_transaction.date:
        start_year = first_transaction.date.year
    
    years = []
    for year in range(start_year, current_year + 1):
        years.append(year)
    
    return years


def format_amount(amount: float) -> str:
    """Formate un montant en €."""
    if amount is None:
        return '-'
    return f"{amount:,.2f} €".replace(',', ' ').replace('.', ',')


def compare_bilan_bdd_vs_frontend():
    """Compare les données du bilan entre BDD et Frontend."""
    print("=" * 100)
    print("📊 COMPARAISON BILAN : BACKEND (BDD) vs FRONTEND (API)")
    print("=" * 100)
    
    db = SessionLocal()
    client = TestClient(app)
    
    try:
        # 1. Récupérer les années à afficher
        years = get_years_to_display(db)
        print(f"\n📅 Années à afficher: {years}\n")
        
        # 2. Récupérer les mappings et la config
        mappings = get_mappings(db)
        config = db.query(BilanConfig).first()
        
        if not config:
            print("⚠️  Aucune configuration trouvée")
            return
        
        level_3_values = get_level_3_values(db)
        print(f"🔧 Level 3 values sélectionnés: {level_3_values}\n")
        print(f"📋 Mappings configurés: {len(mappings)}\n")
        
        # 3. Pour chaque année, comparer backend vs frontend
        for year in years:
            print("=" * 100)
            print(f"📆 ANNÉE {year}")
            print("=" * 100)
            
            # BACKEND : Calculer directement depuis la BDD
            print("\n🔵 BACKEND (Base de données):")
            print("-" * 100)
            
            backend_result = calculate_bilan(db, year, mappings, level_3_values)
            backend_categories = backend_result["categories"]
            
            # Afficher les catégories par Type et Sous-catégorie
            for mapping in mappings:
                category_name = mapping.category_name
                amount = backend_categories.get(category_name, 0.0)
                is_special = mapping.is_special
                
                print(f"  {mapping.type:6} | {mapping.sub_category:25} | {category_name:50} | {format_amount(amount):>15} {'(SPÉCIAL)' if is_special else ''}")
            
            print(f"\n  TOTAL ACTIF (backend)  : {format_amount(backend_result['actif_total'])}")
            print(f"  TOTAL PASSIF (backend) : {format_amount(backend_result['passif_total'])}")
            print(f"  Différence (backend)   : {format_amount(backend_result['difference'])} ({backend_result['difference_percent']:.2f}%)")
            
            # FRONTEND : Récupérer via l'API
            print("\n🟢 FRONTEND (API):")
            print("-" * 100)
            
            try:
                response = client.post(
                    "/api/bilan/calculate",
                    json={
                        "year": year,
                        "selected_level_3_values": level_3_values
                    }
                )
                
                if response.status_code != 200:
                    print(f"  ❌ Erreur API: {response.status_code} - {response.text}")
                    continue
                
                frontend_data = response.json()
                
                # Parcourir la structure hiérarchique du frontend
                for type_item in frontend_data.get("types", []):
                    type_name = type_item.get("type", "")
                    print(f"\n  📊 {type_name}:")
                    
                    for sub_category_item in type_item.get("sub_categories", []):
                        sub_category_name = sub_category_item.get("sub_category", "")
                        sub_category_total = sub_category_item.get("total", 0.0)
                        print(f"    └─ {sub_category_name:25} | Total: {format_amount(sub_category_total):>15}")
                        
                        for category_item in sub_category_item.get("categories", []):
                            category_name = category_item.get("category_name", "")
                            amount = category_item.get("amount", 0.0)
                            print(f"        └─ {category_name:50} | {format_amount(amount):>15}")
                
                print(f"\n  TOTAL ACTIF (frontend)  : {format_amount(frontend_data.get('actif_total', 0))}")
                print(f"  TOTAL PASSIF (frontend) : {format_amount(frontend_data.get('passif_total', 0))}")
                print(f"  Différence (frontend)   : {format_amount(frontend_data.get('difference', 0))} ({frontend_data.get('difference_percent', 0):.2f}%)")
                
                # COMPARAISON
                print("\n🔍 COMPARAISON:")
                print("-" * 100)
                
                # Comparer les catégories
                differences_found = False
                for mapping in mappings:
                    category_name = mapping.category_name
                    backend_amount = backend_categories.get(category_name, 0.0)
                    
                    # Trouver le montant dans la réponse frontend
                    frontend_amount = None
                    for type_item in frontend_data.get("types", []):
                        for sub_category_item in type_item.get("sub_categories", []):
                            for category_item in sub_category_item.get("categories", []):
                                if category_item.get("category_name") == category_name:
                                    frontend_amount = category_item.get("amount", 0.0)
                                    break
                            if frontend_amount is not None:
                                break
                        if frontend_amount is not None:
                            break
                    
                    if frontend_amount is None:
                        frontend_amount = 0.0
                    
                    # Comparer avec une tolérance de 0.01€
                    if abs(backend_amount - frontend_amount) > 0.01:
                        differences_found = True
                        diff = frontend_amount - backend_amount
                        print(f"  ⚠️  {category_name:50} | Backend: {format_amount(backend_amount):>15} | Frontend: {format_amount(frontend_amount):>15} | Diff: {format_amount(diff):>15}")
                
                # Comparer les totaux
                backend_actif = backend_result['actif_total']
                frontend_actif = frontend_data.get('actif_total', 0)
                backend_passif = backend_result['passif_total']
                frontend_passif = frontend_data.get('passif_total', 0)
                
                if abs(backend_actif - frontend_actif) > 0.01:
                    differences_found = True
                    print(f"  ⚠️  TOTAL ACTIF  | Backend: {format_amount(backend_actif):>15} | Frontend: {format_amount(frontend_actif):>15} | Diff: {format_amount(frontend_actif - backend_actif):>15}")
                
                if abs(backend_passif - frontend_passif) > 0.01:
                    differences_found = True
                    print(f"  ⚠️  TOTAL PASSIF | Backend: {format_amount(backend_passif):>15} | Frontend: {format_amount(frontend_passif):>15} | Diff: {format_amount(frontend_passif - backend_passif):>15}")
                
                if not differences_found:
                    print("  ✅ Aucune différence trouvée - Backend et Frontend sont identiques")
                
            except Exception as e:
                print(f"  ❌ Erreur lors de l'appel API: {e}")
                import traceback
                traceback.print_exc()
            
            print("\n")
        
        print("=" * 100)
        print("✅ Comparaison terminée")
        print("=" * 100)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    compare_bilan_bdd_vs_frontend()
