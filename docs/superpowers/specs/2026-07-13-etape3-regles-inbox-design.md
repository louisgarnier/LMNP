# Étape 3 (partie §5) — Règles de classification unifiées + Inbox

**Date** : 2026-07-13
**Branche** : `refonte` (jamais mergée vers `main` pendant la refonte)
**Statut** : Design validé — prêt pour writing-plans
**Réf. spec mère** : `2026-07-10-refonte-lmnp-design.md` §5 (moteur de classification) ; §11 étape 3

---

## 1. Périmètre

Cette spec couvre **uniquement le §5** de l'étape 3 : le moteur de classification unifié,
l'inbox de classification et l'écran Règles.

**Hors périmètre (chantier séparé)** : le §8bis (dashboard moderne + design system +
restylage des écrans). Décision de découpage prise le 2026-07-13 — le §8bis fera l'objet de
sa propre spec → plan → build après celui-ci. Raison : §5 est de la logique métier + données
(indépendante du design), §8bis est une refonte UI transverse ; deux natures différentes,
chacune plus sûre validée séparément.

### Objectif

Fusionner les **4 systèmes de classification actuels** en **un seul** :
`mappings` (366 lignes) + `allowed_mappings` (168, référentiel) + `mappings_obligatoires.xlsx`
+ le script `update_hardcoded_mappings.py` + les cas codés en dur (`VIR STRIPE`, `PRLV SEPA`).

**Résultat visé** : renommer/configurer les règles se fait dans l'app ; valider une transaction
non classée prend un clic et crée la règle qui évite de refaire le geste. **Les calculs ne
bougent pas d'un centime** (golden master bloquant).

---

## 2. Décisions verrouillées (brainstorm 2026-07-13)

1. **Découpage** : §5 (règles + inbox) d'abord ; §8bis (dashboard) ensuite, spec séparée.
2. **Auto-règle depuis l'inbox** : à la validation, le moteur propose une **règle préfixe
   intelligente, éditable** (motif = libellé sans le token variable de fin), pré-remplie ;
   l'utilisateur ajuste et valide en un geste. Pas de règle exacte sur un libellé à suffixe
   unique (qui ne rematcherait jamais).
3. **Portée d'une règle** : **par propriété par défaut, promouvable en global**
   (`property_id` NULL = global). Colle aux 366 mappings existants (migration 1:1).
4. **Bascule** : **directe** (approche A) — migration en une fois, réécriture du moteur,
   suppression des vieilles tables. Sûre grâce à : sauvegarde `.db`, golden master bloquant,
   et **aucun reclassement de l'historique**.
5. **Suggestion inbox** : meilleur candidat du moteur **en relâchant le garde-fou 70 %**, à
   défaut la catégorie de la transaction déjà classée la plus proche. Affichée, jamais
   appliquée automatiquement.
6. **« Tout valider »** : **regroupe** les transactions par motif-préfixe + catégorie
   suggérés, crée **une règle par groupe**, ne valide que les suggestions fiables (les
   ambiguës restent dans l'inbox).

---

## 3. Modèle de données

### Nouvelle table `classification_rules`

Remplace `mappings` + `allowed_mappings` + l'Excel + le script hardcodé.

| Colonne       | Type            | Notes |
|---------------|-----------------|-------|
| `id`          | PK              | |
| `pattern`     | texte           | le motif, ex. `"VIR AIRBNB PAYMENTS LUXEMBOU"` |
| `match_type`  | enum            | `exact \| prefix \| contains` |
| `category_id` | FK → `categories` | le référentiel de l'étape 2 |
| `property_id` | FK nullable     | renseigné = règle du bien ; **NULL = globale (3 biens)** |
| `priority`    | int             | départage les candidats (défaut 0) |
| `source`      | enum            | `migrated \| manual \| auto_from_inbox` |
| `created_at`  | datetime        | |

- Montants : sans objet (aucune colonne monétaire).
- Promotion bien → global = passer `property_id` à NULL.

### Tables **non** touchées

Les tables de **config** des états financiers (`compte_resultat_mappings`,
`compte_resultat_mapping_categories`, `bilan_mappings`, `bilan_mapping_categories`) sont le
sujet de l'étape 2 (lignes d'états financiers par `category_id`) — **hors périmètre**, on n'y
touche pas.

### Tables / fichiers **supprimés** (en fin d'étape uniquement)

`mappings`, `allowed_mappings`, `mapping_imports`, `mappings_obligatoires.xlsx`,
`backend/scripts/update_hardcoded_mappings.py` (+ `update_hardcoded_mappings_from_excel.py`,
`load_hardcoded_mappings.py`, `manage_hardcoded_mappings.py`),
`backend/api/routes/mappings_allowed_endpoints.py` (dead code déjà noté §9 spec mère).

---

## 4. Moteur unifié

Réécriture de `backend/api/services/enrichment_service.py` pour lire `classification_rules`.
**Signatures publiques conservées** (`assign_category`, `enrich_transaction`,
`enrich_all_transactions`, `update_transaction_classification`) — les appelants ne changent pas.

### Sémantique de résolution (identique à l'actuelle)

Pour une transaction (libellé `L`) :

1. **Exact** : `pattern == L` → gagne toujours (même court).
2. Sinon **préfixe / contient**, filtrés par le garde-fou de similarité
   `len(pattern) / len(L) ≥ 0.70` (constante `MIN_SIMILARITY_RATIO = 0.70`, inchangée).
3. Entre candidats restants : **priorité décroissante**, puis **longueur de motif
   décroissante** (motif le plus spécifique gagne).
4. **Portée** : à priorité/longueur égales, une règle du bien (`property_id = P`) prime sur une
   règle globale (`property_id IS NULL`).

Les cas `VIR STRIPE` / `PRLV SEPA` sont désormais des **règles ordinaires** en base — plus
aucun `if` magique dans le code.

### Heuristique du motif préfixe (auto-règle inbox)

À partir du libellé complet, retirer le(s) **token(s) variable(s) de fin** : segments qui
ressemblent à un identifiant (suite alphanumérique longue avec chiffres, préfixe `G-`,
références de type `GP…`, hash). Le motif proposé est le préfixe stable restant. Le résultat
est **pré-rempli et éditable** — l'utilisateur reste maître du motif final. (Cas de repli si
l'heuristique ne trouve pas de token variable : proposer le libellé entier en `exact`, à
l'utilisateur d'élargir.)

---

## 5. Migration (script dédié, ordre strict)

1. **Sauvegarde** `.db` horodatée dans `backups/` avant toute écriture.
2. **Traduction des 366 mappings** → `classification_rules` :
   `nom → pattern` ; `is_prefix_match` : `0 → exact`, `1 → prefix` ; `priority`, `property_id`
   conservés ; `source = migrated` ; `(level_1, level_2, level_3) → category_id` via le
   référentiel étape 2. **Un triplet non résolu = arrêt de la migration** (rapport, pas de
   devinette).
3. **Cas hardcodés** (`VIR STRIPE`, `PRLV SEPA`) → règles ; suppression des `if` correspondants.
4. **Dédoublonnage** : fusion des règles identiques `(pattern, match_type, category_id,
   property_id)`. Compte réel de règles après fusion reporté dans le build-log.
5. **Contrôle de non-régression** : rejouer le moteur sur les transactions déjà classées →
   **rapport des divergences, sans réappliquer**. Objectif : **0 divergence**. Toute divergence
   est examinée avant de continuer.
6. **Golden master** `--compare` bloquant (tag courant) : CR/Bilan identiques au centime.
   Garanti par construction — aucun `category_id` de transaction n'est modifié.
7. **Suppression** des tables/fichiers (§3) **seulement** une fois 5 et 6 verts.

**Invariant de sûreté** : l'historique garde ses `category_id`. La migration ne peut pas bouger
un chiffre d'état financier. Le seul risque réel est une règle mal traduite classant mal une
*future* transaction — attrapé par le contrôle 5.

---

## 6. Écran Inbox (maquette ①)

Remplace « Non classées ». Pour le bien courant, liste les transactions à `category_id` NULL.

- **Ligne** : date, libellé, montant + **suggestion** (catégorie) avec `[Valider]` `[Modifier]`,
  ou un sélecteur de catégorie si aucune suggestion.
- **Suggestion** (décision §2.5) : meilleur candidat du moteur en relâchant le seuil 70 %, à
  défaut la catégorie de la transaction déjà classée la plus proche. Jamais appliquée seule.
- **Valider (1 clic)** : pose `category_id` **et** crée l'auto-règle préfixe (heuristique §4),
  `source = auto_from_inbox`, portée = bien courant par défaut.
- **Modifier** : ajuster catégorie et/ou motif proposé (et portée bien/global) avant création.
- **Tout valider** (décision §2.6) : regroupe par motif-préfixe + catégorie suggérés, crée une
  règle par groupe, ne valide que les suggestions fiables ; les ambiguës restent.
- **Compteur** dans l'onglet.
- Chaque validation déclenche le **recalcul temps réel** (étape 1) : CR à jour au clic.

---

## 7. Écran Règles (maquette ②)

Table unique remplaçant l'onglet Mapping + l'Excel + le script.

- **Colonnes** : motif, type de match, catégorie, portée (bien/global), nombre de transactions
  concernées, source.
- **Préversion live** à la création/édition : « classerait **N** non classées » **et** « en
  conflit avec **M** déjà classées différemment ».
- **Appliquer aux existantes** : choix explicite de l'utilisateur. **Défaut : non** (jamais de
  reclassement silencieux).
- **Supprimer** une règle **ne déclasse pas** les transactions déjà classées (n'affecte que le
  futur).
- **Portée** : bascule bien ↔ global (promotion `property_id` → NULL).

---

## 8. API (backend)

Nouvelles routes (remplacent `mappings.py`, `enrichment.py`, `mappings_allowed_endpoints.py`) :

| Méthode | Route | Rôle |
|---------|-------|------|
| GET  | `/api/rules?property_id=` | Liste des règles (bien + globales) avec compte de transactions concernées |
| POST | `/api/rules` | Créer une règle |
| PUT  | `/api/rules/{id}` | Éditer (motif, match, catégorie, portée, priorité) |
| DELETE | `/api/rules/{id}` | Supprimer (n'affecte que le futur) |
| POST | `/api/rules/preview` | Préversion d'une règle non enregistrée : `{would_classify: N, conflicts: [...]}` |
| GET  | `/api/inbox?property_id=` | Transactions non classées + suggestion par transaction |
| POST | `/api/inbox/validate` | Valider une transaction : `{transaction_id, category_id, rule?: {pattern, match_type, scope}}` (rule absent = « juste celle-ci ») |
| POST | `/api/inbox/validate-all?property_id=` | Validation groupée (règles par groupe) |

- Erreurs métier remontées en HTTP avec message exploitable, **jamais avalées** (bandeau UI).
- Recalcul implicite après mutation (temps réel étape 1).

---

## 9. Tests & validation

- **pytest isolé** (conftest + SQLite en mémoire, jamais la base de prod — harnais existant) :
  - moteur : exact > préfixe/contient, seuil 70 %, priorité puis longueur, bien > global ;
  - heuristique motif préfixe (cas Airbnb `G-…`, Getaround `GP…`, virement simple) ;
  - portée bien/global ; préversion (compte + conflits) ;
  - migration : traduction 1:1, triplet non résolu = échec, dédoublonnage.
- **Contrôle de non-régression** (script) : 0 divergence de `category_id` sur l'historique.
- **Golden master** `--compare` bloquant après migration.
- **E2E Playwright** : parcours inbox (valider → CR à jour) et règles (créer avec préversion).
- Budget perf : préversion et liste de règles < 300 ms sur les volumes actuels.

---

## 10. Risques & parades

| Risque | Parade |
|--------|--------|
| Triplet `level_1/2/3` sans catégorie cible | Migration s'arrête et rapporte ; on complète le référentiel avant de reprendre |
| Explicitation `is_prefix_match` → contient perdu | Contrôle de non-régression (§5.5) : toute divergence détectée avant suppression des vieilles tables |
| Auto-règle préfixe trop large (faux positifs futurs) | Motif éditable + préversion au moment de la création ; portée bien par défaut |
| SQLite corrompu pendant migration | Sauvegarde `.db` horodatée avant écriture (§5.1) |
| Écart golden après migration | Comparaison bloquante ; impossible par construction (historique figé) |

---

## 11. Livrable de fin d'étape

- Table `classification_rules` peuplée, vieilles tables/fichiers supprimés.
- Moteur unifié en place, signatures publiques inchangées.
- Écrans Inbox + Règles fonctionnels (maquettes `ui-mockup` validées écran par écran avant code).
- Golden master vert, contrôle de non-régression à 0 divergence, suite pytest verte.
- `build-log.md` + `codebase.md` à jour ; commit `[REFONTE] …` ; app fonctionnelle.
