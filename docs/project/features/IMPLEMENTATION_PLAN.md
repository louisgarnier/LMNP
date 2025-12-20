# Plan d'Implémentation - Application Web LMNP

**Status**: En cours  
**Dernière mise à jour**: 2025-12-19

## Vue d'ensemble

Transformation des 9 scripts Python en application web moderne avec dashboard interactif.

---

## Phase 1 : Infrastructure de base

### Step 1.1 : Configuration base de données
**Status**: ✅ COMPLÉTÉ  
**Description**: Créer le schéma de base de données pour stocker transactions, enrichissements, calculs et états financiers.

**Tasks**:
- [x] Créer modèles SQLAlchemy (7 tables)
- [x] Mettre à jour schema.sql
- [x] Migrer connection.py vers SQLAlchemy
- [x] Mettre à jour requirements.txt
- [x] Créer test de base (test_database_schema.py)
- [x] Créer test complet avec données réelles (test_database_complete.py)
- [x] Exécuter test complet et valider résultats
- [x] **Validé par l'utilisateur** (colonnes pourront être revues plus tard)

**Deliverables**:
- `backend/database/models.py` - Modèles SQLAlchemy
- `backend/database/schema.sql` - Schéma SQL
- `backend/database/connection.py` - Configuration SQLAlchemy
- `backend/tests/test_database_schema.py` - Test de validation

**Tests**:
- [x] Test création de toutes les tables (test_database_schema.py)
- [x] Test insertion/requête de transactions (test_database_schema.py)
- [x] Test insertion/requête de mappings (test_database_complete.py)
- [x] Test insertion/requête de paramètres (test_database_complete.py)
- [x] Test relations entre tables (transactions ↔ enriched_transactions) (test_database_complete.py)
- [x] Test workflow complet avec données réelles (test_database_complete.py)
- [x] Test index et performance (validé via tests)

**Acceptance Criteria**:
- [x] Toutes les 7 tables créées correctement
- [x] Modèles SQLAlchemy fonctionnels
- [x] Test script de base exécutable et passe (test_database_schema.py)
- [x] Test script complet exécutable et passe (test_database_complete.py)
- [x] Workflow complet validé avec données réelles
- [x] **Utilisateur confirme que le schéma est correct** (colonnes pourront être revues plus tard)

**Impact Frontend**: Aucun pour l'instant (infrastructure backend)

---

### Step 1.2 : API Backend de base
**Status**: ✅ COMPLÉTÉ  
**Description**: Mettre en place la structure FastAPI avec endpoints de base et connexion DB.

**Tasks**:
- [x] Mettre à jour main.py pour projet LMNP
- [x] Créer routes/transactions.py avec endpoints CRUD de base
- [x] Créer modèles Pydantic pour validation
- [x] Configurer CORS pour frontend
- [x] Créer test complet de l'API (test_api_base.py)
- [x] Exécuter tests et valider résultats
- [x] Tester API manuellement (tous les endpoints validés)
- [x] **Validé par l'utilisateur**

**Deliverables**:
- `backend/api/main.py` - Application FastAPI
- `backend/api/routes/transactions.py` - Endpoints transactions
- `backend/api/models.py` - Modèles Pydantic
- `backend/tests/test_api_base.py` - Tests API

**Tests**:
- [x] Test démarrage API (health check) - Validé
- [x] Test connexion DB via API - Validé
- [x] Test GET /api/transactions (liste vide) - Validé
- [x] Test POST /api/transactions (création) - Validé
- [x] Test GET /api/transactions/{id} - Validé
- [x] Test PUT /api/transactions/{id} (mise à jour) - Validé
- [x] Test DELETE /api/transactions/{id} (suppression) - Validé
- [x] Test filtres et pagination - Validé
- [x] Test documentation Swagger accessible - Validé

**Acceptance Criteria**:
- [x] API démarre sans erreur
- [x] Endpoints répondent correctement
- [x] Documentation Swagger accessible
- [x] Test script exécutable et tous les tests passent
- [x] **Utilisateur confirme que l'API fonctionne** (validé après tests manuels)

**Impact Frontend**: 
- [x] Créer client API de base (`frontend/src/api/client.ts`)
- [x] Tester connexion API depuis frontend (fait dans Step 1.3)
- [x] Afficher message de connexion réussie dans le navigateur (fait dans Step 1.3)

---

### Step 1.3 : Frontend de base et routing
**Status**: ✅ COMPLÉTÉ  
**Description**: Créer la structure Next.js avec routing et layout du dashboard.

**Tasks**:
- [x] Créer layout dashboard avec navigation onglets
- [x] Créer page dashboard principale
- [x] Configurer client API pour backend
- [x] Créer composants de base (Header, Navigation)
- [x] Tester connexion API depuis frontend
- [x] Corriger imports (alias @/*)
- [x] **Test visuel dans navigateur effectué**
- [x] **Validé par l'utilisateur** (dashboard fonctionnel, API connectée, 6 transactions affichées)

**Deliverables**:
- `frontend/app/dashboard/layout.tsx` - Layout avec onglets
- `frontend/app/dashboard/page.tsx` - Page principale
- `frontend/src/api/client.ts` - Client API
- `frontend/src/components/Header.tsx` - Header
- `frontend/src/components/Navigation.tsx` - Navigation onglets

**Tests**:
- [x] Test affichage dashboard dans navigateur (test visuel) - Validé
- [x] Test navigation entre onglets (test visuel) - Validé
- [x] Test connexion API depuis frontend (test visuel) - Validé (API Backend: Connecté)
- [x] Test affichage nombre de transactions (test visuel) - Validé (6 transactions)
- [x] Test structure fichiers (fichiers créés et importables) - Validé

**Acceptance Criteria**:
- [x] Dashboard s'affiche avec structure d'onglets - Validé
- [x] Navigation entre onglets fonctionne - Validé
- [x] Client API configuré et testé - Validé (connexion réussie)
- [x] **Utilisateur confirme que l'interface de base fonctionne** - Validé

**Impact Frontend**: 
- ✅ Dashboard visible avec onglets (Transactions, Pivot, Bilan, Amortissements, Cashflow) - Validé
- ✅ Navigation fonctionnelle - Validé
- ✅ Connexion API testée - Validé (statut "Connecté" affiché)
- ✅ Nombre de transactions affiché (6 transactions) - Validé

---

## Phase 2 : Fonctionnalité 1 - Chargement et visualisation des transactions

### Step 2.1.1 : Nettoyage BDD et création table file_imports
**Status**: ✅ COMPLÉTÉ  
**Description**: Nettoyer les transactions de test et créer la table pour tracker les fichiers déjà chargés (archive).

**Tasks**:
- [x] Créer modèle FileImport dans models.py
- [x] Mettre à jour schema.sql avec table file_imports
- [x] Créer script de nettoyage des transactions de test
- [x] **Créer test pour vérifier BDD propre**
- [x] **Valider avec l'utilisateur**

**Deliverables**:
- `backend/database/models.py` - Modèle FileImport ajouté
- `backend/database/schema.sql` - Table file_imports ajoutée
- `backend/scripts/cleanup_test_data.py` - Script de nettoyage
- `backend/tests/test_cleanup_and_file_imports.py` - Tests de vérification

**Tests**:
- [x] Test création table file_imports
- [x] Test nettoyage transactions de test
- [x] Test vérification BDD vide (0 transactions)

**Acceptance Criteria**:
- [x] Table file_imports créée avec colonnes : id, filename (unique), imported_at, imported_count, duplicates_count, errors_count, period_start, period_end
- [x] Transactions de test supprimées de la BDD (6 transactions supprimées)
- [x] BDD contient 0 transactions
- [x] Test script exécutable et tous les tests passent
- [x] **Utilisateur confirme que la BDD est propre**

---

### Step 2.1.2 : Frontend - Sous-onglets Transactions et "Load Trades"
**Status**: ✅ COMPLÉTÉ  
**Description**: Créer la structure avec sous-onglets dans l'onglet Transactions, avec un onglet dédié "Load Trades" pour l'upload de fichiers CSV.

**Tasks**:
- [x] Créer composant FileUpload.tsx
  - [x] Input file pour sélectionner CSV
  - [x] Bouton "Load Trades"
  - [x] Affichage nom fichier sélectionné
  - [x] Gestion état fichier sélectionné
- [x] Ajouter "Load Trades" dans Navigation.tsx (sous-onglets existants)
- [x] Intégrer FileUpload dans sous-onglet "Load Trades"
- [x] Page transactions utilise query params pour afficher contenu selon onglet
- [x] **Test visuel dans navigateur effectué**
- [x] **Validé par l'utilisateur**

**Deliverables**:
- `frontend/src/components/FileUpload.tsx` - Composant upload (sélection fichier uniquement)
- `frontend/app/dashboard/transactions/page.tsx` - Page transactions avec gestion query params
- `frontend/src/components/Navigation.tsx` - Sous-onglets mis à jour avec "Load Trades"
- `frontend/src/api/client.ts` - Préparé pour futures fonctions API

**Tests**:
- [x] Test affichage 4 sous-onglets horizontaux (dans Navigation.tsx)
- [x] Test navigation entre sous-onglets
- [x] Test affichage bouton "Load Trades" dans sous-onglet "Load Trades"
- [x] Test sélection fichier CSV
- [x] Test affichage nom fichier sélectionné

**Acceptance Criteria**:
- [x] 4 sous-onglets visibles : "Toutes les transactions", "Non classées", "À valider", "Load Trades"
- [x] Navigation entre sous-onglets fonctionne
- [x] Bouton "Load Trades" visible uniquement dans sous-onglet "Load Trades"
- [x] Sélection fichier fonctionne
- [x] Nom fichier sélectionné affiché
- [x] **Utilisateur confirme que la structure fonctionne** (test visuel navigateur)

**Note**: Les onglets "Toutes les transactions", "Non classées" et "À valider" seront implémentés plus tard (après enrichissement).

---

### Step 2.1.3 : Backend - Détection colonnes et validation CSV
**Status**: ✅ COMPLÉTÉ  
**Description**: Créer les fonctions backend pour lire CSV, détecter colonnes, valider données.

**Tasks**:
- [x] Créer csv_utils.py avec fonctions :
  - [x] read_csv_safely() - Détection encodage/séparateur (UTF-8, Latin-1, ISO-8859-1, CP1252)
  - [x] detect_column_mapping() - Détection intelligente mapping colonnes fichier → BDD
  - [x] validate_transactions() - Validation dates (DD/MM/YYYY), montants numériques, noms
  - [x] preview_transactions() - Retourner premières lignes pour aperçu
- [x] **Créer test unitaire pour chaque fonction**
- [x] **Valider avec l'utilisateur**

**Deliverables**:
- `backend/api/utils/csv_utils.py` - Utilitaires CSV
- `backend/api/utils/__init__.py` - Package utils
- `backend/tests/test_csv_utils.py` - Tests unitaires (8 tests, tous passés)

**Tests**:
- [x] Test détection encodage (UTF-8, Latin-1)
- [x] Test détection séparateur (; ,)
- [x] Test détection mapping colonnes (Date→date, amount→quantite, name→nom)
- [x] Test détection mapping avec variantes (Montant, Libellé)
- [x] Test détection fichiers sans en-tête (par contenu)
- [x] Test validation dates DD/MM/YYYY
- [x] Test validation montants numériques (avec virgule)
- [x] Test validation noms (non vides)
- [x] Test preview premières lignes

**Acceptance Criteria**:
- [x] Détection encodage/séparateur automatique fonctionne
- [x] Détection mapping colonnes intelligente fonctionne (avec variantes)
- [x] Validation des données fonctionne (dates, montants, noms)
- [x] Preview retourne premières lignes correctement
- [x] Test script exécutable et tous les tests passent (8/8)
- [x] **Utilisateur confirme que les utilitaires fonctionnent**

---

### Step 2.1.4 : Backend - Endpoints API preview et import
**Status**: ✅ COMPLÉTÉ  
**Description**: Créer endpoints API pour preview (analyse fichier) et import (chargement BDD). **MODIFICATION**: Le solde sera calculé automatiquement, plus besoin de l'importer.

**Tasks**:
- [x] Créer endpoint POST /api/transactions/preview
  - [x] Recevoir fichier uploadé
  - [x] Lire CSV avec csv_utils
  - [x] Détecter mapping colonnes (intelligent)
  - [x] Valider données
  - [x] Retourner preview (premières lignes) + mapping proposé + stats
- [x] Créer endpoint POST /api/transactions/import
  - [x] Recevoir fichier + mapping confirmé par utilisateur
  - [x] Vérifier si fichier déjà chargé (table file_imports)
  - [x] Sauvegarder fichier dans backend/data/input/trades/ (archive)
  - [x] Détecter doublons (Date + Quantité + nom) dans BDD existante
  - [x] Insérer transactions (sans doublons)
  - [x] **Calculer solde automatiquement** (solde = solde précédent + quantité, solde initial = 0)
  - [x] Trier transactions par date avant insertion
  - [x] Calculer solde pour chaque transaction : solde = solde_précédent + quantité
  - [x] Solde initial = 0.0 (si aucune transaction en BDD)
  - [x] **Récupérer solde de la dernière transaction en BDD** (si transactions existantes)
  - [x] **Continuer le calcul du solde depuis le solde existant** (pour fichiers suivants)
  - [x] Ignorer colonne solde dans les fichiers CSV (ne plus la détecter/mapper)
  - [x] Enregistrer dans file_imports avec statistiques
  - [x] Retourner réponse avec stats (imported, duplicates, errors, period) + liste doublons
- [x] Créer endpoint GET /api/transactions/imports
  - [x] Lister historique des imports (file_imports)
- [x] **Créer test API complet**
- [x] **Valider avec l'utilisateur**

**Deliverables**:
- `backend/api/routes/transactions.py` - Endpoints preview et import ajoutés
- `backend/api/models.py` - Modèles Pydantic (FilePreviewResponse, FileImportResponse, ColumnMapping, DuplicateTransaction, FileImportHistory)
- `backend/tests/test_api_upload.py` - Tests API upload (5 tests, tous passés)

**Tests**:
- [x] Test POST /api/transactions/preview avec fichier CSV
- [x] Test détection mapping colonnes automatique
- [x] Test validation données
- [x] Test POST /api/transactions/import avec mapping confirmé
- [x] Test vérification fichier déjà chargé (ne pas re-processer)
- [x] Test sauvegarde fichier dans data/input/trades/
- [x] Test détection doublons (Date + Quantité + nom)
- [x] Test insertion en BDD sans doublons
- [x] Test enregistrement dans file_imports
- [x] Test réponse API avec statistiques + liste doublons
- [x] Test GET /api/transactions/imports (historique)
- [x] **Test calcul solde automatique** (solde initial = 0, solde = solde précédent + quantité)
- [ ] **Test calcul solde avec transactions existantes en BDD** (vérifier que le solde continue depuis la dernière transaction en BDD)

**Acceptance Criteria**:
- [x] Preview fonctionne et retourne mapping proposé + premières lignes
- [x] Import fonctionne avec mapping confirmé
- [x] Fichier sauvegardé dans data/input/trades/ (archive)
- [x] Fichier déjà chargé détecté et non re-processé
- [x] Doublons détectés même si transaction existe dans autre fichier
- [x] Liste des doublons retournée dans la réponse
- [x] Statistiques retournées correctement (imported, duplicates, errors, period)
- [x] **Solde calculé automatiquement** (solde initial = 0, solde = solde précédent + quantité)
- [x] **Colonne solde ignorée dans les fichiers** (mapping ne propose plus solde, détection désactivée)
- [x] **Transactions triées par date** avant calcul du solde
- [x] **Solde continue depuis transactions existantes en BDD** (récupère le solde de la dernière transaction et continue le calcul)
- [x] Test script exécutable et tous les tests passent (5/5 + test balance)
- [x] **Utilisateur confirme que les endpoints fonctionnent** (test via Swagger/Postman)

**Test à effectuer manuellement**:
- [ ] **Test avec transactions existantes en BDD** :
  - Créer quelques transactions en BDD (ex: 3 transactions avec solde final = 1000€)
  - Uploader un nouveau fichier avec des transactions à dates ultérieures
  - Vérifier que le solde de la première nouvelle transaction = 1000€ + quantité de cette transaction
  - Vérifier que les soldes suivants sont correctement cumulés

**Note importante**: 
- Le solde n'est plus importé depuis les fichiers CSV
- Le solde est calculé automatiquement lors de l'insertion : solde = solde précédent + quantité
- Solde initial = 0.0 (si aucune transaction en BDD)
- **Si transactions existantes en BDD** : le solde de la dernière transaction est récupéré et le calcul continue à partir de là
- Les transactions sont triées par date avant calcul du solde

**Test manuel à effectuer** :
- [ ] **Test cumul solde avec transactions existantes** :
  1. Créer quelques transactions en BDD (ex: 3 transactions avec solde final = 1000€)
  2. Uploader un nouveau fichier avec des transactions à dates ultérieures (ex: 2 transactions avec quantités +500€ et -200€)
  3. Vérifier que :
     - Le solde de la première nouvelle transaction = 1000€ + 500€ = 1500€
     - Le solde de la deuxième nouvelle transaction = 1500€ - 200€ = 1300€
  4. Vérifier que les soldes sont correctement cumulés dans l'ordre chronologique

---

### Step 2.1.5 : Frontend - Popup mapping et aperçu
**Status**: ✅ COMPLÉTÉ  
**Description**: Créer le popup de mapping des colonnes avec aperçu des données avant import.

**Tasks**:
- [x] Mettre à jour FileUpload.tsx
  - [x] Après sélection fichier, appeler POST /api/transactions/preview
  - [x] Ouvrir popup ColumnMappingModal avec résultats preview
- [x] Créer composant ColumnMappingModal.tsx
  - [x] Afficher mapping proposé (colonnes fichier → colonnes BDD)
  - [x] Permettre modification du mapping (dropdowns)
  - [x] Afficher aperçu premières lignes (tableau)
  - [x] Bouton "Confirmer" pour lancer l'import
  - [x] **Mapping limité à 3 colonnes** : date, quantite, nom (solde retiré)
- [x] Intégrer dans page transactions
- [x] **Test visuel dans navigateur effectué**
- [x] **Validé par l'utilisateur**

**Deliverables**:
- `frontend/src/components/FileUpload.tsx` - Mise à jour avec appel preview
- `frontend/src/components/ColumnMappingModal.tsx` - Popup mapping
- `frontend/src/api/client.ts` - Fonctions previewFile, importFile ajoutées

**Tests**:
- [x] Test sélection fichier CSV déclenche preview
- [x] Test appel preview API
- [x] Test affichage popup mapping après preview
- [x] Test modification mapping (dropdowns)
- [x] Test affichage aperçu premières lignes
- [x] Test confirmation import
- [x] Test mapping limité à 3 colonnes (date, quantite, nom)

**Acceptance Criteria**:
- [x] Après sélection fichier, preview automatique
- [x] Popup mapping s'affiche avec résultats preview
- [x] Mapping proposé automatiquement (modifiable)
- [x] Aperçu premières lignes affiché correctement
- [x] Modification mapping fonctionne
- [x] **Mapping limité à 3 colonnes** : date, quantite, nom (pas de solde)
- [x] **Utilisateur confirme que le popup mapping fonctionne** (test avec fichier réel)

---

### Step 2.1.6 : Frontend - Import et affichage résultats
**Status**: ✅ COMPLÉTÉ  
**Description**: Gérer l'import final, afficher résultats et liste des doublons. Ajout d'un onglet "Log" avec historique des imports et logs étape par étape.

**Tasks**:
- [x] Dans ColumnMappingModal, après confirmation :
  - [x] Appeler POST /api/transactions/import avec mapping
  - [x] Afficher loading pendant import
  - [x] Afficher résultats (statistiques : imported, duplicates, errors)
  - [x] Afficher liste des doublons détectés (si présents)
  - [x] Afficher message d'erreur si fichier déjà chargé
- [x] Recharger automatiquement liste transactions après import réussi
- [x] Créer système de logging étape par étape (ImportLogContext)
- [x] Créer composant ImportLog avec historique des imports
- [x] Ajouter onglet "Log" dans Navigation
- [x] Afficher logs détaillés étape par étape (fichier sélectionné, parsing, import, doublons)
- [x] Auto-refresh des logs toutes les 2-3 secondes si import en cours
- [x] Afficher chaque doublon individuellement dans les logs
- [x] **Test visuel dans navigateur effectué**
- [x] **Validé par l'utilisateur**

**Deliverables**:
- `frontend/src/components/ColumnMappingModal.tsx` - Gestion import et résultats avec logs
- `frontend/src/components/ImportLog.tsx` - Composant historique et logs détaillés
- `frontend/src/contexts/ImportLogContext.tsx` - Contexte React pour logs étape par étape
- `frontend/app/dashboard/layout.tsx` - Ajout ImportLogProvider
- `frontend/src/components/Navigation.tsx` - Ajout onglet "Log"
- `frontend/src/api/client.ts` - Ajout getImportsHistory()

**Tests**:
- [x] Test appel import API avec mapping
- [x] Test affichage loading pendant import
- [x] Test affichage résultats (imported, duplicates, errors)
- [x] Test affichage liste doublons (chaque doublon individuellement)
- [x] Test message erreur si fichier déjà chargé
- [x] Test rechargement automatique liste transactions après import
- [x] Test affichage historique des imports depuis BDD
- [x] Test logs étape par étape (Étape 1: Fichier sélectionné, Étape 2: Analyse, Étape 3: Import)
- [x] Test auto-refresh des logs pendant import en cours

**Acceptance Criteria**:
- [x] Import fonctionne depuis interface
- [x] Résultats affichés correctement (statistiques)
- [x] Liste des doublons affichée si présents (chaque doublon avec détails)
- [x] Message d'erreur si fichier déjà chargé
- [x] Liste transactions rechargée automatiquement après import réussi
- [x] Onglet "Log" affiche historique des imports (mémoire + BDD)
- [x] Logs étape par étape compréhensibles (pas trop techniques)
- [x] Auto-refresh des logs toutes les 2-3 secondes si import en cours et ligne sélectionnée
- [x] **Utilisateur confirme que l'import et les logs fonctionnent** (test avec fichier réel)

---

### Step 2.1.6 (bis) : Frontend - Visualisation transactions et suppression
**Status**: ✅ COMPLÉTÉ  
**Description**: Afficher les transactions dans un tableau avec possibilité de supprimer (pour gérer doublons).

**Tasks**:
- [x] Créer composant TransactionsTable.tsx
  - [x] Tableau avec colonnes : Date, Quantité, Nom, Solde
  - [x] Format date DD/MM/YYYY pour affichage
  - [x] Format montants avec 2 décimales (format EUR français)
  - [x] Tri par colonnes (clic sur en-tête)
  - [x] Pagination (25, 50, 100, 200 par page)
  - [x] Bouton "Supprimer" pour chaque transaction avec confirmation
- [x] Intégrer dans page transactions (onglet "Toutes les transactions")
- [x] Appeler API GET /api/transactions
- [x] Appeler API DELETE /api/transactions/{id} pour suppression
- [x] Implémenter filtrage par date (date début et date fin)
- [x] Implémenter recherche par nom (avec debounce)
- [x] **Créer test visuel dans navigateur**
- [x] **Validé par l'utilisateur**

**Deliverables**:
- `frontend/src/components/TransactionsTable.tsx` - Tableau transactions avec suppression
- `frontend/app/dashboard/transactions/page.tsx` - Page complète avec tableau intégré
- `frontend/src/api/client.ts` - Fonction delete() déjà disponible

**Tests**:
- [x] Test affichage transactions dans tableau
- [x] Test format date DD/MM/YYYY
- [x] Test format montants (EUR avec 2 décimales)
- [x] Test tri par colonnes (asc/desc)
- [x] Test pagination (navigation et changement taille page)
- [x] Test suppression transaction (avec confirmation)
- [x] Test rechargement après suppression
- [x] Test filtrage par date (date début et fin)
- [x] Test recherche par nom (debounce 300ms)

**Acceptance Criteria**:
- [x] Tableau des transactions s'affiche avec toutes les colonnes
- [x] Dates affichées en format DD/MM/YYYY
- [x] Montants formatés correctement (format EUR français)
- [x] Tri par colonnes fonctionnel (clic sur en-tête)
- [x] Pagination fonctionnelle (navigation et sélection taille page)
- [x] Bouton suppression fonctionne pour chaque transaction (avec confirmation)
- [x] Transactions chargées depuis BDD s'affichent correctement
- [x] Filtrage par date fonctionnel
- [x] Recherche par nom fonctionnelle
- [x] **Utilisateur confirme que la visualisation et suppression fonctionnent** (test avec données réelles)

**Impact Frontend**: 
- ✅ Onglet Transactions fonctionnel
- ✅ Upload CSV visible et testé
- ✅ Tableau transactions avec toutes les colonnes
- ✅ Filtrage et recherche opérationnels

---

### Step 2.1.7 : Backend - Recalcul automatique des soldes et améliorations
**Status**: ✅ COMPLÉTÉ  
**Description**: Amélioration de la gestion des transactions avec recalcul automatique des soldes après modifications et gestion améliorée des fichiers déjà chargés.

**Tasks**:
- [x] Créer utilitaire `balance_utils.py` pour recalcul des soldes
  - [x] Fonction `recalculate_balances_from_date()` : recalcule depuis une date donnée
  - [x] Fonction `recalculate_all_balances()` : recalcule depuis le début
- [x] Modifier endpoint DELETE /api/transactions/{id}
  - [x] Recalculer les soldes des transactions suivantes après suppression
  - [x] Utiliser `recalculate_balances_from_date()` avec la date de la transaction supprimée
- [x] Modifier endpoint POST /api/transactions/import
  - [x] Changer comportement pour fichiers déjà chargés : warning au lieu d'erreur
  - [x] Permettre le traitement même si le fichier existe déjà
  - [x] Mettre à jour l'enregistrement `FileImport` existant au lieu de créer un nouveau
  - [x] Retourner un message d'avertissement dans la réponse
- [x] Modifier endpoint PUT /api/transactions/{transaction_id}
  - [x] Recalculer les soldes après modification d'une transaction
  - [x] Utiliser la date minimale (ancienne ou nouvelle) pour le recalcul
  - [x] Gérer correctement la conversion de date string en date object
- [x] **Créer test de recalcul des soldes**
- [x] **Valider avec l'utilisateur**

**Deliverables**:
- `backend/api/utils/balance_utils.py` - Utilitaires de recalcul des soldes
- `backend/api/routes/transactions.py` - Endpoints modifiés (DELETE, PUT, POST import)
- `frontend/src/components/ColumnMappingModal.tsx` - Gestion du warning pour fichiers déjà chargés

**Tests**:
- [x] Test recalcul des soldes après suppression d'une transaction
- [x] Test recalcul des soldes après modification d'une transaction (date, quantité, nom)
- [x] Test import d'un fichier déjà chargé (warning au lieu d'erreur)
- [x] Test mise à jour de FileImport existant lors de ré-import
- [x] Test recalcul avec changement de date (recalcul depuis date minimale)

**Acceptance Criteria**:
- [x] Suppression d'une transaction recalcule automatiquement les soldes suivants
- [x] Modification d'une transaction recalcule automatiquement les soldes (transaction modifiée + suivantes)
- [x] Import d'un fichier déjà chargé affiche un warning mais continue le traitement
- [x] Les doublons sont toujours détectés et affichés dans les logs
- [x] Les soldes restent cohérents après toutes les opérations (suppression, modification)
- [x] **Utilisateur confirme que le recalcul fonctionne correctement** (test avec données réelles)

---

### Step 2.1.8 : Frontend - Édition des transactions et sélection multiple
**Status**: ✅ COMPLÉTÉ  
**Description**: Ajout de la fonctionnalité d'édition inline des transactions et de sélection multiple pour suppression en masse.

**Tasks**:
- [x] Modifier composant `TransactionsTable.tsx` pour édition inline
  - [x] Ajouter bouton "✏️" dans colonne Actions pour chaque transaction
  - [x] Implémenter édition inline (comme dans MappingTable) :
    - [x] Clic sur ✏️ → les champs Date, Nom, Quantité deviennent des inputs inline
    - [x] Le bouton ✏️ devient ✓ pour sauvegarder
    - [x] Ajouter bouton ✗ pour annuler l'édition
    - [x] Conversion format date pour input HTML (YYYY-MM-DD)
    - [x] Appeler API PUT /api/transactions/{id} pour sauvegarder
    - [x] Gestion d'erreurs avec messages clairs
    - [x] Recharger la liste après sauvegarde réussie
  - [x] Ajouter colonne checkbox à gauche de la colonne Date
  - [x] Ajouter checkbox "sélectionner tout" dans l'en-tête du tableau
  - [x] Gérer l'état de sélection (Set<number> pour les IDs sélectionnés)
  - [x] Mise en évidence visuelle des lignes sélectionnées (fond bleu clair)
  - [x] Afficher compteur de transactions sélectionnées
  - [x] Ajouter bouton "Supprimer X" pour suppression multiple
  - [x] Implémenter suppression multiple (appels API en parallèle)
  - [x] Réinitialiser sélection après suppression ou changement de page
- [x] Améliorer gestion d'erreurs dans `client.ts`
  - [x] Détection spécifique de l'erreur "Failed to fetch"
  - [x] Messages d'erreur plus clairs pour l'utilisateur
  - [x] Logs détaillés pour le diagnostic
- [x] **Créer test visuel dans navigateur**
- [x] **Valider avec l'utilisateur**

**Deliverables**:
- `frontend/src/components/TransactionsTable.tsx` - Tableau avec édition inline et sélection multiple
- `frontend/src/api/client.ts` - Amélioration gestion d'erreurs

**Tests**:
- [x] Test ouverture édition inline (clic sur bouton ✏️)
- [x] Test affichage des inputs inline pour Date, Nom, Quantité
- [x] Test conversion format date (YYYY-MM-DD pour input)
- [x] Test sauvegarde d'une transaction modifiée (clic sur ✓)
- [x] Test annulation de l'édition (clic sur ✗)
- [x] Test rechargement de la liste après édition
- [x] Test recalcul des soldes après édition (vérification visuelle)
- [x] Test sélection/désélection d'une transaction (checkbox)
- [x] Test sélection/désélection de toutes les transactions (checkbox en-tête)
- [x] Test affichage compteur de sélection
- [x] Test suppression multiple (plusieurs transactions sélectionnées)
- [x] Test réinitialisation de la sélection après suppression
- [x] Test gestion d'erreurs (messages clairs au lieu de [object Object])

**Acceptance Criteria**:
- [x] Bouton "✏️" active l'édition inline (champs deviennent inputs)
- [x] Édition inline permet de modifier Date, Quantité et Nom directement dans le tableau
- [x] Bouton ✏️ devient ✓ pour sauvegarder, ✗ pour annuler
- [x] Sauvegarde met à jour la transaction et recharge la liste
- [x] Les soldes sont recalculés automatiquement après édition
- [x] Checkbox permet de sélectionner/désélectionner des transactions
- [x] Checkbox en-tête sélectionne/désélectionne toutes les transactions de la page
- [x] Lignes sélectionnées sont mises en évidence visuellement
- [x] Compteur affiche le nombre de transactions sélectionnées
- [x] Bouton "Supprimer X" supprime toutes les transactions sélectionnées
- [x] Confirmation demandée avant suppression multiple
- [x] Messages d'erreur sont clairs et compréhensibles
- [x] **Utilisateur confirme que l'édition et la sélection multiple fonctionnent** (test avec données réelles)

**Impact Frontend**: 
- ✅ Édition des transactions fonctionnelle
- ✅ Sélection multiple et suppression en masse opérationnelles
- ✅ Gestion d'erreurs améliorée
- ✅ Interface utilisateur plus intuitive

---

### Step 2.1.9 : Amélioration import CSV - Gestion erreurs et transactions sans nom
**Status**: ✅ COMPLÉTÉ  
**Description**: Amélioration de la gestion des erreurs d'import avec détails ligne par ligne, génération automatique de noms pour transactions sans nom, et correction de la détection de doublons.

**Tasks**:
- [x] Créer modèle `TransactionError` pour erreurs détaillées
  - [x] Numéro de ligne, date, quantité, nom, message d'erreur
- [x] Modifier `FileImportResponse` pour inclure liste d'erreurs détaillées
- [x] Modifier backend pour collecter toutes les erreurs avec détails
  - [x] Erreurs de validation (dates invalides, quantités invalides)
  - [x] Erreurs de traitement (exceptions lors du traitement)
  - [x] Chaque erreur avec numéro de ligne et contexte
- [x] Modifier frontend pour afficher erreurs détaillées ligne par ligne
  - [x] Affichage formaté avec tous les détails
  - [x] Limite à 100 erreurs pour ne pas surcharger
- [x] Gérer colonnes combinées lors de l'import
  - [x] Recréer colonnes combinées si nécessaire (ex: "Col5_combined")
  - [x] Détection automatique des colonnes à combiner
- [x] Génération automatique de noms pour transactions sans nom
  - [x] Générer "nom_a_justifier_N" si nom vide
  - [x] Compter les transactions existantes avec ce préfixe
- [x] Affichage visuel des transactions à justifier
  - [x] Nom en rouge avec emoji ⚠️ dans le tableau
  - [x] Police en gras pour ces transactions
- [x] Correction détection doublons pour transactions sans nom
  - [x] Vérifier doublons sur (Date + Quantité) uniquement si nom vide
  - [x] Éviter création de doublons lors du rechargement de fichiers
- [x] Correction bug import datetime
  - [x] Supprimer import local qui masquait l'import global
- [x] **Valider avec l'utilisateur**

**Deliverables**:
- `backend/api/models.py` - Ajout modèle `TransactionError`
- `backend/api/routes/transactions.py` - Amélioration gestion erreurs et doublons
- `frontend/src/components/ColumnMappingModal.tsx` - Affichage erreurs détaillées
- `frontend/src/components/TransactionsTable.tsx` - Affichage transactions à justifier

**Tests**:
- [x] Test affichage erreurs détaillées ligne par ligne
- [x] Test génération noms automatiques pour transactions sans nom
- [x] Test affichage visuel transactions à justifier (rouge + ⚠️)
- [x] Test détection doublons pour transactions sans nom
- [x] Test rechargement fichier avec transactions sans nom (pas de doublons)
- [x] Test colonnes combinées lors de l'import

**Acceptance Criteria**:
- [x] Toutes les erreurs sont affichées avec détails (ligne, date, quantité, nom, message)
- [x] Transactions sans nom génèrent automatiquement "nom_a_justifier_N"
- [x] Transactions à justifier affichées en rouge avec ⚠️ dans le tableau
- [x] Rechargement fichier ne crée pas de doublons pour transactions sans nom
- [x] Détection doublons fonctionne correctement (Date + Quantité pour noms vides)
- [x] Colonnes combinées recréées correctement lors de l'import
- [x] **Utilisateur confirme que toutes les fonctionnalités fonctionnent** (test avec fichiers réels)

**Impact Backend**: 
- ✅ Gestion erreurs améliorée avec détails complets
- ✅ Détection doublons plus robuste
- ✅ Génération automatique de noms pour transactions sans nom

**Impact Frontend**: 
- ✅ Affichage erreurs détaillées ligne par ligne
- ✅ Indicateur visuel pour transactions à justifier
- ✅ Meilleure expérience utilisateur pour le débogage

---

### Step 2.1.10 : Amélioration interface - Clear logs et recalcul soldes
**Status**: ✅ COMPLÉTÉ  
**Description**: Ajout d'un bouton pour supprimer l'historique des logs et correction du recalcul des soldes lors de l'import de fichiers dans un ordre non chronologique.

**Tasks**:
- [x] Ajouter bouton "Clear logs" dans l'onglet Load Trades
  - [x] Placement à droite de la carte "Transactions en BDD"
  - [x] Style rouge pour indiquer action de suppression
  - [x] Confirmation avant suppression
- [x] Implémenter suppression des logs
  - [x] Supprimer logs en mémoire (via ImportLogContext)
  - [x] ~~Masquer logs de la base de données dans l'affichage~~ (remplacé par suppression réelle)
  - [x] ~~État persistant pour empêcher le rechargement automatique~~ (remplacé par suppression réelle)
  - [x] **AMÉLIORATION** : Supprimer vraiment de la BDD via endpoint `DELETE /api/transactions/imports` (ajouté dans Step 3.7.9)
- [x] Correction recalcul des soldes après import
  - [x] Recalculer tous les soldes depuis le début après chaque import
  - [x] Garantir la cohérence même si transactions insérées à dates antérieures
  - [x] Utiliser `recalculate_all_balances()` après insertion
- [x] **Valider avec l'utilisateur**

**Deliverables**:
- `frontend/app/dashboard/transactions/page.tsx` - Bouton Clear logs
- `frontend/src/components/ImportLog.tsx` - Gestion masquage historique BDD (initialement)
- `backend/api/routes/transactions.py` - Recalcul complet des soldes après import
- **AMÉLIORATION** : `backend/api/routes/transactions.py` - Endpoint `DELETE /api/transactions/imports` pour suppression réelle (ajouté dans Step 3.7.9)

**Tests**:
- [x] Test bouton Clear logs (suppression logs mémoire)
- [x] Test masquage logs base de données après Clear logs
- [x] Test pas de rechargement automatique après Clear logs
- [x] Test import fichiers dans ordre non chronologique (2021, 2023, 2022)
- [x] Test recalcul correct des soldes après import dans ordre non chronologique

**Acceptance Criteria**:
- [x] Bouton "Clear logs" visible à droite de la carte "Transactions en BDD"
- [x] Clic sur "Clear logs" supprime tous les logs affichés (mémoire + BDD)
- [x] ~~Les logs de la base de données ne se rechargent plus après Clear logs~~ (remplacé par suppression réelle)
- [x] **AMÉLIORATION** : Les logs sont vraiment supprimés de la BDD et ne réapparaissent plus (ajouté dans Step 3.7.9)
- [x] Import de fichiers dans n'importe quel ordre chronologique fonctionne correctement
- [x] Les soldes sont toujours corrects après import, même si transactions insérées à dates antérieures
- [x] **Utilisateur confirme que toutes les fonctionnalités fonctionnent** (test avec fichiers réels)

**Impact Backend**: 
- ✅ Recalcul complet des soldes garantit la cohérence des données
- ✅ Support de l'import de fichiers dans n'importe quel ordre

**Impact Frontend**: 
- ✅ Bouton Clear logs pour nettoyer l'interface
- ✅ Meilleure gestion de l'historique des logs

---

## Phase 3 : Fonctionnalité 2 - Enrichissement et catégorisation

### Vue d'ensemble
**Objectif** : Enrichir automatiquement les transactions avec des classifications hiérarchiques (level 1, 2, 3) basées sur un système de mapping intelligent, permettant la catégorisation comptable des transactions.

**Migration depuis l'ancien système** :
- **Fichiers de référence** : `scripts/mapping.xlsx` et `scripts/2_add_extra_columns.py` servent de référence pour la migration
- **Après migration** : Ces fichiers peuvent être supprimés car toute la logique sera dans la nouvelle architecture (table `mappings` + `enrichment_service.py`)

**Architecture** :
- **Table `enriched_transactions`** : Stocke les classifications et métadonnées (annee, level_1, level_2, level_3) liées aux transactions via `transaction_id`
- **Table `mappings`** : Stocke les règles de mapping (nom → level_1, level_2, level_3) pour l'enrichissement automatique
- **Enrichissement automatique** : Après chaque import CSV, les transactions sont automatiquement enrichies via le mapping
- **Enrichissement manuel** : Possibilité de modifier les classifications directement sur les transactions, ce qui crée automatiquement de nouveaux mappings

**Fonctionnalités clés** :
1. Enrichissement automatique après import CSV
2. Mapping intelligent par préfixe (basé sur le script `2_add_extra_columns.py`)
3. Modification manuelle des classifications dans le tableau des transactions
4. Création automatique de mappings lors de modifications manuelles
5. Re-enrichissement en cascade lors de modification d'un mapping
6. Onglet "Non classées" pour les transactions sans classifications
7. Onglet "Mapping" pour gérer les règles de mapping

---

### Step 3.1 : Migration mappings depuis Excel vers DB
**Status**: ✅ COMPLÉTÉ  
**Description**: Migrer les mappings depuis `mapping.xlsx` vers la table `mappings` dans la base de données.

**Objectif** : Préparer les données de référence pour l'enrichissement. Backend uniquement, testable via script.

**Tasks**:
- [x] Créer script de migration `backend/scripts/migrate_mappings.py`
- [x] Lire `scripts/mapping.xlsx` avec pandas
- [x] Insérer les mappings dans la table `mappings` (nom, level_1, level_2, level_3)
- [x] Gérer les doublons (skip si mapping existe déjà)
- [x] Afficher statistiques de migration (nombre de mappings importés)
- [x] **Tester le script et valider avec l'utilisateur**

**Deliverables**:
- `backend/scripts/migrate_mappings.py` - Script de migration

**Tests**:
- [x] Script exécutable sans erreur
- [x] 88 mappings importés dans la table `mappings` (fichier mis à jour)
- [x] Vérification manuelle de quelques mappings dans la DB
- [x] Script idempotent (peut être exécuté plusieurs fois sans doublons)
- [x] Gestion des doublons dans le fichier Excel

**Acceptance Criteria**:
- [x] Script de migration fonctionne
- [x] Tous les mappings sont dans la table `mappings`
- [x] **Utilisateur confirme que les mappings sont corrects dans la DB**

---

### Step 3.2 : CRUD mappings backend + Interface frontend
**Status**: ✅ COMPLÉTÉ  
**Description**: Créer les endpoints API pour gérer les mappings ET l'interface frontend pour les visualiser.

**Objectif** : Permettre la gestion des mappings via API ET interface web. Backend + Frontend, testable visuellement.

**Tasks Backend**:
- [x] Créer `backend/api/routes/mappings.py`
- [x] Endpoint `GET /api/mappings` - Liste tous les mappings (avec pagination et recherche)
- [x] Endpoint `GET /api/mappings/{mapping_id}` - Détails d'un mapping
- [x] Endpoint `POST /api/mappings` - Créer un nouveau mapping
- [x] Endpoint `PUT /api/mappings/{mapping_id}` - Modifier un mapping
- [x] Endpoint `DELETE /api/mappings/{mapping_id}` - Supprimer un mapping
- [x] Créer modèles Pydantic pour les requêtes/réponses
- [x] Enregistrer la route dans `backend/api/main.py`

**Tasks Frontend**:
- [x] Créer `frontend/src/components/MappingTable.tsx` - Tableau pour afficher les mappings
- [x] Ajouter sous-onglet "Mapping" dans `frontend/app/dashboard/transactions/page.tsx`
- [x] Afficher tous les mappings (nom, level_1, level_2, level_3) dans un tableau
- [x] Permettre création, modification, suppression de mappings via interface
- [x] Édition inline des mappings
- [x] Recherche et pagination
- [x] Mise à jour `frontend/src/api/client.ts` - Ajout endpoints mappings
- [x] Ajout onglet "Mapping" dans Navigation
- [x] **Tester l'interface et valider avec l'utilisateur**

**Deliverables**:
- `backend/api/routes/mappings.py` - Endpoints CRUD mappings
- Mise à jour `backend/api/models.py` - Modèles Pydantic pour mappings
- Mise à jour `backend/api/main.py` - Enregistrement route mappings
- `frontend/src/components/MappingTable.tsx` - Composant gestion mappings
- Mise à jour `frontend/app/dashboard/transactions/page.tsx` - Ajout onglet Mapping
- Mise à jour `frontend/src/components/Navigation.tsx` - Ajout onglet Mapping
- Mise à jour `frontend/src/api/client.ts` - Interface API mappings

**Tests**:
- [x] Test GET /api/mappings (liste tous les mappings)
- [x] Test POST /api/mappings (création)
- [x] Test PUT /api/mappings/{id} (modification)
- [x] Test DELETE /api/mappings/{id} (suppression)
- [x] Test affichage mappings dans interface
- [x] Test création/modification/suppression via interface
- [x] Test recherche et pagination

**Acceptance Criteria**:
- [x] Tous les endpoints CRUD fonctionnent
- [x] Interface frontend affiche tous les mappings
- [x] CRUD complet fonctionne via interface web
- [x] **Utilisateur confirme que l'interface fonctionne et est intuitive**

---

### Step 3.3 : Service enrichissement backend + Enrichissement automatique après import + Affichage dans tableau
**Status**: ✅ COMPLÉTÉ  
**Description**: Créer le service d'enrichissement, l'intégrer dans l'import CSV, et afficher les classifications dans le tableau.

**Objectif** : Implémenter l'enrichissement complet et le rendre visible immédiatement. Backend + Frontend, testable visuellement après import CSV.

**Tasks Backend**:
- [x] Créer `backend/api/services/enrichment_service.py`
- [x] Implémenter fonction `find_best_mapping(transaction_name, mappings)` avec logique :
  - Recherche par préfixe le plus long
  - Matching "smart" par pattern/contient (si le nom de la transaction contient le nom du mapping)
  - Cas spéciaux PRLV SEPA et VIR STRIPE
- [x] Implémenter fonction `enrich_transaction(transaction, db)` :
  - Calculer `annee` depuis `transaction.date`
  - Calculer `mois` depuis `transaction.date`
  - Trouver le meilleur mapping
  - Créer/update ligne `enriched_transaction` avec level_1/2/3 (ou NULL si pas de mapping)
- [x] Modifier `backend/api/routes/transactions.py` - Endpoint `POST /api/transactions/import`
  - Après insertion des transactions, appeler `enrich_transaction` pour chaque transaction
  - Optimisation : charger les mappings une seule fois pour toutes les transactions
- [x] Modifier `backend/api/routes/transactions.py` - Endpoint `GET /api/transactions` pour inclure les données enrichies
- [x] Modifier `backend/api/models.py` - `TransactionResponse` pour inclure level_1/2/3

**Tasks Frontend**:
- [x] Modifier `frontend/src/components/TransactionsTable.tsx` :
  - Ajouter colonnes level_1, level_2, level_3 (entre Solde et Actions)
  - Afficher "à remplir" en italique gris si level_1/2/3 = NULL
- [x] Mise à jour `frontend/src/api/client.ts` - Interface Transaction pour inclure level_1/2/3
- [x] **Tester avec import CSV réel et valider visuellement avec l'utilisateur**

**Deliverables**:
- `backend/api/services/enrichment_service.py` - Service enrichissement
- Mise à jour `backend/api/routes/transactions.py` - Intégration enrichissement après import + GET avec données enrichies
- Mise à jour `backend/api/models.py` - TransactionResponse avec level_1/2/3
- Mise à jour `frontend/src/components/TransactionsTable.tsx` - Colonnes level_1/2/3
- Mise à jour `frontend/src/api/client.ts` - Interface Transaction avec level_1/2/3

**Tests**:
- [x] Test mapping par préfixe (préfixe le plus long)
- [x] Test matching "smart" (pattern/contient)
- [x] Test cas spéciaux (PRLV SEPA, VIR STRIPE)
- [x] Test enrichissement automatique après import CSV
- [x] Test création `enriched_transaction` pour chaque transaction
- [x] Test transactions avec mapping (level_1/2/3 appliqués)
- [x] Test transactions sans mapping (level_1/2/3 = NULL)
- [x] Colonnes level_1/2/3 visibles dans le tableau après import
- [x] Affichage correct des classifications (ou "à remplir" si NULL)

**Acceptance Criteria**:
- [x] Logique de matching fonctionne correctement
- [x] Enrichissement automatique fonctionne après chaque import CSV
- [x] Colonnes level_1, level_2, level_3 visibles dans tableau "Toutes les transactions" (entre Solde et Actions)
- [x] Affichage correct des classifications après import
- [x] Transactions sans mapping affichent "à remplir" en italique gris
- [x] **Utilisateur confirme que l'enrichissement fonctionne et est visible après import CSV réel**

---

### Step 3.4 : Édition inline classifications + création mapping automatique + Dropdowns intelligents
**Status**: ✅ COMPLÉTÉ  
**Description**: Permettre l'édition inline des classifications avec dropdowns intelligents et création automatique de mappings.

**Objectif** : Modifier les classifications directement dans le tableau avec une UX optimale. Backend + Frontend, testable.

**Tasks Backend**:
- [x] Créer endpoint `PUT /api/enrichment/transactions/{transaction_id}` pour modifier classifications
- [x] Implémenter logique de création automatique de mapping :
  - Si mapping existe avec le nom → update le mapping
  - Si mapping n'existe pas → créer nouveau mapping
  - Récupération des valeurs existantes si seulement level_1, level_2 ou level_3 est modifié
- [x] Créer endpoint `GET /api/mappings/combinations` pour obtenir toutes les combinaisons possibles
  - Support paramètres `all_level_2` et `all_level_3` pour retourner toutes les valeurs sans filtre
- [x] Implémenter re-enrichissement lors de suppression de mapping (Step 3.6 partiel)
  - Trouver toutes les transactions qui utilisent le mapping supprimé
  - Re-enrichir ces transactions (elles seront remises à NULL si aucun autre mapping ne correspond)

**Tasks Frontend**:
- [x] Modifier `frontend/src/components/TransactionsTable.tsx` :
  - Édition inline des level_1/2/3 avec dropdowns intelligents
  - Filtrer level_2 selon level_1 sélectionné (si level_1 depuis dropdown)
  - Filtrer level_3 selon level_1 + level_2 sélectionnés (si level_1 et level_2 depuis dropdown)
  - Mode "Nouveau..." pour saisie libre avec chargement de toutes les valeurs disponibles
  - Chargement automatique de toutes les valeurs pour les niveaux suivants en mode custom
  - Conservation de level_3 lors du changement de level_1 ou level_2
  - Appel API pour sauvegarder les modifications
- [x] Mise à jour `frontend/src/api/client.ts` - Endpoints pour édition et combinations
- [x] Ajout sélection multiple dans `frontend/src/components/MappingTable.tsx` :
  - Checkbox dans l'en-tête pour sélectionner/désélectionner tout
  - Checkbox dans chaque ligne
  - Bouton de suppression multiple avec compteur
  - Mise en surbrillance des lignes sélectionnées
- [x] Ajout sélecteur "Par page" dans `frontend/src/components/MappingTable.tsx` :
  - Options : 25, 50, 100, 200
  - Réinitialisation à la page 1 lors du changement
- [x] **Tester l'édition avec dropdowns et valider avec l'utilisateur**

**Deliverables**:
- Mise à jour `backend/api/routes/enrichment.py` - Endpoint PUT pour modifier classifications
- Mise à jour `backend/api/services/enrichment_service.py` - Logique création mapping automatique + fonctions `update_transaction_classification` et `create_or_update_mapping_from_classification`
- Mise à jour `backend/api/routes/mappings.py` - Endpoint GET combinations + re-enrichissement lors de suppression
- Mise à jour `backend/api/main.py` - Inclusion du router enrichment
- Mise à jour `frontend/src/components/TransactionsTable.tsx` - Édition inline avec dropdowns intelligents
- Mise à jour `frontend/src/components/MappingTable.tsx` - Sélection multiple + sélecteur "Par page"
- Mise à jour `frontend/src/api/client.ts` - Endpoints édition et combinations

**Tests**:
- [x] Test modification classification inline
- [x] Test création automatique de mapping lors de modification
- [x] Test update de mapping existant lors de modification
- [x] Test filtrage level_2 selon level_1 (mode dropdown)
- [x] Test filtrage level_3 selon level_1 + level_2 (mode dropdown)
- [x] Test mode "Nouveau..." avec chargement de toutes les valeurs disponibles
- [x] Test conservation de level_3 lors du changement de level_1 ou level_2
- [x] Test sauvegarde persistante dans DB
- [x] Test re-enrichissement lors de suppression de mapping

**Acceptance Criteria**:
- [x] Édition inline des classifications fonctionne
- [x] Dropdowns intelligents fonctionnent (filtrage dynamique selon hiérarchie)
- [x] Mode "Nouveau..." permet la saisie libre avec toutes les valeurs disponibles
- [x] Création automatique de mapping fonctionne (même si seulement level_1, level_2 ou level_3 est modifié)
- [x] Modifications persistées dans DB
- [x] Re-enrichissement automatique lors de suppression de mapping
- [x] Sélection multiple fonctionne dans l'onglet Mapping
- [x] Sélecteur "Par page" fonctionne dans l'onglet Mapping
- [x] **Utilisateur confirme que l'édition avec dropdowns est intuitive**

---

### Step 3.5 : Onglet Non classées
**Status**: ⏸️ EN ATTENTE  
**Description**: Créer l'onglet "Non classées" pour afficher et éditer les transactions sans classifications.

**Objectif** : Faciliter le travail sur les transactions non mappées. Frontend, testable.

**Tasks**:
- [ ] Créer `frontend/src/components/UnclassifiedTransactionsTable.tsx`
- [ ] Ajouter sous-onglet "Non classées" dans `frontend/app/dashboard/transactions/page.tsx`
- [ ] Filtrer uniquement les transactions avec level_1/2/3 = NULL
- [ ] Permettre édition des classifications depuis cet onglet (avec dropdowns intelligents)
- [ ] **Tester l'interface et valider avec l'utilisateur**

**Deliverables**:
- `frontend/src/components/UnclassifiedTransactionsTable.tsx` - Composant transactions non classées
- Mise à jour `frontend/app/dashboard/transactions/page.tsx` - Ajout onglet Non classées

**Tests**:
- [ ] Affichage uniquement transactions avec level_1/2/3 = NULL
- [ ] Édition depuis cet onglet fonctionne
- [ ] Transactions disparaissent de l'onglet après classification

**Acceptance Criteria**:
- [ ] Onglet "Non classées" fonctionne
- [ ] Affichage correct des transactions non classées
- [ ] Édition fonctionne depuis cet onglet
- [ ] **Utilisateur confirme que l'onglet est utile**

---

### Step 3.6 : Re-enrichissement en cascade
**Status**: ⏸️ EN ATTENTE  
**Description**: Implémenter le re-enrichissement en cascade lors de modification/suppression d'un mapping.

**Objectif** : Maintenir la cohérence entre mappings et transactions. Backend + frontend, testable.

**Tasks Backend**:
- [ ] Modifier `backend/api/routes/mappings.py` :
  - Lors de modification mapping → re-enrichir toutes les transactions qui l'utilisent
  - Lors de suppression mapping → remettre toutes les transactions à NULL
- [ ] Créer endpoint `POST /api/enrichment/re-enrich` pour re-enrichir toutes les transactions

**Tasks Frontend**:
- [ ] Ajouter bouton "Re-enrichir toutes les transactions" dans onglet Mapping
- [ ] **Tester le re-enrichissement et valider avec l'utilisateur**

**Deliverables**:
- Mise à jour `backend/api/routes/mappings.py` - Re-enrichissement en cascade
- Mise à jour `backend/api/routes/enrichment.py` - Endpoint re-enrichissement
- Mise à jour `frontend/src/components/MappingTable.tsx` - Bouton re-enrichissement

**Tests**:
- [ ] Test modification mapping → update toutes transactions concernées
- [ ] Test suppression mapping → transactions remises à NULL
- [ ] Test bouton re-enrichissement manuel

**Acceptance Criteria**:
- [ ] Re-enrichissement en cascade fonctionne
- [ ] Cohérence maintenue entre mappings et transactions
- [ ] **Utilisateur confirme que le re-enrichissement fonctionne**

---

### Step 3.7 : Import de mappings depuis fichier Excel
**Status**: ✅ COMPLÉTÉ  
**Description**: Permettre l'import de mappings depuis des fichiers Excel externes avec aperçu, logs et historique. **Même processus que "Load Trades" mais pour Excel et mappings.**

**Objectif** : Faciliter l'ajout en masse de mappings depuis des fichiers Excel. Backend + Frontend, testable étape par étape.

---

#### Step 3.7.1 : Backend - Modèle MappingImport et table mapping_imports
**Status**: ✅ COMPLÉTÉ  
**Description**: Créer le modèle et la table pour historiser les imports de mappings (identique à `file_imports`).

**Tasks**:
- [x] Créer modèle `MappingImport` dans `backend/database/models.py`
  - Colonnes : id, filename, imported_at, imported_count, duplicates_count, errors_count, created_at, updated_at
  - Index sur filename et imported_at
- [x] Mettre à jour `backend/database/schema.sql` avec la table `mapping_imports`
- [x] **Tester la création de la table et valider avec l'utilisateur**

**Deliverables**:
- Mise à jour `backend/database/models.py` - Modèle `MappingImport`
- Mise à jour `backend/database/schema.sql` - Table `mapping_imports`
- `backend/tests/test_mapping_imports_table.py` - Tests de validation

**Acceptance Criteria**:
- [x] Table `mapping_imports` créée dans la base de données
- [x] Modèle SQLAlchemy fonctionnel
- [x] Test script exécutable et tous les tests passent
- [x] **Utilisateur confirme que la table est créée correctement**

---

#### Step 3.7.2 : Backend - Endpoint preview mappings (POST /api/mappings/preview)
**Status**: ✅ COMPLÉTÉ  
**Description**: Créer l'endpoint pour prévisualiser un fichier Excel de mappings (identique à `/api/transactions/preview`).

**Tasks**:
- [x] Créer fonction `detect_mapping_columns(df)` pour détecter automatiquement les colonnes (nom, level_1, level_2, level_3)
- [x] Créer endpoint `POST /api/mappings/preview` dans `backend/api/routes/mappings.py`
  - Parser le fichier Excel (pandas.read_excel)
  - Détecter automatiquement les colonnes
  - Créer preview des premières lignes (max 10)
  - Validation basique (vérifier que nom, level_1, level_2 sont détectés)
  - Retourner `MappingPreviewResponse`
- [x] Créer modèle Pydantic `MappingPreviewResponse` dans `backend/api/models.py`
  - filename, total_rows, column_mapping, preview, validation_errors, stats
- [x] **Tester l'endpoint avec un fichier Excel et valider avec l'utilisateur**

**Deliverables**:
- Fonction `detect_mapping_columns` dans `backend/api/routes/mappings.py`
- Endpoint `POST /api/mappings/preview` dans `backend/api/routes/mappings.py`
- Modèle `MappingPreviewResponse` dans `backend/api/models.py`
- `backend/tests/test_mappings_preview.py` - Tests de validation
- Mise à jour `backend/requirements.txt` - Ajout pandas et openpyxl

**Acceptance Criteria**:
- [x] Endpoint répond correctement avec un fichier Excel
- [x] Détection automatique des colonnes fonctionne
- [x] Preview des données affiché
- [x] Test script exécutable et tous les tests passent
- [x] **Utilisateur confirme que le preview fonctionne**

---

#### Step 3.7.3 : Backend - Endpoint import mappings (POST /api/mappings/import)
**Status**: ✅ COMPLÉTÉ  
**Description**: Créer l'endpoint pour importer un fichier Excel de mappings (identique à `/api/transactions/import`).

**Tasks**:
- [x] Créer endpoint `POST /api/mappings/import` dans `backend/api/routes/mappings.py`
  - Parser le mapping des colonnes (JSON string)
  - Lire le fichier Excel
  - Valider les données (nom, level_1, level_2 obligatoires)
  - Gérer les doublons (ignorer si mapping existe déjà avec même nom)
  - Créer l'enregistrement `MappingImport` pour l'historique
  - Retourner statistiques (importés, doublons, erreurs) + liste détaillée
- [x] Créer modèle Pydantic `MappingImportResponse` dans `backend/api/models.py`
  - filename, imported_count, duplicates_count, errors_count, duplicates, errors, message
- [x] Créer modèle Pydantic `MappingImportHistory` dans `backend/api/models.py`
- [x] **Tester l'import avec un fichier Excel et valider avec l'utilisateur**

**Deliverables**:
- Endpoint `POST /api/mappings/import` dans `backend/api/routes/mappings.py`
- Modèles `MappingImportResponse` et `MappingImportHistory` dans `backend/api/models.py`
- Modèles `MappingError` et `DuplicateMapping` dans `backend/api/models.py`
- `backend/tests/test_mappings_import.py` - Tests de validation

**Acceptance Criteria**:
- [x] Import crée les mappings dans la base de données
- [x] Doublons ignorés (pas de mise à jour)
- [x] Erreurs détectées et listées ligne par ligne
- [x] Historique créé dans `mapping_imports`
- [x] Test script exécutable et tous les tests passent
- [x] **Utilisateur confirme que l'import fonctionne**

---

#### Step 3.7.4 : Backend - Endpoints historique et count (GET /api/mappings/imports, DELETE, GET /api/mappings/count)
**Status**: ✅ COMPLÉTÉ  
**Description**: Créer les endpoints pour l'historique et le compteur (identiques aux endpoints transactions).

**Tasks**:
- [x] Créer endpoint `GET /api/mappings/imports` pour récupérer l'historique
- [x] Créer endpoint `DELETE /api/mappings/imports/{import_id}` pour supprimer un import
- [x] Créer endpoint `GET /api/mappings/count` pour obtenir le nombre total de mappings
- [x] Créer endpoint `DELETE /api/mappings/imports` pour supprimer tous les imports (Clear logs)
- [x] **IMPORTANT** : Placer ces routes AVANT `/mappings/{mapping_id}` pour éviter les conflits de routing
- [x] **Tester les endpoints et valider avec l'utilisateur**

**Deliverables**:
- Endpoints dans `backend/api/routes/mappings.py`
- `backend/tests/test_mappings_history_count.py` - Tests de validation

**Acceptance Criteria**:
- [x] Historique récupéré correctement
- [x] Suppression d'un import fonctionne
- [x] Suppression de tous les imports fonctionne
- [x] Compteur retourne le bon nombre
- [x] Pas de conflit de routing
- [x] Test script exécutable et tous les tests passent
- [x] **Utilisateur confirme que les endpoints fonctionnent**

---

#### Step 3.7.5 : Frontend - API client (endpoints mappings)
**Status**: ✅ COMPLÉTÉ  
**Description**: Ajouter les endpoints mappings dans l'API client (identique à `fileUploadAPI`).

**Tasks**:
- [x] Ajouter types TypeScript dans `frontend/src/api/client.ts` :
  - `MappingPreviewResponse`
  - `MappingImportResponse`
  - `MappingImportHistory`
  - `MappingError`
  - `DuplicateMapping`
- [x] Ajouter méthodes dans `mappingsAPI` :
  - `preview(file: File)` - Appel POST /api/mappings/preview
  - `import(file: File, mapping: ColumnMapping[])` - Appel POST /api/mappings/import
  - `getImportsHistory()` - Appel GET /api/mappings/imports
  - `deleteImport(importId: number)` - Appel DELETE /api/mappings/imports/{id}
  - `deleteAllImports()` - Appel DELETE /api/mappings/imports (Clear logs)
  - `getCount()` - Appel GET /api/mappings/count
- [x] **Tester les appels API et valider avec l'utilisateur**

**Deliverables**:
- Mise à jour `frontend/src/api/client.ts` - Types et méthodes mappings

**Acceptance Criteria**:
- [x] Tous les endpoints sont accessibles depuis le frontend
- [x] Types TypeScript corrects
- [x] Code compile sans erreur
- [x] **Utilisateur confirme que l'API client fonctionne**

---

#### Step 3.7.6 : Frontend - Composant MappingFileUpload
**Status**: ✅ COMPLÉTÉ  
**Description**: Créer le composant pour uploader un fichier Excel de mappings (identique à `FileUpload.tsx`).

**Tasks**:
- [x] Créer `frontend/src/components/MappingFileUpload.tsx`
  - Copier la structure de `FileUpload.tsx`
  - Modifier pour accepter `.xlsx` et `.xls` au lieu de `.csv`
  - Appeler `mappingsAPI.preview(file)` au lieu de `fileUploadAPI.preview(file)`
  - Ouvrir `MappingColumnMappingModal` au lieu de `ColumnMappingModal`
  - Bouton "📋 Load mapping" (même style que "📁 Load Trades")
- [x] **Tester le composant et valider avec l'utilisateur**

**Deliverables**:
- `frontend/src/components/MappingFileUpload.tsx`

**Acceptance Criteria**:
- [x] Bouton "Load mapping" visible et fonctionnel
- [x] Sélection de fichier Excel fonctionne
- [x] Preview appelé automatiquement
- [x] Modal s'ouvre avec les données
- [x] **Utilisateur confirme que le composant fonctionne**

---

#### Step 3.7.7 : Frontend - Composant MappingColumnMappingModal
**Status**: ✅ COMPLÉTÉ  
**Description**: Créer le modal pour mapper les colonnes et importer (identique à `ColumnMappingModal.tsx`).

**Tasks**:
- [x] Créer `frontend/src/components/MappingColumnMappingModal.tsx`
  - Copier la structure de `ColumnMappingModal.tsx`
  - Modifier les colonnes DB : `nom`, `level_1`, `level_2`, `level_3` (au lieu de date, quantite, nom)
  - Utiliser `mappingsAPI.import(file, mapping)` au lieu de `fileUploadAPI.import(file, mapping)`
  - Utiliser `useImportLog` pour les logs en temps réel (même système que transactions)
  - Afficher les logs détaillés (importés, doublons, erreurs ligne par ligne)
  - Validation : nom, level_1, level_2 obligatoires
- [x] **Tester le modal et valider avec l'utilisateur**

**Deliverables**:
- `frontend/src/components/MappingColumnMappingModal.tsx`

**Acceptance Criteria**:
- [x] Mapping des colonnes fonctionne (auto + manuel)
- [x] Aperçu des données affiché
- [x] Import fonctionne
- [x] Logs en temps réel affichés
- [x] **Utilisateur confirme que le modal fonctionne**

---

#### Step 3.7.8 : Frontend - Composant MappingImportLog
**Status**: ✅ COMPLÉTÉ  
**Description**: Créer le composant pour afficher l'historique des imports de mappings (identique à `ImportLog.tsx`).

**Tasks**:
- [x] Créer `frontend/src/components/MappingImportLog.tsx`
  - Copier la structure de `ImportLog.tsx`
  - Utiliser `mappingsAPI.getImportsHistory()` au lieu de `fileUploadAPI.getImportsHistory()`
  - Utiliser `mappingsAPI.getCount()` pour le compteur "X lignes de mapping"
  - Afficher l'historique (DB + mémoire via `useImportLog`)
  - Afficher les détails d'un import (doublons, erreurs ligne par ligne)
  - Bouton "Supprimer" pour chaque import
  - Refresh automatique si import en cours
  - Filtrer uniquement les logs Excel (.xlsx, .xls)
- [x] **Tester le composant et valider avec l'utilisateur**

**Deliverables**:
- `frontend/src/components/MappingImportLog.tsx`

**Acceptance Criteria**:
- [x] Historique affiché correctement
- [x] Compteur "X lignes de mapping" affiché
- [x] Détails d'un import affichés
- [x] Suppression d'un import fonctionne
- [x] **Utilisateur confirme que le composant fonctionne**

---

#### Step 3.7.9 : Frontend - Intégration dans page.tsx
**Status**: ✅ COMPLÉTÉ  
**Description**: Intégrer tous les composants dans la page transactions (identique à l'intégration Load Trades).

**Tasks**:
- [x] Modifier `frontend/app/dashboard/transactions/page.tsx` :
  - Ajouter état pour `mappingCount` et `isLoadingMappingCount`
  - Ajouter fonction `loadMappingCount()`
  - Dans l'onglet `load_trades` :
    - Ajouter compteur "X lignes de mapping" à côté de "Transactions en BDD" (même style)
    - Ajouter section séparée en dessous avec :
      - Titre "Import de mappings"
      - Composant `MappingFileUpload`
      - Texte explicatif (comme pour Load Trades)
      - Composant `MappingImportLog` (hideHeader=true)
  - Mettre à jour bouton "Clear logs" pour supprimer vraiment de la BDD (transactions + mappings)
- [x] **Tester l'intégration et valider avec l'utilisateur**

**Deliverables**:
- Mise à jour `frontend/app/dashboard/transactions/page.tsx`

**Acceptance Criteria**:
- [x] Compteur "X lignes de mapping" visible et fonctionnel
- [x] Section "Import de mappings" visible
- [x] Tous les composants fonctionnent ensemble
- [x] Bouton "Clear logs" supprime vraiment de la BDD
- [x] **Utilisateur confirme que l'intégration fonctionne**

---

#### Step 3.7.10 : Frontend - Renommage onglet "Load Trades/Mappings"
**Status**: ✅ COMPLÉTÉ  
**Description**: Renommer l'onglet pour refléter les deux fonctionnalités.

**Tasks**:
- [x] Modifier `frontend/src/components/Navigation.tsx`
  - Changer "Load Trades" en "Load Trades/Mappings"
- [x] **Tester et valider avec l'utilisateur**

**Deliverables**:
- Mise à jour `frontend/src/components/Navigation.tsx`

**Acceptance Criteria**:
- [x] Onglet renommé correctement
- [x] **Utilisateur confirme que le renommage est correct**

---

**Tests finaux**:
- [x] Test complet du workflow (upload → preview → import → historique)
- [x] Test avec différents formats Excel
- [x] Test gestion des doublons
- [x] Test logs détaillés
- [x] Test compteur
- [x] Test suppression de tous les imports (Clear logs)
- [x] **Utilisateur confirme que tout fonctionne comme "Load Trades"**

---

#### Step 3.7.11 : Améliorations - Re-enrichissement automatique des transactions
**Status**: ✅ COMPLÉTÉ  
**Description**: Améliorer le re-enrichissement automatique lors de la modification d'un mapping ou d'une transaction pour que toutes les transactions avec le même nom soient mises à jour.

**Problème identifié**:
- Quand on modifie un mapping, seules les transactions qui avaient exactement les mêmes level_1/2/3 étaient re-enrichies
- Quand on modifie une transaction, les autres transactions avec le même nom n'étaient pas re-enrichies
- Cas d'usage : plusieurs transactions avec le même nom (ex: facture d'électricité chaque mois) doivent toutes avoir le même mapping

**Tasks**:
- [x] Créer fonction utilitaire `transaction_matches_mapping_name()` dans `backend/api/services/enrichment_service.py`
  - Utilise la même logique que `find_best_mapping` pour vérifier si une transaction correspond à un nom de mapping
- [x] Améliorer endpoint `PUT /mappings/{mapping_id}` dans `backend/api/routes/mappings.py`
  - Trouver TOUTES les transactions dont le nom correspond au mapping (peu importe leurs level_1/2/3 actuels)
  - Re-enrichir toutes ces transactions après la mise à jour du mapping
- [x] Améliorer endpoint `PUT /enrichment/transactions/{id}` dans `backend/api/routes/enrichment.py`
  - Après la mise à jour du mapping, trouver toutes les transactions avec le même nom
  - Re-enrichir automatiquement toutes ces transactions
- [x] Améliorer gestion d'erreur 404 dans `frontend/src/components/MappingTable.tsx`
  - Détecter si le mapping n'existe plus et rafraîchir automatiquement la liste
- [x] Créer test `backend/tests/test_mapping_update_re_enrich.py`
  - Vérifie que toutes les transactions correspondantes sont re-enrichies (même celles non encore enrichies)
- [x] Créer test `backend/tests/test_transaction_update_re_enriches_others.py`
  - Vérifie que la modification d'une transaction re-enrichit toutes les autres avec le même nom

**Deliverables**:
- Fonction `transaction_matches_mapping_name()` dans `backend/api/services/enrichment_service.py`
- Mise à jour `PUT /mappings/{mapping_id}` dans `backend/api/routes/mappings.py`
- Mise à jour `PUT /enrichment/transactions/{id}` dans `backend/api/routes/enrichment.py`
- Amélioration gestion d'erreur dans `frontend/src/components/MappingTable.tsx`
- Tests `backend/tests/test_mapping_update_re_enrich.py` et `backend/tests/test_transaction_update_re_enriches_others.py`

**Acceptance Criteria**:
- [x] Modification d'un mapping → toutes les transactions correspondantes sont re-enrichies
- [x] Modification d'une transaction → toutes les autres transactions avec le même nom sont re-enrichies
- [x] Fonctionne même pour les transactions non encore enrichies
- [x] Tests passent avec succès
- [x] **Utilisateur confirme que le comportement est correct**

**Comportement final**:
- ✅ **Scénario 1** : Modifier une transaction → toutes les transactions avec le même nom sont automatiquement re-enrichies
- ✅ **Scénario 2** : Modifier un mapping → toutes les transactions correspondantes sont automatiquement re-enrichies (même celles non encore enrichies)

---

### Step 3.8 : Tri et filtres avancés pour TransactionsTable et MappingTable
**Status**: ⏸️ EN ATTENTE  
**Description**: Ajouter le tri par colonnes (cliquable sur tous les en-têtes) et une ligne de filtres auto (comme Excel) sous les en-têtes pour filtrer les données en temps réel. Ajouter aussi les contrôles de pagination en haut du tableau.

**Objectifs**:
- Tri cliquable sur toutes les colonnes (avec indicateur visuel ↑/↓)
- Ligne de filtres sous les en-têtes avec dropdown de valeurs uniques (comme Excel)
- Filtrage en temps réel (insensible à la casse, contient)
- Filtres combinables (AND entre colonnes)
- Pagination en haut + en bas du tableau
- Tri côté serveur pour gérer toutes les données (pas seulement la page courante)

---

#### Step 3.8.1 : Backend - Ajouter paramètres de tri aux endpoints
**Status**: ⏸️ EN ATTENTE  
**Description**: Ajouter les paramètres `sort_by` et `sort_direction` aux endpoints GET pour supporter le tri côté serveur.

**Tasks**:
- [ ] Modifier endpoint `GET /api/transactions` dans `backend/api/routes/transactions.py`
  - Ajouter paramètre `sort_by` (date, quantite, nom, solde, level_1, level_2, level_3)
  - Ajouter paramètre `sort_direction` (asc, desc)
  - Implémenter tri SQLAlchemy pour chaque colonne
- [ ] Modifier endpoint `GET /api/mappings` dans `backend/api/routes/mappings.py`
  - Ajouter paramètre `sort_by` (id, nom, level_1, level_2, level_3)
  - Ajouter paramètre `sort_direction` (asc, desc)
  - Implémenter tri SQLAlchemy pour chaque colonne
- [ ] Mettre à jour modèles Pydantic si nécessaire
- [ ] **Tester les endpoints avec différents paramètres de tri**

**Deliverables**:
- Mise à jour `backend/api/routes/transactions.py` - Paramètres de tri
- Mise à jour `backend/api/routes/mappings.py` - Paramètres de tri
- Tests backend pour vérifier le tri

**Acceptance Criteria**:
- [ ] Tri par date fonctionne (asc/desc)
- [ ] Tri par toutes les colonnes fonctionne
- [ ] Tri combiné avec pagination fonctionne
- [ ] Tests passent

---

#### Step 3.8.2 : Backend - Endpoints pour récupérer valeurs uniques (filtres)
**Status**: ⏸️ EN ATTENTE  
**Description**: Créer des endpoints pour récupérer les valeurs uniques de chaque colonne (pour les dropdowns de filtres).

**Tasks**:
- [ ] Créer endpoint `GET /api/transactions/unique-values` dans `backend/api/routes/transactions.py`
  - Paramètre `column` (nom, level_1, level_2, level_3, etc.)
  - Retourner liste des valeurs uniques (non null)
  - Optionnel : filtrer par date range si présent
- [ ] Créer endpoint `GET /api/mappings/unique-values` dans `backend/api/routes/mappings.py`
  - Paramètre `column` (nom, level_1, level_2, level_3)
  - Retourner liste des valeurs uniques (non null)
- [ ] **Tester les endpoints**

**Deliverables**:
- Endpoint `GET /api/transactions/unique-values` dans `backend/api/routes/transactions.py`
- Endpoint `GET /api/mappings/unique-values` dans `backend/api/routes/mappings.py`

**Acceptance Criteria**:
- [ ] Endpoints retournent les valeurs uniques correctes
- [ ] Filtrage par date range fonctionne (transactions)
- [ ] Tests passent

---

#### Step 3.8.3 : Frontend - API client - Méthodes tri et valeurs uniques
**Status**: ⏸️ EN ATTENTE  
**Description**: Ajouter les méthodes dans l'API client pour appeler les nouveaux endpoints.

**Tasks**:
- [ ] Mettre à jour `transactionsAPI.getAll()` dans `frontend/src/api/client.ts`
  - Ajouter paramètres `sortBy?: string` et `sortDirection?: 'asc' | 'desc'`
- [ ] Mettre à jour `mappingsAPI.list()` dans `frontend/src/api/client.ts`
  - Ajouter paramètres `sortBy?: string` et `sortDirection?: 'asc' | 'desc'`
- [ ] Ajouter méthode `transactionsAPI.getUniqueValues(column: string)` dans `frontend/src/api/client.ts`
- [ ] Ajouter méthode `mappingsAPI.getUniqueValues(column: string)` dans `frontend/src/api/client.ts`
- [ ] **Tester les appels API**

**Deliverables**:
- Mise à jour `frontend/src/api/client.ts` - Méthodes avec tri
- Méthodes `getUniqueValues` pour transactions et mappings

**Acceptance Criteria**:
- [ ] Méthodes ajoutées avec types TypeScript corrects
- [ ] Appels API fonctionnent

---

#### Step 3.8.4 : Frontend - TransactionsTable - Tri sur toutes les colonnes
**Status**: ⏸️ EN ATTENTE  
**Description**: Rendre toutes les colonnes triables avec indicateur visuel et tri côté serveur.

**Tasks**:
- [ ] Modifier `frontend/src/components/TransactionsTable.tsx`
  - Rendre tous les `<th>` cliquables (Date, Quantité, Nom, Solde, Level 1, Level 2, Level 3)
  - Ajouter indicateur visuel (↑/↓) sur la colonne triée
  - Modifier `handleSort()` pour gérer toutes les colonnes
  - Changer le tri pour utiliser l'API (côté serveur) au lieu du tri côté client
  - Passer `sortBy` et `sortDirection` à `transactionsAPI.getAll()`
- [ ] Ajouter état pour colonne triée et direction
- [ ] **Tester le tri sur chaque colonne**

**Deliverables**:
- Mise à jour `frontend/src/components/TransactionsTable.tsx` - Tri sur toutes les colonnes

**Acceptance Criteria**:
- [ ] Toutes les colonnes sont triables (cliquables)
- [ ] Indicateur visuel (↑/↓) affiché sur colonne triée
- [ ] Tri fonctionne côté serveur (toutes les données)
- [ ] Tri alternant asc/desc au clic
- [ ] **Utilisateur confirme que le tri fonctionne**

---

#### Step 3.8.5 : Frontend - TransactionsTable - Ligne de filtres auto
**Status**: ⏸️ EN ATTENTE  
**Description**: Ajouter une ligne de filtres sous les en-têtes avec champs texte et dropdowns de valeurs uniques (comme Excel).

**Tasks**:
- [ ] Modifier `frontend/src/components/TransactionsTable.tsx`
  - Ajouter ligne `<tr>` sous `<thead>` avec champs de filtre
  - Un champ par colonne filtrable (Date, Quantité, Nom, Solde, Level 1, Level 2, Level 3)
  - Chaque champ : input texte + dropdown avec valeurs uniques
  - Charger valeurs uniques via `transactionsAPI.getUniqueValues()` au montage
  - Implémenter filtrage en temps réel (insensible à la casse, contient)
  - Filtres combinables (AND entre colonnes)
  - Appliquer filtres côté serveur (modifier `transactionsAPI.getAll()` avec paramètres de filtre)
- [ ] Ajouter état pour chaque filtre
- [ ] Style similaire au filtre date existant
- [ ] **Tester le filtrage en temps réel**

**Deliverables**:
- Mise à jour `frontend/src/components/TransactionsTable.tsx` - Ligne de filtres

**Acceptance Criteria**:
- [ ] Ligne de filtres visible sous les en-têtes
- [ ] Champs texte fonctionnent (filtrage en temps réel)
- [ ] Dropdowns avec valeurs uniques fonctionnent
- [ ] Filtrage insensible à la casse
- [ ] Filtrage "contient" (partiel)
- [ ] Filtres combinables (AND)
- [ ] Filtres appliqués côté serveur (toutes les données)
- [ ] **Utilisateur confirme que les filtres fonctionnent**

---

#### Step 3.8.6 : Frontend - TransactionsTable - Pagination en haut
**Status**: ⏸️ EN ATTENTE  
**Description**: Ajouter les contrôles de pagination (Première, Précédente, Suivante, Dernière) et le sélecteur "Par page" (50/100/200) en haut du tableau.

**Tasks**:
- [ ] Modifier `frontend/src/components/TransactionsTable.tsx`
  - Dupliquer les contrôles de pagination existants (qui sont en bas)
  - Les placer en haut du tableau (avant `<table>`)
  - Inclure : "Première", "Précédente", "Suivante", "Dernière"
  - Inclure : Sélecteur "Par page: 50/100/200"
  - Inclure : Affichage "Page X sur Y"
  - Synchroniser les deux contrôles (haut et bas)
- [ ] **Tester la pagination en haut**

**Deliverables**:
- Mise à jour `frontend/src/components/TransactionsTable.tsx` - Pagination en haut

**Acceptance Criteria**:
- [ ] Contrôles de pagination visibles en haut
- [ ] Tous les boutons fonctionnent (Première, Précédente, Suivante, Dernière)
- [ ] Sélecteur "Par page" fonctionne
- [ ] Synchronisation entre pagination haut et bas
- [ ] **Utilisateur confirme que la pagination fonctionne**

---

#### Step 3.8.7 : Frontend - MappingTable - Tri et filtres (identique à TransactionsTable)
**Status**: ⏸️ EN ATTENTE  
**Description**: Appliquer les mêmes fonctionnalités de tri et filtres à MappingTable.

**Tasks**:
- [ ] Modifier `frontend/src/components/MappingTable.tsx`
  - Rendre toutes les colonnes triables (ID, Nom, Level 1, Level 2, Level 3)
  - Ajouter indicateur visuel (↑/↓) sur colonne triée
  - Implémenter tri côté serveur (passer `sortBy` et `sortDirection` à `mappingsAPI.list()`)
  - Ajouter ligne de filtres sous les en-têtes
  - Champs texte + dropdowns avec valeurs uniques
  - Filtrage en temps réel (insensible à la casse, contient)
  - Filtres combinables (AND)
  - Ajouter pagination en haut (comme TransactionsTable)
- [ ] **Tester tri et filtres sur MappingTable**

**Deliverables**:
- Mise à jour `frontend/src/components/MappingTable.tsx` - Tri, filtres, pagination

**Acceptance Criteria**:
- [ ] Toutes les colonnes sont triables
- [ ] Indicateur visuel affiché
- [ ] Ligne de filtres fonctionne
- [ ] Dropdowns avec valeurs uniques fonctionnent
- [ ] Filtrage en temps réel fonctionne
- [ ] Pagination en haut fonctionne
- [ ] **Utilisateur confirme que tout fonctionne**

---

#### Step 3.8.8 : Backend - Ajouter paramètres de filtre aux endpoints
**Status**: ⏸️ EN ATTENTE  
**Description**: Ajouter les paramètres de filtre aux endpoints GET pour supporter le filtrage côté serveur.

**Tasks**:
- [ ] Modifier endpoint `GET /api/transactions` dans `backend/api/routes/transactions.py`
  - Ajouter paramètres de filtre optionnels : `filter_nom`, `filter_level_1`, `filter_level_2`, `filter_level_3`, `filter_quantite_min`, `filter_quantite_max`, `filter_solde_min`, `filter_solde_max`
  - Implémenter filtrage SQLAlchemy (LIKE pour texte, BETWEEN pour nombres)
  - Filtrage insensible à la casse pour texte
- [ ] Modifier endpoint `GET /api/mappings` dans `backend/api/routes/mappings.py`
  - Ajouter paramètres de filtre optionnels : `filter_nom`, `filter_level_1`, `filter_level_2`, `filter_level_3`
  - Implémenter filtrage SQLAlchemy (LIKE, insensible à la casse)
- [ ] **Tester les filtres avec différents paramètres**

**Deliverables**:
- Mise à jour `backend/api/routes/transactions.py` - Paramètres de filtre
- Mise à jour `backend/api/routes/mappings.py` - Paramètres de filtre

**Acceptance Criteria**:
- [ ] Filtres texte fonctionnent (contient, insensible à la casse)
- [ ] Filtres numériques fonctionnent (min/max)
- [ ] Filtres combinables (AND)
- [ ] Filtres combinés avec tri et pagination fonctionnent
- [ ] Tests passent

---

**Tests finaux**:
- [ ] Test tri sur toutes les colonnes (TransactionsTable et MappingTable)
- [ ] Test filtres en temps réel (texte + dropdown)
- [ ] Test filtres combinés (AND)
- [ ] Test pagination en haut et en bas
- [ ] Test combinaison tri + filtres + pagination
- [ ] Test performance avec beaucoup de données
- [ ] **Utilisateur confirme que toutes les fonctionnalités fonctionnent**

---

## Phase 4 : Fonctionnalité 3 - Calcul des amortissements

### Step 4.1 : Service calcul amortissements backend
**Status**: ⏸️ EN ATTENTE  
**Description**: Migrer la logique de `amort.py` avec convention 30/360.

**Tasks**:
- [ ] Créer amortization_service.py
- [ ] Implémenter calcul convention 30/360
- [ ] Implémenter répartition année par année
- [ ] Créer endpoint POST /api/calculations/amortizations
- [ ] **Créer test complet avec calculs réels**
- [ ] **Valider avec l'utilisateur**

**Deliverables**:
- `backend/api/services/amortization_service.py` - Service amortissements
- `backend/api/routes/calculations.py` - Endpoint amortissements
- `backend/tests/test_amortization.py` - Tests amortissements

**Tests**:
- [ ] Test calcul convention 30/360
- [ ] Test répartition proportionnelle
- [ ] Test 4 catégories (meubles, travaux, construction, terrain)
- [ ] Test paramètres configurables
- [ ] Test validation somme = montant initial

**Acceptance Criteria**:
- [ ] Calculs d'amortissements corrects
- [ ] Répartition proportionnelle validée
- [ ] Stockage en DB
- [ ] Test script exécutable et tous les tests passent
- [ ] **Utilisateur confirme que les calculs sont corrects**

**Impact Frontend**: 
- [ ] Afficher résultats calculs dans console/logs
- [ ] Tester calcul depuis interface

---

### Step 4.2 : Vue amortissements frontend
**Status**: ⏸️ EN ATTENTE  
**Description**: Interface pour visualiser les amortissements par catégorie et année.

**Tasks**:
- [ ] Créer composant AmortizationTable
- [ ] Créer page vue amortissements
- [ ] Implémenter affichage par catégorie et année
- [ ] **Créer test visuel dans navigateur**
- [ ] **Valider avec l'utilisateur**

**Deliverables**:
- `frontend/app/dashboard/amortissements/page.tsx` - Page amortissements
- `frontend/src/components/AmortizationTable.tsx` - Tableau amortissements

**Tests**:
- [ ] Test affichage tableau amortissements
- [ ] Test répartition par catégorie
- [ ] Test répartition par année
- [ ] Test totaux corrects

**Acceptance Criteria**:
- [ ] Tableau des amortissements s'affiche
- [ ] Répartition par catégorie et année visible
- [ ] Totaux corrects
- [ ] **Utilisateur confirme que la vue fonctionne**

**Impact Frontend**: 
- ✅ Onglet Amortissements fonctionnel
- ✅ Tableau avec répartition visible
- ✅ Totaux validés visuellement

---

## Phase 5 : Fonctionnalités 4-6 - États financiers

### Step 5.1 : Service compte de résultat backend
**Status**: ⏸️ EN ATTENTE  
**Description**: Migrer la logique de `compte_de_resultat.py`.

**Tasks**:
- [ ] Ajouter compte de résultat dans financial_statements_service.py
- [ ] Implémenter calcul produits/charges
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

### Step 5.2 : Service bilans backend
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

### Step 5.3 : Vue bilan frontend
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

## Phase 6 : Fonctionnalité 7 - Consolidation et autres vues

### Step 6.1 : Service consolidation backend
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

### Step 6.2 : Vue cashflow frontend
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

### Step 6.3 : Onglet tableau croisé dynamique
**Status**: ⏸️ EN ATTENTE  
**Description**: Interface pour analyses pivot avec groupby par colonnes.

**Tasks**:
- [ ] Créer composant PivotTable
- [ ] Créer page tableau croisé
- [ ] Implémenter groupby par colonnes
- [ ] Créer endpoint GET /api/analytics/pivot
- [ ] **Créer test visuel dans navigateur**
- [ ] **Valider avec l'utilisateur**

**Deliverables**:
- `frontend/app/dashboard/pivot/page.tsx` - Page pivot
- `frontend/src/components/PivotTable.tsx` - Composant pivot
- `backend/api/routes/analytics.py` - Endpoint pivot

**Tests**:
- [ ] Test groupby par level 1
- [ ] Test groupby par level 2
- [ ] Test groupby par mois/année
- [ ] Test totaux et sous-totaux

**Acceptance Criteria**:
- [ ] Tableau croisé fonctionne avec groupby
- [ ] Sélection des colonnes pour groupby
- [ ] Totaux et sous-totaux affichés
- [ ] **Utilisateur confirme que l'onglet fonctionne**

**Impact Frontend**: 
- ✅ Onglet Pivot fonctionnel
- ✅ Groupby opérationnel
- ✅ Totaux validés visuellement

---

## Phase 7 : Tests et validation finale

### Step 7.1 : Tests end-to-end
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

### Step 7.2 : Documentation et finalisation
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

