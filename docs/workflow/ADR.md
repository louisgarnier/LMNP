# Architecture Decision Records (ADR)

Format court : Contexte / Décision / Conséquences. Un ADR par décision
structurante, dans l'ordre chronologique (le plus récent en bas).

---

## ADR-001 — Calcul à la lecture (suppression des caches CR/Bilan)

**Date** : 2026-07-10 (Bloc A, Task 7)

**Contexte** : le compte de résultat et le bilan étaient historiquement
persistés dans deux tables de cache (`compte_resultat_data`,
`bilan_data`), peuplées par un endpoint `POST .../generate` et supposées
invalidées à chaque écriture pertinente (transaction, mapping, config
d'amortissement, échéance de prêt...). L'audit de Task 7 a montré que ce
mécanisme était **mort en pratique** :
- `bilan_data` n'avait **aucun writer** dans tout le code (0 ligne en
  base) — le bilan était donc déjà, de fait, recalculé implicitement à
  chaque lecture par un autre chemin.
- `compte_resultat_data` n'était peuplée que par `/generate`, que le
  frontend n'appelait **jamais** (aucune référence à `generate` côté
  client, aucun bouton, aucun appel `GET /compte-resultat` plat).
- Tous les appels d'invalidation passaient de mauvais arguments (ex.
  `invalidate_all_compte_resultat(db)` sans `property_id` obligatoire) →
  `TypeError` systématiquement avalée par un `try/except` loggé.
  L'invalidation ne faisait donc **rien** depuis l'origine du mécanisme.

Résultat : deux tables de cache, un système d'invalidation, et un
endpoint `/generate` existaient dans le code sans jamais produire ni
consommer de données utiles — un risque latent de désynchronisation
(chiffres périmés) sans aucun bénéfice de performance réel.

**Décision** : remplacer les deux caches par un **calcul à la lecture**
pur. `GET /api/compte-resultat` et `GET /api/bilan` appellent directement
`calculate_compte_resultat` / `calculate_bilan` (les mêmes fonctions déjà
utilisées par les routes `/calculate`), aplatissent le résultat en lignes
`(annee, category_name, amount)`, et ne persistent plus rien. Les tables
`CompteResultatData` / `BilanData` (modèles ORM + tables SQL) ont été
supprimées via `backend/scripts/drop_cache_tables.py` (backup automatique
avant DROP). Une **mémoïsation de requête** (portée à un seul appel HTTP,
pas un cache persistant) est conservée pour éviter de recalculer le CR de
chaque année plusieurs fois lors d'un calcul de bilan multi-années
(`cr_cache: Optional[Dict[int, Dict]]` passé en paramètre de
`calculate_bilan`).

**Conséquences** :
- Les chiffres affichés sont **toujours à jour**, par construction (plus
  de risque de cache périmé/désynchronisé) — élimine toute une classe de
  bugs (bug B1 documenté ci-dessous).
- Coût : un calcul à chaque `GET` au lieu d'une lecture de table. Mesuré
  et validé : bilan 6 ans pour Evry (property_id=25, cas le plus
  volumineux du jeu de données réel) = **médiane 53,8 ms** (< budget de
  300 ms fixé par le plan), avec mémoïsation du CR.
- Simplification nette du code : suppression de 2 modèles ORM, de 4
  fonctions d'invalidation par service (CR + Bilan), et de tous leurs
  ~20 call sites dans les routes (transactions, mappings, loan_configs,
  loan_payments, amortization, enrichment).
- Golden master re-comparé après la bascule (`v3-apres-amortissements`) :
  **zéro écart** — la migration ne change aucun chiffre, uniquement le
  chemin de calcul.
- Contrainte pour le futur : toute nouvelle fonctionnalité qui aurait
  besoin de persister un état CR/Bilan (ex. export, historisation figée à
  une date) devra explicitement documenter pourquoi elle réintroduit un
  cache, et comment elle garantit son invalidation — ne pas reproduire le
  pattern mort sans un mécanisme d'invalidation testé.

---

## ADR-002 — Activité d'un prêt déterminée par son échéancier réel (LoanPayment), pas par une date de config

**Date** : 2026-07-10 (Bloc A, Task 4)

**Contexte** : `calculate_capital_restant_du` (bilan, catégorie « Emprunt
bancaire (capital restant dû) ») décidait qu'un prêt était « actif » pour
l'année N à partir de `LoanConfig.loan_start_date`, un champ de
configuration saisi indépendamment de l'échéancier réel des paiements
(`LoanPayment`). Pour le prêt Evry, ce champ valait `2026-05-08` alors que
l'échéancier réel (36+ lignes de `LoanPayment`) démarre en 2021. Résultat
: le capital remboursé n'était jamais déduit pour les années 2022-2025,
gonflant artificiellement le PASSIF et déséquilibrant le bilan (écarts de
-2 814,69 € à -37 201,47 € selon l'année, voir `ECARTS.md` v1→v2).

**Décision** : la fonction ne dépend plus de `LoanConfig.loan_start_date`
pour décider si un prêt est actif — elle vérifie désormais l'existence
d'au moins un `LoanPayment` daté au plus tard le 31/12/N (sous-requête
corrélée `exists()`), indépendamment de la config. La donnée
`loan_start_date` a ensuite été **recalée** sur `MIN(LoanPayment.date)`
pour tous les prêts existants (`backend/scripts/fix_loan_start_dates.py`,
idempotent), pour que la config reflète la réalité observée plutôt que
l'inverse.

**Conséquences** :
- Source de vérité unique et non ambiguë : l'échéancier réel des
  paiements, pas un champ de configuration qui peut diverger silencieusement.
- Bilan Evry rééquilibré pour 2022-2025 (ACTIF = PASSIF, écart ≤ 0,01 €),
  capital restant dû 2025 = 194 613,53 € vérifié contre le tableau
  d'amortissement Excel documentaire.
- Toute future saisie de `LoanConfig` doit accompagner la création
  immédiate de ses `LoanPayment` (ou accepter que le prêt soit considéré
  inactif tant qu'aucun paiement n'est enregistré) — la config seule ne
  suffit plus à activer un prêt dans les calculs.
- Risque résiduel documenté (hors périmètre de cette tâche, non
  introduit par elle) : mars colloc (property 26) a un écart de bilan
  2025 de 0,75 € sans rapport avec ce mécanisme — voir
  `docs/project/reference/golden/ECARTS.md` et le rapport de checkpoint.

---

## ADR-003 — Quarantaine des tests legacy qui touchent la production directement

**Date** : 2026-07-10 (Bloc A, Task 3 puis Task 8)

**Contexte** : la suite `backend/tests/` mélange des tests isolés
(harnais Task 3, fixtures `db_session`/`client` sur SQLite en mémoire) et
~46 fichiers de tests hérités qui touchent la base de PRODUCTION
(`backend/database/lmnp.db`) directement, de deux façons :
1. Import/usage direct de `SessionLocal` ou `next(get_db())` — un
   incident réel s'est produit le 2026-07-10 (Task 4) :
   `test_database_complete.py` a effacé 880 lignes de
   `transactions`/`enriched_transactions` de production en lançant un
   simple `pytest` de vérification. Restauré depuis backup, voir
   `ERROR_INVESTIGATION.md`.
2. Scripts « manuels » hérités qui appellent un serveur en dur sur
   `http://localhost:8000` (documentés eux-mêmes comme devant être
   lancés à la main, pas via pytest), et dont plusieurs fonctions
   `POST`/`PUT`/`DELETE` peuvent écrire dans la même base de production
   via l'API HTTP. Découvert lors de Task 8 (clôture Bloc A) en cherchant
   à obtenir un run `pytest backend/tests/` à zéro échec.

**Décision** : `backend/tests/conftest.py::pytest_collection_modifyitems`
détecte ces deux motifs par analyse statique du code source (regex sur
`SessionLocal`/`next(get_db())` d'une part, sur
`BASE_URL = "http://localhost:8000` d'autre part) et **skip** ces modules
à la collecte, avec un message explicite renvoyant vers
`ERROR_INVESTIGATION.md`. Un run complet de `pytest backend/tests/` est
donc considéré PASS si et seulement si il y a **zéro échec/erreur** —
les skips de cette quarantaine sont **attendus et corrects**, pas un
signe de suite incomplète. Un override existe
(`LMNP_ALLOW_PROD_DB_TESTS=1`) pour les lancer explicitement, à n'utiliser
qu'après un backup frais de `lmnp.db`.

**Conséquences** :
- Un `pytest backend/tests/` normal ne touche **jamais** la base de
  production, éliminant la classe de risque qui a causé l'incident du
  2026-07-10.
- Les tests quarantinés ne sont **pas** corrigés/migrés dans le cadre de
  cette tâche (hors périmètre Bloc A) — ils restent une dette de test
  identifiée, à traiter dans une tâche dédiée de migration vers le
  harnais isolé (Task 3) si leur couverture doit être restaurée.
- Nouvelle règle pour tout futur fichier de test : ne jamais utiliser
  `SessionLocal`/`get_db()` hors des fixtures `db_session`/`client`, et ne
  jamais coder en dur une URL de serveur local dans un test destiné à
  tourner sous `pytest` — sinon il sera automatiquement mis en
  quarantaine (ou pire, laissé actif et dangereux si son motif échappe
  aux deux regex actuelles).

---

## ADR-004 — Référentiel global `category_groups`/`categories` + bascule des lectures/écritures sur `transactions.category_id`

**Date** : 2026-07-12 (Étape 2, Tasks 2-4, 7, 8)

**Contexte** : la classification d'une transaction était portée par la
table `enriched_transactions` (une ligne par transaction enrichie),
stockant les libellés de classification en clair (`level_1`, `level_2`,
`level_3`) et dupliqués/dénormalisés à travers les configs CR/Bilan, les
mappings et les types d'amortissement. Aucune table de référence : les
catégories n'existaient que comme chaînes de caractères répétées, sans
identité stable ni contrainte d'intégrité, ce qui rendait tout renommage
risqué et toute jointure fragile (comparaisons de libellés).

**Décision** : introduire un **référentiel global** en deux tables
(`category_groups`, `categories`, seedées de façon idempotente : 19
groupes, 56 catégories) donnant à chaque catégorie une **identité stable
par ID**, puis ajouter `transactions.category_id` (FK nullable, indexée) et
**basculer tout le code** dessus :
- backfill `transactions.category_id` (880/880, 0 mismatch de libellé) ;
- **double-écriture transitoire** (helper unique `_sync_transaction_category`)
  pendant la migration : tout site d'écriture de classification met à jour
  À LA FOIS l'ancien `enriched_transactions` ET le nouveau `category_id`,
  pour ne jamais désynchroniser les deux représentations pendant la bascule ;
- toutes les LECTURES basculées sur `category_id` via un helper unique
  `classification_read.py` (`level_1/2/3` = `Category.label` /
  `CategoryGroup.label` / `CASE` sur la nature), puis
- suppression finale de `enriched_transactions` (table + classe ORM +
  colonnes mortes) une fois toutes les lectures et écritures migrées :
  la classification n'est plus portée QUE par `transactions.category_id`.

**Conséquences** :
- Identité stable par ID : renommer une catégorie ne casse plus aucune
  jointure ni aucune config ; l'intégrité est garantie par une FK.
- Une seule source de vérité pour la classification (`category_id`), une
  seule table transaction — fin de la duplication `enriched_transactions`.
- Golden master **zéro écart** à chaque étape (backfill, double-écriture,
  bascule des lectures, drop) — la migration ne change aucun chiffre.
- Sémantique préservée découverte en route :
  `update_transaction_classification(level_1=None)` signifie « conserver »
  (pas « effacer ») ; la désassignation réelle passe par
  `reset_allowed_mappings` (couverte par la double-écriture en bulk UPDATE).
- Dette restante pour l'étape 3 (documentée) : les tables `mappings` /
  `allowed_mappings` / `mapping_imports` et le moteur de règles de
  classification restent vivants jusqu'à l'étape 3.

---

## ADR-005 — Configs CR/Bilan liées par `category_id` + `line_code` stables ; sérialisation « label at the edge »

**Date** : 2026-07-12 (Étape 2, Tasks 5-6)

**Contexte** : les configs du compte de résultat et du bilan
sélectionnaient les transactions à agréger par **listes de libellés en
clair** (`level_1_values`, `level_3_values`) et identifiaient leurs lignes
spéciales (calculées) par un champ texte `special_source`. Deux fragilités :
la sélection par libellé se casse au moindre renommage, et les lignes
calculées n'avaient pas d'identifiant stable indépendant de leur nom
d'affichage français.

**Décision** :
- migrer les configs CR (55 lignes) et Bilan (35 lignes) vers des **tables
  de liaison par `category_id`** (many-to-one, pas de fan-out vérifié) —
  la sélection se fait désormais par ID de catégorie, pas par libellé ;
- introduire un **`line_code` stable** (5 codes × propriétés pour le bilan,
  injection par le service pour les lignes calculées du CR) comme identité
  des lignes spéciales, indépendante de leur libellé d'affichage ;
- adopter la règle **« label at the edge »** : les libellés français
  (identité du golden master) ne sont PAS stockés dans les liaisons — ils
  sont **résolus au bord** (à la sérialisation de la réponse API) depuis le
  référentiel. Le cœur du calcul travaille sur des IDs/natures ; seul le
  bord parle français.

**Conséquences** :
- Les configs survivent à un renommage de catégorie (liaison par ID).
- L'équivalence a été **prouvée** byte-à-byte par le reviewer :
  `NATURE_BY_LABEL` étant 1:1, le filtre par nature ≡ l'ancien filtre par
  `level_3` ; `SPECIAL_LINE_NAMES` et la logique de signe (surface la plus
  risquée) préservées à l'identique. Golden **zéro écart**.
- Invariant de traductibilité à surveiller (validé sur toutes les configs
  réelles par la migration `validate_bilan_config_natures`, documenté aux
  sites de garde) : le calcul des lignes normales est gardé par
  `if all_cat_ids and natures:` — une config dont les `level_3_values` ne
  contiendraient QUE des libellés non-nature produirait `natures=[]` → bloc
  sauté → lignes absentes au lieu de valant 0. Aucune config actuelle n'est
  dans ce cas ; à revalider si de nouvelles configs sont éditées.

---

## ADR-006 — Montants stockés en centimes entiers via `EuroCents` (TypeDecorator) ; `amortization_results.amount` laissé en Float

**Date** : 2026-07-12 (Étape 2, Task 9)

**Contexte** : les montants monétaires étaient stockés en `Float` (euros),
exposant le modèle aux erreurs d'arrondi binaire classiques du flottant sur
des additions/soustractions répétées.

**Décision** : introduire un **`TypeDecorator` `EuroCents`** (module
`backend/database/money.py`) qui **stocke des centimes entiers** en base et
expose des **euros** côté ORM/API (conversion au bord). Appliqué à **11
colonnes monétaires sur 12**. Migration in-place par `UPDATE` (les colonnes
étaient déclarées `FLOAT` mais contenaient des valeurs entières après
conversion, le décorateur gouverne la lecture/écriture). `func.sum` propage
correctement le type `EuroCents` (SQLAlchemy 2.0 `ReturnTypeFromArgs`,
vérifié par test). `SUM` préservée à `0.000000 €` sur les 11 colonnes.

**Déviation spec assumée** : la **12ᵉ colonne, `amortization_results.amount`,
est laissée en `Float`**. Ses valeurs sont des dotations d'amortissement
**dérivées, sous le centime** (ex. `-643,7569`) ; les arrondir au centime
ferait dériver les amortissements cumulés **jusqu'à 0,06 €**, ce qui
**casserait le golden master** (contrat au centime). Le contrat golden au
centime prime sur la règle « toutes les colonnes en entier ». Décision
documentée à la colonne, dans la migration et le rapport de Task 9.

**Conséquences** :
- Plus d'erreur d'arrondi flottant sur les 11 colonnes stockées en centimes.
- Golden **zéro écart** ; perf inchangée (60-84 ms).
- Résidu latent documenté : le mode d'arrondi de la migration
  (`CAST ROUND`, half-away) diffère de celui du décorateur (half-to-even)
  au cas `x.xx5` exact — aucune valeur de prod concernée.

---

## ADR-007 — Durcissement de la quarantaine des tests : `pytest_ignore_collect` (avant import) + garde sur le moteur de PRODUCTION

**Date** : 2026-07-12 (Étape 2, Tasks 1 et 10)

**Contexte** : la quarantaine initiale (ADR-003) posait des marqueurs skip
via `pytest_collection_modifyitems`, ce qui **importait** quand même les
modules — depuis la purge des modèles morts (Task 1), certains modules
hérités ne s'importent plus (`ImportError`) et cassaient la collecte. De
plus, la garde par collecte ne protège que les **scans de répertoire** :
un fichier **nommé explicitement** sur la ligne de commande pytest la
contourne. Le 2026-07-12 (Task 5), un test hérité utilisant le sessionmaker
de prod, ainsi nommé, a **contaminé la base de production** (remédié,
restauré depuis backup, prod vérifiée byte-identique — voir
`ERROR_INVESTIGATION.md`).

**Décision** : deux niveaux complémentaires.
1. **Avant import** : bascule de la quarantaine sur `pytest_ignore_collect`
   (Task 1) — le texte du fichier est lu SANS l'importer (regex sur
   `SessionLocal`/`next(get_db())` et sur l'URL serveur en dur) ; les
   fichiers en quarantaine n'apparaissent même plus comme « skipped » et ne
   cassent plus la collecte.
2. **Défense en profondeur, à l'accès** (Task 10) : `conftest.py` attache un
   évènement `connect` sur l'**OBJET moteur de PRODUCTION**
   (`backend.database.connection.engine`, bindé sur `lmnp.db`) qui **lève une
   `RuntimeError`** dès qu'une connexion est ouverte via ce moteur (donc via
   le sessionmaker de prod ou `next(get_db())`), tant que
   `LMNP_ALLOW_PROD_DB_TESTS != "1"`. Le pool du moteur est vidé à l'install
   (`dispose()`) pour qu'une connexion recyclée ne contourne pas l'évènement.

**Conséquences** :
- **Aucun** test — scanné, nommé explicitement, ou important le moteur
  directement — ne peut plus toucher `lmnp.db` sans le flag d'override
  (à n'utiliser qu'après backup).
- Ciblage volontairement étroit sur l'objet moteur de prod : le harnais
  isolé (`db_session`/`client`, moteur mémoire) et les **tests golden en
  lecture seule** (`test_amortization_evry_golden.py` = vrai fichier
  `?mode=ro`, `test_realtime_states.py` = copie temporaire) ont LEUR PROPRE
  moteur → **non affectés** (vérifié : ils passent toujours). L'évènement
  n'est attaché qu'au moteur de prod, pas à ces moteurs-là.
- Couvert par un test dédié `test_prod_db_guard.py` (écrit pour ne PAS
  matcher les regex de quarantaine, donc il s'exécute réellement) qui prouve
  que l'ouverture d'une connexion sur le moteur de prod lève la
  `RuntimeError` — sans jamais écrire en prod.

---

## ADR — Étape 3 §5 : moteur de classification unifié `classification_rules` (2026-07-13)

**Contexte :** 4 systèmes de classification coexistaient (table `mappings`,
`allowed_mappings`, Excel `mappings_obligatoires.xlsx`, script hardcodé).
Objectif étape 3 §5 : les unifier en **une** table `classification_rules` +
**un** moteur, sans déplacer un centime (golden master v4 bloquant).

**Décisions :**
1. **Table unique `classification_rules`** (`pattern`, `match_type` ∈
   exact|prefix|contains, `category_id` FK→categories, `property_id` nullable
   = règle globale, `priority`, `source` migrated|manual|auto_from_inbox,
   `strict_ratio`). Migration des 366 `mappings` → règles (0 non résolu),
   validée par un **contrôle de non-régression** (rejeu du moteur sur les 880
   transactions classées → 0 divergence) + golden 0.
2. **`strict_ratio` (bool, défaut True)** — garde de similarité 70 %
   désactivable **par règle**. L'ancien moteur (`find_best_mapping`)
   contournait la garde pour les préfixes `PRLV SEPA` et le motif
   `VIR STRIPE` (prélèvements récurrents : préfixe stable + suffixe variable
   = n° de contrat). Plutôt que recopier ces littéraux dans le moteur
   runtime, on porte un **drapeau par règle** : le moteur reste générique, et
   les littéraux vivent UNIQUEMENT dans la migration one-shot
   (`strict_ratio=False` si `'PRLV SEPA' in pattern or pattern=='VIR STRIPE'`).
   48/366 règles ont la garde désactivée.
3. **Portée** : règle de bien (`property_id` non NULL) prime sur globale à
   égalité ; le moteur charge `règles du bien + globales`.

**Statut :** cœur livré et vérifié (non-régression 0, golden 0, 91 tests).
**Différé (décision assumée par l'agent, sur les faits) :** suppression des
tables/routes/code legacy (`mappings`/`allowed_mappings`/`mapping_imports`) —
`allowed_mappings` reste une **whitelist de validation VIVANTE**
(`validate_mapping` interroge la table pour la classification manuelle), donc
son retrait est un refactor à faire **avec le plan frontend** (les écrans
inbox+éditeur remplaceront l'UI mapping en un seul geste). Les 2 écrans =
plan séparé après maquette, consommant `/api/inbox` + `/api/rules`.
