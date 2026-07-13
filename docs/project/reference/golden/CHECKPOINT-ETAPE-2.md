# Checkpoint Étape 2 — Référentiel par IDs, centimes, golden inchangé

**Date** : 2026-07-12
**Branche** : `refonte`
**Statut** : Étape 2 fonctionnellement complète (Tasks 1-9 committées), clôturée par cette tâche (Task 10).

Ce document répond aux questions de Louis pour l'étape 2 : qu'est-ce qui a
changé (structurellement, pas dans les chiffres), la preuve que les chiffres
sont inchangés, ce qui a été supprimé, la déviation de spec à trancher, et ce
qui reste comme dette pour l'étape 3.

---

## 1. Ce que l'étape 2 a changé (structure, pas chiffres)

L'étape 2 est une refonte **structurelle** de la classification et du stockage,
à **sortie financière strictement inchangée**. Trois axes (détail dans
`docs/workflow/ADR.md`, ADR-004 à ADR-007) :

1. **Référentiel global** `category_groups` (19) / `categories` (56), seedé de
   façon idempotente → **identité stable par ID**. Ajout de
   `transactions.category_id` (FK nullable indexée), backfill 880/880 (0
   mismatch), double-écriture transitoire, bascule de **toutes** les lectures
   et écritures sur `category_id`, puis **suppression de `enriched_transactions`**.
   La classification n'est plus portée QUE par `transactions.category_id`
   (ADR-004).

2. **Configs CR/Bilan liées par `category_id`** (55 lignes CR, 35 lignes bilan)
   + **`line_code` stables** pour les lignes calculées, **libellés français
   résolus au bord** (« label at the edge ») — le cœur du calcul travaille sur
   IDs/natures, seule la sérialisation API parle français (ADR-005).

3. **Montants en centimes entiers** via le `TypeDecorator` `EuroCents`
   (`backend/database/money.py`) — **11 colonnes sur 12** (ADR-006).

---

## 2. PREUVE : les chiffres sont inchangés (golden v3 → v4 = 0 écart)

Le golden master fige un instantané au centime de tous les états (CR, bilan,
amortissements) pour les 3 propriétés (Evry=25, mars=15, mars colloc=26).

- **AVANT étape 2** : `v3-apres-amortissements` (fin Bloc A).
- **APRÈS étape 2** : `v4-etape2-referentiel` (cette tâche).

```
python3 backend/scripts/golden_master.py --compare --tag v3-apres-amortissements
→ [golden_master] Aucune différence détectée. OK.
python3 backend/scripts/golden_master.py --extract  --tag v4-etape2-referentiel
→ 17 combinaison(s) propriété × année extraite(s).
```

Vérification indépendante : `golden-v3-apres-amortissements.json` ==
`golden-v4-etape2-referentiel.json` (**égalité stricte** des dicts sur les 17
combos ; seule différence de sérialisation = zéro signé `-0.0` vs `0.0` sur des
champs `difference` déjà nuls → valeur identique). Détail dans
`ECARTS.md` (section v3 → v4).

**L'étape 2 ne change aucun chiffre** — référentiel + IDs + centimes à output
identique.

---

## 3. Tables supprimées

| Table(s) | Quand | Nature |
|---|---|---|
| 8 tables orphelines | Task 1 | tables mortes (comptages conformes), aucune lecture/écriture vivante |
| `enriched_transactions` | Task 8 | classification migrée vers `transactions.category_id` (+ classe ORM et colonnes mortes `level_1_values`×2, `special_source` du modèle supprimées) |

Absence vérifiée dans `sqlite_master` après drop ; hash prod inchangé ; golden
0 écart à chaque étape.

---

## 4. ⚠️ DÉVIATION SPEC à trancher par Louis

**`amortization_results.amount` est laissé en `Float`** (11/12 colonnes en
centimes entiers, **pas 12/12**).

- Raison : ses valeurs sont des **dotations dérivées sous le centime**
  (ex. `-643,7569`). Les arrondir au centime ferait **dériver les
  amortissements cumulés jusqu'à 0,06 €** → **casserait le golden master**
  (contrat au centime).
- Décision prise : le contrat golden au centime **prime** sur la règle « toutes
  les colonnes en entier ». Documenté à la colonne, dans la migration et le
  rapport de Task 9, validé par le reviewer.
- **À confirmer par Louis** : accepter cette exception (recommandé), ou décider
  d'un traitement centimes des amortissements qui impliquerait de **rebaser le
  golden** (accepter un écart jusqu'à 0,06 € sur les cumuls).

---

## 5. Dette / poids mort restant pour l'étape 3

Rien de tout ceci n'est mort-vivant dangereux — c'est de la dette identifiée,
**hors périmètre étape 2**, à traiter en étape 3 :

- **Moteur de classification par règles encore vivant** : les tables
  `mappings`, `allowed_mappings`, `mapping_imports` (toutes trois EXISTENT
  encore en base) et le moteur de règles qui les exploite restent en place
  **jusqu'à l'étape 3**. L'étape 2 a basculé le STOCKAGE de la classification
  (résultat = `category_id`) mais pas encore le moteur qui la PRODUIT.
- **Colonnes libellés physiquement présentes mais NON lues** : les anciennes
  colonnes de sélection par libellé subsistent sur disque alors que le code lit
  désormais par `category_id` + `line_code` :
  - `bilan_mappings.level_1_values`, `bilan_mappings.special_source`
  - `compte_resultat_mappings.level_1_values`
  - `compte_resultat_config.level_3_values`, `bilan_config.level_3_values`
  (à supprimer physiquement en étape 3 une fois le moteur migré).
- **Valeurs parasites migrées telles quelles** dans les configs de la propriété
  25 (Evry), dans ces colonnes libellés désormais inertes :
  - `bilan_config[25].level_3_values` contient `"TEST_L3_VALUE"`
  - `compte_resultat_config[25].level_3_values` contient `"Emprunt"`
  Migrées **as-is** (pas de nettoyage de données en étape 2, pour ne pas
  risquer un écart golden) — sans effet puisque ces colonnes ne sont plus lues.
  À purger avec les colonnes ci-dessus.

---

## 6. État des tests (Task 10)

- **Backend** (`python3 -m pytest backend/tests/`) : **58 passed, 0 failed, 0
  error, 0 skipped.** Les fichiers en quarantaine (tests hérités touchant la
  base de PROD, scripts « manuels » serveur local) sont **ignorés à la
  collecte** (`pytest_ignore_collect`) — ils n'apparaissent plus comme
  « skipped ». Voir ADR-003/ADR-007.
- **Nouveau garde moteur-prod** (Task 10, Part B) : `test_prod_db_guard.py`
  (2 tests) prouve qu'ouvrir une connexion sur le moteur de PRODUCTION lève une
  `RuntimeError` tant que `LMNP_ALLOW_PROD_DB_TESTS != "1"` — défense en
  profondeur après l'incident de contamination Task 5 (voir
  `docs/workflow/ERROR_INVESTIGATION.md`). Les 2 tests golden en lecture seule
  (`test_amortization_evry_golden.py`, `test_realtime_states.py`) passent
  toujours (moteur propre, non affecté).
- **Frontend** (`npx jest`) : **3 suites, 6 tests, 0 failed.**
- **Build** (`npm run build`) : succès.

---

## 7. Minors accumulés qui « ride » vers la revue finale de branche

Findings mineurs relevés en revue de code pendant l'étape 2, **non corrigés**
(hors périmètre de leur tâche), à réévaluer à la revue whole-branch :

- **Seed référentiel** (T2) : `except ValueError → return 2` avant toute
  écriture (UX CLI) ; lookup de groupe par libellé seul (sûr sur les sources
  actuelles).
- **Script dev** (T4) : `generate_test_amortization_results.py` construisait un
  `EnrichedTransaction` direct sans passer par le helper de sync — exclusion
  légitime (table désormais supprimée).
- **Service catégorie** (T5) : branche de désambiguïsation
  `category_service:56-72` non testée (dead code pour les données actuelles) ;
  les libellés non résolus disparaissent de la réponse GET (par design, 0 en
  prod).
- **Configs** (T5/T6) : `GET level_1_values` re-trié/ré-encodé (par design) ;
  branches de signe PASSIF « normale » non testées E2E.
- **Invariant nature-traductibilité** (T6/T8, latent) : calcul des lignes
  normales gardé par `if all_cat_ids and natures:` — une config dont les
  `level_3_values` ne seraient QUE des libellés non-nature donnerait des lignes
  **absentes au lieu de 0**. Validé sur toutes les configs réelles par
  `validate_bilan_config_natures`, documenté aux sites de garde ; à revalider
  si de nouvelles configs sont éditées.
- **Lectures** (T7, non exerçables sur données valides) : `unclassified_only`
  (= `category_id IS NULL`) diverge de l'ancien SI `level_1` set mais
  `level_2/3` invalide (impossible : les mappings portent les 3 niveaux) ;
  `recalculate_all` ne visite plus que `category_id NOT NULL`.
- **Migration centimes** (T9, latent) : mode d'arrondi de la migration
  (`CAST ROUND`, half-away) ≠ décorateur (half-to-even) au cas `x.xx5` exact —
  aucune valeur de prod concernée.

Les points « ouverts pour Louis » du Bloc A (bannière équilibre bilan Evry,
colloc 26 non rapproché xlsx, écart 0,75 € mars colloc 2025, écarts forecast
2026) restent ouverts — voir `CHECKPOINT-BLOC-A.md §3`.
