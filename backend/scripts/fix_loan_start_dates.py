"""
Script de correction de `loan_configs.loan_start_date`.

Contexte (Tâche 4, bug bilan Evry) : `calculate_capital_restant_du`
(backend/api/services/bilan_service.py) a été corrigé pour ne plus filtrer
les crédits "actifs" sur `loan_start_date`, mais sur la présence d'au moins
un `LoanPayment` réel (voir ce module). Cela rend `loan_start_date` non
plus utilisé pour ce calcul — mais la colonne reste affichée/utilisée
ailleurs (ex: pages crédits) et doit refléter la réalité de l'échéancier
pour ne pas induire en erreur.

Ce script recale `loan_start_date` de CHAQUE `LoanConfig` sur
`MIN(LoanPayment.date)` parmi les paiements portant le même `loan_name`
(`LoanPayment.loan_name == LoanConfig.name`) et le même `property_id`.

Cas particuliers :
- Un `LoanConfig` sans aucun `LoanPayment` correspondant est laissé
  INCHANGÉ (rien à recaler) — signalé dans le rapport.
- Un `LoanConfig` dont `loan_start_date` est déjà égale à
  `MIN(LoanPayment.date)` est laissé inchangé (pas de mise à jour inutile).

⚠️ Ce script MODIFIE la base de production (backend/database/lmnp.db).
Toujours faire un backup AVANT exécution (cf. Tâche 4, Step 1) :
    cp backend/database/lmnp.db "backups/lmnp_$(date +%F_%H%M)_avant-fix-pret.db"

Usage:
    python3 backend/scripts/fix_loan_start_dates.py          # demande confirmation
    python3 backend/scripts/fix_loan_start_dates.py --yes    # sans confirmation
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import func

from backend.database.connection import SessionLocal
from backend.database.models import LoanConfig, LoanPayment, Property


def compute_planned_updates(db):
    """Calcule, pour chaque LoanConfig, la loan_start_date corrigée
    (MIN(LoanPayment.date) du même loan_name/property_id).

    Retourne une liste de dicts décrivant chaque LoanConfig avec son état
    actuel et sa valeur cible, sans rien modifier en base.
    """
    loan_configs = db.query(LoanConfig).all()
    planned = []

    for loan_config in loan_configs:
        min_date = db.query(func.min(LoanPayment.date)).filter(
            LoanPayment.property_id == loan_config.property_id,
            LoanPayment.loan_name == loan_config.name,
        ).scalar()

        property_obj = db.query(Property).filter(
            Property.id == loan_config.property_id
        ).first()
        property_name = property_obj.name if property_obj else f"property_id={loan_config.property_id}"

        planned.append({
            "loan_config_id": loan_config.id,
            "property_name": property_name,
            "loan_name": loan_config.name,
            "current_loan_start_date": loan_config.loan_start_date,
            "target_loan_start_date": min_date,
        })

    return planned


def apply_updates(db, planned):
    """Applique les mises à jour calculées par `compute_planned_updates`.

    Ne touche que les LoanConfig dont la loan_start_date cible existe
    (au moins un LoanPayment trouvé) ET diffère de la valeur actuelle.
    Retourne le nombre de lignes effectivement mises à jour.
    """
    updated_count = 0

    for entry in planned:
        target = entry["target_loan_start_date"]
        current = entry["current_loan_start_date"]

        if target is None:
            # Aucun LoanPayment pour ce LoanConfig : rien à recaler.
            continue
        if target == current:
            # Déjà correct : pas de mise à jour inutile.
            continue

        loan_config = db.query(LoanConfig).filter(
            LoanConfig.id == entry["loan_config_id"]
        ).first()
        loan_config.loan_start_date = target
        updated_count += 1

    db.commit()
    return updated_count


def print_report(planned, applied: bool):
    print("\n📊 État des loan_configs (avant" + (" / après" if applied else "") + " correction):")
    for entry in planned:
        target = entry["target_loan_start_date"]
        current = entry["current_loan_start_date"]
        if target is None:
            status = "⚠️  aucun LoanPayment trouvé -> inchangé"
        elif target == current:
            status = "✅ déjà correcte -> inchangé"
        else:
            status = f"🔧 {current} → {target}"
        print(
            f"   - LoanConfig id={entry['loan_config_id']} "
            f"property={entry['property_name']!r} loan_name={entry['loan_name']!r}: {status}"
        )


def main() -> int:
    db = SessionLocal()

    try:
        planned = compute_planned_updates(db)

        if not planned:
            print("✅ Aucun loan_config en base. Rien à faire.")
            return 0

        print_report(planned, applied=False)

        to_update = [p for p in planned if p["target_loan_start_date"] is not None
                     and p["target_loan_start_date"] != p["current_loan_start_date"]]

        if not to_update:
            print("\n✅ Toutes les loan_start_date sont déjà alignées sur l'échéancier réel.")
            return 0

        if '--yes' not in sys.argv:
            print(f"\n⚠️  {len(to_update)} loan_config(s) vont être mis à jour (voir détail ci-dessus).")
            response = input("Continuer ? (oui/non): ")
            if response.lower() not in ('oui', 'o', 'yes', 'y'):
                print("❌ Opération annulée")
                return 1
        else:
            print(f"\n⚠️  Mise à jour de {len(to_update)} loan_config(s) (--yes activé)")

        updated_count = apply_updates(db, planned)

        print(f"\n✅ Mise à jour réussie : {updated_count} loan_config(s) mis à jour.")

        # Rapport après correction : relire depuis la base pour confirmer.
        planned_after = compute_planned_updates(db)
        print_report(planned_after, applied=True)

        return 0

    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("CORRECTION DE loan_configs.loan_start_date")
    print("=" * 60)
    sys.exit(main())
