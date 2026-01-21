# Phase 11 : Multi-propriétés (Appartements)

**Status**: ⏳ À FAIRE  
**Environnement**: Local uniquement  
**Durée estimée**: 2-3 semaines

## ⚠️ RAPPELS IMPORTANTS

**AVANT TOUTE MODIFICATION DE CODE :**
1. **Lire `docs/workflow/BEST_PRACTICES.md`** - Obligatoire avant toute modification
2. **Consulter `docs/workflow/ERROR_INVESTIGATION.md`** - En cas d'erreurs
3. **Vérifier les erreurs frontend** - Utiliser `docs/workflow/check_frontend_errors.js` si disponible

**NE JAMAIS COMMITER SANS ACCORD EXPLICITE DE L'UTILISATEUR**

## Objectif

Permettre la gestion de plusieurs appartements/propriétés dans l'application. Actuellement, toutes les données sont globales et ne permettent pas de distinguer plusieurs propriétés.

**Principe d'isolation** : Toutes les données sont strictement isolées par propriété via `property_id`. Aucune donnée ne peut être mélangée entre propriétés.

## Vue d'ensemble

Cette phase implique :
- Ajout d'une table `properties` pour stocker les appartements
- Ajout d'un champ `property_id` à toutes les tables existantes (isolation stricte)
- Modification de tous les endpoints backend pour filtrer par propriété
- Création d'une page d'accueil avec sélection de propriété
- Migration des données existantes vers une propriété par défaut
- Tests à chaque étape pour garantir l'isolation
- Validations frontend pour s'assurer que les données sont bien isolées

## Principe d'isolation

**Toutes les données suivantes sont isolées par propriété** :
- Transactions et enriched_transactions
- Mappings (y compris mappings hardcodés modifiables par propriété)
- Bilan (mappings, data, config)
- Amortissements (results)
- Compte de résultat (mappings, data, config, overrides)
- Crédits (loan_configs, loan_payments)

**Note** : Les vues agrégées (somme de tous les crédits, total de tous les résultats) seront implémentées en Phase 13 (Dashboards) avec des dashboards par propriété ET des dashboards mixtes.

## Étapes principales

### Step 11.1 : Backend - Table et modèle Property
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer la table `properties` dans la base de données
- [ ] Créer le modèle SQLAlchemy `Property`
- [ ] Ajouter les champs : id, name, address, created_at, updated_at
- [ ] Créer une migration pour la table
- [ ] Créer un script de test pour valider la création de la table
- [ ] Tester la création, lecture, modification, suppression de propriétés

**Deliverables**:
- Table `properties` créée
- Modèle `Property` dans `backend/database/models.py`
- Migration créée et testée
- Script de test : `backend/scripts/test_property_model_step11_1.py`
- Tests validés (CRUD complet)

**Tests**:
- [ ] Créer une propriété
- [ ] Lire une propriété
- [ ] Modifier une propriété
- [ ] Supprimer une propriété
- [ ] Vérifier les contraintes (name unique, etc.)

---

### Step 11.2 : Backend - Ajout de property_id aux tables existantes
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Identifier toutes les tables qui doivent avoir `property_id`
  - transactions
  - enriched_transactions
  - mappings
  - loan_configs
  - loan_payments
  - amortization_results
  - compte_resultat_mappings
  - compte_resultat_data
  - compte_resultat_config
  - compte_resultat_override
  - bilan_mappings
  - bilan_data
  - bilan_config
  - allowed_mappings (mappings hardcodés modifiables par propriété)
- [ ] Créer des migrations pour ajouter `property_id` à chaque table
- [ ] Ajouter les ForeignKey et Index nécessaires
- [ ] Créer un script de test pour valider les migrations
- [ ] Tester les migrations sur une base de test

**Deliverables**:
- Toutes les tables ont un champ `property_id`
- Migrations créées et testées
- Index créés pour les performances
- Script de test : `backend/scripts/test_property_id_migrations_step11_2.py`
- Tests validés (vérification de l'ajout de property_id sur toutes les tables)

**Tests**:
- [ ] Vérifier que property_id est ajouté à toutes les tables
- [ ] Vérifier les ForeignKey vers properties
- [ ] Vérifier les Index sur property_id
- [ ] Vérifier que les contraintes sont correctes

---

### Step 11.3 : Backend - Endpoints CRUD pour les propriétés
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer les endpoints CRUD pour les propriétés
  - GET /api/properties (liste)
  - GET /api/properties/{id} (détail)
  - POST /api/properties (créer)
  - PUT /api/properties/{id} (modifier)
  - DELETE /api/properties/{id} (supprimer)
- [ ] Créer les modèles Pydantic (PropertyCreate, PropertyUpdate, PropertyResponse)
- [ ] Créer un script de test pour valider tous les endpoints
- [ ] Tester tous les endpoints avec TestClient

**Deliverables**:
- Endpoints CRUD fonctionnels dans `backend/api/routes/properties.py`
- Modèles Pydantic créés dans `backend/api/models.py`
- Script de test : `backend/scripts/test_properties_endpoints_step11_3.py`
- Tests validés (tous les endpoints fonctionnent)

**Tests**:
- [ ] GET /api/properties retourne la liste
- [ ] GET /api/properties/{id} retourne le détail
- [ ] POST /api/properties crée une propriété
- [ ] PUT /api/properties/{id} modifie une propriété
- [ ] DELETE /api/properties/{id} supprime une propriété
- [ ] Validation des erreurs (404, 400, etc.)

---

### Step 11.4 : Backend - Modification des endpoints existants pour filtrer par property_id
**Status**: ⏳ À FAIRE

**Description**: Décomposé en sous-steps pour chaque groupe d'endpoints avec tests spécifiques.

---

#### Step 11.4.1 : Backend - Endpoints Transactions avec property_id
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Modifier `GET /api/transactions` pour accepter `property_id` (query param obligatoire)
- [ ] Modifier `POST /api/transactions` pour inclure `property_id` dans le body
- [ ] Modifier `PUT /api/transactions/{id}` pour filtrer par `property_id`
- [ ] Modifier `DELETE /api/transactions/{id}` pour filtrer par `property_id`
- [ ] Modifier `GET /api/transactions/unique-values` pour filtrer par `property_id`
- [ ] Modifier `GET /api/transactions/sum-by-level1` pour filtrer par `property_id`
- [ ] Modifier `GET /api/transactions/export` pour filtrer par `property_id`
- [ ] Ajouter validation : erreur 400 si property_id manquant
- [ ] Créer script de test : `backend/scripts/test_transactions_property_id_step11_4_1.py`
- [ ] Tester l'isolation : créer des transactions pour property_id=1, vérifier qu'on ne peut pas les voir avec property_id=2

**Deliverables**:
- Endpoints transactions modifiés dans `backend/api/routes/transactions.py`
- Script de test créé et exécuté avec succès
- Tests d'isolation validés

**Tests**:
- [ ] GET /api/transactions?property_id=1 retourne uniquement les transactions de la propriété 1
- [ ] POST /api/transactions avec property_id crée une transaction pour cette propriété
- [ ] PUT /api/transactions/{id}?property_id=1 ne peut modifier que les transactions de la propriété 1
- [ ] DELETE /api/transactions/{id}?property_id=1 ne peut supprimer que les transactions de la propriété 1
- [ ] Test d'isolation : transaction créée pour property_id=1 n'est pas visible avec property_id=2
- [ ] Test d'isolation : tentative d'accès à une transaction d'une autre propriété retourne 404
- [ ] Validation : erreur 400 si property_id manquant

---

#### Step 11.4.2 : Backend - Endpoints Mappings avec property_id
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Modifier `GET /api/mappings` pour filtrer par `property_id`
- [ ] Modifier `POST /api/mappings` pour inclure `property_id`
- [ ] Modifier `PUT /api/mappings/{id}` pour filtrer par `property_id`
- [ ] Modifier `DELETE /api/mappings/{id}` pour filtrer par `property_id`
- [ ] Modifier `GET /api/mappings/export` pour filtrer par `property_id`
- [ ] Modifier `GET /api/mappings/allowed` pour filtrer par `property_id` (mappings hardcodés modifiables)
- [ ] Modifier `POST /api/mappings/allowed` pour inclure `property_id`
- [ ] Modifier `PUT /api/mappings/allowed/{id}` pour filtrer par `property_id`
- [ ] Modifier `DELETE /api/mappings/allowed/{id}` pour filtrer par `property_id`
- [ ] Ajouter validation : erreur 400 si property_id manquant
- [ ] Créer script de test : `backend/scripts/test_mappings_property_id_step11_4_2.py`
- [ ] Tester l'isolation : créer des mappings pour property_id=1, vérifier qu'on ne peut pas les voir avec property_id=2

**Deliverables**:
- Endpoints mappings modifiés dans `backend/api/routes/mappings.py`
- Script de test créé et exécuté avec succès
- Tests d'isolation validés

**Tests**:
- [ ] GET /api/mappings?property_id=1 retourne uniquement les mappings de la propriété 1
- [ ] POST /api/mappings avec property_id crée un mapping pour cette propriété
- [ ] PUT /api/mappings/{id}?property_id=1 ne peut modifier que les mappings de la propriété 1
- [ ] DELETE /api/mappings/{id}?property_id=1 ne peut supprimer que les mappings de la propriété 1
- [ ] GET /api/mappings/allowed?property_id=1 retourne uniquement les mappings hardcodés de la propriété 1
- [ ] Test d'isolation : mapping créé pour property_id=1 n'est pas visible avec property_id=2
- [ ] Validation : erreur 400 si property_id manquant

---

#### Step 11.4.3 : Backend - Endpoints Crédits (Loan) avec property_id
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Modifier `GET /api/loan-configs` pour filtrer par `property_id`
- [ ] Modifier `POST /api/loan-configs` pour inclure `property_id`
- [ ] Modifier `PUT /api/loan-configs/{id}` pour filtrer par `property_id`
- [ ] Modifier `DELETE /api/loan-configs/{id}` pour filtrer par `property_id`
- [ ] Modifier `GET /api/loan-payments` pour filtrer par `property_id`
- [ ] Modifier `POST /api/loan-payments` pour inclure `property_id`
- [ ] Modifier `PUT /api/loan-payments/{id}` pour filtrer par `property_id`
- [ ] Modifier `DELETE /api/loan-payments/{id}` pour filtrer par `property_id`
- [ ] Ajouter validation : erreur 400 si property_id manquant
- [ ] Créer script de test : `backend/scripts/test_loans_property_id_step11_4_3.py`
- [ ] Tester l'isolation : créer des crédits pour property_id=1, vérifier qu'on ne peut pas les voir avec property_id=2

**Deliverables**:
- Endpoints crédits modifiés dans `backend/api/routes/loan_configs.py` et `loan_payments.py`
- Script de test créé et exécuté avec succès
- Tests d'isolation validés

**Tests**:
- [ ] GET /api/loan-configs?property_id=1 retourne uniquement les crédits de la propriété 1
- [ ] POST /api/loan-configs avec property_id crée un crédit pour cette propriété
- [ ] GET /api/loan-payments?property_id=1 retourne uniquement les paiements de la propriété 1
- [ ] Test d'isolation : crédit créé pour property_id=1 n'est pas visible avec property_id=2
- [ ] Validation : erreur 400 si property_id manquant

---

#### Step 11.4.4 : Backend - Endpoints Amortissements avec property_id
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Modifier `GET /api/amortization/types` pour filtrer par `property_id`
- [ ] Modifier `POST /api/amortization/types` pour inclure `property_id`
- [ ] Modifier `PUT /api/amortization/types/{id}` pour filtrer par `property_id`
- [ ] Modifier `DELETE /api/amortization/types/{id}` pour filtrer par `property_id`
- [ ] Modifier `GET /api/amortization/results` pour filtrer par `property_id`
- [ ] Modifier `GET /api/amortization/results/aggregated` pour filtrer par `property_id`
- [ ] Ajouter validation : erreur 400 si property_id manquant
- [ ] Créer script de test : `backend/scripts/test_amortizations_property_id_step11_4_4.py`
- [ ] Tester l'isolation : créer des amortissements pour property_id=1, vérifier qu'on ne peut pas les voir avec property_id=2

**Deliverables**:
- Endpoints amortissements modifiés dans `backend/api/routes/amortization_types.py` et `amortization.py`
- Script de test créé et exécuté avec succès
- Tests d'isolation validés

**Tests**:
- [ ] GET /api/amortization/types?property_id=1 retourne uniquement les types d'amortissement de la propriété 1
- [ ] POST /api/amortization/types avec property_id crée un type pour cette propriété
- [ ] GET /api/amortization/results?property_id=1 retourne uniquement les résultats de la propriété 1
- [ ] Test d'isolation : amortissement créé pour property_id=1 n'est pas visible avec property_id=2
- [ ] Validation : erreur 400 si property_id manquant

---

#### Step 11.4.5 : Backend - Endpoints Compte de résultat avec property_id
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Modifier `GET /api/compte-resultat/mappings` pour filtrer par `property_id`
- [ ] Modifier `POST /api/compte-resultat/mappings` pour inclure `property_id`
- [ ] Modifier `PUT /api/compte-resultat/mappings/{id}` pour filtrer par `property_id`
- [ ] Modifier `DELETE /api/compte-resultat/mappings/{id}` pour filtrer par `property_id`
- [ ] Modifier `GET /api/compte-resultat/config` pour filtrer par `property_id`
- [ ] Modifier `PUT /api/compte-resultat/config` pour inclure `property_id`
- [ ] Modifier `GET /api/compte-resultat/calculate` pour filtrer par `property_id`
- [ ] Modifier `GET /api/compte-resultat/overrides` pour filtrer par `property_id`
- [ ] Modifier `POST /api/compte-resultat/overrides` pour inclure `property_id`
- [ ] Modifier `DELETE /api/compte-resultat/overrides/{id}` pour filtrer par `property_id`
- [ ] Ajouter validation : erreur 400 si property_id manquant
- [ ] Créer script de test : `backend/scripts/test_compte_resultat_property_id_step11_4_5.py`
- [ ] Tester l'isolation : créer des données pour property_id=1, vérifier qu'on ne peut pas les voir avec property_id=2

**Deliverables**:
- Endpoints compte de résultat modifiés dans `backend/api/routes/compte_resultat.py`
- Script de test créé et exécuté avec succès
- Tests d'isolation validés

**Tests**:
- [ ] GET /api/compte-resultat/mappings?property_id=1 retourne uniquement les mappings de la propriété 1
- [ ] GET /api/compte-resultat/calculate?property_id=1&years=... calcule uniquement pour la propriété 1
- [ ] Test d'isolation : données créées pour property_id=1 ne sont pas visibles avec property_id=2
- [ ] Validation : erreur 400 si property_id manquant

---

#### Step 11.4.6 : Backend - Endpoints Bilan avec property_id
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Modifier `GET /api/bilan/mappings` pour filtrer par `property_id`
- [ ] Modifier `POST /api/bilan/mappings` pour inclure `property_id`
- [ ] Modifier `PUT /api/bilan/mappings/{id}` pour filtrer par `property_id`
- [ ] Modifier `DELETE /api/bilan/mappings/{id}` pour filtrer par `property_id`
- [ ] Modifier `GET /api/bilan/config` pour filtrer par `property_id`
- [ ] Modifier `PUT /api/bilan/config` pour inclure `property_id`
- [ ] Modifier `GET /api/bilan/calculate` pour filtrer par `property_id`
- [ ] Ajouter validation : erreur 400 si property_id manquant
- [ ] Créer script de test : `backend/scripts/test_bilan_property_id_step11_4_6.py`
- [ ] Tester l'isolation : créer des données pour property_id=1, vérifier qu'on ne peut pas les voir avec property_id=2

**Deliverables**:
- Endpoints bilan modifiés dans `backend/api/routes/bilan.py`
- Script de test créé et exécuté avec succès
- Tests d'isolation validés

**Tests**:
- [ ] GET /api/bilan/mappings?property_id=1 retourne uniquement les mappings de la propriété 1
- [ ] GET /api/bilan/calculate?property_id=1&years=... calcule uniquement pour la propriété 1
- [ ] Test d'isolation : données créées pour property_id=1 ne sont pas visibles avec property_id=2
- [ ] Validation : erreur 400 si property_id manquant

---

### Step 11.5 : Backend - Migration des données existantes
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer un script de migration
- [ ] Créer une propriété par défaut (ex: "Appartement 1")
- [ ] Assigner toutes les données existantes à cette propriété
- [ ] Vérifier l'intégrité des données après migration
- [ ] Créer un script de test pour valider la migration
- [ ] Tester la migration sur une copie de la base

**Deliverables**:
- Script de migration : `backend/scripts/migrate_to_multi_properties_step11_5.py`
- Données existantes migrées vers une propriété par défaut
- Script de validation : `backend/scripts/validate_migration_step11_5.py`
- Vérification de l'intégrité validée

**Tests**:
- [ ] Toutes les transactions ont un property_id
- [ ] Tous les mappings ont un property_id
- [ ] Tous les crédits ont un property_id
- [ ] Tous les amortissements ont un property_id
- [ ] Tous les comptes de résultat ont un property_id
- [ ] Tous les bilans ont un property_id
- [ ] Aucune donnée orpheline (property_id NULL)
- [ ] Comptage : même nombre de données avant/après migration

---

### Step 11.6 : Frontend - API Client pour les propriétés
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Ajouter les fonctions API dans `frontend/src/api/client.ts`
  - getAllProperties()
  - getProperty(id)
  - createProperty(data)
  - updateProperty(id, data)
  - deleteProperty(id)
- [ ] Créer les interfaces TypeScript pour Property
- [ ] Créer un script de test Node.js pour valider les appels API
- [ ] Tester les appels API

**Deliverables**:
- API client fonctionnel dans `frontend/src/api/client.ts`
- Interfaces TypeScript créées
- Script de test : `frontend/scripts/test_properties_api.js`
- Tests validés

**Tests**:
- [ ] getAllProperties() retourne la liste
- [ ] getProperty(id) retourne le détail
- [ ] createProperty() crée une propriété
- [ ] updateProperty() modifie une propriété
- [ ] deleteProperty() supprime une propriété
- [ ] Gestion des erreurs (404, 400, etc.)

---

### Step 11.7 : Frontend - Page d'accueil avec sélection de propriété
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer une page d'accueil (`/` ou `/dashboard`)
- [ ] Afficher les propriétés sous forme de cards
- [ ] Permettre la création d'une nouvelle propriété (modal ou formulaire)
- [ ] Permettre la sélection d'une propriété
- [ ] Rediriger vers les pages existantes avec la propriété sélectionnée
- [ ] Ajouter des validations frontend (nom requis, etc.)
- [ ] Tester la page manuellement

**Deliverables**:
- Page d'accueil créée : `frontend/app/page.tsx` ou `frontend/app/dashboard/page.tsx`
- Sélection de propriété fonctionnelle
- Création de propriété possible
- Validations frontend implémentées

**Tests**:
- [ ] Affichage de toutes les propriétés
- [ ] Création d'une nouvelle propriété
- [ ] Sélection d'une propriété
- [ ] Redirection vers les pages avec property_id
- [ ] Validation : nom requis
- [ ] Validation : nom unique (si applicable)
- [ ] Gestion des erreurs (affichage des messages)

---

### Step 11.8 : Frontend - Contexte de propriété active
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer un contexte React pour la propriété active : `frontend/src/contexts/PropertyContext.tsx`
- [ ] Stocker la propriété sélectionnée (localStorage)
- [ ] Utiliser le contexte dans toutes les pages
- [ ] Passer `property_id` à tous les appels API
- [ ] Ajouter validation : redirection vers page d'accueil si aucune propriété sélectionnée
- [ ] Tester le contexte

**Deliverables**:
- Contexte de propriété créé : `frontend/src/contexts/PropertyContext.tsx`
- Toutes les pages utilisent le contexte
- `property_id` passé à tous les appels API
- Validation : redirection si propriété manquante

**Tests**:
- [ ] Contexte fournit la propriété active
- [ ] Propriété stockée dans localStorage
- [ ] Propriété récupérée au chargement de l'app
- [ ] Redirection si aucune propriété sélectionnée
- [ ] Tous les appels API incluent property_id
- [ ] Changement de propriété met à jour toutes les pages

---

### Step 11.9 : Frontend - Modification des pages existantes
**Status**: ⏳ À FAIRE

**Description**: Décomposé en sous-steps pour chaque page avec tests spécifiques.

---

#### Step 11.9.1 : Frontend - Page Transactions avec property_id
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Modifier `frontend/app/dashboard/transactions/page.tsx` pour utiliser le contexte de propriété
- [ ] Passer `property_id` à tous les appels API de transactions
- [ ] Ajouter validation : vérifier que les transactions affichées correspondent à la propriété sélectionnée
- [ ] Tester manuellement : créer des transactions pour 2 propriétés, vérifier l'isolation
- [ ] Créer script de test : `frontend/scripts/test_transactions_isolation_step11_9_1.js`

**Deliverables**:
- Page transactions modifiée
- Script de test créé et exécuté avec succès
- Tests d'isolation validés

**Tests**:
- [ ] Transactions affichées correspondent à la propriété sélectionnée
- [ ] Création de transaction inclut property_id
- [ ] Modification de transaction vérifie property_id
- [ ] Changement de propriété : les transactions changent correctement
- [ ] Validation : impossible d'accéder aux transactions d'une autre propriété

---

#### Step 11.9.2 : Frontend - Page Mapping avec property_id
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Modifier `frontend/app/dashboard/transactions/page.tsx` (section Mapping) pour utiliser le contexte de propriété
- [ ] Passer `property_id` à tous les appels API de mappings
- [ ] Ajouter validation : vérifier que les mappings affichés correspondent à la propriété sélectionnée
- [ ] Tester manuellement : créer des mappings pour 2 propriétés, vérifier l'isolation
- [ ] Créer script de test : `frontend/scripts/test_mappings_isolation_step11_9_2.js`

**Deliverables**:
- Page mapping modifiée
- Script de test créé et exécuté avec succès
- Tests d'isolation validés

**Tests**:
- [ ] Mappings affichés correspondent à la propriété sélectionnée
- [ ] Création de mapping inclut property_id
- [ ] Changement de propriété : les mappings changent correctement
- [ ] Validation : impossible d'accéder aux mappings d'une autre propriété

---

#### Step 11.9.3 : Frontend - Page États financiers (Compte de résultat) avec property_id
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Modifier `frontend/app/dashboard/etats-financiers/page.tsx` (onglet Compte de résultat) pour utiliser le contexte de propriété
- [ ] Modifier `CompteResultatConfigCard` pour passer `property_id`
- [ ] Modifier `CompteResultatTable` pour passer `property_id`
- [ ] Passer `property_id` à tous les appels API de compte de résultat
- [ ] Ajouter validation : vérifier que les données affichées correspondent à la propriété sélectionnée
- [ ] Tester manuellement : créer des données pour 2 propriétés, vérifier l'isolation
- [ ] Créer script de test : `frontend/scripts/test_compte_resultat_isolation_step11_9_3.js`

**Deliverables**:
- Page compte de résultat modifiée
- Script de test créé et exécuté avec succès
- Tests d'isolation validés

**Tests**:
- [ ] Données affichées correspondent à la propriété sélectionnée
- [ ] Création/modification de mapping inclut property_id
- [ ] Calcul du compte de résultat utilise property_id
- [ ] Changement de propriété : les données changent correctement
- [ ] Validation : impossible d'accéder aux données d'une autre propriété

---

#### Step 11.9.4 : Frontend - Page États financiers (Bilan) avec property_id
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Modifier `frontend/app/dashboard/etats-financiers/page.tsx` (onglet Bilan) pour utiliser le contexte de propriété
- [ ] Modifier `BilanConfigCard` pour passer `property_id`
- [ ] Modifier `BilanTable` pour passer `property_id`
- [ ] Passer `property_id` à tous les appels API de bilan
- [ ] Ajouter validation : vérifier que les données affichées correspondent à la propriété sélectionnée
- [ ] Tester manuellement : créer des données pour 2 propriétés, vérifier l'isolation
- [ ] Créer script de test : `frontend/scripts/test_bilan_isolation_step11_9_4.js`

**Deliverables**:
- Page bilan modifiée
- Script de test créé et exécuté avec succès
- Tests d'isolation validés

**Tests**:
- [ ] Données affichées correspondent à la propriété sélectionnée
- [ ] Création/modification de mapping inclut property_id
- [ ] Calcul du bilan utilise property_id
- [ ] Changement de propriété : les données changent correctement
- [ ] Validation : impossible d'accéder aux données d'une autre propriété

---

#### Step 11.9.5 : Frontend - Page Crédit avec property_id
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Modifier `frontend/app/dashboard/etats-financiers/page.tsx` (onglet Crédit) pour utiliser le contexte de propriété
- [ ] Modifier `LoanConfigCard` pour passer `property_id`
- [ ] Modifier `LoanPaymentTable` pour passer `property_id`
- [ ] Passer `property_id` à tous les appels API de crédits
- [ ] Ajouter validation : vérifier que les crédits affichés correspondent à la propriété sélectionnée
- [ ] Tester manuellement : créer des crédits pour 2 propriétés, vérifier l'isolation
- [ ] Créer script de test : `frontend/scripts/test_credits_isolation_step11_9_5.js`

**Deliverables**:
- Page crédit modifiée
- Script de test créé et exécuté avec succès
- Tests d'isolation validés

**Tests**:
- [ ] Crédits affichés correspondent à la propriété sélectionnée
- [ ] Création de crédit inclut property_id
- [ ] Changement de propriété : les crédits changent correctement
- [ ] Validation : impossible d'accéder aux crédits d'une autre propriété

---

#### Step 11.9.6 : Frontend - Page Amortissements avec property_id
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Modifier `frontend/app/dashboard/amortissements/page.tsx` pour utiliser le contexte de propriété
- [ ] Modifier `AmortizationConfigCard` pour passer `property_id`
- [ ] Modifier `AmortizationTable` pour passer `property_id`
- [ ] Passer `property_id` à tous les appels API d'amortissements
- [ ] Ajouter validation : vérifier que les amortissements affichés correspondent à la propriété sélectionnée
- [ ] Tester manuellement : créer des amortissements pour 2 propriétés, vérifier l'isolation
- [ ] Créer script de test : `frontend/scripts/test_amortizations_isolation_step11_9_6.js`

**Deliverables**:
- Page amortissements modifiée
- Script de test créé et exécuté avec succès
- Tests d'isolation validés

**Tests**:
- [ ] Amortissements affichés correspondent à la propriété sélectionnée
- [ ] Création de type d'amortissement inclut property_id
- [ ] Changement de propriété : les amortissements changent correctement
- [ ] Validation : impossible d'accéder aux amortissements d'une autre propriété

---

#### Step 11.9.7 : Frontend - Navigation et sélecteur de propriété
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Ajouter un sélecteur de propriété dans la navigation (header ou sidebar)
- [ ] Le sélecteur affiche la propriété active
- [ ] Le sélecteur permet de changer de propriété
- [ ] Le changement de propriété met à jour toutes les pages
- [ ] Le changement de propriété sauvegarde dans localStorage
- [ ] Tester le sélecteur dans toutes les pages
- [ ] Créer script de test : `frontend/scripts/test_property_selector_step11_9_7.js`

**Deliverables**:
- Sélecteur de propriété ajouté dans la navigation
- Script de test créé et exécuté avec succès
- Tests validés

**Tests**:
- [ ] Sélecteur affiche la propriété active
- [ ] Changement de propriété met à jour toutes les pages
- [ ] Changement de propriété sauvegarde dans localStorage
- [ ] Sélecteur fonctionne dans toutes les pages
- [ ] Validation : redirection si aucune propriété sélectionnée

---

## Notes techniques

### Base de données
- SQLite reste suffisant pour le multi-propriétés
- Ajout de ForeignKey `property_id` partout
- Index sur `property_id` pour les performances
- Contrainte NOT NULL sur `property_id` (sauf pour certaines tables globales)

### Migration
- Script Python pour migrer les données existantes
- Création d'une propriété par défaut
- Assignation de toutes les données à cette propriété
- Vérification de l'intégrité après migration

### Frontend
- Contexte React pour la propriété active
- localStorage pour persister la sélection
- Redirection si aucune propriété sélectionnée
- Validation : tous les appels API doivent inclure property_id

### Isolation garantie
- Tous les endpoints backend filtrent par property_id
- Validation backend : erreur 400 si property_id manquant
- Validation frontend : vérification que les données affichées correspondent à la propriété sélectionnée
- Tests d'isolation : impossible d'accéder aux données d'une autre propriété

### Mappings hardcodés
- Les mappings hardcodés (`allowed_mappings`) peuvent être modifiés par propriété
- Chaque propriété peut avoir ses propres règles hardcodées
- Script de gestion des mappings hardcodés adapté pour property_id

## Tests finaux

### Tests backend
- [ ] Création de plusieurs propriétés
- [ ] Isolation des données entre propriétés (test d'isolation)
- [ ] Migration des données existantes
- [ ] Tous les endpoints filtrent par property_id
- [ ] Validation : erreur si property_id manquant
- [ ] Validation : impossible d'accéder aux données d'une autre propriété

### Tests frontend
- [ ] Sélection de propriété fonctionne
- [ ] Changement de propriété met à jour toutes les pages
- [ ] Isolation visuelle : les données affichées correspondent à la propriété sélectionnée
- [ ] Toutes les fonctionnalités fonctionnent avec le multi-propriétés
- [ ] Validation : redirection si aucune propriété sélectionnée

### Tests d'intégration
- [ ] Créer 2 propriétés
- [ ] Ajouter des transactions pour chaque propriété
- [ ] Vérifier que chaque propriété ne voit que ses propres transactions
- [ ] Vérifier que les mappings sont isolés
- [ ] Vérifier que les crédits sont isolés
- [ ] Vérifier que les amortissements sont isolés
- [ ] Vérifier que les comptes de résultat sont isolés
- [ ] Vérifier que les bilans sont isolés

## Livrables finaux

- [ ] Table `properties` créée
- [ ] Toutes les tables ont `property_id`
- [ ] Endpoints CRUD pour les propriétés
- [ ] Tous les endpoints filtrent par `property_id`
- [ ] Page d'accueil avec sélection de propriété
- [ ] Contexte de propriété actif
- [ ] Toutes les pages modifiées
- [ ] Données existantes migrées
- [ ] Tests validés

---

## Notes importantes

⚠️ **Rappel Best Practices**:
- Ne jamais cocher [x] avant que les tests soient créés ET exécutés ET validés
- Toujours créer un test script (.py) après chaque implémentation
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

**Dernière mise à jour**: 2025-01-27
