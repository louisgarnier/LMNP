# Plan d'Implémentation - Phase 6 : Fonctionnalité 3 - Calcul des amortissements

**Status**: En attente  
**Dernière mise à jour**: 2025-01-XX

## Vue d'ensemble

**Objectif** : Créer l'onglet "Amortissements" avec configuration, calcul automatique et affichage en tableau croisé.

**Fonctionnalités principales** :

- Configuration des types d'amortissement (7 types initiaux)
- Calcul automatique des amortissements avec convention 30/360
- Affichage en tableau croisé (années × catégories)
- Drill-down vers les transactions détaillées
- Recalcul automatique après modification de transactions

**Ordre d'implémentation optimisé pour tests frontend progressifs :**

1. **Backend** : Configuration + Tables + Service (Steps 6.1, 6.2)

2. **Backend** : Endpoints API (Step 6.4)

3. **Frontend** : Vue tableau croisé (Step 6.6)

4. **Backend** : Recalcul automatique (Step 6.8)

5. **Frontend** : Intégration et tests finaux (Step 6.7)

---

### Step 6.1 : Backend - Table AmortizationType

**Status**: ✅ COMPLÉTÉ  

**Description**: Créer la table `amortization_types` pour stocker les types d'amortissement.

**Objectifs**:

- Créer modèle SQLAlchemy `AmortizationType`

- Créer migration pour créer la table

- Créer script pour initialiser les 7 types par défaut

**Tasks**:

- [x] Créer modèle `AmortizationType` dans `backend/database/models.py` :

  - `id`, `name`, `level_2_value`, `level_1_values` (JSON), `start_date` (nullable), `duration`, `annual_amount` (nullable)

  - Index sur `level_2_value`

- [x] Créer script d'initialisation `backend/scripts/init_amortization_types.py` :

  - Créer 7 types initiaux si la table est vide

  - Noms par défaut : "Immobilisation terrain", "Immobilisation structure/GO", "Immobilisation mobilier", "Immobilisation IGT", "Immobilisation agencements", "Immobilisation Facade/Toiture", "Immobilisation travaux"

- [x] Exécuter script et valider

- [x] **Créer test unitaire pour le modèle**

- [x] **Valider avec l'utilisateur**

**Deliverables**:

- `backend/database/models.py` - Modèle `AmortizationType`

- `backend/scripts/init_amortization_types.py` - Script d'initialisation

- `backend/tests/test_amortization_type.py` - Tests unitaires

**Acceptance Criteria**:

- [x] Table `amortization_types` créée

- [x] 7 types initiaux créés automatiquement si table vide

- [x] Modèle SQLAlchemy fonctionnel

- [x] Tests unitaires passent (4 tests)

---

### Step 6.2 : Backend - Table et service calcul amortissements

**Status**: ✅ COMPLÉTÉ  

**Description**: Créer table BDD pour stocker les résultats d'amortissements et service de calcul.

**Objectifs**:

- Table `amortization_results` pour stocker les résultats

- Service de calcul avec convention 30/360

- Recalcul automatique lors des changements de transactions

**Tasks**:

- [x] Créer table `amortization_results` avec colonnes :

  - `id` (PK)

  - `transaction_id` (FK vers Transaction)

  - `year` (année, ex: 2021, 2022)

  - `category` (type: meubles, travaux, construction, terrain)

  - `amount` (montant amorti pour cette année, négatif)

  - `created_at`, `updated_at`

- [x] Créer modèle SQLAlchemy `AmortizationResult`

- [x] Créer service `amortization_service.py` avec :

  - Fonction `calculate_30_360_days(start_date, end_date)`

  - Fonction `calculate_yearly_amounts(start_date, total_amount, duration)`

  - Fonction `recalculate_all_amortizations()` - Recalcul complet

  - Fonction `recalculate_transaction_amortization(transaction_id)` - Recalcul pour une transaction

- [x] Implémenter logique Yearly Amount Distribution :

  - Calcul montant journalier (total_amount / total_days)

  - Répartition proportionnelle par année

  - Dernière année = solde restant pour garantir somme exacte

- [x] Validation : vérifier que somme des amortissements = montant initial

- [x] **Créer test complet avec calculs réels** (8 tests, tous passés)

- [x] Service utilise `AmortizationType` pour le matching des transactions :

  - `recalculate_transaction_amortization()` utilise les `AmortizationType` configurés

  - Gestion de `start_date` override depuis le type

  - Gestion de `annual_amount` override depuis le type

  - Stockage du nom du type dans `AmortizationResult.category`

- [x] **Valider avec l'utilisateur**

**Deliverables**:

- `backend/database/models.py` - Modèle `AmortizationResult`

- `backend/api/services/amortization_service.py` - Service calcul amortissements (utilise AmortizationType)

- `backend/tests/test_amortization_service.py` - Tests amortissements (8 tests)

**Tests**:

- [x] Test calcul convention 30/360

- [x] Test répartition proportionnelle

- [x] Test 4 catégories (meubles, travaux, construction, terrain)

- [x] Test validation somme = montant initial

- [x] Test recalcul complet

- [x] Test recalcul transaction unique

**Acceptance Criteria**:

- [x] Calculs d'amortissements corrects (convention 30/360)

- [x] Répartition proportionnelle validée

- [x] Validation somme = montant initial

- [x] Stockage en DB fonctionnel

- [x] Service utilise `AmortizationType` pour le matching des transactions

- [x] Gestion de `start_date` override depuis le type

- [x] Gestion de `annual_amount` override depuis le type

- [x] **Utilisateur confirme que les calculs sont corrects**

---

---

### Step 6.4 : Backend - Endpoints API amortissements

**Status**: ✅ COMPLÉTÉ  

**Description**: Créer endpoints API pour récupérer les résultats d'amortissements.

**Tasks**:

- [x] Créer endpoint `GET /api/amortization/results` :
  - Retourne résultats agrégés par année et catégorie
  - Format : `{ year: { category: amount, ... }, ... }`

  - Inclure ligne Total et colonne Total

- [x] Créer endpoint `GET /api/amortization/results/aggregated` :

  - Retourne tableau croisé prêt pour affichage

  - Format : `{ categories: [...], years: [...], data: [[...], ...], totals: {...} }`

- [x] Créer endpoint `GET /api/amortization/results/details` :

  - Paramètres : `year` (optionnel), `category` (optionnel)

  - Retourne liste des transactions correspondantes (avec pagination)

  - Utilisé pour drill-down depuis le tableau croisé

- [x] Créer endpoint `POST /api/amortization/recalculate` :

  - Force recalcul complet de tous les amortissements

  - Utile pour recalculer après changement de config

- [x] **Créer test manuel** (script de test)

- [x] **Valider avec l'utilisateur**

**Deliverables**:

- `backend/api/routes/amortization.py` - Endpoints API (4 endpoints)

- `backend/api/models.py` - Modèles Pydantic pour réponses (AmortizationResultsResponse, AmortizationAggregatedResponse, AmortizationRecalculateResponse)

- `backend/tests/test_amortization_endpoints_manual.py` - Script de test manuel

**Acceptance Criteria**:

- [x] Endpoints retournent données correctes

- [x] Format adapté pour affichage frontend

- [x] Totaux calculés correctement

- [x] Pagination fonctionne pour details endpoint

- [x] Filtres (year, category) fonctionnent pour details endpoint

- [x] **Utilisateur confirme que les endpoints fonctionnent**


---

### Step 6.6 : Frontend - Vue amortissements (tableau croisé)

**Status**: ⏳ EN ATTENTE  

**Description**: Créer page et composant pour afficher les amortissements en tableau croisé.

**Tasks**:

- [ ] Créer page `frontend/app/dashboard/amortissements/page.tsx`

- [ ] Créer composant `AmortizationTable.tsx` :

  - Tableau croisé : années en colonnes, catégories en lignes

  - Ligne Total en bas

  - Colonne Total à droite

  - Formatage montants : 2 décimales, négatifs en rouge

- [ ] Appeler API `GET /api/amortization/results/aggregated`

- [ ] Gérer état de chargement

- [ ] Afficher message si aucune configuration

- [ ] Afficher message si aucun résultat

- [ ] Rendre les cellules cliquables (sauf totaux) - handler prêt pour Step 6.6.1

- [ ] **Créer test visuel dans navigateur**

- [ ] **Valider avec l'utilisateur**

**Deliverables**:

- `frontend/app/dashboard/amortissements/page.tsx` - Page amortissements

- `frontend/src/components/AmortizationTable.tsx` - Tableau amortissements

- Mise à jour `frontend/src/api/client.ts` - Méthodes API amortissements

**Acceptance Criteria**:

- [ ] Tableau des amortissements s'affiche

- [ ] Répartition par catégorie et année visible

- [ ] Ligne Total et colonne Total correctes

- [ ] Formatage montants correct (2 décimales, négatifs en rouge)

- [ ] Cellules cliquables (sauf totaux) - handler prêt pour drill-down

- [ ] **Utilisateur confirme que la vue fonctionne**

---

#### Step 6.6.1: Backend - API Endpoints AmortizationType

**Status**: ✅ COMPLÉTÉ  

**Description**: Créer les endpoints API pour gérer les types d'amortissement.

**Objectifs**:

- CRUD complet pour `AmortizationType`

- Endpoint pour calculer les montants et cumulés

**Tasks**:

- [x] Créer `backend/api/models.py` - Modèles Pydantic :

  - `AmortizationTypeBase`, `AmortizationTypeCreate`, `AmortizationTypeUpdate`, `AmortizationTypeResponse`

  - `AmortizationTypeListResponse`, `AmortizationTypeAmountResponse`, `AmortizationTypeCumulatedResponse`

  - `AmortizationTypeTransactionCountResponse`

- [x] Créer `backend/api/routes/amortization_types.py` :

  - `GET /api/amortization/types` - Liste tous les types

  - `POST /api/amortization/types` - Créer un type

  - `GET /api/amortization/types/{id}` - Récupérer un type

  - `PUT /api/amortization/types/{id}` - Mettre à jour un type

  - `DELETE /api/amortization/types/{id}` - Supprimer un type

  - `GET /api/amortization/types/{id}/amount` - Calculer montant d'immobilisation

  - `GET /api/amortization/types/{id}/cumulated` - Calculer montant cumulé

  - `GET /api/amortization/types/{id}/transaction-count` - Compter transactions

- [x] Intégrer dans `backend/api/main.py`

- [x] **Créer tests API (script de test manuel)**

- [x] **Valider avec l'utilisateur**

**Deliverables**:

- `backend/api/models.py` - Modèles Pydantic

- `backend/api/routes/amortization_types.py` - Routes API

- Mise à jour `backend/api/main.py`

- `backend/tests/test_amortization_types_endpoints_manual.py` - Tests manuels

**Acceptance Criteria**:

- [x] Tous les endpoints créés (8 endpoints)

- [x] Validation des données (durée obligatoire, etc.)

- [x] Imports validés

- [x] Tests manuels exécutés (8/8 passés)

---

#### Step 6.6.2: Frontend - Card de configuration (structure de base)

**Status**: ⏳ EN ATTENTE  

**Description**: Créer la card de configuration au-dessus du tableau année par année.

**Objectifs**:

- Afficher une card vide au-dessus de `AmortizationTable`

- Supprimer le panneau latéral actuel

- **Masquer le tableau quand aucune valeur Level 2 n'est disponible**

**Tasks**:

- [ ] Créer composant `AmortizationConfigCard.tsx` :

  - Card avec titre "Configuration des amortissements"

  - Structure de base (vide pour l'instant)

- [ ] Modifier `frontend/app/dashboard/amortissements/page.tsx` :

  - Afficher `AmortizationConfigCard` au-dessus de `AmortizationTable`

  - Supprimer `AmortizationConfigPanel` (panneau latéral)

- [ ] **Masquer le tableau quand `level2Values.length === 0`** :

  - Condition `{level2Values.length > 0 && (...)}` autour du tableau

  - Aucun affichage si "Aucune valeur disponible" est affiché dans le dropdown

- [ ] **Créer test visuel dans navigateur**

- [ ] **Valider avec l'utilisateur**

**Deliverables**:

- `frontend/src/components/AmortizationConfigCard.tsx` - Card de configuration

- Mise à jour `frontend/app/dashboard/amortissements/page.tsx`

**Acceptance Criteria**:

- [ ] Card s'affiche au-dessus du tableau

- [ ] Panneau latéral supprimé

- [ ] Layout correct

- [ ] **Tableau masqué quand aucune valeur Level 2 n'est disponible**

---

#### Step 6.6.3: Frontend - Champ Level 2

**Status**: ⏳ EN ATTENTE  

**Description**: Ajouter le champ "Level 2" en haut de la card.

**Objectifs**:

- Dropdown pour sélectionner la valeur `level_2`

- Charger les valeurs uniques depuis l'API

- Sauvegarde automatique

- **Empêcher la sélection de "-- Sélectionner une valeur --" une fois qu'un Level 2 est sélectionné**

- **Persistance du Level 2 sélectionné via localStorage**

**Tasks**:

- [ ] Ajouter champ "Level 2" dans `AmortizationConfigCard.tsx` :

  - Dropdown avec valeurs uniques de `level_2`

  - Il faut que ce soit des checkbox pour sélectionner un seul level 2 possible

  - Utiliser `transactionsAPI.getUniqueValues('level_2')`

  - État local pour la valeur sélectionnée

  - **Option "-- Sélectionner une valeur --" affichée uniquement si aucun Level 2 n'est sélectionné**

  - **Option masquée une fois qu'un Level 2 est sélectionné**

- [ ] Sauvegarde automatique sur changement (`onChange`)

- [ ] **Persistance dans localStorage** : sauvegarder et restaurer le Level 2 sélectionné

- [ ] **Empêcher la désélection** : ignorer toute tentative de sélectionner une valeur vide si un Level 2 est déjà sélectionné

- [ ] **Créer test visuel dans navigateur**

- [ ] **Valider avec l'utilisateur**

**Deliverables**:

- Mise à jour `frontend/src/components/AmortizationConfigCard.tsx`

**Acceptance Criteria**:

- [ ] Dropdown s'affiche avec les valeurs

- [ ] Sélection fonctionne

- [ ] **Option "-- Sélectionner une valeur --" masquée une fois qu'un Level 2 est sélectionné**

- [ ] **Impossible de revenir à "-- Sélectionner une valeur --" après sélection**

- [ ] **Persistance du Level 2 sélectionné via localStorage**

- [ ] État local géré (sauvegarde dans types d'amortissement à venir)

---

#### Step 6.6.4: Frontend - Tableau (structure vide)

**Status**: ⏳ EN ATTENTE  

**Description**: Créer la structure du tableau dans la card.

**Objectifs**:

- Tableau HTML avec en-têtes de colonnes

- Pas de données pour l'instant

**Tasks**:

- [ ] Ajouter tableau dans `AmortizationConfigCard.tsx` :

  - En-têtes : Type d'immobilisation, Level 1 (valeurs), **Nombre de transactions**, Date de début, Montant, Durée, Annuité, Cumulé, VNC

  - Structure `<table>` avec `<thead>` et `<tbody>` vide

- [ ] Style cohérent avec le reste de l'app

- [ ] **Masquer le tableau quand `level2Values.length === 0`** (ajouté dans Step 6.6.2)

- [ ] **Créer test visuel dans navigateur**

- [ ] **Valider avec l'utilisateur**

**Deliverables**:

- Mise à jour `frontend/src/components/AmortizationConfigCard.tsx`

**Acceptance Criteria**:

- [ ] Tableau s'affiche avec en-têtes

- [ ] Style correct

- [ ] Structure prête pour les données

- [ ] **Tableau masqué quand aucune valeur Level 2 n'est disponible**

---

#### Step 6.6.5: Frontend - Colonne "Type d'immobilisation"

**Status**: ⏳ EN ATTENTE  

**Description**: Ajouter la colonne "Type d'immobilisation" avec les 7 types initiaux.

**Objectifs**:

- Afficher les 7 types initiaux dans le tableau

- Champ texte éditable pour chaque type

- Charger depuis l'API au démarrage

**Tasks**:

- [ ] Ajouter logique pour charger les types depuis `GET /api/amortization/types`

- [ ] Afficher les 7 types initiaux (créés automatiquement si inexistants)

- [ ] Colonne "Type d'immobilisation" : champ texte éditable (clic pour éditer)

- [ ] Sauvegarde automatique sur `onBlur` (ou Enter/Escape)

- [ ] **Créer test visuel dans navigateur**

- [ ] **Valider avec l'utilisateur**

**Deliverables**:

- Mise à jour `frontend/src/components/AmortizationConfigCard.tsx`

- Mise à jour `frontend/src/api/client.ts` - Méthode `amortizationTypesAPI.getAll()`

**Acceptance Criteria**:

- [ ] 7 types initiaux s'affichent (créés automatiquement si inexistants)

- [ ] Édition du nom fonctionne (clic pour éditer, onBlur/Enter pour sauvegarder)

- [ ] Sauvegarde automatique fonctionne

---

#### Step 6.6.6: Frontend - Colonne "Level 1 (valeurs)"

**Status**: ⏳ EN ATTENTE  

**Description**: Ajouter la colonne "Level 1 (valeurs)" avec multi-select.

**Objectifs**:

- Multi-select pour mapper les valeurs `level_1` à chaque type

- Charger les valeurs uniques depuis l'API

- **Filtrer les valeurs `level_1` par le `level_2` sélectionné** (ex: si `level_2 = "ammortissements"`, ne montrer que les `level_1` associés)

- Sauvegarde automatique

**Tasks**:

- [ ] Ajouter colonne "Level 1 (valeurs)" :

  - Multi-select dropdown

  - Utiliser `transactionsAPI.getUniqueValues('level_1', undefined, undefined, level2Value)`

  - Afficher les valeurs sélectionnées sous forme de tags bleus

  - Bouton "+" pour ajouter une valeur

  - Bouton "×" sur chaque tag pour supprimer

- [ ] **Backend - Ajouter paramètre `filter_level_2` à `/api/transactions/unique-values`**

- [ ] **Frontend - Filtrer les valeurs `level_1` par `level2Value`**

- [ ] **Recharger automatiquement les valeurs `level_1` quand `level2Value` change**

- [ ] Sauvegarde automatique sur changement

- [ ] **Créer test visuel dans navigateur**

- [ ] **Valider avec l'utilisateur**

**Deliverables**:

- Mise à jour `backend/api/routes/transactions.py` (endpoint `get_transaction_unique_values`)

- Mise à jour `frontend/src/api/client.ts` (méthode `getUniqueValues`)

- Mise à jour `frontend/src/components/AmortizationConfigCard.tsx`

**Acceptance Criteria**:

- [ ] Multi-select fonctionne

- [ ] Ajout/suppression de valeurs fonctionne

- [ ] **Filtrage par `level_2` fonctionne (seules les valeurs `level_1` associées au `level_2` sélectionné sont affichées)**

- [ ] Sauvegarde automatique fonctionne

---

#### Step 6.6.7: Frontend - Colonne "Date de début"

**Status**: ⏳ EN ATTENTE  

**Description**: Ajouter la colonne "Date de début" (input date).

**Objectifs**:

- Champ date éditable (nullable)

- **Permettre de supprimer la date (retour à NULL)**

- Sauvegarde automatique

- **Comportement** : Si `start_date` est NULL, utiliser les dates des transactions. Si une date est définie, elle override les dates des transactions pour le calcul d'amortissement.

**Tasks**:

- [ ] Ajouter colonne "Date de début" :

  - Input type="date"

  - Peut être vide (NULL)

  - Format date correct (affichage DD/MM/YYYY)

  - Bouton "×" pour supprimer la date

- [ ] **Backend - Modifier `update_amortization_type` pour accepter `start_date: null`**

  - Utiliser `model_dump(exclude_unset=True)` pour distinguer "champ non fourni" vs "champ = None"

- [ ] Sauvegarde automatique sur `onBlur` ou `Enter`

- [ ] **Créer test visuel dans navigateur**

- [ ] **Valider avec l'utilisateur**

**Deliverables**:

- Mise à jour `backend/api/routes/amortization_types.py` (méthode `update_amortization_type`)

- Mise à jour `frontend/src/components/AmortizationConfigCard.tsx`

**Acceptance Criteria**:

- [ ] Champ date s'affiche

- [ ] Édition fonctionne

- [ ] Valeur NULL gérée correctement (peut être définie et supprimée)

- [ ] Bouton "×" supprime la date correctement

- [ ] Sauvegarde automatique fonctionne

---

#### Step 6.6.8: Frontend - Colonne "Montant d'immobilisation" (calculé)

**Status**: ⏳ EN ATTENTE  

**Description**: Ajouter la colonne "Montant d'immobilisation" avec calcul automatique.

**Objectifs**:

- Afficher le montant calculé (somme des transactions)

- Recalcul automatique quand `level_1_values` change

- Appeler `GET /api/amortization/types/{id}/amount`

**Tasks**:

- [ ] Ajouter colonne "Montant d'immobilisation" :

  - Champ en lecture seule (calculé)

  - Appeler API pour calculer le montant

  - Recalculer quand `level_1_values` ou `level_2_value` change

  - Indicateur de chargement "⏳ Calcul..." pendant le calcul

- [ ] Afficher formatage monétaire (2 décimales, EUR)

- [ ] Gérer état de chargement

- [ ] **Créer test visuel dans navigateur**

- [ ] **Valider avec l'utilisateur**

**Deliverables**:

- Mise à jour `frontend/src/components/AmortizationConfigCard.tsx`

**Acceptance Criteria**:

- [ ] Montant s'affiche correctement

- [ ] Recalcul automatique fonctionne (quand types chargés, level2Value change, level_1_values modifiés)

- [ ] Formatage correct (EUR, 2 décimales)

---

#### Step 6.6.9: Frontend - Colonne "Durée d'amortissement"

**Status**: ⏳ EN ATTENTE  

**Description**: Ajouter la colonne "Durée d'amortissement" (input nombre).

**Objectifs**:

- Champ nombre éditable (obligatoire)

- Sauvegarde automatique

- Recalcul de l'annuité quand durée change

- **0 ans signifie que l'immobilisation ne s'amortit pas (ex: terrain)**

**Tasks**:

- [ ] Ajouter colonne "Durée d'amortissement" :

  - Input type="number" avec `min="0"` et `step="0.1"`

  - Validation : nombre positif obligatoire

  - Sauvegarde automatique sur `onBlur` ou `Enter`

  - Affichage formaté : "X ans" ou "0 ans" (au lieu de "Non défini")

- [ ] Recalculer annuité quand durée change : `Annuité = Montant / Durée` (si montant > 0 et durée > 0)

- [ ] **Créer test visuel dans navigateur**

- [ ] **Valider avec l'utilisateur**

**Deliverables**:

- Mise à jour `frontend/src/components/AmortizationConfigCard.tsx`

**Acceptance Criteria**:

- [ ] Champ durée s'affiche

- [ ] Édition fonctionne (clic sur la cellule)

- [ ] Validation obligatoire fonctionne (nombre positif)

- [ ] Recalcul annuité fonctionne (automatique si montant disponible)

- [ ] Sauvegarde automatique fonctionne

---

#### Step 6.6.10: Frontend - Colonne "Annuité d'amortissement"

**Status**: ⏳ EN ATTENTE  

**Description**: Ajouter la colonne "Annuité d'amortissement" (calculée puis éditable).

**Objectifs**:

- Calcul automatique : `Annuité = abs(Montant) / Durée`

- Éditable manuellement

- Sauvegarde automatique

- **Gestion des montants négatifs avec Math.abs()**

- **annual_amount = 0 considéré comme "non défini" (calcul automatique)**

**Tasks**:

- [ ] Ajouter colonne "Annuité d'amortissement" :

  - Calcul automatique : `Annuité = abs(Montant) / Durée` (si Montant ≠ 0 et Durée > 0)

  - Input type="number" éditable

  - Sauvegarde automatique sur `onBlur` ou `Enter`

  - Formatage monétaire EUR avec 2 décimales

- [ ] Recalculer quand Montant ou Durée change

- [ ] **Gérer les montants négatifs avec Math.abs()**

- [ ] **Ignorer annual_amount = 0 pour permettre le calcul automatique**

- [ ] **Créer test visuel dans navigateur**

- [ ] **Valider avec l'utilisateur**

**Deliverables**:

- Mise à jour `frontend/src/components/AmortizationConfigCard.tsx`

**Acceptance Criteria**:

- [ ] Calcul automatique fonctionne (avec montants négatifs)

- [ ] Édition manuelle fonctionne (clic sur la cellule)

- [ ] Recalcul automatique fonctionne (quand montant ou durée change)

- [ ] Sauvegarde automatique fonctionne

---

#### Step 6.6.11: Frontend - Colonne "Montant cumulé" (calculé)

**Status**: ⏳ EN ATTENTE  

**Description**: Ajouter la colonne "Montant cumulé" avec calcul automatique.

**Objectifs**:

- Afficher le montant cumulé (somme des `AmortizationResult`)

- Recalcul automatique après calcul d'amortissement

- Appeler `GET /api/amortization/types/{id}/cumulated`

**Tasks**:

- [ ] Ajouter colonne "Montant cumulé" :

  - Champ en lecture seule (calculé)

  - Appeler API pour calculer le cumulé

  - Recalculer après chaque calcul d'amortissement

- [ ] Afficher formatage monétaire (2 décimales)

- [ ] Gérer état de chargement

- [ ] **Créer test visuel dans navigateur**

- [ ] **Valider avec l'utilisateur**

**Deliverables**:

- Mise à jour `frontend/src/components/AmortizationConfigCard.tsx`

- Mise à jour `frontend/src/api/client.ts` - Méthode `getAmortizationTypeCumulated()`

**Acceptance Criteria**:

- [ ] Montant cumulé s'affiche correctement

- [ ] Recalcul automatique fonctionne

- [ ] Formatage correct

---

#### Step 6.6.12: Frontend - Colonne "VNC" (calculé)

**Status**: ⏳ EN ATTENTE  

**Description**: Ajouter la colonne "VNC" avec calcul automatique.

**Objectifs**:

- Calcul automatique : `VNC = Montant - Cumulé`

- Recalcul automatique quand Montant ou Cumulé change

**Tasks**:

- [ ] Ajouter colonne "VNC" :

  - Champ en lecture seule (calculé)

  - Calcul : `VNC = abs(Montant) - abs(Cumulé)`

  - Recalculer quand Montant ou Cumulé change

- [ ] Afficher formatage monétaire (2 décimales)

- [ ] Affichage conditionnel : couleur rouge si VNC < 0, noir sinon

- [ ] **Créer test visuel dans navigateur**

- [ ] **Valider avec l'utilisateur**

**Deliverables**:

- Mise à jour `frontend/src/components/AmortizationConfigCard.tsx`

**Acceptance Criteria**:

- [ ] VNC s'affiche correctement

- [ ] Calcul automatique fonctionne (VNC = abs(Montant) - abs(Cumulé))

- [ ] Recalcul automatique fonctionne (quand Montant ou Cumulé change)

- [ ] Formatage correct (monétaire, 2 décimales)

- [ ] Affichage conditionnel (rouge si négatif)

---

#### Step 6.6.13: Frontend - Colonne "Nombre de transactions"

**Status**: ⏳ EN ATTENTE  

**Description**: Ajouter la colonne "Nombre de transactions" pour afficher le nombre de transactions correspondant à chaque type d'immobilisation.

**Objectifs**:

- Afficher le nombre de transactions qui correspondent à chaque type d'amortissement

- Basé sur le `level_2` sélectionné et les `level_1_values` mappés

- Recalcul automatique quand `level_1_values` change

- **Fusion des résultats au lieu de remplacement pour préserver les compteurs des autres types**

**Tasks**:

- [ ] **Backend - Ajouter modèle `AmortizationTypeTransactionCountResponse`** :

  - `type_id`, `type_name`, `transaction_count`

- [ ] **Backend - Ajouter endpoint `GET /api/amortization/types/{id}/transaction-count`** :

  - Compter les transactions où `level_2 == type.level_2_value` ET `level_1 IN type.level_1_values`

  - Si `start_date` est renseignée, filtrer par année

  - Retourner 0 si aucune valeur `level_1` mappée

- [ ] **Frontend - Ajouter méthode `getTransactionCount()` dans `amortizationTypesAPI`**

- [ ] Ajouter colonne "Nombre de transactions" dans `AmortizationConfigCard.tsx` :

  - Position : après "Level 1 (valeurs)" et avant "Date de début"

  - Champ en lecture seule (calculé)

  - Appeler API pour compter les transactions

  - Recalculer quand `level_1_values` ou `level_2_value` change

  - Indicateur de chargement "⏳..." pendant le calcul

- [ ] **Fusion des résultats** : `loadTransactionCounts()` fusionne les nouveaux résultats avec les existants au lieu de les remplacer

- [ ] **Recharger tous les types** : Dans `recalculateTypeComplete()`, appeler `loadTransactionCounts()` sans paramètre pour recharger tous les types

- [ ] **Créer test visuel dans navigateur**

- [ ] **Valider avec l'utilisateur**

**Deliverables**:

- Mise à jour `backend/api/models.py` - Modèle `AmortizationTypeTransactionCountResponse`

- Mise à jour `backend/api/routes/amortization_types.py` - Endpoint `get_amortization_type_transaction_count`

- Mise à jour `frontend/src/api/client.ts` - Méthode `getTransactionCount()`

- Mise à jour `frontend/src/components/AmortizationConfigCard.tsx`

  - Ajout état `transactionCounts` et `loadingTransactionCounts`

  - Ajout fonction `loadTransactionCounts()` avec fusion des résultats

  - Ajout colonne dans le tableau

**Acceptance Criteria**:

- [ ] Colonne "Nombre de transactions" s'affiche correctement

- [ ] Nombre calculé correctement (basé sur `level_2` et `level_1_values`)

- [ ] Recalcul automatique fonctionne (quand `level_1_values` change)

- [ ] **Fusion des résultats : les compteurs des autres types ne sont pas perdus lors des modifications**

- [ ] Formatage correct (nombre entier)

- [ ] Indicateur de chargement visible pendant le calcul

---

#### Step 6.6.14: Frontend - Bouton "+" Ajouter un type

**Status**: ⏳ EN ATTENTE  

**Description**: Ajouter le bouton "+" pour créer un nouveau type d'amortissement.

**Objectifs**:

- Bouton "+" dans le tableau

- Créer un nouveau type avec valeurs par défaut

- Appeler `POST /api/amortization/types`

**Tasks**:

- [ ] Ajouter bouton "+" dans le tableau :

  - Position : après la dernière ligne (ligne dédiée avec colspan)

  - Créer nouveau type avec valeurs par défaut :

    - `name` : "Nouveau type" (à renommer par l'utilisateur)

    - `level_2_value` : valeur sélectionnée dans le dropdown

    - `level_1_values` : `[]`

    - `start_date` : `null`

    - `duration` : `0`

    - `annual_amount` : `null`

  - Appeler API `POST /api/amortization/types`

  - Rafraîchir le tableau et les montants

  - Bouton désactivé si `level2Value` n'est pas sélectionné

- [ ] **Créer test visuel dans navigateur**

- [ ] **Valider avec l'utilisateur**

**Deliverables**:

- Mise à jour `frontend/src/components/AmortizationConfigCard.tsx`

- Méthode `create()` déjà disponible dans `frontend/src/api/client.ts`

**Acceptance Criteria**:

- [ ] Bouton "+" s'affiche (après toutes les lignes)

- [ ] Création d'un nouveau type fonctionne

- [ ] Nouveau type apparaît dans le tableau

- [ ] Bouton désactivé si Level 2 non sélectionné

- [ ] Rechargement automatique des types et montants après création

---

#### Step 6.6.15: Frontend - Suppression de type (clic droit)

**Status**: ⏳ EN ATTENTE  

**Description**: Ajouter la fonctionnalité de suppression via clic droit.

**Objectifs**:

- Menu contextuel (clic droit) sur chaque ligne

- Option "Supprimer" avec confirmation

- Appeler `DELETE /api/amortization/types/{id}`

- **Suppression automatique des résultats d'amortissement associés** (backend)

**Tasks**:

- [ ] Ajouter menu contextuel :

  - Clic droit sur une ligne du tableau (`onContextMenu`)

  - Afficher menu avec option "Supprimer" à la position du clic

  - Confirmation avant suppression (window.confirm)

  - Appeler API `DELETE /api/amortization/types/{id}`

  - Rafraîchir le tableau et les montants

  - Fermer le menu après action ou clic ailleurs

- [ ] **Backend - Modifier endpoint `DELETE /api/amortization/types/{id}`** :

  - Supprimer automatiquement tous les `AmortizationResult` associés au type avant de supprimer le type

  - Filtrer les résultats par `category == type.name`, `level_2 == type.level_2_value`, et `level_1 IN type.level_1_values`

  - Plus d'erreur de contrainte de clé étrangère

- [ ] **Créer test visuel dans navigateur**

- [ ] **Valider avec l'utilisateur**

**Deliverables**:

- Mise à jour `frontend/src/components/AmortizationConfigCard.tsx`

- Mise à jour `backend/api/routes/amortization_types.py` - Endpoint `delete_amortization_type`

- Méthode `delete()` déjà disponible dans `frontend/src/api/client.ts`

**Acceptance Criteria**:

- [ ] Menu contextuel s'affiche à la position du clic

- [ ] Confirmation fonctionne (window.confirm)

- [ ] Suppression fonctionne (appel API DELETE)

- [ ] **Suppression automatique des résultats d'amortissement associés (plus d'erreur de contrainte)**

- [ ] **On peut supprimer un type même s'il est utilisé dans des résultats d'amortissement**

---

#### Step 6.6.16: Frontend - Recalcul automatique des amortissements

**Status**: ⏳ EN ATTENTE  

**Description**: Améliorer la fluidité en déclenchant automatiquement le recalcul des amortissements après modification des paramètres.

**Objectifs**:

- Recalcul automatique après modification de paramètres impactant les amortissements

- Rechargement automatique des montants cumulés après recalcul

- Améliorer l'expérience utilisateur (pas besoin de cliquer manuellement sur "🔄 Calculer les amortissements")

**Problème actuel**:

- Après modification de la date de début (ou autres paramètres), l'utilisateur doit :

  1. Cliquer manuellement sur "🔄 Calculer les amortissements"

  2. Rafraîchir la page pour que le "montant cumulé" se mette à jour

- Ce n'est pas fluide et nécessite des actions manuelles

**Tasks**:

- [ ] Identifier les champs qui impactent les amortissements :

  - `start_date` (date de début)

  - `duration` (durée d'amortissement)

  - `annual_amount` (annuité d'amortissement)

  - `level_1_values` (valeurs level_1 mappées)

- [ ] Après sauvegarde de ces champs, déclencher automatiquement :

  - Appel à `amortizationAPI.recalculate()` (recalcul complet)

  - Afficher un indicateur de chargement pendant le recalcul

- [ ] Après le recalcul, recharger automatiquement :

  - `loadCumulatedAmounts()` (montants cumulés)

  - Rafraîchir le tableau d'amortissements (via `onConfigUpdated()`)

- [ ] Gérer les erreurs potentielles lors du recalcul automatique (silencieux, pas d'alerte)

- [ ] **Créer test visuel dans navigateur**

- [ ] **Valider avec l'utilisateur**

**Deliverables**:

- Mise à jour `frontend/src/components/AmortizationConfigCard.tsx`

  - Modifier `handleDateEditSave()` pour déclencher le recalcul

  - Modifier `handleDurationEditSave()` pour déclencher le recalcul

  - Modifier `handleAnnualAmountEditSave()` pour déclencher le recalcul

  - Modifier `handleLevel1Add()` et `handleLevel1Remove()` pour déclencher le recalcul

- Ajouter état de chargement pour le recalcul automatique (`isAutoRecalculating`)

- Ajouter fonction utilitaire `triggerAutoRecalculate()` pour centraliser la logique

- Ajouter indicateur visuel "⏳ Recalcul en cours..." dans le titre de la card

**Acceptance Criteria**:

- [ ] Modification de `start_date` → recalcul automatique → montant cumulé mis à jour

- [ ] Modification de `duration` → recalcul automatique → montant cumulé mis à jour

- [ ] Modification de `annual_amount` → recalcul automatique → montant cumulé mis à jour

- [ ] Modification de `level_1_values` → recalcul automatique → montant cumulé mis à jour

- [ ] Indicateur de chargement visible pendant le recalcul ("⏳ Recalcul en cours..." dans le titre)

- [ ] Pas besoin de rafraîchir la page manuellement

- [ ] Pas besoin de cliquer sur "🔄 Calculer les amortissements" manuellement

- [ ] Gestion d'erreur si le recalcul échoue (silencieux, log dans la console)

---

#### Step 6.6.17: Frontend - Rafraîchissement automatique des amortissements

**Status**: ⏸️ EN ATTENTE  

**Description**: Rafraîchir automatiquement l'affichage des amortissements après modification de transactions ou mappings.

**Objectifs**:

- Rafraîchissement automatique de l'affichage des amortissements après modification de transactions

- Rafraîchissement automatique après modification de mappings dans l'onglet "Toutes les transactions"

- Améliorer l'expérience utilisateur (pas besoin de rafraîchir manuellement la page)

**Problème actuel**:

- Après modification d'un mapping dans l'onglet "Toutes les transactions" → les amortissements ne se rafraîchissent pas automatiquement

- Après ajout d'une transaction → les amortissements ne se rafraîchissent pas automatiquement

- Après suppression d'une transaction → les amortissements ne se rafraîchissent pas automatiquement

- L'utilisateur doit rafraîchir manuellement la page pour voir les changements

**Approche**:

1. **D'abord tester** si le rafraîchissement fonctionne déjà

2. Si ça marche → on saute l'implémentation

3. Si ça ne marche pas → on code pour corriger

**Tests à effectuer**:

- [ ] **Test 1** : Modifier un mapping (level_1, level_2, level_3) dans l'onglet "Toutes les transactions"

  - Vérifier si l'onglet "Amortissements" se rafraîchit automatiquement

  - Vérifier si les montants sont mis à jour

- [ ] **Test 2** : Créer une nouvelle transaction avec level_2 = "ammortissements"

  - Vérifier si l'onglet "Amortissements" se rafraîchit automatiquement

  - Vérifier si la nouvelle transaction apparaît dans les calculs

- [ ] **Test 3** : Supprimer une transaction qui était dans les amortissements

  - Vérifier si l'onglet "Amortissements" se rafraîchit automatiquement

  - Vérifier si la transaction disparaît des calculs

- [ ] **Test 4** : Modifier une transaction (level_1, level_2) dans l'onglet "Toutes les transactions"

  - Vérifier si l'onglet "Amortissements" se rafraîchit automatiquement

  - Vérifier si les montants sont mis à jour

**Si les tests échouent - Tasks**:

- [ ] Identifier les composants qui doivent être rafraîchis :

  - `AmortizationTable` (tableau année par année)

  - `AmortizationConfigCard` (montants cumulés)

- [ ] Implémenter mécanisme de rafraîchissement :

  - Option A : Polling périodique (vérifier les changements toutes les X secondes)

  - Option B : Événements/callbacks entre composants

  - Option C : Rechargement automatique après actions dans TransactionsTable

- [ ] Ajouter état de chargement pendant le rafraîchissement

- [ ] Gérer les erreurs potentielles

- [ ] **Créer test visuel dans navigateur**

- [ ] **Valider avec l'utilisateur**

**Deliverables** (si nécessaire):

- Mise à jour `frontend/src/components/AmortizationTable.tsx` - Rafraîchissement automatique

- Mise à jour `frontend/src/components/AmortizationConfigCard.tsx` - Rafraîchissement automatique

- Mise à jour `frontend/app/dashboard/amortissements/page.tsx` - Gestion des événements

- Possiblement : Mise à jour `frontend/src/components/TransactionsTable.tsx` - Émission d'événements

**Acceptance Criteria**:

- [ ] Modification de mapping → rafraîchissement automatique des amortissements

- [ ] Création de transaction → rafraîchissement automatique des amortissements

- [ ] Suppression de transaction → rafraîchissement automatique des amortissements

- [ ] Modification de transaction → rafraîchissement automatique des amortissements

- [ ] Pas besoin de rafraîchir manuellement la page

- [ ] Indicateur de chargement visible pendant le rafraîchissement (si nécessaire)

---

#### Step 6.6.18: Frontend - Réinitialisation des Level 1 lors du changement de Level 2

**Status**: ⏳ EN ATTENTE  

**Description**: Réinitialiser (vider) tous les `level_1_values` des types d'amortissement quand l'utilisateur change le Level 2 sélectionné dans le dropdown.

**Objectifs**:

- S'assurer que chaque Level 2 a ses propres types d'amortissement complètement indépendants

- Éviter que des mappings Level 1 d'un Level 2 précédent polluent les types d'un nouveau Level 2

- Garantir que seules les données liées au Level 2 sélectionné sont affichées et sauvegardées

- **Supprimer tous les types d'amortissement pour TOUS les Level 2 lors du changement**

- **Créer automatiquement les 7 types par défaut pour le nouveau Level 2 sélectionné**

**Problème actuel**:

- Quand l'utilisateur change le Level 2 dans le dropdown "Level 2 (Valeur à considérer comme amortissement)" :

  - Les types d'amortissement sont bien filtrés par le nouveau Level 2 (déjà corrigé)

  - MAIS les `level_1_values` de ces types peuvent contenir des valeurs qui ne correspondent pas aux transactions du nouveau Level 2

  - Ces valeurs Level 1 proviennent d'un mapping précédent fait pour un autre Level 2

  - Exemple : Level 2 = "ammortissements" → Type "Part terrain" a Level 1 = ["Caution entree"]

    - L'utilisateur change Level 2 = "Produit"

    - Le type "Part terrain" pour "Produit" affiche encore Level 1 = ["Caution entree"]

    - Cette valeur ne correspond pas aux transactions de "Produit"

    - Le montant d'immobilisation ne se calcule pas correctement

**Solution**:

- Quand `level2Value` change dans le dropdown :

  1. **Si changement de Level 2 (pas première sélection)** :

     - Afficher popup de confirmation "Clear previous amortisations?"

     - Si confirmé :

       - Supprimer TOUS les résultats d'amortissement (`DELETE /api/amortization/results`)

       - Supprimer TOUS les types d'amortissement pour TOUS les Level 2

       - Créer les 7 types par défaut pour le nouveau Level 2 sélectionné

     - Si annulé : revenir au Level 2 précédent

  2. **Si première sélection** :

     - Vérifier si des types existent déjà pour ce Level 2

     - Si non, créer automatiquement les 7 types par défaut

  3. Filtrer les types d'amortissement par le Level 2 sélectionné

  4. Vider les cards (types, montants, montants cumulés)

**Tasks**:

- [ ] Modifier `handleLevel2Change()` dans `AmortizationConfigCard.tsx` :

  - Gérer le changement de Level 2 avec popup de confirmation

  - Supprimer tous les résultats d'amortissement avant de supprimer les types

  - Supprimer tous les types d'amortissement pour tous les Level 2

  - Créer les 7 types par défaut pour le nouveau Level 2

  - Vider les cards (types, montants, montants cumulés)

- [ ] **Backend - Ajouter endpoint `DELETE /api/amortization/results`** :

  - Supprimer tous les résultats d'amortissement

  - Utilisé avant la suppression des types pour éviter les erreurs de contrainte

- [ ] Gérer le cas où plusieurs types doivent être créés (faire les appels en parallèle)

- [ ] Recharger les montants après la réinitialisation (`loadAmounts()`)

- [ ] Gérer les erreurs potentielles (alert si erreur critique)

- [ ] **Créer test visuel dans navigateur**

- [ ] **Valider avec l'utilisateur**

**Deliverables**:

- Mise à jour `frontend/src/components/AmortizationConfigCard.tsx`

  - Modifier `handleLevel2Change()` pour supprimer tous les types et créer les 7 types par défaut

  - Ajouter fonction `createInitialTypes()` pour créer les 7 types par défaut

  - Ajouter fonction `resetTypesForLevel2()` pour réinitialiser les types pour un Level 2 donné

- Mise à jour `backend/api/routes/amortization.py` - Endpoint `DELETE /api/amortization/results`

- Mise à jour `frontend/src/api/client.ts` - Méthode `deleteAllResults()`

**Acceptance Criteria**:

- [ ] Changement de Level 2 = "ammortissements" vers "Produit" → popup de confirmation affiché

- [ ] Si confirmé : tous les types pour tous les Level 2 sont supprimés, 7 types par défaut créés pour "Produit"

- [ ] Si annulé : retour au Level 2 précédent

- [ ] Première sélection d'un Level 2 → création automatique des 7 types par défaut (sans popup)

- [ ] Les types affichés dans la card ne contiennent que des données liées au Level 2 sélectionné

- [ ] Après réinitialisation, l'utilisateur peut ajouter de nouveaux Level 1 qui correspondent aux transactions du nouveau Level 2

- [ ] Les montants d'immobilisation se calculent correctement après réinitialisation et ajout de nouveaux Level 1

- [ ] Pas de données "fantômes" d'un Level 2 précédent qui polluent l'affichage

- [ ] Gestion d'erreur si la réinitialisation échoue (alert avec message d'erreur)

---

#### Step 6.6.19 : Frontend - Fonctionnalité pin/unpin pour la card de configuration

**Status**: ⏸️ EN ATTENTE  

**Description**: Ajouter un bouton pin/unpin à côté du titre "Configuration des amortissements" pour replier/déplier la card.

**Tasks**:

- [ ] Ajouter un état `isCollapsed` pour gérer l'état replié/déplié

- [ ] Ajouter un bouton pin/unpin (📌/📌) à côté du titre "Configuration des amortissements"

- [ ] Implémenter la logique de repli/dépli : masquer/afficher le contenu de la card (tableau, boutons)

- [ ] Sauvegarder l'état dans localStorage pour persister entre les sessions

- [ ] Charger l'état depuis localStorage au montage du composant

- [ ] **Tester dans le navigateur**

**Acceptance Criteria**:

- [ ] Bouton pin/unpin visible à côté du titre

- [ ] Clic sur le bouton replie/déplie la card

- [ ] Le contenu (tableau, boutons) est masqué quand la card est repliée

- [ ] Seul le titre et le bouton pin restent visibles quand replié

- [ ] L'état est sauvegardé dans localStorage

- [ ] L'état est restauré au rechargement de la page

- [ ] **Test visuel dans navigateur validé**

---

### Step 6.8 : Backend - Recalcul automatique

**Status**: ⏳ EN ATTENTE  

**Description**: Implémenter le recalcul automatique des amortissements après modification de transactions.

**Objectifs**:

- Déclencher recalcul automatique après modification de transaction

- Déclencher recalcul après modification de mapping

- Optimiser les performances (recalcul incrémental)

**Tasks**:

- [ ] Intégrer recalcul automatique dans `PUT /api/transactions/{id}`

- [ ] Intégrer recalcul automatique dans `PUT /api/enrichment/transactions/{id}`

- [ ] Optimiser recalcul (uniquement pour transactions impactées)

- [ ] Gérer les erreurs de recalcul (logging, pas de blocage)

- [ ] **Créer test de recalcul automatique**

- [ ] **Valider avec l'utilisateur**

**Deliverables**:

- Mise à jour `backend/api/routes/transactions.py` - Recalcul automatique

- Mise à jour `backend/api/routes/enrichment.py` - Recalcul automatique

- `backend/tests/test_amortization_auto_recalc.py` - Tests recalcul automatique

**Acceptance Criteria**:

- [ ] Modification transaction → recalcul automatique des amortissements

- [ ] Modification mapping → recalcul automatique des amortissements

- [ ] Recalcul optimisé (uniquement transactions impactées)

- [ ] Gestion d'erreur correcte (pas de blocage)

- [ ] **Utilisateur confirme que le recalcul automatique fonctionne**

---

### Step 6.7 : Frontend - Intégration et tests finaux

**Status**: ⏳ EN ATTENTE  

**Description**: Intégrer tous les composants et tester le workflow complet.

**Tasks**:

- [ ] Ajouter onglet "Amortissements" dans la navigation

- [ ] Tester workflow complet :

  - Configuration initiale

  - Ajout transaction avec level_2/level_3 d'amortissement

  - Vérification recalcul automatique

  - Affichage résultats dans tableau

  - Modification configuration

  - Vérification recalcul après changement config

- [ ] Tester cas limites :

  - Transaction modifiée (montant, date, level_2/level_3)

  - Transaction supprimée

  - Plusieurs transactions même catégorie

  - Transactions sur plusieurs années

- [ ] Vérifier validation somme = montant initial

- [ ] **Créer test visuel complet dans navigateur**

- [ ] **Valider avec l'utilisateur**

**Deliverables**:

- Tests manuels complets

- Documentation si nécessaire

**Acceptance Criteria**:

- [ ] Workflow complet fonctionnel

- [ ] Recalcul automatique fonctionne

- [ ] Tableau affiche résultats corrects

- [ ] Configuration sauvegardée et appliquée

- [ ] Validation somme = montant initial

- [ ] **Utilisateur confirme que tout fonctionne parfaitement**

**Impact Frontend**: 

- [ ] Onglet Amortissements fonctionnel

- [ ] Card de configuration avec pin/unpin

- [ ] Tableau croisé avec répartition visible

- [ ] Totaux validés

- [ ] Recalcul automatique

---

## Notes importantes

1. **Convention de calcul** : Utilisation de la convention 30/360 pour le calcul des jours
2. **Répartition proportionnelle** : Les montants sont répartis proportionnellement par année, avec la dernière année contenant le solde restant pour garantir une somme exacte
3. **Validation** : La somme des amortissements doit toujours être égale au montant initial
4. **Recalcul automatique** : Les amortissements sont recalculés automatiquement après modification de transactions ou de configuration
5. **Types d'amortissement** : 7 types initiaux créés automatiquement (meubles, travaux, construction, terrain, etc.)
6. **Level 2 indépendant** : Chaque Level 2 a ses propres types d'amortissement complètement indépendants

