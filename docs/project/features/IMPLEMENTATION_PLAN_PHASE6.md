# Plan d'Implémentation - Application Web LMNP (Phases 6+)

**Status**: En cours  
**Dernière mise à jour**: 2025-12-26

> **Note** : Ce fichier contient les Phases 6 et suivantes.  
> Pour les Phases 1-5 (complétées), voir [`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md)

## Vue d'ensemble

Ce document contient le plan d'implémentation pour les phases suivantes du projet LMNP.

---

## Phase 6 : Structure États financiers et crédit

### Step 6.1 : Frontend - Restructuration de l'onglet États financiers
**Status**: ✅ COMPLÉTÉ  
**Description**: Renommer l'onglet Bilan, créer la structure avec sous-onglets et checkbox crédit.

**Tasks**:
- [x] Renommer onglet "Bilan" → "États financiers" dans `frontend/src/components/Header.tsx`
- [x] Changer URL `/dashboard/bilan` → `/dashboard/etats-financiers`
- [x] Renommer/move `frontend/app/dashboard/bilan/page.tsx` → `frontend/app/dashboard/etats-financiers/page.tsx`
- [x] Supprimer l'ancien contenu de la page Bilan (rebuild complet)
- [x] Créer système de sous-onglets horizontaux (comme dans Transactions avec `Navigation.tsx`) :
  - Sous-onglet 1 : "Compte de résultat" → URL `/dashboard/etats-financiers?tab=compte-resultat` (par défaut)
  - Sous-onglet 2 : "Bilan" → URL `/dashboard/etats-financiers?tab=bilan`
  - Sous-onglet 3 : "Liasse fiscale" → URL `/dashboard/etats-financiers?tab=liasse-fiscale`
  - Sous-onglet 4 : "Crédit" → URL `/dashboard/etats-financiers?tab=credit` (conditionnel, affiché si checkbox activée)
- [x] Ajouter checkbox "J'ai un crédit" en dessous des sous-onglets
- [x] Persister état checkbox dans localStorage
- [x] Gérer comportement checkbox :
  - Si activée → onglet "Crédit" apparaît immédiatement
  - Si désactivée → popup confirmation "Les données de crédit (si il y en a) vont être écrasées" → si confirmé : onglet disparaît et retour au dernier onglet actif parmi les 3 de base
- [x] Définir onglet par défaut au chargement (Compte de résultat)
- [ ] **Créer test visuel dans navigateur**
- [ ] **Valider avec l'utilisateur**

**Deliverables**:
- Mise à jour `frontend/src/components/Header.tsx` - Renommage onglet
- `frontend/app/dashboard/etats-financiers/page.tsx` - Nouvelle page avec sous-onglets
- `frontend/src/components/FinancialStatementsNavigation.tsx` - Navigation avec sous-onglets (optionnel, peut être intégré dans la page)
- Suppression `frontend/app/dashboard/bilan/` (ancien dossier)

**Acceptance Criteria**:
- [x] Onglet renommé dans la navigation
- [x] URL changée et fonctionnelle (`/dashboard/etats-financiers`)
- [x] 3 sous-onglets de base affichés avec URLs distinctes (`?tab=compte-resultat`, `?tab=bilan`, `?tab=liasse-fiscale`)
- [x] Checkbox "J'ai un crédit" visible en dessous des onglets
- [x] État checkbox persisté dans localStorage
- [x] Onglet "Crédit" apparaît/disparaît selon checkbox avec URL `/dashboard/etats-financiers?tab=credit`
- [x] Confirmation affichée si désactivation avec données existantes
- [x] Navigation entre sous-onglets fonctionne (URLs changent)
- [x] Onglet par défaut = Compte de résultat (si pas de `?tab=` dans l'URL)

---

### Step 6.2 : Backend - Table et modèles pour les mensualités
**Status**: ✅ COMPLÉTÉ  
**Description**: Créer la structure pour stocker les mensualités de crédit (capital, intérêt, assurance).

**Tasks**:
- [x] Créer table `loan_payments` avec colonnes :
  - `id` (PK)
  - `date` (date de la mensualité)
  - `capital` (montant du capital remboursé)
  - `interest` (montant des intérêts)
  - `insurance` (montant de l'assurance crédit)
  - `total` (total de la mensualité)
  - `loan_name` (nom du prêt, ex: "Prêt construction", peut correspondre au `name` d'une configuration de crédit)
  - `created_at`, `updated_at`
- [x] Créer modèle SQLAlchemy `LoanPayment` dans `backend/database/models.py`
- [x] Créer modèles Pydantic dans `backend/api/models.py`
- [x] **Créer test unitaire pour le modèle**
- [ ] **Valider avec l'utilisateur**

**Deliverables**:
- `backend/database/models.py` - Modèle `LoanPayment` ✅
- `backend/api/models.py` - Modèles Pydantic pour les mensualités ✅
- `backend/tests/test_loan_payment_model.py` - Test unitaire ✅
- `backend/database/__init__.py` - Export du modèle ✅

**Acceptance Criteria**:
- [x] Table créée en BDD
- [x] Modèle SQLAlchemy fonctionnel
- [x] Modèles Pydantic créés et validés
- [x] Tests unitaires passent

---

### Step 6.3 : Backend - Endpoints API pour les mensualités
**Status**: ✅ COMPLÉTÉ  
**Description**: Créer les endpoints API pour gérer les mensualités de crédit.

**Clarifications** :
- **Format d'import** : 1 enregistrement par année (pas de mensualités mensuelles)
- **Date** : 01/01 de chaque année (ex: 01/01/2021, 01/01/2022, etc.)
- **Nom du prêt** : "Prêt principal" par défaut (un seul prêt par fichier)
- **Bouton d'import** : Même style que "Load Trades/Mappings" (bouton + modal de preview)
- **Structure Excel** : 
  - Colonne `annee` : types ("capital", "interets", "assurance cred", "total")
  - Colonnes années : 2021, 2022, 2023, etc.
  - Chaque ligne = un type de montant pour toutes les années
- **Gestion des doublons** : 
  - Un seul tableau d'amortissement par crédit (`loan_name`)
  - Si on charge un nouveau fichier, supprimer toutes les mensualités existantes pour ce `loan_name` (écraser l'ancien)
  - **Confirmation** : Les deux - dans le modal de preview (avant l'import) ET dans l'endpoint backend (retourner un warning si données existent)
- **Nom du prêt** :
  - Toujours "Prêt principal" par défaut (pas de personnalisation dans le modal)
  - L'utilisateur sélectionne les fichiers, l'application charge juste les xlsx/csv
- **Validation des données** :
  - Vérifier que `capital + interest + insurance = total`
  - Si erreur, corriger automatiquement (utiliser le total calculé)
- **Années sans données** :
  - Si NaN/vides, créer un enregistrement avec des valeurs à 0
- **Preview** :
  - Afficher les colonnes détectées (structure du fichier Excel)
  - Afficher les lignes (aperçu des données parsées)
  - Afficher les années détectées et montants
  - **Colonnes invalides** : Avertir dans le preview si une colonne n'est pas une année valide (texte, format incorrect)
- **Historique** : Pas besoin d'historique des imports, juste supprimer et remplacer à chaque import

**Tasks**:
- [x] Créer fichier `backend/api/routes/loan_payments.py`
- [x] Créer endpoint `GET /api/loan-payments` : Liste des mensualités (filtrées par date, prêt, etc.)
- [x] Créer endpoint `POST /api/loan-payments` : Créer une mensualité
- [x] Créer endpoint `POST /api/loan-payments/preview` : Preview du fichier Excel (comme transactions/mappings)
  - Afficher les colonnes détectées (structure du fichier Excel)
  - Afficher les lignes (aperçu des données parsées)
  - Afficher les années détectées et montants extraits
- [x] Créer endpoint `POST /api/loan-payments/import` : Importer depuis Excel
  - Parser le fichier Excel avec structure : colonne `annee` + colonnes années
  - **Avant import** : Supprimer toutes les mensualités existantes pour le `loan_name` (avec confirmation)
  - Pour chaque année avec données : créer 1 enregistrement avec date = 01/01/année
  - Extraire capital, interest, insurance, total depuis les lignes correspondantes
  - **Validation** : Vérifier que `capital + interest + insurance = total`, corriger automatiquement si erreur
  - **Années vides** : Si NaN/vides, créer un enregistrement avec valeurs à 0
  - `loan_name` = "Prêt principal" par défaut
- [x] Créer endpoint `PUT /api/loan-payments/{id}` : Mettre à jour une mensualité
- [x] Créer endpoint `DELETE /api/loan-payments/{id}` : Supprimer une mensualité
- [x] Enregistrer router dans `backend/api/main.py`
- [x] **Créer test manuel pour les endpoints**
- [x] **Valider avec l'utilisateur**

**Deliverables**:
- `backend/api/routes/loan_payments.py` - Endpoints API
- Mise à jour `backend/api/main.py` - Enregistrement du router

**Acceptance Criteria**:
- [x] Tous les endpoints fonctionnent correctement
- [x] Preview du fichier Excel fonctionne (affiche structure détectée)
- [x] Import depuis Excel fonctionne (parse correctement la structure)
- [x] Création de 1 enregistrement par année avec date = 01/01/année
- [x] Extraction correcte de capital, interest, insurance, total
- [x] Gestion d'erreur correcte
- [x] Tests manuels passent

---

### Step 6.4 : Backend - Table et modèles pour les configurations de crédit
**Status**: ✅ COMPLÉTÉ  
**Description**: Créer la structure pour stocker les configurations de crédit (plusieurs lignes de crédit possibles).

**Tasks**:
- [x] Créer table `loan_configs` avec colonnes :
  - `id` (PK)
  - `name` (nom du crédit, ex: "Prêt principal", "Prêt construction")
  - `credit_amount` (montant du crédit accordé en euros)
  - `interest_rate` (taux fixe actuel hors assurance en %)
  - `duration_years` (durée de l'emprunt en années)
  - `initial_deferral_months` (décalage initial en mois)
  - `created_at`, `updated_at`
- [x] Créer modèle SQLAlchemy `LoanConfig` dans `backend/database/models.py`
- [x] Créer modèles Pydantic dans `backend/api/models.py`
- [x] **Créer test unitaire pour le modèle**
- [ ] **Valider avec l'utilisateur**

**Deliverables**:
- `backend/database/models.py` - Modèle `LoanConfig` ✅
- `backend/api/models.py` - Modèles Pydantic pour les configurations de crédit ✅
- `backend/tests/test_loan_config_model.py` - Test unitaire ✅
- `backend/database/__init__.py` - Export du modèle ✅

**Acceptance Criteria**:
- [x] Table créée en BDD
- [x] Modèle SQLAlchemy fonctionnel
- [x] Modèles Pydantic créés et validés
- [x] Tests unitaires passent

---

### Step 6.5 : Backend - Endpoints API pour les configurations de crédit
**Status**: ✅ COMPLÉTÉ  
**Description**: Créer les endpoints API pour gérer les configurations de crédit.

**Tasks**:
- [x] Créer fichier `backend/api/routes/loan_configs.py`
- [x] Créer endpoint `GET /api/loan-configs` : Liste des configurations de crédit
- [x] Créer endpoint `GET /api/loan-configs/{id}` : Récupérer une configuration par ID
- [x] Créer endpoint `POST /api/loan-configs` : Créer une configuration
- [x] Créer endpoint `PUT /api/loan-configs/{id}` : Mettre à jour une configuration
- [x] Créer endpoint `DELETE /api/loan-configs/{id}` : Supprimer une configuration
- [x] Enregistrer router dans `backend/api/main.py`
- [x] **Créer test manuel pour les endpoints**
- [ ] **Valider avec l'utilisateur**

**Deliverables**:
- `backend/api/routes/loan_configs.py` - Endpoints API ✅
- Mise à jour `backend/api/main.py` - Enregistrement du router ✅
- `backend/tests/test_loan_configs_endpoints_manual.py` - Test manuel ✅

**Acceptance Criteria**:
- [x] Tous les endpoints fonctionnent correctement
- [x] Gestion d'erreur correcte
- [x] Tests manuels passent (5/5 tests réussis)

---

### Step 6.6 : Frontend - Card de configuration des crédits
**Status**: ✅ COMPLÉTÉ  
**Description**: Créer la card de configuration des crédits dans l'onglet Crédit.

**Tasks**:
- [x] Créer composant `LoanConfigCard.tsx` avec :
  - Card en haut de la page avec plusieurs champs de saisie
  - Champs à renseigner :
    - **Nom du crédit** (éditable)
    - **Crédit accordé** (en euros €)
    - **Taux fixe actuel (hors assurance)** (en %)
    - **Durée emprunt** (en années)
    - **Décalage initial** (en mois)
  - Possibilité d'ajouter plusieurs lignes de crédit (bouton "Ajouter un crédit")
  - Possibilité de supprimer une ligne de crédit
  - Sauvegarde automatique au blur (tous les champs)
- [x] Intégrer le composant dans `frontend/app/dashboard/etats-financiers/page.tsx` (onglet Crédit)
- [x] Créer API client dans `frontend/src/api/client.ts` pour les configurations de crédit
- [x] **Créer test visuel dans navigateur**
- [x] **Valider avec l'utilisateur**

**Deliverables**:
- `frontend/src/components/LoanConfigCard.tsx` - Card de configuration ✅
- Mise à jour `frontend/app/dashboard/etats-financiers/page.tsx` - Intégration dans onglet Crédit ✅
- Mise à jour `frontend/src/api/client.ts` - API client ✅

**Acceptance Criteria**:
- [x] Card affichée en haut de l'onglet Crédit
- [x] Tous les champs sont éditables avec les bonnes unités (€, %, ans, mois)
- [x] Possibilité d'ajouter plusieurs lignes de crédit
- [x] Possibilité de supprimer une ligne de crédit
- [x] Sauvegarde fonctionne (backend) - sauvegarde automatique au blur
- [x] Données persistées et rechargées au chargement de la page
- [x] Interface intuitive et cohérente avec le reste de l'application

---

### Step 6.7 : Frontend - Import et gestion des mensualités
**Status**: ✅ COMPLÉTÉ  
**Description**: Interface pour importer et gérer les mensualités de crédit.

**Tasks**:
- [x] Créer composant d'import Excel/CSV pour les mensualités (`LoanPaymentFileUpload.tsx`)
- [x] Créer modal de prévisualisation (`LoanPaymentPreviewModal.tsx`)
- [x] Créer tableau d'affichage des mensualités (`LoanPaymentTable.tsx`)
- [x] Créer formulaire d'édition inline dans le tableau
- [x] Lier les mensualités aux configurations de crédit (via `loan_name`)
- [x] Créer API client dans `frontend/src/api/client.ts` pour les mensualités
- [x] Intégrer dans l'onglet Crédit
- [ ] **Créer test visuel dans navigateur**
- [ ] **Valider avec l'utilisateur**

**Deliverables**:
- `frontend/src/components/LoanPaymentFileUpload.tsx` - Composant d'import ✅
- `frontend/src/components/LoanPaymentPreviewModal.tsx` - Modal de prévisualisation ✅
- `frontend/src/components/LoanPaymentTable.tsx` - Tableau d'affichage ✅
- Mise à jour `frontend/app/dashboard/etats-financiers/page.tsx` - Intégration ✅
- Mise à jour `frontend/src/api/client.ts` - API client ✅

**Acceptance Criteria**:
- [x] Import Excel fonctionne (format attendu : colonne 'annee' + colonnes années)
- [x] Preview affiche les données parsées avec avertissements
- [x] Tableau affiche toutes les mensualités (triées par date)
- [x] Édition inline fonctionne (modification des champs capital, intérêts, assurance, total auto-calculé)
- [x] Suppression fonctionne avec confirmation
- [x] Association avec les configurations de crédit via `loan_name` ("Prêt principal" par défaut)
- [x] Interface intuitive et cohérente avec le reste de l'application

---

### Step 6.8 : Frontend - Multi-crédits avec sous-onglets dans LoanPaymentTable
**Status**: ✅ COMPLÉTÉ  
**Description**: Transformer LoanPaymentTable pour supporter plusieurs crédits avec sous-onglets, synchronisation avec LoanConfigCard.

**Tasks**:
- [x] Modifier `LoanPaymentTable` pour :
  - Charger la liste des crédits depuis `LoanConfigCard` (via API `loanConfigsAPI.getAll()`)
  - Afficher des sous-onglets horizontaux (un par crédit)
  - Chaque onglet affiche les mensualités du crédit correspondant
  - Le titre affiche le nom du crédit (pas "Prêt principal" en dur)
  - Ordre des onglets : par ordre de création (selon `created_at`)
- [x] Synchronisation avec `LoanConfigCard` :
  - Quand un nouveau crédit est créé dans `LoanConfigCard` → nouvel onglet apparaît automatiquement (vide)
  - Quand un crédit est supprimé dans `LoanConfigCard` → confirmation → suppression de toutes les mensualités associées + suppression de l'onglet
  - Utiliser `useEffect` pour recharger la liste des crédits quand nécessaire
- [x] Modifier `LoanPaymentFileUpload` :
  - Le bouton "Load Mensualités" charge pour le crédit de l'onglet actif
  - Le `loan_name` passé à l'API = `name` du `LoanConfig` sélectionné
- [x] Gestion de la suppression :
  - Si un crédit a des mensualités et qu'on le supprime → confirmation avec message clair
  - Supprimer toutes les mensualités associées (via `loan_name`)
  - Supprimer l'onglet associé
- [x] Filtrage strict des mensualités par crédit (isolation complète)
- [x] Ne pas créer d'enregistrements avec toutes les valeurs à 0 (éviter lignes vides)
- [x] Rafraîchissement automatique après import
- [x] Correction de l'édition des mensualités (gestion de la date et recalcul du total)
- [x] Ajout d'une ligne de totaux en bas du tableau
- [x] **Créer test visuel dans navigateur**
- [x] **Valider avec l'utilisateur**

**Deliverables**:
- Mise à jour `frontend/src/components/LoanPaymentTable.tsx` - Sous-onglets par crédit
- Mise à jour `frontend/src/components/LoanPaymentFileUpload.tsx` - Association au crédit actif
- Mise à jour `frontend/app/dashboard/etats-financiers/page.tsx` - Synchronisation avec LoanConfigCard

**Acceptance Criteria**:
- [x] Sous-onglets affichés (un par crédit créé dans LoanConfigCard)
- [x] Titre affiche le nom du crédit (pas "Prêt principal" en dur)
- [x] Chaque onglet affiche les mensualités du crédit correspondant
- [x] Création d'un crédit → nouvel onglet apparaît automatiquement
- [x] Suppression d'un crédit → confirmation → suppression des mensualités + onglet
- [x] Bouton "Load Mensualités" charge pour le crédit de l'onglet actif
- [x] Ordre des onglets : par ordre de création
- [x] Synchronisation correcte entre LoanConfigCard et LoanPaymentTable
- [x] Isolation complète des crédits (pas de mélange de données entre crédits)
- [x] Pas de lignes vides affichées (années avec toutes valeurs à 0)
- [x] Rafraîchissement automatique du tableau après import
- [x] Édition des mensualités fonctionne correctement (date et recalcul du total)
- [x] Ligne de totaux affichée en bas du tableau

**Détails techniques**:
- Utiliser `loanConfigsAPI.getAll()` pour charger la liste des crédits
- Filtrer les mensualités par `loan_name` = `name` du `LoanConfig`
- Gérer l'état de l'onglet actif avec `useState`
- Utiliser `useEffect` pour recharger la liste des crédits quand LoanConfigCard change
- Implémenter la confirmation de suppression avec message détaillé

---

## Phase 7 : Fonctionnalités 4-6 - États financiers

### Step 7.1 : Service compte de résultat backend
**Status**: ⏸️ EN ATTENTE  
**Description**: Migrer la logique de `compte_de_resultat.py`.

**Tasks**:
- [ ] Renommer onglet Bilan a "Etats Financiers"
- [ ] Ajouter card compte de résultat dans l'ongle
- [ ] Implémenter calcul produits/charges - selectionner les level 3 et 2 qui doivent composer:
    - Charges d'exploitation
        - Charges
        - Impots
        - ammortissments, il faudra recuperer le montant total des ammortissement pour une année donnée - selectionner la vue d'ammortissment que lon veut utiliser pour synchoniser la bonne valeur
    - Produits d'exploitation 
    - Charges d'interet
- [ ] Implémenter prorata année courante
- [ ] Créer endpoint POST /api/reports/compte-resultat
- [ ] **Créer test complet avec données réelles**
- [ ] **Valider avec l'utilisateur**

**Deliverables**:
- Mise à jour `backend/api/services/financial_statements_service.py`
- Mise à jour `backend/api/routes/reports.py`
- `backend/tests/test_compte_resultat.py` - Tests compte de résultat

**Tests**:
- [ ] Test calcul produits d'exploitation
- [ ] Test calcul charges d'exploitation
- [ ] Test calcul charges financières
- [ ] Test prorata année courante
- [ ] Test résultat net

**Acceptance Criteria**:
- [ ] Compte de résultat généré correctement
- [ ] Produits, charges, résultat calculés
- [ ] Prorata année courante fonctionne
- [ ] Stockage en DB
- [ ] Test script exécutable et tous les tests passent
- [ ] **Utilisateur confirme que les calculs sont corrects**

**Impact Frontend**: 
- [ ] Afficher résultats dans console/logs
- [ ] Tester génération depuis interface

---

### Step 7.2 : Service bilans backend
**Status**: ⏸️ EN ATTENTE  
**Description**: Migrer les logiques de `bilan_actif.py` et `bilan_passif.py`.

**Tasks**:
- [ ] Ajouter bilans dans financial_statements_service.py
- [ ] Implémenter bilan actif
- [ ] Implémenter bilan passif
- [ ] Implémenter validation équilibre
- [ ] Créer endpoints POST /api/reports/bilan-actif et /api/reports/bilan-passif
- [ ] **Créer test complet avec validation équilibre**
- [ ] **Valider avec l'utilisateur**

**Deliverables**:
- Mise à jour `backend/api/services/financial_statements_service.py`
- Mise à jour `backend/api/routes/reports.py`
- `backend/tests/test_bilans.py` - Tests bilans

**Tests**:
- [ ] Test calcul bilan actif
- [ ] Test calcul bilan passif
- [ ] Test équilibre Actif = Passif
- [ ] Test calculs cumulés
- [ ] Test dettes fin d'année courante

**Acceptance Criteria**:
- [ ] Bilan actif généré (immobilisations, actif circulant)
- [ ] Bilan passif généré (capitaux propres, dettes)
- [ ] Équilibre Actif = Passif validé
- [ ] Calculs cumulés corrects
- [ ] Test script exécutable et tous les tests passent
- [ ] **Utilisateur confirme que les bilans sont corrects**

**Impact Frontend**: 
- [ ] Afficher résultats dans console/logs
- [ ] Tester génération depuis interface

---

### Step 7.3 : Vue bilan frontend
**Status**: ⏸️ EN ATTENTE  
**Description**: Interface pour visualiser les bilans actif et passif.

**Tasks**:
- [ ] Créer composant BalanceSheet
- [ ] Créer page vue bilan
- [ ] Implémenter affichage actif/passif côte à côte
- [ ] Implémenter vérification équilibre
- [ ] **Créer test visuel dans navigateur**
- [ ] **Valider avec l'utilisateur**

**Deliverables**:
- `frontend/app/dashboard/bilan/page.tsx` - Page bilan
- `frontend/src/components/BalanceSheet.tsx` - Composant bilan

**Tests**:
- [ ] Test affichage bilan actif
- [ ] Test affichage bilan passif
- [ ] Test vérification équilibre
- [ ] Test évolution année par année

**Acceptance Criteria**:
- [ ] Bilan actif et passif affichés côte à côte
- [ ] Équilibre vérifié et affiché
- [ ] Évolution année par année visible
- [ ] **Utilisateur confirme que la vue fonctionne**

**Impact Frontend**: 
- ✅ Onglet Bilan fonctionnel
- ✅ Actif et Passif visibles côte à côte
- ✅ Équilibre validé visuellement

---

## Phase 8 : Fonctionnalité 7 - Consolidation et autres vues

### Step 8.1 : Service consolidation backend
**Status**: ⏸️ EN ATTENTE  
**Description**: Migrer la logique de `merge_etats_financiers.py`.

**Tasks**:
- [ ] Ajouter consolidation dans financial_statements_service.py
- [ ] Implémenter analyses de cohérence
- [ ] Implémenter formatage français
- [ ] Créer endpoint POST /api/reports/consolidation
- [ ] **Créer test complet**
- [ ] **Valider avec l'utilisateur**

**Deliverables**:
- Mise à jour `backend/api/services/financial_statements_service.py`
- Mise à jour `backend/api/routes/reports.py`
- `backend/tests/test_consolidation.py` - Tests consolidation

**Tests**:
- [ ] Test consolidation des états
- [ ] Test analyses de cohérence
- [ ] Test formatage français
- [ ] Test détection dernière date

**Acceptance Criteria**:
- [ ] Consolidation des états financiers fonctionne
- [ ] Analyses de cohérence calculées
- [ ] Formatage français appliqué
- [ ] Test script exécutable et tous les tests passent
- [ ] **Utilisateur confirme que la consolidation fonctionne**

**Impact Frontend**: 
- [ ] Afficher résultats dans console/logs
- [ ] Tester génération depuis interface

---

### Step 8.2 : Vue cashflow frontend
**Status**: ⏸️ EN ATTENTE  
**Description**: Interface pour suivre le solde bancaire et vérifier la cohérence.

**Tasks**:
- [ ] Créer composant CashflowChart
- [ ] Créer page vue cashflow
- [ ] Implémenter évolution solde dans le temps
- [ ] Implémenter détection écarts
- [ ] **Créer test visuel dans navigateur**
- [ ] **Valider avec l'utilisateur**

**Deliverables**:
- `frontend/app/dashboard/cashflow/page.tsx` - Page cashflow
- `frontend/src/components/CashflowChart.tsx` - Graphique cashflow

**Tests**:
- [ ] Test affichage évolution solde
- [ ] Test détection écarts
- [ ] Test comparaison avec transactions

**Acceptance Criteria**:
- [ ] Évolution du solde bancaire affichée
- [ ] Détection des écarts possibles
- [ ] Comparaison avec transactions
- [ ] **Utilisateur confirme que la vue fonctionne**

**Impact Frontend**: 
- ✅ Onglet Cashflow fonctionnel
- ✅ Graphique évolution solde visible
- ✅ Détection écarts testée

---


## Phase 9 : Tests et validation finale

### Step 9.1 : Tests end-to-end
**Status**: ⏸️ EN ATTENTE  
**Description**: Tests complets du workflow depuis upload jusqu'aux états financiers.

**Tasks**:
- [ ] Créer tests E2E backend
- [ ] Créer tests E2E frontend
- [ ] Tester workflow complet
- [ ] Valider tous les calculs
- [ ] **Valider avec l'utilisateur**

**Deliverables**:
- `backend/tests/test_e2e.py` - Tests E2E backend
- `frontend/__tests__/e2e/` - Tests E2E frontend

**Tests**:
- [ ] Test workflow complet upload → enrichissement → calculs → états
- [ ] Test validation calculs finaux
- [ ] Test interface dans différents navigateurs

**Acceptance Criteria**:
- [ ] Workflow complet testé
- [ ] Tous les calculs validés
- [ ] Interface testée dans différents navigateurs
- [ ] **Utilisateur confirme que tout fonctionne**

**Impact Frontend**: 
- ✅ Application complète testée
- ✅ Tous les onglets fonctionnels

---

### Step 9.2 : Documentation et finalisation
**Status**: ⏸️ EN ATTENTE  
**Description**: Documentation utilisateur et technique, optimisation finale.

**Tasks**:
- [ ] Créer guide utilisateur
- [ ] Mettre à jour README.md
- [ ] Optimisation finale
- [ ] **Valider avec l'utilisateur**

**Deliverables**:
- `docs/guides/user_guide.md` - Guide utilisateur
- Mise à jour `README.md`

**Acceptance Criteria**:
- [ ] Documentation complète
- [ ] Application prête pour utilisation
- [ ] **Utilisateur confirme que tout est prêt**

---

## Notes importantes

⚠️ **Rappel Best Practices**:
- Ne jamais cocher [x] avant que les tests soient créés ET exécutés ET validés
- Toujours créer un test script (.py) après chaque implémentation
- Toujours proposer le test à l'utilisateur avant exécution
- Toujours montrer l'impact frontend à chaque étape
- Ne cocher [x] qu'après confirmation explicite de l'utilisateur

**Légende Status**:
- ⏸️ EN ATTENTE - Pas encore commencé
- ⏳ EN COURS - En cours d'implémentation
- ✅ COMPLÉTÉ - Terminé et validé par l'utilisateur

