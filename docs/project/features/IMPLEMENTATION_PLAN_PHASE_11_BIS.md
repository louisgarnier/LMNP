# Phase 11 bis : Prévisions annuelles (Forecast) pour Compte de Résultat et Bilan

**Status**: ⏳ À FAIRE  
**Environnement**: Local uniquement  
**Durée estimée**: 1-2 semaines
**Prérequis**: Phase 11 (Multi-propriétés) complétée

---

## Objectif

Permettre d'afficher des données **cohérentes pour l'année en cours** dans le Compte de Résultat et le Bilan, même si toutes les transactions n'ont pas encore eu lieu.

### Problème actuel
- En janvier 2026, les données affichées sont incomplètes (1 mois de loyers, 0€ de taxe foncière)
- Impossible de comparer avec les années précédentes
- Chiffres non représentatifs de l'année complète

### Solution
- L'utilisateur entre les **montants prévus annuels** par catégorie comptable
- Le système affiche `MAX(réel, prévu)` pour chaque catégorie
- Option de **projection sur X années futures** avec taux d'évolution

---

## ⚠️ Règles métier importantes

### 1. Catégories CALCULÉES vs CONFIGURABLES

Il existe **deux types de catégories** :

#### Catégories CALCULÉES (lecture seule - valeurs réelles du système)
Ces catégories sont calculées automatiquement, l'utilisateur **ne peut pas les modifier** :

**Compte de Résultat :**
- Dotations aux amortissements (calculé depuis `amortization_service`)
- Charges d'intérêts (calculé depuis `LoanPayments`)

**Bilan - ACTIF :**
- Amortissements cumulés (calculé depuis `amortization_service`)
- Compte bancaire (solde réel des transactions)

**Bilan - PASSIF :**
- Résultat de l'exercice (vient du Compte de Résultat)
- Report à nouveau (cumulé des exercices précédents)
- Capital restant dû (calculé depuis `LoanPayments` et transactions)

#### Catégories CONFIGURABLES (utilisateur entre le prévu)
L'utilisateur peut saisir un montant prévu annuel :

**Compte de Résultat :**
- Loyers, Taxe foncière, Assurance PNO, Charges copropriété, Entretien, Frais gestion, Autres

**Bilan - ACTIF :**
- Immobilisations corporelles, Frais d'acquisition

**Bilan - PASSIF :**
- Capital, Dettes fournisseurs, Autres dettes

### 2. Logique d'affichage

```
Pour les catégories CONFIGURABLES :
  montant_affiché = MAX(réel, prévu)

Pour les catégories CALCULÉES :
  montant_affiché = valeur_réelle (toujours)
```

### 3. Colonnes de référence

Pour aider la saisie, le tableau affiche :
- **Réel 2026** : montant des transactions de l'année en cours
- **Année 2025** : montant total de l'année précédente (référence)
- **Prévu 2026** : champ de saisie pour le montant prévu
- **Évol. %/an** : taux d'évolution pour les années futures

### 4. Bouton "Pré-remplir avec 2025"

Copie les valeurs de l'année précédente dans "Prévu 2026" pour toutes les catégories configurables.

### 5. Multi-propriétés

- Chaque propriété a sa propre configuration de prévisions
- Filtrage par `property_id` obligatoire
- Rechargement des données au changement de propriété

---

## Vue d'ensemble des étapes

| Step | Description | Testable |
|------|-------------|----------|
| 11bis.1 | Modèle de données + CRUD + Card basique | ✅ Card s'affiche et sauvegarde |
| 11bis.2 | Logique MAX(réel, prévu) | ✅ API retourne données modifiées |
| 11bis.3 | Intégration Compte de Résultat | ✅ CR affiche données avec prévisions |
| 11bis.4 | Intégration Bilan (ACTIF + PASSIF) | ✅ Bilan affiche données avec prévisions |
| 11bis.5 | Projection multi-années (Forecast) | ✅ Colonnes futures affichées |
| 11bis.6 | Tests et validation | ✅ Tests automatisés |

---

## Step 11bis.1 : Modèle de données + CRUD + Card basique

**Objectif**: Créer la table, les endpoints, et la card frontend pour tester immédiatement

### Base de données

**Table `annual_forecast_configs`** :
- `id` (PK)
- `property_id` (FK → properties, CASCADE)
- `year` (int) - Année de base
- `level_1` (string) - Catégorie comptable
- `target_type` (string) - "compte_resultat", "bilan_actif", "bilan_passif"
- `base_annual_amount` (float) - Montant prévu annuel
- `annual_growth_rate` (float) - Taux d'évolution (0.02 = +2%)
- `created_at`, `updated_at`

**Table `prorata_settings`** :
- `id` (PK)
- `property_id` (FK → properties, CASCADE, UNIQUE)
- `prorata_enabled` (bool) - Activer prévisions année en cours
- `forecast_enabled` (bool) - Activer projection multi-années
- `forecast_years` (int) - Nombre d'années à projeter (1-10)

### Endpoints API

- `GET /api/prorata-settings?property_id=X` → Récupérer settings
- `PUT /api/prorata-settings?property_id=X` → Mettre à jour settings
- `GET /api/forecast-configs?property_id=X&year=Y&target_type=Z` → Récupérer configs
- `POST /api/forecast-configs/bulk?property_id=X` → Créer/MAJ plusieurs configs
- `GET /api/forecast-configs/reference-data?property_id=X&year=Y&target_type=Z` → Données de référence

### Frontend - Composant ProRataForecastCard

Affiche un tableau avec :
| Catégorie | Réel 2026 | Année 2025 | Prévu 2026 | Évol. %/an |
|-----------|-----------|------------|------------|------------|
| Loyers | 8 500 € | 14 400 € | [input] | [input] |
| Dotations aux amortissements | 5 200 € | 5 200 € | *(calculé)* | — |

- Checkboxes : "Activer prévisions année en cours" + "Projeter sur X années"
- Bouton "Pré-remplir avec 2025"
- Bouton "Sauvegarder"
- Les catégories calculées sont en lecture seule (grisées)

### Tests Step 11bis.1
- [ ] Tables créées
- [ ] CRUD endpoints fonctionnent
- [ ] Filtrage par property_id
- [ ] Card frontend affiche les données
- [ ] Sauvegarde fonctionne

---

## Step 11bis.2 : Logique MAX(réel, prévu)

**Objectif**: Implémenter la logique de calcul dans les services

### Service prorata_service.py (NOUVEAU)

Fonctions :
- `get_prorata_settings(db, property_id)` → Settings ou None
- `get_forecast_configs(db, property_id, year, target_type)` → Dict[level_1, amount]
- `apply_prorata(db, property_id, year, target_type, real_amounts)` → Dict avec MAX appliqué

### Tests Step 11bis.2
- [ ] Si désactivé → retourne montants réels
- [ ] Si activé → retourne MAX(réel, prévu)
- [ ] Cas réel > prévu → retourne réel
- [ ] Cas réel < prévu → retourne prévu
- [ ] Cas réel = 0 → retourne prévu

---

## Step 11bis.3 : Intégration Compte de Résultat

**Objectif**: Intégrer les prévisions dans le Compte de Résultat

### Backend - compte_resultat_service.py

1. Définir liste `CALCULATED_CATEGORIES_CR` (amortissements, intérêts)
2. Après calcul des montants réels, appeler `apply_prorata()` uniquement sur les catégories configurables
3. Fusionner : calculées (réelles) + configurables (ajustées)

### Frontend - etats-financiers/page.tsx

- Ajouter `<ProRataForecastCard targetType="compte_resultat" />` sous le tableau CR
- Callback `onConfigChange` pour rafraîchir le tableau

### Tests Step 11bis.3
- [ ] CR sans prévisions → affiche montants réels
- [ ] CR avec prévisions → affiche MAX pour catégories configurables
- [ ] Amortissements/intérêts → toujours valeurs réelles
- [ ] Taxe foncière (réel=0) → affiche prévu
- [ ] Loyers (réel>prévu) → affiche réel
- [ ] Bouton pré-remplir fonctionne

---

## Step 11bis.4 : Intégration Bilan (ACTIF + PASSIF)

**Objectif**: Intégrer les prévisions dans le Bilan

### Backend - bilan_service.py

1. Définir liste `CALCULATED_CATEGORIES_BILAN` (amortissements cumulés, compte bancaire, résultat exercice, report à nouveau, capital restant dû)
2. Appeler `apply_prorata()` séparément pour actif et passif
3. `target_type` = "bilan_actif" ou "bilan_passif"

### Frontend - etats-financiers/page.tsx

Ajouter 2 cards sous le tableau Bilan :
- `<ProRataForecastCard targetType="bilan_actif" sectionTitle="ACTIF" />`
- `<ProRataForecastCard targetType="bilan_passif" sectionTitle="PASSIF" />`

Note : les checkboxes (activer prévisions) ne s'affichent que sur la première card

### Équilibre Actif = Passif

⚠️ Si l'utilisateur modifie des catégories, le bilan peut être déséquilibré.
→ Afficher un **avertissement** si Actif ≠ Passif après application des prévisions

### Tests Step 11bis.4
- [ ] Bilan sans prévisions → affiche montants réels
- [ ] Bilan avec prévisions → MAX pour catégories configurables
- [ ] Catégories calculées → toujours valeurs réelles
- [ ] 2 cards distinctes (ACTIF / PASSIF)
- [ ] Avertissement si déséquilibre

---

## Step 11bis.4.bis : Projection Bilan - Année en cours (par étapes)

⚠️ **Important (ordre strict)** :  
- On commence par **l’interface et les explications** (aucun changement de calcul backend).  
- Ensuite seulement, si les chiffres sont compris et validés, on pourra éventuellement faire évoluer le calcul du **Compte bancaire**.

### 11bis.4.bis.1 – Frontend : encadré de l’année en cours + card d’explication (sans changer les chiffres)

#### 11bis.4.bis.1.a – Remettre l’encadré bleu sur la colonne de l’année en cours (BilanTable)

**Objectif**: avoir le même repère visuel que pour le Compte de Résultat.

- Dans `BilanTable` :
  - Re-mettre un **encadré bleu léger** sur toute la colonne de l’année en cours (par ex. 2026) :
    - Bordure gauche et droite bleues sur cette colonne,
    - Optionnel : mention `(en cours)` dans l’en-tête de colonne.
- Ne **rien changer** d’autre :
  - Pas de nouvelles colonnes,
  - Pas de changements de valeurs.

**Tests 11bis.4.bis.1.a** :
- [ ] Sur l’onglet Bilan, la colonne de l’année en cours est clairement encadrée en bleu sur toute la hauteur.  
- [ ] Les montants du Bilan (toutes lignes, toutes années) sont **strictement identiques** à l’état actuel (avant encadré).

#### 11bis.4.bis.1.b – Ajouter une card "📊 Prévisions Bilan - Année en cours (explication)"

**Objectif**: expliquer ce qui se passe aujourd’hui, **sans modifier aucun calcul**.

- Ajouter sous le tableau Bilan une card, par exemple :
  - Titre : **📊 Prévisions Bilan - Année en cours (2026)**.
  - Deux blocs explicatifs :

**Bloc 1 – Compte courant d’associé (CCA)**  
- Rappeler que le CCA garde **exactement** son comportement actuel :
  - Le CCA est déterminé uniquement par les **transactions taguées CCA**.
  - Pour l’année en cours N (ex. 2026) :  
    \( \text{CCA}_N = \text{CCA}_{N-1} + \sum \text{transactions CCA de l'année N} \)
- Afficher dans la card :
  - La valeur CCA N-1 (lue dans le Bilan),
  - La **somme des transactions CCA de l’année N** (calculée à partir des transactions),
  - La valeur CCA N (lue dans le Bilan).

**Bloc 2 – Compte bancaire (état actuel, sans forecast)**  
- Expliquer simplement le comportement actuel :
  - Le Compte bancaire affiché dans le Bilan pour l’année N est **100% réel**, basé sur les transactions bancaires jusqu’à la fin de l’année.
- Afficher dans la card :
  - Compte bancaire N-1 (valeur Bilan),
  - Compte bancaire N (valeur Bilan),
  - Variation simple N – N-1 (optionnelle, à titre informatif).

**⚠️ À ce stade :**
- Aucun "cash forecasté" n’est calculé ni utilisé.
- Le but est uniquement de **documenter** et **rendre lisible** ce que fait déjà le système.

**Tests 11bis.4.bis.1.b** :
- [ ] La card s’affiche bien sous le tableau Bilan.  
- [ ] Les valeurs CCA N-1, CCA N et somme des transactions CCA N sont cohérentes entre la card, les transactions et le Bilan.  
- [ ] Les valeurs Compte bancaire N-1 et N affichées dans la card sont strictement égales à celles du Bilan.

> Tant que cette étape n’est pas validée visuellement et fonctionnellement, **on ne touche pas au calcul du Compte bancaire dans le backend.**

---

### 11bis.4.bis.2 – (Optionnel, après validation) Introduire le cash forecasté dans la card uniquement

**Objectif**: commencer à présenter la logique "cash réel + cash forecasté" dans la card, sans modifier encore la valeur utilisée par le Bilan.

1. **Définir dans le backend (bilan_service)**, pour l’année en cours N :
   - `cash_reel_N_1` = solde bancaire réel au 31/12/N-1 (réutiliser la logique existante),
   - `cash_forecast_N` = delta de cash projeté pour N basé sur :
     - les montants "Prévu N" du Compte de Résultat (catégories de produits encaissés + charges cash hors amortissements),
     - les remboursements de crédit (capital + intérêts + assurance) de l’onglet Crédit,
     - en neutralisant les montants prévus qui alimentent le CCA.
   - `compte_bancaire_simule_N = cash_reel_N_1 + cash_forecast_N`.

2. **Exposer ces 3 valeurs uniquement pour l’année en cours** dans la réponse Bilan (sans casser le schéma actuel).

3. **Mettre à jour la card** pour afficher :
   - "Cash réel 31/12/N-1 : X €",
   - "Cash forecasté N : Y €",
   - "Compte bancaire simulé N : Z € = X + Y".

**Tests 11bis.4.bis.2** :
- [ ] Vérifier par script de debug que X, Y et Z sont cohérents et stables pour au moins une propriété (Evry).  
- [ ] Vérifier que le Bilan continue d’utiliser la **même valeur Compte bancaire N qu’avant** (pas encore branchée sur Z).  
- [ ] Vérifier que X + Y = Z dans la card.

---

### 11bis.4.bis.3 – (Optionnel, après validation 11bis.4.bis.2) Brancher la simulation sur le Compte bancaire du Bilan

**Objectif**: si et seulement si les chiffres de la card sont jugés corrects et utiles, utiliser `compte_bancaire_simule_N` dans la cellule Bilan "Compte bancaire" de l’année en cours.

1. **Remplacer**, pour la seule année en cours N, la valeur du Compte bancaire dans la structure Bilan par `compte_bancaire_simule_N` (Z).
2. Ajouter un **tooltip** sur la cellule "Compte bancaire / année N" qui affiche :
   - `Cash réel (31/12/N-1) : X €`,
   - `+ Cash forecasté N : Y €`,
   - `= Compte bancaire N : Z €`.

**Tests 11bis.4.bis.3** :
- [ ] Vérifier que pour l’année N, la valeur "Compte bancaire" du Bilan est bien Z (et que la card et le tooltip racontent la même histoire).  
- [ ] Vérifier que l’équilibre Actif = Passif est toujours respecté (ou différence < tolérance d’arrondis).  
- [ ] Vérifier qu’aucune autre année (N-1, N-2, etc.) n’a été impactée par cette modification.

---

## Step 11bis.5 : Projection multi-années (Forecast)

**Objectif**: Projeter les montants sur plusieurs années futures

### Formule de calcul

```
montant_année_N+X = base_annual_amount × (1 + annual_growth_rate)^X
```

Exemple avec Loyers = 14,400 € et taux = +2% :
- 2026 : 14,400 €
- 2027 : 14,688 €
- 2028 : 14,982 €
- 2029 : 15,281 €

### Backend

Ajouter dans `prorata_service.py` :
- `calculate_forecast_amount(base, rate, years_ahead)`
- `get_forecast_for_year(db, property_id, base_year, target_year, target_type)`

### Frontend

Si `forecast_enabled` :
- Ajouter colonnes pour les années futures dans les tableaux CR et Bilan
- Colonnes en lecture seule (calculées automatiquement)

### Tests Step 11bis.5
- [ ] Calcul année+1 correct
- [ ] Calcul année+3 correct
- [ ] Taux négatif fonctionne
- [ ] Colonnes futures affichées

---

## Step 11bis.6 : Tests et validation

### Tests d'isolation
- [ ] Config propriété A n'affecte pas propriété B
- [ ] Changement de propriété recharge les données

### Tests de persistance
- [ ] Configs sauvegardées au refresh
- [ ] Settings sauvegardés au refresh

### Tests de cas limites
- [ ] Année sans transactions
- [ ] Catégorie sans config → montant = 0 ou réel
- [ ] Taux d'évolution = 0
- [ ] Taux d'évolution négatif

---

## Récapitulatif des fichiers

### Backend - CRÉER
- `backend/api/routes/prorata_forecast.py`
- `backend/api/services/prorata_service.py`
- `backend/database/migrations/add_forecast_tables.py`

### Backend - MODIFIER
- `backend/database/models.py` (ajouter AnnualForecastConfig, ProRataSettings)
- `backend/api/models.py` (ajouter Pydantic models)
- `backend/api/main.py` (enregistrer router)
- `backend/api/services/compte_resultat_service.py` (intégrer apply_prorata)
- `backend/api/services/bilan_service.py` (intégrer apply_prorata)

### Frontend - CRÉER
- `frontend/src/components/ProRataForecastCard.tsx`

### Frontend - MODIFIER
- `frontend/src/api/client.ts` (ajouter prorataAPI)
- `frontend/app/dashboard/etats-financiers/page.tsx` (intégrer les cards)

---

**Dernière mise à jour**: 03/02/2026
