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

**Status**: ⏳ EN ATTENTE  

**Description**: Ajouter des champs input et calculés à la card de configuration de crédit pour afficher des informations dérivées (dates, durées, mois écoulés/restants).

**Tasks**:

- [ ] **7.10.1** - Ajouter deux champs input :
  - Date d'emprunt (input date)
  - Date de fin prévisionnelle (input date)
  - Stocker ces dates dans la base de données (ajout de colonnes dans `loan_configs`)

- [ ] **7.10.2** - Ajouter une colonne calculée "Durée crédit (années)" :
  - Calcul : `YEARFRAC(date_emprunt, date_fin, 3)` (base 3 = année réelle/365)
  - Affichage en lecture seule (calculé automatiquement)

- [ ] **7.10.3** - Ajouter une colonne calculée "Durée crédit (années) incluant différé" :
  - Calcul : `YEARFRAC(date_emprunt, date_fin, 3) - (Décalage initial (mois))/12`
  - Affichage en lecture seule

- [ ] **7.10.5** - Ajouter un champ calculé "Nombre de mois écoulés" :
  - Calcul : `ROUND(YEARFRAC(date_emprunt, date_du_jour, 3) * 12, 0)`
  - Mois depuis le début de l'emprunt jusqu'à aujourd'hui
  - Affichage en lecture seule (recalculé à chaque affichage)

- [ ] **7.10.6** - Ajouter un champ calculé "Nombre de mois restants" :
  - Calcul : `ROUND(YEARFRAC(date_du_jour, date_fin_previsionnelle, 3) * 12, 0)`
  - Mois restants jusqu'à la fin prévisionnelle
  - Affichage en lecture seule (recalculé à chaque affichage)

- [ ] **7.10.7** - Ajouter un champ calculé "Durée restante" formatée :
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

- [ ] Champs input "Date d'emprunt" et "Date de fin prévisionnelle" visibles et éditables

- [ ] Les dates sont sauvegardées en base de données

- [ ] Colonne "Durée crédit (années)" affiche le résultat de YEARFRAC(date_emprunt, date_fin, 3)

- [ ] Colonne "Durée crédit (années) incluant différé" affiche le résultat correct

- [ ] Champ "Nombre de mois écoulés" affiche le nombre de mois depuis le début jusqu'à aujourd'hui

- [ ] Champ "Nombre de mois restants" affiche le nombre de mois restants jusqu'à la fin

- [ ] Champ "Durée restante" affiche le format "X ans et Y mois"

- [ ] Tous les champs calculés sont en lecture seule et se mettent à jour automatiquement

- [ ] Les calculs sont corrects (vérification avec Excel)

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

## Notes importantes

1. **Format d'import mensualités** : 1 enregistrement par année (date = 01/01/année), pas de mensualités mensuelles
2. **Nom par défaut** : "Prêt principal" pour le premier crédit
3. **Gestion des doublons** : Écrasement avec confirmation (dans preview ET backend)
4. **Multi-crédits** : Synchronisation automatique entre configurations et mensualités via `loan_name`
5. **Validation** : Vérification automatique que `capital + interest + insurance = total`

