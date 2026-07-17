# Position fiscale — où on en est, pour reprendre (2026-07-18)

Sous-projet 3 (affichage). La partie moteur (sous-projet 1) + réconciliation
backend (sous-projet 2) sont LIVRÉES et poussées sur `refonte`. Ici : la **vue
"position fiscale"** avec les deux tirelires, en cours de conception (maquettes).

## Maquette approuvée par Louis : `vue-complete-v2.html`

C'est celle à coder. Ouvre-la pour voir le rendu cible. Structure :
- Détail **par appartement** (Evry/abnb/colloc) — App seul (l'officiel ne ventile pas).
- **Résultat entité**, **Tirelire déficit (cumulé)**, **Tirelire amortissements reportés (cumulé)** :
  chacun en **3 colonnes App / Officiel / Écart**.
- Ligne **reprise** (2025) = point de départ officiel adopté ; **2026** = brouillon (App seul).

Louis a validé (« c'est top »). Dernier échange : le `≈ 54 621` de 2026 = tirelire
amort fin 2026 = reprise 35 364 + 19 257 déféré en 2026 (≈ car base reconstituée).

Question ouverte laissée en suspens : si le tableau (12 colonnes) est trop large,
masquer les colonnes « App » derrière un bouton « voir les écarts » (défaut =
Officiel + Écart). À trancher avec Louis à la reprise.

## LA décision de conception (validée)

**On adopte la position OFFICIELLE (comptable) comme réalité et point de reprise.**
- L'appli AFFICHE la réalité déposée + où elle aurait calculé différemment (colonnes
  App/Officiel/Écart), sans réécrire l'officiel.
- À partir de 2026, l'appli calcule en **repartant de la position officielle fin 2025**,
  pas de son propre calcul. C'est une reprise comptable classique.
- Motif : les chiffres officiels sont la réalité fiscale ; l'appli devient l'outil pour
  calculer 2026+ et **challenger le comptable avant chaque dépôt**.

### Chiffres de reprise (fin 2025)
- **Déficit reportable = 39 912,96 €** — OFFICIEL, source `aide_au_report (2025).pdf`. Ferme.
- **Amortissements reportés ≈ 35 364 €** — RECONSTITUÉ des écritures (FEC), non publié par
  le comptable. Approximatif (d'où le ≈).
- Total à déduire ≈ 75 277 € (avant tout impôt).

## Ce qu'il reste à CONSTRUIRE (backend + frontend)

1. **Backend — "reprise des reports"** : le moteur fiscal doit pouvoir partir d'une
   position d'ouverture officielle (déficit + amort reportés à une année de bascule),
   au lieu de recalculer depuis 2021. Paramètre de config, valeurs saisies depuis les
   docs officiels. 2026+ calculé depuis cette reprise.
2. **Backend — colonne "officiel" des tirelires cumulées** : exposer, par année, le
   déficit reportable et l'amort reporté OFFICIELS (déjà dans les liasses de référence
   pour le déficit ; amort reporté à reconstituer des réintégrations annuelles).
3. **Frontend — la vue `vue-complete-v2`** : nouvelle page (ou refonte de
   `/dashboard/liasse-fiscale`), tableau App/Officiel/Écart par appartement + entité +
   2 tirelires. Repositionnée en GLOBAL (pas dans le menu par-propriété — cf. retour
   de Louis « l'onglet apparait comme si j'étais dans une propriété »).

## Découvertes des FEC (comptabilité officielle 2021-2023) — à consigner dans ECARTS

Louis a fourni les FEC 2021/2022/2023 (~/Downloads/Re_ demande admin fiscale (2)/).
Elles EXPLIQUENT les divergences :

- **Écarts ~600 € (2021-2022)** = les **travaux** : l'appli les immobilise au
  **01/12/2021** (date de la transaction), le comptable en **2022**. Décalage de timing
  d'amortissement qui **converge en 2023** (amort identique au centime : 11 119).
  Ni erreur de l'app ni du comptable — une date de mise en service différente.
- **Divergence déficit 2023 (−3 462 €)** = **ordre d'imputation**. Le comptable a
  neutralisé le bénéfice 2023 (+4 077) en imputant l'**amortissement reporté** (la ligne
  « déductions diverses 4 077 » de la liasse), **en gardant le déficit** à 23 497.
  L'appli fait l'inverse (impute le **déficit** d'abord — l'ordre recommandé, car le
  déficit expire à 10 ans, pas l'amortissement). Pas une faute nette du comptable : un
  choix d'ordre, un peu moins prudent. À faire confirmer par un fiscaliste si besoin.
- **Insight clé** : le TOTAL à déduire est quasi identique des deux méthodes (~75-76 k€),
  seule la **répartition** entre les deux tirelires diffère.
- Trop tard / pas worth de corriger 2023 (enjeu = ordre, pas d'impôt payé en trop).

Chiffres officiels des FEC (résultat comptable / amort) :
```
2021 : résultat −23 828,65  amort 331,53
2022 : résultat  −4 218,02  amort 9 750,45
2023 : résultat  +4 076,58  amort 11 119,16
```

## Documents sources (dans docs/files/, gitignorés)
- `appartements/aide_au_report (2024).pdf.pdf`, `aide_au_report (2025).pdf` → déficit reportable officiel cumulé
- FEC : `~/Downloads/Re_ demande admin fiscale (2)/917800823FEC{2021,2022,2023}1231.txt`
- Liasses 2021-2025 déjà saisies dans `docs/project/reference/liasses/liasse-*.json`
