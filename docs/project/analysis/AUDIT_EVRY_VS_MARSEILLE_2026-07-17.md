# Audit Evry vs Marseille colloc — 2026-07-17

Demande : comparer les deux biens (wireframe, modules), lister les écarts
techniques, et recenser le code dormant / inutile.

Méthode : comparaison base de données table par table, lecture du code, et
**tests A/B réels** (avant/après sur 8 années) pour chaque écart supposé — aucune
conclusion tirée de la seule lecture du code.

---

## 1. La logique est déjà identique

**Aucun identifiant de bien codé en dur**, ni côté serveur ni côté écran :

```
grep -rE "property_id *[=!]= *(15|25|26)" backend/api frontend/src frontend/app  -> 0
grep -rniE "\"(evry|mars colloc)\""      backend/api frontend/src frontend/app  -> 0
```

Le code traite les trois biens de la même façon. **Tout écart de comportement
vient donc de la configuration en base**, jamais du code.

## 2. Les écrans sont les mêmes

Aucun branchement par bien. Chaque écran monte les mêmes modules quel que soit le
bien actif :

| Écran (`frontend/app/…`) | Modules montés |
|---|---|
| `dashboard/etats-financiers` | LoanConfigSingleCard, LoanPaymentTable, CompteResultatConfigCard, CompteResultatTable, BilanConfigCard, BilanTable, BilanForecastCard¹, ProRataForecastCard |
| `dashboard/transactions` | FileUpload, ImportLog, TransactionsTable, InboxScreen, RulesScreen, ParametresScreen |
| `dashboard/amortissements` | AmortizationConfigCard, AmortizationTable |
| `dashboard/pivot` | PivotFieldSelector, PivotTable, PivotTabs, PivotDetailsTable |
| `eb-callback` | ParametresScreen |

¹ ne s'affiche jamais aujourd'hui — voir §5.

⚠️ Les pages sont dans **`frontend/app/`**, PAS `frontend/src/app/`. Une recherche
limitée à `frontend/src` conclut à tort que des composants sont morts.

## 3. Écarts de configuration — corrigés ce jour

Trois écarts supprimés, chacun **validé par un test A/B** (calcul complet avant /
après sur 8 années, comparaison ligne à ligne) :

| Écart | Evry (avant) | Marseille | Impact mesuré | Action |
|---|---|---|---|---|
| `prorata_settings.prorata_enabled` | `true` | `false` | colonne « 2026 (projeté) » + écart affiché de **5,47 %** | aligné à `false` |
| `bilan_config.level_3_values` | `["TEST_L3_VALUE","Actif","Passif"]` | `["Actif","Passif"]` | **0 différence** sur 8 ans | `TEST_L3_VALUE` retiré |
| `compte_resultat_config.level_3_values` | `["Charges Déductibles","Produits","Emprunt"]` | `["Charges Déductibles","Produits"]` | **0 différence** sur 8 ans | `Emprunt` retiré |

`TEST_L3_VALUE` = contamination de test dans la base de production (incident
connu). Sans effet sur les chiffres (le calcul ne comprend que 5 libellés :
`Produits`, `Charges Déductibles`, `Emprunt`, `Actif`, `Passif` — le reste est
ignoré) mais **affiché** comme case à cocher par `BilanConfigCard`.

`Emprunt` était sans effet car les catégories de nature `emprunt` d'Evry
(mensualités de crédit) ne sont reliées à aucune ligne du CR : elles entraient
dans le filtre puis étaient écartées faute de mapping.

Config finale, identique sur les deux biens :

```
              CR                                  bilan                prévision
Evry      ["Charges Déductibles","Produits"]      ["Actif","Passif"]   éteinte
Marseille ["Charges Déductibles","Produits"]      ["Actif","Passif"]   éteinte
```

Bilan Evry : **écart 0,00 € de 2021 à 2028**.

## 4. Écarts restants — tous légitimes (données)

| | Evry | Marseille | Verdict |
|---|---|---|---|
| `amortization_types` | 4 | 7 | découpage d'immeuble différent. Les 7 types de Marseille pointent tous vers de vraies catégories (vérifié) — pas de type orphelin |
| `loan_configs` | 1 | 2 | Marseille a 2 crédits |
| `pivot_configs` | 2 (`test`, `cca`) | 0 | vues sauvegardées par l'utilisateur ; `test` est probablement du déchet |
| `classification_rules` | 180 | 49 | historique plus long ; voir ERROR_INVESTIGATION.md §« règles = annuaire » |
| lignes CR | 9 | 7 | voir §6 |

## 5. Code dormant et code mort

### 5.1 Certainement mort (supprimable)

| Cible | Lignes | Preuve |
|---|---|---|
| `src/components/LoanConfigCard.tsx` + son import (`app/dashboard/etats-financiers/page.tsx:12`) | 919 | importé mais **jamais rendu** (`<LoanConfigCard` → 0 hit). Le composant utilisé est `LoanConfigSingleCard` |
| `src/api/client.ts:607-1094` — `mappingsAPI` (24 méthodes) | ~490 | 0 référence hors `client.ts`. Vestige de la migration `mappings` → `classification_rules` |
| `src/components/EditTransactionModal.tsx` | 290 | 0 référence hors du fichier. `README.md:54,240,246` le documente encore (doc obsolète) |
| `src/types/index.ts` (`Example`, `CreateExampleRequest`, `UpdateExampleRequest`) | 30 | boilerplate de scaffold, 0 usage |
| `src/utils/logger.ts` — `getLogs`, `exportLogs`, `downloadLogs`, `setLogToConsole`, `warn`, `error`, `debug` | ~50 | seul `info()` est appelé |
| 22 méthodes API isolées (`healthAPI`, `enrichmentAPI`, `transactionsAPI.getById/create`, les 4 méthodes `override`, `bilanAPI.calculate/getBilan/getMapping`, `rulesAPI.update`, …) | ~150 | **46 méthodes mortes sur 125 (37 %)** |
| `app/dashboard/etats-financiers/page.tsx:14` — import `LoanPaymentFileUpload` | 1 | non utilisé dans ce fichier (monté depuis `LoanConfigSingleCard.tsx:448`) |

**≈ 1 930 lignes supprimables en confiance « certain ».**

### 5.2 Dormant — PAS mort, décision requise

Le code de **projection du bilan** ne s'exécute plus, car `prorata_enabled` est à
`false` sur tous les biens. Mais le réglage reste **activable** (route
`prorata_forecast.py:94`, défaut `False` en base) et un test backend l'exerce
(`test_cr_no_forecast_pollution.py:71`). C'est une fonction désactivée, pas du
code mort — **ne pas supprimer sans décider d'abandonner la fonction**.

- `src/components/BilanForecastCard.tsx:166` — `if (!settings?.prorata_enabled) return null` → **la carte entière (~250 lignes) ne s'affiche jamais**
- `src/components/BilanTable.tsx:230-269` — bloc de projection ; en cascade : `isProjectionActiveForYear()` toujours `false` (`:94`), `getProjectedActifTotal` jamais appelé (`:98`), branches ACTIF projetées mortes (`:414`, `:448`), badge « (projeté) » (`:649`), affichage (`:770`)
- `src/utils/bilanProjection.ts:18` — `computeCompteBancairePrevu` : 2 call sites, tous deux inatteignables. `extractCategory` reste vivant
- `__tests__/bilanProjection.test.ts` — teste une fonction non exécutée en production

**⚠️ Si la fonction est rallumée un jour, elle est cassée** (voir §7).

### 5.3 Résidus

- `src/components/ProRataForecastCard.tsx` — les branches `bilan_actif`/`bilan_passif` **ont bien été supprimées**. Restent : l'union de types `client.ts:2547,2558` (valeurs jamais produites), les gardes `targetType === 'compte_resultat'` (`:277`, `:299`) toujours vraies, et la prop `sectionTitle` (`:27`) jamais passée → branche `:175` inatteignable
- **521 `console.*`** dans le code livré (`app` + `src`), dont **143 dans `client.ts`**. Cas typique : `BilanTable.tsx:109` logue à chaque rendu, hors de tout `useEffect`
- 1 seul TODO : `app/dashboard/amortissements/page.tsx:102`
- Aucun bloc de code commenté (vérifié)

## 6. Risque latent — sur Marseille, pas sur Evry

**Aucune bombe active** : sur les 3 biens, zéro catégorie utilisée sans
rattachement à une ligne du CR. Le trou CFE (−358 €, corrigé ce jour) était le
dernier.

Mais **10 catégories sont rattachées chez Evry et absentes chez Marseille** :

```
Assurance Propriétaire Non Occupant    <-- Marseille n'a AUCUNE ligne « Assurances »
Cotisation Foncière des Entreprises    <-- exactement le bug corrigé ce matin
Internet
Frais de comptabilité
Frais de gestion locative
Diagnostics immobilier (DPE)
Frais postaux
Refacturations & revenus accessoires
Autres produits
Service bancaires et assimile
```

**Mécanisme du danger** : une charge réelle sort du compte en banque (l'actif
baisse, car le compte bancaire = solde du dernier relevé) mais n'est comptée
nulle part au CR → le résultat n'est pas diminué → **le passif reste trop haut du
montant exact de la charge**. Aucun avertissement. C'est ainsi que les 358 € de
CFE ont déséquilibré Evry ce matin.

Le jour où Marseille paie sa PNO ou son CFE → même déséquilibre silencieux.

Incohérence de référentiel au passage : la ligne « Autres charges diverses »
pointe vers **deux catégories différentes** selon le bien — `Service bancaires et
assimile` (Evry) vs `Frais bancaires` (Marseille).

## 7. Code mort côté serveur

Toutes les affirmations ci-dessous ont été **revérifiées à la main** après l'audit.

### 7.1 L'ADR est factuellement faux — il bloque un nettoyage pour rien

`docs/workflow/ADR.md:355-358` justifie le report du drop des tables legacy ainsi :
« `allowed_mappings` reste une **whitelist de validation VIVANTE**
(`validate_mapping` interroge la table pour la classification manuelle) ».

**Les deux moitiés de cette phrase sont fausses aujourd'hui :**

1. `validate_mapping` n'interroge plus `allowed_mappings` — il délègue à
   `resolve_category` (référentiel `categories`/`category_groups`) :
   `mapping_obligatoire_service.py:46-67`.
2. `validate_mapping` **n'a aucun appelant en production** :

```
grep -rn "\bvalidate_mapping\b" backend --include="*.py" | grep -v /tests/
  -> mapping_obligatoire_service.py:46:def validate_mapping(...)     [sa propre def, rien d'autre]
```

→ **`mapping_obligatoire_service.py` est mort en entier** (ses 2 fonctions
publiques, `validate_mapping` et `validate_level3_value`, n'ont aucun appelant
prod). Sa suppression lève à elle seule le verrou du drop des tables legacy.
**ADR à corriger.**

### 7.2 Tables legacy — classes ORM déjà supprimées, tables encore pleines

```
mappings                    366 lignes    (classification_rules en a 370 : migration faite)
allowed_mappings            168 lignes    classe ORM ABSENTE de models.py
mapping_imports               3 lignes    classe ORM ABSENTE de models.py
compte_resultat_override      0 ligne     drop sans risque
```

`allowed_mappings` et `mapping_imports` n'ont **plus aucun mapper ORM** : ce sont
des tables physiques orphelines. `mappings` n'est plus lu que par
`backend/scripts/migrate_mappings_to_rules.py`, script one-shot déjà consommé.

### 7.3 ⚠️ Colonnes `level_1_values` — mortes ET activement toxiques

Les attributs ORM ont été retirés (`models.py:364` et `:463`) : SQLAlchemy ne lit
ni n'écrit plus ces colonnes. Mais **les colonnes physiques existent toujours**,
figées à leur valeur du jour du retrait — et elles mentent :

```
compte_resultat_mappings :
  id=87  bien=25  'Impôts et taxes'
     colonne (périmée) : ['Taxe foncière']
     liaison  (vérité) : ['Cotisation Foncière des Entreprises (CFE)', 'Taxe foncière']
  id=99  bien=26  'Travaux et mobilier'
     colonne (périmée) : ['Entretien et réparations']
     liaison  (vérité) : ['Entretien et réparations', 'Mobilier et équipements']
bilan_mappings : 0 désynchronisé
```

**Coût réel constaté** : lors du débogage du bilan Evry le 17/07, la lecture SQL
de cette colonne a fait conclure à tort que la CFE n'était rattachée à rien, et
envoyé l'investigation sur une fausse piste pendant 10 minutes. **À DROPper.**

⚠️ Ne PAS confondre avec `amortization_types.level_1_values` (`models.py:256`)
qui est **vivant et lu pour du calcul** (`amortization_service.py:178-179`,
`routes/amortization_types.py` filtres `IN`). Ne pas toucher.

### 7.4 Routes mortes

| Cible | Preuve |
|---|---|
| `backend/api/routes/example.py` — **fichier entier, 5 routes** | routeur **jamais enregistré** (`grep -c example backend/api/main.py` → **0**). Son docstring l'admet : « This is a template route file… or delete it » |
| `compte_resultat.py:438,468,502,557` — 4 routes Override | fonction retirée par le commit 3345ea9 côté frontend ; back laissé dormant. Table à 0 ligne |
| `compte_resultat.py:293` — GET /compte-resultat | aucun appelant |
| `logs.py:78` — GET /logs/frontend | le front n'appelle qu'en POST (`logger.ts:67`) |
| `prorata_forecast.py:135,167,202` — POST/PUT/DELETE /forecast-configs | le front passe exclusivement par `/forecast-configs/bulk` |
| 14 routes unitaires (`GET /transactions/{id}`, `POST /transactions`, `GET /properties/{id}`, `POST /bilan/calculate`, `GET /bilan`, `PUT /rules/{id}`, …) | fonction cliente existante, **0 appelant composant** |

⚠️ Le **GET** `/bilan/calculate` (`bilan.py:397`) est **vivant** — seul le POST
(`bilan.py:464`) est mort. Ne pas confondre.

### 7.5 Client frontend appelant des routes INEXISTANTES (404 garanti)

Aucun fichier `backend/api/routes/mappings.py` ni `enrichment.py` n'existe, et
rien n'est monté sur ces préfixes :

- `client.ts:607-1094` — `mappingsAPI` (~490 lignes, 24 méthodes)
- `client.ts:412-444` — `enrichmentAPI`

→ **~530 lignes de client mort pointant vers du vide.** 0 appelant composant, ce
qui explique que personne ne s'en soit aperçu.

### 7.6 Services sans appelant

| Cible | Statut |
|---|---|
| `mapping_obligatoire_service.py` — module entier | mort (§7.1) |
| `prorata_service.py:287` — `get_forecast_for_year` | mort, 0 test |
| `enrichment_service.py:100` — `enrich_all_transactions` | 0 appelant prod, 0 test. ⚠️ **dangereuse** : re-classe tout et remet à NULL ce qu'aucune règle ne rattrape → écrase les classements manuels |
| `amortization_service.py:255` — `validate_amortization_sum` | mort en prod, retenu par un test seul |
| `enrichment_service.py:141` — `update_transaction_classification` | mort en prod, retenu par 4 tests |

### 7.7 Autres reliquats

- **`backend/database/schema.sql` n'est jamais exécuté** (la création passe par
  `Base.metadata`, `connection.py:13`). Il déclare 4 tables qui n'existent ni en
  ORM ni en base : `parameters`, `amortizations`, `financial_statements`,
  `consolidated_financial_statements`. Fichier trompeur, référencé par 3 README.
- **2 fichiers `.db` de 0 octet** : `./lmnp.db` et `./backend/database.db`. La
  vraie base est `backend/database/lmnp.db` (1,9 Mo). Tout `sqlite3 lmnp.db`
  lancé à la racine ouvre une base VIDE.
- **~24 scripts one-shot** déjà consommés dans `backend/scripts/` (migrations
  appliquées, correctifs d'incidents clos, scripts de debug datés).
  **À conserver** : `golden_master.py`, `check_rules_no_regression.py` (appelé par
  `test_no_regression_check.py`), `fix_amortization_evry.py` (verrouillé par
  `test_amortization_evry_golden.py`).

### 7.8 Ordre de démantèlement (dépendances)

1. Supprimer `mapping_obligatoire_service.py` + ses 3 tests → **lève la
   justification ADR**
2. DROP `allowed_mappings`, `mapping_imports`, `mappings` + `class Mapping`
   (`models.py:118`) + `Property.mappings` (`models.py:32`) + le script de
   migration + son test
3. Supprimer `mappingsAPI` + `enrichmentAPI` de `client.ts` (~530 lignes)
4. DROP `compte_resultat_override` (0 ligne) + 4 routes + modèle + relation +
   schémas + méthodes client
5. **DROP `compte_resultat_mappings.level_1_values` et
   `bilan_mappings.level_1_values`** (colonnes fantômes qui mentent)
6. Supprimer `backend/api/routes/example.py` + schémas `Example*`
7. Purger les ~24 scripts one-shot et les 2 `.db` de 0 octet
8. **Corriger `docs/workflow/ADR.md:355-358`**

## 8. Si la projection du bilan est rallumée un jour

Elle est cassée. Référence : le test du plan
(`docs/superpowers/plans/2026-07-10-bloc-a-chiffres-justes-temps-reel.md`),
écrit pour Evry, attend `1 282,78 €`. L'appli calculait `11 690,22 €` :

| Entrée | Plan | Appli |
|---|---|---|
| Réel N-1 | 2 540,72 | 2 540,72 ✅ |
| CR prévisionnel | 10 217,50 | 9 149,50 ❌ |
| Crédit annuel | 13 798,44 | **0,00** ❌ |
| Variation CCA | 2 323,00 | **0,00** ❌ |

- **Crédit annuel = 0** : `/api/loan-payments` pagine à 100 lignes sur 234, triées
  par date décroissante → la page 1 couvre 2033→2041, **2026 n'y est jamais**.
  `BilanTable.tsx:246` fait `creditData.items || []` et ne demande jamais la
  page 2. Marseille : même troncature (100 sur 492).
- **Variation CCA = 0** : la ligne du 05/01/2026 (2 323 €) n'est pas en base.
- Le test `__tests__/bilanProjection.test.ts` ne pouvait rien voir : **les quatre
  chiffres y sont tapés à la main**. Il teste l'addition, jamais le câblage.
  Même piège que les loyers Matera (cf. ERROR_INVESTIGATION.md).

**Défaut de conception à trancher** : même en corrigeant ces entrées, le bilan
projeté ne s'équilibre pas (écart résiduel calculé : **−3 452,79 €**, soit
−1,92 %). La projection remplace le compte bancaire **à l'actif** et ne touche
jamais au passif, qui garde le résultat réel. Les deux colonnes ne décrivent plus
la même année. Soit le passif doit être projeté lui aussi, soit la colonne
projetée n'a pas à être contrôlée pour l'équilibre.
