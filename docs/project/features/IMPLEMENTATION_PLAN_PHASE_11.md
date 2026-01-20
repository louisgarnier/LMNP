# Phase 11 : Multi-propriétés (Appartements)

**Status**: ⏳ À FAIRE  
**Environnement**: Local uniquement  
**Durée estimée**: 2-3 semaines

## Objectif

Permettre la gestion de plusieurs appartements/propriétés dans l'application. Actuellement, toutes les données sont globales et ne permettent pas de distinguer plusieurs propriétés.

## Vue d'ensemble

Cette phase implique :
- Ajout d'une table `properties` pour stocker les appartements
- Ajout d'un champ `property_id` à toutes les tables existantes
- Modification de tous les endpoints backend pour filtrer par propriété
- Création d'une page d'accueil avec sélection de propriété
- Migration des données existantes vers une propriété par défaut

## Étapes principales

### Step 11.1 : Backend - Table et modèle Property
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer la table `properties` dans la base de données
- [ ] Créer le modèle SQLAlchemy `Property`
- [ ] Ajouter les champs : id, name, address, created_at, updated_at
- [ ] Créer une migration pour la table

**Deliverables**:
- Table `properties` créée
- Modèle `Property` dans `backend/database/models.py`
- Migration créée et testée

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
- [ ] Créer des migrations pour ajouter `property_id` à chaque table
- [ ] Ajouter les ForeignKey et Index nécessaires
- [ ] Tester les migrations

**Deliverables**:
- Toutes les tables ont un champ `property_id`
- Migrations créées et testées
- Index créés pour les performances

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
- [ ] Tester tous les endpoints

**Deliverables**:
- Endpoints CRUD fonctionnels
- Modèles Pydantic créés
- Tests validés

---

### Step 11.4 : Backend - Modification des endpoints existants pour filtrer par property_id
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Modifier tous les endpoints pour accepter `property_id` (query param ou header)
- [ ] Filtrer toutes les requêtes par `property_id`
- [ ] S'assurer que les créations incluent `property_id`
- [ ] Tester tous les endpoints modifiés

**Tables concernées**:
- Transactions
- Mappings
- Loan configs/payments
- Amortizations
- Compte de résultat
- Bilan

**Deliverables**:
- Tous les endpoints filtrent par `property_id`
- Tests validés

---

### Step 11.5 : Backend - Migration des données existantes
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer un script de migration
- [ ] Créer une propriété par défaut (ex: "Appartement 1")
- [ ] Assigner toutes les données existantes à cette propriété
- [ ] Vérifier l'intégrité des données après migration

**Deliverables**:
- Script de migration créé
- Données existantes migrées vers une propriété par défaut
- Vérification de l'intégrité

---

### Step 11.6 : Frontend - API Client pour les propriétés
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Ajouter les fonctions API dans `frontend/src/api/client.ts`
- [ ] Créer les interfaces TypeScript pour Property
- [ ] Tester les appels API

**Deliverables**:
- API client fonctionnel
- Interfaces TypeScript créées

---

### Step 11.7 : Frontend - Page d'accueil avec sélection de propriété
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer une page d'accueil (`/` ou `/dashboard`)
- [ ] Afficher les propriétés sous forme de cards
- [ ] Permettre la création d'une nouvelle propriété
- [ ] Permettre la sélection d'une propriété
- [ ] Rediriger vers les pages existantes avec la propriété sélectionnée

**Deliverables**:
- Page d'accueil créée
- Sélection de propriété fonctionnelle
- Création de propriété possible

---

### Step 11.8 : Frontend - Contexte de propriété active
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer un contexte React pour la propriété active
- [ ] Stocker la propriété sélectionnée (localStorage)
- [ ] Utiliser le contexte dans toutes les pages
- [ ] Passer `property_id` à tous les appels API

**Deliverables**:
- Contexte de propriété créé
- Toutes les pages utilisent le contexte
- `property_id` passé à tous les appels API

---

### Step 11.9 : Frontend - Modification des pages existantes
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Modifier toutes les pages pour utiliser le contexte de propriété
- [ ] Ajouter un sélecteur de propriété dans la navigation
- [ ] S'assurer que toutes les requêtes incluent `property_id`
- [ ] Tester toutes les fonctionnalités

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
- Tests validés

---

## Notes techniques

### Base de données
- SQLite reste suffisant pour le multi-propriétés
- Ajout de ForeignKey `property_id` partout
- Index sur `property_id` pour les performances

### Migration
- Script Python pour migrer les données existantes
- Création d'une propriété par défaut
- Assignation de toutes les données à cette propriété

### Frontend
- Contexte React pour la propriété active
- localStorage pour persister la sélection
- Redirection si aucune propriété sélectionnée

## Tests

- [ ] Création de plusieurs propriétés
- [ ] Isolation des données entre propriétés
- [ ] Migration des données existantes
- [ ] Toutes les fonctionnalités fonctionnent avec le multi-propriétés

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
