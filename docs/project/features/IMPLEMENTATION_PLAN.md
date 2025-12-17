# Plan d'Implémentation - Application Web LMNP

**Status**: En cours  
**Dernière mise à jour**: 2025-01-XX

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

## Phase 2 : Fonctionnalité 1 - Agrégation des transactions

### Step 2.1 : Service d'agrégation backend
**Status**: ⏸️ EN ATTENTE  
**Description**: Migrer la logique de `1_aggregate_trades.py` en service backend.

**Tasks**:
- [ ] Créer aggregation_service.py
- [ ] Implémenter détection encodage/séparateur
- [ ] Implémenter normalisation colonnes/dates
- [ ] Implémenter détection doublons
- [ ] Créer endpoint POST /api/transactions/upload
- [ ] **Créer test complet avec fichiers CSV réels**
- [ ] **Valider avec l'utilisateur**

**Deliverables**:
- `backend/api/services/aggregation_service.py` - Service d'agrégation
- `backend/api/routes/transactions.py` - Endpoint upload
- `backend/tests/test_aggregation.py` - Tests agrégation

**Tests**:
- [ ] Test upload CSV simple
- [ ] Test upload CSV multiple
- [ ] Test détection encodage (UTF-8, Latin-1, ISO-8859-1, CP1252)
- [ ] Test détection séparateur (; , \t)
- [ ] Test normalisation dates
- [ ] Test normalisation montants
- [ ] Test détection doublons
- [ ] Test gestion erreurs format

**Acceptance Criteria**:
- [ ] Upload CSV fonctionne via API
- [ ] Détection encodage/séparateur automatique
- [ ] Doublons détectés et gérés
- [ ] Transactions stockées en DB
- [ ] Test script exécutable et tous les tests passent
- [ ] **Utilisateur confirme que l'agrégation fonctionne**

**Impact Frontend**: 
- [ ] Créer composant FileUpload
- [ ] Afficher prévisualisation fichiers
- [ ] Afficher résultats upload (nombre transactions, erreurs)
- [ ] Tester upload depuis navigateur

---

### Step 2.2 : Interface upload et visualisation transactions
**Status**: ⏸️ EN ATTENTE  
**Description**: Créer l'interface frontend pour upload CSV et visualiser les transactions.

**Tasks**:
- [ ] Créer composant FileUpload
- [ ] Créer composant TransactionsTable
- [ ] Créer page onglet transactions
- [ ] Implémenter filtrage et recherche
- [ ] **Créer test visuel dans navigateur**
- [ ] **Valider avec l'utilisateur**

**Deliverables**:
- `frontend/app/dashboard/transactions/page.tsx` - Page transactions
- `frontend/src/components/FileUpload.tsx` - Composant upload
- `frontend/src/components/TransactionsTable.tsx` - Tableau transactions

**Tests**:
- [ ] Test upload fichier depuis interface
- [ ] Test affichage transactions dans tableau
- [ ] Test filtrage par date
- [ ] Test recherche par nom
- [ ] Test tri par colonnes
- [ ] Test pagination (si nécessaire)

**Acceptance Criteria**:
- [ ] Upload de fichiers fonctionne via interface
- [ ] Prévisualisation des fichiers avant traitement
- [ ] Tableau des transactions s'affiche avec toutes les colonnes
- [ ] Filtrage et recherche fonctionnels
- [ ] **Utilisateur confirme que l'interface fonctionne**

**Impact Frontend**: 
- ✅ Onglet Transactions fonctionnel
- ✅ Upload CSV visible et testé
- ✅ Tableau transactions avec toutes les colonnes
- ✅ Filtrage et recherche opérationnels

---

## Phase 3 : Fonctionnalité 2 - Enrichissement et catégorisation

### Step 3.1 : Service d'enrichissement backend
**Status**: ⏸️ EN ATTENTE  
**Description**: Migrer la logique de `2_add_extra_columns.py` avec système de mapping intelligent.

**Tasks**:
- [ ] Créer enrichment_service.py
- [ ] Implémenter ajout métadonnées temporelles
- [ ] Implémenter mapping intelligent par préfixe
- [ ] Créer endpoints CRUD pour mappings
- [ ] **Créer test complet avec mappings réels**
- [ ] **Valider avec l'utilisateur**

**Deliverables**:
- `backend/api/services/enrichment_service.py` - Service enrichissement
- `backend/api/routes/enrichment.py` - Endpoints enrichissement
- `backend/api/routes/mappings.py` - CRUD mappings
- `backend/tests/test_enrichment.py` - Tests enrichissement

**Tests**:
- [ ] Test ajout métadonnées (mois, année)
- [ ] Test mapping par préfixe
- [ ] Test cas spéciaux (PRLV SEPA, VIR STRIPE)
- [ ] Test catégorisation hiérarchique
- [ ] Test transactions non mappées
- [ ] Test CRUD mappings

**Acceptance Criteria**:
- [ ] Enrichissement automatique fonctionne
- [ ] Mapping par préfixe opérationnel
- [ ] Transactions enrichies stockées en DB
- [ ] Rapport des non-mappées généré
- [ ] Test script exécutable et tous les tests passent
- [ ] **Utilisateur confirme que l'enrichissement fonctionne**

**Impact Frontend**: 
- [ ] Afficher classifications dans tableau transactions
- [ ] Tester enrichissement depuis interface

---

### Step 3.2 : Interface gestion mapping et classifications
**Status**: ⏸️ EN ATTENTE  
**Description**: Interface pour visualiser/modifier les classifications et gérer les mappings.

**Tasks**:
- [ ] Créer composant ClassificationEditor
- [ ] Créer composant MappingEditor
- [ ] Ajouter édition inline dans tableau transactions
- [ ] Créer interface gestion mappings
- [ ] **Créer test visuel dans navigateur**
- [ ] **Valider avec l'utilisateur**

**Deliverables**:
- `frontend/src/components/ClassificationEditor.tsx` - Éditeur classifications
- `frontend/src/components/MappingEditor.tsx` - Éditeur mappings
- Mise à jour `frontend/app/dashboard/transactions/page.tsx`

**Tests**:
- [ ] Test modification classification inline
- [ ] Test création nouveau mapping
- [ ] Test modification mapping existant
- [ ] Test application mapping aux nouvelles transactions

**Acceptance Criteria**:
- [ ] Visualisation des classifications dans le tableau
- [ ] Modification des classifications existantes
- [ ] Création/modification de mappings via interface
- [ ] Application des mappings aux nouvelles transactions
- [ ] **Utilisateur confirme que l'interface fonctionne**

**Impact Frontend**: 
- ✅ Classifications visibles et éditables
- ✅ Interface gestion mappings fonctionnelle
- ✅ Modifications testées dans navigateur

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

