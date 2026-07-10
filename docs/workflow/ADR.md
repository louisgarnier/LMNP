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
