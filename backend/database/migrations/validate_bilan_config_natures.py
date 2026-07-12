"""
Validation Étape 2 Task 8 (Part B) : invariant « config non vide → ≥1 nature ».

Contexte (point latent Important des tâches 5 & 6). Le calcul des lignes
NORMALES du bilan (bilan_service.calculate_bilan) et des produits/charges du
compte de résultat filtrent désormais par nature de groupe :

    natures = _natures_from_level_3_values(config.level_3_values)

Ancien code : un `level_3_values` NON VIDE dont AUCUN label ne se traduit en
nature filtrait `level_3 IN (labels intraduisibles)` → 0 ligne → montant 0
(ligne PRÉSENTE à 0). Nouveau code : `natures` vide → le bloc de calcul est
SAUTÉ (bilan) ou renvoie {} (CR) → ligne ABSENTE. Divergence structurelle
latente « absent vs 0 », uniquement possible sur une config éditée à la main
dont tous les labels seraient intraduisibles.

Une config VIDE (`[]`) ne diverge pas : le garde `if not level_3_values`
court-circuite en amont, comme avant.

Cette validation PROUVE l'invariant sur les données réelles : toute config NON
VIDE (bilan_config ET compte_resultat_config) contient au moins un label
traduisible en nature (Actif/Passif/Produits/Charges Déductibles/Emprunt). Si
c'est vrai partout, la divergence est structurellement impossible en production
et la suppression des colonnes mortes (Task 8) est sûre. Si UNE config échoue,
STOP : divergence réelle, ne pas dropper.

Usage:
    python3 backend/database/migrations/validate_bilan_config_natures.py
Sortie : code 0 si tout est valide, 2 si au moins une config non vide échoue.
"""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from sqlalchemy.orm import sessionmaker

from backend.database.connection import engine
from backend.database.models import BilanConfig, CompteResultatConfig
from backend.api.services.category_service import NATURE_BY_LABEL


def _parse_labels(raw):
    """Parse le JSON level_3_values en liste de labels ([] si vide/illisible)."""
    try:
        value = json.loads(raw) if raw else []
    except (json.JSONDecodeError, TypeError):
        return []
    return value if isinstance(value, list) else []


def _translatable(labels):
    """Sous-ensemble des labels traduisibles en nature de groupe."""
    return [label for label in labels if label in NATURE_BY_LABEL]


def validate(db):
    """Valide toutes les configs. Retourne (ok: bool, report: list[dict])."""
    report = []
    ok = True

    checks = (
        ("bilan_config", db.query(BilanConfig).all()),
        ("compte_resultat_config", db.query(CompteResultatConfig).all()),
    )
    for table, rows in checks:
        for row in rows:
            labels = _parse_labels(row.level_3_values)
            translatable = _translatable(labels)
            if not labels:
                status = "VIDE (court-circuit, pas de divergence)"
            elif translatable:
                status = f"OK ({len(translatable)} nature(s): {translatable})"
            else:
                status = f"ÉCHEC (aucun label traduisible: {labels})"
                ok = False
            report.append({
                "table": table,
                "property_id": row.property_id,
                "labels": labels,
                "status": status,
                "failed": bool(labels) and not translatable,
            })
    return ok, report


def main() -> int:
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    try:
        ok, report = validate(db)
    finally:
        db.close()

    print("=" * 70)
    print("VALIDATION INVARIANT « config non vide → ≥1 nature » (Task 8 Part B)")
    print("=" * 70)
    for entry in report:
        marker = "❌" if entry["failed"] else "✅"
        print(f"{marker} {entry['table']} property_id={entry['property_id']}: {entry['status']}")

    if ok:
        print("\n✅ Invariant vérifié : toutes les configs non vides ont ≥1 nature "
              "traduisible. La divergence latente « absent vs 0 » est structurellement "
              "impossible sur données réelles. Drop autorisé.")
        return 0

    print("\n❌ STOP : au moins une config non vide n'a aucun label traduisible en "
          "nature — divergence réelle. NE PAS dropper enriched_transactions.",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
