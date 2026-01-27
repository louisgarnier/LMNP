
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
- **AllowedMappings** : 50 mappings hardcodés dupliqués pour cette propriété
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
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer la table `properties` dans la base de données
- [ ] Créer le modèle SQLAlchemy `Property`
- [ ] Ajouter les champs : id, name, address, created_at, updated_at
- [ ] Ajouter contrainte UNIQUE sur `name`
- [ ] Créer une migration pour la table
- [ ] Créer un script de test : `backend/scripts/test_property_model_phase_11_bis_0_1.py`
- [ ] Tester la création, lecture, modification, suppression de propriétés
- [ ] Créer fonction d'initialisation des templates : `initialize_default_templates_for_property(property_id)`
  - Initialiser 50 AllowedMappings hardcodés
  - Initialiser 7 AmortizationTypes hardcodés
  - Initialiser CompteResultatMappings par défaut
  - Initialiser CompteResultatConfig par défaut
  - Initialiser BilanMappings par défaut
  - Initialiser BilanConfig par défaut

**Tests**:
- [ ] Créer une propriété
- [ ] Lire une propriété
- [ ] Modifier une propriété
- [ ] Supprimer une propriété
- [ ] Vérifier les contraintes (name unique, etc.)
- [ ] Vérifier que l'initialisation des templates fonctionne à la création
- [ ] Vérifier que les 50 AllowedMappings sont créés
- [ ] Vérifier que les 7 AmortizationTypes sont créés
- [ ] Vérifier que les CompteResultatMappings sont créés
- [ ] Vérifier que les BilanMappings sont créés

---

### Step 0.2 : Frontend - Page d'accueil et contexte Property
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer un contexte PropertyContext pour gérer la propriété active
- [ ] Créer une page d'accueil (`frontend/app/page.tsx`) avec sélection de propriété
- [ ] Afficher les propriétés sous forme de cards
- [ ] Permettre la création d'une nouvelle propriété (modal)
- [ ] Permettre la sélection d'une propriété
- [ ] Après sélection d'une propriété : Rediriger vers `/dashboard`
- [ ] Modifier Header pour afficher la propriété active et permettre de changer
- [ ] Modifier DashboardLayout pour rediriger si aucune propriété sélectionnée
- [ ] Stocker la propriété active dans localStorage

**Tests**:
- [ ] Affichage de toutes les propriétés (cards avec nom, adresse, date de création)
- [ ] Création d'une nouvelle propriété (modal avec validation)
- [ ] Sélection d'une propriété (redirection vers dashboard)
- [ ] Header affiche la propriété active avec bouton "Changer"
- [ ] Redirection automatique si aucune propriété sélectionnée
- [ ] Persistance dans localStorage (propriété restaurée au rechargement)

---

## ONGLET 1 : TRANSACTIONS

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

---

### Step 1.1 : Backend - Endpoints Transactions avec property_id
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Ajouter `property_id` à la table `transactions` (migration avec FOREIGN KEY)
- [ ] Ajouter `property_id` à la table `enriched_transactions` (migration avec FOREIGN KEY)
- [ ] Modifier `GET /api/transactions` pour accepter `property_id` (query param obligatoire)
- [ ] Modifier `POST /api/transactions` pour inclure `property_id` dans le body
- [ ] Modifier `PUT /api/transactions/{id}` pour filtrer par `property_id`
- [ ] Modifier `DELETE /api/transactions/{id}` pour filtrer par `property_id`
- [ ] Modifier `GET /api/transactions/unique-values` pour filtrer par `property_id`
- [ ] Modifier `GET /api/transactions/sum-by-level1` pour filtrer par `property_id`
- [ ] Modifier `GET /api/transactions/export` pour filtrer par `property_id`
- [ ] Modifier `GET /api/transactions/{id}` pour filtrer par `property_id`
- [ ] Modifier `POST /api/transactions/import` pour inclure `property_id` dans le FormData
- [ ] Modifier `recalculate_balances_from_date` pour accepter `property_id`
- [ ] Modifier `recalculate_all_balances` pour accepter `property_id`
- [ ] Ajouter validation : erreur 400 si property_id invalide, 422 si manquant
- [ ] Créer script de test : `backend/scripts/test_transactions_isolation_phase_11_bis_1_1.py`

**Tests d'isolation (script Python)**:
- [ ] Créer 2 propriétés (prop1, prop2)
- [ ] Créer 5 transactions pour prop1
- [ ] Créer 3 transactions pour prop2
- [ ] GET /api/transactions?property_id=prop1 → doit retourner uniquement les 5 transactions de prop1
- [ ] GET /api/transactions?property_id=prop2 → doit retourner uniquement les 3 transactions de prop2
- [ ] POST /api/transactions avec property_id=prop1 → doit créer une transaction pour prop1 uniquement
- [ ] PUT /api/transactions/{id}?property_id=prop1 → ne peut modifier que les transactions de prop1
- [ ] DELETE /api/transactions/{id}?property_id=prop1 → ne peut supprimer que les transactions de prop1
- [ ] Tentative d'accès à une transaction de prop2 avec property_id=prop1 → doit retourner 404
- [ ] Import de transactions avec property_id=prop1 → doit créer uniquement pour prop1
- [ ] Recalcul des soldes pour prop1 → ne doit affecter que les transactions de prop1

---

### Step 1.2 : Frontend - Page Transactions avec property_id
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Modifier `frontend/app/dashboard/transactions/page.tsx` pour utiliser `useProperty()`
- [ ] Modifier `TransactionsTable.tsx` pour passer `activeProperty.id` à tous les appels API
- [ ] Modifier `UnclassifiedTransactionsTable.tsx` pour passer `activeProperty.id`
- [ ] Modifier `FileUpload.tsx` / `ColumnMappingModal.tsx` pour passer `activeProperty.id` à l'import
- [ ] Modifier `ImportLog.tsx` pour utiliser `activeProperty.id`
- [ ] Ajouter réinitialisation de la page à 1 quand la propriété change
- [ ] Ajouter réinitialisation du total et des transactions quand la propriété change
- [ ] Vérifier que tous les filtres fonctionnent avec property_id
- [ ] Vérifier que le tri fonctionne avec property_id
- [ ] Vérifier que la pagination fonctionne avec property_id
- [ ] Créer script de test frontend : `frontend/scripts/test_transactions_isolation_phase_11_bis_1_2.js`

**Tests d'isolation (script frontend)**:
- [ ] Créer 2 propriétés via l'interface
- [ ] Sélectionner prop1
- [ ] Créer 3 transactions pour prop1
- [ ] Vérifier qu'elles s'affichent dans l'onglet Transactions
- [ ] Changer pour prop2
- [ ] Vérifier que les 3 transactions de prop1 ne s'affichent PAS
- [ ] Créer 2 transactions pour prop2
- [ ] Vérifier qu'elles s'affichent
- [ ] Revenir à prop1
- [ ] Vérifier que seules les 3 transactions de prop1 s'affichent

**Tests de non-régression (manuel)**:
- [ ] Onglet "Transactions" : Toutes les transactions s'affichent ✅
- [ ] Tri par colonne fonctionne ✅
- [ ] Filtres fonctionnent ✅
- [ ] Pagination fonctionne ✅
- [ ] Édition inline fonctionne ✅
- [ ] Suppression fonctionne ✅
- [ ] Suppression multiple fonctionne ✅
- [ ] Classification inline fonctionne ✅
- [ ] Export Excel/CSV fonctionne ✅
- [ ] Onglet "Non classées" : Seules les non classées s'affichent ✅
- [ ] Onglet "Load Trades" : Upload fonctionne ✅
- [ ] Mapping des colonnes fonctionne ✅
- [ ] Import fonctionne ✅
- [ ] Détection des doublons fonctionne ✅
- [ ] Affichage des erreurs fonctionne ✅
- [ ] Compteur de transactions fonctionne ✅
- [ ] Recalcul des soldes fonctionne ✅

**Validation avant Step 1.3** :
- [ ] Tous les tests d'isolation passent ✅
- [ ] Tous les tests de non-régression passent ✅
- [ ] Aucune erreur dans la console frontend ✅
- [ ] Aucune erreur dans les logs backend ✅
- [ ] Validation explicite de l'utilisateur ✅

---

### Step 1.3 : Migration des données Transactions existantes
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer un script de migration : `backend/scripts/migrate_transactions_phase_11_bis_1_3.py`
- [ ] Créer une propriété par défaut ("Appartement 1")
- [ ] Assigner toutes les transactions existantes à cette propriété
- [ ] Vérifier qu'aucune transaction n'a property_id=NULL après migration
- [ ] Recalculer tous les soldes pour la propriété par défaut
- [ ] Créer script de validation : `backend/scripts/validate_transactions_migration_phase_11_bis_1_3.py`

**Tests**:
- [ ] Toutes les transactions ont un property_id ✅
- [ ] Aucune transaction orpheline (property_id=NULL) ✅
- [ ] Les soldes sont corrects pour la propriété par défaut ✅
- [ ] Le frontend affiche correctement les transactions après migration ✅

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

**Tasks**:
- [ ] Ajouter `property_id` à la table `mappings` (migration avec FOREIGN KEY)
- [ ] Ajouter `property_id` à la table `allowed_mappings` (migration avec FOREIGN KEY)
- [ ] Modifier l'index unique de `allowed_mappings` pour inclure `property_id` : `(property_id, level_1, level_2, level_3)`
- [ ] Modifier `GET /api/mappings` pour filtrer par `property_id`
- [ ] Modifier `POST /api/mappings` pour inclure `property_id`
- [ ] Modifier `PUT /api/mappings/{id}` pour filtrer par `property_id`
- [ ] Modifier `DELETE /api/mappings/{id}` pour filtrer par `property_id`
- [ ] Modifier `GET /api/mappings/{id}` pour filtrer par `property_id`
- [ ] Modifier `GET /api/mappings/export` pour filtrer par `property_id`
- [ ] Modifier `GET /api/mappings/unique-values` pour filtrer par `property_id`
- [ ] Modifier `GET /api/mappings/allowed` pour filtrer par `property_id`
- [ ] Modifier `POST /api/mappings/allowed` pour inclure `property_id`
- [ ] Modifier `DELETE /api/mappings/allowed/{id}` pour filtrer par `property_id`
- [ ] Modifier `POST /api/mappings/import` pour inclure `property_id`
- [ ] Modifier `GET /api/mappings/imports/history` pour filtrer par `property_id`
- [ ] Modifier `DELETE /api/mappings/imports/all` pour filtrer par `property_id`
- [ ] Modifier `GET /api/mappings/allowed/level-1` pour filtrer par `property_id`
- [ ] Modifier `GET /api/mappings/allowed/level-2` pour filtrer par `property_id`
- [ ] Modifier `GET /api/mappings/allowed/level-3` pour filtrer par `property_id`
- [ ] Modifier toutes les fonctions de validation pour accepter `property_id`
- [ ] Créer script de test : `backend/scripts/test_mappings_isolation_phase_11_bis_2_1.py`

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

**Tasks**:
- [ ] Ajouter `property_id` à la table `amortization_types` (migration avec FOREIGN KEY)
- [ ] Modifier `GET /api/amortization/types` pour filtrer par `property_id`
- [ ] Modifier `POST /api/amortization/types` pour inclure `property_id`
- [ ] Modifier `PUT /api/amortization/types/{id}` pour filtrer par `property_id`
- [ ] Modifier `DELETE /api/amortization/types/{id}` pour filtrer par `property_id`
- [ ] Modifier `GET /api/amortization/types/{id}` pour filtrer par `property_id`
- [ ] Modifier `GET /api/amortization/types/{id}/amount` pour filtrer par `property_id`
- [ ] Modifier `GET /api/amortization/types/{id}/cumulated` pour filtrer par `property_id`
- [ ] Modifier `GET /api/amortization/types/{id}/transaction-count` pour filtrer par `property_id`
- [ ] Modifier `GET /api/amortization/results` pour filtrer par `property_id` (via Transaction.property_id)
- [ ] Modifier `GET /api/amortization/results/aggregated` pour filtrer par `property_id`
- [ ] Modifier `GET /api/amortization/results/details` pour filtrer par `property_id`
- [ ] Modifier `POST /api/amortization/recalculate` pour accepter `property_id`
- [ ] Modifier `recalculate_transaction_amortization` pour filtrer par `property_id`
- [ ] Modifier `recalculate_all_amortizations` pour accepter `property_id`
- [ ] Créer script de test : `backend/scripts/test_amortizations_isolation_phase_11_bis_3_1.py`

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

**Tasks**:
- [ ] Modifier `GET /api/loan-configs` pour filtrer par `property_id`
- [ ] Modifier `POST /api/loan-configs` pour inclure `property_id`
- [ ] Modifier `PUT /api/loan-configs/{id}` pour filtrer par `property_id`
- [ ] Modifier `DELETE /api/loan-configs/{id}` pour filtrer par `property_id`
- [ ] Modifier `GET /api/loan-configs/{id}` pour filtrer par `property_id`
- [ ] Modifier `GET /api/loan-payments` pour filtrer par `property_id`
- [ ] Modifier `POST /api/loan-payments` pour inclure `property_id`
- [ ] Modifier `PUT /api/loan-payments/{id}` pour filtrer par `property_id`
- [ ] Modifier `DELETE /api/loan-payments/{id}` pour filtrer par `property_id`
- [ ] Modifier `GET /api/loan-payments/{id}` pour filtrer par `property_id`
- [ ] Modifier `POST /api/loan-payments/preview` pour inclure `property_id`
- [ ] Modifier `POST /api/loan-payments/upload` pour inclure `property_id`
- [ ] Créer script de test : `backend/scripts/test_credits_isolation_phase_11_bis_4_1.py`

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

**Tasks**:
- [ ] Modifier `GET /api/compte-resultat/mappings` pour filtrer par `property_id`
- [ ] Modifier `POST /api/compte-resultat/mappings` pour inclure `property_id`
- [ ] Modifier `PUT /api/compte-resultat/mappings/{id}` pour filtrer par `property_id`
- [ ] Modifier `DELETE /api/compte-resultat/mappings/{id}` pour filtrer par `property_id`
- [ ] Modifier `GET /api/compte-resultat/config` pour filtrer par `property_id`
- [ ] Modifier `PUT /api/compte-resultat/config` pour inclure `property_id`
- [ ] Modifier `GET /api/compte-resultat/calculate` pour filtrer par `property_id`
- [ ] Modifier `GET /api/compte-resultat/override` pour filtrer par `property_id`
- [ ] Modifier `GET /api/compte-resultat/override/{year}` pour filtrer par `property_id`
- [ ] Modifier `POST /api/compte-resultat/override` pour inclure `property_id`
- [ ] Modifier `DELETE /api/compte-resultat/override/{year}` pour filtrer par `property_id`
- [ ] Modifier toutes les fonctions du service pour accepter `property_id`
- [ ] Créer script de test : `backend/scripts/test_compte_resultat_isolation_phase_11_bis_5_1.py`

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

**Tasks**:
- [ ] Modifier `GET /api/bilan/mappings` pour filtrer par `property_id`
- [ ] Modifier `POST /api/bilan/mappings` pour inclure `property_id`
- [ ] Modifier `GET /api/bilan/mappings/{id}` pour filtrer par `property_id`
- [ ] Modifier `PUT /api/bilan/mappings/{id}` pour filtrer par `property_id`
- [ ] Modifier `DELETE /api/bilan/mappings/{id}` pour filtrer par `property_id`
- [ ] Modifier `GET /api/bilan/config` pour filtrer par `property_id`
- [ ] Modifier `PUT /api/bilan/config` pour inclure `property_id`
- [ ] Modifier `GET /api/bilan/calculate` pour filtrer par `property_id`
- [ ] Modifier `POST /api/bilan/calculate` pour inclure `property_id`
- [ ] Modifier `GET /api/bilan` pour filtrer par `property_id`
- [ ] Modifier toutes les fonctions du service pour accepter `property_id`
- [ ] Modifier `calculate_compte_bancaire` pour filtrer par `property_id`
- [ ] Modifier `calculate_capital_restant_du` pour filtrer par `property_id`
- [ ] Créer script de test : `backend/scripts/test_bilan_isolation_phase_11_bis_6_1.py`

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

**Tasks**:
- [ ] Modifier `GET /api/pivot-configs` pour filtrer par `property_id`
- [ ] Modifier `POST /api/pivot-configs` pour inclure `property_id`
- [ ] Modifier `PUT /api/pivot-configs/{id}` pour filtrer par `property_id`
- [ ] Modifier `DELETE /api/pivot-configs/{id}` pour filtrer par `property_id`
- [ ] Modifier `GET /api/pivot-configs/{id}` pour filtrer par `property_id`
- [ ] Modifier `GET /api/analytics/pivot` pour filtrer par `property_id`
- [ ] Modifier `GET /api/analytics/pivot/details` pour filtrer par `property_id`
- [ ] Ajouter `property_id` à la table `pivot_configs` (migration)
- [ ] Créer script de test : `backend/scripts/test_pivot_isolation_phase_11_bis_7_1.py`

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

