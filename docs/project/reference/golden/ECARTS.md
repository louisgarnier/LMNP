# Écarts golden master — v2-apres-pret → v3-apres-amortissements

Contexte : Tâche 5 (Bloc A), remise à plat des amortissements Evry
(`property_id=25`) via `backend/scripts/fix_amortization_evry.py`, validée
contre `docs/files/appartements/Evry/Immobilisations_Evry.pdf` (page 1).

**Nature du correctif : ré-étiquetage + nettoyage, PAS un changement de
chiffres.** Les `amortization_types` d'Evry étaient une copie défectueuse du
gabarit Marseille : les NOMS de composant (utilisés comme `category` dans
`amortization_results`) ne correspondaient plus à la valeur `level_1` mappée,
et 3 types « orphelins » (`level_1_values == []`) polluaient la table. Les
DURÉES, DATES et MONTANTS étaient déjà corrects (annuité pleine totale
11 119,148 €/an, base amortissable 188 191,48 € — conformes au document).
Le script recrée 4 types propres (un par catégorie `level_1` réellement
utilisée : Terrain 0 an, Immeuble 30 ans, Travaux 10 ans, Mobilier 10 ans),
supprime les types orphelins et régénère les résultats avec les bons libellés.

Commande utilisée pour produire la comparaison :

```
python3 backend/scripts/fix_amortization_evry.py --yes
python3 backend/scripts/golden_master.py --extract --tag v3-apres-amortissements
python3 backend/scripts/golden_master.py --compare --tag v2-apres-pret
```

Résultat : **48 différences détectées, TOUTES sur la propriété 25 (Evry),
années 2021-2028, exclusivement dans le bloc `amort.categories`** (6 par
année × 8 années). Ce sont des RENOMMAGES de catégorie : le montant est
préservé, il migre simplement vers la clé au bon nom. Aucune autre ligne
n'est impactée — en particulier `cr.charges["Charges d'amortissements"]`
(CR Evry) et `bilan...["Amortissements cumulés"]` (bilan Evry) restent
NUMÉRIQUEMENT IDENTIQUES (ils étaient déjà conformes au document ; c'est
pourquoi ils n'apparaissent PAS dans le diff). Aucun écart sur les autres
propriétés (mars=15, colloc=26), ni sur le capital restant dû, ni sur les
totaux/résultats. Conforme à l'attendu de la Tâche 5 (aucune fuite).

## Détail des écarts acceptés — renommage des catégories d'amortissement Evry

Le même renommage s'applique à l'identique pour chaque année 2021→2028.
Correspondance ancienne clé (nom gabarit erroné) → nouvelle clé (composant
documentaire), montant inchangé :

| Ancienne catégorie (v2) | Nouvelle catégorie (v3) | Composant documentaire | Durée | Justification |
|---|---|---|---|---|
| `Immobilisation agencements` | `Immeuble (hors terrain)` | Compte 21300000 CONSTRUCTIONS (ligne 07) | 30 ans | Le libellé « agencements » ne correspondait pas à la construction ; `level_1 = "Immeuble (hors terrain)"`. Montant inchangé (-3 850 €/an pleine). |
| `Immobilisation mobilier` | `Travaux de rénovation, gros œuvre` | Compte 21810000 (lignes 01/02/04 TRAVAUX) | 10 ans | Le libellé « mobilier » masquait des travaux ; `level_1 = "Travaux…"`. Montant inchangé (-5 406,99 €/an pleine). |
| `Immobilisation Facade/Toiture` | `Mobilier & électroménager` | Compte 21810000 (lignes 03/05 LAVE LINGE, SERRURE + mobilier) | 10 ans | Le libellé « Facade/Toiture » masquait du mobilier ; `level_1 = "Mobilier & électroménager"`. Montant inchangé (-1 862,15 €/an pleine). |

Exemple (année pleine, ex. 2024) — 6 lignes de diff : les 3 anciennes clés
disparaissent (`→ <absent>`) et les 3 nouvelles apparaissent avec le MÊME
montant. Total `amort` inchangé (-11 119,148 €), donc CR et bilan stables.

Les premières années (2021 : -331,53 construction + -300,97 travaux ;
2022 : proratas) migrent de la même façon, montants préservés. Ces proratas
2021/2022 diffèrent des « Amort. Prat. » cumulés du document (10 081,98 €
fin 2022) car la base contient une transaction travaux datée 2021-12-01
(-36 115,83 €) absente des lignes documentaires 2022 ; écart 2021/2022
explicitement toléré par le plan (« chiffres 2023-2025 = référence au
centime »). Les années pleines 2023-2025 sont, elles, au centime.

## Vérification croisée Marseille / Marseille colloc (hors périmètre Evry)

- **Marseille (15)** : dotations recalculées CONFORMES à son xlsx
  `Tablea_Immo_Mars_abnb.xlsx` (année pleine 2025 = 6 157,28 €, chaque
  catégorie au centime : structure/GO 807,50 · mobilier 750,62 · IGT
  1 076,67 · agencements 1 615,00 · Facade/Toiture 807,50 · travaux
  1 100,00). Verrouillé par `test_marseille_dotations_conformes_xlsx`. Aucun
  correctif nécessaire.
- **Marseille colloc (26)** : la source `Tablea_Immo_Mars_colloc.xlsx` est
  AMBIGUË (deux scénarios « matera » divergents, dates exprimées en ratios
  0,12 / 0,55 plutôt qu'en dates réelles) et les annuités DB ne correspondent
  à NI l'un NI l'autre scénario (ex. DB structure/GO 613,47 vs xlsx 1 887,60
  ou 1 657,50 ; agencements 1 673,10 vs 5 148 ou 3 315). **Écart documenté,
  NON corrigé** (hors périmètre Task 5 Evry ; à arbitrer au checkpoint avec
  une source documentaire non ambiguë). Non testé ici volontairement.

---

# Écarts golden master — v1-avant-corrections → v2-apres-pret

Contexte : Tâche 4 (Bloc A), correction de `calculate_capital_restant_du`
(`backend/api/services/bilan_service.py`) — un prêt est désormais considéré
« actif » pour l'année N s'il a au moins un `LoanPayment` daté au plus tard
le 31/12/N, indépendamment de `LoanConfig.loan_start_date` (qui était erronée
pour le prêt Evry : 2026-05-08 alors que l'échéancier réel démarre en 2021).
La donnée `loan_start_date` a ensuite été recalée sur `MIN(LoanPayment.date)`
pour tous les prêts via `backend/scripts/fix_loan_start_dates.py`.

Commande utilisée pour produire la comparaison :

```
python3 backend/scripts/golden_master.py --extract --tag v2-apres-pret
python3 backend/scripts/golden_master.py --compare --tag v1-avant-corrections
```

Résultat : **24 différences détectées, toutes sur la propriété 25 (Evry),
années 2022-2025**, réparties en 6 lignes par année (capital restant dû,
totaux PASSIF, équilibre). Aucune autre ligne (CR, amortissements, détails
ACTIF, autres propriétés) n'est impactée — conforme à l'attendu de la
Tâche 4.

## Détail des écarts acceptés

### Année 2022 (property_id=25, Evry)
| Chemin | v1 (stocké) | v2 (actuel) | Justification |
|---|---|---|---|
| `bilan.types[PASSIF].sub_categories[Dettes financières].categories[Emprunt bancaire (capital restant dû)].amount` | 231 815,00 | 229 000,31 | Fix date prêt : capital remboursé (échéancier réel dès 2021) désormais déduit du montant du crédit accordé. |
| `bilan.types[PASSIF].sub_categories[Dettes financières].total` | 231 815,00 | 229 000,31 | Conséquence directe de la ligne ci-dessus (seule catégorie de la sous-catégorie). |
| `bilan.types[PASSIF].total` | 245 232,30 | 242 417,61 | Conséquence directe (capital restant dû fait partie du total PASSIF). |
| `bilan.passif_total` | 245 232,30 | 242 417,61 | Idem. |
| `bilan.difference` | -2 814,69 | -0,0 | Équilibre bilan rétabli (ACTIF = PASSIF, écart ≤ 0,01 €). |
| `bilan.difference_percent` | -1,15 % | -0,0 % | Conséquence de l'équilibre rétabli. |

### Année 2023 (property_id=25, Evry)
| Chemin | v1 (stocké) | v2 (actuel) | Justification |
|---|---|---|---|
| `...Emprunt bancaire (capital restant dû)].amount` | 231 815,00 | 217 663,85 | Fix date prêt. |
| `...Dettes financières].total` | 231 815,00 | 217 663,85 | Conséquence directe. |
| `bilan.types[PASSIF].total` | 235 293,89 | 221 142,74 | Conséquence directe. |
| `bilan.passif_total` | 235 293,89 | 221 142,74 | Idem. |
| `bilan.difference` | -14 151,15 | -0,0 | Équilibre bilan rétabli. |
| `bilan.difference_percent` | -6,01 % | -0,0 % | Conséquence de l'équilibre rétabli. |

### Année 2024 (property_id=25, Evry)
| Chemin | v1 (stocké) | v2 (actuel) | Justification |
|---|---|---|---|
| `...Emprunt bancaire (capital restant dû)].amount` | 231 815,00 | 206 202,05 | Fix date prêt. |
| `...Dettes financières].total` | 231 815,00 | 206 202,05 | Conséquence directe. |
| `bilan.types[PASSIF].total` | 234 034,73 | 208 421,78 | Conséquence directe. |
| `bilan.passif_total` | 234 034,73 | 208 421,78 | Idem. |
| `bilan.difference` | -25 612,95 | -0,0 | Équilibre bilan rétabli. |
| `bilan.difference_percent` | -10,94 % | -0,0 % | Conséquence de l'équilibre rétabli. |

### Année 2025 (property_id=25, Evry)
| Chemin | v1 (stocké) | v2 (actuel) | Justification |
|---|---|---|---|
| `...Emprunt bancaire (capital restant dû)].amount` | 231 815,00 | 194 613,53 | Fix date prêt. Valeur conforme à l'ancre attendue (≈194 613,53 €) et au tableau d'amortissement `docs/files/appartements/Evry/Tableau_Ammort_Crédit_Evry.xlsx` (colonne capital restant dû après paiement du 15/12/2025 = ligne du 15/01/2026 = 194 613,53). |
| `...Dettes financières].total` | 231 815,00 | 194 613,53 | Conséquence directe. |
| `bilan.types[PASSIF].total` | 233 092,79 | 195 891,32 | Conséquence directe. |
| `bilan.passif_total` | 233 092,79 | 195 891,32 | Idem — désormais égal à `actif_total` (195 891,32). |
| `bilan.difference` | -37 201,47 | -0,0 | Équilibre bilan rétabli. |
| `bilan.difference_percent` | -15,96 % | -0,0 % | Conséquence de l'équilibre rétabli. |

## Propriétés sans écart (mars=15, mars colloc=26)

Ces deux propriétés ont également des `loan_configs`/`loan_payments` et ont
vu leur `loan_start_date` recalée par `fix_loan_start_dates.py`, mais
n'affichent AUCUN écart golden v1↔v2 : leur ancienne `loan_start_date`
(ex: 2024-03-12 pour mars, 2025-09-04 / 2024-09-04 pour mars colloc) était
déjà antérieure ou égale au 31/12 de chaque année couverte par le golden
(2021-2028) là où ces propriétés ont des données (`is_cr_empty` filtre les
années sans transaction) — le bug de filtrage sur `loan_start_date` ne
changeait donc rien pour elles sur la plage observée. Confirmé par
`bilan.difference` déjà à 0 (ou écart pré-existant hors périmètre, voir
ci-dessous) dans golden v1 pour ces deux propriétés sur 2022-2025.

## Écarts pré-existants HORS périmètre (non touchés, non golden-comparés ici)

Deux écarts de bilan pré-existent dans golden v1 (avant toute correction
Tâche 4) et restent identiques en v2 (donc n'apparaissent pas dans le diff
`--compare`, puisqu'ils n'ont pas changé) :
- `26.2025.bilan.difference = 0.75` (mars colloc, 2025) — écart de
  0,75 €, sans rapport avec `loan_start_date` (déjà correcte pour l'année
  2025 dans les deux versions). Hors périmètre de la Tâche 4.
- `15.2026.bilan.difference = 3506.85` et `26.2026.bilan.difference =
  643.95` — années 2026 (prévisionnel), hors périmètre "équilibre bilan
  2022-2025" de la Tâche 4.

Ces deux écarts ne sont PAS couverts par la contrainte "chiffres 2023-2025
= référence au centime" (qui porte sur Evry) et ne sont pas introduits ni
aggravés par cette tâche — ils préexistaient dans golden v1 à l'identique.
Aucune action prise sur eux ici ; à traiter dans une tâche dédiée si besoin.

---

# `v3-apres-amortissements` → `v4-etape2-referentiel` (Étape 2) : **0 écart**

**0 écart — l'étape 2 ne change aucun chiffre** (référentiel + IDs +
centimes à output identique).

L'étape 2 est une refonte **structurelle** de la classification et du
stockage, à sortie financière strictement inchangée :
- référentiel global `category_groups`/`categories` + bascule des
  lectures/écritures sur `transactions.category_id`, puis suppression de
  `enriched_transactions` (ADR-004) ;
- configs CR/Bilan liées par `category_id` + `line_code` stables, libellés
  résolus au bord (ADR-005) ;
- montants stockés en **centimes entiers** via `EuroCents` (11/12 colonnes ;
  `amortization_results.amount` laissé Float, cf. déviation ci-dessous) (ADR-006).

**Preuve** : `python3 backend/scripts/golden_master.py --compare --tag
v3-apres-amortissements` → « Aucune différence détectée ». Vérification
indépendante : `golden-v3-apres-amortissements.json == golden-v4-etape2-referentiel.json`
(égalité stricte des dicts Python sur les 17 combinaisons propriété × année ;
seule différence de sérialisation JSON = zéro signé `-0.0` vs `0.0` sur les
champs `difference`/`difference_percent` déjà nuls, valeur identique).

**Snapshot figé** : `docs/project/reference/golden/golden-v4-etape2-referentiel.json`
(17 combos : Evry 25 × 8 ans 2021-2028, mars 15 × 5 ans 2024-2028, mars
colloc 26 × 4 ans 2025-2028).

**Déviation spec à noter (non un écart golden)** :
`amortization_results.amount` reste en `Float` (et non en centimes entiers)
car ses valeurs dérivées sous le centime (ex. `-643,7569`), arrondies,
feraient dériver les amortissements cumulés jusqu'à **0,06 €** — ce qui
casserait précisément ce golden. Le contrat au centime prime (ADR-006).

Les 3 écarts prévisionnels 2026 pré-existants (mars 3 506,85 € ; mars colloc
643,95 € ; mars colloc 2025 0,75 €) restent **identiques** en v4 (donc absents
du diff `--compare`) — l'étape 2 ne les touche pas.
