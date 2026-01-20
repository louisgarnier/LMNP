# Phase 11 : Multi-propriétés (Appartements)

**Status**: ⏳ À FAIRE  
**Environnement**: Local uniquement  
**Durée estimée**: 2-3 semaines

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

**Tasks**:
- [ ] Modifier tous les endpoints pour accepter `property_id` (query param obligatoire)
- [ ] Filtrer toutes les requêtes par `property_id`
- [ ] S'assurer que les créations incluent `property_id`
- [ ] Ajouter validation : erreur 400 si property_id manquant
- [ ] Créer des scripts de test pour chaque groupe d'endpoints
- [ ] Tester l'isolation : vérifier qu'on ne peut pas accéder aux données d'une autre propriété

**Tables concernées**:
- Transactions
- Mappings (y compris allowed_mappings)
- Loan configs/payments
- Amortizations
- Compte de résultat
- Bilan

**Deliverables**:
- Tous les endpoints filtrent par `property_id`
- Validation des erreurs si property_id manquant
- Scripts de test pour chaque groupe d'endpoints
- Tests d'isolation validés

**Tests**:
- [ ] Tous les GET filtrent par property_id
- [ ] Tous les POST incluent property_id
- [ ] Tous les PUT filtrent par property_id
- [ ] Tous les DELETE filtrent par property_id
- [ ] Test d'isolation : créer des données pour property_id=1, vérifier qu'on ne peut pas les voir avec property_id=2
- [ ] Test d'isolation : essayer d'accéder à des données d'une autre propriété (doit retourner vide ou 404)

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

**Tasks**:
- [ ] Modifier toutes les pages pour utiliser le contexte de propriété
- [ ] Ajouter un sélecteur de propriété dans la navigation
- [ ] S'assurer que toutes les requêtes incluent `property_id`
- [ ] Ajouter des validations frontend pour vérifier l'isolation
- [ ] Tester toutes les fonctionnalités manuellement
- [ ] Créer un script de test pour valider l'isolation frontend

**Pages concernées**:
- Transactions
- Mapping
- États financiers (Compte de résultat, Bilan)
- Crédit
- Amortissements
- Pivot

**Deliverables**:
- Toutes les pages fonctionnent avec le multi-propriétés
- Sélecteur de propriété dans la navigation
- Validations frontend pour l'isolation
- Script de test : `frontend/scripts/test_property_isolation.js`
- Tests validés

**Tests**:
- [ ] Transactions : isolation par propriété
- [ ] Mappings : isolation par propriété
- [ ] Compte de résultat : isolation par propriété
- [ ] Bilan : isolation par propriété
- [ ] Crédits : isolation par propriété
- [ ] Amortissements : isolation par propriété
- [ ] Changement de propriété : les données changent correctement
- [ ] Sélecteur de propriété : fonctionne dans toutes les pages
- [ ] Validation : impossible d'accéder aux données d'une autre propriété

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

**Dernière mise à jour**: [Date]
