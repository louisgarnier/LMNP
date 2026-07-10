# Plan de refonte LMNP + Enable Banking

> Établi le 2026-07-10 après audit complet (backend + frontend + données).
> Principe : chaque étape est livrable et utilisable indépendamment — l'app n'est jamais cassée entre deux étapes.
> Les calculs comptables existants (CR, bilan, amortissements 30/360, prorata) sont **conservés** à chaque étape.

---

## Étape 0 — Fiabiliser l'existant (corrections, avant toute refonte)

Objectif : des chiffres justes avant de toucher à l'architecture.

- **0.1** Corriger le bug d'invalidation des caches CR/bilan : `property_id` manquant dans ~15 appels
  (`transactions.py`, `loan_payments.py`, `compte_resultat.py`), exceptions avalées par des `try/except print`.
- **0.2** Corriger la date de début du prêt Evry (`loan_start_date = 2026-05-08` → date réelle 2021/2022).
  Cause unique du bilan non équilibré 2022-2025 (capital remboursé ignoré, vérifié au centime près).
- **0.3** Remettre à plat les mappings d'amortissement d'Evry (types ↔ catégories croisés :
  « agencements 30 ans » → Immeuble, « mobilier 10 ans » → Travaux, « Facade/Toiture » → Mobilier…)
  + purger les résultats d'amortissement périmés (8 transactions référencées vs 2 réelles) + recalcul complet.
- **0.4** Corriger la page Amortissements qui ne recharge pas la config existante (7 types en base, écran vide).
- **0.5** Vérification finale : équilibre du bilan sur toutes les années, CR cohérent, tests de régression.

**Résultat pour toi : bilan équilibré, dotations justes, états fiables.**

## Étape 1 — Temps réel : suppression des caches

- Supprimer les tables `compte_resultat_data` / `bilan_data` et les endpoints `/generate`.
- CR et bilan calculés à la lecture (quelques ms à cette échelle).
- Corriger le calcul quadratique du report à nouveau (mémoïsation des CR par année dans la requête).

**Résultat : plus jamais de chiffres périmés, par construction. Écrans identiques.**

## Étape 2 — Référentiel de catégories (IDs au lieu de texte libre)

- Table de catégories hiérarchique (remplace les level 1/2/3 en chaînes comparées au caractère près).
- Migration par script des 174 règles existantes + de toutes les transactions déjà classées (zéro perte, zéro écart).
- Les configs CR / Bilan / Amortissements référencent des IDs (fini le JSON de libellés dans des colonnes texte).
- Jeu de catégories par défaut « seedé » à la création d'une propriété.

**Résultat : renommer une catégorie ne casse plus rien ; configurer une nouvelle propriété prend 2 minutes.**

## Étape 3 — Règles unifiées + Inbox de classification (maquettes ① et ②)

- Fusion des 2 systèmes actuels (mappings + mappings autorisés + Excel + script manuel) en **une** table de règles.
- Éditeur dans l'app : motif, type de match explicite (exact/préfixe/contient), priorité,
  **préversion live** (« cette règle classerait 11 transactions ») avant enregistrement.
- L'onglet « Non classées » devient une **inbox** : suggestion par transaction, validation en un clic,
  création automatique de la règle correspondante.

**Résultat : c'est la réponse à « faciliter les mappings ». Les calculs ne bougent pas d'un centime.**

## Étape 4 — Socle multi-comptes + ingestion unifiée

- Entité `BankAccount` (compte bancaire lié à une propriété), `Transaction.external_id` + `account_id`.
- Dédoublonnage par identifiant externe unique `(property_id, external_id)` — fini le match date+montant+nom en float.
- Service d'ingestion **commun** : CSV et API bancaire passent par le même tuyau
  (normalisation → dedup → classification → recalculs), le tout dans une seule transaction DB.

**Résultat : invisible à l'écran, mais indispensable pour la banque. Corrige aussi le dedup multi-propriétés.**

## Étape 5 — Enable Banking (maquette ③)

- Client API (app enregistrée, clé privée + JWT — même pattern que les autres projets de Louis).
- Écran « Sources » : connecter sa banque (consentement PSD2), comptes liés par propriété,
  synchro auto quotidienne + bouton manuel, alerte renouvellement de consentement (~180 jours).
- Les nouvelles transactions tombent dans l'inbox, déjà pré-classées par les règles.
- L'import CSV reste disponible (historique / banques non connectées).

**Résultat : plus de CSV à télécharger. Banque → inbox → un clic → CR à jour.**

## Étape 6 (option métier) — Fiscalité LMNP avancée

- **Article 39C** : plafonnement de l'amortissement déductible (ne peut pas creuser le déficit),
  report illimité de l'excédent, distinction déficits reportables 10 ans vs amortissements différés.
- **Ventilation par composants assistée** : part terrain non amortissable (~10-20 %),
  structure / façade / IGT / agencements avec durées standards.
- Objectif final possible : montants prêts pour la liasse 2031/2033.

**Résultat : un résultat fiscal juste, pas seulement un résultat comptable.**

---

## Ce qui change au quotidien (résumé UX)

- **Aujourd'hui** : télécharger le CSV → l'importer → vérifier le mapping des colonnes → aller dans
  « Non classées » → éditer à la main ou maintenir l'Excel de mappings → espérer que le CR est à jour.
- **Après** : ouvrir l'app → l'inbox affiche 2-3 transactions avec suggestions → un clic → tout est à jour.
  Les écrans TCD, États financiers, Amortissements restent visuellement identiques — c'est voulu.

## Prochaine étape

Brainstorm structuré (Step 1 de la méthodo) pour verrouiller le périmètre, puis PRD.
Maquettes de référence : serveur ui-mockup, fichier `refonte-v1.html` (inbox, règles, sources, temps réel).
