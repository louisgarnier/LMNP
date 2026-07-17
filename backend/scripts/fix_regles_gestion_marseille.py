"""
Remplace les règles-annuaire des virements de gestion Marseille (property_id=15)
par des règles qui généralisent, et reclasse les 6 transactions perdues.

Contexte (2026-07-17) : depuis la bascule vers la synchro Enable Banking, 6
transactions Marseille ne sont classées nulle part — donc invisibles au compte
de résultat ET au bilan (elles déséquilibrent ce dernier de -3 167,36 €) :

    2026-02-16    -8,00  F COMM INTERVENTION 1 OPER
    2026-03-08  -525,59  VIR INST GESTION FEVRIER 26 - LG
    2026-03-08  -692,39  VIR INST VIREMENT JANVIER 26 - LG
    2026-04-15  -629,10  VIR INST VIREMENT GESTION - MARS LG
    2026-05-08  -691,65  VIR INST AVRIL 2026 - LOUIS G
    2026-06-29  -620,63  VIR INST VIREMENT GESTION - LG MAI

Soit 5 mois consécutifs de frais de gestion. Les mêmes virements, à l'époque du
CSV, étaient bien classés en « Frais de gestion locative » (catégorie 49).

--- CAUSE RACINE : la garde des 70 % ---------------------------------------

`classification_engine.py:22-23` rejette tout motif faisant moins de 70 % de la
longueur du libellé quand `strict_ratio` est vrai. Écrire « GESTION » pour
attraper « VIR INST GESTION FEVRIER 26 - LG » donne un ratio de 0,22 → refusé.
Le moteur interdit donc mécaniquement les motifs courts, ce qui pousse à écrire
le libellé complet (référence bancaire unique comprise) — d'où l'annuaire :
272 des 370 règles (74 %) ne matchent qu'une seule transaction.

Le contre-exemple existe déjà en base : la règle 209 « VIR STRIPE » (prefix,
strict_ratio=0, property 25) matche 24 transactions pour 10 776,88 €. C'est le
patron suivi ici : motif court + strict_ratio=False.

--- PRIORITÉ : le conflit d'égalité ----------------------------------------

`classification_engine.py:58-62` : si plusieurs règles de même longueur ET même
priorité matchent, le moteur renvoie None (transaction NON classée) plutôt que
de trancher. « GESTION » et « LOUIS G » font 7 caractères chacun : un libellé
futur contenant les deux (« VIR INST GESTION JUIN 26 - LOUIS G ») déclencherait
ce conflit. D'où priority=10 sur GESTION, qui tranche.

--- PIÈGES ÉCARTÉS PAR LE TEST ---------------------------------------------

- « VIR INST » (prefix) capturerait « VIR INST MR VICTOR BRIAND » (+1 000 €,
  catégorie 18 Compte courant d'associé) → un apport reclassé en charge.
- « LG » (contains) capturerait des encaissements Airbnb (cat 14) et AMEUBLEA
  (cat 29) via leurs références internes (…LGQQJ…). D'où « - LG ».

Vérification : 6 transactions résolues, 0 régression sur les 296 transactions
du bien (contrôlé par le script lui-même avant/après).

Usage (idempotent) :
    python3 backend/scripts/fix_regles_gestion_marseille.py [--dry-run]
"""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend.database.connection import SessionLocal  # noqa: E402
from backend.database.models import ClassificationRule, Transaction  # noqa: E402
from backend.api.services.classification_engine import find_matching_rule  # noqa: E402

MARSEILLE = 15
CAT_GESTION = 49  # Frais de gestion locative
CAT_BANCAIRE = 34  # Frais bancaires (choix de Louis dans l'inbox le 17/07/2026,
                   # et catégorie utilisée par la colloc de référence)

# (pattern, match_type, priority, category_id)
REGLES = [
    ("GESTION", "contains", 10, CAT_GESTION),
    ("LOUIS G", "contains", 0, CAT_GESTION),
    ("- LG", "contains", 0, CAT_GESTION),
    ("F COMM", "prefix", 0, CAT_BANCAIRE),
]


def snapshot(db):
    """{tx_id: category_id} pour tout le bien — sert de contrôle de régression."""
    return {
        t.id: t.category_id
        for t in db.query(Transaction)
        .filter(Transaction.property_id == MARSEILLE, Transaction.is_split_parent == False)  # noqa: E712
        .all()
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    db = SessionLocal()
    try:
        avant = snapshot(db)
        non_classees_avant = [i for i, c in avant.items() if c is None]
        print(f"🚀 [FixReglesGestion] {len(avant)} transactions Marseille, "
              f"{len(non_classees_avant)} non classées")

        print("\n1) Création des règles qui généralisent")
        for pattern, mtype, prio, cat in REGLES:
            existe = (
                db.query(ClassificationRule)
                .filter(
                    ClassificationRule.property_id == MARSEILLE,
                    ClassificationRule.pattern == pattern,
                    ClassificationRule.match_type == mtype,
                )
                .one_or_none()
            )
            if existe is not None:
                print(f"  ⏭️  « {pattern} » existe déjà (id {existe.id})")
                continue
            r = ClassificationRule(
                pattern=pattern,
                match_type=mtype,
                category_id=cat,
                property_id=MARSEILLE,
                priority=prio,
                source="manual",
                strict_ratio=False,  # ⚠️ obligatoire : sinon la garde des 70 % rejette
            )
            print(f"  ➕ « {pattern} » ({mtype}, prio {prio}) -> catégorie {cat}")
            if not args.dry_run:
                db.add(r)
        if not args.dry_run:
            db.flush()

        print("\n2) Reclassement des transactions non classées")
        regles = (
            db.query(ClassificationRule)
            .filter(ClassificationRule.property_id.in_([MARSEILLE, None]))
            .all()
        )
        touchees = 0
        for tid in non_classees_avant:
            t = db.query(Transaction).get(tid)
            regle = find_matching_rule(t.nom, regles)
            if regle is None:
                print(f"  ❌ TOUJOURS non classée: {t.date} {t.quantite:+.2f} « {t.nom[:44]} »")
                continue
            print(f"  ✅ {t.date} {t.quantite:+.2f} « {t.nom[:44]} »")
            print(f"         -> catégorie {regle.category_id} via « {regle.pattern} »")
            if not args.dry_run:
                t.category_id = regle.category_id
            touchees += 1

        print("\n3) Contrôle de régression (aucun classement existant ne doit changer)")
        if not args.dry_run:
            db.flush()
        apres = snapshot(db)
        regressions = [
            (i, avant[i], apres[i])
            for i in avant
            if avant[i] is not None and avant[i] != apres.get(i)
        ]
        if regressions:
            print(f"  ❌ {len(regressions)} RÉGRESSION(S) — annulation totale:")
            for i, a, b in regressions[:10]:
                print(f"     tx {i}: catégorie {a} -> {b}")
            db.rollback()
            raise SystemExit(1)
        print(f"  ✅ 0 régression sur {len(avant)} transactions")

        restantes = [i for i, c in apres.items() if c is None]
        print(f"\n{'⏭️  --dry-run : rollback' if args.dry_run else '✅ [FixReglesGestion] terminé'} — "
              f"{touchees} transaction(s) reclassée(s), {len(restantes)} non classée(s) restante(s)")
        if args.dry_run:
            db.rollback()
        else:
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
