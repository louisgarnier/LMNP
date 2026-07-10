# Bloc A — Chiffres justes + temps réel : Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fiabiliser les chiffres (prêt Evry, amortissements, page config) puis supprimer les caches CR/Bilan pour un calcul temps réel, avec preuve par golden master.

**Architecture:** On fige d'abord un golden master (sorties HTTP des endpoints `/calculate` live, par propriété × année). On corrige ensuite les données (date du prêt, mappings d'amortissement validés contre les documents comptables de `docs/files/`), on re-fige un golden v2, puis on supprime les tables de cache `compte_resultat_data`/`bilan_data` au profit du calcul à la lecture (mémoïsé). Comparaison golden bloquante à chaque tâche.

**Tech Stack:** FastAPI + SQLAlchemy + SQLite (backend), pytest, Next.js/React (frontend), scripts Python autonomes dans `backend/scripts/`.

## Global Constraints

- **Chiffres 2023-2025 = référence au centime** ; écart 2021/2022 vs comptable toléré (on reproduit les chiffres actuels de l'app, spec §10).
- **Écarts autorisés uniquement** : équilibre bilan 2022-2025 (fix date prêt), dotations amortissement Evry (fix mappings, validées contre `docs/files/appartements/Evry/Immobilisations_Evry.pdf`), arrondis ≤ 1 centime.
- **Backup avant toute migration** : copie horodatée de `backend/database/lmnp.db` vers `backups/` (jamais purgé).
- **Aucun `except: print`** dans le code nouveau ou modifié — les erreurs remontent en HTTPException avec message exploitable.
- **Tests jamais contre la base de prod** : toute nouvelle suite utilise le conftest de la Tâche 3.
- Branche de travail : `refonte`. Commits format `[REFONTE] type: description`.
- Serveurs : backend port 8000, frontend port 3000 — toujours vérifier `lsof -nP -iTCP:<port> -sTCP:LISTEN` avant lancement.

---

### Task 1: Finaliser le WIP de la branche forecast (prévisions Bilan)

**Files:**
- Create: `frontend/src/utils/bilanProjection.ts`
- Modify: `frontend/src/components/BilanForecastCard.tsx`, `frontend/src/components/BilanTable.tsx`, `frontend/src/components/ProRataForecastCard.tsx`, `frontend/app/dashboard/etats-financiers/page.tsx`
- Test: `frontend/__tests__/bilanProjection.test.ts`

**Interfaces:**
- Produces: `computeCompteBancairePrevu(params: {reelN1: number, totalCrPrevisionnel: number, creditAnnuel: number, variationCca: number}): number` et `extractCategory(bilanData: BilanResponse, type: 'actif'|'passif', categoryName: string): number` — utilisées par BilanForecastCard ET BilanTable (une seule source de vérité).

- [ ] **Step 1: Écrire le test de la formule partagée**

```ts
// frontend/__tests__/bilanProjection.test.ts
import { computeCompteBancairePrevu } from '../src/utils/bilanProjection';

test('compte bancaire prévu = réel N-1 + CR prévisionnel - crédit annuel + variation CCA', () => {
  expect(computeCompteBancairePrevu({
    reelN1: 2540.72, totalCrPrevisionnel: 10217.50,
    creditAnnuel: 13798.44, variationCca: 2323.00,
  })).toBeCloseTo(1282.78, 2);
});
```

- [ ] **Step 2: Lancer le test — il doit échouer** — `cd frontend && npx jest __tests__/bilanProjection.test.ts` → FAIL (module inexistant).
- [ ] **Step 3: Créer `bilanProjection.ts`** en déplaçant la formule et `extractCategory` depuis `BilanForecastCard.tsx:68-82,270-271` (code identique, exporté, avec arrondi `Math.round(x*100)/100` sur le résultat).
- [ ] **Step 4: Refactorer les 3 composants** pour importer depuis `bilanProjection.ts` : supprimer les 5 duplications dans `BilanTable.tsx`, la copie dans `BilanForecastCard.tsx`, les branches mortes `bilan_actif`/`bilan_passif` de `ProRataForecastCard.tsx:207-209,322-335`, les `console.log` de debug, et corriger le libellé « Réinitialiser projections 2025 » → année dynamique `annee N-1`.
- [ ] **Step 5: Corriger l'incohérence de signe des prévisions CR** : dans la carte prévisions et les colonnes 2027/2028, les charges s'affichent en valeur absolue comme l'historique (le signe reste porté par la catégorie, pas par l'affichage).
- [ ] **Step 6: Vérifier** : `npx jest` (suite complète) PASS + `npm run build` PASS + lancement app et contrôle visuel de l'onglet Bilan (la carte et la colonne 2026 affichent la MÊME valeur projetée).
- [ ] **Step 7: Commit** — `[REFONTE] fix: prévisions bilan finalisées (formule unique, signes CR, nettoyage)`.

### Task 2: Script golden master (extraction + comparaison)

**Files:**
- Create: `backend/scripts/golden_master.py`
- Create: `docs/project/reference/golden/` (sorties JSON)

**Interfaces:**
- Produces: CLI `python3 backend/scripts/golden_master.py --extract --tag v1` (fige les sorties) et `--compare --tag v1` (diff au centime, exit 1 si écart hors tolérance). Consommé par toutes les tâches suivantes.

- [ ] **Step 1: Écrire le script.** Il appelle en HTTP (backend lancé sur 8000) pour chaque propriété (25, 15, 26) × année (2021-2028 si données) : `GET /api/compte-resultat/calculate`, `GET /api/bilan/calculate`, `GET /api/amortization/aggregated`, `GET /api/transactions?limit=1&sort=date_desc` (dernier solde), et normalise en JSON trié `{property_id: {year: {cr: {...}, bilan: {...}, amort: {...}}}}` arrondi à 2 décimales. `--compare` recharge le JSON taggé et affiche chaque différence `chemin: avant → après` ; tolérance 0,01 € par valeur ; exit code 1 si écart.
- [ ] **Step 2: Vérifier le backend lancé** (`lsof` puis santé `/health`), lancer `--extract --tag v1-avant-corrections`, vérifier que le JSON contient les valeurs connues (CR Evry 2025 produits = 23 803,02 ; bilan Evry 2025 ACTIF = 195 891,32).
- [ ] **Step 3: Contrôle d'idempotence** : `--compare --tag v1-avant-corrections` immédiat → zéro écart, exit 0.
- [ ] **Step 4: Commit** (script + JSON v1) — `[REFONTE] feat: golden master (extraction/comparaison des états au centime)`.

### Task 3: Harnais de tests isolé (conftest)

**Files:**
- Create: `backend/tests/conftest.py`
- Test: `backend/tests/test_conftest_isolation.py`

**Interfaces:**
- Produces: fixtures pytest `db_session` (SQLite en mémoire, schéma complet via `Base.metadata.create_all`) et `client` (TestClient FastAPI avec `app.dependency_overrides[get_db]`). AUCUN test ne touche plus `backend/database/lmnp.db`.

- [ ] **Step 1: Test d'isolation** : `test_conftest_isolation.py` crée une Property via `client`, vérifie qu'elle existe via l'API, puis vérifie que `backend/database/lmnp.db` n'a PAS changé (hash du fichier avant/après).
- [ ] **Step 2:** Le test échoue (pas de conftest) → écrire `conftest.py` (engine `sqlite:///:memory:` + `StaticPool`, override `get_db`) → le test passe.
- [ ] **Step 3: Commit** — `[REFONTE] test: harnais pytest isolé (fin des tests sur la base de prod)`.

### Task 4: Correction date du prêt Evry (équilibre bilan)

**Files:**
- Create: `backend/scripts/fix_loan_start_dates.py`
- Test: `backend/tests/test_capital_restant_du.py`

**Interfaces:**
- Consumes: `calculate_capital_restant_du(db, year, property_id)` (`bilan_service.py:359`).

- [ ] **Step 1: Backup** : `cp backend/database/lmnp.db "backups/lmnp_$(date +%F_%H%M)_avant-fix-pret.db"`.
- [ ] **Step 2: Test (harnais Tâche 3)** : un prêt dont `loan_start_date` est postérieure mais dont l'échéancier commence en 2021 doit déduire le capital dès 2021. Reproduire le bug : avec `loan_start_date=2026-05-08`, `calculate_capital_restant_du(db, 2023, pid)` ignore les paiements → test RED sur le comportement attendu.
- [ ] **Step 3: Corriger `calculate_capital_restant_du`** : un prêt est « actif » pour l'année N s'il a **au moins un `LoanPayment` ≤ 31/12/N** (la clause `loan_start_date` disparaît du filtre). Test GREEN.
- [ ] **Step 4: Corriger la donnée** : script `fix_loan_start_dates.py` → pour chaque `loan_configs`, `loan_start_date = MIN(loan_payments.date)` du prêt (Evry : 2021). Exécuter sur la vraie base (après backup Step 1).
- [ ] **Step 5: Vérifier l'équilibre** : backend relancé, `GET /api/bilan/calculate` Evry 2022-2025 → ACTIF = PASSIF (écart ≤ 0,01) pour chaque année. Capital restant dû 2025 attendu ≈ 194 613,53 (231 815 − 37 201,47) — à confronter aussi à `docs/files/appartements/Evry/Tableau_Ammort_Crédit_Evry.xlsx` (valeur au 31/12/2025).
- [ ] **Step 6: Golden** : `--extract --tag v2-apres-pret` puis `--compare` v1↔v2 : les SEULS écarts sont capital restant dû + totaux PASSIF/équilibre 2022-2025 (toutes propriétés avec échéancier). Consigner la liste dans `docs/project/reference/golden/ECARTS.md`.
- [ ] **Step 7: Commit** — `[REFONTE] fix: capital restant dû basé sur l'échéancier réel (bilan équilibré 2022-2025)`.

### Task 5: Remise à plat des amortissements Evry (validée documents)

**Files:**
- Create: `backend/scripts/fix_amortization_evry.py`
- Modify: données `amortization_types` / `amortization_results` (property 25)
- Test: `backend/tests/test_amortization_evry_golden.py`

**Interfaces:**
- Consumes: `recalculate_all_amortizations(db, property_id)` (`amortization_service.py:225`), `calculate_yearly_amounts` (30/360).

- [ ] **Step 1: Extraire la vérité des documents** : lire `docs/files/appartements/Evry/Immobilisations_Evry.pdf` (+ xlsx Marseille pour le format) → tableau {composant, base amortissable, durée, date de début, dotation annuelle, part terrain}. Croiser avec la liasse 2024 (2033-A : immobilisations brutes 358 445, amortissements cumulés 35 753 — ce sont les 3 apparts consolidés). Documenter l'extraction dans le script (constantes commentées avec référence page/document).
- [ ] **Step 2: Backup** : copie horodatée de la base.
- [ ] **Step 3: Script de correction** : recrée les `amortization_types` d'Evry conformes aux documents (bon composant → bonnes valeurs level_1, durées et dates du tableau, part terrain en `duration=0`), supprime TOUS les `amortization_results` orphelins ou périmés d'Evry (y compris ceux dont la transaction n'existe plus ou n'est plus classée en Immobilisations), puis `recalculate_all_amortizations(db, 25)`.
- [ ] **Step 4: Test golden dotations** : test (base réelle en lecture seule, pas le harnais mémoire) qui compare les dotations recalculées par année aux annuités du tableau d'immobilisations (tolérance 0,01, première année prorata 30/360 acceptée selon le document). Vérifier aussi Marseille/Marseille colloc contre leurs xlsx — si écart, le documenter SANS corriger (hors périmètre Evry, à traiter au checkpoint).
- [ ] **Step 5: Golden v3** + mise à jour `ECARTS.md` (écarts = lignes Charges d'amortissements du CR Evry + Amortissements cumulés du bilan Evry, justifiés par le document).
- [ ] **Step 6: Commit** — `[REFONTE] fix: amortissements Evry réalignés sur le tableau d'immobilisations`.

### Task 6: Fix rechargement config page Amortissements

**Files:**
- Modify: `frontend/src/components/AmortizationConfigCard.tsx` (chargement initial)
- Test: `frontend/__tests__/amortizationConfig.test.tsx`

- [ ] **Step 1:** Identifier pourquoi le dropdown « Level 2 » revient à vide alors que 7 types existent (probable : état initial non hydraté depuis `GET /api/amortization-types?property_id=`). Écrire un test RTL qui monte le composant avec un mock API renvoyant les 7 types d'Evry et vérifie que le select affiche « Immobilisations » et le tableau les 7 lignes.
- [ ] **Step 2:** Corriger l'hydratation (useEffect de chargement au montage + à chaque changement de propriété). Test PASS. Vérification visuelle dans l'app.
- [ ] **Step 3: Commit** — `[REFONTE] fix: la page Amortissements recharge la configuration existante`.

### Task 7: Étape 1 — calcul à la lecture (suppression des caches)

**Files:**
- Modify: `backend/api/routes/compte_resultat.py` (GET principal → calcul live), `backend/api/routes/bilan.py` (idem + mémo CR par année), `backend/api/services/bilan_service.py` (accepte `cr_cache: dict`), `backend/api/routes/transactions.py` + `loan_payments.py` (suppression des appels d'invalidation)
- Delete: endpoints `/generate`, modèles `CompteResultatData`/`BilanData`, fonctions `invalidate_*`
- Modify: `frontend/src/api/client.ts` + composants appelant `/generate`
- Test: `backend/tests/test_realtime_states.py`

**Interfaces:**
- Produces: `GET /api/compte-resultat` et `GET /api/bilan` renvoient le MÊME schéma JSON qu'avant (contrat HTTP inchangé pour le frontend) mais calculé à la demande. `calculate_bilan(db, year, property_id, cr_cache=None)` — `cr_cache: dict[int, dict]` partagé sur une requête multi-années.

- [ ] **Step 1: Test de non-régression du contrat** (harnais isolé) : seed minimal (1 propriété, 6 transactions classées sur 2 ans, 1 prêt, 1 type d'amortissement), snapshot du JSON `GET /api/compte-resultat` et `GET /api/bilan` AVANT modification (les endpoints cache), sauvegardé en fixture.
- [ ] **Step 2: Basculer les GET sur le calcul live** en réutilisant les fonctions des endpoints `/calculate` ; supprimer `/generate` ; adapter le frontend (suppression des appels generate + boutons associés). Le test Step 1 doit rendre un JSON identique à la fixture.
- [ ] **Step 3: Mémoïsation** : `calculate_bilan` reçoit `cr_cache` ; la route bilan multi-années le remplit une fois par année (brancher ce que `bilan.py:430-432` préparait sans l'utiliser). Test de perf : bilan 6 ans × Evry < 300 ms (mesuré dans `test_realtime_states.py` sur copie de la vraie base).
- [ ] **Step 4: Suppression du code d'invalidation** (`invalidate_compte_resultat_*`, `invalidate_bilan_*` et tous leurs appels — le bug B1 disparaît avec le concept) + migration `backend/scripts/drop_cache_tables.py` (backup, `DROP TABLE compte_resultat_data, bilan_data`).
- [ ] **Step 5: Golden final** : `--compare` v3 → zéro écart (le passage au live ne change AUCUN chiffre). E2E manuel : modifier une transaction dans l'UI → le CR affiché reflète le changement immédiatement, sans action.
- [ ] **Step 6: Commit** — `[REFONTE] feat: états financiers calculés en temps réel (suppression caches et invalidation)`.

### Task 8: Clôture Bloc A

- [ ] **Step 1:** `pytest backend/tests` complet PASS + `npx jest` PASS + `npm run build` PASS.
- [ ] **Step 2:** Mettre à jour `docs/workflow/ERRORS.md` (bug date de prêt, mappings croisés, caches — avec règles de prévention) et `docs/workflow/ADR.md` (décision calcul-à-la-lecture, décision activité-prêt-par-échéancier).
- [ ] **Step 3:** Rapport de checkpoint pour Louis : liste des écarts golden v1→v3 (`ECARTS.md`), captures avant/après du bilan équilibré, état des tests. Commit final — `[REFONTE] docs: clôture Bloc A (chiffres justes + temps réel)`.

---

## Self-review (fait à l'écriture)

- **Couverture spec** : §10 golden+backups (T2, steps backup), §6 temps réel (T7), étape 0 complète (T4-T6), pré-travail forecast (T1). Les étapes 2-6 du spec relèvent des plans Blocs B/C/D (à écrire après validation Bloc A).
- **Types cohérents** : `computeCompteBancairePrevu` (T1) réutilisé nulle part ailleurs dans ce bloc ; `cr_cache` défini T7 step 3 et utilisé T7 uniquement.
- **Placeholders** : néant — chaque étape a code, commande ou critère chiffré.
