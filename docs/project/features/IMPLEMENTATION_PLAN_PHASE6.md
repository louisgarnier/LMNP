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

## Phase 7 : Compte de résultat

**Structure** : Identique aux amortissements
- **CompteResultatConfigCard** : Card de configuration (mapping level_1/level_2 → catégories comptables)
- **CompteResultatTable** : Card d'affichage (tableau multi-années avec montants agrégés)

**Ordre d'implémentation** :
1. Backend (Steps 7.1 à 7.4)
2. Frontend - Card Config (Step 7.5 avec sous-steps détaillés)
3. Frontend - Card Table (Step 7.6 avec sous-steps détaillés)

---

### Step 7.1 : Backend - Table et modèles pour les mappings et comptes de résultat
**Status**: ✅ TERMINÉ  
**Description**: Créer la structure de base de données pour stocker les mappings (level_1/level_2 → catégories comptables) et les comptes de résultat générés.

**Catégories comptables à mapper** :
- **Produits d'exploitation** :
  - Loyers hors charge encaissés
  - Charges locatives payées par locataires
  - Autres revenus
- **Charges d'exploitation** :
  - Charges de copropriété hors fonds travaux
  - Fluides non refacturés
  - Assurances
  - Honoraires
  - Travaux et mobilier
  - Impôts et taxes
  - Charges d'amortissements (depuis vues d'amortissement)
  - Autres charges diverses
  - Coût du financement (Intérêts et assurance emprunteur depuis loan_payments)

**Tasks**:
- [x] Créer table `compte_resultat_mappings` avec colonnes :
  - `id` (PK)
  - `category_name` (nom de la catégorie comptable, ex: "Loyers hors charge encaissés")
  - `level_1_values` (JSON array optionnel des level_1 à inclure, NULL par défaut)
  - `level_2_values` (JSON array des level_2 à inclure, ex: ["LOYERS"])
  - `level_3_values` (JSON array optionnel des level_3 à inclure, NULL par défaut)
  - `created_at`, `updated_at`
- [x] Créer table `compte_resultat_data` avec colonnes :
  - `id` (PK)
  - `annee` (année du compte de résultat)
  - `category_name` (nom de la catégorie comptable)
  - `amount` (montant pour cette catégorie et cette année)
  - `amortization_view_id` (ID de la vue d'amortissement utilisée, NULL si N/A)
  - `created_at`, `updated_at`
- [x] Créer modèles SQLAlchemy dans `backend/database/models.py`
- [x] Créer modèles Pydantic dans `backend/api/models.py`
- [x] **Créer test unitaire pour les modèles**
- [x] **Valider avec l'utilisateur**

**Deliverables**:
- `backend/database/models.py` - Modèles `CompteResultatMapping` et `CompteResultatData`
- `backend/api/models.py` - Modèles Pydantic
- `backend/tests/test_compte_resultat_models.py` - Test unitaire
- `backend/database/__init__.py` - Export des modèles

**Acceptance Criteria**:
- [x] Tables créées en BDD
- [x] Modèles SQLAlchemy fonctionnels
- [x] Modèles Pydantic créés
- [x] Tests unitaires passent
- [x] Modèles Pydantic créés et validés
- [x] Tests unitaires passent

---

### Step 7.2 : Backend - Service compte de résultat (calculs)
**Status**: ✅ TERMINÉ  
**Description**: Implémenter la logique de calcul du compte de résultat.

**Sources de données** :
- **Produits/Charges** : Transactions enrichies via `level_1` OU `level_2` (logique OR, filtrer par date pour l'année)
- **Amortissements** : Depuis les vues d'amortissement (sélectionner le total pour chaque année)
- **Intérêts/Assurance crédit** : Depuis `loan_payments` (filtrer par année, sommer `interest` + `insurance`)

**Tasks**:
- [x] Créer fichier `backend/api/services/compte_resultat_service.py`
- [x] Implémenter fonction `get_mappings()` : Charger les mappings depuis la table
- [x] Implémenter fonction `calculate_produits_exploitation(year, mappings)` :
  - Filtrer transactions par année (date entre 01/01/année et 31/12/année)
  - Grouper par catégorie selon les mappings level_1 OU level_2 (logique OR)
  - Sommer les montants par catégorie
- [x] Implémenter fonction `calculate_charges_exploitation(year, mappings)` :
  - Filtrer transactions par année
  - Grouper par catégorie selon les mappings level_1 OU level_2 (logique OR)
  - Sommer les montants par catégorie
- [x] Implémenter fonction `get_amortissements(year, amortization_view_id)` :
  - Récupérer le total d'amortissement pour l'année depuis la vue sélectionnée
- [x] Implémenter fonction `get_cout_financement(year)` :
  - Filtrer `loan_payments` par année (date entre 01/01/année et 31/12/année)
  - Sommer `interest` + `insurance` de tous les crédits
- [x] Implémenter fonction `calculate_compte_resultat(year, mappings, amortization_view_id)` :
  - Calculer tous les produits d'exploitation
  - Calculer toutes les charges d'exploitation (incluant amortissements et coût financement)
  - Calculer Résultat d'exploitation = Produits - Charges
  - Calculer Résultat net = Résultat d'exploitation
- [x] **Créer test complet avec données réelles**
- [x] **Valider avec l'utilisateur**

**Deliverables**:
- `backend/api/services/compte_resultat_service.py` - Service de calcul
- `backend/tests/test_compte_resultat_service.py` - Tests du service

**Tests**:
- [x] Test calcul produits d'exploitation (avec mappings)
- [x] Test calcul charges d'exploitation (avec mappings)
- [x] Test récupération amortissements depuis vue
- [x] Test calcul coût du financement depuis loan_payments
- [x] Test calcul résultat d'exploitation
- [x] Test calcul résultat net
- [x] Test avec données réelles (année complète)

**Acceptance Criteria**:
- [x] Tous les calculs fonctionnent correctement
- [x] Mappings level_1 et level_2 appliqués correctement (logique OR)
- [x] Amortissements récupérés depuis AmortizationResult
- [x] Coût du financement calculé depuis loan_payments
- [x] Test script exécutable et tous les tests passent
- [x] **Utilisateur confirme que les calculs sont corrects**

---

### Step 7.3 : Backend - Endpoints API pour compte de résultat
**Status**: ✅ TERMINÉ  
**Description**: Créer les endpoints API pour gérer les mappings et générer/récupérer les comptes de résultat.

**Tasks**:
- [x] Créer fichier `backend/api/routes/compte_resultat.py`
- [x] Créer endpoint `GET /api/compte-resultat/mappings` : Liste des mappings
- [x] Créer endpoint `POST /api/compte-resultat/mappings` : Créer un mapping
- [x] Créer endpoint `PUT /api/compte-resultat/mappings/{id}` : Mettre à jour un mapping
- [x] Créer endpoint `DELETE /api/compte-resultat/mappings/{id}` : Supprimer un mapping
- [x] Créer endpoint `POST /api/compte-resultat/generate` : Générer un compte de résultat
  - Paramètres : `year`, `amortization_view_id`
  - Retourne : Compte de résultat calculé et stocké en DB
- [x] Créer endpoint `GET /api/compte-resultat` : Récupérer les comptes de résultat
  - Paramètres : `year` (optionnel), `start_year`, `end_year` (pour plusieurs années)
  - Retourne : Liste des comptes de résultat (plusieurs années possibles)
- [x] Créer endpoint `GET /api/compte-resultat/data` : Récupérer les données brutes
- [x] Créer endpoint `DELETE /api/compte-resultat/data/{id}` : Supprimer une donnée
- [x] Créer endpoint `DELETE /api/compte-resultat/year/{year}` : Supprimer toutes les données d'une année
- [x] Enregistrer router dans `backend/api/main.py`
- [x] **Créer test manuel pour les endpoints**
- [x] **Valider avec l'utilisateur**

**Deliverables**:
- `backend/api/routes/compte_resultat.py` - Endpoints API
- Mise à jour `backend/api/main.py` - Enregistrement du router
- `backend/tests/test_compte_resultat_endpoints_manual.py` - Test manuel

**Acceptance Criteria**:
- [x] Tous les endpoints fonctionnent correctement
- [x] Génération de compte de résultat fonctionne
- [x] Récupération de plusieurs années fonctionne
- [x] Gestion d'erreur correcte
- [x] Tests manuels créés (à exécuter avec serveur backend démarré)

---

### Step 7.4 : Backend - Recalcul automatique
**Status**: ✅ TERMINÉ  
**Description**: Implémenter le recalcul automatique des comptes de résultat quand les données sources changent.

**Déclencheurs de recalcul** :
- Transactions ajoutées/modifiées/supprimées
- Données d'amortissement dans les vues changent
- Crédits ajoutés/modifiés (mensualités loan_payments)
- Mappings modifiés

**Tasks**:
- [x] Créer fonction `invalidate_compte_resultat_for_year(year)` : Supprimer les comptes de résultat pour une année
- [x] Créer fonction `invalidate_compte_resultat_for_date_range(start_date, end_date)` : Supprimer pour une plage de dates
- [x] Créer fonction `invalidate_all_compte_resultat()` : Supprimer tous les comptes de résultat
- [x] Implémenter recalcul automatique dans :
  - Endpoints de transactions (POST, PUT, DELETE, import)
  - Endpoints d'amortissement (recalculate_amortizations)
  - Endpoints de loan_payments (POST, PUT, DELETE, import)
  - Endpoints de mappings (POST, PUT, DELETE)
  - Endpoints d'amortization_views (POST, PUT, DELETE)
- [x] **Créer test pour vérifier le recalcul automatique**
- [x] **Valider avec l'utilisateur**

**Deliverables**:
- Mise à jour `backend/api/services/compte_resultat_service.py` - Fonctions de recalcul
- Mise à jour des endpoints concernés (transactions, amortization, loan_payments, mappings)
- `backend/tests/test_compte_resultat_recalcul.py` - Tests de recalcul

**Acceptance Criteria**:
- [x] Recalcul déclenché quand transactions changent (create, update, delete, import)
- [x] Recalcul déclenché quand amortissements changent (recalculate_amortizations)
- [x] Recalcul déclenché quand loan_payments changent (create, update, delete, import)
- [x] Recalcul déclenché quand mappings changent (create, update, delete)
- [x] Recalcul déclenché quand amortization_views changent (create, update, delete)
- [x] Tests de recalcul passent
- [x] **Utilisateur confirme que le recalcul fonctionne**

---

### Step 7.5 : Frontend - Card de configuration (CompteResultatConfigCard)
**Status**: ⏸️ EN ATTENTE  
**Description**: Créer l'interface de configuration pour mapper les level_1 et level_2 aux catégories comptables. Structure identique à `AmortizationConfigCard`.

**Structure du tableau** :
- **4 colonnes** :
  1. **Type** : Dropdown éditable avec "Produits d'exploitation" ou "Charges d'exploitation" (pas stocké en backend, utilisé uniquement pour filtrer les catégories)
  2. **Catégorie comptable** : Dropdown avec catégories prédéfinies (filtrées selon le type sélectionné)
  3. **Level 1 (valeurs)** : Tags bleus avec "x" pour supprimer + bouton "+ Ajouter" (optionnel)
  4. **Level 2 (valeurs)** : Tags bleus avec "x" pour supprimer + bouton "+ Ajouter" (optionnel)
- **Une ligne = une catégorie comptable**
- **Logique de mapping** : Une transaction est mappée à une catégorie si son `level_1` OU son `level_2` est dans les listes (logique OR)
- **Validation** : Pas d'obligation de level_1 ou level_2. Si une catégorie n'a aucune valeur, elle n'impacte pas le compte de résultat (comme AmortizationConfigCard)
- **Ordre** : Tri par Type puis par Catégorie comptable

**Catégories prédéfinies** :
- **Produits d'exploitation** :
  - Loyers hors charge encaissés
  - Charges locatives payées par locataires
  - Autres revenus
- **Charges d'exploitation** :
  - Charges de copropriété hors fonds travaux
  - Fluides non refacturés
  - Assurances
  - Honoraires
  - Travaux et mobilier
  - Impôts et taxes
  - Charges d'amortissements ⚠️ (données depuis vues d'amortissement - pas de mapping level_1/level_2)
  - Autres charges diverses
  - Coût du financement (hors remboursement du capital) ⚠️ (données depuis loan_payments - pas de mapping level_1/level_2)

**Fonctionnalités** (comme AmortizationConfigCard) :
- Bouton "🔄 Réinitialiser les mappings" (supprimer tous les mappings)
- Bouton "+ Ajouter une catégorie" en bas du tableau (création directe, pas de modal)
- Menu contextuel (clic droit) avec "🗑️ Supprimer" pour supprimer une ligne
- Sauvegarde automatique à chaque modification

---

#### Step 7.5.1 : Backend - Support level_1 dans les mappings
**Status**: ✅ TERMINÉ  
**Description**: Ajouter le support de `level_1_values` dans la table et les modèles.

**Tasks**:
- [x] Ajouter colonne `level_1_values` (JSON, nullable=True) dans la table `compte_resultat_mappings`
- [x] Mettre à jour le modèle SQLAlchemy `CompteResultatMapping` pour inclure `level_1_values`
- [x] Mettre à jour les modèles Pydantic pour inclure `level_1_values` dans les requêtes/réponses
- [x] Mettre à jour le service `compte_resultat_service.py` pour filtrer aussi par `level_1` si présent
- [x] Créer migration script si nécessaire
- [x] **Créer test unitaire**
- [x] **Valider avec l'utilisateur**

**Deliverables**:
- Mise à jour `backend/database/models.py` - Ajout `level_1_values`
- Mise à jour `backend/api/models.py` - Ajout `level_1_values` dans Pydantic
- Mise à jour `backend/api/services/compte_resultat_service.py` - Filtrage par `level_1`
- `backend/scripts/migrate_add_level1_to_compte_resultat_mapping.py` - Migration (si nécessaire)

**Acceptance Criteria**:
- [ ] Colonne `level_1_values` ajoutée en BDD
- [ ] Modèles SQLAlchemy et Pydantic mis à jour
- [ ] Service filtre correctement par `level_1` si présent
- [ ] Tests passent

---

#### Step 7.5.2 : Frontend - Structure de base du tableau
**Status**: ✅ TERMINÉ  
**Description**: Créer la structure de base du composant et du tableau (comme AmortizationConfigCard).

**Tasks**:
- [x] Créer composant `CompteResultatConfigCard.tsx` (copier structure de base d'`AmortizationConfigCard`)
- [x] Créer le tableau avec 4 colonnes (en-têtes) : Type, Catégorie comptable, Level 1 (valeurs), Level 2 (valeurs)
- [x] Charger les mappings depuis l'API (`compteResultatAPI.getMappings()`)
- [x] Afficher les lignes existantes (lecture seule pour l'instant, sans édition)
- [x] Déduire le Type automatiquement selon la catégorie (logique frontend)
- [x] Trier les lignes par Type puis par Catégorie comptable
- [x] Ajuster les largeurs des colonnes (Type: 15%, Catégorie: 25%, Level 1: 30%, Level 2: 30%)
- [x] Intégrer dans l'onglet "Compte de résultat"
- [x] **Tester dans le navigateur**

**Deliverables**:
- `frontend/src/components/CompteResultatConfigCard.tsx` - Structure de base
- Mise à jour `frontend/app/dashboard/etats-financiers/page.tsx` - Intégration
- Mise à jour `frontend/src/api/client.ts` - API client de base

**Acceptance Criteria**:
- [x] Tableau affiché avec 4 colonnes
- [x] Mappings chargés depuis l'API
- [x] Lignes triées par Type puis Catégorie
- [x] Largeurs des colonnes ajustées
- [x] Catégories spéciales affichées avec "Données calculées"
- [x] **Test visuel dans navigateur validé**

---

#### Step 7.5.3 : Frontend - Colonne 1 "Type"
**Status**: ✅ TERMINÉ  
**Description**: Afficher le Type en première colonne avec un dropdown éditable pour sélectionner "Produits d'exploitation" ou "Charges d'exploitation".

**Tasks**:
- [x] Afficher le Type en première colonne avec un dropdown
- [x] Dropdown avec 2 options : "Produits d'exploitation" et "Charges d'exploitation"
- [x] Permettre la modification du Type via le dropdown pour chaque ligne
- [x] Permettre plusieurs lignes avec la même valeur de Type
- [x] Initialiser le Type selon la catégorie (déduction automatique au chargement)
- [x] Stocker le Type en frontend uniquement (pas en backend)
- [x] Utiliser le Type pour filtrer les catégories disponibles lors de l'ajout d'une ligne (Step 7.5.7)
- [x] **Tester dans le navigateur**

**Acceptance Criteria**:
- [x] Type affiché avec dropdown éditable pour chaque ligne
- [x] Modification du Type possible via dropdown
- [x] Plusieurs lignes peuvent avoir le même Type
- [x] Type initialisé automatiquement selon la catégorie au chargement
- [x] **Test visuel dans navigateur validé**

---

#### Step 7.5.4 : Frontend - Colonne 2 "Catégorie comptable"
**Status**: ✅ TERMINÉ  
**Description**: Ajouter dropdown "Catégorie comptable" en deuxième colonne. Le dropdown doit filtrer les catégories disponibles selon le Type sélectionné en colonne 1.

**Tasks**:
- [x] Ajouter dropdown "Catégorie comptable" en deuxième colonne
- [x] Filtrer les catégories disponibles selon le Type sélectionné en colonne 1 :
  - Si Type = "Produits d'exploitation" → afficher seulement les catégories de `PRODUITS_CATEGORIES`
  - Si Type = "Charges d'exploitation" → afficher seulement les catégories de `CHARGES_CATEGORIES`
- [x] Permettre la sélection d'une catégorie dans le dropdown
- [x] Permettre plusieurs lignes avec la même catégorie comptable
- [x] Gérer les catégories spéciales (amortissements, coût financement) :
  - Ces catégories doivent être disponibles dans le dropdown si le Type correspond
  - Afficher "Données calculées" dans les colonnes Level 1 et Level 2 (read-only)
  - Pas de dropdown pour Level 1/Level 2 pour ces catégories
- [x] Sauvegarde automatique au changement de catégorie (mise à jour du mapping via API)
- [x] Réinitialiser automatiquement la catégorie si elle n'est plus valide après un changement de Type
- [x] **Tester dans le navigateur**

**Acceptance Criteria**:
- [x] Dropdown visible et fonctionnel pour chaque ligne
- [x] Catégories filtrées dynamiquement selon le Type sélectionné en colonne 1
- [x] Changement de Type en colonne 1 met à jour les options disponibles dans le dropdown de la colonne 2
- [x] Si la catégorie actuelle n'est plus valide après un changement de Type, elle est réinitialisée automatiquement
- [x] Sauvegarde automatique fonctionne (mise à jour du mapping en backend)
- [x] Plusieurs lignes peuvent avoir la même catégorie comptable
- [x] Catégories spéciales affichées avec "Données calculées" dans Level 1 et Level 2
- [x] **Test visuel dans navigateur validé**

---

#### Step 7.5.5 : Frontend - Colonne 3 "Level 1 (valeurs)"
**Status**: ✅ TERMINÉ  
**Description**: Implémenter l'affichage et la gestion des tags level_1 (comme AmortizationConfigCard).

**Tasks**:
- [x] Implémenter l'affichage des tags bleus pour les valeurs level_1 sélectionnées
- [x] Ajouter bouton "+ Ajouter" qui ouvre un dropdown avec toutes les valeurs level_1 disponibles
- [x] Charger les valeurs level_1 depuis les transactions enrichies (valeurs uniques via `transactionsAPI.getUniqueValues('level_1')`)
- [x] Implémenter l'ajout d'une valeur (tag bleu avec "x")
- [x] Implémenter la suppression d'une valeur (clic sur "x")
- [x] Sauvegarde automatique à chaque ajout/suppression
- [x] Filtrer les valeurs déjà assignées dans le dropdown
- [x] Désactiver le bouton "+ Ajouter" si toutes les valeurs sont déjà assignées
- [x] Pour les catégories spéciales, afficher "Données calculées" (read-only, grisé)
- [x] **Tester dans le navigateur**

**Acceptance Criteria**:
- [x] Tags bleus affichés pour les valeurs level_1
- [x] Bouton "+ Ajouter" ouvre dropdown avec valeurs disponibles
- [x] Ajout/suppression fonctionne
- [x] Sauvegarde automatique fonctionne (mise à jour du mapping via API)
- [x] Valeurs déjà assignées filtrées du dropdown
- [x] Catégories spéciales affichent "Données calculées"
- [x] **Test visuel dans navigateur validé**

---

#### Step 7.5.6 : Frontend - Colonne 4 "Level 2 (valeurs)"
**Status**: ✅ TERMINÉ  
**Description**: Implémenter l'affichage et la gestion des tags level_2 (comme AmortizationConfigCard).

**Tasks**:
- [x] Implémenter l'affichage des tags bleus pour les valeurs level_2 sélectionnées
- [x] Ajouter bouton "+ Ajouter" qui ouvre un dropdown avec toutes les valeurs level_2 disponibles
- [x] Charger les valeurs level_2 depuis les transactions enrichies (valeurs uniques via `transactionsAPI.getUniqueValues('level_2')`)
- [x] Implémenter l'ajout d'une valeur (tag bleu avec "x")
- [x] Implémenter la suppression d'une valeur (clic sur "x")
- [x] Sauvegarde automatique à chaque ajout/suppression
- [x] Filtrer les valeurs déjà assignées dans le dropdown
- [x] Désactiver le bouton "+ Ajouter" si toutes les valeurs sont déjà assignées
- [x] Pour les catégories spéciales, afficher "Données calculées" (read-only, grisé)
- [x] **Tester dans le navigateur**

**Acceptance Criteria**:
- [x] Tags bleus affichés pour les valeurs level_2
- [x] Bouton "+ Ajouter" ouvre dropdown avec valeurs disponibles
- [x] Ajout/suppression fonctionne
- [x] Sauvegarde automatique fonctionne (mise à jour du mapping via API)
- [x] Valeurs déjà assignées filtrées du dropdown
- [x] Catégories spéciales affichent "Données calculées"
- [x] **Test visuel dans navigateur validé**

---

#### Step 7.5.7 : Frontend - Ajout de lignes (catégories)
**Status**: ✅ TERMINÉ  
**Description**: Ajouter bouton "+ Ajouter une catégorie" en bas du tableau (comme "+ Ajouter un type" dans AmortizationConfigCard).

**Tasks**:
- [x] Ajouter bouton "+ Ajouter une catégorie" en bas du tableau (dans une ligne spéciale, comme AmortizationConfigCard)
- [x] **PAS DE MODAL** - Création directe d'une ligne avec catégorie par défaut (comme AmortizationConfigCard)
- [x] Prendre la première catégorie de "Charges d'exploitation" par défaut
- [x] Créer une nouvelle ligne avec la catégorie sélectionnée
- [x] Sauvegarde automatique à la création
- [x] **Tester dans le navigateur**

**Acceptance Criteria**:
- [x] Bouton "+ Ajouter une catégorie" visible en bas du tableau
- [x] Création directe sans modal (comme AmortizationConfigCard)
- [x] Nouvelle ligne créée avec catégorie par défaut
- [x] Sauvegarde automatique fonctionne
- [x] **Test visuel dans navigateur validé**

---

#### Step 7.5.8 : Frontend - Suppression de lignes (catégories)
**Status**: ✅ TERMINÉ  
**Description**: Implémenter le menu contextuel (clic droit) pour supprimer une ligne (comme AmortizationConfigCard).

**Tasks**:
- [x] Implémenter le menu contextuel (clic droit) sur une ligne
- [x] Ajouter option "🗑️ Supprimer" dans le menu
- [x] Confirmation avant suppression (comme AmortizationConfigCard)
- [x] Supprimer le mapping depuis l'API (`compteResultatAPI.deleteMapping(id)`)
- [x] Recharger les mappings après suppression
- [x] **Tester dans le navigateur**

**Acceptance Criteria**:
- [x] Menu contextuel s'affiche au clic droit
- [x] Option "🗑️ Supprimer" visible
- [x] Confirmation demandée avant suppression
- [x] Suppression fonctionne (backend)
- [x] Tableau se rafraîchit après suppression
- [x] **Test visuel dans navigateur validé**

---

#### Step 7.5.9 : Frontend - Bouton "Réinitialiser les mappings"
**Status**: ✅ TERMINÉ  
**Description**: Ajouter bouton "🔄 Réinitialiser les mappings" dans le header de la card (comme AmortizationConfigCard).

**Tasks**:
- [x] Ajouter bouton "🔄 Réinitialiser les mappings" dans le header de la card
- [x] Bouton visible uniquement s'il y a des mappings
- [x] Confirmation avant réinitialisation (comme AmortizationConfigCard)
- [x] Supprimer tous les mappings depuis l'API (un par un)
- [x] Afficher le nombre de mappings à supprimer dans la confirmation
- [x] Recharger les mappings après réinitialisation
- [x] Message de succès après réinitialisation
- [x] **Tester dans le navigateur**

**Acceptance Criteria**:
- [x] Bouton visible dans le header (uniquement si mappings existent)
- [x] Confirmation demandée avant réinitialisation avec nombre de mappings
- [x] Tous les mappings supprimés
- [x] Tableau se rafraîchit après réinitialisation
- [x] Message de succès affiché
- [x] **Test visuel dans navigateur validé**

---

#### Step 7.5.10 : Frontend - Bouton engrenage (Save/Load/Delete)
**Status**: ✅ TERMINÉ  
**Description**: Ajouter un bouton engrenage (⚙️) à droite du bouton "Réinitialiser les mappings" avec les mêmes fonctionnalités que dans AmortizationConfigCard : Save, Load, Delete.

**Tasks**:
- [x] Ajouter un bouton engrenage (⚙️) dans le header à droite du bouton "Réinitialiser les mappings"
- [x] Menu déroulant avec 3 options : "Load...", "Save", "Delete..."
- [x] **Save** : Popup pour sauvegarder la configuration actuelle des mappings sous un nom
  - Champ texte pour le nom de la vue
  - Bouton "Sauvegarder" et "Annuler"
  - Sauvegarder tous les mappings actuels dans une vue (backend)
  - Gestion de l'écrasement si une vue avec le même nom existe déjà
- [x] **Load** : Popup pour charger une vue sauvegardée
  - Liste déroulante avec toutes les vues disponibles
  - Option "(default)" pour ne rien charger
  - Confirmation avant chargement (remplace la configuration actuelle)
  - Charger tous les mappings de la vue sélectionnée
- [x] **Delete** : Popup pour supprimer une vue sauvegardée
  - Liste déroulante avec toutes les vues disponibles
  - Confirmation avant suppression
  - Supprimer la vue sélectionnée
- [x] Backend : Créer les tables et modèles pour les vues de mappings (CompteResultatMappingView)
- [x] Backend : API endpoints pour CRUD des vues (create, get, list, delete)
- [x] Script de migration pour créer la table
- [x] Gérer l'état du menu (ouvert/fermé)
- [x] Fermer le menu au clic ailleurs
- [x] **Tester dans le navigateur**

**Acceptance Criteria**:
- [x] Bouton engrenage visible dans le header
- [x] Menu déroulant fonctionne (ouvre/ferme)
- [x] Save : Popup fonctionne, sauvegarde la configuration
- [x] Load : Popup fonctionne, charge une vue sauvegardée
- [x] Delete : Popup fonctionne, supprime une vue
- [x] Backend : Tables et API fonctionnelles
- [x] **Test visuel dans navigateur validé**

---

#### Step 7.5.11 : Frontend - Colonne "Vue" et gestion des charges d'amortissement
**Status**: ✅ TERMINÉ  
**Description**: Ajouter une colonne "Vue" au tableau et gérer la sélection de vue d'amortissement pour la catégorie "Charges d'amortissements".

**Tasks**:
- [x] Ajouter une nouvelle colonne "Vue" au tableau (5 colonnes au total : Type, Catégorie comptable, Level 1, Level 2, Vue)
- [x] Pour toutes les catégories sauf "Charges d'amortissements" et "Coût du financement" :
  - Afficher "Aucune valeur" en grisé (read-only)
- [x] Pour la catégorie "Charges d'amortissements" :
  - Dropdown avec toutes les vues d'amortissement sauvegardées (via `amortizationViewsAPI.getAll()`)
  - Si aucune vue sauvegardée : afficher "vue à configurer" (grisé)
  - Permettre de sélectionner une vue d'amortissement
  - Sauvegarder la sélection en base de données (backend : ajouter champ `amortization_view_id` dans `CompteResultatMapping`)
- [x] Afficher "Données calculées" dans les colonnes Level 1 (valeurs) et Level 2 (valeurs) pour cette catégorie
- [x] Désactiver les colonnes Level 1 et Level 2 pour cette catégorie (read-only, grisées)
- [x] Afficher un message explicatif (tooltip ou texte) : "Données récupérées depuis les vues d'amortissement (AmortizationTable) en fonction de l'année"
- [x] Backend : Ajouter champ `amortization_view_id` dans `CompteResultatMapping`
- [x] Backend : Script de migration pour ajouter la colonne
- [x] Backend : Mettre à jour les modèles Pydantic et l'API
- [x] **Tester dans le navigateur**

**Acceptance Criteria**:
- [x] Colonne "Vue" ajoutée au tableau (5 colonnes au total)
- [x] "Aucune valeur" affiché en grisé pour les catégories normales
- [x] Catégorie "Charges d'amortissements" détectée automatiquement
- [x] Dropdown avec vues d'amortissement fonctionne
- [x] "vue à configurer" affiché si aucune vue disponible
- [x] Sélection de la vue sauvegardée et persistée en BDD
- [x] Badge "Données calculées" affiché dans colonnes Level 1 et Level 2
- [x] Colonnes Level 1 et Level 2 désactivées (read-only, grisées)
- [x] Message explicatif affiché (tooltip ou texte)
- [x] **Test visuel dans navigateur validé**

---

#### Step 7.5.12 : Frontend - Gestion des coûts du financement
**Status**: ✅ TERMINÉ  
**Description**: Gérer la sélection de crédits pour la catégorie "Coût du financement (hors remboursement du capital)" dans la colonne "Vue".

**Tasks**:
- [x] Pour la catégorie "Coût du financement (hors remboursement du capital)" :
  - Dans la colonne "Vue" : Dropdown avec checkboxes (multi-sélection)
  - Récupérer tous les crédits configurés (via `loanConfigsAPI.getAll()`)
  - Afficher la liste des crédits avec checkboxes (nom du crédit)
  - Permettre de sélectionner un ou plusieurs crédits
  - Si aucun crédit configuré : afficher "vue à configurer" (grisé)
  - Sauvegarder la sélection en base de données (backend : stocker les IDs des crédits sélectionnés dans `selected_loan_ids` JSON)
- [x] Afficher "Données calculées" dans les colonnes Level 1 (valeurs) et Level 2 (valeurs) pour cette catégorie
- [x] Désactiver les colonnes Level 1 et Level 2 pour cette catégorie (read-only, grisées)
- [x] Afficher un message explicatif (tooltip ou texte) : "Données récupérées depuis la table loan_payments (somme interest + insurance par année pour les crédits sélectionnés)"
- [x] Gérer dynamiquement l'ajout/suppression de crédits (si un crédit est ajouté/supprimé, mettre à jour le dropdown)
- [x] Fermeture du dropdown au clic ailleurs
- [x] **Tester dans le navigateur**

**Acceptance Criteria**:
- [x] Catégorie "Coût du financement" détectée automatiquement
- [x] Dropdown avec checkboxes fonctionne dans la colonne "Vue"
- [x] Liste des crédits configurés affichée avec checkboxes
- [x] Multi-sélection fonctionne (un ou plusieurs crédits)
- [x] "vue à configurer" affiché si aucun crédit disponible
- [x] Sélection des crédits sauvegardée et persistée en BDD
- [x] Badge "Données calculées" affiché dans colonnes Level 1 et Level 2
- [x] Colonnes Level 1 et Level 2 désactivées (read-only, grisées)
- [x] Mise à jour automatique lors de l'ajout/suppression de crédits
- [x] Message explicatif affiché (tooltip ou texte)
- [x] **Test visuel dans navigateur validé**

---

**Step 7.5 - Acceptance Criteria globaux**:
- [ ] Tableau affiché dans l'onglet "Compte de résultat" (structure comme AmortizationConfigCard)
- [ ] 5 colonnes : Type, Catégorie comptable, Level 1 (valeurs), Level 2 (valeurs), Vue
- [ ] Dropdown Type fonctionne et filtre les catégories
- [ ] Dropdown Catégorie fonctionne avec catégories prédéfinies
- [ ] Tags bleus pour level_1 avec "+ Ajouter" et "x" pour supprimer
- [ ] Tags bleus pour level_2 avec "+ Ajouter" et "x" pour supprimer
- [ ] Bouton "+ Ajouter une catégorie" fonctionne (création directe, pas de modal)
- [ ] Menu contextuel (clic droit) avec "Supprimer" fonctionne
- [ ] Bouton "🔄 Réinitialiser les mappings" fonctionne
- [ ] Bouton engrenage (⚙️) avec Save/Load/Delete fonctionne (Step 7.5.10)
- [ ] Catégorie spéciale "Charges d'amortissements" gérée correctement (Step 7.5.11)
- [ ] Catégorie spéciale "Coût du financement" gérée correctement (Step 7.5.12)
- [ ] Sauvegarde automatique fonctionne (comme AmortizationConfigCard)
- [ ] API client créé et fonctionnel
- [ ] **Test visuel dans navigateur validé**
- [ ] **Utilisateur confirme que l'interface correspond à ses attentes**

---

### Step 7.6 : Frontend - Card d'affichage (CompteResultatTable)
**Status**: ⏸️ EN ATTENTE  
**Description**: Créer l'interface d'affichage du compte de résultat avec tableau multi-années. Structure identique à `AmortizationTable`.

**⚠️ IMPORTANT : Liaison avec CompteResultatConfigCard**
- La `CompteResultatTable` est **toujours liée** aux données affichées dans `CompteResultatConfigCard`
- Les montants affichés dans le tableau sont calculés **uniquement** à partir des mappings configurés dans la card config
- Les catégories affichées dans le tableau correspondent **exactement** aux catégories configurées dans la card config
- Les vues d'amortissement et crédits utilisés sont ceux **sélectionnés dans la colonne "Vue"** de la card config (Steps 7.5.11 et 7.5.12)
- Toute modification dans la card config (ajout/suppression de mapping, changement de vue, changement de crédits) doit **automatiquement** mettre à jour le tableau
- Le tableau ne doit afficher que les catégories qui ont au moins un mapping configuré dans la card config

**Structure du tableau** :
- **Colonnes** : Catégories | Année 1 | Année 2 | Année 3 | ... (jusqu'à l'année en cours)
- **Lignes** :
  - **Total des produits d'exploitation** (ligne de total, fond gris)
  - Loyers hors charge encaissés
  - Charges locatives payées par locataires
  - Autres revenus
  - **Total des charges d'exploitation** (ligne de total, fond gris)
  - Charges de copropriété hors fonds travaux
  - Fluides non refacturés
  - Assurances
  - Honoraires
  - Travaux et mobilier
  - Impôts et taxes
  - Charges d'amortissements
  - Autres charges diverses
  - Coût du financement (hors remboursement du capital)
  - **Résultat d'exploitation** (ligne de total, fond gris) = Produits - Charges
  - **Résultat net de l'exercice** (ligne de total, fond gris, texte magenta) = Résultat d'exploitation

**Fonctionnalités** :
- Calculer automatiquement pour toutes les années jusqu'à l'année en cours
- Possibilité d'ajouter des années au fur et à mesure
- Utiliser les vues d'amortissement et crédits sélectionnés dans la card config (Step 7.5.11 et 7.5.12)
- Formatage des montants (€, séparateurs de milliers, 2 décimales)
- Mise en évidence des totaux (fond gris, texte en gras)
- Résultat net en magenta (comme dans l'image)

---

#### Step 7.6.1 : Frontend - Structure de base du tableau
**Status**: ⏸️ EN ATTENTE  
**Description**: Créer la structure de base du composant et du tableau (comme AmortizationTable).

**Tasks**:
- [ ] Créer composant `CompteResultatTable.tsx` (copier structure de base d'`AmortizationTable`)
- [ ] Créer le tableau avec colonnes : Catégories | Années (dynamiques)
- [ ] Définir la liste des catégories comptables (ordre fixe)
- [ ] Calculer automatiquement les années à afficher (de la première transaction jusqu'à l'année en cours)
- [ ] Afficher les en-têtes de colonnes (Catégories + une colonne par année)
- [ ] Intégrer dans l'onglet "Compte de résultat" (sous la card de config)
- [ ] **Tester dans le navigateur**

**Deliverables**:
- `frontend/src/components/CompteResultatTable.tsx` - Structure de base
- Mise à jour `frontend/app/dashboard/etats-financiers/page.tsx` - Intégration

**Acceptance Criteria**:
- [ ] Tableau affiché avec colonnes dynamiques (années)
- [ ] Catégories affichées dans l'ordre fixe
- [ ] Années calculées automatiquement (jusqu'à l'année en cours)
- [ ] **Test visuel dans navigateur validé**

---

#### Step 7.6.2 : Backend - Calcul des montants par catégorie et année
**Status**: ⏸️ EN ATTENTE  
**Description**: Implémenter le calcul des montants pour chaque catégorie et chaque année en utilisant **uniquement** les configurations de la card config (`CompteResultatConfigCard`).

**⚠️ Principe fondamental** :
- Les calculs sont basés **exclusivement** sur les mappings configurés dans `CompteResultatConfigCard`
- Seules les catégories avec au moins un mapping configuré sont calculées et affichées
- Les vues d'amortissement et crédits utilisés sont ceux sélectionnés dans la card config

**Tasks**:
- [ ] Mettre à jour `compte_resultat_service.py` pour calculer les montants par catégorie et année
- [ ] Récupérer tous les mappings configurés depuis `CompteResultatMapping`
- [ ] Pour chaque catégorie avec mapping level_1/level_2 :
  - Filtrer les transactions par année (date entre 01/01/année et 31/12/année)
  - Filtrer par level_1 OU level_2 selon le mapping (logique OR)
  - Si plusieurs mappings pour la même catégorie : sommer les résultats de tous les mappings
  - Sommer les montants (`Transaction.quantite`)
- [ ] Pour "Charges d'amortissements" :
  - Récupérer le mapping correspondant et son `amortization_view_id`
  - Si `amortization_view_id` est défini : récupérer le total depuis cette vue d'amortissement pour l'année
  - Si `amortization_view_id` est NULL : retourner 0 ou une erreur
- [ ] Pour "Coût du financement (hors remboursement du capital)" :
  - Récupérer le mapping correspondant et son `selected_loan_ids`
  - Si `selected_loan_ids` est défini : filtrer `loan_payments` par année et par les IDs de crédits sélectionnés
  - Sommer `interest` + `insurance` uniquement pour les crédits sélectionnés
  - Si `selected_loan_ids` est NULL ou vide : retourner 0
- [ ] Créer endpoint `GET /api/compte-resultat/calculate?year={year}` qui retourne les montants par catégorie pour une année donnée
- [ ] Ou créer endpoint `GET /api/compte-resultat/calculate?years={year1,year2,...}` pour plusieurs années
- [ ] **Créer test unitaire**
- [ ] **Valider avec l'utilisateur**

**Deliverables**:
- Mise à jour `backend/api/services/compte_resultat_service.py` - Calculs par catégorie/année
- Mise à jour `backend/api/routes/compte_resultat.py` - Endpoint de calcul
- `backend/tests/test_compte_resultat_calculs.py` - Tests de calculs

**Acceptance Criteria**:
- [ ] Calculs corrects pour chaque catégorie avec mapping
- [ ] Utilisation de `amortization_view_id` du mapping pour "Charges d'amortissements"
- [ ] Utilisation de `selected_loan_ids` du mapping pour "Coût du financement"
- [ ] Gestion des cas où vue/crédits ne sont pas sélectionnés (retourner 0)
- [ ] Endpoint retourne les montants par catégorie et année
- [ ] Tests passent
- [ ] **Utilisateur confirme que les calculs sont corrects**

---

#### Step 7.6.3 : Frontend - Chargement et affichage des montants
**Status**: ⏸️ EN ATTENTE  
**Description**: Charger les montants depuis l'API et les afficher dans le tableau. **Les montants sont toujours liés aux mappings de la card config.**

**⚠️ Liaison avec CompteResultatConfigCard** :
- Le tableau doit se mettre à jour automatiquement quand les mappings changent dans la card config
- Utiliser le callback `onConfigUpdated` de `CompteResultatConfigCard` pour déclencher le rechargement
- Afficher uniquement les catégories qui ont des mappings configurés dans la card config

**Tasks**:
- [ ] Appeler l'API pour calculer les montants pour toutes les années (jusqu'à l'année en cours)
- [ ] Afficher les montants dans les cellules correspondantes (catégorie × année)
- [ ] Gérer l'état de chargement (spinner ou "Chargement...")
- [ ] Gérer les erreurs (affichage de message d'erreur)
- [ ] Recharger les données quand les mappings changent (via callback `onConfigUpdated` de la card config)
- [ ] Afficher un message si une catégorie spéciale n'a pas de vue/crédits sélectionnés (ex: "Vue non configurée")
- [ ] **Tester dans le navigateur**

**Acceptance Criteria**:
- [ ] Montants chargés depuis l'API
- [ ] Montants affichés dans les bonnes cellules
- [ ] État de chargement géré
- [ ] Erreurs gérées
- [ ] Rechargement automatique quand les mappings changent dans la card config
- [ ] Message affiché si vue/crédits non configurés
- [ ] **Test visuel dans navigateur validé**

---

#### Step 7.6.4 : Frontend - Test et validation des charges d'amortissements
**Status**: ⏸️ EN ATTENTE  
**Description**: Tester et valider spécifiquement l'affichage correct de la catégorie "Charges d'amortissements".

**Tasks**:
- [ ] Vérifier que les montants sont récupérés depuis la vue d'amortissement sélectionnée dans la card config (Step 7.5.11)
- [ ] Tester avec une vue d'amortissement sélectionnée : montants affichés correctement dans le tableau
- [ ] Tester sans vue sélectionnée : afficher "Vue non configurée" ou 0,00 €
- [ ] Vérifier que les montants correspondent aux totaux de la vue d'amortissement pour chaque année
  - Comparer avec les données de `AmortizationResult` pour la vue sélectionnée
  - Vérifier que la somme par année correspond au total d'amortissement de la vue
- [ ] Tester le rechargement automatique quand la vue d'amortissement change dans la card config
- [ ] Tester avec différentes vues d'amortissement : vérifier que les montants changent correctement
- [ ] Vérifier que les montants sont corrects pour plusieurs années
- [ ] **Tester dans le navigateur**

**Acceptance Criteria**:
- [ ] Montants corrects depuis la vue sélectionnée dans la card config
- [ ] Message affiché si vue non configurée
- [ ] Montants correspondent aux totaux de la vue d'amortissement pour chaque année
- [ ] Rechargement automatique quand vue change dans card config
- [ ] Montants corrects pour plusieurs années
- [ ] **Test visuel dans navigateur validé**
- [ ] **Utilisateur confirme que les montants sont corrects**

---

#### Step 7.6.5 : Frontend - Test et validation du coût du financement
**Status**: ⏸️ EN ATTENTE  
**Description**: Tester et valider spécifiquement l'affichage correct de la catégorie "Coût du financement (hors remboursement du capital)".

**Tasks**:
- [ ] Vérifier que les montants sont calculés depuis les crédits sélectionnés dans la card config (Step 7.5.12)
- [ ] Tester avec un crédit sélectionné : montants affichés correctement (interest + insurance)
- [ ] Tester avec plusieurs crédits sélectionnés : somme des montants de tous les crédits
- [ ] Tester sans crédit sélectionné : afficher "Crédits non configurés" ou 0,00 €
- [ ] Vérifier que les montants correspondent à la somme des loan_payments (interest + insurance) pour les crédits sélectionnés, par année
  - Filtrer `loan_payments` par année et par les IDs de crédits sélectionnés
  - Sommer `interest + insurance` pour chaque crédit sélectionné
  - Vérifier que le total correspond au montant affiché
- [ ] Tester le rechargement automatique quand les crédits sélectionnés changent dans la card config
- [ ] Tester avec différents crédits sélectionnés : vérifier que les montants changent correctement
- [ ] Vérifier que les montants sont corrects pour plusieurs années
- [ ] **Tester dans le navigateur**

**Acceptance Criteria**:
- [ ] Montants corrects depuis les crédits sélectionnés dans la card config
- [ ] Somme correcte pour plusieurs crédits sélectionnés
- [ ] Message affiché si crédits non configurés
- [ ] Montants correspondent à la somme des loan_payments (interest + insurance) pour les crédits sélectionnés
- [ ] Rechargement automatique quand crédits changent dans card config
- [ ] Montants corrects pour plusieurs années
- [ ] **Test visuel dans navigateur validé**
- [ ] **Utilisateur confirme que les montants sont corrects**

---

#### Step 7.6.6 : Frontend - Calcul et affichage des totaux
**Status**: ⏸️ EN ATTENTE  
**Description**: Calculer et afficher les lignes de totaux (comme dans l'image).

**Tasks**:
- [ ] Calculer "Total des produits d'exploitation" = somme des 3 catégories de produits
- [ ] Calculer "Total des charges d'exploitation" = somme des 9 catégories de charges
- [ ] Calculer "Résultat d'exploitation" = Total produits - Total charges
- [ ] Calculer "Résultat net de l'exercice" = Résultat d'exploitation
- [ ] Afficher les lignes de totaux avec fond gris (comme dans l'image)
- [ ] Afficher "Résultat net" en magenta (comme dans l'image)
- [ ] Mettre en évidence les totaux (texte en gras)
- [ ] **Tester dans le navigateur**

**Acceptance Criteria**:
- [ ] Totaux calculés correctement
- [ ] Lignes de totaux affichées avec fond gris
- [ ] Résultat net en magenta
- [ ] Totaux mis en évidence (texte en gras)
- [ ] **Test visuel dans navigateur validé**

---

#### Step 7.6.7 : Frontend - Formatage des montants
**Status**: ⏸️ EN ATTENTE  
**Description**: Formater les montants (€, séparateurs de milliers, 2 décimales).

**Tasks**:
- [ ] Formater les montants avec séparateurs de milliers (ex: 1 234,56 €)
- [ ] Afficher 2 décimales
- [ ] Afficher le symbole €
- [ ] Gérer les valeurs négatives (affichage en rouge ou avec signe -)
- [ ] Gérer les valeurs nulles (affichage "0,00 €" ou vide)
- [ ] **Tester dans le navigateur**

**Acceptance Criteria**:
- [ ] Montants formatés correctement (1 234,56 €)
- [ ] 2 décimales affichées
- [ ] Symbole € visible
- [ ] Valeurs négatives gérées
- [ ] **Test visuel dans navigateur validé**

---

#### Step 7.6.8 : Frontend - Ajout d'années
**Status**: ⏸️ EN ATTENTE  
**Description**: Permettre d'ajouter des années au fur et à mesure.

**Tasks**:
- [ ] Ajouter bouton "+ Ajouter une année" dans le header
- [ ] Ouvrir un input ou dropdown pour sélectionner une année
- [ ] Calculer et afficher les montants pour la nouvelle année
- [ ] Ajouter la colonne correspondante dans le tableau
- [ ] Sauvegarder la liste des années ajoutées (localStorage ou state)
- [ ] **Tester dans le navigateur**

**Acceptance Criteria**:
- [ ] Bouton "+ Ajouter une année" visible
- [ ] Sélection d'année fonctionne
- [ ] Nouvelle colonne ajoutée au tableau
- [ ] Montants calculés pour la nouvelle année
- [ ] Liste des années sauvegardée
- [ ] **Test visuel dans navigateur validé**

---

**Step 7.6 - Acceptance Criteria globaux**:
- [ ] Tableau affiché dans l'onglet "Compte de résultat" (sous la card de config)
- [ ] **⚠️ LIAISON AVEC CompteResultatConfigCard** : Le tableau est **toujours lié** aux données de la card config
- [ ] **Seules les catégories avec mappings configurés dans la card config sont affichées**
- [ ] Structure : 1 colonne catégories + 1 colonne par année
- [ ] Années calculées automatiquement (jusqu'à l'année en cours)
- [ ] Utilisation des vues d'amortissement et crédits sélectionnés dans la card config (Steps 7.5.11 et 7.5.12)
- [ ] Montants calculés et affichés correctement pour toutes les catégories configurées
- [ ] Totaux calculés et affichés (fond gris, texte en gras)
- [ ] Résultat net en magenta
- [ ] Formatage des montants correct (€, séparateurs, 2 décimales)
- [ ] Ajout d'années fonctionne
- [ ] **Rechargement automatique quand les mappings changent dans la card config**
- [ ] **Toute modification dans la card config (ajout/suppression mapping, changement vue/crédits) met à jour le tableau automatiquement**
- [ ] **Test visuel dans navigateur validé**
- [ ] **Utilisateur confirme que l'interface correspond à l'image**

---

## Phase 8 : Bilans et autres états financiers

### Step 8.1 : Service bilans backend
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

### Step 8.2 : Vue bilan frontend
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

## Phase 9 : Consolidation et autres vues

### Step 9.1 : Service consolidation backend
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

### Step 9.2 : Vue cashflow frontend
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


## Phase 10 : Tests et validation finale

### Step 10.1 : Tests end-to-end
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

### Step 10.2 : Documentation et finalisation
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

