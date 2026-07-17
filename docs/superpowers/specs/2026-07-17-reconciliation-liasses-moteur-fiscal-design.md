# Réconciliation des liasses fiscales & moteur fiscal LMNP — Conception

Date : 2026-07-17
Statut : en attente de relecture Louis

## 1. Contexte et objectif

L'entité **Louis Garnier (SIREN 917 800 823)**, loueur en meublé au réel
simplifié, détient trois appartements (Evry, Marseille abnb, Marseille colloc).
Jusqu'ici, un cabinet comptable établissait la liasse fiscale annuelle. Ce
cabinet n'est plus disponible.

**Objectif.** Faire de l'application la **source de vérité** des chiffres
fiscaux. L'application calcule tout, dynamiquement, à partir des relevés
bancaires réels. Les liasses passées (2021→2025) sont chargées **uniquement
comme référence de contrôle** : elles servent à vérifier l'application, pas à
l'alimenter.

**Principe directeur (corrigé en cours de cadrage).**

```
L'APPLI CALCULE  →  colonne « application » = la vérité
LA LIASSE VÉRIFIE →  colonne « liasse » = ce que le cabinet a déposé
écart ≠ 0        →  quelqu'un s'est trompé (le cabinet, OU un bug de l'appli qu'on corrige)
```

Ce n'est **pas** une interface de lecture de PDF. Les chiffres viennent de
l'application et sont dynamiques. La liasse n'est qu'une pièce de contrôle — et
comme le cabinet a déjà commis des erreurs (voir §2), l'indépendance de
l'application est l'intérêt central du projet.

## 2. Preuve de faisabilité (déjà établie)

La réconciliation a été menée à la main sur 2024 et 2025 avant ce document :

| Exercice | Résultat appli | Liasse | Écart | Cause |
|---|---|---|---|---|
| 2024 | −20 031,64 | −20 032 | 0,36 | arrondi (liasse en euros entiers) |
| 2025 | −31 338,22 | −31 274 | −64,22 | **erreur du cabinet** : intérêts colloc sous-évalués de 63,68 € |

Deux corrections de données déjà appliquées et validées (golden master à 0) :
- **2024** : virement « VIR DE MANDA (remb frais recherche) » (600 €) reclassé de
  « produit » en « compte courant d'associé » (flux neutre).
- Les intérêts de la colloc (1 518,68 €) reproduisent **au centime** les tableaux
  d'amortissement LCL (prêts 5008900I01QH11AH et QH12AH), différé de 12 mois et
  déblocages progressifs compris. **L'appli a raison, le cabinet a tort.**

Détail dans `docs/project/analysis/ECARTS_LIASSES_FISCALES.md`.

**Conclusion** : sur la partie la plus technique (échéanciers de crédit,
amortissements), l'application est démontrée plus fiable que le cabinet.

## 3. Décomposition en trois sous-projets

Le moteur fiscal n'existe pas aujourd'hui : l'application s'arrête au **résultat
comptable** (vérifié : aucune logique de réintégration / report en base de code).
Il faut le construire, et c'est le cœur. L'ordre est impératif — l'affichage
sans le moteur n'a aucun sens.

1. **Moteur fiscal LMNP** (le cerveau) — calcule réintégration, déficit
   reportable, amortissements reportés, et leurs **cumuls d'une année sur
   l'autre**. Validé contre les cinq liasses. *Seul morceau à risque.*
2. **Donnée de référence liasse** — un fichier JSON par année, saisi à la main
   depuis les PDF, chargé pour confronter.
3. **Page d'accueil + carte de réconciliation** — l'affichage (maquettes
   validées), nourri par le moteur.

Chaque sous-projet aura son propre plan d'implémentation. Ce document spécifie
le **sous-projet 1** en détail ; les 2 et 3 sont esquissés.

---

## 4. Sous-projet 1 — Moteur fiscal LMNP (détaillé)

### 4.1 La règle, rétro-conçue depuis les liasses

Le calcul se fait **au niveau de l'entité entière** (tous les biens agrégés),
PAS bien par bien. Preuve : en 2024, Evry était bénéficiaire avant amortissement
(+8 360 €) mais la liasse a tout de même reporté la **totalité** des
amortissements (14 553 €) — ce qui n'est possible que si la limitation
s'applique au résultat global (−5 479 €), pas au résultat de chaque bien.

**Conséquence pour l'affichage** : les colonnes par bien montrent le
**comptable** (produits, charges, amortissements, résultat comptable) ; le
**fiscal** (déficit reportable, amortissements reportés) est un stock **global**,
affiché en total uniquement. Le ventiler par bien n'aurait aucun sens fiscal.

### 4.2 Algorithme (par année, chronologique, niveau entité)

Pour chaque exercice N, du plus ancien (2021) au plus récent :

```
a. Résultat hors amortissement   R_ha = Σ produits − Σ charges (hors amortissement)
b. Amortissements de l'année      A    = Σ amortissements de tous les biens présents

c. Amortissement de l'année déductible = min(A, max(0, R_ha))
   Amortissement différé de l'année     = A − déductible        (report indéfini)
   Résultat après amort. de l'année     = R_ha − déductible

d. SI résultat après amort. > 0 (bénéfice) :
      1) imputer les DÉFICITS antérieurs (plus anciens d'abord, ≤ durée de report)
         → réduit le résultat, consomme le stock de déficit
      2) imputer les AMORTISSEMENTS différés antérieurs
         → réduit le résultat, consomme le stock d'amortissement
      Résultat fiscal imposable = ce qui reste (≥ 0)

   SI résultat après amort. ≤ 0 (déficit) :
      Déficit reportable de l'année = |résultat après amort.|   (report N ans)
      Résultat fiscal imposable = 0

e. Mise à jour des stocks :
      Stock déficit          += nouveau déficit (millésimé N) ; −= imputé ; purge > durée
      Stock amort. différé   += amort. différé de l'année ; −= imputé
```

### 4.3 Validation attendue (vérité-terrain = les liasses)

| Exercice | R_ha (appli) | Déficit reportable | Amort. reportés | Impôt | Liasse |
|---|---|---|---|---|---|
| 2024 | −5 479 | 5 479 | 14 553 | 0 | déficit 5 479 ✓ |
| 2025 | −11 001 | 11 001 | 20 338 | 0 | déficit 10 937 (−64 = erreur cabinet) |

Le moteur doit reproduire ces chiffres (au centime pour 2024 ; à l'écart-cabinet
près pour 2025). 2021-2023 (Evry seul) valideront les cumuls d'un exercice à
l'autre.

### 4.4 Paramètres configurables (réglages « année »)

Un encadré dans les paramètres, avec deux variables :

- **Durée de report du déficit** — défaut **10 ans** (nombre éditable). Au-delà,
  un déficit millésimé est purgé (perdu).
- **Durée de report des amortissements** — défaut **indéfiniment** (choix :
  « indéfiniment » ou un nombre d'années).

Ces paramètres sont globaux à l'entité (pas par bien).

### 4.5 Modèle de données

- Le moteur est **recalculé à la volée** (pas de table de cache), comme le reste
  des calculs financiers de l'app, pour rester cohérent avec les transactions.
- Il lit : transactions classées + `amortization_results` + échéanciers de
  crédit (déjà tout présent).
- Il écrit : rien en base pour les cumuls (recalcul chronologique depuis 2021 à
  chaque appel). Les deux paramètres de durée sont stockés (table de config à
  définir dans le plan).

### 4.6 Interface (API)

Une route type `GET /api/fiscal/calculate?year=YYYY` renvoyant, pour l'entité :
résultat comptable, R_ha, amortissement déductible / différé, déficit reportable
de l'année, imputations, résultat fiscal imposable, et les **stocks cumulés** de
déficit (millésimés) et d'amortissements différés à la fin de l'exercice.
Contrat précis à définir via `api-and-interface-design` dans le plan.

---

## 5. Sous-projet 2 — Donnée de référence liasse (esquisse)

Fichier `docs/project/reference/liasses/liasse-<année>.json`, un par année, saisi
à la main depuis les PDF. Contenu : `annee`, `source` (nom du PDF), `depose_le`,
`unite` ("euros entiers"), `biens_inclus` (liste d'IDs), et les postes du CR, du
bilan et du fiscal tels qu'ils figurent sur la liasse.

Deux garde-fous :
- `biens_inclus` : la carte recalcule les immobilisations brutes de ces biens et
  les compare à la case 028 de la liasse. Discordance → alerte « composition »,
  pas un faux écart de résultat.
- `unite: "euros entiers"` : tolérance d'arrondi. Un écart de ligne < 1 € = ✓ ;
  ≥ 1 € = écart réel.

## 6. Sous-projet 3 — Page d'accueil + carte (esquisse, maquettes validées)

**Page d'accueil** — deux sections :
- **Appartements** : une carte par bien (solde bancaire réel, résultat de
  l'exercice, pastille boîte de réception) au lieu de « Créé le … ».
- **Liasse fiscale / données globales** : une carte par exercice (2021→2026),
  affichant biens inclus, résultat, et état de contrôle (`✓ conforme`,
  `❗ N écarts`, `brouillon · liasse non reçue`, `à vérifier`).

**Carte détail par exercice** — structure des tableurs de Louis : une colonne par
appartement, puis Total appli / Liasse / Écart. Lignes : reports, produits,
charges (courantes, impôts, amortissements, intérêts), résultat comptable, puis
bas de tableau fiscal (amortissements réintégrés par bien, déficit reportable et
résultat fiscal en **total** — stock global). Écart affiché **là où il est**
(✓ vert, montant rouge au-delà de 1 €). Bloc d'explication en clair sous le
tableau, renvoyant à `ECARTS_LIASSES_FISCALES.md`.

**État « brouillon » (2026+)** : tant que la liasse n'est pas reçue, plus de
colonnes Liasse/Écart — la carte affiche les chiffres de l'appli comme brouillon
à transmettre au comptable. Une fois la liasse chargée, les colonnes de contrôle
apparaissent, cible = 0 écart.

## 7. Cycle cible (à partir de 2026)

```
L'appli produit les chiffres → transmis à l'expert-comptable → il établit la liasse
→ liasse chargée dans l'appli → la carte confronte → 0 écart attendu
→ si surprise : on corrige AVANT publication
```

Plus jamais d'erreur découverte trois ans après le dépôt.

## 8. Hors périmètre (étapes ultérieures, non couvertes ici)

- **Forecast fiscal** : projeter dans combien d'années les stocks de reports
  seront épuisés et l'entité deviendra imposable. Explicitement reporté par Louis
  à une étape « forecast » ultérieure.
- **Génération du CERFA 2033-A / 2033-B** rempli.

## 9. Stratégie de test

- Moteur fiscal validé par des tests reproduisant les liasses 2024 et 2025 (et
  2021-2023 pour les cumuls). Vérité-terrain = les PDF.
- Golden master étendu au résultat fiscal, pour garantir zéro régression des
  chiffres à chaque évolution.
- E2E sur la carte une fois l'UI construite (webapp-testing).
