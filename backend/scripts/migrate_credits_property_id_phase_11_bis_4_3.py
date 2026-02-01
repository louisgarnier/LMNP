"""
Migration des données Crédit existantes - Ajout de property_id

Ce script migre les configurations de crédit et mensualités existantes 
pour leur assigner un property_id.

⚠️ IMPORTANT : Ce script doit être exécuté une seule fois après la migration de la base de données.

Actions:
1. Vérifier les configurations sans property_id
2. Vérifier les mensualités sans property_id
3. Assigner un property_id par défaut aux données orphelines
4. Valider la migration

⚠️ Before running, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import sys
import os
from datetime import datetime

# Ajouter le chemin du projet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Configuration de la base de données - chemin absolu (même que backend/database/connection.py)
DB_FILE = Path(__file__).parent.parent / "database" / "lmnp.db"
DATABASE_URL = f"sqlite:///{DB_FILE}"

# Import des modèles après avoir défini le chemin
from backend.database.models import LoanConfig, LoanPayment, Property

def print_section(title: str):
    """Affiche une section avec un titre."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def print_success(message: str):
    """Affiche un message de succès."""
    print(f"✅ {message}")

def print_error(message: str):
    """Affiche un message d'erreur."""
    print(f"❌ ERREUR: {message}")

def print_info(message: str):
    """Affiche un message d'information."""
    print(f"ℹ️  {message}")

def print_warning(message: str):
    """Affiche un message d'avertissement."""
    print(f"⚠️  {message}")

def main():
    """Fonction principale de migration."""
    print_section("MIGRATION DES DONNÉES CRÉDIT - Phase 11")
    
    # Connexion à la base de données
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Étape 1: Récupérer la propriété par défaut
        print_section("ÉTAPE 1: Récupération de la propriété par défaut")
        
        properties = session.query(Property).all()
        if not properties:
            print_error("Aucune propriété trouvée dans la base de données.")
            print_info("Veuillez créer au moins une propriété avant de lancer la migration.")
            return 1
        
        # Utiliser la première propriété comme défaut
        default_property = properties[0]
        print_success(f"Propriété par défaut: ID={default_property.id}, Name={default_property.name}")
        print_info(f"Toutes les données orphelines seront assignées à cette propriété.")
        
        # Afficher toutes les propriétés disponibles
        print("\nPropriétés disponibles:")
        for prop in properties:
            print(f"   - ID={prop.id}, Name={prop.name}")
        print()
        
        # Étape 2: Vérifier les configurations de crédit
        print_section("ÉTAPE 2: Vérification des configurations de crédit (LoanConfig)")
        
        # Vérifier si la colonne property_id existe
        try:
            # Compter les configurations sans property_id
            result = session.execute(text(
                "SELECT COUNT(*) FROM loan_configs WHERE property_id IS NULL"
            )).fetchone()
            configs_without_property = result[0] if result else 0
            
            # Compter le total
            total_configs = session.query(LoanConfig).count()
            
            print_info(f"Total de configurations: {total_configs}")
            print_info(f"Configurations sans property_id: {configs_without_property}")
            
            if configs_without_property > 0:
                print_warning(f"{configs_without_property} configuration(s) à migrer")
                
                # Afficher les configurations à migrer
                orphan_configs = session.execute(text(
                    "SELECT id, name, credit_amount FROM loan_configs WHERE property_id IS NULL"
                )).fetchall()
                
                for config in orphan_configs:
                    print(f"   - ID={config[0]}, Name={config[1]}, Montant={config[2]} €")
                
                # Assigner la propriété par défaut
                session.execute(text(
                    f"UPDATE loan_configs SET property_id = :prop_id WHERE property_id IS NULL"
                ), {"prop_id": default_property.id})
                session.commit()
                
                print_success(f"{configs_without_property} configuration(s) migrée(s) vers property_id={default_property.id}")
            else:
                print_success("Toutes les configurations ont déjà un property_id")
                
        except Exception as e:
            print_warning(f"Impossible de vérifier property_id sur loan_configs: {e}")
            print_info("La colonne property_id n'existe peut-être pas encore. Exécutez d'abord les migrations.")
        
        # Étape 3: Vérifier les mensualités
        print_section("ÉTAPE 3: Vérification des mensualités (LoanPayment)")
        
        try:
            # Compter les mensualités sans property_id
            result = session.execute(text(
                "SELECT COUNT(*) FROM loan_payments WHERE property_id IS NULL"
            )).fetchone()
            payments_without_property = result[0] if result else 0
            
            # Compter le total
            total_payments = session.query(LoanPayment).count()
            
            print_info(f"Total de mensualités: {total_payments}")
            print_info(f"Mensualités sans property_id: {payments_without_property}")
            
            if payments_without_property > 0:
                print_warning(f"{payments_without_property} mensualité(s) à migrer")
                
                # Assigner la propriété par défaut
                session.execute(text(
                    f"UPDATE loan_payments SET property_id = :prop_id WHERE property_id IS NULL"
                ), {"prop_id": default_property.id})
                session.commit()
                
                print_success(f"{payments_without_property} mensualité(s) migrée(s) vers property_id={default_property.id}")
            else:
                print_success("Toutes les mensualités ont déjà un property_id")
                
        except Exception as e:
            print_warning(f"Impossible de vérifier property_id sur loan_payments: {e}")
            print_info("La colonne property_id n'existe peut-être pas encore. Exécutez d'abord les migrations.")
        
        # Étape 4: Validation
        print_section("ÉTAPE 4: Validation de la migration")
        
        # Vérifier qu'il n'y a plus de données orphelines
        try:
            orphan_configs = session.execute(text(
                "SELECT COUNT(*) FROM loan_configs WHERE property_id IS NULL"
            )).fetchone()[0]
            
            orphan_payments = session.execute(text(
                "SELECT COUNT(*) FROM loan_payments WHERE property_id IS NULL"
            )).fetchone()[0]
            
            if orphan_configs == 0 and orphan_payments == 0:
                print_success("Migration validée: aucune donnée orpheline")
            else:
                print_error(f"Données orphelines restantes: {orphan_configs} configs, {orphan_payments} payments")
                return 1
                
        except Exception as e:
            print_warning(f"Impossible de valider: {e}")
        
        # Afficher le résumé par propriété
        print_section("RÉSUMÉ PAR PROPRIÉTÉ")
        
        for prop in properties:
            configs_count = session.query(LoanConfig).filter(LoanConfig.property_id == prop.id).count()
            payments_count = session.query(LoanPayment).filter(LoanPayment.property_id == prop.id).count()
            
            print(f"📊 {prop.name} (ID={prop.id}):")
            print(f"   - Configurations de crédit: {configs_count}")
            print(f"   - Mensualités: {payments_count}")
            print()
        
        print_section("MIGRATION TERMINÉE")
        print_success("La migration des données Crédit est terminée avec succès!")
        
        return 0
        
    except Exception as e:
        print_error(f"Erreur lors de la migration: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return 1
        
    finally:
        session.close()

if __name__ == "__main__":
    exit(main())
