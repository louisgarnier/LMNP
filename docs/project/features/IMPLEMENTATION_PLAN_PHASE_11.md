
# Phase 11 : Multi-propriétés (Appartements) - Approche par Onglet

**Status**: ⏳ À FAIRE  
**Environnement**: Local uniquement  
**Durée estimée**: 3-4 semaines

## ⚠️ RAPPELS CRITIQUES

**AVANT TOUTE MODIFICATION DE CODE :**
1. **Lire `docs/workflow/BEST_PRACTICES.md`** - Obligatoire avant toute modification
2. **Consulter `docs/workflow/ERROR_INVESTIGATION.md`** - En cas d'erreurs
3. **Vérifier les erreurs frontend** - Utiliser `docs/workflow/check_frontend_errors.js`

**PRINCIPES FONDAMENTAUX :**
- ✅ **Un onglet à la fois** : Backend + Frontend + Tests avant de passer au suivant
- ✅ **Aucune régression** : Toutes les fonctionnalités existantes doivent continuer à fonctionner
- ✅ **Tests d'isolation** : Créer des données pour 2 propriétés, vérifier qu'elles sont bien isolées
- ✅ **Tests de non-régression** : Vérifier que chaque bouton, chaque fonctionnalité fonctionne comme avant
- ✅ **Validation explicite** : Ne pas passer à l'onglet suivant sans validation complète

**APPROCHE STANDARD POUR CHAQUE ONGLET (Backend) :**

**Ordre d'exécution recommandé :**
1. **Vérifications avant modification** :
   - Vérifier qu'aucune donnée existante ne sera impactée (ou gérer la migration)
   - Lister tous les endpoints à modifier
   - Identifier toutes les fonctions utilitaires qui utilisent les modèles
   - Vérifier les imports et dépendances

2. **Modèles SQLAlchemy** :
   - Ajouter `property_id` avec `ForeignKey("properties.id", ondelete="CASCADE")`
   - Ajouter les index `idx_{table}_property_id`
   - Vérifier que les modèles se chargent correctement

3. **Migrations** :
   - Créer migration pour ajouter `property_id` avec contrainte FK et ON DELETE CASCADE
   - Tester les migrations
   - Vérifier que les index sont créés

4. **Fonction de validation** :
   - Créer fonction utilitaire `validate_property_id(db: Session, property_id: int) -> bool`
   - Ajouter logs : `[Onglet] Validation property_id={property_id}`

5. **Endpoints API** :
   - Modifier chaque endpoint avec :
     - Ajout de `property_id` comme paramètre obligatoire
     - Validation avec `validate_property_id()`
     - Filtrage de toutes les requêtes par `property_id`
     - Logs au début : `[Onglet] {METHOD} {endpoint} - property_id={property_id}`
     - Logs après opération : `[Onglet] {action} réussie - property_id={property_id}`
     - Gestion d'erreurs : 400 si property_id invalide, 422 si manquant, 404 si ressource n'appartient pas à property_id

6. **Fonctions utilitaires** :
   - Modifier toutes les fonctions qui utilisent les modèles pour accepter `property_id`
   - Filtrer toutes les requêtes par `property_id`
   - Ajouter logs pour le debugging

7. **Tests d'isolation** :
   - Créer script de test avec logs détaillés
   - Tester l'isolation complète entre 2 propriétés
   - Vérifier qu'aucune donnée n'est accessible depuis une autre propriété

**NE JAMAIS COMMITER SANS ACCORD EXPLICITE DE L'UTILISATEUR**

## Objectif

Permettre la gestion de plusieurs appartements/propriétés dans l'application avec **isolation stricte** des données par propriété.

**Principe d'isolation** : Toutes les données sont strictement isolées par propriété via `property_id`. Aucune donnée ne peut être mélangée entre propriétés.

## Vue d'ensemble

Cette phase implique :
- Ajout d'une table `properties` pour stocker les appartements
- Ajout d'un champ `property_id` à toutes les tables existantes (isolation stricte)
- Ajout de contraintes FOREIGN KEY pour éviter les données orphelines
- Initialisation automatique des templates par défaut à la création d'une propriété
- Modification de tous les endpoints backend pour filtrer par propriété
- Modification de toutes les pages frontend pour utiliser `property_id`
- Tests d'isolation pour chaque onglet
- Tests de non-régression pour chaque onglet

## Principe d'initialisation des templates

**À la création d'une nouvelle propriété**, les templates suivants sont automatiquement initialisés :
- **AllowedMappings** : 57 mappings hardcodés dupliqués pour cette propriété
- **AmortizationTypes** : 7 types hardcodés dupliqués pour cette propriété
- **CompteResultatMappings** : Mappings par défaut dupliqués pour cette propriété
- **CompteResultatConfig** : Config par défaut dupliquée pour cette propriété
- **BilanMappings** : Mappings par défaut dupliqués pour cette propriété
- **BilanConfig** : Config par défaut dupliquée pour cette propriété

**Après initialisation**, chaque propriété peut modifier ses propres données sans impact sur les autres propriétés.

## Contraintes de base de données

**Toutes les tables avec `property_id` doivent avoir :**
- `property_id INTEGER NOT NULL`
- `FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE`
- `INDEX idx_{table}_property_id ON {table}(property_id)`

**Objectif** : Empêcher toute donnée orpheline. Si une propriété est supprimée, toutes ses données associées sont automatiquement supprimées.

## Ordre d'implémentation par Onglet

1. **Transactions** (toutes les transactions, Non classées, Load Trades)
2. **Mappings** (Mapping, Load mapping, Mappings autorisés, Mappings existants)
3. **Amortissements** (Config et Table)
4. **Crédit** (Config et Table)
5. **Compte de résultat** (Config et Table)
6. **Bilan** (Config et Table)
7. **Pivot** (Tableaux croisés dynamiques)

---

## PRÉ-REQUIS : Infrastructure de base

### Step 0.1 : Backend - Table et modèle Property
**Status**: ⏳ EN COURS (Partiellement complété)

**Tasks**:
- [x] Créer la table `properties` dans la base de données
- [x] Créer le modèle SQLAlchemy `Property`
- [x] Ajouter les champs : id, name, address, created_at, updated_at
- [x] Ajouter contrainte UNIQUE sur `name`
- [x] Créer une migration pour la table (`backend/database/migrations/add_properties_table.py`)
- [x] Créer un script de test : `backend/scripts/test_property_model_phase_11_bis_0_1.py`
- [x] Tester la création, lecture, modification, suppression de propriétés
- [x] Créer endpoints API : GET, POST, PUT, DELETE `/api/properties`
- [x] Configurer contraintes FOREIGN KEY avec ON DELETE CASCADE dans `connection.py`
- [x] Activer `PRAGMA foreign_keys = ON` dans `get_db()` pour SQLite
- [ ] Créer fonction d'initialisation des templates : `initialize_default_templates_for_property(property_id)`
  - Initialiser 57 AllowedMappings hardcodés
  - Initialiser 7 AmortizationTypes hardcodés
  - Initialiser CompteResultatMappings par défaut
  - Initialiser CompteResultatConfig par défaut
  - Initialiser BilanMappings par défaut
  - Initialiser BilanConfig par défaut

**Tests**:
- [x] Créer une propriété
- [x] Lire une propriété
- [x] Modifier une propriété
- [x] Supprimer une propriété
- [x] Vérifier les contraintes (name unique, etc.)
- [x] Vérifier que l'initialisation des templates fonctionne à la création ✅
- [x] Vérifier que les 57 AllowedMappings sont créés ✅ (57 mappings hardcodés)
- [x] Vérifier que les 7 AmortizationTypes sont créés ✅ (non visibles tant qu'il n'y a pas de transactions avec level_2)
- [x] Vérifier que les CompteResultatMappings sont créés ✅ (non visibles tant qu'il n'y a pas de transactions)
- [x] Vérifier que les BilanMappings sont créés ✅

---

### Step 0.2 : Frontend - Page d'accueil et contexte Property
**Status**: ⏳ EN COURS (Partiellement complété)

**Tasks**:
- [x] Créer un contexte PropertyContext pour gérer la propriété active (`frontend/src/contexts/PropertyContext.tsx`)
- [x] Créer une page d'accueil (`frontend/app/page.tsx`) avec sélection de propriété
- [x] Afficher les propriétés sous forme de cards
- [x] Permettre la création d'une nouvelle propriété (modal)
- [x] Permettre la sélection d'une propriété
- [x] Après sélection d'une propriété : Rediriger vers `/dashboard`
- [x] Modifier Header pour afficher la propriété active et permettre de changer (`frontend/src/components/Header.tsx`)
- [x] Modifier DashboardLayout pour rediriger si aucune propriété sélectionnée (`frontend/app/dashboard/layout.tsx`)
- [x] Stocker la propriété active dans localStorage
- [x] Ajouter fonctionnalité de suppression via menu contextuel (clic droit)
- [x] Ajouter `propertiesAPI` dans `frontend/src/api/client.ts`
- [x] Ajouter timeout de 10 secondes pour éviter que l'app reste bloquée
- [x] Améliorer gestion d'erreur avec affichage clair des erreurs de connexion

**Tests**:
- [x] Affichage de toutes les propriétés (cards avec nom, adresse, date de création) ✅
- [x] Création d'une nouvelle propriété (modal avec validation) ✅
- [x] Sélection d'une propriété (redirection vers dashboard) ✅
- [x] Header affiche la propriété active avec bouton "Changer" ✅
- [x] Redirection automatique si aucune propriété sélectionnée ✅ (supprimer localStorage et vérifier redirection vers page d'accueil)
- [x] Persistance dans localStorage (propriété restaurée au rechargement) ✅ (sélectionner une propriété, recharger la page F5, vérifier que la même propriété est toujours active)
- [x] Suppression d'une propriété via menu contextuel (clic droit) ✅

**Notes**:
- Menu contextuel ajouté : clic droit sur une carte de propriété → option "Supprimer"
- Confirmation avant suppression avec liste détaillée des données qui seront supprimées
- Timeout de 10 secondes ajouté pour éviter que l'app reste bloquée si le backend ne répond pas
- Gestion d'erreur améliorée avec affichage clair des erreurs de connexion
- **Correction bug localStorage** : Ajout d'un flag `hasCheckedLocalStorage` pour empêcher la suppression de localStorage au montage initial avant la restauration

**Notes**:
- Menu contextuel ajouté : clic droit sur une carte de propriété → option "Supprimer"
- Confirmation avant suppression avec liste détaillée des données qui seront supprimées
- Timeout de 10 secondes ajouté pour éviter que l'app reste bloquée si le backend ne répond pas
- Gestion d'erreur améliorée avec affichage clair des erreurs de connexion

---

## ONGLET 1 : TRANSACTIONS
**Status**: ✅ COMPLÉTÉ

### Fonctionnalités existantes à préserver

**Onglet "Transactions" (par défaut)** :
- ✅ Affichage de toutes les transactions avec pagination
- ✅ Tri par colonne (date, quantité, nom, solde, level_1, level_2, level_3)
- ✅ Filtres : nom, level_1, level_2, level_3, quantité, solde, date
- ✅ Édition inline d'une transaction (date, quantité, nom)
- ✅ Suppression d'une transaction
- ✅ Suppression multiple de transactions
- ✅ Classification inline (level_1, level_2, level_3)
- ✅ Export Excel/CSV
- ✅ Affichage du solde cumulé

**Onglet "Non classées"** :
- ✅ Affichage uniquement des transactions non classées (level_1 = NULL)
- ✅ Toutes les fonctionnalités de l'onglet Transactions

**Onglet "Load Trades"** :
- ✅ Upload de fichier CSV/Excel
- ✅ Mapping des colonnes (date, quantité, nom)
- ✅ Import des transactions
- ✅ Détection et affichage des doublons
- ✅ Affichage des erreurs d'import
- ✅ Compteur de transactions en BDD
- ✅ Recalcul automatique des soldes après import
- ✅ Enrichissement automatique après import
- ✅ Historique des imports (logs) isolé par propriété

---

### Step 1.1 : Backend - Endpoints Transactions avec property_id
**Status**: ✅ COMPLÉTÉ

**Ordre d'exécution recommandé :**
1. **Modèles SQLAlchemy** (structure de données) ✅
2. **Migrations** (application en BDD) ✅
3. **Endpoints API** (logique métier) ✅
4. **Tests d'isolation** (vérification) ✅

**Vérifications avant modification :**
- [x] Vérifier qu'aucune transaction n'existe dans la BDD (table vide)
- [x] Lister tous les endpoints transactions à modifier
- [x] Identifier toutes les fonctions utilitaires qui utilisent Transaction/EnrichedTransaction
- [x] Vérifier les imports et dépendances

**Tasks**:

**1. Modèles SQLAlchemy** :
- [x] Ajouter `property_id` au modèle SQLAlchemy `Transaction` avec `ForeignKey("properties.id", ondelete="CASCADE")`
- [x] Ajouter `property_id` au modèle SQLAlchemy `EnrichedTransaction` avec `ForeignKey("properties.id", ondelete="CASCADE")`
- [x] Ajouter index `idx_transactions_property_id` sur `transactions(property_id)` dans `__table_args__`
- [x] Ajouter index `idx_enriched_transactions_property_id` sur `enriched_transactions(property_id)` dans `__table_args__`
- [x] Vérifier que les modèles se chargent correctement (pas d'erreur d'import)

**2. Migrations** :
- [x] Créer migration `backend/database/migrations/add_property_id_to_transactions.py` pour ajouter `property_id` à la table `transactions` avec contrainte FK et ON DELETE CASCADE
- [x] Créer migration `backend/database/migrations/add_property_id_to_enriched_transactions.py` pour ajouter `property_id` à la table `enriched_transactions` avec contrainte FK et ON DELETE CASCADE
- [x] **Créer migration `backend/database/migrations/add_property_id_to_file_imports.py` pour ajouter `property_id` à la table `file_imports` avec contrainte FK et ON DELETE CASCADE**
- [x] **Modifier l'index unique de `file_imports` : remplacer `filename` unique par `(property_id, filename)` unique**
- [x] **Assigner `property_id=1` (ou première propriété) à tous les `FileImport` existants**
- [x] Tester les migrations (vérifier que les colonnes sont créées avec les bonnes contraintes)
- [x] Vérifier que les index sont créés

**3. Fonction de validation property_id** :
- [x] Créer fonction utilitaire `validate_property_id(db: Session, property_id: int) -> bool` dans `backend/api/utils/validation.py`
- [x] Cette fonction vérifie que `property_id` existe dans la table `properties`
- [x] Retourne `True` si valide, lève `HTTPException(400)` si invalide
- [x] Ajouter logs : `[Transactions] Validation property_id={property_id}`

**4. Endpoints API - Modifications avec logs** :
- [x] Modifier `GET /api/transactions` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Transactions] GET /api/transactions - property_id={property_id}`
  - Filtrer toutes les requêtes : `query = query.filter(Transaction.property_id == property_id)`
  - Valider property_id avec `validate_property_id(db, property_id)`
  - Ajouter log : `[Transactions] Retourné {count} transactions pour property_id={property_id}`
- [x] Modifier `POST /api/transactions` :
  - Ajouter `property_id` dans `TransactionCreate` model
  - Ajouter log : `[Transactions] POST /api/transactions - property_id={property_id}`
  - Valider property_id avant création
  - Ajouter log : `[Transactions] Transaction créée: id={id}, property_id={property_id}`
- [x] Modifier `PUT /api/transactions/{id}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Transactions] PUT /api/transactions/{id} - property_id={property_id}`
  - Filtrer : `transaction = db.query(Transaction).filter(Transaction.id == id, Transaction.property_id == property_id).first()`
  - Retourner 404 si transaction n'appartient pas à property_id
  - Ajouter log : `[Transactions] Transaction {id} mise à jour pour property_id={property_id}`
- [x] Modifier `DELETE /api/transactions/{id}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Transactions] DELETE /api/transactions/{id} - property_id={property_id}`
  - Filtrer : `transaction = db.query(Transaction).filter(Transaction.id == id, Transaction.property_id == property_id).first()`
  - Retourner 404 si transaction n'appartient pas à property_id
  - Ajouter log : `[Transactions] Transaction {id} supprimée pour property_id={property_id}`
- [x] Modifier `GET /api/transactions/unique-values` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer toutes les requêtes par `property_id`
  - Ajouter log : `[Transactions] GET unique-values - property_id={property_id}, column={column}`
- [x] Modifier `GET /api/transactions/sum-by-level1` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer toutes les requêtes par `property_id`
  - Ajouter log : `[Transactions] GET sum-by-level1 - property_id={property_id}, level_1={level_1}`
- [x] Modifier `GET /api/transactions/export` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer toutes les requêtes par `property_id`
  - Ajouter log : `[Transactions] GET export - property_id={property_id}, format={format}`
- [x] Modifier `GET /api/transactions/{id}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer : `transaction = db.query(Transaction).filter(Transaction.id == id, Transaction.property_id == property_id).first()`
  - Retourner 404 si transaction n'appartient pas à property_id
  - Ajouter log : `[Transactions] GET /api/transactions/{id} - property_id={property_id}`
- [x] Modifier `POST /api/transactions/import` :
  - Ajouter `property_id: int = Form(..., description="ID de la propriété (obligatoire)")`
  - Passer `property_id` à toutes les transactions créées
  - **Enregistrer `property_id` dans `FileImport` lors de la création/mise à jour**
  - Ajouter log : `[Transactions] POST import - property_id={property_id}, file={filename}`
  - Ajouter log : `[Transactions] Import terminé: {count} transactions créées pour property_id={property_id}`
- [x] Modifier `GET /api/transactions/imports` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer : `query = query.filter(FileImport.property_id == property_id)`
  - Ajouter log : `[Transactions] GET imports - property_id={property_id}`
  - Ajouter log : `[Transactions] Retourné {count} imports pour property_id={property_id}`
- [x] Modifier `DELETE /api/transactions/imports` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer : `db.query(FileImport).filter(FileImport.property_id == property_id).delete()`
  - Ajouter log : `[Transactions] DELETE imports - property_id={property_id}`
- [x] Modifier `DELETE /api/transactions/imports/{import_id}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer : `import_obj = db.query(FileImport).filter(FileImport.id == import_id, FileImport.property_id == property_id).first()`
  - Retourner 404 si import n'appartient pas à property_id
  - Ajouter log : `[Transactions] DELETE imports/{import_id} - property_id={property_id}`

**5. Fonctions utilitaires** :
- [x] Modifier `recalculate_balances_from_date` dans `backend/api/utils/balance_utils.py` :
  - Ajouter paramètre `property_id: int`
  - Filtrer toutes les requêtes : `query = query.filter(Transaction.property_id == property_id)`
  - Ajouter log : `[BalanceUtils] Recalcul soldes depuis {date} pour property_id={property_id}`
- [x] Modifier `recalculate_all_balances` dans `backend/api/utils/balance_utils.py` :
  - Ajouter paramètre `property_id: int`
  - Filtrer toutes les requêtes : `query = query.filter(Transaction.property_id == property_id)`
  - Ajouter log : `[BalanceUtils] Recalcul tous les soldes pour property_id={property_id}`
- [x] Vérifier tous les appels à ces fonctions et passer `property_id`

**6. Validation et gestion d'erreurs** :
- [x] Ajouter validation dans chaque endpoint : `validate_property_id(db, property_id)` au début
- [x] Erreur 400 si property_id invalide (n'existe pas dans properties)
- [x] Erreur 422 si property_id manquant (FastAPI validation automatique)
- [x] Erreur 404 si transaction n'appartient pas à property_id demandé
- [x] Ajouter logs d'erreur : `[Transactions] ERREUR: {message} - property_id={property_id}`

**7. Tests d'isolation** :
- [x] Créer script de test : `backend/scripts/test_transactions_isolation_phase_11_bis_1_1.py`
- [x] Le script doit afficher des logs clairs pour chaque test
- [x] Vérifier l'isolation complète entre 2 propriétés

**Tests d'isolation (script Python)**:
- [x] Créer 2 propriétés (prop1, prop2)
- [x] Créer 5 transactions pour prop1
- [x] Créer 3 transactions pour prop2
- [x] GET /api/transactions?property_id=prop1 → doit retourner uniquement les 5 transactions de prop1
- [x] GET /api/transactions?property_id=prop2 → doit retourner uniquement les 3 transactions de prop2
- [x] POST /api/transactions avec property_id=prop1 → doit créer une transaction pour prop1 uniquement
- [x] PUT /api/transactions/{id}?property_id=prop1 → ne peut modifier que les transactions de prop1
- [x] DELETE /api/transactions/{id}?property_id=prop1 → ne peut supprimer que les transactions de prop1
- [x] Tentative d'accès à une transaction de prop2 avec property_id=prop1 → doit retourner 404
- [x] Import de transactions avec property_id=prop1 → doit créer uniquement pour prop1
- [x] Recalcul des soldes pour prop1 → ne doit affecter que les transactions de prop1

---

### Step 1.2 : Frontend - Page Transactions avec property_id
**Status**: ✅ COMPLÉTÉ

**Tasks**:
- [x] Modifier `frontend/app/dashboard/transactions/page.tsx` pour utiliser `useProperty()`
- [x] Modifier `TransactionsTable.tsx` pour passer `activeProperty.id` à tous les appels API
- [x] Modifier `UnclassifiedTransactionsTable.tsx` pour passer `activeProperty.id`
- [x] Modifier `FileUpload.tsx` / `ColumnMappingModal.tsx` pour passer `activeProperty.id` à l'import
- [x] Modifier `ImportLog.tsx` pour utiliser `activeProperty.id`
- [x] Ajouter réinitialisation de la page à 1 quand la propriété change
- [x] Ajouter réinitialisation du total et des transactions quand la propriété change
- [x] Vérifier que tous les filtres fonctionnent avec property_id
- [x] Vérifier que le tri fonctionne avec property_id
- [x] Vérifier que la pagination fonctionne avec property_id
- [x] Créer script de test frontend : `frontend/scripts/test_transactions_isolation_phase_11_bis_1_2.js`

**Tests d'isolation (script frontend)**:
- [x] Créer 2 propriétés via l'interface
- [x] Sélectionner prop1
- [x] Créer 3 transactions pour prop1
- [x] Vérifier qu'elles s'affichent dans l'onglet Transactions
- [x] Changer pour prop2
- [x] Vérifier que les 3 transactions de prop1 ne s'affichent PAS
- [x] Créer 2 transactions pour prop2
- [x] Vérifier qu'elles s'affichent
- [x] Revenir à prop1
- [x] Vérifier que seules les 3 transactions de prop1 s'affichent

**Tests de non-régression (manuel)**:
- [x] Onglet "Transactions" : Toutes les transactions s'affichent ✅
- [x] Tri par colonne fonctionne ✅
- [x] Filtres fonctionnent ✅
- [x] Pagination fonctionne ✅
- [x] Édition inline fonctionne ✅
- [x] Suppression fonctionne ✅
- [x] Suppression multiple fonctionne ✅
- [x] Classification inline fonctionne ✅
- [x] Export Excel/CSV fonctionne ✅
- [x] Onglet "Non classées" : Seules les non classées s'affichent ✅
- [x] Onglet "Load Trades" : Upload fonctionne ✅
- [x] Mapping des colonnes fonctionne ✅
- [x] Import fonctionne ✅
- [x] Détection des doublons fonctionne ✅
- [x] Affichage des erreurs fonctionne ✅
- [x] Compteur de transactions fonctionne ✅
- [x] Recalcul des soldes fonctionne ✅

**Validation avant Step 1.3** :
- [x] Tous les tests d'isolation passent ✅
- [x] Tous les tests de non-régression passent ✅
- [x] Aucune erreur dans la console frontend ✅
- [x] Aucune erreur dans les logs backend ✅
- [x] Validation explicite de l'utilisateur ✅

---

### Step 1.3 : Migration des données Transactions existantes
**Status**: ✅ COMPLÉTÉ

**Tasks**:
- [x] Créer un script de migration : `backend/scripts/migrate_transactions_phase_11_bis_1_3.py`
- [x] Créer une propriété par défaut ("Appartement 1")
- [x] Assigner toutes les transactions existantes à cette propriété
- [x] Vérifier qu'aucune transaction n'a property_id=NULL après migration
- [x] Recalculer tous les soldes pour la propriété par défaut
- [x] Créer script de validation : `backend/scripts/validate_transactions_migration_phase_11_bis_1_3.py`

**Tests**:
- [x] Toutes les transactions ont un property_id ✅
- [x] Aucune transaction orpheline (property_id=NULL) ✅
- [x] Les soldes sont corrects pour la propriété par défaut ✅
- [x] Le frontend affiche correctement les transactions après migration ✅

---

## ONGLET 2 : MAPPINGS

### Fonctionnalités existantes à préserver

**Onglet "Mapping" (Mappings existants)** :
- ✅ Affichage de tous les mappings avec pagination
- ✅ Tri par colonne (nom, level_1, level_2, level_3)
- ✅ Filtres : nom, level_1, level_2, level_3
- ✅ Création d'un mapping (nom, level_1, level_2, level_3, is_prefix_match, priority)
- ✅ Édition d'un mapping
- ✅ Suppression d'un mapping
- ✅ Suppression multiple de mappings
- ✅ Export Excel/CSV
- ✅ Validation des combinaisons autorisées (level_1, level_2, level_3)

**Onglet "Load mapping"** :
- ✅ Upload de fichier Excel
- ✅ Import des mappings
- ✅ Détection et affichage des erreurs
- ✅ Historique des imports

**Onglet "Mappings autorisés"** :
- ✅ Affichage des mappings hardcodés
- ✅ Création d'un mapping autorisé
- ✅ Suppression d'un mapping autorisé
- ✅ Réinitialisation des mappings hardcodés
- ✅ Validation des combinaisons (level_1, level_2, level_3)

---

### Step 2.1 : Backend - Endpoints Mappings avec property_id
**Status**: ⏳ À FAIRE

**1. Vérifications avant modification** :
- [ ] Vérifier qu'aucune donnée existante ne sera impactée (ou gérer la migration)
- [ ] Lister tous les endpoints à modifier dans `backend/api/routes/mappings.py`
- [ ] Identifier toutes les fonctions utilitaires qui utilisent les modèles `Mapping` et `AllowedMapping`
- [ ] Vérifier les imports et dépendances

**2. Modèles SQLAlchemy** :
- [ ] Ajouter `property_id` au modèle `Mapping` dans `backend/database/models.py` :
  - `property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)`
  - Ajouter relation : `property = relationship("Property", back_populates="mappings")`
- [ ] Ajouter `property_id` au modèle `AllowedMapping` dans `backend/database/models.py` :
  - `property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)`
  - Ajouter relation : `property = relationship("Property", back_populates="allowed_mappings")`
- [ ] **Ajouter `property_id` au modèle `MappingImport` avec `ForeignKey("properties.id", ondelete="CASCADE")`**
- [ ] Modifier l'index unique de `AllowedMapping` pour inclure `property_id` : `UniqueConstraint('property_id', 'level_1', 'level_2', 'level_3')`
- [ ] **Modifier l'index unique de `MappingImport` : remplacer `filename` unique par `(property_id, filename)` unique**
- [ ] Ajouter index `idx_mappings_property_id` sur `mappings(property_id)`
- [ ] Ajouter index `idx_allowed_mappings_property_id` sur `allowed_mappings(property_id)`
- [ ] **Ajouter index `idx_mapping_imports_property_id` sur `mapping_imports(property_id)`**
- [ ] Vérifier que les modèles se chargent correctement (pas d'erreur d'import)

**3. Migrations** :
- [ ] Créer migration `backend/database/migrations/add_property_id_to_mappings.py` pour ajouter `property_id` à la table `mappings` avec contrainte FK et ON DELETE CASCADE
- [ ] Créer migration `backend/database/migrations/add_property_id_to_allowed_mappings.py` pour ajouter `property_id` à la table `allowed_mappings` avec contrainte FK et ON DELETE CASCADE
- [ ] **Créer migration `backend/database/migrations/add_property_id_to_mapping_imports.py` pour ajouter `property_id` à la table `mapping_imports` avec contrainte FK et ON DELETE CASCADE**
- [ ] Modifier l'index unique de `allowed_mappings` pour inclure `property_id`
- [ ] **Modifier l'index unique de `mapping_imports` : remplacer `filename` unique par `(property_id, filename)` unique**
- [ ] **Assigner `property_id=1` (ou première propriété) à tous les `MappingImport` existants**
- [ ] Tester les migrations (vérifier que les colonnes sont créées avec les bonnes contraintes)
- [ ] Vérifier que les index sont créés

**4. Fonction de validation property_id** :
- [ ] Utiliser la fonction existante `validate_property_id(db: Session, property_id: int) -> bool` dans `backend/api/utils/validation.py`
- [ ] Ajouter logs : `[Mappings] Validation property_id={property_id}`

**5. Endpoints API - Modifications avec logs** :
- [ ] Modifier `GET /api/mappings` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Mappings] GET /api/mappings - property_id={property_id}`
  - Filtrer toutes les requêtes : `query = query.filter(Mapping.property_id == property_id)`
  - Valider property_id avec `validate_property_id(db, property_id)`
  - Ajouter log : `[Mappings] Retourné {count} mappings pour property_id={property_id}`
- [ ] Modifier `POST /api/mappings` :
  - Ajouter `property_id` dans `MappingCreate` model
  - Ajouter log : `[Mappings] POST /api/mappings - property_id={property_id}`
  - Valider property_id avant création
  - Ajouter log : `[Mappings] Mapping créé: id={id}, property_id={property_id}`
- [ ] Modifier `PUT /api/mappings/{id}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Mappings] PUT /api/mappings/{id} - property_id={property_id}`
  - Filtrer : `mapping = db.query(Mapping).filter(Mapping.id == id, Mapping.property_id == property_id).first()`
  - Retourner 404 si mapping n'appartient pas à property_id
  - Ajouter log : `[Mappings] Mapping {id} mis à jour pour property_id={property_id}`
- [ ] Modifier `DELETE /api/mappings/{id}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Mappings] DELETE /api/mappings/{id} - property_id={property_id}`
  - Filtrer : `mapping = db.query(Mapping).filter(Mapping.id == id, Mapping.property_id == property_id).first()`
  - Retourner 404 si mapping n'appartient pas à property_id
  - Ajouter log : `[Mappings] Mapping {id} supprimé pour property_id={property_id}`
- [ ] Modifier `GET /api/mappings/{id}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer : `mapping = db.query(Mapping).filter(Mapping.id == id, Mapping.property_id == property_id).first()`
  - Retourner 404 si mapping n'appartient pas à property_id
  - Ajouter log : `[Mappings] GET /api/mappings/{id} - property_id={property_id}`
- [ ] Modifier `GET /api/mappings/export` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer toutes les requêtes par `property_id`
  - Ajouter log : `[Mappings] GET export - property_id={property_id}`
- [ ] Modifier `GET /api/mappings/unique-values` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer toutes les requêtes par `property_id`
  - Ajouter log : `[Mappings] GET unique-values - property_id={property_id}, column={column}`
- [ ] Modifier `GET /api/mappings/allowed` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer toutes les requêtes par `property_id`
  - Ajouter log : `[Mappings] GET allowed - property_id={property_id}`
- [ ] Modifier `POST /api/mappings/allowed` :
  - Ajouter `property_id` dans `AllowedMappingCreate` model
  - Ajouter log : `[Mappings] POST allowed - property_id={property_id}`
  - Valider property_id avant création
  - Ajouter log : `[Mappings] AllowedMapping créé: id={id}, property_id={property_id}`
- [ ] Modifier `DELETE /api/mappings/allowed/{id}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer : `allowed_mapping = db.query(AllowedMapping).filter(AllowedMapping.id == id, AllowedMapping.property_id == property_id).first()`
  - Retourner 404 si allowed_mapping n'appartient pas à property_id
  - Ajouter log : `[Mappings] DELETE allowed/{id} - property_id={property_id}`
- [ ] Modifier `POST /api/mappings/import` :
  - Ajouter `property_id: int = Form(..., description="ID de la propriété (obligatoire)")`
  - Passer `property_id` à tous les mappings créés
  - **Enregistrer `property_id` dans `MappingImport` lors de la création/mise à jour**
  - Ajouter log : `[Mappings] POST import - property_id={property_id}, file={filename}`
- [ ] Modifier `GET /api/mappings/imports` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer : `query = query.filter(MappingImport.property_id == property_id)`
  - Ajouter log : `[Mappings] GET imports - property_id={property_id}`
  - Ajouter log : `[Mappings] Retourné {count} imports pour property_id={property_id}`
- [ ] Modifier `DELETE /api/mappings/imports` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer : `db.query(MappingImport).filter(MappingImport.property_id == property_id).delete()`
  - Ajouter log : `[Mappings] DELETE imports - property_id={property_id}`
- [ ] Modifier `DELETE /api/mappings/imports/{import_id}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer : `import_obj = db.query(MappingImport).filter(MappingImport.id == import_id, MappingImport.property_id == property_id).first()`
  - Retourner 404 si import n'appartient pas à property_id
  - Ajouter log : `[Mappings] DELETE imports/{import_id} - property_id={property_id}`
  - Ajouter log : `[Mappings] Import terminé: {count} mappings créés pour property_id={property_id}`
- [ ] Modifier `GET /api/mappings/imports/history` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer toutes les requêtes par `property_id`
  - Ajouter log : `[Mappings] GET imports/history - property_id={property_id}`
- [ ] Modifier `DELETE /api/mappings/imports/all` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer toutes les requêtes par `property_id`
  - Ajouter log : `[Mappings] DELETE imports/all - property_id={property_id}`
- [ ] Modifier `GET /api/mappings/allowed/level-1` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer toutes les requêtes par `property_id`
  - Ajouter log : `[Mappings] GET allowed/level-1 - property_id={property_id}`
- [ ] Modifier `GET /api/mappings/allowed/level-2` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer toutes les requêtes par `property_id`
  - Ajouter log : `[Mappings] GET allowed/level-2 - property_id={property_id}`
- [ ] Modifier `GET /api/mappings/allowed/level-3` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer toutes les requêtes par `property_id`
  - Ajouter log : `[Mappings] GET allowed/level-3 - property_id={property_id}`

**6. Fonctions utilitaires** :
- [ ] Modifier toutes les fonctions de validation pour accepter `property_id`
- [ ] Filtrer toutes les requêtes par `property_id`
- [ ] Ajouter logs pour le debugging
- [ ] Vérifier tous les appels à ces fonctions et passer `property_id`

**7. Validation et gestion d'erreurs** :
- [ ] Ajouter validation dans chaque endpoint : `validate_property_id(db, property_id)` au début
- [ ] Erreur 400 si property_id invalide (n'existe pas dans properties)
- [ ] Erreur 422 si property_id manquant (FastAPI validation automatique)
- [ ] Erreur 404 si mapping n'appartient pas à property_id demandé
- [ ] Ajouter logs d'erreur : `[Mappings] ERREUR: {message} - property_id={property_id}`

**8. Tests d'isolation** :
- [ ] Créer script de test : `backend/scripts/test_mappings_isolation_phase_11_bis_2_1.py`
- [ ] Le script doit afficher des logs clairs pour chaque test
- [ ] Vérifier l'isolation complète entre 2 propriétés

**Tests d'isolation (script Python)**:
- [ ] Créer 2 propriétés (prop1, prop2)
- [ ] Créer 5 mappings pour prop1
- [ ] Créer 3 mappings pour prop2
- [ ] GET /api/mappings?property_id=prop1 → doit retourner uniquement les 5 mappings de prop1
- [ ] GET /api/mappings?property_id=prop2 → doit retourner uniquement les 3 mappings de prop2
- [ ] POST /api/mappings avec property_id=prop1 → doit créer un mapping pour prop1 uniquement
- [ ] PUT /api/mappings/{id}?property_id=prop1 → ne peut modifier que les mappings de prop1
- [ ] DELETE /api/mappings/{id}?property_id=prop1 → ne peut supprimer que les mappings de prop1
- [ ] Tentative d'accès à un mapping de prop2 avec property_id=prop1 → doit retourner 404
- [ ] GET /api/mappings/allowed?property_id=prop1 → doit retourner uniquement les mappings autorisés de prop1
- [ ] POST /api/mappings/allowed avec property_id=prop1 → doit créer un mapping autorisé pour prop1 uniquement
- [ ] Import de mappings avec property_id=prop1 → doit créer uniquement pour prop1

---

### Step 2.2 : Frontend - Page Mappings avec property_id
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Modifier `MappingTable.tsx` pour passer `activeProperty.id` à tous les appels API
- [ ] Modifier `AllowedMappingsTable.tsx` pour passer `activeProperty.id`
- [ ] Modifier `MappingFileUpload.tsx` pour passer `activeProperty.id` à l'import
- [ ] Modifier `MappingImportLog.tsx` pour utiliser `activeProperty.id`
- [ ] Vérifier que tous les filtres fonctionnent avec property_id
- [ ] Vérifier que la pagination fonctionne avec property_id
- [ ] Vérifier que la validation des combinaisons fonctionne avec property_id
- [ ] Créer script de test frontend : `frontend/scripts/test_mappings_isolation_phase_11_bis_2_2.js`

**Tests d'isolation (script frontend)**:
- [ ] Sélectionner prop1
- [ ] Créer 3 mappings pour prop1
- [ ] Vérifier qu'ils s'affichent dans l'onglet "Mapping"
- [ ] Changer pour prop2
- [ ] Vérifier que les 3 mappings de prop1 ne s'affichent PAS
- [ ] Créer 2 mappings pour prop2
- [ ] Vérifier qu'ils s'affichent
- [ ] Revenir à prop1
- [ ] Vérifier que seuls les 3 mappings de prop1 s'affichent
- [ ] Vérifier que les mappings autorisés sont isolés par propriété

**Tests de non-régression (manuel)**:
- [ ] Onglet "Mapping" : Tous les mappings s'affichent ✅
- [ ] Tri par colonne fonctionne ✅
- [ ] Filtres fonctionnent ✅
- [ ] Pagination fonctionne ✅
- [ ] Création d'un mapping fonctionne ✅
- [ ] Édition d'un mapping fonctionne ✅
- [ ] Suppression d'un mapping fonctionne ✅
- [ ] Suppression multiple fonctionne ✅
- [ ] Export Excel/CSV fonctionne ✅
- [ ] Validation des combinaisons fonctionne ✅
- [ ] Onglet "Load mapping" : Upload fonctionne ✅
- [ ] Import fonctionne ✅
- [ ] Historique des imports fonctionne ✅
- [ ] Onglet "Mappings autorisés" : Affichage fonctionne ✅
- [ ] Création d'un mapping autorisé fonctionne ✅
- [ ] Suppression d'un mapping autorisé fonctionne ✅
- [ ] Réinitialisation des mappings hardcodés fonctionne ✅

**Validation avant Step 2.3** :
- [ ] Tous les tests d'isolation passent ✅
- [ ] Tous les tests de non-régression passent ✅
- [ ] Aucune erreur dans la console frontend ✅
- [ ] Aucune erreur dans les logs backend ✅
- [ ] Validation explicite de l'utilisateur ✅

---

### Step 2.3 : Migration des données Mappings existantes
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer un script de migration : `backend/scripts/migrate_mappings_phase_11_bis_2_3.py`
- [ ] Assigner tous les mappings existants à la propriété par défaut
- [ ] Assigner tous les mappings autorisés existants à la propriété par défaut
- [ ] Initialiser les mappings hardcodés pour la propriété par défaut
- [ ] Vérifier qu'aucun mapping n'a property_id=NULL après migration
- [ ] Créer script de validation : `backend/scripts/validate_mappings_migration_phase_11_bis_2_3.py`

**Tests**:
- [ ] Tous les mappings ont un property_id ✅
- [ ] Tous les mappings autorisés ont un property_id ✅
- [ ] Aucun mapping orphelin (property_id=NULL) ✅
- [ ] Les mappings hardcodés sont initialisés pour la propriété par défaut ✅
- [ ] Le frontend affiche correctement les mappings après migration ✅

---

## ONGLET 3 : AMORTISSEMENTS

### Fonctionnalités existantes à préserver

**Onglet "Amortissements"** :
- ✅ Affichage de la table d'amortissement (résultats agrégés)
- ✅ Affichage par catégorie (level_2)
- ✅ Affichage par année
- ✅ Calcul automatique des amortissements
- ✅ Recalcul manuel des amortissements

**Config Amortissements** :
- ✅ Affichage des types d'amortissement par level_2
- ✅ Création d'un type d'amortissement (name, level_2, level_1_values, duration)
- ✅ Édition d'un type d'amortissement
- ✅ Suppression d'un type d'amortissement
- ✅ Calcul du montant par année
- ✅ Calcul du montant cumulé
- ✅ Comptage des transactions associées

---

### Step 3.1 : Backend - Endpoints Amortissements avec property_id
**Status**: ⏳ À FAIRE

**1. Vérifications avant modification** :
- [ ] Vérifier qu'aucune donnée existante ne sera impactée (ou gérer la migration)
- [ ] Lister tous les endpoints à modifier dans `backend/api/routes/amortization.py`
- [ ] Identifier toutes les fonctions utilitaires qui utilisent le modèle `AmortizationType`
- [ ] Identifier toutes les fonctions qui utilisent `Transaction` pour les résultats d'amortissement
- [ ] Vérifier les imports et dépendances

**2. Modèles SQLAlchemy** :
- [ ] Ajouter `property_id` au modèle `AmortizationType` dans `backend/database/models.py` :
  - `property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)`
  - Ajouter relation : `property = relationship("Property", back_populates="amortization_types")`
- [ ] Ajouter index `idx_amortization_types_property_id` sur `amortization_types(property_id)`
- [ ] Vérifier que les modèles se chargent correctement (pas d'erreur d'import)
- [ ] Note : Les résultats d'amortissement sont liés via `Transaction.property_id` (pas besoin de modifier `AmortizationResult`)

**3. Migrations** :
- [ ] Créer migration `backend/database/migrations/add_property_id_to_amortization_types.py` pour ajouter `property_id` à la table `amortization_types` avec contrainte FK et ON DELETE CASCADE
- [ ] Tester les migrations (vérifier que les colonnes sont créées avec les bonnes contraintes)
- [ ] Vérifier que les index sont créés

**4. Fonction de validation property_id** :
- [ ] Utiliser la fonction existante `validate_property_id(db: Session, property_id: int) -> bool` dans `backend/api/utils/validation.py`
- [ ] Ajouter logs : `[Amortizations] Validation property_id={property_id}`

**5. Endpoints API - Modifications avec logs** :
- [ ] Modifier `GET /api/amortization/types` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Amortizations] GET /api/amortization/types - property_id={property_id}`
  - Filtrer toutes les requêtes : `query = query.filter(AmortizationType.property_id == property_id)`
  - Valider property_id avec `validate_property_id(db, property_id)`
  - Ajouter log : `[Amortizations] Retourné {count} types pour property_id={property_id}`
- [ ] Modifier `POST /api/amortization/types` :
  - Ajouter `property_id` dans `AmortizationTypeCreate` model
  - Ajouter log : `[Amortizations] POST /api/amortization/types - property_id={property_id}`
  - Valider property_id avant création
  - Ajouter log : `[Amortizations] AmortizationType créé: id={id}, property_id={property_id}`
- [ ] Modifier `PUT /api/amortization/types/{id}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Amortizations] PUT /api/amortization/types/{id} - property_id={property_id}`
  - Filtrer : `amortization_type = db.query(AmortizationType).filter(AmortizationType.id == id, AmortizationType.property_id == property_id).first()`
  - Retourner 404 si amortization_type n'appartient pas à property_id
  - Ajouter log : `[Amortizations] AmortizationType {id} mis à jour pour property_id={property_id}`
- [ ] Modifier `DELETE /api/amortization/types/{id}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Amortizations] DELETE /api/amortization/types/{id} - property_id={property_id}`
  - Filtrer : `amortization_type = db.query(AmortizationType).filter(AmortizationType.id == id, AmortizationType.property_id == property_id).first()`
  - Retourner 404 si amortization_type n'appartient pas à property_id
  - Ajouter log : `[Amortizations] AmortizationType {id} supprimé pour property_id={property_id}`
- [ ] Modifier `GET /api/amortization/types/{id}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer : `amortization_type = db.query(AmortizationType).filter(AmortizationType.id == id, AmortizationType.property_id == property_id).first()`
  - Retourner 404 si amortization_type n'appartient pas à property_id
  - Ajouter log : `[Amortizations] GET /api/amortization/types/{id} - property_id={property_id}`
- [ ] Modifier `GET /api/amortization/types/{id}/amount` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer : `amortization_type = db.query(AmortizationType).filter(AmortizationType.id == id, AmortizationType.property_id == property_id).first()`
  - Filtrer les transactions par `property_id` dans le calcul
  - Ajouter log : `[Amortizations] GET amount - type_id={id}, property_id={property_id}`
- [ ] Modifier `GET /api/amortization/types/{id}/cumulated` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer : `amortization_type = db.query(AmortizationType).filter(AmortizationType.id == id, AmortizationType.property_id == property_id).first()`
  - Filtrer les transactions par `property_id` dans le calcul
  - Ajouter log : `[Amortizations] GET cumulated - type_id={id}, property_id={property_id}`
- [ ] Modifier `GET /api/amortization/types/{id}/transaction-count` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer : `amortization_type = db.query(AmortizationType).filter(AmortizationType.id == id, AmortizationType.property_id == property_id).first()`
  - Filtrer les transactions par `property_id` dans le calcul
  - Ajouter log : `[Amortizations] GET transaction-count - type_id={id}, property_id={property_id}`
- [ ] Modifier `GET /api/amortization/results` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer via `Transaction.property_id` : `query = query.join(Transaction).filter(Transaction.property_id == property_id)`
  - Ajouter log : `[Amortizations] GET results - property_id={property_id}`
- [ ] Modifier `GET /api/amortization/results/aggregated` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer via `Transaction.property_id`
  - Ajouter log : `[Amortizations] GET results/aggregated - property_id={property_id}`
- [ ] Modifier `GET /api/amortization/results/details` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer via `Transaction.property_id`
  - Ajouter log : `[Amortizations] GET results/details - property_id={property_id}`
- [ ] Modifier `POST /api/amortization/recalculate` :
  - Ajouter `property_id: int = Body(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Amortizations] POST recalculate - property_id={property_id}`
  - Passer `property_id` à `recalculate_all_amortizations`
  - Ajouter log : `[Amortizations] Recalcul terminé pour property_id={property_id}`

**6. Fonctions utilitaires** :
- [ ] Modifier `recalculate_transaction_amortization` dans `backend/api/services/amortization_service.py` :
  - Ajouter paramètre `property_id: int`
  - Filtrer les transactions : `query = query.filter(Transaction.property_id == property_id)`
  - Ajouter log : `[AmortizationService] Recalcul amortissement transaction {transaction_id} pour property_id={property_id}`
- [ ] Modifier `recalculate_all_amortizations` dans `backend/api/services/amortization_service.py` :
  - Ajouter paramètre `property_id: int`
  - Filtrer les transactions : `query = query.filter(Transaction.property_id == property_id)`
  - Filtrer les types d'amortissement : `query = query.filter(AmortizationType.property_id == property_id)`
  - Ajouter log : `[AmortizationService] Recalcul tous les amortissements pour property_id={property_id}`
- [ ] Vérifier tous les appels à ces fonctions et passer `property_id`

**7. Validation et gestion d'erreurs** :
- [ ] Ajouter validation dans chaque endpoint : `validate_property_id(db, property_id)` au début
- [ ] Erreur 400 si property_id invalide (n'existe pas dans properties)
- [ ] Erreur 422 si property_id manquant (FastAPI validation automatique)
- [ ] Erreur 404 si amortization_type n'appartient pas à property_id demandé
- [ ] Ajouter logs d'erreur : `[Amortizations] ERREUR: {message} - property_id={property_id}`

**8. Tests d'isolation** :
- [ ] Créer script de test : `backend/scripts/test_amortizations_isolation_phase_11_bis_3_1.py`
- [ ] Le script doit afficher des logs clairs pour chaque test
- [ ] Vérifier l'isolation complète entre 2 propriétés

**Tests d'isolation (script Python)**:
- [ ] Créer 2 propriétés (prop1, prop2)
- [ ] Créer 3 types d'amortissement pour prop1
- [ ] Créer 2 types d'amortissement pour prop2
- [ ] GET /api/amortization/types?property_id=prop1 → doit retourner uniquement les 3 types de prop1
- [ ] GET /api/amortization/types?property_id=prop2 → doit retourner uniquement les 2 types de prop2
- [ ] POST /api/amortization/types avec property_id=prop1 → doit créer un type pour prop1 uniquement
- [ ] PUT /api/amortization/types/{id}?property_id=prop1 → ne peut modifier que les types de prop1
- [ ] DELETE /api/amortization/types/{id}?property_id=prop1 → ne peut supprimer que les types de prop1
- [ ] GET /api/amortization/results/aggregated?property_id=prop1 → doit retourner uniquement les résultats de prop1
- [ ] POST /api/amortization/recalculate?property_id=prop1 → ne doit recalculer que pour prop1

---

### Step 3.2 : Frontend - Page Amortissements avec property_id
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Modifier `AmortizationTable.tsx` pour passer `activeProperty.id` à tous les appels API
- [ ] Modifier `AmortizationConfigCard.tsx` pour passer `activeProperty.id`
- [ ] Vérifier que l'affichage de la table fonctionne avec property_id
- [ ] Vérifier que le recalcul fonctionne avec property_id
- [ ] Créer script de test frontend : `frontend/scripts/test_amortizations_isolation_phase_11_bis_3_2.js`

**Tests d'isolation (script frontend)**:
- [ ] Sélectionner prop1
- [ ] Créer 2 types d'amortissement pour prop1
- [ ] Vérifier qu'ils s'affichent dans la config
- [ ] Changer pour prop2
- [ ] Vérifier que les 2 types de prop1 ne s'affichent PAS
- [ ] Créer 1 type pour prop2
- [ ] Vérifier qu'il s'affiche
- [ ] Revenir à prop1
- [ ] Vérifier que seuls les 2 types de prop1 s'affichent
- [ ] Vérifier que les résultats d'amortissement sont isolés par propriété

**Tests de non-régression (manuel)**:
- [ ] Table d'amortissement : Affichage fonctionne ✅
- [ ] Affichage par catégorie fonctionne ✅
- [ ] Affichage par année fonctionne ✅
- [ ] Calcul automatique fonctionne ✅
- [ ] Recalcul manuel fonctionne ✅
- [ ] Config : Affichage des types fonctionne ✅
- [ ] Création d'un type fonctionne ✅
- [ ] Édition d'un type fonctionne ✅
- [ ] Suppression d'un type fonctionne ✅
- [ ] Calcul du montant par année fonctionne ✅
- [ ] Calcul du montant cumulé fonctionne ✅
- [ ] Comptage des transactions fonctionne ✅

**Validation avant Step 3.3** :
- [ ] Tous les tests d'isolation passent ✅
- [ ] Tous les tests de non-régression passent ✅
- [ ] Aucune erreur dans la console frontend ✅
- [ ] Aucune erreur dans les logs backend ✅
- [ ] Validation explicite de l'utilisateur ✅

---

### Step 3.3 : Migration des données Amortissements existantes
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer un script de migration : `backend/scripts/migrate_amortizations_phase_11_bis_3_3.py`
- [ ] Assigner tous les types d'amortissement existants à la propriété par défaut
- [ ] Vérifier que les résultats d'amortissement sont liés via Transaction.property_id
- [ ] Recalculer tous les amortissements pour la propriété par défaut
- [ ] Créer script de validation : `backend/scripts/validate_amortizations_migration_phase_11_bis_3_3.py`

**Tests**:
- [ ] Tous les types d'amortissement ont un property_id ✅
- [ ] Aucun type orphelin (property_id=NULL) ✅
- [ ] Les résultats d'amortissement sont corrects pour la propriété par défaut ✅
- [ ] Le frontend affiche correctement les amortissements après migration ✅

---

## ONGLET 4 : CRÉDIT

### Fonctionnalités existantes à préserver

**Onglet "Crédit"** :
- ✅ Affichage des configurations de crédit
- ✅ Création d'une configuration de crédit
- ✅ Édition d'une configuration de crédit
- ✅ Suppression d'une configuration de crédit
- ✅ Affichage des mensualités (loan_payments)
- ✅ Upload de fichier Excel pour les mensualités
- ✅ Suppression d'une mensualité
- ✅ Calcul automatique des mensualités

---

### Step 4.1 : Backend - Endpoints Crédit avec property_id
**Status**: ⏳ À FAIRE

**1. Vérifications avant modification** :
- [ ] Vérifier qu'aucune donnée existante ne sera impactée (ou gérer la migration)
- [ ] Lister tous les endpoints à modifier dans `backend/api/routes/loan.py`
- [ ] Identifier toutes les fonctions utilitaires qui utilisent les modèles `LoanConfig` et `LoanPayment`
- [ ] Vérifier les imports et dépendances

**2. Modèles SQLAlchemy** :
- [ ] Ajouter `property_id` au modèle `LoanConfig` dans `backend/database/models.py` :
  - `property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)`
  - Ajouter relation : `property = relationship("Property", back_populates="loan_configs")`
- [ ] Ajouter `property_id` au modèle `LoanPayment` dans `backend/database/models.py` :
  - `property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)`
  - Ajouter relation : `property = relationship("Property", back_populates="loan_payments")`
- [ ] Ajouter index `idx_loan_configs_property_id` sur `loan_configs(property_id)`
- [ ] Ajouter index `idx_loan_payments_property_id` sur `loan_payments(property_id)`
- [ ] Vérifier que les modèles se chargent correctement (pas d'erreur d'import)

**3. Migrations** :
- [ ] Créer migration `backend/database/migrations/add_property_id_to_loan_configs.py` pour ajouter `property_id` à la table `loan_configs` avec contrainte FK et ON DELETE CASCADE
- [ ] Créer migration `backend/database/migrations/add_property_id_to_loan_payments.py` pour ajouter `property_id` à la table `loan_payments` avec contrainte FK et ON DELETE CASCADE
- [ ] Tester les migrations (vérifier que les colonnes sont créées avec les bonnes contraintes)
- [ ] Vérifier que les index sont créés

**4. Fonction de validation property_id** :
- [ ] Utiliser la fonction existante `validate_property_id(db: Session, property_id: int) -> bool` dans `backend/api/utils/validation.py`
- [ ] Ajouter logs : `[Credits] Validation property_id={property_id}`

**5. Endpoints API - Modifications avec logs** :
- [ ] Modifier `GET /api/loan-configs` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Credits] GET /api/loan-configs - property_id={property_id}`
  - Filtrer toutes les requêtes : `query = query.filter(LoanConfig.property_id == property_id)`
  - Valider property_id avec `validate_property_id(db, property_id)`
  - Ajouter log : `[Credits] Retourné {count} configs pour property_id={property_id}`
- [ ] Modifier `POST /api/loan-configs` :
  - Ajouter `property_id` dans `LoanConfigCreate` model
  - Ajouter log : `[Credits] POST /api/loan-configs - property_id={property_id}`
  - Valider property_id avant création
  - Ajouter log : `[Credits] LoanConfig créé: id={id}, property_id={property_id}`
- [ ] Modifier `PUT /api/loan-configs/{id}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Credits] PUT /api/loan-configs/{id} - property_id={property_id}`
  - Filtrer : `loan_config = db.query(LoanConfig).filter(LoanConfig.id == id, LoanConfig.property_id == property_id).first()`
  - Retourner 404 si loan_config n'appartient pas à property_id
  - Ajouter log : `[Credits] LoanConfig {id} mis à jour pour property_id={property_id}`
- [ ] Modifier `DELETE /api/loan-configs/{id}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Credits] DELETE /api/loan-configs/{id} - property_id={property_id}`
  - Filtrer : `loan_config = db.query(LoanConfig).filter(LoanConfig.id == id, LoanConfig.property_id == property_id).first()`
  - Retourner 404 si loan_config n'appartient pas à property_id
  - Ajouter log : `[Credits] LoanConfig {id} supprimé pour property_id={property_id}`
- [ ] Modifier `GET /api/loan-configs/{id}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer : `loan_config = db.query(LoanConfig).filter(LoanConfig.id == id, LoanConfig.property_id == property_id).first()`
  - Retourner 404 si loan_config n'appartient pas à property_id
  - Ajouter log : `[Credits] GET /api/loan-configs/{id} - property_id={property_id}`
- [ ] Modifier `GET /api/loan-payments` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Credits] GET /api/loan-payments - property_id={property_id}`
  - Filtrer toutes les requêtes : `query = query.filter(LoanPayment.property_id == property_id)`
  - Valider property_id avec `validate_property_id(db, property_id)`
  - Ajouter log : `[Credits] Retourné {count} payments pour property_id={property_id}`
- [ ] Modifier `POST /api/loan-payments` :
  - Ajouter `property_id` dans `LoanPaymentCreate` model
  - Ajouter log : `[Credits] POST /api/loan-payments - property_id={property_id}`
  - Valider property_id avant création
  - Ajouter log : `[Credits] LoanPayment créé: id={id}, property_id={property_id}`
- [ ] Modifier `PUT /api/loan-payments/{id}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Credits] PUT /api/loan-payments/{id} - property_id={property_id}`
  - Filtrer : `loan_payment = db.query(LoanPayment).filter(LoanPayment.id == id, LoanPayment.property_id == property_id).first()`
  - Retourner 404 si loan_payment n'appartient pas à property_id
  - Ajouter log : `[Credits] LoanPayment {id} mis à jour pour property_id={property_id}`
- [ ] Modifier `DELETE /api/loan-payments/{id}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Credits] DELETE /api/loan-payments/{id} - property_id={property_id}`
  - Filtrer : `loan_payment = db.query(LoanPayment).filter(LoanPayment.id == id, LoanPayment.property_id == property_id).first()`
  - Retourner 404 si loan_payment n'appartient pas à property_id
  - Ajouter log : `[Credits] LoanPayment {id} supprimé pour property_id={property_id}`
- [ ] Modifier `GET /api/loan-payments/{id}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer : `loan_payment = db.query(LoanPayment).filter(LoanPayment.id == id, LoanPayment.property_id == property_id).first()`
  - Retourner 404 si loan_payment n'appartient pas à property_id
  - Ajouter log : `[Credits] GET /api/loan-payments/{id} - property_id={property_id}`
- [ ] Modifier `POST /api/loan-payments/preview` :
  - Ajouter `property_id: int = Form(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Credits] POST preview - property_id={property_id}, file={filename}`
- [ ] Modifier `POST /api/loan-payments/upload` :
  - Ajouter `property_id: int = Form(..., description="ID de la propriété (obligatoire)")`
  - Passer `property_id` à tous les payments créés
  - Ajouter log : `[Credits] POST upload - property_id={property_id}, file={filename}`
  - Ajouter log : `[Credits] Upload terminé: {count} payments créés pour property_id={property_id}`

**6. Fonctions utilitaires** :
- [ ] Modifier toutes les fonctions qui utilisent `LoanConfig` ou `LoanPayment` pour accepter `property_id`
- [ ] Filtrer toutes les requêtes par `property_id`
- [ ] Ajouter logs pour le debugging
- [ ] Vérifier tous les appels à ces fonctions et passer `property_id`

**7. Validation et gestion d'erreurs** :
- [ ] Ajouter validation dans chaque endpoint : `validate_property_id(db, property_id)` au début
- [ ] Erreur 400 si property_id invalide (n'existe pas dans properties)
- [ ] Erreur 422 si property_id manquant (FastAPI validation automatique)
- [ ] Erreur 404 si loan_config ou loan_payment n'appartient pas à property_id demandé
- [ ] Ajouter logs d'erreur : `[Credits] ERREUR: {message} - property_id={property_id}`

**8. Tests d'isolation** :
- [ ] Créer script de test : `backend/scripts/test_credits_isolation_phase_11_bis_4_1.py`
- [ ] Le script doit afficher des logs clairs pour chaque test
- [ ] Vérifier l'isolation complète entre 2 propriétés

**Tests d'isolation (script Python)**:
- [ ] Créer 2 propriétés (prop1, prop2)
- [ ] Créer 1 configuration de crédit pour prop1
- [ ] Créer 1 configuration de crédit pour prop2
- [ ] GET /api/loan-configs?property_id=prop1 → doit retourner uniquement la config de prop1
- [ ] GET /api/loan-configs?property_id=prop2 → doit retourner uniquement la config de prop2
- [ ] POST /api/loan-configs avec property_id=prop1 → doit créer une config pour prop1 uniquement
- [ ] PUT /api/loan-configs/{id}?property_id=prop1 → ne peut modifier que la config de prop1
- [ ] DELETE /api/loan-configs/{id}?property_id=prop1 → ne peut supprimer que la config de prop1
- [ ] GET /api/loan-payments?property_id=prop1 → doit retourner uniquement les mensualités de prop1
- [ ] POST /api/loan-payments avec property_id=prop1 → doit créer une mensualité pour prop1 uniquement

---

### Step 4.2 : Frontend - Page Crédit avec property_id
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Modifier `LoanConfigCard.tsx` pour passer `activeProperty.id`
- [ ] Modifier `LoanConfigSingleCard.tsx` pour passer `activeProperty.id`
- [ ] Modifier `LoanPaymentTable.tsx` pour passer `activeProperty.id`
- [ ] Modifier `LoanPaymentFileUpload.tsx` pour passer `activeProperty.id`
- [ ] Créer script de test frontend : `frontend/scripts/test_credits_isolation_phase_11_bis_4_2.js`

**Tests d'isolation (script frontend)**:
- [ ] Sélectionner prop1
- [ ] Créer 1 configuration de crédit pour prop1
- [ ] Vérifier qu'elle s'affiche
- [ ] Changer pour prop2
- [ ] Vérifier que la config de prop1 ne s'affiche PAS
- [ ] Créer 1 config pour prop2
- [ ] Vérifier qu'elle s'affiche
- [ ] Revenir à prop1
- [ ] Vérifier que seule la config de prop1 s'affiche
- [ ] Vérifier que les mensualités sont isolées par propriété

**Tests de non-régression (manuel)**:
- [ ] Affichage des configurations fonctionne ✅
- [ ] Création d'une configuration fonctionne ✅
- [ ] Édition d'une configuration fonctionne ✅
- [ ] Suppression d'une configuration fonctionne ✅
- [ ] Affichage des mensualités fonctionne ✅
- [ ] Upload de fichier Excel fonctionne ✅
- [ ] Suppression d'une mensualité fonctionne ✅
- [ ] Calcul automatique des mensualités fonctionne ✅

**Validation avant Step 4.3** :
- [ ] Tous les tests d'isolation passent ✅
- [ ] Tous les tests de non-régression passent ✅
- [ ] Aucune erreur dans la console frontend ✅
- [ ] Aucune erreur dans les logs backend ✅
- [ ] Validation explicite de l'utilisateur ✅

---

### Step 4.3 : Migration des données Crédit existantes
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer un script de migration : `backend/scripts/migrate_credits_phase_11_bis_4_3.py`
- [ ] Assigner toutes les configurations de crédit existantes à la propriété par défaut
- [ ] Assigner toutes les mensualités existantes à la propriété par défaut
- [ ] Créer script de validation : `backend/scripts/validate_credits_migration_phase_11_bis_4_3.py`

**Tests**:
- [ ] Toutes les configurations de crédit ont un property_id ✅
- [ ] Toutes les mensualités ont un property_id ✅
- [ ] Aucune donnée orpheline (property_id=NULL) ✅
- [ ] Le frontend affiche correctement les crédits après migration ✅

---

## ONGLET 5 : COMPTE DE RÉSULTAT

### Fonctionnalités existantes à préserver

**Onglet "Compte de résultat"** :
- ✅ Affichage du compte de résultat par année
- ✅ Calcul automatique du compte de résultat
- ✅ Affichage des catégories (Produits, Charges)
- ✅ Affichage des montants par catégorie

**Config Compte de résultat** :
- ✅ Affichage des mappings (catégorie → level_1, level_2, level_3)
- ✅ Création d'un mapping
- ✅ Édition d'un mapping
- ✅ Suppression d'un mapping
- ✅ Réinitialisation des mappings
- ✅ Configuration des overrides par année
- ✅ Activation/désactivation des overrides

---

### Step 5.1 : Backend - Endpoints Compte de résultat avec property_id
**Status**: ⏳ À FAIRE

**1. Vérifications avant modification** :
- [ ] Vérifier qu'aucune donnée existante ne sera impactée (ou gérer la migration)
- [ ] Lister tous les endpoints à modifier dans `backend/api/routes/compte_resultat.py`
- [ ] Identifier toutes les fonctions du service qui utilisent les modèles `CompteResultatMapping`, `CompteResultatConfig`, `CompteResultatOverride`
- [ ] Identifier toutes les fonctions qui utilisent `Transaction` pour le calcul
- [ ] Vérifier les imports et dépendances

**2. Modèles SQLAlchemy** :
- [ ] Ajouter `property_id` au modèle `CompteResultatMapping` dans `backend/database/models.py` :
  - `property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)`
  - Ajouter relation : `property = relationship("Property", back_populates="compte_resultat_mappings")`
- [ ] Ajouter `property_id` au modèle `CompteResultatConfig` dans `backend/database/models.py` :
  - `property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)`
  - Ajouter relation : `property = relationship("Property", back_populates="compte_resultat_config")`
- [ ] Ajouter `property_id` au modèle `CompteResultatOverride` dans `backend/database/models.py` :
  - `property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)`
  - Ajouter relation : `property = relationship("Property", back_populates="compte_resultat_overrides")`
- [ ] Ajouter index `idx_compte_resultat_mappings_property_id` sur `compte_resultat_mappings(property_id)`
- [ ] Ajouter index `idx_compte_resultat_config_property_id` sur `compte_resultat_config(property_id)`
- [ ] Ajouter index `idx_compte_resultat_override_property_id` sur `compte_resultat_override(property_id)`
- [ ] Vérifier que les modèles se chargent correctement (pas d'erreur d'import)

**3. Migrations** :
- [ ] Créer migration `backend/database/migrations/add_property_id_to_compte_resultat.py` pour ajouter `property_id` aux tables `compte_resultat_mappings`, `compte_resultat_config`, `compte_resultat_override` avec contraintes FK et ON DELETE CASCADE
- [ ] Tester les migrations (vérifier que les colonnes sont créées avec les bonnes contraintes)
- [ ] Vérifier que les index sont créés

**4. Fonction de validation property_id** :
- [ ] Utiliser la fonction existante `validate_property_id(db: Session, property_id: int) -> bool` dans `backend/api/utils/validation.py`
- [ ] Ajouter logs : `[CompteResultat] Validation property_id={property_id}`

**5. Endpoints API - Modifications avec logs** :
- [ ] Modifier `GET /api/compte-resultat/mappings` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[CompteResultat] GET /api/compte-resultat/mappings - property_id={property_id}`
  - Filtrer toutes les requêtes : `query = query.filter(CompteResultatMapping.property_id == property_id)`
  - Valider property_id avec `validate_property_id(db, property_id)`
  - Ajouter log : `[CompteResultat] Retourné {count} mappings pour property_id={property_id}`
- [ ] Modifier `POST /api/compte-resultat/mappings` :
  - Ajouter `property_id` dans `CompteResultatMappingCreate` model
  - Ajouter log : `[CompteResultat] POST /api/compte-resultat/mappings - property_id={property_id}`
  - Valider property_id avant création
  - Ajouter log : `[CompteResultat] Mapping créé: id={id}, property_id={property_id}`
- [ ] Modifier `PUT /api/compte-resultat/mappings/{id}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[CompteResultat] PUT /api/compte-resultat/mappings/{id} - property_id={property_id}`
  - Filtrer : `mapping = db.query(CompteResultatMapping).filter(CompteResultatMapping.id == id, CompteResultatMapping.property_id == property_id).first()`
  - Retourner 404 si mapping n'appartient pas à property_id
  - Ajouter log : `[CompteResultat] Mapping {id} mis à jour pour property_id={property_id}`
- [ ] Modifier `DELETE /api/compte-resultat/mappings/{id}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[CompteResultat] DELETE /api/compte-resultat/mappings/{id} - property_id={property_id}`
  - Filtrer : `mapping = db.query(CompteResultatMapping).filter(CompteResultatMapping.id == id, CompteResultatMapping.property_id == property_id).first()`
  - Retourner 404 si mapping n'appartient pas à property_id
  - Ajouter log : `[CompteResultat] Mapping {id} supprimé pour property_id={property_id}`
- [ ] Modifier `GET /api/compte-resultat/config` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[CompteResultat] GET /api/compte-resultat/config - property_id={property_id}`
  - Filtrer : `config = db.query(CompteResultatConfig).filter(CompteResultatConfig.property_id == property_id).first()`
  - Valider property_id avec `validate_property_id(db, property_id)`
- [ ] Modifier `PUT /api/compte-resultat/config` :
  - Ajouter `property_id` dans `CompteResultatConfigUpdate` model
  - Ajouter log : `[CompteResultat] PUT /api/compte-resultat/config - property_id={property_id}`
  - Valider property_id avant mise à jour
  - Ajouter log : `[CompteResultat] Config mise à jour pour property_id={property_id}`
- [ ] Modifier `GET /api/compte-resultat/calculate` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[CompteResultat] GET /api/compte-resultat/calculate - property_id={property_id}`
  - Passer `property_id` au service de calcul
  - Filtrer les transactions par `property_id` dans le calcul
  - Ajouter log : `[CompteResultat] Calcul terminé pour property_id={property_id}`
- [ ] Modifier `GET /api/compte-resultat/override` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[CompteResultat] GET /api/compte-resultat/override - property_id={property_id}`
  - Filtrer toutes les requêtes : `query = query.filter(CompteResultatOverride.property_id == property_id)`
- [ ] Modifier `GET /api/compte-resultat/override/{year}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[CompteResultat] GET /api/compte-resultat/override/{year} - property_id={property_id}`
  - Filtrer : `override = db.query(CompteResultatOverride).filter(CompteResultatOverride.year == year, CompteResultatOverride.property_id == property_id).first()`
- [ ] Modifier `POST /api/compte-resultat/override` :
  - Ajouter `property_id` dans `CompteResultatOverrideCreate` model
  - Ajouter log : `[CompteResultat] POST /api/compte-resultat/override - property_id={property_id}`
  - Valider property_id avant création
  - Ajouter log : `[CompteResultat] Override créé: year={year}, property_id={property_id}`
- [ ] Modifier `DELETE /api/compte-resultat/override/{year}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[CompteResultat] DELETE /api/compte-resultat/override/{year} - property_id={property_id}`
  - Filtrer : `override = db.query(CompteResultatOverride).filter(CompteResultatOverride.year == year, CompteResultatOverride.property_id == property_id).first()`
  - Retourner 404 si override n'appartient pas à property_id
  - Ajouter log : `[CompteResultat] Override {year} supprimé pour property_id={property_id}`

**6. Fonctions utilitaires** :
- [ ] Modifier toutes les fonctions du service `backend/api/services/compte_resultat_service.py` pour accepter `property_id`
- [ ] Filtrer toutes les requêtes par `property_id`
- [ ] Filtrer les transactions par `property_id` dans les calculs
- [ ] Ajouter logs pour le debugging
- [ ] Vérifier tous les appels à ces fonctions et passer `property_id`

**7. Validation et gestion d'erreurs** :
- [ ] Ajouter validation dans chaque endpoint : `validate_property_id(db, property_id)` au début
- [ ] Erreur 400 si property_id invalide (n'existe pas dans properties)
- [ ] Erreur 422 si property_id manquant (FastAPI validation automatique)
- [ ] Erreur 404 si mapping/config/override n'appartient pas à property_id demandé
- [ ] Ajouter logs d'erreur : `[CompteResultat] ERREUR: {message} - property_id={property_id}`

**8. Tests d'isolation** :
- [ ] Créer script de test : `backend/scripts/test_compte_resultat_isolation_phase_11_bis_5_1.py`
- [ ] Le script doit afficher des logs clairs pour chaque test
- [ ] Vérifier l'isolation complète entre 2 propriétés

**Tests d'isolation (script Python)**:
- [ ] Créer 2 propriétés (prop1, prop2)
- [ ] Créer 3 mappings pour prop1
- [ ] Créer 2 mappings pour prop2
- [ ] GET /api/compte-resultat/mappings?property_id=prop1 → doit retourner uniquement les 3 mappings de prop1
- [ ] GET /api/compte-resultat/mappings?property_id=prop2 → doit retourner uniquement les 2 mappings de prop2
- [ ] GET /api/compte-resultat/calculate?property_id=prop1 → doit calculer uniquement pour prop1
- [ ] GET /api/compte-resultat/override?property_id=prop1 → doit retourner uniquement les overrides de prop1
- [ ] POST /api/compte-resultat/override avec property_id=prop1 → doit créer un override pour prop1 uniquement

---

### Step 5.2 : Frontend - Page Compte de résultat avec property_id
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Modifier `CompteResultatTable.tsx` pour passer `activeProperty.id`
- [ ] Modifier `CompteResultatConfigCard.tsx` pour passer `activeProperty.id`
- [ ] Créer script de test frontend : `frontend/scripts/test_compte_resultat_isolation_phase_11_bis_5_2.js`

**Tests d'isolation (script frontend)**:
- [ ] Sélectionner prop1
- [ ] Créer 2 mappings pour prop1
- [ ] Calculer le compte de résultat pour prop1
- [ ] Vérifier que les résultats s'affichent
- [ ] Changer pour prop2
- [ ] Vérifier que les résultats de prop1 ne s'affichent PAS
- [ ] Créer 1 mapping pour prop2
- [ ] Calculer le compte de résultat pour prop2
- [ ] Vérifier que les résultats s'affichent
- [ ] Revenir à prop1
- [ ] Vérifier que seuls les résultats de prop1 s'affichent

**Tests de non-régression (manuel)**:
- [ ] Affichage du compte de résultat fonctionne ✅
- [ ] Calcul automatique fonctionne ✅
- [ ] Affichage par année fonctionne ✅
- [ ] Affichage des catégories fonctionne ✅
- [ ] Config : Affichage des mappings fonctionne ✅
- [ ] Création d'un mapping fonctionne ✅
- [ ] Édition d'un mapping fonctionne ✅
- [ ] Suppression d'un mapping fonctionne ✅
- [ ] Réinitialisation des mappings fonctionne ✅
- [ ] Configuration des overrides fonctionne ✅
- [ ] Activation/désactivation des overrides fonctionne ✅

**Validation avant Step 5.3** :
- [ ] Tous les tests d'isolation passent ✅
- [ ] Tous les tests de non-régression passent ✅
- [ ] Aucune erreur dans la console frontend ✅
- [ ] Aucune erreur dans les logs backend ✅
- [ ] Validation explicite de l'utilisateur ✅

---

### Step 5.3 : Migration des données Compte de résultat existantes
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer un script de migration : `backend/scripts/migrate_compte_resultat_phase_11_bis_5_3.py`
- [ ] Assigner tous les mappings existants à la propriété par défaut
- [ ] Assigner la config existante à la propriété par défaut
- [ ] Assigner tous les overrides existants à la propriété par défaut
- [ ] Créer script de validation : `backend/scripts/validate_compte_resultat_migration_phase_11_bis_5_3.py`

**Tests**:
- [ ] Tous les mappings ont un property_id ✅
- [ ] La config a un property_id ✅
- [ ] Tous les overrides ont un property_id ✅
- [ ] Aucune donnée orpheline (property_id=NULL) ✅
- [ ] Le frontend affiche correctement le compte de résultat après migration ✅

---

## ONGLET 6 : BILAN

### Fonctionnalités existantes à préserver

**Onglet "Bilan"** :
- ✅ Affichage du bilan par année
- ✅ Calcul automatique du bilan
- ✅ Affichage des catégories (ACTIF, PASSIF)
- ✅ Affichage des sous-catégories
- ✅ Affichage des catégories spéciales (Compte bancaire, Amortissements cumulés, etc.)

**Config Bilan** :
- ✅ Affichage des mappings (catégorie → level_1, level_2, level_3)
- ✅ Création d'un mapping
- ✅ Édition d'un mapping
- ✅ Suppression d'un mapping
- ✅ Réinitialisation des mappings
- ✅ Configuration des catégories spéciales

---

### Step 6.1 : Backend - Endpoints Bilan avec property_id
**Status**: ⏳ À FAIRE

**1. Vérifications avant modification** :
- [ ] Vérifier qu'aucune donnée existante ne sera impactée (ou gérer la migration)
- [ ] Lister tous les endpoints à modifier dans `backend/api/routes/bilan.py`
- [ ] Identifier toutes les fonctions du service qui utilisent les modèles `BilanMapping` et `BilanConfig`
- [ ] Identifier toutes les fonctions qui utilisent `Transaction`, `LoanPayment`, `AmortizationResult` pour le calcul
- [ ] Vérifier les imports et dépendances

**2. Modèles SQLAlchemy** :
- [ ] Ajouter `property_id` au modèle `BilanMapping` dans `backend/database/models.py` :
  - `property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)`
  - Ajouter relation : `property = relationship("Property", back_populates="bilan_mappings")`
- [ ] Ajouter `property_id` au modèle `BilanConfig` dans `backend/database/models.py` :
  - `property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)`
  - Ajouter relation : `property = relationship("Property", back_populates="bilan_config")`
- [ ] Ajouter index `idx_bilan_mappings_property_id` sur `bilan_mappings(property_id)`
- [ ] Ajouter index `idx_bilan_config_property_id` sur `bilan_config(property_id)`
- [ ] Vérifier que les modèles se chargent correctement (pas d'erreur d'import)

**3. Migrations** :
- [ ] Créer migration `backend/database/migrations/add_property_id_to_bilan.py` pour ajouter `property_id` aux tables `bilan_mappings`, `bilan_config` avec contraintes FK et ON DELETE CASCADE
- [ ] Tester les migrations (vérifier que les colonnes sont créées avec les bonnes contraintes)
- [ ] Vérifier que les index sont créés

**4. Fonction de validation property_id** :
- [ ] Utiliser la fonction existante `validate_property_id(db: Session, property_id: int) -> bool` dans `backend/api/utils/validation.py`
- [ ] Ajouter logs : `[Bilan] Validation property_id={property_id}`

**5. Endpoints API - Modifications avec logs** :
- [ ] Modifier `GET /api/bilan/mappings` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Bilan] GET /api/bilan/mappings - property_id={property_id}`
  - Filtrer toutes les requêtes : `query = query.filter(BilanMapping.property_id == property_id)`
  - Valider property_id avec `validate_property_id(db, property_id)`
  - Ajouter log : `[Bilan] Retourné {count} mappings pour property_id={property_id}`
- [ ] Modifier `POST /api/bilan/mappings` :
  - Ajouter `property_id` dans `BilanMappingCreate` model
  - Ajouter log : `[Bilan] POST /api/bilan/mappings - property_id={property_id}`
  - Valider property_id avant création
  - Ajouter log : `[Bilan] Mapping créé: id={id}, property_id={property_id}`
- [ ] Modifier `GET /api/bilan/mappings/{id}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Filtrer : `mapping = db.query(BilanMapping).filter(BilanMapping.id == id, BilanMapping.property_id == property_id).first()`
  - Retourner 404 si mapping n'appartient pas à property_id
  - Ajouter log : `[Bilan] GET /api/bilan/mappings/{id} - property_id={property_id}`
- [ ] Modifier `PUT /api/bilan/mappings/{id}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Bilan] PUT /api/bilan/mappings/{id} - property_id={property_id}`
  - Filtrer : `mapping = db.query(BilanMapping).filter(BilanMapping.id == id, BilanMapping.property_id == property_id).first()`
  - Retourner 404 si mapping n'appartient pas à property_id
  - Ajouter log : `[Bilan] Mapping {id} mis à jour pour property_id={property_id}`
- [ ] Modifier `DELETE /api/bilan/mappings/{id}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Bilan] DELETE /api/bilan/mappings/{id} - property_id={property_id}`
  - Filtrer : `mapping = db.query(BilanMapping).filter(BilanMapping.id == id, BilanMapping.property_id == property_id).first()`
  - Retourner 404 si mapping n'appartient pas à property_id
  - Ajouter log : `[Bilan] Mapping {id} supprimé pour property_id={property_id}`
- [ ] Modifier `GET /api/bilan/config` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Bilan] GET /api/bilan/config - property_id={property_id}`
  - Filtrer : `config = db.query(BilanConfig).filter(BilanConfig.property_id == property_id).first()`
  - Valider property_id avec `validate_property_id(db, property_id)`
- [ ] Modifier `PUT /api/bilan/config` :
  - Ajouter `property_id` dans `BilanConfigUpdate` model
  - Ajouter log : `[Bilan] PUT /api/bilan/config - property_id={property_id}`
  - Valider property_id avant mise à jour
  - Ajouter log : `[Bilan] Config mise à jour pour property_id={property_id}`
- [ ] Modifier `GET /api/bilan/calculate` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Bilan] GET /api/bilan/calculate - property_id={property_id}`
  - Passer `property_id` au service de calcul
  - Filtrer les transactions, loan_payments, amortizations par `property_id` dans le calcul
  - Ajouter log : `[Bilan] Calcul terminé pour property_id={property_id}`
- [ ] Modifier `POST /api/bilan/calculate` :
  - Ajouter `property_id` dans le body
  - Ajouter log : `[Bilan] POST /api/bilan/calculate - property_id={property_id}`
  - Passer `property_id` au service de calcul
  - Ajouter log : `[Bilan] Calcul terminé pour property_id={property_id}`
- [ ] Modifier `GET /api/bilan` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Bilan] GET /api/bilan - property_id={property_id}`
  - Passer `property_id` au service de calcul
  - Ajouter log : `[Bilan] Bilan retourné pour property_id={property_id}`

**6. Fonctions utilitaires** :
- [ ] Modifier toutes les fonctions du service `backend/api/services/bilan_service.py` pour accepter `property_id`
- [ ] Modifier `calculate_compte_bancaire` pour filtrer par `property_id` :
  - Filtrer les transactions par `property_id`
  - Ajouter log : `[BilanService] Calcul compte bancaire pour property_id={property_id}`
- [ ] Modifier `calculate_capital_restant_du` pour filtrer par `property_id` :
  - Filtrer les loan_payments par `property_id`
  - Ajouter log : `[BilanService] Calcul capital restant dû pour property_id={property_id}`
- [ ] Filtrer toutes les requêtes par `property_id`
- [ ] Filtrer les transactions, loan_payments, amortizations par `property_id` dans les calculs
- [ ] Ajouter logs pour le debugging
- [ ] Vérifier tous les appels à ces fonctions et passer `property_id`

**7. Validation et gestion d'erreurs** :
- [ ] Ajouter validation dans chaque endpoint : `validate_property_id(db, property_id)` au début
- [ ] Erreur 400 si property_id invalide (n'existe pas dans properties)
- [ ] Erreur 422 si property_id manquant (FastAPI validation automatique)
- [ ] Erreur 404 si mapping/config n'appartient pas à property_id demandé
- [ ] Ajouter logs d'erreur : `[Bilan] ERREUR: {message} - property_id={property_id}`

**8. Tests d'isolation** :
- [ ] Créer script de test : `backend/scripts/test_bilan_isolation_phase_11_bis_6_1.py`
- [ ] Le script doit afficher des logs clairs pour chaque test
- [ ] Vérifier l'isolation complète entre 2 propriétés

**Tests d'isolation (script Python)**:
- [ ] Créer 2 propriétés (prop1, prop2)
- [ ] Créer 3 mappings pour prop1
- [ ] Créer 2 mappings pour prop2
- [ ] GET /api/bilan/mappings?property_id=prop1 → doit retourner uniquement les 3 mappings de prop1
- [ ] GET /api/bilan/mappings?property_id=prop2 → doit retourner uniquement les 2 mappings de prop2
- [ ] GET /api/bilan/calculate?property_id=prop1 → doit calculer uniquement pour prop1
- [ ] Vérifier que le compte bancaire est calculé uniquement pour prop1
- [ ] Vérifier que le capital restant dû est calculé uniquement pour prop1

---

### Step 6.2 : Frontend - Page Bilan avec property_id
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Modifier `BilanTable.tsx` pour passer `activeProperty.id`
- [ ] Modifier `BilanConfigCard.tsx` pour passer `activeProperty.id`
- [ ] Créer script de test frontend : `frontend/scripts/test_bilan_isolation_phase_11_bis_6_2.js`

**Tests d'isolation (script frontend)**:
- [ ] Sélectionner prop1
- [ ] Créer 2 mappings pour prop1
- [ ] Calculer le bilan pour prop1
- [ ] Vérifier que les résultats s'affichent
- [ ] Changer pour prop2
- [ ] Vérifier que les résultats de prop1 ne s'affichent PAS
- [ ] Créer 1 mapping pour prop2
- [ ] Calculer le bilan pour prop2
- [ ] Vérifier que les résultats s'affichent
- [ ] Revenir à prop1
- [ ] Vérifier que seuls les résultats de prop1 s'affichent
- [ ] Vérifier que le compte bancaire est isolé par propriété
- [ ] Vérifier que le capital restant dû est isolé par propriété

**Tests de non-régression (manuel)**:
- [ ] Affichage du bilan fonctionne ✅
- [ ] Calcul automatique fonctionne ✅
- [ ] Affichage par année fonctionne ✅
- [ ] Affichage des catégories fonctionne ✅
- [ ] Affichage des sous-catégories fonctionne ✅
- [ ] Affichage des catégories spéciales fonctionne ✅
- [ ] Config : Affichage des mappings fonctionne ✅
- [ ] Création d'un mapping fonctionne ✅
- [ ] Édition d'un mapping fonctionne ✅
- [ ] Suppression d'un mapping fonctionne ✅
- [ ] Réinitialisation des mappings fonctionne ✅
- [ ] Configuration des catégories spéciales fonctionne ✅

**Validation avant Step 6.3** :
- [ ] Tous les tests d'isolation passent ✅
- [ ] Tous les tests de non-régression passent ✅
- [ ] Aucune erreur dans la console frontend ✅
- [ ] Aucune erreur dans les logs backend ✅
- [ ] Validation explicite de l'utilisateur ✅

---

### Step 6.3 : Migration des données Bilan existantes
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer un script de migration : `backend/scripts/migrate_bilan_phase_11_bis_6_3.py`
- [ ] Assigner tous les mappings existants à la propriété par défaut
- [ ] Assigner la config existante à la propriété par défaut
- [ ] Créer script de validation : `backend/scripts/validate_bilan_migration_phase_11_bis_6_3.py`

**Tests**:
- [ ] Tous les mappings ont un property_id ✅
- [ ] La config a un property_id ✅
- [ ] Aucune donnée orpheline (property_id=NULL) ✅
- [ ] Le frontend affiche correctement le bilan après migration ✅

---

## ONGLET 7 : PIVOT (Tableaux croisés dynamiques)

### Fonctionnalités existantes à préserver

**Onglet "Pivot"** :
- ✅ Création d'un tableau croisé dynamique
- ✅ Configuration des lignes, colonnes, valeurs
- ✅ Sauvegarde d'un tableau
- ✅ Chargement d'un tableau sauvegardé
- ✅ Suppression d'un tableau
- ✅ Renommage d'un tableau
- ✅ Réorganisation des tableaux (drag & drop)
- ✅ Affichage des détails (transactions détaillées)
- ✅ Export des résultats

---

### Step 7.1 : Backend - Endpoints Pivot avec property_id
**Status**: ⏳ À FAIRE

**1. Vérifications avant modification** :
- [ ] Vérifier qu'aucune donnée existante ne sera impactée (ou gérer la migration)
- [ ] Lister tous les endpoints à modifier dans `backend/api/routes/pivot.py` ou `backend/api/routes/analytics.py`
- [ ] Identifier toutes les fonctions qui utilisent le modèle `PivotConfig`
- [ ] Identifier toutes les fonctions qui utilisent `Transaction` pour les données du pivot
- [ ] Vérifier les imports et dépendances

**2. Modèles SQLAlchemy** :
- [ ] Ajouter `property_id` au modèle `PivotConfig` dans `backend/database/models.py` :
  - `property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)`
  - Ajouter relation : `property = relationship("Property", back_populates="pivot_configs")`
- [ ] Ajouter index `idx_pivot_configs_property_id` sur `pivot_configs(property_id)`
- [ ] Vérifier que les modèles se chargent correctement (pas d'erreur d'import)

**3. Migrations** :
- [ ] Créer migration `backend/database/migrations/add_property_id_to_pivot_configs.py` pour ajouter `property_id` à la table `pivot_configs` avec contrainte FK et ON DELETE CASCADE
- [ ] Tester les migrations (vérifier que les colonnes sont créées avec les bonnes contraintes)
- [ ] Vérifier que les index sont créés

**4. Fonction de validation property_id** :
- [ ] Utiliser la fonction existante `validate_property_id(db: Session, property_id: int) -> bool` dans `backend/api/utils/validation.py`
- [ ] Ajouter logs : `[Pivot] Validation property_id={property_id}`

**5. Endpoints API - Modifications avec logs** :
- [ ] Modifier `GET /api/pivot-configs` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Pivot] GET /api/pivot-configs - property_id={property_id}`
  - Filtrer toutes les requêtes : `query = query.filter(PivotConfig.property_id == property_id)`
  - Valider property_id avec `validate_property_id(db, property_id)`
  - Ajouter log : `[Pivot] Retourné {count} configs pour property_id={property_id}`
- [ ] Modifier `POST /api/pivot-configs` :
  - Ajouter `property_id` dans `PivotConfigCreate` model
  - Ajouter log : `[Pivot] POST /api/pivot-configs - property_id={property_id}`
  - Valider property_id avant création
  - Ajouter log : `[Pivot] PivotConfig créé: id={id}, property_id={property_id}`
- [ ] Modifier `PUT /api/pivot-configs/{id}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Pivot] PUT /api/pivot-configs/{id} - property_id={property_id}`
  - Filtrer : `pivot_config = db.query(PivotConfig).filter(PivotConfig.id == id, PivotConfig.property_id == property_id).first()`
  - Retourner 404 si pivot_config n'appartient pas à property_id
  - Ajouter log : `[Pivot] PivotConfig {id} mis à jour pour property_id={property_id}`
- [ ] Modifier `DELETE /api/pivot-configs/{id}` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Pivot] DELETE /api/pivot-configs/{id} - property_id={property_id}`
  - Filtrer : `pivot_config = db.query(PivotConfig).filter(PivotConfig.id == id, PivotConfig.property_id == property_id).first()`
  - Retourner 404 si pivot_config n'appartient pas à property_id
  - Ajouter log : `[Pivot] PivotConfig {id} supprimé pour property_id={property_id}`
- [ ] Modifier `GET /api/analytics/pivot` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Pivot] GET /api/analytics/pivot - property_id={property_id}`
  - Filtrer les transactions par `property_id` dans le calcul
  - Ajouter log : `[Pivot] Pivot calculé pour property_id={property_id}`
- [ ] Modifier `GET /api/analytics/pivot/details` :
  - Ajouter `property_id: int = Query(..., description="ID de la propriété (obligatoire)")`
  - Ajouter log : `[Pivot] GET /api/analytics/pivot/details - property_id={property_id}`
  - Filtrer les transactions par `property_id` dans le calcul
  - Ajouter log : `[Pivot] Détails pivot retournés pour property_id={property_id}`

**6. Fonctions utilitaires** :
- [ ] Modifier toutes les fonctions qui utilisent `PivotConfig` pour accepter `property_id`
- [ ] Modifier toutes les fonctions qui calculent les données du pivot pour filtrer les transactions par `property_id`
- [ ] Filtrer toutes les requêtes par `property_id`
- [ ] Ajouter logs pour le debugging
- [ ] Vérifier tous les appels à ces fonctions et passer `property_id`

**7. Validation et gestion d'erreurs** :
- [ ] Ajouter validation dans chaque endpoint : `validate_property_id(db, property_id)` au début
- [ ] Erreur 400 si property_id invalide (n'existe pas dans properties)
- [ ] Erreur 422 si property_id manquant (FastAPI validation automatique)
- [ ] Erreur 404 si pivot_config n'appartient pas à property_id demandé
- [ ] Ajouter logs d'erreur : `[Pivot] ERREUR: {message} - property_id={property_id}`

**8. Tests d'isolation** :
- [ ] Créer script de test : `backend/scripts/test_pivot_isolation_phase_11_bis_7_1.py`
- [ ] Le script doit afficher des logs clairs pour chaque test
- [ ] Vérifier l'isolation complète entre 2 propriétés

**Tests d'isolation (script Python)**:
- [ ] Créer 2 propriétés (prop1, prop2)
- [ ] Créer 2 configurations pivot pour prop1
- [ ] Créer 1 configuration pivot pour prop2
- [ ] GET /api/pivot-configs?property_id=prop1 → doit retourner uniquement les 2 configs de prop1
- [ ] GET /api/pivot-configs?property_id=prop2 → doit retourner uniquement la config de prop2
- [ ] POST /api/pivot-configs avec property_id=prop1 → doit créer une config pour prop1 uniquement
- [ ] GET /api/analytics/pivot?property_id=prop1 → doit retourner uniquement les données de prop1
- [ ] GET /api/analytics/pivot/details?property_id=prop1 → doit retourner uniquement les détails de prop1

---

### Step 7.2 : Frontend - Page Pivot avec property_id
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Modifier `PivotTable.tsx` pour passer `activeProperty.id`
- [ ] Modifier `PivotDetailsTable.tsx` pour passer `activeProperty.id`
- [ ] Modifier `PivotFieldSelector.tsx` pour passer `activeProperty.id`
- [ ] Modifier `app/dashboard/pivot/page.tsx` pour passer `activeProperty.id`
- [ ] Créer script de test frontend : `frontend/scripts/test_pivot_isolation_phase_11_bis_7_2.js`

**Tests d'isolation (script frontend)**:
- [ ] Sélectionner prop1
- [ ] Créer 1 tableau pivot pour prop1
- [ ] Vérifier qu'il s'affiche
- [ ] Changer pour prop2
- [ ] Vérifier que le tableau de prop1 ne s'affiche PAS
- [ ] Créer 1 tableau pour prop2
- [ ] Vérifier qu'il s'affiche
- [ ] Revenir à prop1
- [ ] Vérifier que seul le tableau de prop1 s'affiche
- [ ] Vérifier que les données du tableau sont isolées par propriété

**Tests de non-régression (manuel)**:
- [ ] Création d'un tableau fonctionne ✅
- [ ] Configuration des lignes fonctionne ✅
- [ ] Configuration des colonnes fonctionne ✅
- [ ] Configuration des valeurs fonctionne ✅
- [ ] Sauvegarde d'un tableau fonctionne ✅
- [ ] Chargement d'un tableau fonctionne ✅
- [ ] Suppression d'un tableau fonctionne ✅
- [ ] Renommage d'un tableau fonctionne ✅
- [ ] Réorganisation des tableaux fonctionne ✅
- [ ] Affichage des détails fonctionne ✅
- [ ] Export des résultats fonctionne ✅

**Validation avant Step 7.3** :
- [ ] Tous les tests d'isolation passent ✅
- [ ] Tous les tests de non-régression passent ✅
- [ ] Aucune erreur dans la console frontend ✅
- [ ] Aucune erreur dans les logs backend ✅
- [ ] Validation explicite de l'utilisateur ✅

---

### Step 7.3 : Migration des données Pivot existantes
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer un script de migration : `backend/scripts/migrate_pivot_phase_11_bis_7_3.py`
- [ ] Assigner toutes les configurations pivot existantes à la propriété par défaut
- [ ] Créer script de validation : `backend/scripts/validate_pivot_migration_phase_11_bis_7_3.py`

**Tests**:
- [ ] Toutes les configurations pivot ont un property_id ✅
- [ ] Aucune donnée orpheline (property_id=NULL) ✅
- [ ] Le frontend affiche correctement les tableaux pivot après migration ✅

---

## TESTS FINAUX

### Tests d'intégration complets
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer 2 propriétés via l'interface
- [ ] Pour chaque onglet, créer des données pour les 2 propriétés
- [ ] Vérifier que chaque propriété ne voit que ses propres données
- [ ] Vérifier que toutes les fonctionnalités fonctionnent pour chaque propriété
- [ ] Vérifier qu'il n'y a aucun mélange de données entre propriétés
- [ ] Créer script de test complet : `backend/scripts/test_integration_complete_phase_11_bis.py`

**Tests**:
- [ ] Transactions : Isolation complète ✅
- [ ] Mappings : Isolation complète ✅
- [ ] Amortissements : Isolation complète ✅
- [ ] Crédit : Isolation complète ✅
- [ ] Compte de résultat : Isolation complète ✅
- [ ] Bilan : Isolation complète ✅
- [ ] Pivot : Isolation complète ✅
- [ ] Aucune régression fonctionnelle ✅

---

## Notes importantes

⚠️ **Rappel Best Practices**:
- Ne jamais cocher [x] avant que les tests soient créés ET exécutés ET validés
- Toujours créer un test script (.py ou .js) après chaque implémentation
- **Convention de nommage des scripts de test** : `test_*_phase_11_bis_X_Y.py` ou `.js`
- Toujours proposer le test à l'utilisateur avant exécution
- Toujours montrer l'impact frontend à chaque étape
- Ne cocher [x] qu'après confirmation explicite de l'utilisateur
- **NE JAMAIS COMMITER SANS ACCORD EXPLICITE DE L'UTILISATEUR**
- **TOUJOURS LIRE `docs/workflow/BEST_PRACTICES.md` AVANT TOUTE MODIFICATION**
- **CONSULTER `docs/workflow/ERROR_INVESTIGATION.md` EN CAS D'ERREURS**
- **VÉRIFIER LES ERREURS FRONTEND AVEC `docs/workflow/check_frontend_errors.js`**

**Légende Status**:
- ⏳ À FAIRE - Pas encore commencé
- ⏸️ EN ATTENTE - En attente de validation
- 🔄 EN COURS - En cours d'implémentation
- ✅ TERMINÉ - Terminé et validé par l'utilisateur

---

**Dernière mise à jour**: 2026-01-22

