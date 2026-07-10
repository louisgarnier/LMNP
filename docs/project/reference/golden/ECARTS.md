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
