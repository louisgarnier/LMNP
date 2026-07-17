#!/usr/bin/env python3
"""
Golden master: fige (extraction) puis vérifie (comparaison) les sorties
financières de l'API pour servir de référence pendant la refonte.

⚠️ Ce script est STRICTEMENT EN LECTURE SEULE : il n'effectue que des
requêtes GET contre l'API (jamais de POST/PUT/DELETE). Il ne modifie
jamais la base de données de production.

Prérequis : le backend doit tourner sur http://localhost:8000
(`python3 -m uvicorn api.main:app --port 8000` depuis backend/).

Usage:
    python3 backend/scripts/golden_master.py --extract --tag v1
    python3 backend/scripts/golden_master.py --compare --tag v1

- `--extract --tag X` : interroge l'API en direct pour chaque propriété x
  année, normalise et arrondit les résultats, et écrit
  docs/project/reference/golden/golden-X.json (clés triées, JSON indenté
  pour des diffs stables).

- `--compare --tag X` : recharge golden-X.json, ré-interroge l'API en
  direct avec la même logique d'extraction, et affiche chaque différence
  sous la forme `chemin: valeur_stockée → valeur_actuelle`. Tolérance de
  0,01 € par valeur numérique. Exit code 1 si au moins un écart au-delà de
  la tolérance est détecté, exit code 0 sinon.

Aucune dépendance externe : uniquement la bibliothèque standard (urllib).
"""

import argparse
import datetime
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE_URL = "http://localhost:8000"
PROPERTIES = [25, 15, 26]  # Evry, mars, mars colloc
YEARS = list(range(2021, 2029))  # 2021..2028 inclus
TOLERANCE = 0.01
REQUEST_TIMEOUT_SECONDS = 30

GOLDEN_DIR = Path(__file__).resolve().parents[2] / "docs" / "project" / "reference" / "golden"


class GoldenMasterError(RuntimeError):
    """Erreur fatale : un appel HTTP a échoué. Le script doit s'arrêter net
    plutôt que de produire un fichier golden partiel ou de masquer l'échec.
    """


def http_get(path: str, params: dict) -> dict:
    """Effectue une requête GET et retourne le JSON décodé.

    Abandonne immédiatement avec un message clair en cas d'échec (pas
    d'exception avalée silencieusement).
    """
    query = urllib.parse.urlencode(params)
    url = f"{BASE_URL}{path}?{query}"
    try:
        with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
            status = resp.status
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        raise GoldenMasterError(
            f"GET {url} a échoué avec HTTP {e.code}: {body}"
        ) from e
    except urllib.error.URLError as e:
        raise GoldenMasterError(
            f"GET {url} a échoué (backend injoignable sur {BASE_URL} ?): {e}"
        ) from e

    if status != 200:
        raise GoldenMasterError(f"GET {url} a retourné HTTP {status}: {body}")

    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        raise GoldenMasterError(f"GET {url} a retourné un JSON invalide: {e}") from e


# Clés candidates identifiant un élément au sein d'une liste de dicts dans
# les payloads bilan/CR (ex: bilan.types[].type == "ACTIF"/"PASSIF",
# bilan.types[].sub_categories[].sub_category, .categories[].category_name).
# Utilisées à la fois pour canoniser l'ordre à l'extraction (ci-dessous) et
# pour apparier les éléments par clé plutôt que par position lors du diff
# (cf. diff_json).
LIST_ITEM_ID_KEYS = ("type", "sub_category", "category_name", "name")


def list_item_id_key(items: list):
    """Retourne la première clé de LIST_ITEM_ID_KEYS présente sur TOUS les
    éléments de `items` (qui doivent être des dicts), ou None si la liste
    n'est pas une liste de dicts identifiables (ex: liste de nombres, ou
    liste de dicts sans clé candidate commune) — dans ce cas on retombe sur
    une comparaison/tri positionnel."""
    if not items or not all(isinstance(item, dict) for item in items):
        return None
    for key in LIST_ITEM_ID_KEYS:
        if all(key in item for item in items):
            return key
    return None


def round_floats(obj):
    """Arrondit récursivement tous les flottants à 2 décimales, trie les
    clés des dictionnaires, et — pour les listes de dicts identifiables via
    LIST_ITEM_ID_KEYS — trie les éléments par leur clé d'identification.
    Objectif : un dump JSON déterministe/order-independent, y compris si
    l'API renvoie un jour les mêmes éléments dans un ordre différent."""
    if isinstance(obj, float):
        return round(obj, 2)
    if isinstance(obj, dict):
        return {k: round_floats(obj[k]) for k in sorted(obj.keys())}
    if isinstance(obj, list):
        items = [round_floats(v) for v in obj]
        key = list_item_id_key(items)
        if key is not None:
            items = sorted(items, key=lambda item: str(item.get(key)))
        return items
    return obj


def is_cr_empty(cr_result: dict) -> bool:
    """Un compte de résultat sans aucun produit ni charge signifie qu'il
    n'y a aucune donnée pour cette combinaison propriété x année (la
    propriété n'existait pas encore / aucune transaction importée)."""
    return cr_result.get("produits") == {} and cr_result.get("charges") == {}


def extract_amort_for_year(amort_aggregated: dict, year: int):
    """Découpe la matrice agrégée (catégories x années, toutes années
    confondues pour la propriété) pour ne garder que l'année demandée.

    Retourne None si l'année n'apparaît pas du tout dans la matrice
    (aucune donnée d'amortissement pour cette année) — à ne PAS remplacer
    par zéro, cf. consigne "absent plutôt que zero-filled".
    """
    years = amort_aggregated.get("years", [])
    if year not in years:
        return None

    idx = years.index(year)
    categories = amort_aggregated.get("categories", [])
    data = amort_aggregated.get("data", [])

    per_category = {}
    for cat_idx, category in enumerate(categories):
        row = data[cat_idx] if cat_idx < len(data) else []
        per_category[category] = row[idx] if idx < len(row) else 0.0

    total_for_year = amort_aggregated.get("totals_by_year", {}).get(str(year))
    if total_for_year is None:
        total_for_year = sum(per_category.values())

    return {"categories": per_category, "total": total_for_year}


def fetch_last_balance(property_id: int, year: int):
    """Dernier solde connu (transaction la plus récente) sur l'année
    donnée. Retourne None si aucune transaction sur cette année.

    RÈGLE DE DÉPARTAGE (déterminisme) : la route /api/transactions ne trie
    que par `date` (aucune clé secondaire côté SQL, cf.
    backend/api/routes/transactions.py), donc quand plusieurs transactions
    partagent la date la plus récente, l'ordre entre elles dépend de
    l'ordre physique des lignes en base — non garanti, et fragile à tout
    refactor (ré-import, VACUUM, etc.). Des combos du golden ont déjà des
    ex-aequo réels (ex: 2 transactions le même jour x2, jusqu'à 3). On
    récupère donc une fenêtre large (limit=20, largement au-dessus des
    ex-aequo observés) triée par date desc, on ne garde que les
    transactions dont la date == date max renvoyée, puis on départage de
    façon déterministe en gardant l'id le plus élevé parmi les ex-aequo
    (id le plus élevé = transaction insérée en dernier) et on retourne son
    solde.
    """
    resp = http_get(
        "/api/transactions",
        {
            "property_id": property_id,
            "start_date": f"{year}-01-01",
            "end_date": f"{year}-12-31",
            "sort_by": "date",
            "sort_direction": "desc",
            "limit": 20,
        },
    )
    transactions = resp.get("transactions", [])
    if not transactions:
        return None
    max_date = transactions[0].get("date")
    tied = [t for t in transactions if t.get("date") == max_date]
    winner = max(tied, key=lambda t: t.get("id"))
    return winner.get("solde")


def extract_property(property_id: int) -> dict:
    """Extrait toutes les données golden master pour une propriété, sur
    l'ensemble de la plage d'années YEARS, en ne conservant que les
    années où il existe réellement des données (cf. is_cr_empty)."""
    years_param = ",".join(str(y) for y in YEARS)

    cr_response = http_get(
        "/api/compte-resultat/calculate",
        {"property_id": property_id, "years": years_param},
    )
    bilan_response = http_get(
        "/api/bilan/calculate",
        {"property_id": property_id, "years": years_param},
    )
    amort_response = http_get(
        "/api/amortization/results/aggregated",
        {"property_id": property_id},
    )

    cr_results = cr_response["results"]
    bilan_results = bilan_response["results"]

    property_data = {}
    for year in YEARS:
        year_key = str(year)
        cr_result = cr_results.get(year_key)
        if cr_result is None or is_cr_empty(cr_result):
            # Absent : ni la propriété ni l'API n'ont de données pour cette
            # année -> on omet complètement la clé (pas de zéro-filling).
            continue

        bilan_result = bilan_results.get(year_key)
        amort_result = extract_amort_for_year(amort_response, year)
        last_balance = fetch_last_balance(property_id, year)

        property_data[year_key] = round_floats(
            {
                "cr": cr_result,
                "bilan": bilan_result,
                "amort": amort_result,
                "last_balance": last_balance,
            }
        )

    return property_data


def extract_fiscal() -> dict:
    """Extrait le bloc fiscal, au niveau ENTITÉ (pas par propriété) : un
    seul appel à /api/fiscal/timeline, dont on ne garde que `results`
    (les années sont déjà les clés de ce dict), normalisé/arrondi comme
    les blocs par propriété (round_floats trie aussi les clés).

    On exclut l'exercice courant (et tout exercice futur) du gel : il est
    encore ouvert, donc son résultat change à chaque nouvelle transaction
    saisie, ce qui ferait déclencher le garde-fou de régression à chaque
    fois sans qu'il y ait de vraie régression. Seuls les exercices clos
    sont figés."""
    response = http_get("/api/fiscal/timeline", {})
    current_year = datetime.date.today().year
    closed_years = {
        year: values
        for year, values in response["results"].items()
        if int(year) < current_year
    }
    return round_floats(closed_years)


def build_dataset() -> dict:
    dataset = {}
    for property_id in PROPERTIES:
        dataset[str(property_id)] = extract_property(property_id)
    dataset["fiscal"] = extract_fiscal()
    return dataset


def diff_json(path: str, stored, current, diffs: list, tolerance: float = TOLERANCE):
    """Compare récursivement deux structures JSON et accumule les écarts
    dans `diffs`, sous forme de chaînes 'chemin: stocké → actuel'.

    - Les nombres sont comparés avec une tolérance de `tolerance` (borne
      stricte ">", donc dépendante du bruit flottant : un écart d'exactement
      1 centime peut, selon les erreurs d'arrondi accumulées de part et
      d'autre, tomber juste en-deça ou juste au-delà de la tolérance).
    - Les clés présentes d'un seul côté sont rapportées comme différences
      (valeur '<absent>' côté manquant).
    - Les listes de dicts identifiables via LIST_ITEM_ID_KEYS (ex: `type`,
      `sub_category`, `category_name`) sont appariées par clé plutôt que
      par position, pour ne pas rapporter de faux positifs si l'API change
      simplement l'ordre de renvoi (ex: ACTIF/PASSIF inversés). Les listes
      sans clé d'identification commune retombent sur une comparaison
      positionnelle (zip par index).
    """
    if isinstance(stored, dict) and isinstance(current, dict):
        all_keys = sorted(set(stored.keys()) | set(current.keys()))
        for key in all_keys:
            new_path = f"{path}.{key}" if path else str(key)
            if key not in stored:
                diffs.append(f"{new_path}: <absent> → {current[key]!r}")
            elif key not in current:
                diffs.append(f"{new_path}: {stored[key]!r} → <absent>")
            else:
                diff_json(new_path, stored[key], current[key], diffs, tolerance)
    elif isinstance(stored, list) and isinstance(current, list):
        id_key = list_item_id_key(stored) or list_item_id_key(current)
        if id_key is not None:
            stored_by_id = {item.get(id_key): item for item in stored if isinstance(item, dict)}
            current_by_id = {item.get(id_key): item for item in current if isinstance(item, dict)}
            all_ids = sorted(set(stored_by_id) | set(current_by_id), key=str)
            for item_id in all_ids:
                item_path = f"{path}[{id_key}={item_id!r}]"
                if item_id not in stored_by_id:
                    diffs.append(f"{item_path}: <absent> → {current_by_id[item_id]!r}")
                elif item_id not in current_by_id:
                    diffs.append(f"{item_path}: {stored_by_id[item_id]!r} → <absent>")
                else:
                    diff_json(item_path, stored_by_id[item_id], current_by_id[item_id], diffs, tolerance)
        elif len(stored) != len(current):
            diffs.append(f"{path}: longueur liste {len(stored)} → {len(current)}")
        else:
            for i, (s_item, c_item) in enumerate(zip(stored, current)):
                diff_json(f"{path}[{i}]", s_item, c_item, diffs, tolerance)
    elif isinstance(stored, (int, float)) and isinstance(current, (int, float)) \
            and not isinstance(stored, bool) and not isinstance(current, bool):
        if abs(float(stored) - float(current)) > tolerance:
            diffs.append(f"{path}: {stored} → {current}")
    else:
        if stored != current:
            diffs.append(f"{path}: {stored!r} → {current!r}")


def cmd_extract(tag: str) -> int:
    print(f"[golden_master] Extraction en cours (tag={tag})...")
    dataset = build_dataset()

    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    out_path = GOLDEN_DIR / f"golden-{tag}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")

    combo_count = sum(len(dataset[str(pid)]) for pid in PROPERTIES)
    print(f"[golden_master] Extraction terminée -> {out_path}")
    print(f"[golden_master] {combo_count} combinaison(s) propriété x année extraite(s).")
    for property_id in PROPERTIES:
        years = dataset[str(property_id)]
        print(f"  - propriété {property_id}: années {sorted(years.keys())}")
    print(f"  - fiscal (entité): années {sorted(dataset['fiscal'].keys())}")
    return 0


def cmd_compare(tag: str) -> int:
    in_path = GOLDEN_DIR / f"golden-{tag}.json"
    if not in_path.exists():
        print(f"[golden_master] ERREUR: fichier golden introuvable: {in_path}", file=sys.stderr)
        return 2

    with open(in_path, "r", encoding="utf-8") as f:
        stored = json.load(f)

    print(f"[golden_master] Comparaison en cours (tag={tag})...")
    current = build_dataset()

    diffs: list = []
    diff_json("", stored, current, diffs)

    if diffs:
        print(f"[golden_master] {len(diffs)} différence(s) détectée(s) (tolérance {TOLERANCE} €):")
        for d in diffs:
            print(f"  {d}")
        return 1

    print(f"[golden_master] Aucune différence détectée (tag={tag}). OK.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--extract", action="store_true", help="Fige les sorties actuelles de l'API dans un fichier golden.")
    mode_group.add_argument("--compare", action="store_true", help="Compare les sorties actuelles de l'API à un fichier golden existant.")
    parser.add_argument("--tag", required=True, help="Étiquette du fichier golden (ex: v1-avant-corrections).")
    args = parser.parse_args()

    try:
        if args.extract:
            return cmd_extract(args.tag)
        return cmd_compare(args.tag)
    except GoldenMasterError as e:
        print(f"[golden_master] ERREUR FATALE: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
