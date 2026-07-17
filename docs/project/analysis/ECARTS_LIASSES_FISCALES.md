# Écarts constatés entre les liasses fiscales déposées et la comptabilité

Document de travail — base pour un courrier au cabinet comptable.
Dernière mise à jour : 2026-07-17.

Entité : **Louis Garnier — SIREN 917 800 823** — loueur en meublé, régime réel
simplifié.

Composition par exercice (déduite des immobilisations brutes de chaque liasse,
et vérifiée : le total tombe au centime) :

| Exercice | Biens inclus | Immobilisations brutes | Liasse (case 028) |
|---|---|---|---|
| 2021 → 2023 | Evry | 237 691,48 | à vérifier |
| 2024 | Evry + Marseille abnb | 358 444,57 | **358 445** ✓ |
| 2025 | Evry + Marseille abnb + Marseille colloc | 559 455,06 | **559 455** ✓ |

---

## ❗ Écart 1 — Exercice 2025 : charges financières sous-évaluées de 63,68 €

**Statut : erreur du cabinet. Confirmée par le tableau d'amortissement de la banque.**

La liasse 2025 porte **8 878 €** de charges financières (case 294). Le montant
exact est **8 941,36 €**. L'écart de **63,68 €** porte entièrement sur
l'appartement Marseille colloc.

| Bien | Intérêts + assurance retenus | Montant exact | Écart |
|---|---|---|---|
| Evry | 2 489 | 2 488,88 | ✓ |
| Marseille abnb | 4 934 | 4 933,80 | ✓ |
| **Marseille colloc** | **1 455** | **1 518,68** | **−63,68** |

### Justificatif — tableaux d'amortissement LCL

Deux prêts, tous deux débités sur le compte LCL de la colloc.

**Prêt n° 5008900I01QH11AH** — 169 540,00 € à 2,95 %, départ 13/08/2025,
première échéance 13/09/2025 (12 mois de différé, déblocages progressifs) :

| Échéance | Intérêts | Assurance |
|---|---|---|
| 13/09/2025 | 116,05 | 22,17 |
| 13/10/2025 | 397,26 | 21,76 |
| 13/11/2025 | 408,50 | 21,76 |
| 13/12/2025 | 408,50 | 21,76 |
| **Total 2025** | **1 330,31** | **87,45** |

**Prêt n° 5008900I01QH12AH** — 18 870,00 € à 1,99 %, départ 04/09/2025,
première échéance 04/10/2025 :

| Échéance | Intérêts | Assurance |
|---|---|---|
| 04/10/2025 | 30,86 | 2,95 |
| 04/11/2025 | 31,19 | 2,42 |
| 04/12/2025 | 31,08 | 2,42 |
| **Total 2025** | **93,13** | **7,79** |

**Total colloc 2025 : 1 423,44 d'intérêts + 95,24 d'assurance = 1 518,68 €.**

Les échéances des tableaux LCL correspondent au centime aux prélèvements
constatés sur le compte (7 prélèvements, 1 711,23 € au total).

### Conséquence

Charges financières sous-évaluées de 63,68 € → **résultat 2025 majoré de 63,68 €**.
La liasse porte un résultat de **−31 274 €** ; le résultat exact est
**−31 337,68 €** (avant l'écart d'arrondi ci-dessous).

---

## ⚠️ Écart 2 — Exercice 2025 : contrôle des autres postes

Tous les autres postes 2025 sont conformes, aux arrondis près (la liasse est
établie en euros entiers) :

| Poste (case) | Liasse | Exact | Écart |
|---|---|---|---|
| Produits (232) | 42 709 | 42 708,53 | −0,47 (arrondi) |
| Dotations aux amortissements (254) | 20 338 | 20 337,59 | −0,41 (arrondi) |
| Charges financières (294) | 8 878 | 8 941,36 | **−63,36** ❗ |
| Résultat (310) | −31 274 | −31 338,22 | −64,22 |

À noter : les **frais de dossier et commissions de caution** (1 000,00 +
2 518,91 + 577,94 = **4 096,85 €**), présents dans les tableaux LCL en « Frais
Divers », sont bien constatés en charges. Rien à signaler.

---

## ✅ Écart 3 — Exercice 2024 : résolu, aucune erreur du cabinet

La liasse 2024 porte un résultat de **−20 032 €**. Un écart de 600 € était
constaté avec la comptabilité ; il provenait du classement d'un virement reçu :

```
04/12/2024   +600,00   « VIR DE MANDA (remb frais recherche) »
```

Ce remboursement était comptabilisé en **produit**. Le cabinet l'avait — à
raison — exclu du compte de résultat. Il a été reclassé en **compte courant
d'associé** (flux neutre). Après reclassement :

| Poste | Liasse | Exact | Écart |
|---|---|---|---|
| Produits | 29 782 | 29 782,37 | +0,37 (arrondi) |
| Charges | −49 814 | −49 814,01 | −0,01 (arrondi) |
| Résultat | −20 032 | −20 031,64 | +0,36 (arrondi) |

**Exercice 2024 conforme.** Seuls subsistent 36 centimes d'arrondi.

---

## 🔎 Reste à vérifier

- **Exercices 2021, 2022, 2023** (Evry seul) — non contrôlés à ce jour.
  Documents : `BILAN LOUIS GARNIER 2021 (1).PDF`, `BILAN LOUIS GARNIER 2022 (1).PDF`,
  `BILAN 2023 LOUIS GARNIER.PDF`.
- Le **report à nouveau** entre exercices : un écart sur un exercice se propage
  mécaniquement aux suivants. À contrôler une fois 2021-2023 vérifiés.

---

## Méthode

Les montants « exacts » ci-dessus sont produits par l'application de
comptabilité, à partir des relevés bancaires réels (transactions rapprochées au
centime avec les comptes LCL, Crédit Mutuel et Boursorama) et des tableaux
d'amortissement officiels des prêteurs.

Contrôle de fiabilité effectué sur les postes calculés :
- **Échéanciers de crédit** : les 7 échéances 2025 de la colloc reproduisent au
  centime le tableau d'amortissement LCL, y compris la première échéance
  partielle (116,05 €) et les déblocages progressifs.
- **Amortissements** : 20 337,59 € contre 20 338 € à la liasse 2025 — conforme.
- **Charges courantes** : 21 889,40 € contre 21 889 € — conforme.
