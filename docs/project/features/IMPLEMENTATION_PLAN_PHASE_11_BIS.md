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
