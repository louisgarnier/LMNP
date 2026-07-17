"""Ajoute la règle de classement des loyers Matera d'Evry et rattrape les
transactions restées non classées.

Contexte : le Crédit Mutuel libelle les virements de loyer 'VIR MATERA' nu (le
détail « LOYER - APPARTEMENT… » vit dans un champ séparé que l'ingestion ne
conserve pas). Les règles historiques embarquent la référence unique du
virement ('VIR MATERA E2EID-23469349') : une référence ne se répète jamais,
donc aucune ne peut matcher le libellé nu. Résultat : 31 loyers non classés.

Le script est idempotent (ne recrée pas la règle si elle existe) et ne touche
QUE les transactions `category_id IS NULL` : les classements manuels existants
ne sont jamais écrasés — contrairement à `enrich_all_transactions`, qui
re-classe tout et remet à NULL ce qu'aucune règle ne rattrape.

Usage : python3 backend/scripts/fix_regle_matera_evry.py [--yes]
"""
import sys

from backend.database.connection import SessionLocal
from backend.database.models import ClassificationRule, Transaction
from backend.api.services.classification_engine import find_matching_rule
from backend.api.services.enrichment_service import _rules_for_property

PROPERTY_ID = 25          # Evry
CATEGORY_LOYERS = 14      # Encaissement locataire et CAF
PATTERN = "VIR MATERA"


def main(apply: bool) -> int:
    db = SessionLocal()
    try:
        existing = (db.query(ClassificationRule)
                    .filter(ClassificationRule.pattern == PATTERN,
                            ClassificationRule.match_type == "exact",
                            ClassificationRule.property_id == PROPERTY_ID)
                    .one_or_none())
        if existing:
            print(f"Règle déjà présente (id={existing.id}) — rien à créer.")
        else:
            # 'exact' et non 'prefix' : le libellé stable est le libellé entier.
            # Un futur 'VIR MATERA REMBOURSEMENT' restera donc à trancher à la
            # main plutôt que d'être classé en loyer à tort.
            rule = ClassificationRule(pattern=PATTERN, match_type="exact",
                                      category_id=CATEGORY_LOYERS,
                                      property_id=PROPERTY_ID, priority=0,
                                      source="manual", strict_ratio=True)
            if not apply:
                print(f"[DRY-RUN] créerait la règle '{PATTERN}' (exact) → catégorie {CATEGORY_LOYERS}")
            else:
                db.add(rule)
                db.commit()
                print(f"Règle créée (id={rule.id}) : '{PATTERN}' (exact) → catégorie {CATEGORY_LOYERS}")

        if not apply:
            db.rollback()
            print("[DRY-RUN] aucun rattrapage effectué. Relancer avec --yes.")
            return 0

        rules = _rules_for_property(db, PROPERTY_ID)
        pending = (db.query(Transaction)
                   .filter(Transaction.property_id == PROPERTY_ID,
                           Transaction.category_id.is_(None))
                   .all())
        rattrapees = 0
        for tx in pending:
            match = find_matching_rule(tx.nom, rules)
            if match:
                tx.category_id = match.category_id
                rattrapees += 1
        db.commit()

        print(f"Non classées avant : {len(pending)} — rattrapées : {rattrapees}")
        restantes = (db.query(Transaction)
                     .filter(Transaction.property_id == PROPERTY_ID,
                             Transaction.category_id.is_(None))
                     .all())
        print(f"Restent non classées : {len(restantes)}")
        for tx in restantes:
            print(f"  {tx.date} {tx.quantite / 100:>10.2f} €  {tx.nom}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main(apply="--yes" in sys.argv))
