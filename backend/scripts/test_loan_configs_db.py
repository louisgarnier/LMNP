"""
Script de test pour vérifier les configurations de crédit en base de données.

Usage: python3 backend/scripts/test_loan_configs_db.py
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database import init_database, SessionLocal, engine
from backend.database.models import LoanConfig
from sqlalchemy import inspect, text

def print_section(title):
    """Affiche une section."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_table_structure():
    """Vérifie la structure de la table loan_configs."""
    print_section("1. Structure de la table loan_configs")
    
    inspector = inspect(engine)
    
    # Vérifier que la table existe
    tables = inspector.get_table_names()
    if 'loan_configs' not in tables:
        print("❌ Table 'loan_configs' n'existe pas !")
        return False
    
    print("✅ Table 'loan_configs' existe")
    
    # Afficher les colonnes
    columns = inspector.get_columns('loan_configs')
    print(f"\n📋 Colonnes ({len(columns)}):")
    for col in columns:
        nullable = "NULL" if col['nullable'] else "NOT NULL"
        default = f" DEFAULT {col['default']}" if col['default'] else ""
        print(f"   - {col['name']}: {col['type']} {nullable}{default}")
    
    # Afficher les index
    indexes = inspector.get_indexes('loan_configs')
    if indexes:
        print(f"\n📑 Index ({len(indexes)}):")
        for idx in indexes:
            unique = "UNIQUE" if idx['unique'] else ""
            print(f"   - {idx['name']}: {idx['column_names']} {unique}")
    
    return True

def test_count_configs():
    """Compte le nombre de configurations."""
    print_section("2. Nombre de configurations")
    
    db = SessionLocal()
    try:
        count = db.query(LoanConfig).count()
        print(f"📊 Total de configurations: {count}")
        return count
    finally:
        db.close()

def test_list_all_configs():
    """Liste toutes les configurations."""
    print_section("3. Liste de toutes les configurations")
    
    db = SessionLocal()
    try:
        configs = db.query(LoanConfig).order_by(LoanConfig.name).all()
        
        if not configs:
            print("⚠️  Aucune configuration trouvée")
            return []
        
        print(f"📋 {len(configs)} configuration(s) trouvée(s):\n")
        
        for i, config in enumerate(configs, 1):
            print(f"   Configuration #{i} (ID: {config.id}):")
            print(f"      Nom: {config.name}")
            print(f"      Crédit accordé: {config.credit_amount:,.2f} €")
            print(f"      Taux fixe: {config.interest_rate} %")
            print(f"      Durée: {config.duration_years} ans")
            print(f"      Décalage initial: {config.initial_deferral_months} mois")
            print(f"      Créé le: {config.created_at}")
            print(f"      Modifié le: {config.updated_at}")
            print()
        
        return configs
    finally:
        db.close()

def test_detailed_config(config_id: int):
    """Affiche les détails d'une configuration spécifique."""
    print_section(f"4. Détails de la configuration ID {config_id}")
    
    db = SessionLocal()
    try:
        config = db.query(LoanConfig).filter(LoanConfig.id == config_id).first()
        
        if not config:
            print(f"❌ Configuration ID {config_id} non trouvée")
            return None
        
        print(f"   ID: {config.id}")
        print(f"   Nom: {config.name}")
        print(f"   Crédit accordé: {config.credit_amount:,.2f} €")
        print(f"   Taux fixe: {config.interest_rate} %")
        print(f"   Durée: {config.duration_years} ans")
        print(f"   Décalage initial: {config.initial_deferral_months} mois")
        print(f"   Créé le: {config.created_at}")
        print(f"   Modifié le: {config.updated_at}")
        
        # Calculs dérivés
        print(f"\n   Calculs dérivés:")
        monthly_rate = config.interest_rate / 100 / 12
        total_months = config.duration_years * 12
        if monthly_rate > 0:
            monthly_payment = config.credit_amount * (monthly_rate * (1 + monthly_rate)**total_months) / ((1 + monthly_rate)**total_months - 1)
            total_paid = monthly_payment * total_months
            total_interest = total_paid - config.credit_amount
            print(f"      Mensualité estimée: {monthly_payment:,.2f} €")
            print(f"      Total remboursé: {total_paid:,.2f} €")
            print(f"      Total intérêts: {total_interest:,.2f} €")
        else:
            print(f"      (Taux à 0%, calculs non applicables)")
        
        return config
    finally:
        db.close()

def test_raw_sql():
    """Exécute une requête SQL brute pour vérifier les données."""
    print_section("5. Requête SQL brute")
    
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT * FROM loan_configs ORDER BY name"))
        rows = result.fetchall()
        
        if not rows:
            print("⚠️  Aucune ligne trouvée")
            return
        
        print(f"📋 {len(rows)} ligne(s) trouvée(s):\n")
        
        # Afficher les colonnes
        columns = result.keys()
        print("   Colonnes:", ", ".join(columns))
        print()
        
        # Afficher les données
        for row in rows:
            print(f"   ID {row.id}: {row.name}")
            print(f"      credit_amount={row.credit_amount}, interest_rate={row.interest_rate}")
            print(f"      duration_years={row.duration_years}, initial_deferral_months={row.initial_deferral_months}")
            print()
    finally:
        db.close()

def test_unique_constraint():
    """Teste la contrainte unique sur le nom."""
    print_section("6. Test contrainte unique (nom)")
    
    db = SessionLocal()
    try:
        # Compter les noms en double
        result = db.execute(text("""
            SELECT name, COUNT(*) as count 
            FROM loan_configs 
            GROUP BY name 
            HAVING COUNT(*) > 1
        """))
        duplicates = result.fetchall()
        
        if duplicates:
            print("⚠️  Noms en double détectés:")
            for dup in duplicates:
                print(f"   - '{dup.name}': {dup.count} occurrence(s)")
        else:
            print("✅ Tous les noms sont uniques")
        
        # Afficher tous les noms
        result = db.execute(text("SELECT DISTINCT name FROM loan_configs ORDER BY name"))
        names = [row[0] for row in result.fetchall()]
        print(f"\n📋 Noms uniques ({len(names)}):")
        for name in names:
            print(f"   - {name}")
    finally:
        db.close()

def main():
    """Exécute tous les tests."""
    print("=" * 60)
    print("  TEST DES CONFIGURATIONS DE CRÉDIT EN BASE DE DONNÉES")
    print("=" * 60)
    
    # Initialiser la base de données
    init_database()
    
    # Tests
    if not test_table_structure():
        print("\n❌ La table n'existe pas, arrêt des tests")
        return
    
    count = test_count_configs()
    
    if count > 0:
        configs = test_list_all_configs()
        
        # Afficher les détails de la première configuration
        if configs:
            test_detailed_config(configs[0].id)
        
        test_unique_constraint()
    else:
        print("\n⚠️  Aucune configuration en base de données")
        print("   Créez des configurations via l'interface web ou l'API")
    
    test_raw_sql()
    
    print("\n" + "=" * 60)
    print("  ✅ TESTS TERMINÉS")
    print("=" * 60)

if __name__ == "__main__":
    main()
