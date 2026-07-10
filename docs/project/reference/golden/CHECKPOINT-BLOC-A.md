# Checkpoint Bloc A — chiffres justes + temps réel

**Date** : 2026-07-10
**Branche** : `refonte`
**Statut** : Bloc A fonctionnellement complet (Tasks 1-7 committées), clôturé par cette tâche (Task 8).

Ce document répond à trois questions pour Louis : qu'est-ce qui a changé
dans les chiffres (et pourquoi c'était nécessaire), où en est l'équilibre
du bilan aujourd'hui, et qu'est-ce qui reste ouvert / à trancher.

---

## 1. Trajectoire golden master v1 → v2 → v3

Le golden master (`backend/scripts/golden_master.py`) extrait un instantané
au centime de tous les états financiers (CR, bilan, amortissements) pour
les 3 propriétés (Evry=25, mars=15, mars colloc=26) et compare deux
versions ligne à ligne, par clé stable. Trois versions ont été prises
pendant le Bloc A :

| Tag | Quand | Contenu |
|---|---|---|
| `v1-avant-corrections` | avant Task 4 | état de référence initial |
| `v2-apres-pret` | après Task 4 | après fix capital restant dû |
| `v3-apres-amortissements` | après Task 5 | après réalignement amortissements Evry |
| (état courant) | après Task 7 | calcul à la lecture — reverifié **zéro écart** vs v3 |

### v1 → v2 (Task 4) : 24 écarts — fix de la date de départ du prêt Evry

**Cause** : `calculate_capital_restant_du` considérait un prêt « actif »
via `LoanConfig.loan_start_date` (config saisie séparément), pas via
l'échéancier réel (`LoanPayment`). Pour Evry, cette date valait
2026-05-08 alors que le premier paiement réel est de 2021 — le capital
remboursé n'était donc jamais déduit pour 2022-2025.

**Résultat** : 24 diffs, toutes sur Evry (property 25), années 2022-2025,
6 lignes par année (capital restant dû, total « Dettes financières »,
total PASSIF, `passif_total`, `difference`, `difference_percent`) :

| Année | Capital restant dû AVANT (v1) | APRÈS (v2) | Bilan `difference` AVANT | APRÈS |
|---|---|---|---|---|
| 2022 | 231 815,00 € | 229 000,31 € | -2 814,69 € | ≈ 0 |
| 2023 | 231 815,00 € | 217 663,85 € | -14 151,15 € | ≈ 0 |
| 2024 | 231 815,00 € | 206 202,05 € | -25 612,95 € | ≈ 0 |
| 2025 | 231 815,00 € | **194 613,53 €** | -37 201,47 € | ≈ 0 |

La valeur 2025 (194 613,53 €) est vérifiée au centime contre le tableau
d'amortissement Excel documentaire
(`docs/files/appartements/Evry/Tableau_Ammort_Crédit_Evry.xlsx`, solde
après le paiement du 15/12/2025). Aucun autre écart (CR, amortissements,
autres propriétés) — détail complet et justification ligne par ligne dans
`ECARTS.md` (section « v1-avant-corrections → v2-apres-pret »).

### v2 → v3 (Task 5) : 48 écarts — RENOMMAGE des catégories d'amortissement Evry, pas un changement de chiffres

**Cause** : `amortization_types` d'Evry était une copie défectueuse du
gabarit Marseille — les NOMS de composant ne correspondaient pas à leur
`level_1` réellement mappé (ex. le type nommé « agencements » était en
réalité la construction), et 3 types orphelins (`level_1_values == []`)
polluaient la table. Les durées/dates/montants documentaires étaient
**déjà corrects** (annuité pleine totale 11 119,148 €/an, base
amortissable 188 191,48 €, conformes au PDF d'immobilisations).

**Résultat** : 48 diffs, toutes sur `25.<année>.amort.categories`
(2021-2028), un pur renommage à montant identique :

| Ancienne catégorie (v2) | Nouvelle catégorie (v3) | Montant pleine (inchangé) |
|---|---|---|
| Immobilisation agencements | Immeuble (hors terrain) | -3 850,00 €/an |
| Immobilisation mobilier | Travaux de rénovation, gros œuvre | -5 406,99 €/an |
| Immobilisation Facade/Toiture | Mobilier & électroménager | -1 862,15 €/an |

**Aucun** écart sur `cr.charges["Charges d'amortissements"]`, sur
`bilan...["Amortissements cumulés"]`, sur les autres propriétés, ni sur le
capital restant dû ou les totaux/résultats — zéro fuite hors du bloc
`amort.categories`. Détail dans `ECARTS.md` (section « v2 → v3 »).

### v3 → état courant (Task 7) : calcul à la lecture, zéro écart

Task 7 a supprimé les caches CR/Bilan persistés (jamais correctement
peuplés/invalidés — voir ADR-001 dans `docs/workflow/ADR.md`) et fait
calculer les `GET` en direct. Le golden master a été recomparé **après**
cette bascule : **« Aucune différence détectée »** (revérifié à nouveau
pendant cette tâche de clôture, Task 8, ci-dessous). La migration ne
change aucun chiffre, uniquement le chemin de calcul.

---

## 2. Équilibre du bilan Evry — avant / après

**Avant Task 4** : le bilan Evry (property_id=25) était déséquilibré pour
toutes les années 2022-2025 (ACTIF ≠ PASSIF), avec un écart croissant
d'année en année :

| Année | ACTIF (v1=v2, inchangé) | PASSIF (v1, AVANT fix) | Écart (v1) |
|---|---|---|---|
| 2022 | 242 417,61 € | 245 232,30 € | -2 814,69 € (-1,15 %) |
| 2023 | 221 142,74 € | 235 293,89 € | -14 151,15 € (-6,01 %) |
| 2024 | 208 421,78 € | 234 034,73 € | -25 612,95 € (-10,94 %) |
| 2025 | 195 891,32 € | 233 092,79 € | -37 201,47 € (-15,96 %) |

**Après Task 4** (fix capital restant dû) :

| Année | ACTIF | PASSIF | Écart |
|---|---|---|---|
| 2022 | 242 417,61 € | 242 417,61 € | ≈ 0 |
| 2023 | 221 142,74 € | 221 142,74 € | ≈ 0 |
| 2024 | 208 421,78 € | 208 421,78 € | ≈ 0 |
| 2025 | 195 891,32 € | 195 891,32 € | ≈ 0 |

**Capital restant dû (Emprunt bancaire) 2025 = 194 613,53 €**, vérifié au
centime contre le tableau d'amortissement Excel
(`Tableau_Ammort_Crédit_Evry.xlsx`, solde après le dernier paiement 2025).

**Vérifié visuellement pendant cette tâche** (voir §4) : le bilan Evry
reste équilibré aujourd'hui pour les 6 colonnes affichées (2021-2026),
« Équilibre respecté ✓ » partout dans l'UI, avec les mêmes valeurs
exactes qu'ci-dessus pour 2022-2025.

---

## 3. Ouverts pour décision

Ces points sont **documentés, non corrigés** — hors périmètre des tâches
qui les ont identifiés, à trancher par Louis :

1. **Marseille colloc (26) non rapproché avec son xlsx.**
   `Tablea_Immo_Mars_colloc.xlsx` est ambigu (deux scénarios « matera »
   divergents, dates exprimées en ratios 0,12/0,55 plutôt qu'en dates
   réelles) et les annuités en base ne correspondent à NI l'un NI l'autre
   scénario (ex. structure/GO : DB 613,47 € vs xlsx 1 887,60 € ou
   1 657,50 €). Non corrigé en Task 5 (hors périmètre Evry). **Nécessite
   une source documentaire non ambiguë avant toute correction.**

2. **Écart mars colloc 2025 = 0,75 €.** Écart de bilan pré-existant,
   présent identiquement dans golden v1 et v2, sans rapport avec le fix
   `loan_start_date` (déjà correcte pour cette année dans les deux
   versions). Jamais aggravé ni corrigé par le Bloc A. Cause non
   investiguée.

3. **Écarts forecast 2026** pour mars (3 506,85 €) et mars colloc
   (643,95 €) — imbalances du bilan sur la colonne prévisionnelle/en
   cours 2026, documentées dans `ECARTS.md` comme hors périmètre de la
   Tâche 4 (« équilibre bilan 2022-2025 » uniquement, pas 2026).

4. **Nouveau, observé pendant cette tâche (Task 8), non investigué** : en
   vérifiant visuellement le tab Bilan pour Evry (property 25), la bannière
   globale « ⚠️ Attention : Le bilan n'est pas équilibré » s'affiche sous
   le tableau **alors que les 6 colonnes visibles (2021-2026) affichent
   toutes individuellement « Équilibre respecté ✓ »**. Le code
   (`frontend/src/components/BilanTable.tsx:791-806`) recalcule
   `actif_total - passif_total` pour CHAQUE année de l'état `years` avec
   une tolérance de 0,01 % du total ACTIF (~20 € pour Evry) — plus
   large que le seuil utilisé pour l'indicateur par colonne. Cause
   possible : un léger écart résiduel sur une année de l'état interne
   (2027/2028 non affichées, ou arrondi d'affichage masquant un écart
   sous le centime visible) qui dépasse quand même 0,01 % du total. Golden
   master reconfirmé « zéro écart » avant et après cette observation (le
   backend n'a pas été touché pendant Task 8), donc **ce n'est pas une
   régression introduite par cette tâche** — mais c'est un signal
   d'UI potentiellement trompeur, non exploré plus avant (hors périmètre
   du check visuel demandé, qui portait sur la concordance carte/colonne
   2026, confirmée exacte — voir §4). À investiguer si Louis le juge
   prioritaire.

---

## 4. Vérification visuelle carte == colonne (Bilan, 2026)

Backend (`:8000`, `GET /health` → 200) et frontend (`:3000`) démarrés/
réutilisés pour cette vérification (voir rapport Task 8 pour le détail).
Onglet Bilan, propriété Evry, catégorie « Compte bancaire » :

| Source | Valeur 2026 |
|---|---|
| Colonne « 2026 (projeté) » du tableau Bilan | **1 013,20 €** |
| Carte « Prévisions annuelles - Bilan » → ligne Compte bancaire → « Prévu 2026 » | **1 013,20 €** |

**Identiques.** Vérifié via un snapshot d'accessibilité Chrome DevTools
(pas seulement une capture d'écran) sur la page réelle, propriété active
Evry (id=25).

---

## 5. État des tests (Task 8)

- **Backend** (`python3 -m pytest backend/tests/`) : **32 passed, 137
  skipped, 0 failed, 0 error.** Les skips sont la quarantaine
  attendue (tests hérités touchant la base de PRODUCTION directement, ou
  scripts « manuels » codant en dur un serveur local — voir
  `docs/workflow/ADR.md` ADR-003 et `docs/workflow/ERROR_INVESTIGATION.md`).
- **Frontend** (`npx jest`) : **3 suites, 6 tests, 0 failed.**
- **Build** (`npm run build`) : succès, 8/8 pages générées.
- **Golden master** : zéro écart vs `v3-apres-amortissements`, reconfirmé
  pendant cette tâche après les changements de tests/docs (aucun code de
  calcul modifié dans Task 8).

Détail complet (fichiers touchés, décisions test_database.py/
example.test.tsx/jest.config.js racine, quasi-incident
`dependency_overrides`) dans le rapport de la tâche :
`.superpowers/sdd/task-8-report.md`.
