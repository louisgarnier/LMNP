# Spec — Refonte LMNP : temps réel, classification simplifiée, Enable Banking, fiscalité

- **Date** : 2026-07-10
- **Statut** : validé sur le principe par Louis (détails techniques délégués), en attente de sa relecture rapide
- **Références** : `docs/project/REFONTE_PLAN.md` (plan en étapes), maquettes `refonte-v1.html` (inbox, règles, sources, temps réel), audit du 2026-07-09

---

## 1. Contexte et objectif

L'app actuelle fonctionne (import CSV → classification 3 niveaux → TCD → CR/Bilan/Crédit → amortissements → prévisions) mais elle est pénible à utiliser et à faire évoluer : 4 systèmes de mappings en texte libre, caches d'états financiers jamais invalidés (bug), montants en float, configuration à refaire par propriété, import CSV manuel.

**Objectif de Louis** (ses mots) : « un truc plus carré, par appart, et l'objectif après sera d'avoir le résultat total de tous les apparts pour remplir la feuille d'impôts ». Comptabilité **en temps réel**, mappings **faciles**, calculs **conservés**.

**Contrat de validation** : la refonte doit reproduire les chiffres actuels au centime près, à l'exception des bugs identifiés et documentés (voir §10). Ses documents comptables réels (bilans, tableaux d'amortissement, échéanciers) sont la référence absolue quand ils existent. Si le résultat ne convient pas → rollback de branche.

## 2. Décisions actées avec l'utilisateur

| Sujet | Décision |
|---|---|
| Découpage | Un seul spec global, plans d'implémentation par étape |
| Fiscalité 39C | Incluse dans le spec |
| Comptes bancaires | **Un compte dédié par propriété** (pas de compte partagé, pas de flux perso) |
| Enable Banking | App déjà enregistrée (autre projet), **production directe** |
| Déploiement | **Local mono-utilisateur** (pas d'auth, SQLite conservé, callback localhost) |
| Branche `forecast` (WIP prévisions bilan) | **Finir et merger avant** la refonte |
| Stratégie de migration | **Évolution incrémentale en place** (jamais d'app cassée, rollback par étape) |
| Détention | **Nom propre, seul** → une seule activité LMNP, consolidation des 3 apparts vers la 2042-C-PRO |
| Process | Louis ne valide pas les choix techniques ; il valide les chiffres et l'usage |

## 3. Non-objectifs

- Pas de changement de stack (FastAPI + SQLite + Next.js conservés).
- Pas d'authentification / multi-utilisateurs.
- Pas de génération du PDF Cerfa lui-même — mais les montants sont produits **case par case au format liasse** (voir §8), prêts à recopier dans Teledec.
- Pas de TVA (LMNP non assujetti dans le cas de Louis).

> Note : la refonte **inclut** une modernisation visuelle (dashboard widgets, voir §8bis) — décision de Louis du 2026-07-10, qui remplace l'ancien non-objectif « écrans identiques ».

## 4. Modèle de données cible

### Nouvelles tables

- **`category_groups`** : les « Level 2 » actuels. Champs : `id`, `label`, `nature` (énum fermée : `produits | charges_deductibles | emprunt | actif | passif` — l'actuel Level 3).
- **`categories`** : les « Level 1 » actuels. Champs : `id`, `label`, `group_id` (FK), `is_custom`. Référentiel **global** (le plan de catégories LMNP est le même pour toutes les propriétés), seedé depuis les 53 combinaisons « hardcodées » actuelles + les combinaisons manuelles existantes.
- **`classification_rules`** : fusion `mappings` + `allowed_mappings` + Excel. Champs : `id`, `pattern`, `match_type` (`exact | prefix | contains`), `priority`, `category_id` (FK), `property_id` (nullable = règle globale), `source` (`migrated | manual | auto_from_inbox`), `created_at`.
- **`bank_accounts`** : `id`, `property_id` (FK, un compte par propriété), `bank_name`, `iban_masked`, `eb_account_uid`, `eb_session_id`, `session_valid_until`, `last_sync_at`, `last_tx_cursor`.

### Tables modifiées

- **`transactions`** : + `category_id` (FK nullable — remplace `enriched_transactions`, qui était du 1:1), + `account_id` (FK nullable pour l'historique CSV), + `external_id` (id banque, contrainte unique `(account_id, external_id)`), + `source` (`csv | api | manual`). `solde` reste calculé par propriété (comptes dédiés → équivalent au solde de compte).
- **Configs CR/Bilan** : les lignes référencent des **listes de `category_id`** (table de liaison, plus de JSON de libellés). Les lignes « données calculées » sont identifiées par un **code stable** : `AMORT`, `COUT_FINANCEMENT`, `CAPITAL_RESTANT_DU`, `RESULTAT_EXERCICE`, `REPORT_A_NOUVEAU`, `COMPTE_BANCAIRE`, `AMORT_CUMULES` (plus de chaînes magiques françaises).
- **`loan_configs`** : suppression de l'index unique global sur `name` (unicité par propriété seulement) et du rôle du champ `loan_start_date` dans les calculs — l'activité d'un prêt se déduit de son échéancier (`loan_payments`).
- **`amortization_types`** → **`amortization_components`** : + `land_share_amount` (part terrain non amortissable) au niveau du bien, ventilation par composants (structure, façade/toiture, IGT, agencements, mobilier, travaux) avec durées et bases par **montants** (plus de matching par catégorie croisée). Rattachement explicite aux transactions d'immobilisation par FK.

### Montants en centimes

Toutes les colonnes monétaires passent de `Float` à `Integer` (centimes). Conversion unique par migration (`round(x*100)`), vérifiée par comparaison des totaux avant/après. Formatage en euros uniquement à l'affichage (un seul utilitaire partagé `formatCurrency`).

### Tables supprimées

`compte_resultat_data`, `bilan_data` (caches), `enriched_transactions`, `mappings`, `allowed_mappings`, `mapping_imports`, et les 4 tables legacy orphelines (`parameters`, `amortizations`, `financial_statements`, `consolidated_financial_statements`).

## 5. Moteur de classification (règles + inbox)

### Sémantique des règles

1. À l'arrivée d'une transaction (synchro, CSV ou création manuelle), le moteur cherche la règle applicable : correspondance exacte d'abord, puis préfixe/contient par priorité décroissante puis longueur de motif décroissante. Le seuil de similarité 70 % actuel est conservé comme garde-fou pour les règles `prefix`/`contains`.
2. **Une règle ne reclasse jamais l'historique silencieusement.** À la création/édition d'une règle, une préversion montre : transactions non classées qui seraient classées, et transactions déjà classées différemment (conflits). L'utilisateur choisit d'appliquer ou non aux existantes.
3. Les cas spéciaux hardcodés (`PRLV SEPA`, `VIR STRIPE`) deviennent des règles ordinaires migrées en base.
4. Valider une suggestion dans l'inbox crée automatiquement la règle correspondante (`source = auto_from_inbox`).

### Inbox (maquette ①)

Remplace « Non classées » : liste des transactions sans `category_id`, chacune avec la suggestion du moteur (si une règle matche partiellement) ou un sélecteur. Actions : Valider (1 clic), Modifier, Tout valider. Compteur dans l'onglet. Chaque validation déclenche le recalcul implicite (cf. §6) — le CR est à jour dès le clic.

### Écran Règles (maquette ②)

Table unique : motif, type de match, catégorie, nombre de transactions concernées, source. Édition avec préversion live. Remplace l'onglet Mapping, le fichier `mappings_obligatoires.xlsx` et le script `update_hardcoded_mappings.py` (supprimés).

## 6. Calculs en temps réel

- Suppression des endpoints `/generate` et des tables de cache. `GET /compte-resultat` et `GET /bilan` **calculent à la demande** (mêmes formules qu'aujourd'hui, services conservés).
- Fix du coût quadratique : dans une requête bilan multi-années, les CR par année sont calculés une fois et mémoïsés (dict passé aux fonctions, pattern déjà amorcé mais non branché dans `bilan.py:430`).
- Budget de performance : < 300 ms pour un bilan 6 ans × 1 propriété sur les volumes actuels (~600 transactions). Mesuré par test.
- Le concept d'« invalidation » disparaît entièrement (le bug B1 devient sans objet).
- Frontend : suppression des `refreshKey` manuels au profit d'un refetch après mutation (l'existant marche, on ne généralise pas de lib de cache — YAGNI).

## 7. Ingestion unifiée + Enable Banking

### Service d'ingestion (backend)

`ingest_transactions(db, property_id, account_id, rows, source)` — unique point d'entrée pour CSV **et** API :
normalisation → dédoublonnage → insertion → classification par règles → recalcul soldes → recalcul amortissements concernés — le tout dans **une seule transaction DB** (échec = rollback complet, erreur remontée à l'UI, jamais avalée).

Dédoublonnage : par `external_id` quand il existe (API) ; pour le CSV, clé de repli `(property_id, date, montant_centimes, nom)` — l'égalité en centimes remplace l'égalité float. À la première synchro API d'un compte ayant un historique CSV, la fenêtre de recouvrement est dédupliquée par la clé de repli.

### Module Enable Banking

- Client : JWT RS256 signé avec la clé privée de l'app existante de Louis. **Clé et `application_id` en variables d'environnement / fichier hors repo** (`.env` gitignoré), jamais commités.
- Flux de connexion : choisir la banque (liste ASPSP France) → URL d'autorisation → consentement sur le site de la banque → callback `localhost` → création de session (validité ~180 jours selon banque) → sélection du compte → liaison à la propriété.
- Synchro : à l'ouverture de l'app (si > 6 h depuis la dernière) + bouton manuel. Pagination par continuation key, curseur persisté (`last_tx_cursor`). Transactions en attente (`pending`) ignorées jusqu'à comptabilisation.
- Renouvellement : alerte visible dès J-30 avant expiration du consentement (bandeau écran Sources).
- Écran Sources (maquette ③) : carte par compte connecté (solde banque, dernière synchro, échéance consentement), connexion nouvelle banque, section Import CSV conservée pour l'historique.

## 8. Amortissements et fiscalité (39C + consolidation)

### Ventilation par composants

Pour chaque bien : prix d'acquisition ventilé en **part terrain (non amortissable)** + composants amortissables (structure ~50 ans, façade/toiture ~20, IGT ~15, agencements ~10, mobilier 5-10, travaux selon nature — durées par défaut modifiables). L'UI propose la ventilation en % avec presets, les montants exacts sont saisis depuis les documents de Louis (tableaux d'amortissement existants = source de vérité pour les biens déjà en cours). Convention 30/360 et prorata première/dernière année conservés tels quels.

### Article 39C (calcul fiscal)

Par année, pour l'activité LMNP globale :
- `dotation_potentielle` = somme des dotations des composants.
- `plafond_39C` = max(0, loyers et produits − charges hors dotations) : l'amortissement déduit ne peut pas créer ni aggraver le déficit.
- `dotation_deduite` = min(dotation_potentielle, plafond_39C) ; l'excédent alimente le **stock d'amortissements réputés différés**, reportable sans limite, imputé automatiquement les années bénéficiaires.
- Le CR affiche les deux résultats : **comptable** (dotation complète, comme aujourd'hui) et **fiscal** (dotation plafonnée + suivi du stock différé). Tout calculé à la volée, rien de stocké.

### Consolidation au format liasse (nouvel écran)

Une seule activité LMNP en nom propre → un écran « Consolidation » : résultat fiscal par propriété + **total consolidé, présenté dans la structure exacte de la liasse** avec les codes de cases Cerfa — 2031-SD (récapitulation, cadre I « BIC non professionnels »), 2033-A bilan simplifié (cases 010-199), 2033-B compte de résultat simplifié, 2033-C immobilisations/amortissements, 2033-D (dont suivi des déficits et amortissements différés). Montants prêts à recopier dans Teledec.

**Référence de validation** : les liasses réelles 2024 et 2025 de Louis (`docs/files/liasse_fiscale_2024_*.pdf`, `liasse_fiscale_25.pdf`) et les bilans 2022/2023 — l'écran doit retomber sur ces chiffres pour les exercices passés. Les déficits LMNP non-professionnels (hors amortissements différés) suivis avec leur péremption à 10 ans.

## 8bis. Dashboard & widgets (modernisation visuelle)

Décision de Louis : les écrans ne restent pas identiques — l'app gagne un **dashboard moderne, épuré, par propriété**, avec les informations clés en widgets :

- **Par propriété** : solde bancaire, loyers encaissés vs attendus (année en cours), charges payées, résultat comptable et fiscal en cours (temps réel), prochaine échéance de crédit + capital restant dû, compteur inbox (transactions à classer), alerte consentement bancaire.
- **Vue globale (accueil)** : les 3 propriétés côte à côte + le consolidé (résultat fiscal total en cours, trésorerie totale), accès direct à l'inbox.
- Design system unifié à cette occasion : palette et composants partagés (fin des styles inline hex répétés), formatage monétaire unique.
- Les écrans de travail (TCD, tableaux CR/Bilan détaillés, Amortissements) sont **restylés** dans le même design system mais gardent leur structure fonctionnelle actuelle.
- Chaque écran passe par une **maquette validée par Louis avant code** (process ui-mockup, comme refonte-v1.html).

## 9. Gestion d'erreurs, logging, hygiène

- Plus aucun `except: print` : les erreurs métier remontent en HTTP avec message exploitable, affichées dans l'UI (bandeau d'erreur par carte, plus de `return null` silencieux).
- Logging conservé selon les conventions existantes (fichiers `logs/backend_*.log` etc., emojis, format `[Module] verbe: détail`).
- Nettoyage inclus : fichiers iCloud « `* 2.*` » supprimés du repo + `.gitignore`, dead code supprimé (`mappings_allowed_endpoints.py`, `example.py`, branches bilan mortes de `ProRataForecastCard`), URL API centralisée dans `client.ts`, CORS restreint à `localhost:3000` sans wildcard+credentials, nom de fichier d'upload sanitisé.

## 10. Validation par les chiffres (golden master)

1. **Avant toute modification** : script d'extraction qui fige dans `docs/project/reference/golden/` les sorties actuelles — CR par année × propriété, bilan par année × propriété, dotations par composant × année, soldes — au centime.
2. **Écarts attendus et documentés** (les seuls tolérés) :
   - Capital restant dû 2022-2025 d'Evry : diminue désormais chaque année (bug de la date de prêt corrigé) → le bilan s'équilibre.
   - Dotations d'amortissement d'Evry : recalculées après remise à plat des mappings croisés et de la part terrain — validées contre **les tableaux d'amortissement fournis par Louis**, pas contre les chiffres bugués actuels.
   - Arrondis : écarts ≤ 1 centime par ligne dus au passage float → centimes, listés par le script de comparaison.
3. **Après chaque étape** : script de comparaison golden vs actuel ; tout écart hors liste = bloquant.
4. Les documents comptables réels de Louis priment sur le golden master en cas de divergence. Ils sont déposés dans **`docs/files/`** : bilans 2022 et 2023, liasses fiscales 2024 et 2025 (format cible + chiffres de validation), et par appartement (`docs/files/appartements/{Evry, Marseille, Marseille colloc}/`) les tableaux d'amortissement des crédits (PDF + xlsx), les tableaux d'immobilisations, les trades CSV et les mappings.
5. Tests : suite pytest isolée (conftest + SQLite en mémoire, plus jamais la base de prod), tests unitaires des services de calcul, E2E Playwright sur les parcours inbox/règles/états financiers.

## 11. Ordre d'exécution

0. **Pré-travail** : finir et merger la branche `forecast` ; golden master figé ; corrections de données (date du prêt Evry, mappings d'amortissement — avec les documents de Louis).
1. **Temps réel** : suppression caches + fix quadratique (§6).
2. **Référentiel** : tables catégories/groupes, migration des classifications, configs par IDs, centimes (§4).
3. **Règles + inbox + dashboard** : moteur unifié, écrans ① ②, dashboard widgets et design system (§5, §8bis) — maquettes validées avant code.
4. **Ingestion + comptes** : service unique, `bank_accounts`, `external_id` (§7 partie 1).
5. **Enable Banking** : client, connexion, synchro, écran Sources (§7 partie 2).
6. **Fiscalité** : composants + 39C + consolidation au format liasse (2031/2033, cases Cerfa) validée contre les liasses 2024/2025 (§8).

Chaque étape : plan d'implémentation dédié (writing-plans), app fonctionnelle à la fin, comparaison golden master, commit. Rollback possible par étape.

## 12. Risques et parades

| Risque | Parade |
|---|---|
| Écart de chiffres non expliqué après migration | Comparaison golden master bloquante à chaque étape |
| Historique CSV dupliqué à la première synchro API | Dédoublonnage de recouvrement par clé de repli (§7) |
| Session Enable Banking expirée / banque capricieuse | Alerte J-30, resynchro manuelle, curseur persisté |
| Ventilation amortissements sans documents | Bloquer l'étape 0.3 tant que les tableaux de Louis ne sont pas fournis ; presets par défaut sinon, marqués « à confirmer » |
| SQLite corrompu pendant migration | Copie de sauvegarde du fichier `.db` avant chaque étape de migration |
