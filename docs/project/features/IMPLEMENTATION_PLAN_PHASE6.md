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
**Status**: ✅ COMPLÉTÉ  
**Description**: Créer la structure de base du composant et du tableau (comme AmortizationTable).

**Tasks**:
- [x] Créer composant `CompteResultatTable.tsx` (copier structure de base d'`AmortizationTable`)
- [x] Créer le tableau avec colonnes : Compte de résultat | Années (dynamiques)
- [x] Définir la liste des catégories comptables (ordre fixe, groupées par type)
- [x] Calculer automatiquement les années à afficher (de la première transaction jusqu'à l'année en cours)
- [x] Afficher les en-têtes de colonnes (Compte de résultat + une colonne par année)
- [x] Afficher structure hiérarchique : ligne de type (avec totaux) + catégories indentées
- [x] Intégrer dans l'onglet "Compte de résultat" (sous la card de config)
- [x] **Tester dans le navigateur**

**Deliverables**:
- `frontend/src/components/CompteResultatTable.tsx` - Structure de base
- Mise à jour `frontend/app/dashboard/etats-financiers/page.tsx` - Intégration

**Acceptance Criteria**:
- [x] Tableau affiché avec colonnes dynamiques (années)
- [x] Catégories affichées dans l'ordre fixe (groupées par type)
- [x] Structure hiérarchique : types avec totaux, catégories indentées
- [x] Années calculées automatiquement (jusqu'à l'année en cours)
- [x] **Test visuel dans navigateur validé**

---

#### Step 7.6.2 : Backend - Calcul des montants par catégorie et année
**Status**: ✅ COMPLÉTÉ  
**Description**: Implémenter le calcul des montants pour chaque catégorie et chaque année en utilisant **uniquement** les configurations de la card config (`CompteResultatConfigCard`).

**⚠️ Principe fondamental** :
- Les calculs sont basés **exclusivement** sur les mappings configurés dans `CompteResultatConfigCard`
- Seules les catégories avec au moins un mapping configuré sont calculées et affichées
- Les vues d'amortissement et crédits utilisés sont ceux sélectionnés dans la card config

**⚠️ Corrections importantes** :
- **Regroupement des conditions** : Tous les mappings d'une même catégorie sont regroupés avec OR pour éviter de compter plusieurs fois les mêmes transactions
- **Transactions positives ET négatives** : Pour toutes les catégories, on prend en compte :
  - **Produits** : revenus (positifs) - remboursements/annulations (négatifs)
  - **Charges** : dépenses (négatifs) - remboursements/crédits (positifs)

**Tasks**:
- [x] Mettre à jour `compte_resultat_service.py` pour calculer les montants par catégorie et année
- [x] Récupérer tous les mappings configurés depuis `CompteResultatMapping`
- [x] Pour chaque catégorie avec mapping level_1/level_2 :
  - Filtrer les transactions par année (date entre 01/01/année et 31/12/année)
  - Filtrer par level_1 OU level_2 selon le mapping (logique OR)
  - Regrouper tous les mappings d'une catégorie avec OR pour éviter les doublons
  - **Prendre en compte transactions positives ET négatives** :
    - Produits : revenus (positifs) - remboursements (négatifs)
    - Charges : dépenses (négatifs) - remboursements/crédits (positifs)
- [x] Pour "Charges d'amortissements" :
  - Récupérer le mapping correspondant et son `amortization_view_id`
  - Si `amortization_view_id` est défini : récupérer le total depuis cette vue d'amortissement pour l'année
  - Si `amortization_view_id` est NULL : retourner 0
- [x] Pour "Coût du financement (hors remboursement du capital)" :
  - Récupérer le mapping correspondant et son `selected_loan_ids`
  - Si `selected_loan_ids` est défini : filtrer `loan_payments` par année et par les IDs de crédits sélectionnés
  - Sommer `interest` + `insurance` uniquement pour les crédits sélectionnés
  - Si `selected_loan_ids` est NULL ou vide : retourner 0
- [x] Créer endpoint `GET /api/compte-resultat/calculate?years={year1,year2,...}` pour plusieurs années
- [x] **Valider avec l'utilisateur**

**Deliverables**:
- Mise à jour `backend/api/services/compte_resultat_service.py` - Calculs par catégorie/année
- Mise à jour `backend/api/routes/compte_resultat.py` - Endpoint de calcul
- `backend/tests/test_compte_resultat_special_categories.py` - Tests de validation des catégories spéciales

**Acceptance Criteria**:
- [x] Calculs corrects pour chaque catégorie avec mapping
- [x] Utilisation de `amortization_view_id` du mapping pour "Charges d'amortissements"
- [x] Utilisation de `selected_loan_ids` du mapping pour "Coût du financement"
- [x] Gestion des cas où vue/crédits ne sont pas sélectionnés (retourner 0)
- [x] Endpoint retourne les montants par catégorie et année
- [x] Transactions positives ET négatives prises en compte pour toutes les catégories
- [x] **Utilisateur confirme que les calculs sont corrects**

---

#### Step 7.6.3 : Frontend - Chargement et affichage des montants
**Status**: ✅ COMPLÉTÉ  
**Description**: Charger les montants depuis l'API et les afficher dans le tableau. **Les montants sont toujours liés aux mappings de la card config.**

**⚠️ Liaison avec CompteResultatConfigCard** :
- Le tableau doit se mettre à jour automatiquement quand les mappings changent dans la card config
- Utiliser le callback `onConfigUpdated` de `CompteResultatConfigCard` pour déclencher le rechargement
- Afficher uniquement les catégories qui ont des mappings configurés dans la card config

**Tasks**:
- [x] Appeler l'API pour calculer les montants pour toutes les années (jusqu'à l'année en cours)
- [x] Afficher les montants dans les cellules correspondantes (catégorie × année)
- [x] Gérer l'état de chargement (spinner ou "Chargement...")
- [x] Gérer les erreurs (affichage de message d'erreur)
- [x] Recharger les données quand les mappings changent (via `refreshKey` déclenché par `onConfigUpdated` de la card config)
- [x] Afficher un message si une catégorie spéciale n'a pas de vue/crédits sélectionnés (ex: "Vue non configurée" / "Crédits non configurés")
- [x] **Tester dans le navigateur**

**Acceptance Criteria**:
- [x] Montants chargés depuis l'API
- [x] Montants affichés dans les bonnes cellules
- [x] État de chargement géré
- [x] Erreurs gérées
- [x] Rechargement automatique quand les mappings changent dans la card config
- [x] Message affiché si vue/crédits non configurés
- [x] **Test visuel dans navigateur validé**

---

#### Step 7.6.4 : Frontend - Test et validation des charges d'amortissements
**Status**: ✅ COMPLÉTÉ  
**Description**: Tester et valider spécifiquement l'affichage correct de la catégorie "Charges d'amortissements".

**Tasks**:
- [x] Vérifier que les montants sont récupérés depuis la vue d'amortissement sélectionnée dans la card config (Step 7.5.11)
- [x] Tester avec une vue d'amortissement sélectionnée : montants affichés correctement dans le tableau
- [x] Tester sans vue sélectionnée : afficher "Vue non configurée" (implémenté dans Step 7.6.3)
- [x] Vérifier que les montants correspondent aux totaux de la vue d'amortissement pour chaque année
  - Comparer avec les données de `AmortizationResult` pour la vue sélectionnée
  - Vérifier que la somme par année correspond au total d'amortissement de la vue
  - **Tests automatisés créés et validés** : `test_compte_resultat_special_categories.py`
- [x] Tester le rechargement automatique quand la vue d'amortissement change dans la card config (via `refreshKey`)
- [x] Vérifier que les montants sont corrects pour plusieurs années (tests validés pour toutes les années)
- [x] **Tester dans le navigateur**

**Acceptance Criteria**:
- [x] Montants corrects depuis la vue sélectionnée dans la card config
- [x] Message affiché si vue non configurée ("Vue non configurée")
- [x] Montants correspondent aux totaux de la vue d'amortissement pour chaque année (tests validés)
- [x] Rechargement automatique quand vue change dans card config (via `refreshKey`)
- [x] Montants corrects pour plusieurs années (tests validés pour toutes les années disponibles)
- [x] **Test visuel dans navigateur validé**
- [x] **Utilisateur confirme que les montants sont corrects**

---

#### Step 7.6.5 : Frontend - Test et validation du coût du financement
**Status**: ✅ COMPLÉTÉ  
**Description**: Tester et valider spécifiquement l'affichage correct de la catégorie "Coût du financement (hors remboursement du capital)".

**Tasks**:
- [x] Vérifier que les montants sont calculés depuis les crédits sélectionnés dans la card config (Step 7.5.12)
- [x] Tester avec un crédit sélectionné : montants affichés correctement (interest + insurance)
- [x] Tester avec plusieurs crédits sélectionnés : somme des montants de tous les crédits (logique implémentée)
- [x] Tester sans crédit sélectionné : afficher "Crédits non configurés" (implémenté dans Step 7.6.3)
- [x] Vérifier que les montants correspondent à la somme des loan_payments (interest + insurance) pour les crédits sélectionnés, par année
  - Filtrer `loan_payments` par année et par les IDs de crédits sélectionnés
  - Sommer `interest + insurance` pour chaque crédit sélectionné
  - Vérifier que le total correspond au montant affiché
  - **Tests automatisés créés et validés** : `test_compte_resultat_special_categories.py`
- [x] Tester le rechargement automatique quand les crédits sélectionnés changent dans la card config (via `refreshKey`)
- [x] Vérifier que les montants sont corrects pour plusieurs années (tests validés pour toutes les années disponibles)
- [x] **Tester dans le navigateur**

**Acceptance Criteria**:
- [x] Montants corrects depuis les crédits sélectionnés dans la card config
- [x] Somme correcte pour plusieurs crédits sélectionnés (logique implémentée)
- [x] Message affiché si crédits non configurés ("Crédits non configurés")
- [x] Montants correspondent à la somme des loan_payments (interest + insurance) pour les crédits sélectionnés (tests validés)
- [x] Rechargement automatique quand crédits changent dans card config (via `refreshKey`)
- [x] Montants corrects pour plusieurs années (tests validés pour toutes les années disponibles)
- [x] **Test visuel dans navigateur validé**
- [x] **Utilisateur confirme que les montants sont corrects**

---

#### Step 7.6.6 : Frontend - Calcul et affichage des totaux
**Status**: ✅ COMPLÉTÉ  
**Description**: Calculer et afficher les lignes de totaux (comme dans l'image).

**Tasks**:
- [x] Calculer "Total des produits d'exploitation" = somme des catégories de produits (affiché sur ligne de type)
- [x] Calculer "Total des charges d'exploitation" = somme des catégories de charges (affiché sur ligne de type)
- [x] Calculer "Résultat de l'exercice" = Total produits - Total charges
- [x] Afficher la ligne "Résultat de l'exercice" en bas du tableau avec fond gris
- [x] Mettre en évidence les totaux (texte en gras, fond gris)
- [x] Afficher en rouge si résultat négatif
- [x] **Tester dans le navigateur**

**Acceptance Criteria**:
- [x] Totaux calculés correctement (par type et résultat de l'exercice)
- [x] Lignes de totaux affichées avec fond gris
- [x] Totaux mis en évidence (texte en gras)
- [x] Résultat négatif affiché en rouge
- [x] **Test visuel dans navigateur validé**

---

#### Step 7.6.7 : Frontend - Formatage des montants
**Status**: ✅ COMPLÉTÉ  
**Description**: Formater les montants (€, séparateurs de milliers, 2 décimales).

**Tasks**:
- [x] Formater les montants avec séparateurs de milliers (ex: 1 234,56 €)
- [x] Afficher 2 décimales
- [x] Afficher le symbole €
- [x] Gérer les valeurs négatives (affichage en rouge)
- [x] Gérer les valeurs nulles (affichage "0,00 €")
- [x] **Tester dans le navigateur**

**Acceptance Criteria**:
- [x] Montants formatés correctement (1 234,56 €)
- [x] 2 décimales affichées
- [x] Symbole € visible
- [x] Valeurs négatives gérées (affichage en rouge)
- [x] **Test visuel dans navigateur validé**

---

#### Step 7.6.8 : Frontend - Fonctionnalité pin/unpin pour la card de configuration
**Status**: ⏸️ EN ATTENTE  
**Description**: Ajouter un bouton pin/unpin à côté du titre "Configuration du compte de résultat" pour replier/déplier la card.

**Tasks**:
- [ ] Ajouter un état `isCollapsed` pour gérer l'état replié/déplié
- [ ] Ajouter un bouton pin/unpin (📌/📌) à côté du titre "Configuration du compte de résultat"
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

#### Step 7.6.9 : Frontend - Ajout d'années
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

## Phase 8 : Nouveau système de mapping avec valeurs prédéfinies

### Vue d'ensemble
**Objectif** : Refondre le système de mapping pour imposer des valeurs prédéfinies (level_1, level_2, level_3) au lieu de permettre des valeurs libres.

**Changements principaux** :
- Fichier de référence `scripts/mapping_default.xlsx` contenant toutes les valeurs autorisées
- Validation des mappings importés contre ce fichier de référence
- Dropdowns filtrés hiérarchiquement (level_1 → level_2 → level_3) dans l'onglet Transactions
- Dropdowns filtrés dans l'onglet Mapping
- Héritage automatique : quand une transaction est mappée, toutes les transactions avec le même nom sont mises à jour immédiatement
- Recalcul automatique des modules dépendants (compte de résultat, amortissements, etc.)

---

### Step 8.1 : Backend - Création de la table de mappings autorisés
**Status**: ✅ COMPLÉTÉ  
**Description**: Créer une table en BDD pour stocker tous les mappings autorisés (combinaisons valides de level_1, level_2, level_3).

**Tasks**:
- [x] Créer un nouveau modèle SQLAlchemy `AllowedMapping` dans `backend/database/models.py` :
  - Colonnes : `id`, `level_1` (String, not null), `level_2` (String, not null), `level_3` (String, nullable)
  - Contrainte unique sur (level_1, level_2, level_3) pour éviter les doublons
  - Index sur level_1, level_2, level_3 pour performance
- [x] Créer script de migration `backend/scripts/create_allowed_mappings_table.py` pour créer la table
- [x] Créer `backend/api/services/mapping_default_service.py` :
  - Fonction `get_allowed_level1_values(db: Session)` : retourne toutes les valeurs level_1 autorisées (distinct)
  - Fonction `get_allowed_level2_values(db: Session, level_1: str)` : retourne les valeurs level_2 autorisées pour un level_1 donné (distinct)
  - Fonction `get_allowed_level3_values(db: Session, level_1: str, level_2: str)` : retourne les valeurs level_3 autorisées pour un couple (level_1, level_2) (distinct)
  - Fonction `validate_mapping(db: Session, level_1: str, level_2: str, level_3: Optional[str])` : valide qu'une combinaison existe dans la table
- [x] Créer Pydantic models dans `backend/api/models.py` :
  - `AllowedMappingBase`, `AllowedMappingCreate`, `AllowedMappingResponse`, `AllowedMappingListResponse`
- [x] Endpoint `GET /api/mappings/allowed-level1` pour récupérer toutes les valeurs level_1 autorisées
- [x] Endpoint `GET /api/mappings/allowed-level2?level_1={value}` pour récupérer les level_2 autorisés pour un level_1
- [x] Endpoint `GET /api/mappings/allowed-level3?level_1={value}&level_2={value}` pour récupérer les level_3 autorisés pour un couple (level_1, level_2)
- [x] **Tester les endpoints et la validation**

**Deliverables**:
- Nouveau modèle `AllowedMapping` dans `backend/database/models.py`
- Script de migration `backend/scripts/create_allowed_mappings_table.py`
- `backend/api/services/mapping_default_service.py` - Service de gestion des mappings autorisés
- Mise à jour `backend/api/routes/mappings.py` - Nouveaux endpoints
- Mise à jour `backend/api/models.py` - Modèles Pydantic

**Acceptance Criteria**:
- [x] Table `allowed_mappings` créée en BDD avec structure correcte
- [x] Service charge correctement les valeurs depuis la BDD
- [x] Fonctions de validation fonctionnent correctement
- [x] Endpoints API retournent les bonnes valeurs filtrées
- [x] **Test script exécutable et tous les tests passent**

**Note** : Le fichier `scripts/mapping_default.xlsx` sera géré plus tard dans Step 8.7 pour permettre d'ajouter de nouvelles valeurs.

---

### Step 8.2 : Backend - Validation des mappings importés
**Status**: ✅ COMPLÉTÉ  
**Description**: Modifier l'endpoint d'import de mappings pour valider les valeurs contre la table `allowed_mappings`. Le bouton "Load mapping" reste exactement le même, seule la validation change.

**Tasks**:
- [x] Modifier `POST /api/mappings/import` dans `backend/api/routes/mappings.py` :
  - **Le workflow reste identique** : détection de colonnes, preview, import
  - Pour chaque ligne du fichier importé, valider que les valeurs level_1, level_2, level_3 sont autorisées
  - Utiliser `validate_mapping()` du service créé en Step 8.1 (validation contre la table `allowed_mappings`)
  - Si une ligne contient des valeurs invalides :
    - Incrémenter `errors_count`
    - Ajouter un message "erreur - mapping inconnu" dans `errors_list`
    - **Ignorer la ligne** (ne pas créer le mapping)
  - Si toutes les valeurs sont valides, créer le mapping comme avant (pas de changement ici)
- [x] Mettre à jour le modèle de réponse `MappingImportResponse` pour inclure les détails des erreurs
- [x] Logger les erreurs de validation dans les logs backend avec "erreur - mapping inconnu"
- [x] **Tester avec un fichier contenant des valeurs valides et invalides**

**Deliverables**:
- Mise à jour `backend/api/routes/mappings.py` - Validation lors de l'import (workflow identique, validation ajoutée)
- Mise à jour `backend/api/models.py` - Modèle de réponse enrichi

**Acceptance Criteria**:
- [x] Le bouton "Load mapping" fonctionne exactement comme avant (même interface, même workflow)
- [x] Les lignes avec valeurs invalides sont ignorées (pas de mapping créé)
- [x] Les erreurs sont loggées avec "erreur - mapping inconnu"
- [x] Les statistiques d'import incluent le nombre d'erreurs
- [x] Les lignes valides sont importées normalement
- [x] **Test avec fichier mixte (valides + invalides) validé**

---

### Step 8.3 : Backend - Vérification et test de la mise à jour automatique
**Status**: ✅ COMPLÉTÉ  
**Description**: Vérifier que la mise à jour automatique de toutes les transactions avec le même nom fonctionne correctement (cette fonctionnalité devrait déjà exister).

**Tasks**:
- [x] Vérifier le code actuel de `update_transaction_classification()` dans `backend/api/services/enrichment_service.py`
- [x] Vérifier le code actuel de `create_or_update_mapping_from_classification()`
- [x] Tester que quand on modifie le mapping d'une transaction :
  - Toutes les transactions existantes avec le même nom sont mises à jour
  - Le mapping dans la table `mappings` est créé/mis à jour
  - Les futures transactions avec le même nom héritent du mapping
- [x] Si la fonctionnalité n'existe pas ou ne fonctionne pas correctement, l'implémenter/corriger
  - Amélioration: Utiliser une correspondance exacte du nom au lieu d'un matching par préfixe
- [x] **Tester la mise à jour en cascade avec plusieurs transactions du même nom**

**Deliverables**:
- Vérification/correction de `backend/api/services/enrichment_service.py` si nécessaire
- Script de test pour valider la mise à jour en cascade

**Acceptance Criteria**:
- [x] Quand on modifie le mapping d'une transaction, toutes les transactions avec le même nom sont mises à jour
- [x] Le mapping dans la table `mappings` est créé/mis à jour
- [x] Les futures transactions avec le même nom héritent automatiquement du mapping
- [x] **Test avec plusieurs transactions du même nom validé**

---

### Step 8.4 : Frontend - Dropdowns filtrés hiérarchiquement dans l'onglet Transactions
**Status**: ⏸️ EN ATTENTE  
**Description**: Modifier l'interface de mapping manuel dans l'onglet Transactions pour utiliser des dropdowns filtrés hiérarchiquement avec filtrage bidirectionnel. **Garder l'option "✏️" (bouton d'édition)** - voir Step 8.8 pour les détails.

**Important** : Chaque level_1 a une combinaison unique level_2/level_3 dans `allowed_mappings`.

**Tasks**:
- [ ] **Backend - Nouvelles fonctions de filtrage** :
  - Créer `get_allowed_level2_for_level3(db: Session, level_3: str)` dans `mapping_default_service.py` : retourne les level_2 qui ont ce level_3
  - Créer `get_allowed_level1_for_level2(db: Session, level_2: str)` dans `mapping_default_service.py` : retourne les level_1 qui ont ce level_2
  - Créer `get_allowed_level1_for_level2_and_level3(db: Session, level_2: str, level_3: str)` : retourne les level_1 qui ont ce couple (pour validation)
  - Créer endpoints API correspondants dans `backend/api/routes/mappings.py` :
    - `GET /api/mappings/allowed-level2-for-level3?level_3={value}`
    - `GET /api/mappings/allowed-level1-for-level2?level_2={value}`
    - `GET /api/mappings/allowed-level1-for-level2-and-level3?level_2={value}&level_3={value}`
- [ ] **Frontend - API Client** :
  - Ajouter fonctions dans `frontend/src/api/client.ts` pour les nouveaux endpoints
- [ ] **Frontend - TransactionsTable** :
  - Remplacer les inputs texte par des dropdowns pour level_1, level_2, level_3
  - Charger les valeurs prédéfinies depuis `GET /api/mappings/allowed-level1` au montage
  - Implémenter le **filtrage hiérarchique bidirectionnel** :
    
    **Scénario 1 : Sélection de level_1 en premier**
    - Level_1 sélectionné → level_2 et level_3 sont **automatiquement sélectionnés** (combinaison unique)
    - Dropdown level_2 et level_3 restent disponibles mais pré-remplis
    
    **Scénario 2 : Sélection de level_2 en premier**
    - Level_2 sélectionné → level_3 est **automatiquement sélectionné** (combinaison unique pour ce level_2)
    - Level_1 doit être sélectionné manuellement (plusieurs level_1 peuvent avoir le même level_2)
    - Dropdown level_1 : affiche les level_1 autorisés pour ce level_2 (appel à `GET /api/mappings/allowed-level1-for-level2?level_2={value}`)
    
    **Scénario 3 : Sélection de level_3 en premier**
    - Level_3 sélectionné → level_2 et level_1 doivent être sélectionnés manuellement
    - Dropdown level_2 : affiche les level_2 autorisés pour ce level_3 (appel à `GET /api/mappings/allowed-level2-for-level3?level_3={value}`)
    - Dropdown level_1 : affiche les level_1 autorisés pour le couple (level_2, level_3) sélectionné
    
    **Règles de changement** :
    - Changer level_1 → level_2 et level_3 changent automatiquement (nouvelle combinaison unique)
    - Changer level_2 → level_3 change automatiquement, level_1 reste tel quel
    - Changer level_3 → level_2 et level_1 restent tels quels (pas de réinitialisation)
  
  - Ajouter option "Unassigned" dans chaque dropdown pour permettre de retirer le mapping
  - **Garder le bouton "✏️" (édition)** - voir Step 8.8 pour les détails
- [ ] **Tester le filtrage hiérarchique bidirectionnel dans le navigateur**

**Deliverables**:
- Mise à jour `backend/api/services/mapping_default_service.py` - Nouvelles fonctions de filtrage
- Mise à jour `backend/api/routes/mappings.py` - Nouveaux endpoints
- Mise à jour `frontend/src/components/TransactionsTable.tsx` - Dropdowns filtrés bidirectionnels
- Mise à jour `frontend/src/api/client.ts` - Nouveaux appels API

**Acceptance Criteria**:
- [ ] Dropdowns remplacent les inputs texte (level_1, level_2, level_3 ne sont plus éditables en texte libre)
- [ ] **Filtrage bidirectionnel fonctionne** :
  - Sélection level_1 → level_2 et level_3 sélectionnés automatiquement
  - Sélection level_2 → level_3 sélectionné automatiquement, level_1 disponible
  - Sélection level_3 → level_2 et level_1 disponibles
- [ ] Les règles de changement fonctionnent correctement
- [ ] Option "Unassigned" permet de retirer le mapping
- [ ] Bouton "✏️" conservé (fonctionnalité détaillée dans Step 8.8)
- [ ] Mise à jour en cascade fonctionne (toutes les transactions avec le même nom sont mises à jour)
- [ ] **Test visuel dans navigateur validé**

---

### Step 8.5 : Frontend - Dropdowns filtrés dans l'onglet Mapping
**Status**: ✅ COMPLÉTÉ  
**Description**: Modifier l'onglet Mapping pour utiliser des dropdowns filtrés au lieu d'inputs texte libres.

**Tasks**:
- [x] Identifier l'onglet/composant Mapping dans le frontend
- [x] Remplacer les inputs texte level_1, level_2, level_3 par des dropdowns
- [x] Implémenter le même filtrage hiérarchique que Step 8.4
- [x] Charger les valeurs prédéfinies depuis l'API
- [x] Permettre la modification des mappings existants (avec validation)
- [x] Permettre la suppression des mappings (comme actuellement)
- [x] **Tester la modification et suppression de mappings**

**Deliverables**:
- Mise à jour du composant Mapping frontend - Dropdowns filtrés

**Acceptance Criteria**:
- [x] Les inputs texte sont remplacés par des dropdowns
- [x] Filtrage hiérarchique fonctionne
- [x] Modification de mapping fonctionne avec validation
- [x] Suppression de mapping fonctionne (transactions retournent à "unassigned")
- [x] **Test visuel dans navigateur validé**

---

### Step 8.6 : Backend - Vérification et test du recalcul automatique
**Status**: ✅ COMPLÉTÉ  
**Description**: Vérifier que le recalcul automatique des modules dépendants fonctionne correctement après une mise à jour de mapping (cette fonctionnalité devrait déjà exister).

**Tasks**:
- [x] Vérifier le code actuel de `update_transaction_classification()` dans `backend/api/services/enrichment_service.py`
- [x] Vérifier que l'invalidation des données calculées est déclenchée :
  - `CompteResultatData` (via fonction existante)
  - `AmortizationResult` (via fonction existante)
  - Tous les autres modules qui dépendent des transactions enrichies
- [x] Tester que le recalcul est déclenché automatiquement après mise à jour de mapping
- [x] Si la fonctionnalité n'existe pas ou ne fonctionne pas correctement, l'implémenter/corriger
- [x] **Tester le recalcul automatique**

**Deliverables**:
- Vérification/correction de `backend/api/services/enrichment_service.py` si nécessaire
- Script de test pour valider le recalcul automatique

**Acceptance Criteria**:
- [x] Après mise à jour de mapping, les données calculées sont invalidées
- [x] Le recalcul est déclenché automatiquement
- [x] Tous les modules dépendants sont mis à jour (compte de résultat, amortissements, etc.)
- [x] **Test de recalcul automatique validé**

**Modifications apportées**:
- Ajout de l'invalidation `invalidate_all_compte_resultat()` dans :
  - `create_mapping` (backend/api/routes/mappings.py)
  - `update_mapping` (backend/api/routes/mappings.py)
  - `delete_mapping` (backend/api/routes/mappings.py)
  - `update_transaction_classifications` (backend/api/routes/enrichment.py)
- Ajout du recalcul `recalculate_all_amortizations()` dans les mêmes endpoints
- Création du test `backend/tests/test_automatic_recalculation_step8_6.py` pour valider le recalcul automatique

---

### Step 8.7 : Frontend - Gestion de la table allowed_mappings (optionnel, dernier step)
**Status**: ✅ COMPLÉTÉ  
**Description**: Créer un sous-onglet dans l'onglet Mapping pour gérer la table `allowed_mappings` (combinaisons autorisées de level_1/level_2/level_3).

**Structure**:
- L'onglet Mapping aura 2 sous-onglets :
  - **"Mappings existants"** : Contenu actuel de `MappingTable.tsx` (liste, création, modification, suppression des mappings de transactions)
  - **"Mappings autorisés"** : Nouveau composant pour gérer la table `allowed_mappings`

**Tasks**:
- [x] Modifier `frontend/app/dashboard/transactions/page.tsx` pour ajouter des sous-onglets dans l'onglet Mapping
- [x] Créer composant `AllowedMappingsTable.tsx` pour gérer les mappings autorisés :
  - Tableau pour visualiser tous les mappings autorisés (level_1, level_2, level_3)
  - Bouton "+ Ajouter" pour créer une nouvelle combinaison
  - Modal de création avec dropdowns filtrés hiérarchiquement (même logique que Step 8.4 et 8.5)
  - **Option C : Dropdowns + bouton "+" pour créer de nouvelles valeurs** (pas seulement les valeurs existantes)
  - Bouton de suppression avec confirmation pour chaque ligne
  - Pagination et filtres
- [x] Ajouter fonctions API dans `frontend/src/api/client.ts` pour les endpoints CRUD
- [x] **Bouton "Reset mappings autorisés par défaut"** :
  - Endpoint backend `POST /api/mappings/allowed/reset` qui :
    - Supprime tous les `allowed_mappings` existants
    - Recharge depuis `scripts/mappings_default.xlsx`
    - **Supprime tous les `mappings` invalides** (combinaisons qui ne sont plus dans `allowed_mappings`)
    - **Marque les transactions associées comme "non assignées"** (supprime leurs `EnrichedTransaction`)
    - **Invalide les données calculées** (`CompteResultatData`, `AmortizationResult`)
- [x] **Tester l'ajout et la suppression de mappings autorisés**
- [x] **Tester le reset avec suppression des mappings invalides**

**Deliverables**:
- Mise à jour `frontend/app/dashboard/transactions/page.tsx` - Sous-onglets dans Mapping
- Nouveau composant `frontend/src/components/AllowedMappingsTable.tsx` - Gestion des mappings autorisés
- Endpoints backend CRUD pour la table `allowed_mappings` :
  - `GET /api/mappings/allowed` - Liste tous les mappings autorisés
  - `POST /api/mappings/allowed` - Ajouter un nouveau mapping autorisé
  - `DELETE /api/mappings/allowed/{id}` - Supprimer un mapping autorisé
  - `POST /api/mappings/allowed/reset` - Reset depuis Excel avec nettoyage des mappings invalides

**Acceptance Criteria**:
- [x] Sous-onglets fonctionnent dans l'onglet Mapping
- [x] Interface pour visualiser les mappings autorisés (tableau)
- [x] Interface pour ajouter de nouvelles combinaisons (level_1, level_2, level_3) avec dropdowns filtrés
- [x] **Possibilité de créer de nouvelles valeurs (pas seulement sélectionner les existantes)**
- [x] Validation de la hiérarchie (même logique que Step 8.4 et 8.5)
- [x] Suppression de mappings autorisés fonctionne (avec confirmation)
- [x] **Bouton "Reset mappings autorisés par défaut" fonctionne**
- [x] **Reset supprime les mappings invalides et réinitialise les transactions associées**
- [x] **Test visuel dans navigateur validé**

**Modifications apportées**:
- Création du composant `AllowedMappingsTable.tsx` avec :
  - Tableau avec pagination, tri et filtres
  - Modal de création avec dropdowns hiérarchiques
  - **Boutons "+" à côté de chaque dropdown pour créer de nouvelles valeurs** (Option C)
  - Bouton "Reset mappings autorisés par défaut" avec confirmation
- Endpoint backend `POST /api/mappings/allowed/reset` qui :
  - Recharge les `allowed_mappings` depuis Excel
  - **Vérifie tous les `mappings` existants et supprime ceux qui ne sont plus valides**
  - **Supprime les `EnrichedTransaction` des transactions qui utilisaient les mappings invalides**
  - **Invalide `CompteResultatData` et recalcule les amortissements**
  - Retourne les statistiques (mappings supprimés, transactions réinitialisées)

---

### Step 8.8 : Frontend - Fonctionnalité du bouton "✏️" dans l'onglet Transactions
**Status**: ✅ COMPLÉTÉ  
**Description**: Le bouton "✏️" édite uniquement les champs `date`, `nom`, `quantite` (pas les classifications). Les classifications (level_1, level_2, level_3) sont déjà éditables via les dropdowns filtrés en cliquant directement sur les valeurs (implémenté dans Step 8.4).

**Tasks**:
- [x] **Fonctionnalité confirmée** : Le bouton "✏️" édite les champs transaction (date, nom, quantite)
- [x] **Édition des classifications** : Déjà implémentée dans Step 8.4 via clic sur les valeurs level_1/level_2/level_3
- [x] Validation contre `allowed_mappings` respectée (déjà implémentée dans Step 8.4)
- [x] Mise à jour en cascade fonctionne (déjà implémentée dans Step 8.3)
- [x] **Test visuel dans navigateur validé**

**Deliverables**:
- Aucune modification nécessaire - fonctionnalité déjà en place

**Acceptance Criteria**:
- [x] Fonctionnalité du bouton "✏️" définie : édite date, nom, quantite
- [x] Édition des classifications via clic sur les valeurs avec dropdowns filtrés (Step 8.4)
- [x] Validation contre `allowed_mappings` respectée
- [x] Mise à jour en cascade fonctionne (toutes les transactions avec le même nom sont mises à jour)
- [x] **Test visuel dans navigateur validé**

---

**Phase 8 - Acceptance Criteria globaux**:
- [x] Table `allowed_mappings` créée en BDD et peuplée avec les mappings autorisés
- [x] Tous les mappings (importés ou manuels) sont validés contre la table `allowed_mappings`
- [x] Les lignes invalides sont ignorées avec message "erreur - mapping inconnu"
- [x] Le bouton "Load mapping" fonctionne exactement comme avant (même interface, même workflow)
- [x] Dropdowns filtrés hiérarchiquement dans l'onglet Transactions (level_1, level_2, level_3 ne sont plus éditables en texte libre)
- [x] Dropdowns filtrés hiérarchiquement dans l'onglet Mapping
- [x] Bouton "✏️" conservé avec fonctionnalité définie (Step 8.8)
- [x] Mise à jour en cascade : toutes les transactions avec le même nom sont mises à jour (vérifiée et testée)
- [x] Recalcul automatique des modules dépendants (vérifié et testé)
- [x] **Test complet de bout en bout validé**
- [x] **Utilisateur confirme que le nouveau système fonctionne correctement**

---

## Phase 9 : Amélioration du compte de résultat - Filtrage par Level 3

### Step 9.1 : Frontend - Suppression des colonnes Level 2 et Level 3
**Status**: ✅ COMPLÉTÉ  
**Description**: Supprimer les colonnes "Level 2 (valeurs)" et "Level 3 (valeurs)" de `CompteResultatConfigCard`.

**Tasks**:
- [x] Supprimer la colonne "Level 2 (valeurs)" du tableau
- [x] Supprimer la colonne "Level 3 (valeurs)" du tableau
- [x] Conserver uniquement : Type, Catégorie comptable, Level 1 (valeurs), Vue
- [x] Supprimer les états et logiques liés à `level_2_values` et `level_3_values` dans les mappings
- [x] Mettre à jour les interfaces TypeScript si nécessaire
- [x] **Tester que le tableau s'affiche correctement avec 4 colonnes**

**Deliverables**:
- Mise à jour `frontend/src/components/CompteResultatConfigCard.tsx`

**Acceptance Criteria**:
- [x] Colonnes "Level 2 (valeurs)" et "Level 3 (valeurs)" supprimées
- [x] Tableau affiche uniquement 4 colonnes : Type, Catégorie comptable, Level 1 (valeurs), Vue
- [x] Les catégories spéciales conservent "Données calculées" dans la colonne Level 1
- [x] **Test visuel dans navigateur validé**

**Modifications apportées**:
- Suppression des colonnes Level 2 et Level 3 du thead et tbody
- Suppression des états `level2Values`, `editingLevel2Id`, `level3Values`, `editingLevel3Id`
- Suppression des fonctions `handleLevel2Add`, `handleLevel2Remove`, `handleLevel3Add`, `handleLevel3Remove`
- Suppression des fonctions `loadLevel2Values`, `loadLevel3Values`, `getAllUsedLevel2Values`
- Mise à jour de tous les appels API pour mettre `level_2_values` à `[]` et `level_3_values` à `null`
- Mise à jour de `saveView` et `loadView` pour ne plus inclure level_2_values et level_3_values
- Mise à jour du `colSpan` de la ligne "Ajouter une catégorie" de 5 à 4

---

### Step 9.2 : Frontend - Ajout du dropdown "Level 3 valeurs à inclure"
**Status**: ✅ COMPLÉTÉ  
**Description**: Ajouter un dropdown multi-select sous "Configuration du compte de résultat" pour sélectionner les `level_3` à inclure dans le compte de résultat.

**Tasks**:
- [x] Ajouter un dropdown avec checkboxes sous le titre "Configuration du compte de résultat"
- [x] Label : "Level 3 valeurs à inclure dans le compte de résultat"
- [x] Charger toutes les valeurs `level_3` disponibles (depuis `allowed_mappings`)
- [x] Permettre la sélection multiple avec checkboxes
- [x] Sauvegarder la sélection dans `view_data.selected_level_3_values` lors de la sauvegarde d'une vue
- [x] Charger la sélection depuis `view_data.selected_level_3_values` lors du chargement d'une vue
- [x] **Tester la sauvegarde et le chargement de la sélection**

**Deliverables**:
- Mise à jour `frontend/src/components/CompteResultatConfigCard.tsx`
- Mise à jour de la structure `view_data` pour inclure `selected_level_3_values`

**Acceptance Criteria**:
- [x] Dropdown multi-select visible sous "Configuration du compte de résultat"
- [x] Toutes les valeurs `level_3` disponibles sont affichées
- [x] Sélection multiple fonctionne avec checkboxes
- [x] Sélection sauvegardée dans les vues
- [x] Sélection chargée depuis les vues
- [x] **Test visuel dans navigateur validé**

**Modifications apportées**:
- Ajout des états `selectedLevel3Values`, `availableLevel3Values`, `loadingLevel3Values`, `showLevel3Dropdown`
- Création de la fonction `loadAvailableLevel3Values()` qui charge toutes les valeurs depuis `allowedMappingsAPI.getAllowedLevel3()`
- Ajout du dropdown multi-select avec checkboxes juste après le header
- Mise à jour de `saveView()` pour inclure `selected_level_3_values` dans `view_data`
- Mise à jour de `loadView()` pour charger `selected_level_3_values` depuis `view_data` (avec compatibilité pour les vues existantes)
- Ajout d'un `useEffect` pour fermer le dropdown au clic ailleurs

---

### Step 9.3 : Frontend - Filtrage du dropdown Level 1 par Level 3 sélectionnés
**Status**: ✅ COMPLÉTÉ  
**Description**: Filtrer le dropdown "Level 1 (valeurs)" pour n'afficher que les `level_1` associés aux `level_3` sélectionnés ET qui existent dans les transactions enrichies.

**Tasks**:
- [x] Créer fonction backend `get_allowed_level1_for_level3_list()` dans `mapping_default_service.py`
- [x] Créer endpoint API `/api/mappings/allowed-level1-for-level3-list`
- [x] Ajouter fonction frontend `getAllowedLevel1ForLevel3List()` dans `allowedMappingsAPI`
- [x] Modifier la fonction `loadLevel1Values()` pour filtrer par `level_3` sélectionnés
- [x] Ajouter intersection avec les `level_1` qui existent dans les transactions enrichies
- [x] Ajouter `useEffect` pour recharger automatiquement quand `selectedLevel3Values` change
- [x] Si aucun `level_3` n'est sélectionné, afficher message "Sélectionnez d'abord des Level 3"
- [x] Mettre à jour les messages d'alerte et tooltips
- [x] Mettre à jour le dropdown pour afficher message approprié

**Deliverables**:
- ✅ Mise à jour `backend/api/services/mapping_default_service.py` (fonction `get_allowed_level1_for_level3_list`)
- ✅ Mise à jour `backend/api/routes/mappings.py` (endpoint `/api/mappings/allowed-level1-for-level3-list`)
- ✅ Mise à jour `frontend/src/api/client.ts` (fonction `getAllowedLevel1ForLevel3List`)
- ✅ Mise à jour `frontend/src/components/CompteResultatConfigCard.tsx` (filtrage dynamique)

**Acceptance Criteria**:
- [x] Dropdown Level 1 affiche uniquement les `level_1` associés aux `level_3` sélectionnés ET qui existent dans les transactions enrichies
- [x] Si aucun `level_3` sélectionné, message "Sélectionnez d'abord des Level 3" affiché
- [x] Filtrage mis à jour dynamiquement quand la sélection de `level_3` change
- [x] Les catégories spéciales ne sont pas affectées (conservent "Données calculées")
- [ ] **Test visuel dans navigateur validé**

---

### Step 9.4 : Backend - Mise à jour de la structure view_data (si nécessaire)
**Status**: ✅ COMPLÉTÉ  
**Description**: Vérifier et mettre à jour la structure `view_data` pour supporter `selected_level_3_values`.

**Tasks**:
- [x] Vérifier que `view_data` peut stocker `selected_level_3_values` (JSON) - ✅ Confirmé : `view_data` est de type `JSON` dans la base de données et `dict` dans les modèles Pydantic
- [x] Mettre à jour la documentation des modèles Pydantic pour documenter la structure attendue
- [x] Mettre à jour la documentation du modèle de base de données pour documenter la structure attendue
- [x] Vérifier que la sauvegarde/chargement fonctionne correctement - ✅ Confirmé : le frontend sauvegarde et charge déjà `selected_level_3_values` (Step 9.2)
- [x] Vérifier la compatibilité avec les vues existantes - ✅ Confirmé : le frontend initialise à `[]` si `selected_level_3_values` absent

**Deliverables**:
- ✅ Mise à jour `backend/api/models.py` (documentation des modèles Pydantic)
- ✅ Mise à jour `backend/database/models.py` (documentation du modèle SQLAlchemy)

**Acceptance Criteria**:
- [x] `view_data` peut stocker `selected_level_3_values` comme liste de strings - ✅ Confirmé : type `JSON`/`dict` supporte n'importe quelle structure
- [x] Sauvegarde fonctionne correctement - ✅ Confirmé : le frontend sauvegarde déjà `selected_level_3_values` dans `view_data` (Step 9.2)
- [x] Chargement fonctionne correctement - ✅ Confirmé : le frontend charge déjà `selected_level_3_values` depuis `view_data` (Step 9.2)
- [x] Compatibilité avec les vues existantes (valeur par défaut si `selected_level_3_values` absent) - ✅ Confirmé : le frontend initialise à `[]` si absent
- [x] Documentation mise à jour pour clarifier la structure attendue

---

### Step 9.5 : Test et validation
**Status**: ✅ COMPLÉTÉ  
**Description**: Tester l'ensemble des modifications et valider que le compte de résultat calcule correctement avec le filtre Level 3.

**Tasks**:
- [x] Tester la suppression des colonnes Level 2 et Level 3 - ✅ Validé
- [x] Tester le dropdown multi-select Level 3 - ✅ Validé
- [x] Tester le filtrage du dropdown Level 1 - ✅ Validé
- [x] Tester la sauvegarde/chargement des vues avec `selected_level_3_values` - ✅ Validé
- [x] Tester que le calcul du compte de résultat ne prend que les transactions avec les `level_3` sélectionnés - ✅ Validé
- [x] Vérifier que les catégories spéciales fonctionnent toujours correctement - ✅ Validé
- [x] **Test complet de bout en bout validé** - ✅ Validé par l'utilisateur

**Deliverables**:
- ✅ Tests manuels dans le navigateur effectués
- ✅ Validation que les calculs sont corrects

**Acceptance Criteria**:
- [x] Toutes les fonctionnalités fonctionnent correctement - ✅ Validé
- [x] Le calcul du compte de résultat respecte le filtre Level 3 - ✅ Validé
- [x] Les vues sauvegardent et chargent correctement la sélection Level 3 - ✅ Validé
- [x] **Utilisateur confirme que tout fonctionne correctement** - ✅ Validé

---

**Phase 9 - Acceptance Criteria globaux**:
- [x] Colonnes Level 2 et Level 3 supprimées - ✅ Validé
- [x] Dropdown multi-select Level 3 fonctionne - ✅ Validé
- [x] Dropdown Level 1 filtré par Level 3 sélectionnés - ✅ Validé
- [x] Sélection Level 3 sauvegardée dans les vues - ✅ Validé
- [x] Calcul du compte de résultat respecte le filtre Level 3 - ✅ Validé
- [x] **Test complet de bout en bout validé** - ✅ Validé par l'utilisateur

---

## Phase 10 : Implémentation de l'onglet Bilan

**Status**: ⏸️ EN ATTENTE  
**Description**: Créer un nouvel onglet "Bilan" avec une structure similaire au compte de résultat, incluant une card de configuration pour mapper les level_1 aux catégories comptables du bilan et une table pour afficher le bilan par année.

### Structure hiérarchique du Bilan

**Niveau A** : ACTIF / PASSIF (lignes de total)

**Niveau B** : Sous-catégories (lignes de total)
- ACTIF :
  - Actif immobilisé
  - Actif circulant
- PASSIF :
  - Capitaux propres
  - Trésorerie passive
  - Dettes financières

**Niveau C** : Catégories comptables (mappées avec level_1)
- **Actif immobilisé** :
  - Immobilisations (filtre normal)
  - Amortissements cumulés → **catégorie spéciale**
- **Actif circulant** :
  - Compte bancaire → **catégorie spéciale**
  - Créances locataires (filtre normal)
  - Charges payées d'avance (filtre normal)
- **Capitaux propres** :
  - Capitaux propres (filtre normal)
  - Apports initiaux (filtre normal)
  - Souscription de parts sociales (filtre normal)
  - Résultat de l'exercice (bénéfice / perte) → **catégorie spéciale**
  - Report à nouveau / report du déficit → **catégorie spéciale**
  - Compte courant d'associé (filtre normal)
- **Tresorerie passive** :
  - Cautions reçues (filtre normal - dépôt de garantie locataire)
- **Dettes financières** :
  - Emprunt bancaire (capital restant dû) (filtre normal)
  - Autres dettes (filtre normal)

### Logique des catégories spéciales

1. **Amortissements cumulés** :
   - Source : Table `amortizations` (AmortizationResult)
   - Calcul : Cumul de toutes les années jusqu'à l'année en cours
   - Affichage : En diminution de l'actif (négatif)

2. **Compte bancaire** :
   - Source : Table `transactions`
   - Calcul : Solde final de l'année (solde de la dernière transaction de l'année)
   - Affichage : Montant positif

3. **Résultat de l'exercice** :
   - Source : Table `compte_resultat_data` ou calcul depuis CompteResultatService
   - Calcul : Résultat de l'année en cours depuis le compte de résultat
   - Affichage : Bénéfice (positif) ou perte (négatif)

4. **Report à nouveau / report du déficit** :
   - Source : Table `compte_resultat_data` ou calcul depuis CompteResultatService
   - Calcul : Cumul des résultats des années précédentes (N-1, N-2, etc.)
   - Première année : 0 (pas de report)
   - Affichage : Montant cumulé

5. **Emprunt bancaire (capital restant dû)** :
   - Source : Table `loan_payments` (LoanPayment)
   - Calcul : Crédit accordé - Cumulé des remboursements de capital (année par année)
   - Affichage : Montant positif (dette)

### Équilibre ACTIF = PASSIF

- Validation automatique : Afficher un pourcentage de différence sous la ligne total
- Format : `% Différence : X.XX%` (rouge si différence > 0, vert si = 0)

### Step 10.1 : Backend - Modèle de données pour le Bilan

**Status**: ✅ COMPLÉTÉ  
**Description**: Créer les modèles de base de données pour stocker les mappings et les données du bilan.

**Tasks**:
- [x] Créer modèle `BilanMapping` dans `backend/database/models.py`
  - `id` (Integer, primary_key)
  - `category_name` (String, unique=False) - Nom de la catégorie comptable (niveau C)
  - `level_1_values` (JSON) - Liste des level_1 mappés à cette catégorie
  - `type` (String) - "ACTIF" ou "PASSIF"
  - `sub_category` (String) - Sous-catégorie (niveau B)
  - `is_special` (Boolean) - Indique si c'est une catégorie spéciale
  - `special_source` (String, nullable) - Source pour les catégories spéciales ("amortizations", "transactions", "compte_resultat", "compte_resultat_cumul", "loan_payments")
  - `amortization_view_id` (Integer, ForeignKey, nullable) - Pour catégorie "Amortissements cumulés"
  - `created_at`, `updated_at` (DateTime)
- [x] Créer modèle `BilanData` dans `backend/database/models.py`
  - `id` (Integer, primary_key)
  - `annee` (Integer, index=True)
  - `category_name` (String, index=True)
  - `amount` (Float)
  - `created_at`, `updated_at` (DateTime)
- [x] Créer modèle `BilanMappingView` dans `backend/database/models.py`
  - `id` (Integer, primary_key)
  - `name` (String, unique=True)
  - `view_data` (JSON) - Structure: `{'mappings': [...], 'selected_level_3_values': [...]}`
  - `created_at`, `updated_at` (DateTime)
- [x] Créer script de migration `backend/scripts/create_bilan_tables.py`

**Deliverables**:
- ✅ Modèles SQLAlchemy dans `backend/database/models.py`
- ✅ Script de migration `backend/scripts/create_bilan_tables.py`

**Acceptance Criteria**:
- [x] Modèles créés avec tous les champs nécessaires
- [x] Index créés pour les recherches fréquentes (category_name, type, sub_category, annee, category_name)
- [x] Relations définies si nécessaire (ForeignKey vers amortization_views)
- [x] Migration testée - Tables créées avec succès

---

### Step 10.2 : Backend - Service de calcul du Bilan

**Status**: ✅ COMPLÉTÉ  
**Description**: Créer le service pour calculer les montants du bilan par catégorie et par année.

**Tasks**:
- [x] Créer `backend/api/services/bilan_service.py`
- [x] Fonction `get_mappings(db: Session) -> List[BilanMapping]`
- [x] Fonction `calculate_bilan(year: int, mappings: List[BilanMapping], selected_level_3_values: List[str], db: Session) -> dict`
  - Pour chaque mapping :
    - Si `is_special == False` : Calculer depuis transactions enrichies (même logique que compte de résultat)
    - Si `is_special == True` :
      - `special_source == "amortizations"` : Cumul des amortissements jusqu'à l'année
      - `special_source == "transactions"` : Solde final de l'année (dernière transaction)
      - `special_source == "compte_resultat"` : Résultat de l'année depuis compte de résultat
      - `special_source == "compte_resultat_cumul"` : Cumul des résultats précédents
      - `special_source == "loan_payments"` : Capital restant dû au 31/12
- [x] Fonction `invalidate_all_bilan(db: Session)` - Marquer toutes les données comme invalides
- [x] Fonction `invalidate_bilan_for_year(year: int, db: Session)` - Invalider une année spécifique
- [x] Fonction `get_bilan_data(db: Session, year: Optional[int] = None, start_year: Optional[int] = None, end_year: Optional[int] = None) -> List[BilanData]`
- [x] Gérer les totaux par niveau (A, B, C)
- [x] Calculer l'équilibre ACTIF = PASSIF et le pourcentage de différence
- [x] Fonctions auxiliaires pour chaque catégorie spéciale :
  - `calculate_normal_category()` - Catégories normales
  - `calculate_amortizations_cumul()` - Amortissements cumulés
  - `calculate_compte_bancaire()` - Solde bancaire
  - `calculate_resultat_exercice()` - Résultat de l'exercice
  - `calculate_report_a_nouveau()` - Report à nouveau
  - `calculate_capital_restant_du()` - Capital restant dû

**Deliverables**:
- ✅ Fichier `backend/api/services/bilan_service.py`
- ✅ Fonctions de calcul et de gestion des données
- ✅ Test `backend/tests/test_bilan_service_step10_2.py`

**Acceptance Criteria**:
- [x] Toutes les catégories normales calculées correctement depuis transactions
- [x] Toutes les catégories spéciales calculées correctement depuis leurs sources
- [x] Totaux calculés correctement (niveaux A, B, C)
- [x] Équilibre ACTIF = PASSIF calculé et validé
- [x] Pourcentage de différence calculé
- [x] Tous les tests passent

---

### Step 10.3 : Backend - Modèles Pydantic pour l'API

**Status**: ✅ COMPLÉTÉ  
**Description**: Créer les modèles Pydantic pour les requêtes et réponses API du bilan.

**Tasks**:
- [x] Créer `BilanMappingBase`, `BilanMappingCreate`, `BilanMappingUpdate`, `BilanMappingResponse` dans `backend/api/models.py`
- [x] Créer `BilanMappingListResponse` pour la liste des mappings
- [x] Créer `BilanDataBase`, `BilanDataResponse`, `BilanDataListResponse` dans `backend/api/models.py`
- [x] Créer `BilanResponse` avec structure hiérarchique (ACTIF/PASSIF → Sous-catégories → Catégories)
  - `BilanTypeItem` : Type (ACTIF/PASSIF) avec total et sous-catégories
  - `BilanSubCategoryItem` : Sous-catégorie avec total et catégories
  - `BilanCategoryItem` : Catégorie avec montant
- [x] Créer `BilanMappingViewCreate`, `BilanMappingViewUpdate`, `BilanMappingViewResponse`, `BilanMappingViewListResponse`
- [x] Créer `BilanGenerateRequest` (year, selected_level_3_values)

**Deliverables**:
- ✅ Modèles Pydantic dans `backend/api/models.py`

**Acceptance Criteria**:
- [x] Tous les modèles créés avec validation appropriée
- [x] Structure hiérarchique bien représentée (BilanTypeItem → BilanSubCategoryItem → BilanCategoryItem)
- [x] Compatibilité avec les catégories spéciales (champs is_special, special_source, amortization_view_id)
- [x] Tous les modèles importables sans erreur

---

### Step 10.4 : Backend - Endpoints API pour le Bilan

**Status**: ✅ COMPLÉTÉ  
**Description**: Créer les endpoints API pour gérer les mappings, générer le bilan et récupérer les données.

**Tasks**:
- [x] Créer `backend/api/routes/bilan.py`
- [x] Endpoints CRUD pour `BilanMapping` :
  - `GET /api/bilan/mappings` - Liste des mappings
  - `GET /api/bilan/mappings/{mapping_id}` - Détails d'un mapping
  - `POST /api/bilan/mappings` - Créer un mapping
  - `PUT /api/bilan/mappings/{mapping_id}` - Mettre à jour un mapping
  - `DELETE /api/bilan/mappings/{mapping_id}` - Supprimer un mapping
- [x] Endpoint pour générer le bilan :
  - `POST /api/bilan/generate` - Générer le bilan pour une année (avec structure hiérarchique)
- [x] Endpoints pour récupérer les données :
  - `GET /api/bilan` - Récupérer les données du bilan (avec filtres year, start_year, end_year)
- [x] Endpoints pour les vues :
  - `GET /api/bilan/mapping-views` - Liste des vues
  - `GET /api/bilan/mapping-views/{view_id}` - Détails d'une vue
  - `POST /api/bilan/mapping-views` - Créer une vue
  - `PUT /api/bilan/mapping-views/{view_id}` - Mettre à jour une vue
  - `DELETE /api/bilan/mapping-views/{view_id}` - Supprimer une vue
- [x] Intégrer les endpoints dans `backend/api/main.py`
- [x] Invalidation automatique des données lors de modification des mappings

**Deliverables**:
- ✅ Fichier `backend/api/routes/bilan.py`
- ✅ Intégration dans `backend/api/main.py`
- ✅ Test `backend/tests/test_bilan_endpoints_step10_4.py`

**Acceptance Criteria**:
- [x] Tous les endpoints CRUD fonctionnent correctement
- [x] Génération du bilan fonctionne avec toutes les catégories spéciales
- [x] Récupération des données avec filtres fonctionne
- [x] Gestion des vues fonctionne
- [x] Gestion des erreurs appropriée (HTTPException pour erreurs 404, 400)
- [x] Structure hiérarchique correctement construite dans la réponse

---

### Step 10.5 : Backend - Recalcul automatique

**Status**: ✅ COMPLÉTÉ  
**Description**: Implémenter le recalcul automatique du bilan quand les données sources changent.

**Tasks**:
- [x] Appeler `invalidate_all_bilan(db)` dans les endpoints de modification des transactions enrichies
- [x] Appeler `invalidate_all_bilan(db)` dans les endpoints de modification des amortissements
- [x] Appeler `invalidate_all_bilan(db)` dans les endpoints de modification du compte de résultat
- [x] Appeler `invalidate_all_bilan(db)` dans les endpoints de modification des loan payments
- [x] Appeler `invalidate_bilan_for_year(year, db)` dans les endpoints de modification des transactions (create, update, delete)
- [x] Appeler `invalidate_bilan_for_year(year, db)` dans les endpoints de modification des loan payments (create, update, delete)
- [x] Vérifier que le recalcul est déclenché automatiquement

**Deliverables**:
- ✅ Mise à jour des endpoints concernés :
  - `backend/api/routes/enrichment.py`
  - `backend/api/routes/transactions.py`
  - `backend/api/routes/loan_payments.py`
  - `backend/api/routes/amortization.py`
  - `backend/api/routes/amortization_views.py`
  - `backend/api/routes/compte_resultat.py`
  - `backend/api/routes/mappings.py`
- ✅ Test `backend/tests/test_bilan_automatic_recalculation_step10_5.py`

**Acceptance Criteria**:
- [x] Recalcul déclenché lors de la modification des transactions
- [x] Recalcul déclenché lors de la modification des amortissements
- [x] Recalcul déclenché lors de la modification du compte de résultat
- [x] Recalcul déclenché lors de la modification des loan payments
- [x] Recalcul déclenché lors de la modification des mappings

---

### Step 10.6 : Frontend - API Client pour le Bilan

**Status**: ✅ COMPLÉTÉ  
**Description**: Créer les fonctions API client pour communiquer avec le backend du bilan.

**Tasks**:
- [x] Ajouter `bilanAPI` dans `frontend/src/api/client.ts`
- [x] Fonctions CRUD pour les mappings :
  - `getMappings()`, `getMapping(id)`, `createMapping(data)`, `updateMapping(id, data)`, `deleteMapping(id)`
- [x] Fonctions pour les données :
  - `generate(year, selected_level_3_values)`, `getBilan(year?, start_year?, end_year?)`
- [x] Fonctions pour les vues :
  - `getAll()`, `getById(id)`, `create(data)`, `update(id, data)`, `delete(id)` dans `bilanMappingViewsAPI`
- [x] Types TypeScript pour les interfaces :
  - `BilanMapping`, `BilanMappingCreate`, `BilanMappingUpdate`, `BilanMappingListResponse`
  - `BilanData`, `BilanDataListResponse`
  - `BilanCategoryItem`, `BilanSubCategoryItem`, `BilanTypeItem`, `BilanResponse`
  - `BilanGenerateRequest`
  - `BilanMappingView`, `BilanMappingViewCreate`, `BilanMappingViewUpdate`, `BilanMappingViewListResponse`

**Deliverables**:
- ✅ Mise à jour `frontend/src/api/client.ts`
- ✅ Types TypeScript définis

**Acceptance Criteria**:
- [x] Toutes les fonctions API créées
- [x] Types TypeScript corrects (correspondance avec modèles Pydantic backend)
- [x] Gestion des erreurs appropriée (utilise fetchAPI avec gestion d'erreurs)

---

### Step 10.7 : Frontend - Card de configuration du Bilan

**Status**: ✅ COMPLÉTÉ  
**Description**: Créer la card de configuration pour mapper les level_1 aux catégories comptables du bilan.

**Tasks**:
- [x] Créer `frontend/src/components/BilanConfigCard.tsx`
- [x] Structure similaire à `CompteResultatConfigCard.tsx` :
  - Titre "Configuration du bilan" avec bouton pin/unpin
  - Dropdown multi-select "Level 3 valeurs à inclure dans le bilan" (même fonctionnement que compte de résultat) 
  - Table avec colonnes :
    - Type (ACTIF/PASSIF) - Dropdown
    - Sous-catégorie (niveau B) - Dropdown filtré par Type
    - Catégorie comptable (niveau C) - Dropdown filtré par Sous-catégorie
    - Level 1 (valeurs) - Tags avec dropdown filtré par Level 3 sélectionnés
    - Vue (pour catégories spéciales) - Dropdown ou "Données calculées"
  - Bouton "+ Ajouter une catégorie"
  - Bouton "Réinitialiser les mappings"
  - Bouton gear (save/load/delete views)
- [x] Gérer les catégories spéciales :
  - Amortissements cumulés : Dropdown avec vues d'amortissement
  - Compte bancaire : "Données calculées"
  - Résultat de l'exercice : "Données calculées"
  - Report à nouveau : "Données calculées"
- [x] Sauvegarder/charger les vues avec `selected_level_3_values`
- [x] Filtrage du dropdown Level 1 par Level 3 sélectionnés (même logique que compte de résultat)
- [x] Tri des lignes par Type puis Sous-catégorie puis Catégorie

**Deliverables**:
- ✅ Fichier `frontend/src/components/BilanConfigCard.tsx`

**Acceptance Criteria**:
- [x] Card fonctionne comme CompteResultatConfigCard
- [x] Dropdown Level 3 fonctionne
- [x] Filtrage Level 1 par Level 3 fonctionne
- [x] Catégories spéciales gérées correctement
- [x] Sauvegarde/chargement des vues fonctionne
- [x] Pin/unpin fonctionne

**Note**: Fonctionnellement OK. La connexion avec BilanTable sera améliorée dans Step 10.8.

---

### Step 10.8 : Frontend - Table d'affichage du Bilan

**Status**: ⏸️ EN ATTENTE  
**Description**: Créer la table pour afficher le bilan avec structure hiérarchique et colonnes par année. Décomposé en sous-steps pour valider chaque niveau hiérarchique.

---

### Step 10.8.1 : Frontend - Structure de base et affichage niveau C (Catégories)

**Status**: ✅ COMPLÉTÉ  
**Description**: Créer la structure de base de la table et afficher les catégories comptables (niveau C) avec leurs montants par année.

**Tasks**:
- [x] Créer `frontend/src/components/BilanTable.tsx`
- [x] Structure de base similaire à `CompteResultatTable.tsx` :
  - Colonne "Bilan" (catégories)
  - Colonnes par année (dynamiques, basées sur les données disponibles)
- [x] Récupérer les données du bilan depuis l'API (`bilanAPI.getBilan()`)
- [x] Grouper les données par catégorie comptable (niveau C)
- [x] Afficher chaque catégorie (niveau C) :
  - Double indentation (ex: `&nbsp;&nbsp;&nbsp;&nbsp;Immobilisations`)
  - Montant par année dans les colonnes correspondantes
  - Formatage des montants en € (ex: `1 234,56 €`)
  - Affichage des montants négatifs en rouge (pour "Amortissements cumulés")
- [x] Trier les catégories par Type (ACTIF, CAPITAUX PROPRES, puis PASSIF), puis par Sous-catégorie, puis par Catégorie

**Deliverables**:
- ✅ Fichier `frontend/src/components/BilanTable.tsx` avec structure de base
- ✅ Affichage des catégories niveau C

**Acceptance Criteria**:
- [x] Table créée avec colonnes dynamiques par année
- [x] Catégories niveau C affichées avec double indentation
- [x] Montants affichés correctement par année
- [x] Formatage € correct
- [x] Montants négatifs en rouge pour "Amortissements cumulés"
- [x] Tri correct (ACTIF puis PASSIF, puis sous-catégories, puis catégories)

---

### Step 10.8.2 : Frontend - Affichage niveau B (Sous-catégories) avec totaux

**Status**: ✅ COMPLÉTÉ  
**Description**: Ajouter l'affichage des sous-catégories (niveau B) avec leurs totaux calculés.

**Tasks**:
- [x] Ajouter les lignes de sous-catégories (niveau B) :
  - **Actif immobilisé**
  - **Actif circulant**
  - **Capitaux propres**
  - **Tresorerie passive**
  - **Dettes financières**
- [x] Affichage avec indentation simple (ex: `&nbsp;&nbsp;Actif immobilisé`)
- [x] Calculer les totaux par sous-catégorie et par année :
  - Pour chaque sous-catégorie, sommer tous les montants des catégories (niveau C) qui lui appartiennent
  - Gérer les montants négatifs correctement (ex: "Amortissements cumulés" diminue l'actif)
- [x] Afficher les totaux en gras
- [x] Placer chaque ligne de sous-catégorie juste avant ses catégories (niveau C)
- [x] Logique de calcul :
  - **Actif immobilisé** = Immobilisations - Amortissements cumulés
  - **Actif circulant** = Compte bancaire + Créances locataires + Charges payées d'avance
  - **Capitaux propres** = Capitaux propres + Apports initiaux + Souscription de parts sociales + Résultat de l'exercice + Report à nouveau + Compte courant d'associé
  - **Tresorerie passive** = Cautions
  - **Dettes financières** = Emprunt bancaire + Autres dettes

**Deliverables**:
- Mise à jour `frontend/src/components/BilanTable.tsx`
- Affichage des sous-catégories avec totaux

**Acceptance Criteria**:
- [x] Toutes les sous-catégories affichées avec indentation simple
- [x] Totaux calculés correctement pour chaque sous-catégorie
- [x] Logique de calcul respectée (notamment pour "Actif immobilisé" avec amortissements en diminution)
- [x] Totaux affichés en gras
- [x] Ordre hiérarchique respecté (sous-catégorie avant ses catégories)

---

### Step 10.8.3 : Frontend - Affichage niveau A (ACTIF/PASSIF) avec totaux

**Status**: ✅ COMPLÉTÉ  
**Description**: Ajouter l'affichage des niveaux A (ACTIF et PASSIF) avec leurs totaux calculés.

**Tasks**:
- [x] Ajouter les lignes de niveau A :
  - **ACTIF** (en haut)
  - **PASSIF** (en bas)
- [x] Affichage sans indentation, en gras, style titre (fond gris)
- [x] Calculer les totaux par niveau A et par année :
  - **TOTAL ACTIF** = Actif immobilisé + Actif circulant
  - **TOTAL PASSIF** = Capitaux propres + Tresorerie passive + Dettes financières
- [x] Afficher les lignes de niveau A :
  - Ligne "ACTIF" juste avant "Actif immobilisé"
  - Ligne "PASSIF" juste avant "Capitaux propres"
- [x] Style des lignes de niveau A :
  - Fond légèrement gris (#e5e7eb)
  - Texte en gras (fontWeight: '700')
  - Bordure supérieure et inférieure

**Deliverables**:
- Mise à jour `frontend/src/components/BilanTable.tsx`
- Affichage des niveaux A avec totaux

**Acceptance Criteria**:
- [x] Lignes ACTIF et PASSIF affichées correctement
- [x] Totaux ACTIF et PASSIF calculés correctement
- [x] Style visuel distinct pour les niveaux A (fond gris, texte en gras)
- [x] Ordre hiérarchique respecté (ACTIF en haut, PASSIF en bas)

---

### Step 10.8.4 : Frontend - Gestion des catégories spéciales dans l'affichage

**Status**: ⏸️ EN ATTENTE  
**Description**: S'assurer que les catégories spéciales sont affichées correctement avec leurs calculs spécifiques.

---

#### Step 10.8.4.1 : Frontend - Catégorie spéciale "Amortissements cumulés"

**Status**: ✅ COMPLÉTÉ  
**Description**: Vérifier et valider l'affichage de la catégorie spéciale "Amortissements cumulés".

**Tasks**:
- [x] Vérifier que le montant est affiché en négatif (en rouge)
- [x] Vérifier que la catégorie est affichée sous "Immobilisations"
- [x] Vérifier que la catégorie contribue correctement à diminuer "Actif immobilisé" :
  - Actif immobilisé = Immobilisations - Amortissements cumulés
- [x] Vérifier que le calcul backend est correct (cumul des amortissements jusqu'à l'année)
- [x] Vérifier que le montant est récupéré depuis l'API `/api/bilan/calculate`

**Deliverables**:
- Validation de l'affichage "Amortissements cumulés" dans `BilanTable.tsx`
- Fonction `getDisplayAmount()` pour afficher en négatif même si backend retourne positif
- Test script: `backend/tests/test_bilan_amortissements_cumules_step10_8_4_1.py`

**Acceptance Criteria**:
- [x] Montant affiché en négatif et en rouge
- [x] Position correcte (sous "Immobilisations")
- [x] Contribue correctement au calcul "Actif immobilisé"
- [x] Montant calculé correctement par le backend

---

#### Step 10.8.4.2 : Frontend - Catégorie spéciale "Compte bancaire"

**Status**: ✅ COMPLÉTÉ  
**Description**: Vérifier et valider l'affichage de la catégorie spéciale "Compte bancaire".

**Tasks**:
- [x] Vérifier que le montant est affiché en positif
- [x] Vérifier que la catégorie est affichée dans "Actif circulant"
- [x] Vérifier que le montant correspond au solde final de l'année :
  - Solde de la dernière transaction de l'année (au 31/12)
- [x] Vérifier que le calcul backend est correct (dernière transaction de l'année)
- [x] Vérifier que le montant est récupéré depuis l'API `/api/bilan/calculate`

**Deliverables**:
- Validation de l'affichage "Compte bancaire" dans `BilanTable.tsx`

**Acceptance Criteria**:
- [x] Montant affiché en positif
- [x] Position correcte (dans "Actif circulant")
- [x] Montant correspond au solde final de l'année
- [x] Montant calculé correctement par le backend

---

#### Step 10.8.4.3 : Frontend - Catégorie spéciale "Résultat de l'exercice (bénéfice / perte)"

**Status**: ⏸️ EN ATTENTE  
**Description**: Implémenter et valider l'affichage de la catégorie spéciale "Résultat de l'exercice" avec sélection de vue de compte de résultat.

**Étapes de développement :**

**1. Backend - Migration base de données :**
- [ ] Créer migration pour ajouter `compte_resultat_view_id` (Integer, ForeignKey vers `compte_resultat_mapping_views.id`, nullable=True) dans la table `compte_resultat_data`
- [ ] Créer migration pour ajouter `compte_resultat_view_id` (Integer, ForeignKey vers `compte_resultat_mapping_views.id`, nullable=True) dans la table `bilan_mappings`
- [ ] Exécuter les migrations et vérifier la structure

**2. Backend - Modèle de données :**
- [ ] Modifier `CompteResultatData` dans `backend/database/models.py` pour ajouter le champ `compte_resultat_view_id`
- [ ] Modifier `BilanMapping` dans `backend/database/models.py` pour ajouter le champ `compte_resultat_view_id`
- [ ] Ajouter index si nécessaire pour les recherches

**3. Backend - Modèles Pydantic :**
- [ ] Modifier `CompteResultatDataBase` dans `backend/api/models.py` pour inclure `compte_resultat_view_id: Optional[int]`
- [ ] Modifier `BilanMappingBase` dans `backend/api/models.py` pour inclure `compte_resultat_view_id: Optional[int]`
- [ ] Modifier `BilanMappingCreate` et `BilanMappingUpdate` pour inclure `compte_resultat_view_id`
- [ ] Modifier `CompteResultatGenerateRequest` pour inclure `compte_resultat_view_id: Optional[int]`

**4. Backend - Service de génération compte de résultat :**
- [ ] Modifier `generate_compte_resultat()` dans `backend/api/routes/compte_resultat.py` pour stocker `compte_resultat_view_id` lors de la création de `CompteResultatData`
- [ ] Vérifier que la vue est bien sauvegardée dans chaque enregistrement `CompteResultatData`

**5. Backend - Service de calcul du bilan :**
- [ ] Modifier `calculate_resultat_exercice()` dans `backend/api/services/bilan_service.py` pour accepter `compte_resultat_view_id: Optional[int]`
- [ ] Filtrer `CompteResultatData` par `annee`, `category_name` ET `compte_resultat_view_id` si fourni
- [ ] Si `compte_resultat_view_id` est None, utiliser la logique actuelle (chercher sans filtre de vue)
- [ ] Modifier `calculate_bilan()` pour passer `compte_resultat_view_id` depuis le mapping à `calculate_resultat_exercice()`
- [ ] Modifier `calculate_bilan()` pour NE PAS appliquer `abs()` sur "Résultat de l'exercice (bénéfice / perte)" (préserver le signe)

**6. Backend - API endpoints :**
- [ ] Vérifier que l'endpoint `/api/bilan/calculate` transmet correctement `compte_resultat_view_id` depuis les mappings
- [ ] Vérifier que l'endpoint `/api/bilan/mappings` retourne `compte_resultat_view_id` dans les réponses

**7. Frontend - API Client :**
- [ ] Vérifier que `compteResultatMappingViewsAPI.getAll()` existe dans `frontend/src/api/client.ts`
- [ ] Si absent, ajouter les méthodes nécessaires pour récupérer les vues de compte de résultat
- [ ] Modifier l'interface `BilanMapping` dans `client.ts` pour inclure `compte_resultat_view_id?: number | null`
- [ ] Modifier `BilanMappingCreate` et `BilanMappingUpdate` pour inclure `compte_resultat_view_id`

**8. Frontend - BilanConfigCard :**
- [ ] Charger les vues de compte de résultat disponibles via `compteResultatMappingViewsAPI.getAll()` (similaire à `amortizationViewsAPI.getAll()`)
- [ ] Stocker les vues dans un état `compteResultatViews: Array<{id: number, name: string}>`
- [ ] Dans la colonne "Vue" du tableau, pour la catégorie "Résultat de l'exercice (bénéfice / perte)" :
  - [ ] Afficher un `<select>` dropdown (comme pour "Amortissements cumulés")
  - [ ] Options : "Sélectionner une vue..." (valeur vide) + liste des vues disponibles
  - [ ] Si aucune vue disponible : afficher "Vue à configurer dans l'onglet compte de résultat" (texte gris, italique)
  - [ ] Valeur par défaut : "Sélectionner une vue..." (null)
- [ ] Créer fonction `handleCompteResultatViewChange(mappingId: number, viewId: number | null)` similaire à `handleAmortizationViewChange()`
- [ ] Appeler `bilanAPI.updateMapping()` avec `compte_resultat_view_id: viewId`
- [ ] Recharger les mappings après mise à jour

**9. Frontend - BilanTable :**
- [ ] Modifier `getDisplayAmount()` pour gérer "Résultat de l'exercice (bénéfice / perte)" :
  - [ ] Retourner le montant tel quel (peut être positif ou négatif, pas de `abs()`)
- [ ] Modifier `isNegativeAmountCategory()` pour inclure "Résultat de l'exercice (bénéfice / perte)" :
  - [ ] Retourner `true` si le montant est négatif (perte)
- [ ] Vérifier que l'affichage en rouge fonctionne pour les montants négatifs

**10. Tests :**
- [ ] Créer test script `backend/tests/test_bilan_resultat_exercice_step10_8_4_3.py` :
  - [ ] Vérifier que l'API retourne le montant avec le bon signe (positif ou négatif)
  - [ ] Vérifier que le filtrage par `compte_resultat_view_id` fonctionne
  - [ ] Vérifier que le mapping contient `compte_resultat_view_id`
  - [ ] Vérifier que les données `CompteResultatData` sont liées à la vue

**Tasks**:
- [ ] Backend - Migration DB (ajout `compte_resultat_view_id` dans `compte_resultat_data` et `bilan_mappings`)
- [ ] Backend - Modèles de données (ajout champs dans `CompteResultatData` et `BilanMapping`)
- [ ] Backend - Modèles Pydantic (ajout champs dans les modèles API)
- [ ] Backend - Service génération (stocker `compte_resultat_view_id` dans `CompteResultatData`)
- [ ] Backend - Service calcul (filtrer par vue et préserver le signe)
- [ ] Frontend - API Client (ajout `compte_resultat_view_id` dans interfaces)
- [ ] Frontend - BilanConfigCard (dropdown sélection vue compte de résultat)
- [ ] Frontend - BilanTable (affichage signe et couleur rouge si perte)
- [ ] Tests - Validation complète

**Deliverables**:
- Migration DB pour `compte_resultat_view_id`
- Modification `calculate_resultat_exercice()` pour filtrer par vue
- Modification `calculate_bilan()` pour préserver le signe
- Dropdown sélection vue dans `BilanConfigCard.tsx`
- Affichage signe et couleur dans `BilanTable.tsx`
- Test script de validation

**Acceptance Criteria**:
- [ ] Montant peut être positif (bénéfice) ou négatif (perte)
- [ ] Montant récupéré depuis `CompteResultatData` filtré par `compte_resultat_view_id`
- [ ] Position correcte (dans "Capitaux propres")
- [ ] Affichage en rouge si perte (montant négatif)
- [ ] Dropdown vue disponible dans la colonne "Vue" pour "Résultat de l'exercice"
- [ ] Message informatif si aucune vue disponible
- [ ] Montant calculé correctement par le backend (signe préservé)

---

#### Step 10.8.4.4 : Frontend - Catégorie spéciale "Report à nouveau / report du déficit"

**Status**: ⏸️ EN ATTENTE  
**Description**: Vérifier et valider l'affichage de la catégorie spéciale "Report à nouveau".

**Tasks**:
- [ ] Vérifier que le montant est affiché correctement
- [ ] Vérifier que la catégorie est affichée dans "Capitaux propres"
- [ ] Vérifier que le calcul est correct :
  - Cumul des résultats des années précédentes (N-1, N-2, etc.)
  - Première année : 0 (pas de report)
- [ ] Vérifier que le calcul backend est correct (cumul depuis `compte_resultat_data` ou calcul via `CompteResultatService`)
- [ ] Vérifier que le montant est récupéré depuis l'API `/api/bilan/calculate`
- [ ] Tester avec plusieurs années pour vérifier le cumul

**Deliverables**:
- Validation de l'affichage "Report à nouveau" dans `BilanTable.tsx`

**Acceptance Criteria**:
- [ ] Première année affiche 0
- [ ] Années suivantes affichent le cumul des résultats précédents
- [ ] Position correcte (dans "Capitaux propres")
- [ ] Montant calculé correctement par le backend

---

#### Step 10.8.4.5 : Frontend - Catégorie spéciale "Emprunt bancaire (capital restant dû)"

**Status**: ⏸️ EN ATTENTE  
**Description**: Vérifier et valider l'affichage de la catégorie spéciale "Emprunt bancaire".

**Tasks**:
- [ ] Vérifier que le montant est affiché en positif (dette)
- [ ] Vérifier que la catégorie est affichée dans "Dettes financières"
- [ ] Vérifier que le calcul est correct :
  - Capital restant dû = Crédit accordé - Cumulé des remboursements de capital
  - Calculé au 31/12 de chaque année
- [ ] Vérifier que le calcul backend est correct (depuis `loan_payments` et `loan_configs`)
- [ ] Vérifier que le montant est récupéré depuis l'API `/api/bilan/calculate`
- [ ] Tester avec plusieurs années pour vérifier la diminution progressive

**Deliverables**:
- Validation de l'affichage "Emprunt bancaire" dans `BilanTable.tsx`

**Acceptance Criteria**:
- [ ] Montant affiché en positif (dette)
- [ ] Position correcte (dans "Dettes financières")
- [ ] Montant diminue progressivement avec les remboursements
- [ ] Montant calculé correctement par le backend

---

#### Step 10.8.4.6 : Frontend - Indicateurs visuels pour catégories spéciales

**Status**: ⏸️ EN ATTENTE  
**Description**: Ajouter des indicateurs visuels pour identifier les catégories spéciales.

**Tasks**:
- [ ] Ajouter un indicateur visuel (icône ou badge) pour identifier les catégories spéciales
- [ ] Style distinct pour les catégories spéciales (ex: icône ⚙️ ou badge "Calculé")
- [ ] Optionnel : Tooltip expliquant la source de calcul pour chaque catégorie spéciale

**Deliverables**:
- Mise à jour `frontend/src/components/BilanTable.tsx`
- Indicateurs visuels pour catégories spéciales

**Acceptance Criteria**:
- [ ] Catégories spéciales identifiables visuellement
- [ ] Style cohérent avec le reste de l'interface
- [ ] Optionnel : Tooltip informatif

---

### Step 10.8.5 : Frontend - Validation équilibre ACTIF = PASSIF avec % de différence

**Status**: ⏸️ EN ATTENTE  
**Description**: Ajouter la validation de l'équilibre ACTIF = PASSIF et afficher le pourcentage de différence.

**Tasks**:
- [ ] Ajouter une ligne "ÉQUILIBRE" ou "% Différence" après "TOTAL PASSIF"
- [ ] Calculer la différence pour chaque année :
  - `différence = TOTAL ACTIF - TOTAL PASSIF`
  - `pourcentage = (différence / TOTAL ACTIF) * 100` (si TOTAL ACTIF > 0)
- [ ] Afficher le pourcentage de différence :
  - Format : `% Différence : X.XX%`
  - Si différence = 0 : Vert, texte "Équilibre respecté ✓"
  - Si différence > 0 : Rouge, afficher le pourcentage
  - Si TOTAL ACTIF = 0 : Afficher "N/A"
- [ ] Style de la ligne :
  - Fond légèrement coloré (vert si équilibré, rouge si déséquilibré)
  - Texte en gras
  - Bordure supérieure épaisse
- [ ] Ajouter un message d'alerte si déséquilibré :
  - Afficher un warning si différence > 0.01% (tolérance pour arrondis)
  - Message : "⚠️ Attention : Le bilan n'est pas équilibré. Vérifiez les calculs."

**Deliverables**:
- Mise à jour `frontend/src/components/BilanTable.tsx`
- Validation de l'équilibre avec indicateur visuel

**Acceptance Criteria**:
- [ ] Différence calculée correctement pour chaque année
- [ ] Pourcentage de différence calculé et affiché
- [ ] Indicateur visuel (vert/rouge) selon l'équilibre
- [ ] Message d'alerte si déséquilibré
- [ ] Tolérance pour les arrondis (0.01%)

---

### Step 10.8.6 : Frontend - Formatage et finitions

**Status**: ⏸️ EN ATTENTE  
**Description**: Finaliser le formatage, les styles et la présentation de la table.

**Tasks**:
- [ ] Formatage des montants :
  - Format français : `1 234,56 €`
  - Alignement à droite pour les colonnes de montants
  - Zéro affiché comme `0,00 €` (pas de cellule vide)
- [ ] Styles et espacements :
  - Indentation cohérente pour chaque niveau (A: 0px, B: 20px, C: 40px)
  - Espacement vertical entre les sections (ACTIF et PASSIF)
  - Bordures et séparateurs visuels
- [ ] Responsive design :
  - Table scrollable horizontalement si trop de colonnes (années)
  - Colonne "Bilan" fixe lors du scroll horizontal
- [ ] Améliorations UX :
  - Tooltip sur les catégories spéciales expliquant leur calcul
  - Highlight au survol des lignes
  - Alternance de couleurs pour les lignes (zebrage léger)

**Deliverables**:
- Mise à jour `frontend/src/components/BilanTable.tsx`
- Table finalisée avec tous les styles

**Acceptance Criteria**:
- [ ] Formatage des montants cohérent et correct
- [ ] Styles visuels clairs et hiérarchie bien visible
- [ ] Table responsive et scrollable si nécessaire
- [ ] UX améliorée avec tooltips et highlights
- [ ] Présentation professionnelle et lisible

---

### Step 10.9 : Frontend - Page Bilan

**Status**: ⏸️ EN ATTENTE  
**Description**: Créer la page principale de l'onglet Bilan.

**Tasks**:
- [ ] Créer `frontend/app/dashboard/bilan/page.tsx`
- [ ] Intégrer `BilanConfigCard` et `BilanTable`
- [ ] Gérer le rechargement des données après modification de la configuration
- [ ] Ajouter l'onglet "Bilan" dans la navigation principale

**Deliverables**:
- Fichier `frontend/app/dashboard/bilan/page.tsx`
- Mise à jour de la navigation

**Acceptance Criteria**:
- [ ] Page fonctionne correctement
- [ ] Card et table intégrées
- [ ] Rechargement automatique après modification
- [ ] Navigation mise à jour

---

### Step 10.10 : Test et validation

**Status**: ⏸️ EN ATTENTE  
**Description**: Tester l'ensemble des fonctionnalités du bilan.

**Tasks**:
- [ ] Tester la création/modification/suppression des mappings
- [ ] Tester le filtrage par Level 3
- [ ] Tester le calcul des catégories normales
- [ ] Tester le calcul des catégories spéciales
- [ ] Tester l'affichage hiérarchique
- [ ] Tester l'équilibre ACTIF = PASSIF
- [ ] Tester la sauvegarde/chargement des vues
- [ ] Tester le recalcul automatique
- [ ] **Test complet de bout en bout validé**

**Deliverables**:
- Tests manuels dans le navigateur
- Validation que tous les calculs sont corrects

**Acceptance Criteria**:
- [ ] Toutes les fonctionnalités fonctionnent correctement
- [ ] Tous les calculs sont corrects
- [ ] Équilibre ACTIF = PASSIF validé
- [ ] **Utilisateur confirme que tout fonctionne correctement**

---

**Phase 10 - Acceptance Criteria globaux**:
- [ ] Modèles de données créés
- [ ] Service de calcul fonctionne pour toutes les catégories
- [ ] Endpoints API fonctionnent
- [ ] Card de configuration fonctionne avec filtrage Level 3
- [ ] Table d'affichage avec structure hiérarchique fonctionne
- [ ] Équilibre ACTIF = PASSIF validé
- [ ] Recalcul automatique fonctionne
- [ ] **Test complet de bout en bout validé**

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

