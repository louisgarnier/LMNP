# Les deux tirelires fiscales — explication de référence

> Document validé par Louis le 2026-07-28. C'est la formulation à reprendre
> telle quelle pour l'écran à construire dans l'appli.
> Chiffres extraits de `/api/fiscal/chaine` (branche `refonte`), vérifiés ligne à ligne.

---

## LA RÈGLE UNIQUE

Un seul chiffre décide de tout : le **RÉSULTAT AVANT AMORTISSEMENT**.

```
Résultat comptable  +  amortissement  =  RÉSULTAT AVANT AMORT
```

| Cas | Ce qui se passe |
|---|---|
| **NÉGATIF** | Déduit 0 €. La perte → tirelire 1 (déficit). Tout l'amort → tirelire 2. |
| **POSITIF, < amort** | L'amort efface le bénéfice jusqu'à 0 → déduit. Le surplus d'amort → tirelire 2. Tirelire 1 ne bouge pas. |
| **POSITIF, > amort** | Tout l'amort passe → déduit. Il reste du bénéfice → **on puise dans une tirelire** (choix « imputer en priorité »). |

Principe : **l'amortissement ne peut jamais créer de perte.** Il descend le résultat
jusqu'à zéro, jamais en dessous. Ce qui ne rentre pas est mis de côté.

Les deux tirelires se remplissent en même temps, la même année, à partir du même chiffre.

---

## LE TABLEAU COMPLET (2021-2025)

| Année | Résultat comptable | + amort | = AVANT AMORT | Amort fabriqué | Amort déduit | T1 entrée | T1 sortie | **T1 SOLDE** | T2 entrée | T2 sortie | **T2 SOLDE** | Impôt |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| 2021 | −24 729 | +632 | **−24 097** | 632 | 0 | +24 097 | — | **24 097** | +632 | — | **632** | 0 € |
| 2022 | −4 411 | +10 351 | **+5 940** | 10 351 | 5 940 | — | — | **24 097** | +4 411 | — | **5 043** | 0 € |
| 2023 | +4 062 | +11 119 | **+15 181** | 11 119 | 11 119 | — | 0 | **24 097** | — | −4 062 | **981** | 0 € |
| 2024 | −20 032 | +14 553 | **−5 479** | 14 553 | 0 | +5 479 | — | **29 576** | +14 553 | — | **15 534** | 0 € |
| 2025 | −31 338 | +20 338 | **−11 001** | 20 338 | 0 | +11 001 | — | **40 576** | +20 338 | — | **35 872** | 0 € |

Contrôles vérifiés sur chaque ligne :
- `résultat comptable + amort = avant amort` ✓
- `amort fabriqué = amort déduit + entrée tirelire 2` ✓

---

## CHAQUE ANNÉE

### 2021 — négative → les DEUX tirelires se remplissent
`−24 729 + 632 = −24 097` ❌ négatif.
Amort déduit 0. Les 632 € d'amort → T2. La perte 24 097 € → T1.
**T1 = 24 097 | T2 = 632 | Impôt 0**

### 2022 — positive → seule T2 se remplit
`−4 411 + 10 351 = +5 940` ✅ positif mais < 10 351.
L'amort efface les 5 940 € (déduits pour de vrai) et s'arrête à zéro.
Surplus 10 351 − 5 940 = 4 411 € → T2. Pas de perte → T1 inchangée.
**T1 = 24 097 | T2 = 5 043 | Impôt 0**

### 2023 — LA SEULE ANNÉE OÙ UNE TIRELIRE SE VIDE
`+4 062 + 11 119 = +15 181` ✅✅ positif et > 11 119.
Tout l'amort passe (11 119 € déduits), mais il reste 4 062 € imposables.
On puise **4 062 € dans T2**. T1 n'est pas utilisée.
**T1 = 24 097 (intacte) | T2 = 981 | Impôt 0**

> C'est ici que joue le menu « Imputer en priorité » de l'appli. On aurait pu
> vider T1 à la place. Le comptable a choisi T2 — d'où le fait que la tirelire
> déficit n'a **jamais** servi, alors que c'est elle qui périme.

### 2024 — négative → les DEUX tirelires se remplissent
`−20 032 + 14 553 = −5 479` ❌ négatif.
Amort déduit 0. 14 553 € → T2. Perte 5 479 € → T1.
**T1 = 29 576 | T2 = 15 534 | Impôt 0**

### 2025 — négative → les DEUX tirelires se remplissent
`−31 338 + 20 338 = −11 001` ❌ négatif.
Amort déduit 0. 20 338 € → T2. Perte 11 001 € → T1.
**T1 = 40 576 | T2 = 35 872 | Impôt 0**

---

## ÉTAT AU 31/12/2025

| | T1 — DÉFICIT | T2 — AMORTISSEMENTS |
|---|---:|---:|
| Total mis dedans | 40 576 € | 39 934 € |
| Total sorti | 0 € | 4 062 € (2023) |
| **IL RESTE** | **40 576 €** | **35 872 €** |
| Péremption | ⏳ 10 ans — dont **24 097 € meurent fin 2031** | ♾️ jamais |
| Utilité à la revente | ❌ aucune | ✅ preuve |

**Total en réserve : 76 448 €** de réductions d'impôt futures.

### Le relevé de la tirelire 2 (vue « A / B / C »)

| | | Fin 2025 | Affiché par l'appli ? |
|---|---|---:|---|
| **A** | Total amorti depuis 2021 | 56 993 € | ❌ non |
| **B** | dont **déjà déduit** | 21 121 € | ❌ non |
| **C** | dont **encore en tirelire** | 35 872 € | ✅ oui |

`A = B + C`. B se décompose en 17 060 € déduits directement + 4 062 € sortis de la tirelire en 2023.

### Amortissement cumulé par bien (fin 2025)

| Bien | Total amorti (A) | dont déduit (B) | dont tirelire (C) |
|---|---:|---:|---:|
| Evry (id 25, depuis 2021) | 44 341 € | **21 121 €** | **23 220 €** |
| Marseille abnb (id 15, depuis 2024) | 9 591 € | **0 €** | **9 591 €** |
| Marseille colloc (id 26, depuis 2025) | 3 061 € | **0 €** | **3 061 €** |
| **Total** | **56 993 €** | **21 121 €** | **35 872 €** |

**Le découpage de B par bien est déterminable sans règle de répartition arbitraire**
(constaté 2026-07-28) : les seules années où de l'amortissement a été réellement
déduit sont 2022 (5 940 €) et 2023 (15 181 €). À ces dates **Evry était le seul bien**
(Marseille abnb démarre en 2024, Marseille colloc en 2025). Donc la totalité des
21 121 € déduits est attribuable à Evry, et les deux Marseille n'ont **jamais rien
déduit** — 100 % de leur amortissement est encore en tirelire.

Contrôle : 23 220 + 9 591 + 3 061 = 35 872 ✓

⚠️ Cette propriété est vraie **tant qu'aucune déduction n'intervient sur une année où
plusieurs biens coexistent**. Dès la première année bénéficiaire à partir de 2024, il
faudra une règle de répartition (prorata d'amortissement du bien, probablement) — à
faire valider par un fiscaliste. Le backend calcule au niveau entité et ne trace pas
l'origine par bien : c'est le développement à prévoir.

---

---

## CE QUE LA LIASSE ÉCRIT (exercice 2025, les 3 appartements)

⚠️ **Le périmètre change selon l'année** — une liasse ne couvre que les biens détenus
cette année-là :

| Liasse | Biens couverts |
|---|---|
| 2021 · 2022 · 2023 | Evry seul |
| 2024 | Evry + Marseille abnb |
| 2025 | les trois |

C'est ce qui rend le découpage par bien possible (cf. plus haut) : en 2022 et 2023,
seul Evry existait.

La liasse = 3 documents empilés.

**1. Compte de résultat** — loyers 42 709, charges 40 278, impôts et taxes 4 490,
amortissement 20 338, intérêts 8 878 → **résultat comptable −31 274**.

**2. Bilan** — immobilisations 559 455, **amortissements cumulés 56 090** (= le TOTAL
AMORTI, seul chiffre de tirelire au dossier du fisc, et le plus défavorable),
actif 503 365, emprunt restant dû 195 000 ⚠️ (voir anomalie ci-dessous).

### ⚠️ ANOMALIE À VÉRIFIER SUR LE PDF — la ligne emprunt (relevée 2026-07-28)

| Année | Biens | Emprunt au bilan | Intérêts | Taux implicite |
|---|---|---:|---:|---:|
| 2021 | Evry | 201 116 | 257 | (année partielle) |
| 2022 | Evry | 229 000 | 2 451 | 1,07 % |
| 2023 | Evry | 217 664 | 2 462 | 1,13 % |
| 2024 | Evry + abnb | **non relevé** | 6 066 | — |
| 2025 | les 3 | 195 000 | 8 878 | **4,55 %** |

Le crédit d'Evry date de 2021, à ~1,1 % (taux de l'époque). Sur 195 000 € il devrait
coûter ~2 150 € d'intérêts. La liasse 2025 en affiche **8 878 €** → les ~6 700 € d'écart
impliquent **~170 000 € de dette supplémentaire** (crédits Marseille, taux 2024-2025).

Deux hypothèses à départager sur le PDF original :
1. notre transcription de la liasse est incomplète (une seule ligne d'emprunt retenue) ;
2. les autres crédits sont logés ailleurs au passif — le poste `capital_individuel`
   bondit de **304 € (2023) à 342 724 € (2024)**, ce qui est à regarder.

**Tant que ce n'est pas tranché, ne pas se fier à `emprunt_capital_restant_du`.**
Le champ 2024 est d'ailleurs absent (`None`).

**3. Tableau fiscal** — amortissements réintégrés 20 338 (entrée T2),
déficit reportable de l'année 10 937 (entrée T1), **stock déficit reportable fin
39 913 (solde T1)**, résultat fiscal imposable 0. **Solde T2 : absent.**

La liasse applique exactement notre règle : `−31 274 + 20 338 = −10 936` → négatif →
20 338 en T2 (« réintégrés ») + 10 936 en T1 (« déficit de l'année »).

### Dictionnaire liasse ↔ tirelires

| Mot de la liasse | Signification | Tirelire |
|---|---|---|
| Dotation aux amortissements | l'amort fabriqué cette année | — |
| Amortissements réintégrés | ce qu'on **met** en T2 | T2 entrée |
| Déficit reportable de l'année | ce qu'on **met** en T1 | T1 entrée |
| Déficit reportable cumulé | le **solde** de T1 | T1 solde ✅ |
| Amortissements cumulés (bilan) | le **total amorti**, sans distinguer ce qui a servi | ⚠️ piège |
| *(rien)* | le **solde** de T2 | ❌ jamais écrit |

**Logique** : la liasse écrit toutes les **entrées** des deux tirelires, mais ne tient
le **solde** que du déficit. Les **sorties** ne sont écrites nulle part non plus — en
2023 les 4 062 € sortis de T2 ne se déduisent qu'en constatant un bénéfice de 4 062 €
et un impôt à 0 sans que le déficit ait bougé.

**Pourquoi** : le déficit se périme (10 ans) → le fisc doit en tenir le compteur.
Les amortissements reportés sont illimités dans le temps → pas d'expiration à
surveiller, donc seule la réintégration de l'année est demandée. Le cumul est à la
charge du contribuable. Ce n'est pas une omission.

---

## LA REVENTE

Deux impôts distincts, qui ne se parlent presque pas :
- **impôt sur les loyers** — tous les ans, sur les 3 biens ensemble : c'est là que vivent les tirelires
- **impôt sur la vente** — une fois, sur UN bien : les tirelires n'y figurent pas

Un seul chiffre traverse : **les amortissements déduits**.

### Formule (loi de finances 2025, ventes à partir du 15/02/2025)

```
   Prix de vente − prix d'achat − frais − travaux
 + Amortissements DÉDUITS
 = Plus-value imposable   (19 % + 17,2 % = 36,2 %, moins abattements de durée)
```

Le mot « déficit » n'apparaît pas dans cette formule. Avant la réforme 2025, les
amortissements ne comptaient pas du tout (avantage historique du LMNP).

### QUI ÉCRIT LE CHIFFRE : LOUIS, PAS LE FISC

Formulation à ne plus employer : « le fisc rajoute sans preuve ». C'est faux et ça a
perdu Louis. La réalité : **c'est le vendeur (via son notaire) qui remplit la
déclaration de plus-value** et qui y inscrit le montant d'amortissement à réintégrer.
Le risque n'est pas que l'administration invente un chiffre — c'est que Louis
**sur-déclare lui-même**, faute d'avoir autre chose que le total du bilan sous la main.
Et en cas de contrôle, l'administration compare à ce qu'elle détient : la liasse, donc
ce même total. Sans carnet, rien à opposer.

Cadrage à privilégier : **« si tu vendais aujourd'hui »**, avec deux colonnes
« déclaré sans le carnet » / « déclaré avec le carnet ».

### Enjeu par bien — si vente aujourd'hui (arrêté au 31/12/2025)

| Bien | Déclaré SANS le carnet | Déclaré AVEC le carnet | Sur-déclaration évitée | Impôt économisé (36,2 % avant abattements) |
|---|---:|---:|---:|---:|
| Evry | 44 341 € | 21 121 € | 23 220 € | ~8 400 € |
| Marseille abnb | 9 591 € | 0 € | 9 591 € | ~3 470 € |
| Marseille colloc | 3 061 € | 0 € | 3 061 € | ~1 100 € |

L'enjeu **grossit chaque année** tant que l'activité est en perte (T2 = 49 545 € fin 2026 en brouillon).

**La tirelire amortissements n'est pas une cagnotte, c'est un reçu** : elle prouve que
ces euros n'ont jamais baissé l'impôt, donc qu'on ne doit pas les facturer à la vente.

### Le déficit à la revente

Aucun rôle dans le calcul de la plus-value.

**Ordre de consommation = FIFO, le plus ancien d'abord** — vérifié dans le code :
`sorted(stock, key=lambda x: x[0])` (`fiscal_service.py:75`). Le premier bénéfice
attaque donc les 24 097 € de 2021, puis les 5 479 € de 2024, puis les 11 001 € de 2025.
C'est le bon ordre : on dépense d'abord ce qui va mourir. Un bénéfice de 24 097 €
avant fin 2031 suffirait à ce que rien ne soit perdu.

**Échéancier** — chaque tranche meurt 10 ans après sa naissance :

| Née en | Montant | Meurt fin | Perte sèche si aucun bénéfice |
|---|---:|---|---|
| 2021 | 24 097 € | 2031 | 60 % de la tirelire, dans 5 ans |
| 2024 | 5 479 € | 2034 | |
| 2025 | 11 001 € | 2035 | tirelire vidée sans avoir servi |

**Évolution d'une année sur l'autre :**

| Fait MONTER | Fait DESCENDRE |
|---|---|
| Année en perte (la perte s'ajoute) | Année en bénéfice (consommée — c'est le but) |
| Acheter un bien de plus (plus d'amort + intérêts → plus de perte) | Péremption à 10 ans (subie, sans contrepartie) |

Aujourd'hui elle **monte** (+5 479 en 2024, +11 001 en 2025) : signe qu'on n'arrive pas
à l'utiliser, pas une bonne nouvelle.

**Effet d'une vente — c'est une règle de droit, pas un arrangement :** le déficit BIC
appartient à l'**activité de loueur**, pas à l'immeuble.
- vente d'**un** bien en continuant de louer → **intact**, même si c'est le bien qui
  avait créé le déficit
- vente de **tout** + **cessation d'activité** → **40 576 € perdus** (c'est la cessation
  qui tue le report, pas la vente)

**Stratégie que ça ouvre (à chiffrer, pas un coup gagnant automatique) :** vendre les
biens déficitaires rend l'activité restante bénéficiaire → on commence enfin à vider
les tirelires, en attaquant les 24 097 € menacés. Nuances : la perte vient largement de
l'amortissement lui-même (le vendre supprime ce qui la crée), et la vente déclenche
l'impôt sur la plus-value.

---

## ⚠️ RÉSERVES

1. **Hypothèse non vérifiée (~13 000 €)** : que les amortissements restés en tirelire
   échappent à la réintégration, la loi visant les amortissements « admis en déduction ».
   Non contrôlé dans la doctrine BOFiP. À faire confirmer par un fiscaliste avant toute vente.
2. **Exonérations possibles** de la réintégration (résidences étudiantes, EHPAD, seniors) —
   non vérifié pour ces biens.
3. **Écarts avec le cabinet** : ~900 € sur le cumul d'amortissement, 663 € sur le déficit.
   Détail dans `ECARTS_LIASSES_FISCALES.md`.

---

## À FAIRE DANS L'APPLI (demandé par Louis, 2026-07-28)

1. Afficher ce tableau complet — les **deux** tirelires côte à côte, colonne
   « résultat avant amortissement » incluse (c'est elle qui explique tout).
2. Afficher le relevé A / B / C de la tirelire 2.
3. Afficher l'échéancier de péremption du déficit (24 097 € fin 2031).
4. Découpage par bien de A (déjà disponible côté backend).

Voir aussi : `ECARTS_LIASSES_FISCALES.md` (écarts app / cabinet).
