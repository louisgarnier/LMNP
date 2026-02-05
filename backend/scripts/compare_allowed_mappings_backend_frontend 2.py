"""
Script pour comparer les mappings autorisés en backend (DB) et frontend (API).
"""

import sys
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import get_db
from backend.database.models import Property, AllowedMapping

def check_backend():
    """Vérifier les mappings autorisés en backend (base de données)."""
    db = next(get_db())
    
    print("="*80)
    print("📊 BACKEND (BASE DE DONNÉES)")
    print("="*80 + "\n")
    
    properties = db.query(Property).order_by(Property.id).all()
    
    backend_stats = {}
    for prop in properties:
        mappings = db.query(AllowedMapping).filter(
            AllowedMapping.property_id == prop.id
        ).all()
        
        hardcoded = [m for m in mappings if m.is_hardcoded]
        manual = [m for m in mappings if not m.is_hardcoded]
        
        backend_stats[prop.id] = {
            'name': prop.name,
            'total': len(mappings),
            'hardcoded': len(hardcoded),
            'manual': len(manual)
        }
        
        print(f"🏠 {prop.name} (ID: {prop.id})")
        print(f"   Total: {len(mappings)}")
        print(f"   - Hardcodés: {len(hardcoded)}")
        print(f"   - Manuels: {len(manual)}")
        print()
    
    return backend_stats

def check_frontend(api_base_url="http://localhost:8000", properties_list=None):
    """Vérifier les mappings autorisés en frontend (via API)."""
    print("="*80)
    print("🌐 FRONTEND (API)")
    print("="*80 + "\n")
    
    if properties_list is None:
        print("❌ Aucune liste de propriétés fournie")
        return None
    
    frontend_stats = {}
    
    for prop in properties_list:
        property_id = prop.id
        property_name = prop.name
        
        try:
            # Récupérer les mappings autorisés pour cette propriété
            response = requests.get(
                f"{api_base_url}/api/mappings/allowed",
                params={
                    'property_id': property_id,
                    'skip': 0,
                    'limit': 1000  # Récupérer tous les mappings
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                mappings = data.get('mappings', [])
                total = data.get('total', 0)
                
                hardcoded = [m for m in mappings if m.get('is_hardcoded', False)]
                manual = [m for m in mappings if not m.get('is_hardcoded', False)]
                
                frontend_stats[property_id] = {
                    'name': property_name,
                    'total': total,
                    'hardcoded': len(hardcoded),
                    'manual': len(manual),
                    'api_count': len(mappings)  # Nombre réellement retourné par l'API
                }
                
                print(f"🏠 {property_name} (ID: {property_id})")
                print(f"   Total (API): {total}")
                print(f"   - Retournés par l'API: {len(mappings)}")
                print(f"   - Hardcodés: {len(hardcoded)}")
                print(f"   - Manuels: {len(manual)}")
                print()
            else:
                print(f"🏠 {property_name} (ID: {property_id})")
                print(f"   ❌ Erreur API: {response.status_code} - {response.text}")
                print()
                frontend_stats[property_id] = {
                    'name': property_name,
                    'error': f"HTTP {response.status_code}"
                }
                
        except requests.exceptions.RequestException as e:
            print(f"🏠 {property_name} (ID: {property_id})")
            print(f"   ❌ Erreur de connexion: {e}")
            print()
            frontend_stats[property_id] = {
                'name': property_name,
                'error': str(e)
            }
    
    return frontend_stats

def compare_stats(backend_stats, frontend_stats):
    """Comparer les statistiques backend et frontend."""
    print("="*80)
    print("🔍 COMPARAISON BACKEND vs FRONTEND")
    print("="*80 + "\n")
    
    if frontend_stats is None:
        print("⚠️  Impossible de comparer: l'API n'est pas accessible")
        return
    
    all_property_ids = set(backend_stats.keys()) | set(k for k in frontend_stats.keys() if k is not None)
    
    print("📊 RÉSUMÉ PAR PROPRIÉTÉ:")
    print("-" * 80)
    print(f"{'Propriété':<25} {'Backend':<15} {'Frontend':<15} {'Hardcodés':<12} {'Manuels':<10} {'Statut'}")
    print("-" * 80)
    
    for prop_id in sorted([p for p in all_property_ids if p is not None]):
        backend = backend_stats.get(prop_id)
        frontend = frontend_stats.get(prop_id)
        
        if backend and frontend:
            name = backend['name']
            backend_total = backend['total']
            frontend_total = frontend.get('total', 0)
            frontend_api_count = frontend.get('api_count', 0)
            hardcoded = backend['hardcoded']
            manual = backend['manual']
            
            status = "✅ OK" if backend_total == frontend_total == frontend_api_count else "⚠️  Diff"
            
            print(f"{name:<25} {backend_total:<15} {frontend_total:<15} {hardcoded:<12} {manual:<10} {status}")
            
            if backend_total != frontend_total or backend_total != frontend_api_count:
                print(f"   ⚠️  Détails: Backend={backend_total}, Frontend total={frontend_total}, Frontend retournés={frontend_api_count}")
        elif backend:
            name = backend['name']
            backend_total = backend['total']
            hardcoded = backend['hardcoded']
            manual = backend['manual']
            print(f"{name:<25} {backend_total:<15} {'N/A':<15} {hardcoded:<12} {manual:<10} ❌ API")
        elif frontend:
            name = frontend.get('name', f'Property {prop_id}')
            frontend_total = frontend.get('total', 'N/A')
            print(f"{name:<25} {'N/A':<15} {frontend_total:<15} {'N/A':<12} {'N/A':<10} ❌ DB")
    
    print("-" * 80)
    print()
    
    # Détails par propriété
    print("📋 DÉTAILS PAR PROPRIÉTÉ:")
    print("="*80 + "\n")
    
    for prop_id in sorted([p for p in all_property_ids if p is not None]):
        backend = backend_stats.get(prop_id)
        frontend = frontend_stats.get(prop_id)
        
        if backend and frontend:
            name = backend['name']
            backend_total = backend['total']
            frontend_total = frontend.get('total', 0)
            frontend_api_count = frontend.get('api_count', 0)
            
            print(f"🏠 {name} (ID: {prop_id})")
            print(f"   📊 Backend (Base de données):")
            print(f"      - Total mappings autorisés: {backend_total}")
            print(f"      - Hardcodés (protégés): {backend['hardcoded']}")
            print(f"      - Manuels (ajoutés): {backend['manual']}")
            print(f"   🌐 Frontend (API):")
            print(f"      - Total (API): {frontend_total}")
            print(f"      - Retournés par l'API: {frontend_api_count}")
            print(f"      - Hardcodés: {frontend.get('hardcoded', 0)}")
            print(f"      - Manuels: {frontend.get('manual', 0)}")
            
            if backend_total == frontend_total == frontend_api_count:
                print(f"   ✅ Correspondance parfaite")
            elif backend_total == frontend_total:
                print(f"   ⚠️  Total correspond mais seulement {frontend_api_count} retournés (pagination?)")
            else:
                print(f"   ❌ DIFFÉRENCE: Backend={backend_total}, Frontend={frontend_total}")
            
            print()
        elif backend:
            print(f"🏠 {backend['name']} (ID: {prop_id})")
            print(f"   📊 Backend (Base de données):")
            print(f"      - Total mappings autorisés: {backend['total']}")
            print(f"      - Hardcodés (protégés): {backend['hardcoded']}")
            print(f"      - Manuels (ajoutés): {backend['manual']}")
            print(f"   🌐 Frontend: ❌ Non accessible")
            print()
        elif frontend:
            print(f"🏠 {frontend.get('name', f'Property {prop_id}')} (ID: {prop_id})")
            print(f"   📊 Backend: ❌ Non trouvé")
            print(f"   🌐 Frontend (API): {frontend.get('total', 'N/A')} mappings")
            print()

def main():
    """Fonction principale."""
    print("\n" + "="*80)
    print("🔍 COMPARAISON MAPPINGS AUTORISÉS: BACKEND vs FRONTEND")
    print("="*80 + "\n")
    
    # Récupérer la liste des propriétés depuis la DB
    db = next(get_db())
    properties = db.query(Property).order_by(Property.id).all()
    
    # Vérifier le backend
    backend_stats = check_backend()
    
    # Vérifier le frontend (via API)
    frontend_stats = check_frontend(properties_list=properties)
    
    # Comparer
    compare_stats(backend_stats, frontend_stats)
    
    print("="*80)
    print("✅ Analyse terminée")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
