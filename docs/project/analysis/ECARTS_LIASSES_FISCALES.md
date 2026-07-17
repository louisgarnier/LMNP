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

## ✅ Exercice 2023 : résultat fiscal imposable vérifié à 0 (contrôle manuel BILAN 2023)

Lu dans `BILAN 2023 LOUIS GARNIER.PDF` (liasse CERFA 2033, régime réel simplifié) :
- Résultat comptable (bénéfice) : **4 077 €** (case 310 du 2033-B, = case 136 du bilan 2033-A).
- Résultat fiscal avant imputation des déficits antérieurs (case 352) : **4 077 €**, aucune réintégration.
- Déficits antérieurs reportables (case 360 du 2033-B et case 982 du 2033-D) : **23 497 €** — un déficit reportable figure donc bien à la liasse.
- Résultat fiscal après imputation des déficits (cases 370/372 du 2033-B) et « Bénéfice imposable » (cases 1/4 du CERFA 2031) : **vierges** (aucun chiffre imprimé), et aucun montant en case VII « Impôts sur les bénéfices ». Conforme à un résultat fiscal imposable de **0** — les liasses françaises n'impriment pas de « 0 » explicite sur les cases nulles.

→ **Confirmé** : résultat fiscal imposable 2023 = 0, comme le calcule le moteur (`resultat_fiscal_imposable` = 0.0). Le moteur impute 4 061,59 € du bénéfice contre le déficit 2021 reporté ; l'écart avec le résultat comptable liasse (4 077 €, soit 15,41 € de plus) reste à expliquer mais ne remet pas en cause l'imposable nul.

⚠️ **Point d'attention relevé sur la liasse elle-même** (non lié au moteur) : sur le
2033-D, la case 983 « Déficits imputés » est vierge et la case 984 « Déficits
reportables » reste à 23 497 € — identique à la case 982 (stock de début
d'exercice) — alors que le bénéfice de 4 077 € a bien annulé le résultat
imposable. Le cabinet semble ne pas avoir réduit le stock de déficit reportable
malgré l'imputation. À signaler au cabinet, sans impact sur l'imposable 2023
(0 confirmé), mais potentiellement sur le stock de déficit reporté aux
exercices suivants dans leurs déclarations papier.

## ⚠️ Exercice 2021 (Evry seul) — écart de données appli/cabinet (~600 €)

Lu dans `BILAN LOUIS GARNIER 2021 (1).PDF` :
- Résultat comptable : **−23 829 €** (l'appli calcule −24 729, écart ~900).
- Dotations aux amortissements : **332 €** (l'appli calcule 632, écart ~300).
- Déficit reportable (résultat fiscal) : **23 497 €** (l'appli calcule 24 097, écart ~600).
- Produits d'exploitation : **0** (Evry acquis en août 2021, pas encore de loyers).
- Immobilisations brutes : **165 000 €** (terrain 49 500 + construction 115 500) —
  PAS 237 691 : les travaux et le mobilier ont été immobilisés APRÈS 2021.
  ⇒ le contrôle de composition (immo = case 028) doit se faire **année par année**.

Écart à investiguer : l'appli amortit ~300 € de plus et porte ~900 € de charges de
plus qu'en 2021 déclaré. Imposable 0 des deux côtés.

## ✅ Exercice 2022 (Evry seul) — valide la mécanique de réintégration

Lu dans `BILAN LOUIS GARNIER 2022 (1).PDF` :
- Résultat comptable : **−4 218 €** (l'appli calcule −4 410, écart ~200).
- Dotations aux amortissements : **9 750 €** (l'appli calcule 10 351, écart ~600).
- **Amortissements excédentaires réintégrés : 4 218 €** — le résultat avant
  amortissement (5 532 €) absorbe une partie de l'amortissement, l'excédent est
  reporté. **Le moteur applique exactement cette règle.** ✓
- Produits d'exploitation : 18 203 € (loyers 4 875 + transfert de charges 13 328).
- Résultat fiscal imposable : **0**.

## ❗ Divergence de trajectoire du STOCK de déficit reportable (appli vs cabinet)

| Fin d'exercice | Déficit reportable — appli (recalculé) | Déficit reportable — liasse (déposé) |
|---|---|---|
| 2021 | 24 097 | 23 497 |
| 2022 | 24 097 | 23 497 |
| 2023 | **20 035** (bénéfice 2023 imputé) | **23 497** ❗ (non réduit — anomalie 2033-D) |
| 2024 | 25 514 | ~28 976 |
| 2025 | 36 515 | ~39 913 |

**Point majeur pour le cabinet :** en 2023, le bénéfice a annulé le résultat
imposable (0 des deux côtés), mais le cabinet **n'a pas réduit le stock de déficit
reportable** (case 984 du 2033-D restée à 23 497 = case 982 d'ouverture). L'appli,
elle, impute correctement les ~4 062 € de bénéfice sur le déficit. Résultat : le
stock de déficit du cabinet est **surévalué d'environ 3 500 €** à partir de 2023,
ce qui repousserait à tort l'année où Louis deviendra imposable.

## 🔎 Reste à vérifier

- Origine des écarts de données appli/cabinet 2021-2022 (~200-900 € par ligne) :
  différence de prorata d'amortissement de première année, périmètre des charges.
- Le **report à nouveau** entre exercices propage ces écarts ; la carte de
  réconciliation (sous-projet 3) les affichera année par année.

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
