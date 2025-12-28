#!/usr/bin/env python3
"""
Script pour réinitialiser toutes les données des tables d'amortissement.

⚠️ ATTENTION : Ce script supprime TOUTES les données des tables :
- amortization_types
- amortization_results
- amortizations (ancienne table)
- amortization_config (ancienne table)

Usage:
    python backend/scripts/reset_amortization_data.py
"""

import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database import SessionLocal
from backend.database.models import AmortizationType, AmortizationResult, Amortization, AmortizationConfig

def reset_amortization_data():
    """Réinitialise toutes les données des tables d'amortissement."""
    db = SessionLocal()
    
    print("🔄 Réinitialisation des données d'amortissement...")
    print("=" * 60)
    
    try:
        # 1. Supprimer tous les résultats d'amortissement
        deleted_results = db.query(AmortizationResult).delete()
        print(f"✅ Supprimé {deleted_results} résultat(s) d'amortissement")
        
        # 2. Supprimer tous les types d'amortissement
        deleted_types = db.query(AmortizationType).delete()
        print(f"✅ Supprimé {deleted_types} type(s) d'amortissement")
        
        # 3. Supprimer toutes les données de l'ancienne table amortizations (si elle existe)
        try:
            deleted_old = db.query(Amortization).delete()
            print(f"✅ Supprimé {deleted_old} entrée(s) de l'ancienne table amortizations")
        except Exception as e:
            print(f"ℹ️  Table amortizations n'existe pas ou est vide: {e}")
        
        # 4. Supprimer toutes les données de l'ancienne table amortization_config (si elle existe)
        try:
            deleted_config = db.query(AmortizationConfig).delete()
            print(f"✅ Supprimé {deleted_config} entrée(s) de l'ancienne table amortization_config")
        except Exception as e:
            print(f"ℹ️  Table amortization_config n'existe pas ou est vide: {e}")
        
        db.commit()
        
        print("=" * 60)
        print("✅ Réinitialisation terminée avec succès !")
        print("\nToutes les données d'amortissement ont été supprimées.")
        print("Vous pouvez maintenant recharger la page Amortissements.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors de la réinitialisation: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    try:
        reset_amortization_data()
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

