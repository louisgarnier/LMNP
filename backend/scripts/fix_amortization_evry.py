"""
Script de remise à plat des amortissements Evry (property_id=25).

Contexte (Tâche 5, Bloc A) : les `amortization_types` d'Evry étaient une
COPIE défectueuse du gabarit Marseille — les NOMS de composant (qui servent
de `category` dans `amortization_results`, cf. amortization_service.py) ne
correspondaient plus à la valeur `level_1` réellement mappée. Exemples de
l'état AVANT (property_id=25) :
    - "Immobilisation agencements" -> level_1 ["Immeuble (hors terrain)"]  (dur 30)
    - "Immobilisation mobilier"    -> level_1 ["Travaux ... gros œuvre"]   (dur 10)
    - "Immobilisation Facade/Toiture" -> level_1 ["Mobilier & électro..."] (dur 10)
    - "Immobilisation IGT"         -> level_1 ["Terrain (non amortissable)"] (dur 0)
    - 3 types "orphelins" (level_1_values == []) qui ne matchent rien.
Les DURÉES étaient déjà correctes ; seuls les NOMS étaient incohérents, plus
la présence de types orphelins. Ce script recrée un jeu de 4 types propres,
un par catégorie `level_1` réellement utilisée par Evry, avec :
    - le NOM = la valeur level_1 (auto-descriptif, aligné sur le gabarit
      Marseille où name == level_1),
    - la DURÉE issue du tableau d'immobilisations (voir constantes),
    - la part terrain en duration=0 (non amortissable).

VÉRITÉ DOCUMENTAIRE — source : docs/files/appartements/Evry/Immobilisations_Evry.pdf
(« Liste des immobilisations », 2GANRLMNP - Ent. GARNIER LOUIS, page 1,
généré le 03/04/2025). Composants extraits :

  Compte 21100000 TERRAINS
    06 TERRAINS EVRY (165000*0.3)   base 49 500,00  durée 0 an  (mode N, non amort.)  30/11/2021
  Compte 21300000 CONSTRUCTIONS
    07 CONSTRUCTION EVRY (165000*0.7) base 115 500,00 durée 30 ans (mode L, 3,33%)   30/11/2021
  Compte 21810000 INSTALLATIONS, AGENCEMENTS, AMÉNAGEMENTS (tous 10 ans, mode L)
    01 TRAVAUX (MASTEOS)            base 16 905,57  durée 10 ans  28/03/2022
    02 TRAVAUX (MASTEOS)            base 51 594,05  durée 10 ans  28/02/2022
    03 LAVE LINGE (DARTY)           base    758,98  durée 10 ans  19/10/2022
    04 TRAVAUX FERMETURE TERRASSE   base  2 475,88  durée 10 ans  14/01/2022
    05 SERRURE (A&D PLOMBERIE)      base    957,00  durée 10 ans  20/06/2022
  Total base : 237 691,48 €  (= somme des 9 transactions Immobilisations Evry en base).
  Base amortissable (hors terrain) : 188 191,48 €.
  Annuité pleine totale : 3 850,00 (construction) + 72 691,48/10 (compte 21810000)
                        = 3 850,00 + 7 269,148 = 11 119,148 €/an.

Croisement liasse 2024 (Cerfa 2033-A, docs/files/liasse_fiscale_2024_louisgarnier_06_05_2025.pdf) :
immobilisations brutes 358 445 et amortissements cumulés 35 753 sont les 3
apparts CONSOLIDÉS (Evry + Marseille + Marseille colloc), donc pas
directement rapprochables ligne à ligne avec Evry seul — cohérent : Evry brut
237 691,48 est bien < 358 445.

⚠️ Le modèle mappe un `AmortizationType` à N transactions via (level_2, level_1).
Les catégories « travaux » et « mobilier » couvrent chacune PLUSIEURS
transactions à des dates différentes. On laisse donc `start_date=None` : le
service (recalculate_transaction_amortization) retombe alors sur la date de
CHAQUE transaction, qui égale la date d'acquisition documentaire du composant
correspondant (vérifié transaction par transaction). Un `start_date` de type
unique ne pourrait pas représenter ces catégories multi-dates.

Conséquence attendue : les DURÉES/DATES/MONTANTS ne changent pas (ils étaient
déjà corrects) — seuls les LIBELLÉS de catégorie des `amortization_results`
sont réalignés sur les composants documentaires, et les types orphelins sont
supprimés. Les lignes « Charges d'amortissements » (CR) et « Amortissements
cumulés » (bilan) restent donc numériquement identiques (déjà conformes au
document) ; c'est un ré-étiquetage + nettoyage, pas un changement de chiffres.

⚠️ Ce script MODIFIE la base de production (backend/database/lmnp.db).
Toujours faire un backup AVANT exécution :
    cp backend/database/lmnp.db "backups/lmnp_$(date +%F_%H%M)_avant-fix-amortissements.db"

Usage:
    python3 backend/scripts/fix_amortization_evry.py          # demande confirmation
    python3 backend/scripts/fix_amortization_evry.py --yes    # sans confirmation
"""

import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database.connection import SessionLocal
from backend.database.models import (
    AmortizationType,
    AmortizationResult,
    Transaction,
)
from backend.api.services.amortization_service import recalculate_all_amortizations

EVRY_PROPERTY_ID = 25
LEVEL_2_IMMOBILISATIONS = "Immobilisations"

# Jeu de types cible d'Evry — un par catégorie level_1 réellement utilisée.
# Chaque durée est justifiée par docs/files/appartements/Evry/Immobilisations_Evry.pdf (page 1).
# name == level_1 (auto-descriptif). start_date=None -> date de chaque transaction.
EVRY_AMORTIZATION_TYPES = [
    {
        # Compte 21100000 TERRAINS, ligne 06 — mode N, 0 an => non amortissable.
        "name": "Terrain (non amortissable)",
        "level_1": "Terrain (non amortissable)",
        "duration": 0.0,
    },
    {
        # Compte 21300000 CONSTRUCTIONS, ligne 07 — mode L, 30 ans.
        "name": "Immeuble (hors terrain)",
        "level_1": "Immeuble (hors terrain)",
        "duration": 30.0,
    },
    {
        # Compte 21810000, lignes 01/02/04 (TRAVAUX MASTEOS + FERMETURE TERRASSE) — mode L, 10 ans.
        "name": "Travaux de rénovation, gros œuvre",
        "level_1": "Travaux de rénovation, gros œuvre",
        "duration": 10.0,
    },
    {
        # Compte 21810000, lignes 03/05 (LAVE LINGE, SERRURE) + mobilier — mode L, 10 ans.
        "name": "Mobilier & électroménager",
        "level_1": "Mobilier & électroménager",
        "duration": 10.0,
    },
]


def snapshot_types(db):
    """Retourne l'état courant des amortization_types d'Evry (pour rapport)."""
    types = db.query(AmortizationType).filter(
        AmortizationType.property_id == EVRY_PROPERTY_ID
    ).order_by(AmortizationType.id).all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "level_1_values": t.level_1_values,
            "duration": t.duration,
        }
        for t in types
    ]


def count_evry_results(db):
    """Nombre d'amortization_results rattachés à une transaction d'Evry."""
    return (
        db.query(AmortizationResult)
        .join(Transaction, Transaction.id == AmortizationResult.transaction_id)
        .filter(Transaction.property_id == EVRY_PROPERTY_ID)
        .count()
    )


def delete_stale_results(db):
    """Supprime les amortization_results périmés/orphelins d'Evry :

    1. TOUS les résultats rattachés à une transaction d'Evry (ils seront
       régénérés proprement par le recalcul, avec les bons libellés).
    2. Les résultats dont la transaction n'existe plus (orphelins) — non
       rattachables à une propriété, mais nettoyage sûr et attendu par le
       plan (« ceux dont la transaction n'existe plus »).

    Retourne (nb_evry_supprimés, nb_orphelins_supprimés).
    """
    evry_transaction_ids = [
        row[0]
        for row in db.query(Transaction.id)
        .filter(Transaction.property_id == EVRY_PROPERTY_ID)
        .all()
    ]

    evry_deleted = 0
    if evry_transaction_ids:
        evry_deleted = (
            db.query(AmortizationResult)
            .filter(AmortizationResult.transaction_id.in_(evry_transaction_ids))
            .delete(synchronize_session=False)
        )

    # Orphelins : transaction_id ne correspondant à aucune transaction existante.
    existing_ids = {row[0] for row in db.query(Transaction.id).all()}
    orphan_ids = [
        r.id
        for r in db.query(AmortizationResult).all()
        if r.transaction_id not in existing_ids
    ]
    orphan_deleted = 0
    if orphan_ids:
        orphan_deleted = (
            db.query(AmortizationResult)
            .filter(AmortizationResult.id.in_(orphan_ids))
            .delete(synchronize_session=False)
        )

    return evry_deleted, orphan_deleted


def rebuild_types(db):
    """Supprime les amortization_types d'Evry et recrée le jeu cible propre.

    Retourne le nombre de types créés.
    """
    db.query(AmortizationType).filter(
        AmortizationType.property_id == EVRY_PROPERTY_ID
    ).delete(synchronize_session=False)

    created = 0
    for spec in EVRY_AMORTIZATION_TYPES:
        db.add(
            AmortizationType(
                property_id=EVRY_PROPERTY_ID,
                name=spec["name"],
                level_2_value=LEVEL_2_IMMOBILISATIONS,
                level_1_values=json.dumps([spec["level_1"]], ensure_ascii=False),
                start_date=None,
                duration=spec["duration"],
                annual_amount=None,
            )
        )
        created += 1
    return created


def print_types(label, types):
    print(f"\n📊 amortization_types Evry ({label}) — {len(types)} type(s):")
    for t in types:
        print(
            f"   - id={t['id']} name={t['name']!r} "
            f"level_1={t['level_1_values']} duration={t['duration']}"
        )


def main() -> int:
    db = SessionLocal()
    try:
        before_types = snapshot_types(db)
        before_results = count_evry_results(db)
        print_types("AVANT", before_types)
        print(f"\n📈 amortization_results Evry (AVANT): {before_results}")

        if '--yes' not in sys.argv:
            print(
                "\n⚠️  Ce script va RECRÉER les amortization_types d'Evry et "
                "RÉGÉNÉRER ses amortization_results."
            )
            response = input("Continuer ? (oui/non): ")
            if response.lower() not in ('oui', 'o', 'yes', 'y'):
                print("❌ Opération annulée")
                return 1
        else:
            print("\n⚠️  Exécution (--yes activé)")

        evry_deleted, orphan_deleted = delete_stale_results(db)
        print(
            f"\n🗄️  Résultats supprimés : {evry_deleted} (Evry) "
            f"+ {orphan_deleted} (orphelins)"
        )

        created = rebuild_types(db)
        print(f"🗄️  Types recréés : {created}")

        db.flush()
        total_created = recalculate_all_amortizations(db, EVRY_PROPERTY_ID)
        db.commit()
        print(f"✅ Recalcul terminé : {total_created} amortization_results créés pour Evry.")

        after_types = snapshot_types(db)
        after_results = count_evry_results(db)
        print_types("APRÈS", after_types)
        print(f"\n📈 amortization_results Evry (APRÈS): {after_results}")

        return 0

    except Exception:
        db.rollback()
        # Pas d'avalage silencieux : on relance pour exposer la trace complète.
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("REMISE À PLAT DES AMORTISSEMENTS EVRY (property_id=25)")
    print("=" * 60)
    sys.exit(main())
