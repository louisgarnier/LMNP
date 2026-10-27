# Écarts constatés entre les liasses fiscales déposées et la comptabilité

Document de travail — base pour un courrier au cabinet comptable.
Dernière mise à jour : **2026-07-30**.

## 🔬 ENQUÊTE 2026-07-30 — les 13 écarts « à investiguer » sont tous élucidés

Décomposition par les tags de transaction de l'application (chaque écart tracé
poste par poste). Résultat : **4 mécanismes, aucune erreur du cabinet**.

**M1 — Assurance emprunteur reclassée (prouvé au centime).** En 2021-2023 les
charges financières de la liasse = intérêts SEULS (2022 : 2 451 vs intérêts
2 451,40 ; 2023 : 2 462 vs 2 461,98). L'assurance (307,58 / 303,02) était rangée
en charges externes. **Le cabinet a changé de méthode en 2024** : depuis,
intérêts + assurance collent au centime. Explique les écarts intérêts
2021/2022/2023 et l'essentiel des charges externes 2022/2023 (signe inverse).

**M2 — Rattachement : engagement (cabinet) vs trésorerie (app).** Charges fin
2021 (frais bancaires 563 + PNO 38) rattachées à 2022 par le cabinet ; loyers
2022 : 4 762,99 encaissés (app) vs 4 875 rattachés (cabinet) = 112 € à cheval —
décomposé au centime, les transferts de charges collant exactement (13 327,92
vs 13 328).

**M3 — Travaux du 01/12/2021, désormais prouvé au centime sur le bilan.**
Immobilisations brutes 2021 : app 201 115,83 vs liasse 165 000 = **exactement**
la transaction « Travaux de rénovation, gros œuvre −36 115,83 € » du 01/12/2021,
immobilisée en 2022 par le cabinet.

**M4 — Trou de transcription DE NOTRE CÔTÉ (corrigé).** L'écart charges
externes 2024 (−60,10) : le cabinet a rangé 60 € en « charges exceptionnelles »
(2033-B bloc VI, lisible dans la colonne N-1 de la liasse 2025), ligne que notre
JSON ne transcrivait pas. Côté app : frais bancaires 42 + diagnostics 18 = 60.
Corrigé : `charges_exceptionnelles` ajoutée à liasse-2024.json et la
réconciliation compare à périmètre égal. **L'écart a disparu (−0,10 €).**

Les écarts « Résultat » (2021 −900,17 ; 2022 −192,58 ; 2023 −15,41) sont des
**composites** — sommes exactes des écarts composants, pas des écarts propres.

Résidus réellement inexpliqués après enquête : ~29 € (charges 2022), ~15 €
(2023), 7,55 € (intérêts 2021). Ordre de grandeur des arrondis/coupures de date.

Bilan global : **52 écarts app/liasse sur 2021-2025, 52 expliqués** — dont
5 seulement « erreur du cabinet » (tous sur 2025 : les 63,68 € de charges
financières et ses conséquences, et les emprunts Marseille absents du passif).
Les explications sont encodées dans les `liasse-*.json` (clé `ecarts_expliques`)
et affichées dans l'onglet « Face à la liasse ».

> 📮 **Le courrier consolidé est dans `MAIL-COMPTABLE-2026-07-28.md`** (non envoyé).
> Il ne retient que 4 points sur les 8 recensés ici : les emprunts Marseille absents du
> passif 2025, les 63,68 € de charges financières, le 2033-D déposé néant, et la demande
> de ventilation du SUIV39C par bien. Les autres écarts sont classés « pas une erreur »
> et ne doivent pas être envoyés.

## ❗ NOUVEAU 2026-07-28 — Emprunts de Marseille absents du passif 2025

Lecture du PDF `liasse_fiscale_25.pdf` (2033-A) : case 156 « Emprunts et dettes
assimilées » = **195 000 €**, cases 173 et 175 vides, TOTAL III = 195 000 €.

Capital restant dû réel au 31/12/2025, recalculé depuis les échéanciers en base
(table `loan_payments`, 906 lignes, **montants stockés en centimes**) :

| Bien | CRD 31/12/2025 | Intérêts 2025 | Taux implicite |
|---|---:|---:|---:|
| Evry | 194 614 € | 2 210 € | 1,14 % |
| Marseille abnb | 106 251 € | 4 770 € | 4,49 % |
| Marseille colloc (2 prêts) | 184 849 € | 1 423 € | démarré 09/2025 |
| **Total** | **485 713 €** | **8 403 €** | |

**Dette manquante au bilan : 290 713 €.** L'incohérence est *interne* à la liasse :
elle déduit 8 878 € d'intérêts (case 294) dont ~6 700 € proviennent de crédits absents
du passif. Piste : le poste « Capital social ou individuel » (case 120) bondit de 304 €
(31/12/2023) à 342 724 € (31/12/2024) — financements peut-être passés en apports.

## 📄 NOUVEAU 2026-07-28 — ce que contient VRAIMENT la liasse 2025

Deux croyances du projet étaient fausses, corrigées après lecture du PDF :

| | Réalité vérifiée |
|---|---|
| Stock d'amortissements reportés | ✅ **DÉCLARÉ** sur le formulaire **SUIV39C** (art. 39 C, II-1 et 2 CGI), p. 14 : B 15 026 / C 20 338 / D 35 363 / G 0 / **H 35 363**. Ce n'est **pas** une reconstitution des FEC — c'est un chiffre officiel et opposable. Le champ « Dénomination du bien » est **vide** → c'est là qu'est le trou du découpage par bien. |
| Stock de déficit reportable | ❌ **ABSENT** de la liasse 2025 : formulaire 2033-D déposé **néant**, tout vide. Seul le déficit de l'année (10 937 €) figure, au 2031-SD case 7. Le cumul 39 913 € vient de l'aide au report Teledec, hors CERFA. À noter : le 2033-D **était renseigné en 2023** (case 982 = 23 497 €). |

⇒ Renommer le champ `stock_amort_reporte_reconstitue` des JSON de liasse : il n'est pas
reconstitué, il est déclaré.

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

⚠️ ~~**Point d'attention relevé sur la liasse elle-même**~~ — **RÉTRACTÉ le 2026-07-28.**
Sur le 2033-D, la case 983 « Déficits imputés » est vierge et la case 984 « Déficits
reportables » reste à 23 497 € — identique à la case 982. On en avait conclu que le
cabinet avait oublié de réduire le stock de déficit. **C'est faux, et contredit par
l'analyse des FEC plus bas** : le cabinet a neutralisé le bénéfice 2023 en imputant
l'**amortissement reporté** (ligne « déductions diverses 4 077 » de la liasse), et non
le déficit. Le stock de déficit reste donc **légitimement** à 23 497 €.
**Ne pas envoyer ce point au cabinet comme une erreur.** Ce n'est pas une faute mais
un choix d'ordre d'imputation — reformulé en préférence pour l'avenir dans
`MAIL-COMPTABLE-2026-07-28.md`, point 3.

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

## 🔬 Explication des écarts par les FEC (comptabilité officielle 2021-2023)

Les FEC (Fichiers des Écritures Comptables) fournis par Louis expliquent les écarts.

**Écarts ~600 € (2021-2022) = date des travaux.** L'appli immobilise les travaux au
**01/12/2021** (date de la transaction), le cabinet en **2022**. L'amortissement démarre
donc un an plus tôt côté appli → surplus en 2021-2022 qui **converge en 2023** (amort
identique au centime : 11 119). Ni erreur de l'appli ni du cabinet — une date de mise
en service différente. Résultats comptables officiels (FEC) : 2021 −23 828,65
(amort 331,53) ; 2022 −4 218,02 (amort 9 750,45) ; 2023 +4 076,58 (amort 11 119,16).

**Divergence du déficit 2023 (−3 462 €) = ordre d'imputation.** En 2023, bénéfice fiscal
+4 077. Le cabinet l'a neutralisé en imputant l'**amortissement reporté** (ligne
« déductions diverses 4 077 » de la liasse), **conservant le déficit à 23 497**. L'appli
impute le **déficit d'abord** (ordre recommandé : le déficit expire à 10 ans, pas
l'amortissement). Ce n'est pas une faute nette — un choix d'ordre, un peu moins prudent.
Le TOTAL à déduire est quasi identique des deux méthodes (~75-76 k€) ; seule la
répartition entre les deux « tirelires » diffère. **Point à poser au cabinet**, sans
urgence (aucun impôt payé en trop ; correction de 2023 non prioritaire).

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
