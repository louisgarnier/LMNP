# Plan d'Implémentation - Phase 9 : Bilan

**Status**: 🚧 EN COURS  
**Dernière mise à jour**: 2025-01-27

## Vue d'ensemble

**Objectif** : Créer un nouvel onglet "Bilan" avec une structure similaire au compte de résultat, incluant une card de configuration pour mapper les level_1 aux catégories comptables du bilan et une table pour afficher le bilan par année.

**Fonctionnalités principales** :
- Card de configuration pour mapper les level_1 aux catégories comptables du bilan
- Filtre global Level 3 (valeurs à considérer dans le bilan)
- Table d'affichage avec structure hiérarchique (ACTIF/PASSIF → Sous-catégories → Catégories)
- Calcul automatique des catégories spéciales (amortissements cumulés, compte bancaire, résultat de l'exercice, report à nouveau, capital restant dû)
- Validation de l'équilibre ACTIF = PASSIF avec indicateur de différence

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
   - Source : Table `amortization_result` (AmortizationResult)
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

---

### Step 9.1 : Backend - Table et modèles pour les mappings et bilans

**Status**: ✅ COMPLETED  
**Description**: Créer les modèles de base de données pour stocker les mappings et les données du bilan.

**Tasks**:
- [x] Créer modèle `BilanMapping` dans `backend/database/models.py`
  - `id` (Integer, primary_key)
  - `category_name` (String, unique=False) - Nom de la catégorie comptable (niveau C)
  - `level_1_values` (JSON) - Liste des level_1 mappés à cette catégorie
  - `type` (String) - "ACTIF" ou "PASSIF"
  - `sub_category` (String) - Sous-catégorie (niveau B)
  - `is_special` (Boolean) - Indique si c'est une catégorie spéciale
  - `special_source` (String, nullable) - Source pour les catégories spéciales ("amortization_result", "transactions", "compte_resultat", "compte_resultat_cumul", "loan_payments")
  - `compte_resultat_view_id` (Integer, ForeignKey vers `compte_resultat_mapping_views.id`, nullable) - Pour catégorie "Résultat de l'exercice"
  - `created_at`, `updated_at` (DateTime)
- [x] Créer modèle `BilanData` dans `backend/database/models.py`
  - `id` (Integer, primary_key)
  - `annee` (Integer, index=True)
  - `category_name` (String, index=True)
  - `amount` (Float)
  - `created_at`, `updated_at` (DateTime)
- [x] Créer modèle `BilanConfig` dans `backend/database/models.py`
  - `id` (Integer, primary_key)
  - `level_3_values` (JSON) - Liste des level_3 sélectionnés pour le filtre global
  - `created_at`, `updated_at` (DateTime)
- [x] Créer script de migration `backend/database/migrations/add_bilan_tables.py`
- [x] Ajouter les tables dans `backend/database/schema.sql`

**Deliverables**:
- Modèles SQLAlchemy dans `backend/database/models.py`
- Script de migration `backend/database/migrations/add_bilan_tables.py`
- Mise à jour `backend/database/schema.sql`

**Acceptance Criteria**:
- [x] Modèles créés avec tous les champs nécessaires
- [x] Index créés pour les recherches fréquentes (category_name, type, sub_category, annee, category_name)
- [x] Relations définies si nécessaire (ForeignKey vers compte_resultat_mapping_views)
- [x] Migration testée - Tables créées avec succès

---

### Step 9.2 : Backend - Service de calcul du Bilan

**Status**: ✅ COMPLETED  
**Description**: Créer le service pour calculer les montants du bilan par catégorie et par année.

**Tasks**:
- [x] Créer `backend/api/services/bilan_service.py`
- [x] Fonction `get_mappings(db: Session) -> List[BilanMapping]`
- [x] Fonction `calculate_bilan(year: int, mappings: List[BilanMapping], selected_level_3_values: List[str], db: Session) -> dict`
  - Pour chaque mapping :
    - Si `is_special == False` : Calculer depuis transactions enrichies (même logique que compte de résultat)
    - Si `is_special == True` :
      - `special_source == "amortization_result"` : Cumul des amortissements jusqu'à l'année
      - `special_source == "transactions"` : Solde final de l'année (dernière transaction)
      - `special_source == "compte_resultat"` : Résultat de l'année depuis compte de résultat (filtré par `compte_resultat_view_id` si fourni)
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
  - `calculate_resultat_exercice()` - Résultat de l'exercice (avec filtre par vue si fourni)
  - `calculate_report_a_nouveau()` - Report à nouveau
  - `calculate_capital_restant_du()` - Capital restant dû

**Deliverables**:
- Fichier `backend/api/services/bilan_service.py`
- Fonctions de calcul et de gestion des données
- Test `backend/scripts/test_bilan_service_step9_2.py`

**Acceptance Criteria**:
- [x] Toutes les catégories normales calculées correctement depuis transactions
- [x] Toutes les catégories spéciales calculées correctement depuis leurs sources
- [x] Totaux calculés correctement (niveaux A, B, C)
- [x] Équilibre ACTIF = PASSIF calculé et validé
- [x] Pourcentage de différence calculé
- [x] Tous les tests passent

---

### Step 9.3 : Backend - Modèles Pydantic pour l'API

**Status**: ✅ COMPLETED  
**Description**: Créer les modèles Pydantic pour les requêtes et réponses API du bilan.

**Tasks**:
- [x] Créer `BilanMappingBase`, `BilanMappingCreate`, `BilanMappingUpdate`, `BilanMappingResponse` dans `backend/api/models.py`
- [x] Créer `BilanMappingListResponse` pour la liste des mappings
- [x] Créer `BilanDataBase`, `BilanDataResponse`, `BilanDataListResponse` dans `backend/api/models.py`
- [x] Créer `BilanResponse` avec structure hiérarchique (ACTIF/PASSIF → Sous-catégories → Catégories)
  - `BilanTypeItem` : Type (ACTIF/PASSIF) avec total et sous-catégories
  - `BilanSubCategoryItem` : Sous-catégorie avec total et catégories
  - `BilanCategoryItem` : Catégorie avec montant
- [x] Créer `BilanConfigBase`, `BilanConfigResponse` pour la configuration (level_3_values)
- [x] Créer `BilanCalculateRequest` (year, selected_level_3_values)

**Deliverables**:
- Modèles Pydantic dans `backend/api/models.py`

**Acceptance Criteria**:
- [x] Tous les modèles créés avec validation appropriée
- [x] Structure hiérarchique bien représentée (BilanTypeItem → BilanSubCategoryItem → BilanCategoryItem)
- [x] Compatibilité avec les catégories spéciales (champs is_special, special_source, compte_resultat_view_id)
- [x] Tous les modèles importables sans erreur

---

### Step 9.4 : Backend - Endpoints API pour le Bilan

**Status**: ✅ COMPLETED  
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
  - `POST /api/bilan/calculate` - Générer le bilan pour une année (avec structure hiérarchique)
- [x] Endpoints pour récupérer les données :
  - `GET /api/bilan` - Récupérer les données du bilan (avec filtres year, start_year, end_year)
- [x] Endpoints pour la configuration :
  - `GET /api/bilan/config` - Récupérer la configuration (level_3_values)
  - `PUT /api/bilan/config` - Mettre à jour la configuration (level_3_values)
- [x] Intégrer les endpoints dans `backend/api/main.py`
- [x] Invalidation automatique des données lors de modification des mappings

**Deliverables**:
- Fichier `backend/api/routes/bilan.py`
- Intégration dans `backend/api/main.py`
- Test `backend/scripts/test_bilan_endpoints_step9_4.py`

**Acceptance Criteria**:
- [x] Tous les endpoints CRUD fonctionnent correctement
- [x] Génération du bilan fonctionne avec toutes les catégories spéciales
- [x] Récupération des données avec filtres fonctionne
- [x] Gestion de la configuration fonctionne
- [x] Gestion des erreurs appropriée (HTTPException pour erreurs 404, 400)
- [x] Structure hiérarchique correctement construite dans la réponse

---

### Step 9.5 : Backend - Recalcul automatique

**Status**: ✅ COMPLETED  
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
- Mise à jour des endpoints concernés :
  - `backend/api/routes/enrichment.py`
  - `backend/api/routes/transactions.py`
  - `backend/api/routes/loan_payments.py`
  - `backend/api/routes/amortization.py`
  - `backend/api/routes/compte_resultat.py`
- Test `backend/scripts/test_bilan_automatic_recalculation_step9_5.py`

**Acceptance Criteria**:
- [x] Recalcul déclenché lors de la modification des transactions
- [x] Recalcul déclenché lors de la modification des amortissements
- [x] Recalcul déclenché lors de la modification du compte de résultat
- [x] Recalcul déclenché lors de la modification des loan payments
- [x] Recalcul déclenché lors de la modification des mappings

---

### Step 9.6 : Frontend - API Client pour le Bilan

**Status**: ✅ COMPLETED  
**Description**: Créer les fonctions API client pour communiquer avec le backend du bilan.

**Tasks**:
- [x] Ajouter `bilanAPI` dans `frontend/src/api/client.ts`
- [x] Fonctions CRUD pour les mappings :
  - `getMappings()`, `getMapping(id)`, `createMapping(data)`, `updateMapping(id, data)`, `deleteMapping(id)`
- [x] Fonctions pour les données :
  - `calculate(year, selected_level_3_values)`, `calculateMultiple(years)`, `getBilan(year?, start_year?, end_year?)`
- [x] Fonctions pour la configuration :
  - `getConfig()`, `updateConfig(level_3_values)`
- [x] Types TypeScript pour les interfaces :
  - `BilanMapping`, `BilanMappingCreate`, `BilanMappingUpdate`, `BilanMappingListResponse`
  - `BilanData`, `BilanDataListResponse`
  - `BilanCategoryItem`, `BilanSubCategoryItem`, `BilanTypeItem`, `BilanResponse`
  - `BilanCalculateRequest`
  - `BilanConfig`, `BilanConfigUpdate`

**Deliverables**:
- Mise à jour `frontend/src/api/client.ts`
- Types TypeScript définis

**Acceptance Criteria**:
- [x] Toutes les fonctions API créées
- [x] Types TypeScript corrects (correspondance avec modèles Pydantic backend)
- [x] Gestion des erreurs appropriée (utilise fetchAPI avec gestion d'erreurs)

---

### Step 9.7 : Frontend - Card de configuration du Bilan

**Status**: ✅ COMPLETED  
**Description**: Créer la card de configuration pour mapper les level_1 aux catégories comptables du bilan.

**Tasks**:
- [x] Créer `frontend/src/components/BilanConfigCard.tsx`
- [x] Structure similaire à `CompteResultatConfigCard.tsx` :
  - Titre "Configuration du bilan" avec bouton pin/unpin
  - Dropdown multi-select "Level 3 (Valeur à considérer dans le bilan)" (même fonctionnement que compte de résultat) 
  - Table avec colonnes :
    - Type (ACTIF/PASSIF) - Dropdown
    - Sous-catégorie (niveau B) - Dropdown filtré par Type
    - Catégorie comptable (niveau C) - Éditable (champ texte)
    - Level 1 (valeurs) - Tags avec dropdown filtré par Level 3 sélectionnés
    - Vue (pour catégories spéciales) - "Données calculées" ou dropdown pour compte de résultat
  - Bouton "+ Ajouter une catégorie"
  - Bouton "Réinitialiser les mappings"
- [x] Gérer les catégories spéciales :
  - Amortissements cumulés : "Données calculées" (pas de vue nécessaire, utilise directement amortization_result)
  - Compte bancaire : "Données calculées"
  - Résultat de l'exercice : Support pour vue de compte de résultat (compte_resultat_view_id)
  - Report à nouveau : "Données calculées"
  - Emprunt bancaire : "Données calculées"
- [x] Sauvegarder/charger la configuration avec `selected_level_3_values`
- [x] Filtrage du dropdown Level 1 par Level 3 sélectionnés (même logique que compte de résultat)
- [x] Exclusion des Level 1 déjà sélectionnés dans d'autres catégories (comme CompteResultatConfigCard)
- [x] Tri des lignes par Type puis Sous-catégorie puis Catégorie
- [x] Callback `onConfigUpdated` pour notifier le parent
- [x] Intégration dans `frontend/app/dashboard/etats-financiers/page.tsx`

**Deliverables**:
- Fichier `frontend/src/components/BilanConfigCard.tsx`
- Intégration dans la page États financiers

**Acceptance Criteria**:
- [x] Card fonctionne comme CompteResultatConfigCard
- [x] Dropdown Level 3 fonctionne
- [x] Filtrage Level 1 par Level 3 fonctionne
- [x] Exclusion des Level 1 déjà sélectionnés fonctionne (comme CompteResultatConfigCard)
- [x] Catégories spéciales gérées correctement
- [x] Sauvegarde/chargement de la configuration fonctionne
- [x] Pin/unpin fonctionne
- [x] Callback onConfigUpdated fonctionne
- [x] Card affichée dans l'onglet "Bilan"

---

### Step 9.8 : Frontend - Table d'affichage du Bilan

**Status**: ⏳ À FAIRE  
**Description**: Créer la table pour afficher le bilan avec structure hiérarchique et colonnes par année. Décomposé en sous-steps pour valider chaque niveau hiérarchique.

---

#### Step 9.8.1 : Frontend - Structure de base et affichage niveau C (Catégories)

**Status**: ✅ COMPLETED  
**Description**: Créer la structure de base de la table et afficher les catégories comptables (niveau C) avec leurs montants par année.

**Tasks**:
- [x] Créer `frontend/src/components/BilanTable.tsx`
- [x] Structure de base similaire à `CompteResultatTable.tsx` :
  - Colonne "Bilan" (catégories)
  - Colonnes par année (dynamiques, basées sur les données disponibles)
- [x] Récupérer les données du bilan depuis l'API (`bilanAPI.calculate()`)
- [x] Grouper les données par catégorie comptable (niveau C)
- [x] Afficher chaque catégorie (niveau C) :
  - Double indentation (ex: `&nbsp;&nbsp;&nbsp;&nbsp;Immobilisations`)
  - Montant par année dans les colonnes correspondantes
  - Formatage des montants en € (ex: `1 234,56 €`)
  - Affichage des montants négatifs en rouge (pour "Amortissements cumulés" et "Résultat de l'exercice" si perte)
- [x] Trier les catégories par Type (ACTIF, puis PASSIF), puis par Sous-catégorie, puis par Catégorie

**Deliverables**:
- Fichier `frontend/src/components/BilanTable.tsx` avec structure de base
- Affichage des catégories niveau C

**Acceptance Criteria**:
- [x] Table créée avec colonnes dynamiques par année
- [x] Catégories niveau C affichées avec double indentation
- [x] Montants affichés correctement par année
- [x] Formatage € correct
- [x] Montants négatifs en rouge pour les catégories appropriées
- [x] Tri correct (ACTIF puis PASSIF, puis sous-catégories, puis catégories)

---

#### Step 9.8.2 : Frontend - Affichage niveau B (Sous-catégories) avec totaux

**Status**: ✅ COMPLETED  
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

#### Step 9.8.3 : Frontend - Affichage niveau A (ACTIF/PASSIF) avec totaux

**Status**: ✅ COMPLETED  
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

#### Step 9.8.4 : Frontend - Gestion des catégories spéciales dans l'affichage

**Status**: ✅ COMPLETED  
**Description**: S'assurer que les catégories spéciales sont affichées correctement avec leurs calculs spécifiques.

---

##### Step 9.8.4.1 : Frontend - Catégorie spéciale "Amortissements cumulés"

**Status**: ✅ COMPLETED  
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
- Test script: `backend/scripts/test_bilan_amortissements_cumules.py`

**Acceptance Criteria**:
- [x] Montant affiché en négatif et en rouge
- [x] Position correcte (sous "Immobilisations")
- [x] Contribue correctement au calcul "Actif immobilisé"
- [x] Montant calculé correctement par le backend

---

##### Step 9.8.4.2 : Frontend - Catégorie spéciale "Compte bancaire"

**Status**: ✅ COMPLETED  
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

##### Step 9.8.4.3 : Frontend - Catégorie spéciale "Résultat de l'exercice (bénéfice / perte)"

**Status**: ✅ COMPLETED  
**Description**: Vérifier et valider l'affichage de la catégorie spéciale "Résultat de l'exercice" avec sélection de vue de compte de résultat.

**Tasks**:
- [x] Vérifier que le montant peut être positif (bénéfice) ou négatif (perte)
- [x] Vérifier que la catégorie est affichée dans "Capitaux propres"
- [x] Vérifier que le montant est récupéré depuis `CompteResultatData` filtré par `compte_resultat_view_id` (si fourni)
- [x] Vérifier que le calcul backend est correct (depuis compte de résultat, signe préservé)
- [x] Vérifier que l'affichage en rouge fonctionne pour les montants négatifs (perte)
- [x] Vérifier que le montant est récupéré depuis l'API `/api/bilan/calculate`

**Deliverables**:
- Validation de l'affichage "Résultat de l'exercice" dans `BilanTable.tsx`
- Affichage signe et couleur dans `BilanTable.tsx`

**Acceptance Criteria**:
- [x] Montant peut être positif (bénéfice) ou négatif (perte)
- [x] Montant récupéré depuis `CompteResultatData` filtré par `compte_resultat_view_id`
- [x] Position correcte (dans "Capitaux propres")
- [x] Affichage en rouge si perte (montant négatif)
- [x] Montant calculé correctement par le backend (signe préservé)

---

##### Step 9.8.4.4 : Frontend - Catégorie spéciale "Report à nouveau / report du déficit"

**Status**: ✅ COMPLETED  
**Description**: Vérifier et valider l'affichage de la catégorie spéciale "Report à nouveau".

**Tasks**:
- [x] Vérifier que le montant est affiché correctement
- [x] Vérifier que la catégorie est affichée dans "Capitaux propres"
- [x] Vérifier que le calcul est correct :
  - Cumul des résultats des années précédentes (N-1, N-2, etc.)
  - Première année : 0 (pas de report)
- [x] Vérifier que le calcul backend est correct (cumul depuis `compte_resultat_data` ou calcul via `CompteResultatService`)
- [x] Vérifier que le montant est récupéré depuis l'API `/api/bilan/calculate`
- [x] Tester avec plusieurs années pour vérifier le cumul

**Deliverables**:
- Validation de l'affichage "Report à nouveau" dans `BilanTable.tsx`

**Acceptance Criteria**:
- [x] Première année affiche 0
- [x] Années suivantes affichent le cumul des résultats précédents
- [x] Position correcte (dans "Capitaux propres")
- [x] Montant calculé correctement par le backend

---

##### Step 9.8.4.5 : Frontend - Catégorie spéciale "Emprunt bancaire (capital restant dû)"

**Status**: ✅ COMPLETED  
**Description**: Vérifier et valider l'affichage de la catégorie spéciale "Emprunt bancaire".

**Tasks**:
- [x] Vérifier que le montant est affiché en positif (dette)
- [x] Vérifier que la catégorie est affichée dans "Dettes financières"
- [x] Vérifier que le calcul est correct :
  - Capital restant dû = Crédit accordé - Cumulé des remboursements de capital
  - Calculé au 31/12 de chaque année
- [x] Vérifier que le calcul backend est correct (depuis `loan_payments` et `loan_configs`)
- [x] Vérifier que le montant est récupéré depuis l'API `/api/bilan/calculate`
- [x] Tester avec plusieurs années pour vérifier la diminution progressive

**Deliverables**:
- Validation de l'affichage "Emprunt bancaire" dans `BilanTable.tsx`

**Acceptance Criteria**:
- [x] Montant affiché en positif (dette)
- [x] Position correcte (dans "Dettes financières")
- [x] Montant diminue progressivement avec les remboursements
- [x] Montant calculé correctement par le backend

---

#### Step 9.8.5 : Frontend - Validation équilibre ACTIF = PASSIF avec % de différence

**Status**: ✅ COMPLETED  
**Description**: Ajouter la validation de l'équilibre ACTIF = PASSIF et afficher le pourcentage de différence.

**Tasks**:
- [x] Ajouter une ligne "ÉQUILIBRE" ou "% Différence" après "TOTAL PASSIF"
- [x] Calculer la différence pour chaque année :
  - `différence = TOTAL ACTIF - TOTAL PASSIF`
  - `pourcentage = (différence / TOTAL ACTIF) * 100` (si TOTAL ACTIF > 0)
- [x] Afficher le pourcentage de différence :
  - Format : `% Différence : X.XX%`
  - Si différence = 0 : Vert, texte "Équilibre respecté ✓"
  - Si différence > 0 : Rouge, afficher le pourcentage
  - Si TOTAL ACTIF = 0 : Afficher "N/A"
- [x] Style de la ligne :
  - Fond légèrement coloré (vert si équilibré, rouge si déséquilibré)
  - Texte en gras
  - Bordure supérieure épaisse
- [x] Ajouter un message d'alerte si déséquilibré :
  - Afficher un warning si différence > 0.01% (tolérance pour arrondis)
  - Message : "⚠️ Attention : Le bilan n'est pas équilibré. Vérifiez les calculs."

**Deliverables**:
- Mise à jour `frontend/src/components/BilanTable.tsx`
- Validation de l'équilibre avec indicateur visuel

**Acceptance Criteria**:
- [x] Différence calculée correctement pour chaque année
- [x] Pourcentage de différence calculé et affiché
- [x] Indicateur visuel (vert/rouge) selon l'équilibre
- [x] Message d'alerte si déséquilibré
- [x] Tolérance pour les arrondis (0.01%)

---

#### Step 9.8.6 : Frontend - Gestion de l'année en cours (bilan partiel)

**Status**: ⏳ À FAIRE  
**Description**: Gérer le cas particulier de l'année en cours où le bilan ne peut pas être complètement équilibré.

**Contexte** :
Pour l'année en cours, le bilan ne peut pas être complètement équilibré car :
- Les amortissements concernent l'année entière (mais on n'est peut-être qu'en janvier/février)
- Les impôts ne sont pas encore payés (charges à payer)
- Tous les produits/charges ne sont pas encore encaissés/décaissés (créances/dettes d'exploitation)
- Certaines provisions peuvent manquer

**Approches possibles** :

**Option A : Tolérance spécifique pour l'année en cours**
- Appliquer une tolérance plus large pour l'année en cours (ex: 5% au lieu de 0.01%)
- Afficher un message informatif : "⚠️ Année en cours : Le bilan peut être partiellement déséquilibré (amortissements annuels, impôts non payés, etc.)"
- Avantages : Simple à implémenter
- Inconvénients : Peut masquer de vraies erreurs

**Option B : Calcul pro-rata pour l'année en cours**
- Calculer les amortissements au prorata du nombre de mois écoulés
- Estimer les impôts à payer (basé sur le résultat estimé)
- Ajouter des ajustements pour les créances/dettes d'exploitation
- Avantages : Plus précis
- Inconvénients : Complexe, nécessite des estimations

**Option C : Affichage conditionnel avec message explicatif**
- Détecter si l'année est l'année en cours
- Si déséquilibré ET année en cours : Afficher un message explicatif au lieu d'un warning
- Message : "ℹ️ Année en cours : Le bilan est partiel. Les amortissements, impôts et certaines charges/produits ne sont pas encore comptabilisés."
- Afficher quand même le pourcentage de différence mais avec un style "info" (bleu) au lieu de "erreur" (rouge)
- Avantages : Informe l'utilisateur sans alarmer inutilement
- Inconvénients : Nécessite de détecter l'année en cours

**Option D : Catégorie "Écarts d'arrondi et année en cours"**
- Ajouter une catégorie spéciale dans le PASSIF : "Écarts d'arrondi et année en cours"
- Cette catégorie équilibre automatiquement le bilan pour l'année en cours
- Montant = TOTAL ACTIF - TOTAL PASSIF (pour l'année en cours uniquement)
- Avantages : Le bilan est toujours équilibré visuellement
- Inconvénients : Peut masquer des erreurs réelles

**Option E : Combinaison Option C + Option A**
- Pour l'année en cours : Tolérance plus large (ex: 2-3%) + Message informatif
- Si déséquilibré au-delà de la tolérance : Afficher un warning
- Si déséquilibré dans la tolérance : Afficher un message info
- Avantages : Équilibre entre information et alerte
- Inconvénients : Nécessite de définir une tolérance appropriée

**Recommandation** : **Option E (Combinaison C + A)**
- Détecter l'année en cours
- Appliquer une tolérance de 2-3% pour l'année en cours (au lieu de 0.01%)
- Si déséquilibré dans la tolérance : Afficher un message info (bleu) au lieu d'un warning (rouge)
- Si déséquilibré au-delà de la tolérance : Afficher un warning (rouge) comme pour les autres années
- Message info : "ℹ️ Année en cours : Le bilan peut être partiellement déséquilibré (amortissements annuels, impôts non payés, créances/dettes d'exploitation)."

**Tasks** (à définir selon l'option choisie) :
- [ ] Détecter l'année en cours
- [ ] Appliquer une tolérance spécifique pour l'année en cours
- [ ] Modifier l'affichage de la ligne ÉQUILIBRE pour l'année en cours
- [ ] Ajouter un message informatif pour l'année en cours
- [ ] Tester avec différentes dates (janvier, juin, décembre)

**Deliverables**:
- Mise à jour `frontend/src/components/BilanTable.tsx`
- Gestion de l'année en cours avec tolérance et message approprié

**Acceptance Criteria**:
- [ ] L'année en cours est détectée correctement
- [ ] Une tolérance spécifique est appliquée pour l'année en cours
- [ ] L'affichage de l'équilibre est adapté pour l'année en cours (style info au lieu d'erreur si dans la tolérance)
- [ ] Un message informatif est affiché pour l'année en cours
- [ ] Les autres années conservent la validation stricte (0.01%)

---

#### Step 9.8.7 : Frontend - Formatage et finitions

**Status**: ⏳ À FAIRE  
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

### Step 9.9 : Frontend - Intégration dans la page États financiers

**Status**: ✅ COMPLETED  
**Description**: Intégrer la card de configuration et la table du bilan dans l'onglet "Bilan" de la page États financiers.

**Tasks**:
- [x] Modifier `frontend/app/dashboard/etats-financiers/page.tsx`
- [x] Intégrer `BilanConfigCard` dans l'onglet "Bilan"
- [x] Intégrer `BilanTable` dans l'onglet "Bilan"
- [x] Gérer le rechargement des données après modification de la configuration
- [x] Passer les callbacks nécessaires (`onConfigUpdated`, `onLevel3Change`)
- [x] Gérer le `refreshKey` pour forcer le rechargement de la table

**Deliverables**:
- Mise à jour `frontend/app/dashboard/etats-financiers/page.tsx`
- Intégration complète de la card et de la table

**Acceptance Criteria**:
- [x] Card et table intégrées dans l'onglet "Bilan"
- [x] Rechargement automatique après modification de la configuration
- [x] Callbacks fonctionnent correctement
- [x] Navigation entre onglets fonctionne

---

### Step 9.10 : Test et validation

**Status**: ⏳ À FAIRE  
**Description**: Tester l'ensemble des fonctionnalités du bilan.

**Tasks**:
- [ ] Tester la création/modification/suppression des mappings
- [ ] Tester le filtrage par Level 3
- [ ] Tester le calcul des catégories normales
- [ ] Tester le calcul des catégories spéciales
- [ ] Tester l'affichage hiérarchique
- [ ] Tester l'équilibre ACTIF = PASSIF
- [ ] Tester la sauvegarde/chargement de la configuration
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

## Critères d'acceptation globaux Phase 9

- [ ] Modèles de données créés
- [ ] Service de calcul fonctionne pour toutes les catégories
- [ ] Endpoints API fonctionnent
- [ ] Card de configuration fonctionne avec filtrage Level 3
- [ ] Table d'affichage avec structure hiérarchique fonctionne
- [ ] Équilibre ACTIF = PASSIF validé
- [ ] Recalcul automatique fonctionne
- [ ] **Test complet de bout en bout validé**

---

## Notes de développement

- **Structure identique au compte de résultat** : Réutiliser autant que possible la structure et les patterns de `CompteResultatConfigCard` et `CompteResultatTable`
- **Liaison card config ↔ tableau** : Le tableau doit toujours refléter les configurations de la card config
- **Calculs backend** : Tous les calculs doivent être effectués côté backend pour garantir la cohérence
- **Recalcul automatique** : Les bilans doivent être invalidés et recalculés quand les données sources changent
- **Catégories spéciales** : Chaque catégorie spéciale a sa propre logique de calcul, documentée dans le plan
- **Équilibre ACTIF = PASSIF** : Validation automatique avec indicateur visuel de différence

---

## Notes importantes

⚠️ **Rappel Best Practices**:
- Ne jamais cocher [x] avant que les tests soient créés ET exécutés ET validés
- Toujours créer un test script (.py) après chaque implémentation
- Toujours proposer le test à l'utilisateur avant exécution
- Toujours montrer l'impact frontend à chaque étape
- Ne cocher [x] qu'après confirmation explicite de l'utilisateur

**Légende Status**:
- ⏳ À FAIRE - Pas encore commencé
- ⏸️ EN ATTENTE - En attente de validation
- 🔄 EN COURS - En cours d'implémentation
- ✅ TERMINÉ - Terminé et validé par l'utilisateur
