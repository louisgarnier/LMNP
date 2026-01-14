# Plan d'Implémentation - Phase 7 : Structure États financiers et crédit

**Status**: ✅ COMPLÉTÉ  
**Dernière mise à jour**: 2025-01-27

**Notes**:
- Step 7.8 complété le 2025-01-27 - Multi-crédits avec sous-onglets fonctionnel, synchronisation avec LoanConfigCard, suppression des années vides corrigée.
- Step 7.9 complété le 2025-01-27 - Fonctionnalité pin/unpin pour la card de configuration implémentée avec localStorage.

## Vue d'ensemble

**Objectif** : Restructurer l'onglet "Bilan" en "États financiers" avec sous-onglets et ajouter la gestion des crédits.

**Fonctionnalités principales** :

- Restructuration de l'onglet Bilan avec 4 sous-onglets (Compte de résultat, Bilan, Liasse fiscale, Crédit)
- Gestion des configurations de crédit (multi-crédits)
- Import et gestion des mensualités de crédit depuis Excel
- Synchronisation entre configurations et mensualités

---

## Phase 7 : Structure États financiers et crédit

### Step 7.1 : Frontend - Restructuration de l'onglet États financiers

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

- [x] **Créer test visuel dans navigateur**

- [x] **Valider avec l'utilisateur**

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

### Step 7.2 : Backend - Table et modèles pour les mensualités

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

  - `loan_name` (nom du prêt, ex: "Prêt principal", peut correspondre au `name` d'une configuration de crédit)

  - `created_at`, `updated_at`

- [x] Créer modèle SQLAlchemy `LoanPayment` dans `backend/database/models.py`

- [x] Créer modèles Pydantic dans `backend/api/models.py`

- [x] **Créer test unitaire pour le modèle**

- [x] **Valider avec l'utilisateur**

**Deliverables**:

- `backend/database/models.py` - Modèle `LoanPayment`

- `backend/api/models.py` - Modèles Pydantic pour les mensualités

- `backend/tests/test_loan_payment_model.py` - Test unitaire

- `backend/database/__init__.py` - Export du modèle

**Acceptance Criteria**:

- [x] Table créée en BDD

- [x] Modèle SQLAlchemy fonctionnel

- [x] Modèles Pydantic créés et validés

- [x] Tests unitaires passent

---

### Step 7.3 : Backend - Endpoints API pour les mensualités

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

### Step 7.4 : Backend - Table et modèles pour les configurations de crédit

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

- [x] **Valider avec l'utilisateur**

**Deliverables**:

- `backend/database/models.py` - Modèle `LoanConfig`

- `backend/api/models.py` - Modèles Pydantic pour les configurations de crédit

- `backend/tests/test_loan_config_model.py` - Test unitaire

- `backend/database/__init__.py` - Export du modèle

**Acceptance Criteria**:

- [x] Table créée en BDD

- [x] Modèle SQLAlchemy fonctionnel

- [x] Modèles Pydantic créés et validés

- [x] Tests unitaires passent

---

### Step 7.5 : Backend - Endpoints API pour les configurations de crédit

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

- [x] **Valider avec l'utilisateur**

**Deliverables**:

- `backend/api/routes/loan_configs.py` - Endpoints API

- Mise à jour `backend/api/main.py` - Enregistrement du router

- `backend/tests/test_loan_configs_endpoints_manual.py` - Test manuel

**Acceptance Criteria**:

- [x] Tous les endpoints fonctionnent correctement

- [x] Gestion d'erreur correcte

- [x] Tests manuels passent

---

### Step 7.6 : Frontend - Card de configuration des crédits

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

- [ ] **Valider avec l'utilisateur**

**Deliverables**:

- `frontend/src/components/LoanConfigCard.tsx` - Card de configuration

- Mise à jour `frontend/app/dashboard/etats-financiers/page.tsx` - Intégration dans onglet Crédit

- Mise à jour `frontend/src/api/client.ts` - API client

**Acceptance Criteria**:

- [x] Card affichée en haut de l'onglet Crédit

- [x] Tous les champs sont éditables avec les bonnes unités (€, %, ans, mois)

- [x] Possibilité d'ajouter plusieurs lignes de crédit

- [x] Possibilité de supprimer une ligne de crédit

- [x] Sauvegarde fonctionne (backend) - sauvegarde automatique au blur

- [x] Données persistées et rechargées au chargement de la page

- [x] Interface intuitive et cohérente avec le reste de l'application

---

### Step 7.7 : Frontend - Import et gestion des mensualités

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

- `frontend/src/components/LoanPaymentFileUpload.tsx` - Composant d'import

- `frontend/src/components/LoanPaymentPreviewModal.tsx` - Modal de prévisualisation

- `frontend/src/components/LoanPaymentTable.tsx` - Tableau d'affichage

- Mise à jour `frontend/app/dashboard/etats-financiers/page.tsx` - Intégration

- Mise à jour `frontend/src/api/client.ts` - API client

**Acceptance Criteria**:

- [x] Import Excel fonctionne (format attendu : colonne 'annee' + colonnes années)

- [x] Preview affiche les données parsées avec avertissements

- [x] Tableau affiche toutes les mensualités (triées par date)

- [x] Édition inline fonctionne (modification des champs capital, intérêts, assurance, total auto-calculé)

- [x] Suppression fonctionne avec confirmation

- [x] Association avec les configurations de crédit via `loan_name` ("Prêt principal" par défaut)

- [x] Interface intuitive et cohérente avec le reste de l'application

---

### Step 7.8 : Frontend - Multi-crédits avec sous-onglets dans LoanPaymentTable

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

- ✅ Mise à jour `frontend/src/components/LoanPaymentTable.tsx` - Sous-onglets par crédit

- ✅ Mise à jour `frontend/src/components/LoanPaymentFileUpload.tsx` - Association au crédit actif

- ✅ Mise à jour `frontend/app/dashboard/etats-financiers/page.tsx` - Synchronisation avec LoanConfigCard

- ✅ Mise à jour `frontend/src/components/LoanConfigCard.tsx` - Suppression avec confirmation et suppression des mensualités associées

- ✅ Création `backend/scripts/test_loan_payments_db.py` - Script de vérification des mensualités par crédit

- ✅ Création `backend/scripts/cleanup_empty_loan_payments.py` - Script de nettoyage des mensualités vides

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

### Step 7.9 : Frontend - Fonctionnalité pin/unpin pour la card de configuration

**Status**: ✅ COMPLÉTÉ  

**Description**: Ajouter un bouton pin/unpin à côté du titre "Configurations de crédit" pour replier/déplier la card.

**Tasks**:

- [x] Ajouter un état `isCollapsed` pour gérer l'état replié/déplié

- [x] Ajouter un bouton pin/unpin (📌/📍) à côté du titre "Configurations de crédit"

- [x] Implémenter la logique de repli/dépli : masquer/afficher le contenu de la card (formulaires, boutons)

- [x] Sauvegarder l'état dans localStorage pour persister entre les sessions

- [x] Charger l'état depuis localStorage au montage du composant

- [x] **Tester dans le navigateur**

**Deliverables**:

- ✅ Mise à jour `frontend/src/components/LoanConfigCard.tsx` :
  - Ajout de l'état `isCollapsed` avec localStorage (`STORAGE_KEY_LOAN_CONFIG_COLLAPSED`)
  - Ajout du bouton pin/unpin à côté du titre
  - Conditionnement de l'affichage du contenu (formulaires, bouton "Ajouter un crédit") selon `isCollapsed`
  - Fonction `handleToggleCollapse()` pour toggle l'état et sauvegarder dans localStorage

**Acceptance Criteria**:

- [x] Bouton pin/unpin visible à côté du titre

- [x] Clic sur le bouton replie/déplie la card

- [x] Le contenu (formulaires, boutons) est masqué quand la card est repliée

- [x] Seul le titre et le bouton pin restent visibles quand replié

- [x] L'état est sauvegardé dans localStorage

- [x] L'état est restauré au rechargement de la page

- [x] **Test visuel dans navigateur validé**

---

### Step 7.10 : Frontend - Champs supplémentaires dans la card de configuration

**Status**: ✅ COMPLÉTÉ  

**Description**: Ajouter des champs input et calculés à la card de configuration de crédit pour afficher des informations dérivées (dates, durées, mois écoulés/restants).

**Tasks**:

- [x] **7.10.1** - Ajouter deux champs input :
  - Date d'emprunt (input date)
  - Date de fin prévisionnelle (input date)
  - Stocker ces dates dans la base de données (ajout de colonnes dans `loan_configs`)

- [x] **7.10.2** - Ajouter une colonne calculée "Durée crédit (années)" :
  - Calcul : `YEARFRAC(date_emprunt, date_fin, 3)` (base 3 = année réelle/365)
  - Affichage en lecture seule (calculé automatiquement)

- [x] **7.10.3** - Ajouter une colonne calculée "Durée crédit (années) incluant différé" :
  - Calcul : `YEARFRAC(date_emprunt, date_fin, 3) - (Décalage initial (mois))/12`
  - Affichage en lecture seule

- [x] **7.10.5** - Ajouter un champ calculé "Nombre de mois écoulés" :
  - Calcul : `ROUND(YEARFRAC(date_emprunt, date_du_jour, 3) * 12, 0)`
  - Mois depuis le début de l'emprunt jusqu'à aujourd'hui
  - Affichage en lecture seule (recalculé à chaque affichage)

- [x] **7.10.6** - Ajouter un champ calculé "Nombre de mois restants" :
  - Calcul : `ROUND(YEARFRAC(date_du_jour, date_fin_previsionnelle, 3) * 12, 0)`
  - Mois restants jusqu'à la fin prévisionnelle
  - Affichage en lecture seule (recalculé à chaque affichage)

- [x] **7.10.7** - Ajouter un champ calculé "Durée restante" formatée :
  - Format : "10 ans et 3 mois"
  - Calcul : `INT(mois_restants/12) & " ans et " & ROUND(((mois_restants/12)-INT(mois_restants/12))*12, 0) & " mois"`
  - Affichage en lecture seule

**Deliverables**:

- Mise à jour `backend/database/models.py` :
  - Ajout des colonnes `loan_start_date` (DATE) et `loan_end_date` (DATE) dans `LoanConfig`

- Mise à jour `backend/database/schema.sql` :
  - Ajout des colonnes dans la table `loan_configs`

- Mise à jour `backend/api/models.py` :
  - Ajout des champs `loan_start_date` et `loan_end_date` dans les modèles Pydantic

- Mise à jour `frontend/src/components/LoanConfigCard.tsx` :
  - Ajout des champs input pour les dates (7.10.1)
  - Ajout des champs calculés en lecture seule (7.10.2, 7.10.3, 7.10.5, 7.10.6, 7.10.7)
  - Implémentation des fonctions de calcul YEARFRAC équivalentes en JavaScript

- Migration de base de données :
  - Script de migration pour ajouter les nouvelles colonnes

**Acceptance Criteria**:

- [x] Champs input "Date d'emprunt" et "Date de fin prévisionnelle" visibles et éditables

- [x] Les dates sont sauvegardées en base de données

- [x] Colonne "Durée crédit (années)" affiche le résultat de YEARFRAC(date_emprunt, date_fin, 3)

- [x] Colonne "Durée crédit (années) incluant différé" affiche le résultat correct

- [x] Champ "Nombre de mois écoulés" affiche le nombre de mois depuis le début jusqu'à aujourd'hui

- [x] Champ "Nombre de mois restants" affiche le nombre de mois restants jusqu'à la fin

- [x] Champ "Durée restante" affiche le format "X ans et Y mois"

- [x] Tous les champs calculés sont en lecture seule et se mettent à jour automatiquement

- [x] Les calculs sont corrects (vérification avec Excel)

- [x] Script de test `test_loan_payments_db.py` mis à jour pour afficher les calculs

**Détails techniques**:

- **YEARFRAC équivalent JavaScript** : 
  - Base 3 (année réelle/365) : `(date_fin - date_debut) / (365 * 1000 * 60 * 60 * 24)`
  - Ou utiliser une bibliothèque de dates pour plus de précision

- **Calcul des mois** :
  - `ROUND(YEARFRAC * 12, 0)` pour convertir années en mois

- **Format "X ans et Y mois"** :
  - `Math.floor(mois_restants / 12)` pour les années
  - `Math.round((mois_restants / 12 - Math.floor(mois_restants / 12)) * 12)` pour les mois

- **Stockage** : Seules les dates sont stockées en base, les autres champs sont calculés à l'affichage

---

### Step 7.11 : Restructuration de l'onglet Crédit avec sous-onglets par crédit

**Status**: ✅ COMPLÉTÉ  

**Description**: Restructurer l'onglet Crédit pour afficher un sous-onglet par crédit, chacun contenant sa configuration et ses mensualités. Déplacer "J'ai un crédit" dans la barre de navigation principale.

**Tasks**:

- [x] **7.11.1** - Déplacer "J'ai un crédit" dans la barre de navigation :
  - Retirer la checkbox de sa position actuelle (sous la barre de navigation)
  - Afficher une vraie checkbox avec "J'ai un crédit" comme un élément de la barre de navigation principale
  - Position : à droite des onglets (Compte de résultat, Bilan, Liasse fiscale, Crédit)
  - Afficher toujours dans la barre (checkbox toujours visible, état visuel change selon coché/décoché)
  - Conserver la fonctionnalité de toggle (clic pour activer/désactiver avec confirmation)

- [x] **7.11.2** - Créer la structure de sous-onglets crédit :
  - Afficher une deuxième rangée d'onglets horizontaux sous l'onglet "Crédit" principal
  - Visible uniquement quand l'onglet "Crédit" est actif ET "J'ai un crédit" est coché
  - Style cohérent avec les onglets principaux mais visuellement distincts (fond #f9fafb, légèrement plus petits)
  - Structure prête pour l'ajout des onglets individuels dans le step suivant

- [x] **7.11.3** - Afficher un sous-onglet par crédit :
  - Créer un sous-onglet pour chaque crédit existant en base de données
  - Afficher le nom du crédit comme libellé de l'onglet
  - Trier les crédits par date de création (du plus ancien au plus récent)
  - Gérer la sélection de l'onglet actif (surlignage, état actif, couleur différente)
  - Effet hover sur les onglets inactifs

- [x] **7.11.4** - Ajouter le bouton "+ Ajouter un crédit" :
  - Position : à droite de la barre des sous-onglets crédit
  - Style : bouton distinct des onglets (couleur #1e3a5f, icône +)
  - Visible uniquement dans la barre des sous-onglets crédit
  - La fonctionnalité de création sera implémentée dans le step 7.11.5

- [x] **7.11.5** - Créer un nouveau crédit depuis le bouton "+ Ajouter un crédit" :
  - Au clic, créer un nouveau crédit avec valeurs par défaut :
    - Nom : "Nouveau crédit"
    - Crédit accordé : 0 €
    - Taux fixe : 0 %
    - Durée : 0 ans
    - Décalage initial : 0 mois
    - Dates : null
  - Créer automatiquement un nouvel onglet pour ce crédit
  - Bascule automatiquement vers le nouvel onglet créé
  - Recharger la liste des crédits après création
  - Gestion des erreurs avec message d'alerte

- [x] **7.11.6** - Afficher la card de configuration dans chaque sous-onglet :
  - Créer un composant `LoanConfigSingleCard` pour afficher UN seul crédit
  - Afficher tous les champs de configuration (nom, montant, taux, durée, décalage, dates, calculs)
  - Permettre l'édition inline avec auto-save (comme actuellement)
  - Supprimer le bouton "Supprimer" de la card (la suppression se fera via le "x" de l'onglet)
  - Afficher uniquement le crédit de l'onglet actif

- [x] **7.11.7** - Afficher le bouton "Load Mensualités" sur la même ligne que "Configurations de crédit" :
  - Titre "Configurations de crédit" à gauche
  - Bouton "📊 Load Mensualités" (`LoanPaymentFileUpload`) à droite, sur la même ligne
  - Le bouton doit être associé au crédit de l'onglet actif
  - Conserver la fonctionnalité actuelle (upload, prévisualisation, import)
  - Intégré dans le header de `LoanConfigSingleCard`

- [x] **7.11.8** - Afficher le tableau des mensualités dans chaque sous-onglet :
  - Afficher `LoanPaymentTable` en dessous de la card de configuration
  - Filtrer automatiquement les mensualités pour le crédit de l'onglet actif
  - Masquer les sous-onglets dans `LoanPaymentTable` (déjà gérés au niveau supérieur)
  - Conserver toutes les fonctionnalités actuelles (édition inline, suppression, sélection multiple)
  - Utiliser `initialActiveLoanName` pour synchroniser le crédit actif

- [x] **7.11.9** - Ajouter le bouton "x" de suppression au survol de chaque sous-onglet :
  - Afficher un petit "x" à droite du nom du crédit dans l'onglet
  - Visible uniquement au survol de l'onglet (hover)
  - Style discret mais visible (gris #6b7280, devient rouge #dc2626 au survol)
  - Empêcher le clic sur "x" de déclencher le changement d'onglet (stopPropagation)
  - La fonctionnalité de suppression sera implémentée dans le step 7.11.10

- [x] **7.11.10** - Gérer la suppression d'un crédit avec confirmation :
  - Au clic sur le "x", afficher un popup de confirmation :
    - Message : "Êtes-vous sûr de vouloir supprimer le crédit '[nom]' ?"
    - Si des mensualités existent : "Toutes les mensualités associées (X) seront également supprimées."
  - Si confirmé :
    - Supprimer toutes les mensualités associées au crédit (avec Promise.allSettled)
    - Supprimer la configuration du crédit
    - Recharger la liste des crédits
    - Si c'était le dernier crédit, afficher "Aucun crédit configuré" (activeLoanName = null)
    - Si d'autres crédits existent, basculer vers le premier crédit disponible

- [x] **7.11.11** - Gérer le cas "Aucun crédit configuré" :
  - Quand aucun crédit n'existe (après suppression du dernier ou initialement) :
    - Afficher un message centré : "Aucun crédit configuré" avec instructions
    - Afficher le bouton "+ Ajouter un crédit" dans la barre des sous-onglets
    - Permettre la création d'un premier crédit
    - Message visible dans la barre des sous-onglets ET dans le contenu principal

**Deliverables**:

- Mise à jour `frontend/app/dashboard/etats-financiers/page.tsx` :
  - Déplacer "J'ai un crédit" dans la barre de navigation (7.11.1)
  - Créer la structure de sous-onglets crédit (7.11.2, 7.11.3)
  - Ajouter le bouton "+ Ajouter un crédit" (7.11.4, 7.11.5)
  - Gérer la suppression avec "x" (7.11.9, 7.11.10)
  - Gérer le cas "Aucun crédit configuré" (7.11.11)

- Créer ou adapter `frontend/src/components/LoanConfigSingleCard.tsx` :
  - Composant pour afficher UN seul crédit (7.11.6)
  - Afficher tous les champs de configuration
  - Permettre l'édition inline avec auto-save
  - Intégrer le bouton "Load Mensualités" sur la même ligne que le titre (7.11.7)

- Mise à jour de l'affichage dans chaque sous-onglet :
  - Card de configuration (7.11.6, 7.11.7)
  - Tableau des mensualités filtré par crédit (7.11.8)

**Acceptance Criteria**:

- [x] "J'ai un crédit" est affiché dans la barre de navigation principale, à droite des onglets

- [x] Les sous-onglets crédit apparaissent uniquement quand l'onglet "Crédit" est actif ET "J'ai un crédit" est coché

- [x] Un sous-onglet est créé pour chaque crédit existant, affichant son nom

- [x] Les crédits sont triés par date de création (du plus ancien au plus récent)

- [x] Le bouton "+ Ajouter un crédit" est visible à droite de la barre des sous-onglets

- [x] Cliquer sur "+ Ajouter un crédit" crée un nouveau crédit et bascule vers son onglet

- [x] Chaque sous-onglet affiche :
  - Titre "Configurations de crédit" à gauche, bouton "📊 Load Mensualités" à droite (même ligne)
  - Card de configuration complète du crédit
  - Tableau des mensualités filtré pour ce crédit

- [x] Le bouton "x" apparaît au survol de chaque sous-onglet crédit

- [x] Cliquer sur "x" affiche un popup de confirmation avant suppression

- [x] La suppression supprime le crédit, ses mensualités et l'onglet correspondant

- [x] Si aucun crédit n'existe, afficher "Aucun crédit configuré" avec instructions

- [x] Toutes les fonctionnalités existantes (upload, édition, suppression de mensualités) fonctionnent dans chaque sous-onglet

**Détails techniques**:

- **Gestion de l'état** :
  - Utiliser `useState` pour gérer l'onglet crédit actif
  - Charger les crédits depuis l'API au montage et après chaque création/suppression
  - Persister l'onglet actif dans l'URL (query param) ou localStorage

- **Composant `LoanConfigSingleCard`** :
  - Props : `loanConfig: LoanConfig`, `onConfigUpdated: () => void`
  - Afficher tous les champs comme dans `LoanConfigCard` mais pour un seul crédit
  - Intégrer `LoanPaymentFileUpload` dans le header (même ligne que le titre)

- **Filtrage des mensualités** :
  - `LoanPaymentTable` doit recevoir `loanName` comme prop pour filtrer automatiquement
  - Ne pas afficher les sous-onglets dans `LoanPaymentTable` (déjà géré au niveau supérieur)

- **Suppression** :
  - Utiliser `loanConfigsAPI.delete(id)` pour supprimer la configuration
  - Utiliser `loanPaymentsAPI.getAll({ loan_name })` puis `delete` pour chaque mensualité
  - Ou créer un endpoint backend pour supprimer un crédit et toutes ses mensualités en cascade

---

### Step 7.12 : Tableau de simulation de crédit

**Status**: ✅ COMPLÉTÉ

**Description**: Ajouter un tableau de simulation de crédit sous les calculs automatiques dans la card de configuration. Le tableau affiche les calculs financiers (PMT, IPMT, PPMT) pour les mensualités 1, 50, 100, 150, 200, avec un champ input pour l'assurance mensuelle (valeur unique pour toutes les mensualités).

**Tasks**:

- [x] **7.12.1** - Backend - Ajouter le champ `monthly_insurance` au modèle `LoanConfig` :
  - Ajouter la colonne `monthly_insurance` (type `Float`, nullable, default=0) dans `backend/database/models.py`
  - Ajouter le champ dans `backend/api/models.py` (`LoanConfigBase`, `LoanConfigCreate`, `LoanConfigUpdate`)
  - Mettre à jour `backend/database/schema.sql`
  - Créer une migration SQLAlchemy pour ajouter la colonne
  - Mettre à jour les endpoints API pour inclure `monthly_insurance` dans les réponses
  - Créer/mettre à jour un script de test Python (`backend/tests/test_loan_configs_monthly_insurance.py`) pour tester :
    - Création d'un `LoanConfig` avec `monthly_insurance`
    - Mise à jour de `monthly_insurance` via l'API
    - Récupération d'un `LoanConfig` avec `monthly_insurance`
    - Validation que la valeur est bien persistée en base de données

- [x] **7.12.2** - Frontend - Ajouter le champ input "Assurance mensuelle" dans `LoanConfigSingleCard` :
  - Ajouter un champ input numérique pour "Assurance mensuelle (€/mois)"
  - Position : dans la section des champs de configuration (avec les autres champs)
  - Valeur par défaut : 0 si non renseigné
  - Auto-save lors de la modification (comme les autres champs)
  - Format : nombre avec 2 décimales, formatage monétaire à l'affichage

- [x] **7.12.3** - Frontend - Implémenter les fonctions financières JavaScript (PMT, IPMT, PPMT) :
  - Créer un fichier `frontend/src/utils/financial.ts` (ou `.js`)
  - Implémenter `PMT(rate, nper, pv, fv, type)` :
    - `rate` : taux d'intérêt mensuel (taux fixe / 12)
    - `nper` : nombre total de périodes (durée crédit incluant différé * 12)
    - `pv` : valeur actuelle (montant du crédit, négatif)
    - Retourne la mensualité constante (hors assurance)
  - Implémenter `IPMT(rate, per, nper, pv, fv, type)` :
    - `per` : numéro de la période (mensualité 1, 50, 100, 150, 200)
    - Retourne la part d'intérêt pour cette période
  - Implémenter `PPMT(rate, per, nper, pv, fv, type)` :
    - Retourne la part de capital pour cette période
  - Utiliser les formules Excel équivalentes pour garantir la cohérence

- [x] **7.12.4** - Frontend - Créer le tableau de simulation dans `LoanConfigSingleCard` :
  - Position : sous les calculs automatiques (durée crédit, mois écoulés, etc.)
  - Titre : "Simulations crédit"
  - Structure du tableau :
    - Colonnes : Mensualité, Mensualité crédit, Intérêt, Capital, Assurance, Total
    - Lignes : 5 lignes pour les mensualités 1, 50, 100, 150, 200
  - Style cohérent avec le reste de la card (bordures, espacement, typographie)

- [x] **7.12.5** - Frontend - Calculer et afficher les valeurs pour chaque mensualité :
  - Pour chaque mensualité (1, 50, 100, 150, 200) :
    - **Mensualité crédit** : `PMT(taux/12, durée_totale_mois, -montant)` (constant pour toutes)
    - **Intérêt** : `IPMT(taux/12, numéro_mensualité, durée_totale_mois, -montant)` (décroît)
    - **Capital** : `PPMT(taux/12, numéro_mensualité, durée_totale_mois, -montant)` (croît)
    - **Assurance** : valeur du champ "Assurance mensuelle" (identique pour toutes)
    - **Total** : Assurance + Intérêt + Capital
  - Formatage monétaire : tous les montants en euros avec 2 décimales (ex: 1 234,56 €)
  - Arrondi à 2 décimales pour tous les calculs

- [x] **7.12.6** - Frontend - Gérer la mise à jour automatique du tableau :
  - Recalculer automatiquement le tableau quand :
    - Le taux fixe change
    - Le montant du crédit change
    - La durée crédit (incluant différé) change
    - L'assurance mensuelle change
  - Conserver la valeur d'assurance saisie lors des recalculs
  - Afficher un indicateur de chargement si nécessaire (calculs complexes)

**Deliverables**:

- Backend :
  - Migration SQLAlchemy pour `monthly_insurance`
  - Mise à jour des modèles (`LoanConfig` dans `database/models.py` et `api/models.py`)
  - Mise à jour des endpoints API (`loan_configs.py`)
  - Script de test Python (`backend/tests/test_loan_configs_monthly_insurance.py`) pour tester toutes les fonctionnalités backend au fur et à mesure :
    - Test de création avec `monthly_insurance`
    - Test de mise à jour de `monthly_insurance`
    - Test de récupération avec `monthly_insurance`
    - Test de validation des valeurs (null, 0, valeurs positives)
    - Test de persistance en base de données

- Frontend :
  - Fichier `frontend/src/utils/financial.ts` avec PMT, IPMT, PPMT
  - Champ input "Assurance mensuelle" dans `LoanConfigSingleCard`
  - Tableau de simulation dans `LoanConfigSingleCard`
  - Mise à jour de l'interface TypeScript `LoanConfig` dans `client.ts`

**Acceptance Criteria**:

- [x] Le champ `monthly_insurance` est présent dans le modèle `LoanConfig` (backend)

- [x] Le champ input "Assurance mensuelle" est visible dans la card de configuration

- [x] La valeur d'assurance est sauvegardée automatiquement lors de la modification

- [x] Les fonctions PMT, IPMT, PPMT sont implémentées et testées (équivalentes Excel)

- [x] Le tableau "Simulations crédit" est visible sous les calculs automatiques

- [x] Le tableau affiche 5 lignes (mensualités 1, 50, 100, 150, 200) avec 7 colonnes (ajout de "Total (par an)")

- [x] Les calculs sont corrects :
  - Mensualité crédit : constante pour toutes les mensualités
  - Intérêt : décroît au fil du temps
  - Capital : croît au fil du temps
  - Assurance : identique pour toutes les mensualités
  - Total (par mois) : Assurance + Intérêt + Capital
  - Total (par an) : Total (par mois) * 12

- [x] Le tableau se recalcule automatiquement quand les paramètres du crédit changent

- [x] Tous les montants sont formatés en euros avec 2 décimales (ex: 1 234,56 €)

- [x] La valeur d'assurance saisie est conservée lors des recalculs

- [x] Bug IPMT corrigé (solde négatif) - utilisation de valeur absolue pour le calcul du solde

**Détails techniques**:

- **Formules financières** :
  - `PMT(rate, nper, pv)` = `pv * rate * (1 + rate)^nper / ((1 + rate)^nper - 1)`
  - `IPMT(rate, per, nper, pv)` = Calcul basé sur le solde restant dû à la période `per-1`
  - `PPMT(rate, per, nper, pv)` = `PMT(rate, nper, pv) - IPMT(rate, per, nper, pv)`
  - Note : Les valeurs sont négatives dans Excel (remboursements), utiliser la valeur absolue pour l'affichage

- **Durée totale** :
  - Utiliser "Durée crédit (années) incluant différé" pour `nper`
  - `nper = (duration_years + initial_deferral_months / 12) * 12`

- **Gestion des cas limites** :
  - Si `monthly_insurance` est null ou undefined, utiliser 0
  - Si les paramètres du crédit ne sont pas complets, afficher "N/A" ou "-" dans le tableau
  - Si `nper` est 0 ou négatif, ne pas calculer

- **Performance** :
  - Les calculs sont effectués côté client (pas d'appel API)
  - Utiliser `useMemo` pour éviter les recalculs inutiles

---

### Step 7.13 : Ajout/Suppression de rangées personnalisées dans le tableau de simulation

**Status**: ✅ COMPLÉTÉ

**Description**: Permettre à l'utilisateur d'ajouter et supprimer des rangées dans le tableau "Simulations crédit" avec des numéros de mensualité personnalisés. Les valeurs par défaut (1, 50, 100, 150, 200) sont conservées mais peuvent être supprimées.

**Tasks**:

- [x] **7.13.1** - Backend - Ajouter le champ `simulation_months` au modèle `LoanConfig` :
  - Ajouter la colonne `simulation_months` (type `Text`, nullable, stocke un JSON array) dans `backend/database/models.py`
  - Ajouter le champ dans `backend/api/models.py` (`LoanConfigBase`, `LoanConfigCreate`, `LoanConfigUpdate`)
  - Mettre à jour `backend/database/schema.sql`
  - Créer une migration SQLAlchemy pour ajouter la colonne
  - Mettre à jour les endpoints API pour inclure `simulation_months` dans les réponses
  - Format JSON : tableau de nombres `[1, 50, 100, 150, 200]` (valeurs par défaut si null)
  - Créer/mettre à jour un script de test Python pour valider la persistance

- [x] **7.13.2** - Frontend - Ajouter la fonctionnalité d'ajout de ligne :
  - Ajouter un menu contextuel (clic droit) sur le tableau
  - Option "Ajouter une ligne" dans le menu contextuel
  - Au clic, créer une nouvelle rangée avec :
    - Champ mensualité vide (input éditable)
    - Focus automatique sur le champ pour saisie immédiate
    - Autres colonnes affichant "-" en attendant la validation
  - Validation automatique au blur ou Enter :
    - Vérifier que le numéro est un entier positif
    - Vérifier qu'il n'y a pas de doublon (empêcher la validation si doublon)
    - Vérifier qu'il ne dépasse pas la durée totale (afficher message sur la ligne)
    - Si valide : rendre le champ non-éditable et calculer les valeurs
    - Si invalide : afficher un message d'erreur et garder le champ éditable
  - Sauvegarder automatiquement la liste des mensualités en base après validation
  - Trier automatiquement les rangées par numéro de mensualité croissant

- [x] **7.13.3** - Frontend - Ajouter la fonctionnalité de suppression de ligne :
  - Ajouter l'option "Supprimer" dans le menu contextuel (clic droit sur une ligne)
  - Au clic, supprimer la rangée correspondante
  - Sauvegarder automatiquement la liste mise à jour en base
  - Réorganiser l'affichage (tri automatique)

- [x] **7.13.4** - Frontend - Gestion des messages d'erreur et validation :
  - Message "durée total credit depassée" :
    - Afficher uniquement sur la ligne concernée (pas sur tout le tableau)
    - Fusionner toutes les cellules de la ligne en une seule cellule
    - Afficher le message centré
    - Les autres lignes restent normales avec leurs calculs
  - Message de doublon :
    - Afficher un message d'erreur sous le champ input
    - Empêcher la validation tant que le doublon existe
  - Charger les mensualités personnalisées depuis la base au chargement du composant
  - Valeurs par défaut : utiliser `[1, 50, 100, 150, 200]` si `simulation_months` est null ou vide

**Deliverables**:

- Backend :
  - Migration SQLAlchemy pour `simulation_months`
  - Mise à jour des modèles (`LoanConfig` dans `database/models.py` et `api/models.py`)
  - Mise à jour des endpoints API (`loan_configs.py`)
  - Script de test Python pour valider la persistance JSON

- Frontend :
  - Menu contextuel (clic droit) sur le tableau de simulation
  - Gestion de l'état des rangées (éditable/non-éditable)
  - Validation et affichage des messages d'erreur
  - Sauvegarde automatique des mensualités personnalisées
  - Chargement des mensualités depuis la base
  - Mise à jour de l'interface TypeScript `LoanConfig` dans `client.ts`

**Acceptance Criteria**:

- [x] Le champ `simulation_months` est présent dans le modèle `LoanConfig` (backend)

- [x] Le menu contextuel (clic droit) apparaît sur le tableau de simulation

- [x] L'option "Ajouter une ligne" crée une nouvelle rangée avec champ mensualité vide

- [x] Le focus est automatiquement placé sur le champ mensualité lors de l'ajout

- [x] La validation se fait automatiquement au blur ou Enter

- [x] Les doublons sont empêchés (pas de validation possible)

- [x] Le message "durée total credit depassée" s'affiche uniquement sur la ligne concernée (première colonne conservée)

- [x] Les numéros validés deviennent non-éditables

- [x] L'option "Supprimer" supprime la rangée et sauvegarde en base

- [x] Les rangées sont triées automatiquement par numéro croissant

- [x] Les mensualités personnalisées sont chargées depuis la base au montage du composant

- [x] Les valeurs par défaut `[1, 50, 100, 150, 200]` sont utilisées si `simulation_months` est null

- [x] Les valeurs par défaut peuvent être supprimées

**Détails techniques**:

- **Format JSON** :
  - Stockage : `"[1, 50, 100, 150, 200]"` (string JSON)
  - Parsing : `JSON.parse(simulation_months)` pour récupérer le tableau
  - Validation : tableau de nombres entiers positifs, trié, sans doublons

- **Menu contextuel** :
  - Utiliser `onContextMenu` sur le tableau
  - Prévenir le menu contextuel par défaut du navigateur
  - Afficher un menu personnalisé avec les options
  - Positionner le menu à la position du clic

- **Gestion de l'état** :
  - `editingMonth: number | null` : mensualité en cours d'édition
  - `simulationMonths: number[]` : liste des mensualités à afficher
  - `errorMessages: { [month: number]: string }` : messages d'erreur par mensualité

- **Validation** :
  - Numéro valide : entier positif entre 1 et durée totale (incluant différé) * 12
  - Doublon : vérifier dans `simulationMonths` avant validation
  - Durée dépassée : `month > totalMonths`

- **Sauvegarde** :
  - Sauvegarder automatiquement après chaque ajout/suppression validé
  - Utiliser `loanConfigsAPI.update` avec `simulation_months: JSON.stringify(simulationMonths)`

---

## Notes importantes

1. **Format d'import mensualités** : 1 enregistrement par année (date = 01/01/année), pas de mensualités mensuelles
2. **Nom par défaut** : "Prêt principal" pour le premier crédit
3. **Gestion des doublons** : Écrasement avec confirmation (dans preview ET backend)
4. **Multi-crédits** : Synchronisation automatique entre configurations et mensualités via `loan_name`
5. **Validation** : Vérification automatique que `capital + interest + insurance = total`

