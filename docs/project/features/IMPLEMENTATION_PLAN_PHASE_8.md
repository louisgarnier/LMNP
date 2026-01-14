# Plan d'Implémentation - Phase 8 : Compte de résultat

**Status**: ⏳ À FAIRE  
**Dernière mise à jour**: 2025-01-27

## Vue d'ensemble

**Objectif** : Implémenter le module "Compte de résultat" avec configuration des mappings et affichage des données agrégées.

**Fonctionnalités principales** :

- Configuration des mappings (level_1 → catégories comptables)
- Calcul automatique du compte de résultat par année
- Affichage multi-années avec totaux
- Intégration avec amortissements et crédits

---

## Phase 8 : Compte de résultat

**Structure** : Identique aux amortissements
- **CompteResultatConfigCard** : Card de configuration (mapping level_1 → catégories comptables)
- **CompteResultatTable** : Card d'affichage (tableau multi-années avec montants agrégés)

**Ordre d'implémentation** :
1. Backend (Steps 8.1 à 8.4)
2. Frontend - Card Config (Step 8.5 avec sous-steps détaillés)
3. Frontend - Card Table (Step 8.6 avec sous-steps détaillés)

---

### Step 8.1 : Backend - Table et modèles pour les mappings et comptes de résultat
**Status**: ⏳ À FAIRE  
**Description**: Créer la structure de base de données pour stocker les mappings (level_1 → catégories comptables) et les comptes de résultat générés.

**Catégories comptables à mapper** :
- **Produits d'exploitation** :
  - Loyers hors charge encaissés
  - Charges locatives payées par locataires
  - Autres revenus
- **Charges d'exploitation** :
  - Charges de copropriété hors fonds travaux
  - Fluides non refacturés
  - Assurances
  - Honoraires
  - Travaux et mobilier
  - Impôts et taxes
  - Charges d'amortissements (depuis amortissement)
  - Autres charges diverses
  - Coût du financement (Intérêts et assurance crédits)

**Tasks**:
- [ ] Créer table `compte_resultat_mappings` avec colonnes :
  - `id` (PK)
  - `category_name` (nom de la catégorie comptable, ex: "Loyers hors charge encaissés")
  - `level_1_values` (JSON array optionnel des level_1 à inclure, NULL par défaut)
  - `created_at`, `updated_at`
- [ ] Créer table `compte_resultat_data` avec colonnes :
  - `id` (PK)
  - `annee` (année du compte de résultat)
  - `category_name` (nom de la catégorie comptable)
  - `amount` (montant pour cette catégorie et cette année)
  - `created_at`, `updated_at`
- [ ] Créer modèles SQLAlchemy dans `backend/database/models.py`
- [ ] Créer modèles Pydantic dans `backend/api/models.py`
- [ ] Créer test unitaire pour les modèles
- [ ] Valider avec l'utilisateur

**Deliverables**:
- `backend/database/models.py` - Modèles `CompteResultatMapping` et `CompteResultatData`
- `backend/api/models.py` - Modèles Pydantic
- `backend/tests/test_compte_resultat_models.py` - Test unitaire
- `backend/database/__init__.py` - Export des modèles

**Acceptance Criteria**:
- [ ] Tables créées en BDD
- [ ] Modèles SQLAlchemy fonctionnels
- [ ] Modèles Pydantic créés
- [ ] Tests unitaires passent
- [ ] Modèles Pydantic créés et validés
- [ ] Tests unitaires passent

---

### Step 8.2 : Backend - Service compte de résultat (calculs)
**Status**: ⏳ À FAIRE  
**Description**: Implémenter la logique de calcul du compte de résultat.

**Sources de données** :
- **Produits/Charges** : Transactions enrichies via `level_1` (logique OR, filtrer par date pour l'année)
- **Amortissements** : Depuis la table `amortization_result` (sélectionner le total pour chaque année)
- **Intérêts/Assurance crédit** : Depuis `loan_payments` (filtrer par année, sommer `interest` + `insurance` de **tous les crédits configurés**)

**Tasks**:
- [ ] Créer fichier `backend/api/services/compte_resultat_service.py`
- [ ] Implémenter fonction `get_mappings()` : Charger les mappings depuis la table
- [ ] Implémenter fonction `calculate_produits_exploitation(year, mappings, level_3_values)` :
  - **Filtrer d'abord par level_3** : Seules les transactions dont le `level_3` est dans `level_3_values` (depuis `compte_resultat_config`)
  - Filtrer transactions par année (date entre 01/01/année et 31/12/année)
  - Grouper par catégorie selon les mappings level_1 
  - Sommer les montants par catégorie
  - Prendre en compte transactions positives ET négatives (revenus positifs - remboursements négatifs)
- [ ] Implémenter fonction `calculate_charges_exploitation(year, mappings, level_3_values)` :
  - **Filtrer d'abord par level_3** : Seules les transactions dont le `level_3` est dans `level_3_values` (depuis `compte_resultat_config`)
  - Filtrer transactions par année
  - Grouper par catégorie selon les mappings level_1
  - Sommer les montants par catégorie
  - Prendre en compte transactions positives ET négatives (dépenses négatives - remboursements/crédits positifs)
- [ ] Implémenter fonction `get_amortissements(year)` :
  - Récupérer le total d'amortissement pour l'année depuis la table `amortization_result`
  - Sommer tous les montants d'amortissement pour l'année (toutes les catégories)
- [ ] Implémenter fonction `get_cout_financement(year)` :
  - Récupérer tous les crédits configurés (via `loanConfigsAPI.getAll()` ou depuis la base de données)
  - Filtrer `loan_payments` par année (date entre 01/01/année et 31/12/année)
  - **Gérer le cas d'un seul crédit** : Si un seul crédit configuré, sommer `interest` + `insurance` de ce crédit pour l'année
  - **Gérer le cas de plusieurs crédits** : Si plusieurs crédits configurés, sommer `interest` + `insurance` de **tous les crédits** pour chaque année
  - Retourner le total (somme de tous les crédits pour l'année)
- [ ] Implémenter fonction `calculate_compte_resultat(year, mappings, level_3_values)` :
  - Récupérer `level_3_values` depuis `compte_resultat_config`
  - Calculer tous les produits d'exploitation (avec filtrage par level_3)
  - Calculer toutes les charges d'exploitation (incluant amortissements et coût financement, avec filtrage par level_3)
  - Calculer Résultat d'exploitation = Produits - Charges
  - Calculer Résultat net = Résultat d'exploitation
- [ ] Regrouper tous les mappings d'une même catégorie avec OR pour éviter de compter plusieurs fois les mêmes transactions
- [ ] Créer test complet avec données réelles
- [ ] Valider avec l'utilisateur

**Deliverables**:
- `backend/api/services/compte_resultat_service.py` - Service de calcul
- `backend/tests/test_compte_resultat_service.py` - Tests du service

**Tests**:
- [ ] Test calcul produits d'exploitation (avec mappings)
- [ ] Test calcul charges d'exploitation (avec mappings)
- [ ] Test récupération amortissements depuis vue
- [ ] Test calcul coût du financement depuis loan_payments (cas 1 crédit et cas plusieurs crédits)
- [ ] Test calcul résultat d'exploitation
- [ ] Test calcul résultat net
- [ ] Test avec données réelles (année complète)
- [ ] Test regroupement des mappings (éviter doublons)

**Acceptance Criteria**:
- [ ] Tous les calculs fonctionnent correctement
- [ ] **Filtrage par level_3 appliqué en premier** (seules les transactions avec level_3 sélectionné sont considérées)
- [ ] Mappings level_1 appliqués correctement sur les transactions filtrées par level_3
- [ ] Regroupement des mappings d'une même catégorie avec OR pour éviter les doublons
- [ ] Transactions positives ET négatives prises en compte pour toutes les catégories
- [ ] Amortissements récupérés depuis AmortizationResult
- [ ] Coût du financement calculé depuis loan_payments (somme de **tous les crédits configurés** pour chaque année)
- [ ] Gestion correcte du cas d'un seul crédit et du cas de plusieurs crédits
- [ ] Test script exécutable et tous les tests passent
- [ ] Utilisateur confirme que les calculs sont corrects

---

### Step 8.3 : Backend - Endpoints API pour compte de résultat
**Status**: ⏳ À FAIRE  
**Description**: Créer les endpoints API pour gérer les mappings et générer/récupérer les comptes de résultat.

**Tasks**:
- [ ] Créer fichier `backend/api/routes/compte_resultat.py`
- [ ] Créer endpoint `GET /api/compte-resultat/mappings` : Liste des mappings
- [ ] Créer endpoint `POST /api/compte-resultat/mappings` : Créer un mapping
- [ ] Créer endpoint `PUT /api/compte-resultat/mappings/{id}` : Mettre à jour un mapping
- [ ] Créer endpoint `DELETE /api/compte-resultat/mappings/{id}` : Supprimer un mapping
- [ ] Créer endpoint `POST /api/compte-resultat/generate` : Générer un compte de résultat
  - Paramètres : `year`
  - Retourne : Compte de résultat calculé et stocké en DB
- [ ] Créer endpoint `GET /api/compte-resultat/calculate?years={year1,year2,...}` : Calculer les montants pour plusieurs années
  - Retourne : Montants par catégorie et année (basé sur les mappings configurés)
- [ ] Créer endpoint `GET /api/compte-resultat` : Récupérer les comptes de résultat
  - Paramètres : `year` (optionnel), `start_year`, `end_year` (pour plusieurs années)
  - Retourne : Liste des comptes de résultat (plusieurs années possibles)
- [ ] Créer endpoint `GET /api/compte-resultat/data` : Récupérer les données brutes
- [ ] Créer endpoint `DELETE /api/compte-resultat/data/{id}` : Supprimer une donnée
- [ ] Créer endpoint `DELETE /api/compte-resultat/year/{year}` : Supprimer toutes les données d'une année
- [ ] Enregistrer router dans `backend/api/main.py`
- [ ] Créer test manuel pour les endpoints
- [ ] Valider avec l'utilisateur

**Deliverables**:
- `backend/api/routes/compte_resultat.py` - Endpoints API
- Mise à jour `backend/api/main.py` - Enregistrement du router
- `backend/tests/test_compte_resultat_endpoints_manual.py` - Test manuel

**Acceptance Criteria**:
- [ ] Tous les endpoints fonctionnent correctement
- [ ] Génération de compte de résultat fonctionne
- [ ] Calcul pour plusieurs années fonctionne
- [ ] Récupération de plusieurs années fonctionne
- [ ] Gestion d'erreur correcte
- [ ] Tests manuels créés (à exécuter avec serveur backend démarré)

---

### Step 8.4 : Backend - Recalcul automatique
**Status**: ⏳ À FAIRE  
**Description**: Implémenter le recalcul automatique des comptes de résultat quand les données sources changent.

**Déclencheurs de recalcul** :
- Transactions ajoutées/modifiées/supprimées
- Données d'amortissement dans les vues changent
- Crédits ajoutés/modifiés (mensualités loan_payments)
- Mappings modifiés

**Tasks**:
- [ ] Créer fonction `invalidate_compte_resultat_for_year(year)` : Supprimer les comptes de résultat pour une année
- [ ] Créer fonction `invalidate_compte_resultat_for_date_range(start_date, end_date)` : Supprimer pour une plage de dates
- [ ] Créer fonction `invalidate_all_compte_resultat()` : Supprimer tous les comptes de résultat
- [ ] Implémenter recalcul automatique dans :
  - Endpoints de transactions (POST, PUT, DELETE, import)
  - Endpoints d'amortissement (recalculate_amortizations)
  - Endpoints de loan_payments (POST, PUT, DELETE, import)
  - Endpoints de mappings (POST, PUT, DELETE)
  - Endpoints d'amortization (recalculate_amortizations)
- [ ] Créer test pour vérifier le recalcul automatique
- [ ] Valider avec l'utilisateur

**Deliverables**:
- Mise à jour `backend/api/services/compte_resultat_service.py` - Fonctions de recalcul
- Mise à jour des endpoints concernés (transactions, amortization, loan_payments, mappings)
- `backend/tests/test_compte_resultat_recalcul.py` - Tests de recalcul

**Acceptance Criteria**:
- [ ] Recalcul déclenché quand transactions changent (create, update, delete, import)
- [ ] Recalcul déclenché quand amortissements changent (recalculate_amortizations)
- [ ] Recalcul déclenché quand loan_payments changent (create, update, delete, import)
- [ ] Recalcul déclenché quand mappings changent (create, update, delete)
- [ ] Recalcul déclenché quand les données d'amortissement changent (recalculate_amortizations)
- [ ] Tests de recalcul passent
- [ ] Utilisateur confirme que le recalcul fonctionne

---

### Step 8.4.5 : Backend + Frontend - Filtre Level 3 (Valeur à considérer dans le compte de résultat)
**Status**: ⏳ À FAIRE  
**Description**: Implémenter le filtre Level 3 qui détermine quelles transactions seront considérées dans les calculs du compte de résultat. Ce filtre est appliqué EN PREMIER, avant les mappings level_1.

**⚠️ IMPORTANT : Logique de filtrage**
- Le filtre Level 3 est appliqué EN PREMIER
- Seules les transactions dont le `level_3` est dans la liste sélectionnée seront prises en compte
- Ensuite, dans le tableau de mapping, on pourra sélectionner des `level_1` parmi celles qui sont concernées par ces `level_3`
- Si aucune valeur level_3 n'est sélectionnée, aucune transaction ne sera considérée (obligatoire de sélectionner au moins une valeur)

**Tasks Backend**:
- [ ] Créer table `compte_resultat_config` avec colonnes :
  - `id` (PK)
  - `level_3_values` (JSON array des level_3 sélectionnés, ex: ["VALEUR1", "VALEUR2"])
  - `created_at`, `updated_at`
- [ ] Créer modèle SQLAlchemy `CompteResultatConfig` dans `backend/database/models.py`
- [ ] Créer modèles Pydantic dans `backend/api/models.py` :
  - `CompteResultatConfigBase`, `CompteResultatConfigCreate`, `CompteResultatConfigUpdate`, `CompteResultatConfigResponse`
- [ ] Créer endpoint `GET /api/compte-resultat/config` : Récupérer la configuration (level_3_values)
- [ ] Créer endpoint `PUT /api/compte-resultat/config` : Mettre à jour la configuration (level_3_values)
- [ ] Mettre à jour `compte_resultat_service.py` pour filtrer les transactions par `level_3` en premier :
  - Dans `calculate_produits_exploitation` et `calculate_charges_exploitation`, filtrer d'abord par `level_3_values` de la config
  - Seules les transactions avec `level_3` dans la liste sélectionnée seront considérées
- [ ] Créer test unitaire pour vérifier le filtrage par level_3
- [ ] Valider avec l'utilisateur

**Tasks Frontend**:
- [ ] Ajouter champ "Level 3 (Valeur à considérer dans le compte de résultat)" en haut de `CompteResultatConfigCard.tsx`
- [ ] Dropdown avec checkboxes (multi-sélection) pour sélectionner les valeurs level_3
- [ ] Charger les valeurs level_3 depuis les transactions enrichies (valeurs uniques via `transactionsAPI.getUniqueValues('level_3')`)
- [ ] Si aucune transaction chargée : afficher "Aucune valeur disponible" (grisé)
- [ ] Afficher les valeurs level_3 disponibles avec checkboxes
- [ ] Permettre la sélection de plusieurs valeurs level_3
- [ ] Sauvegarde automatique sur changement (mise à jour via API `PUT /api/compte-resultat/config`)
- [ ] Charger la configuration au montage du composant (récupérer les level_3_values depuis l'API)
- [ ] Masquer le tableau de mapping si aucune valeur level_3 n'est sélectionnée
- [ ] Filtrer les valeurs level_1 disponibles dans le tableau selon les level_3 sélectionnés :
  - Seules les transactions avec `level_3` dans la liste sélectionnée seront considérées
  - Les valeurs level_1 disponibles dans le dropdown seront filtrées pour ne montrer que celles qui existent dans les transactions avec les level_3 sélectionnés
- [ ] Persistance dans localStorage (optionnel, pour améliorer l'UX)
- [ ] Tester dans le navigateur

**Deliverables**:
- `backend/database/models.py` - Modèle `CompteResultatConfig`
- `backend/api/models.py` - Modèles Pydantic
- `backend/api/routes/compte_resultat.py` - Endpoints GET/PUT pour la config
- Mise à jour `backend/api/services/compte_resultat_service.py` - Filtrage par level_3
- `backend/tests/test_compte_resultat_config.py` - Test unitaire
- Mise à jour `frontend/src/components/CompteResultatConfigCard.tsx` - Champ Level 3
- Mise à jour `frontend/src/api/client.ts` - API client pour la config

**Acceptance Criteria**:
- [ ] Table `compte_resultat_config` créée en BDD
- [ ] Modèles SQLAlchemy et Pydantic créés
- [ ] Endpoints GET/PUT fonctionnent correctement
- [ ] Service filtre correctement les transactions par level_3 en premier
- [ ] Dropdown avec checkboxes fonctionne (multi-sélection)
- [ ] Valeurs level_3 chargées depuis les transactions enrichies
- [ ] Sauvegarde automatique fonctionne (mise à jour via API)
- [ ] Tableau de mapping masqué si aucune valeur level_3 sélectionnée
- [ ] Valeurs level_1 filtrées selon les level_3 sélectionnés
- [ ] Tests unitaires passent
- [ ] Test visuel dans navigateur validé
- [ ] Utilisateur confirme que le filtrage fonctionne correctement

---

### Step 8.5 : Frontend - Card de configuration (CompteResultatConfigCard)
**Status**: ⏳ À FAIRE  
**Description**: Créer l'interface de configuration pour mapper les level_1 aux catégories comptables. Structure identique à `AmortizationConfigCard`.

**⚠️ IMPORTANT : Le filtre Level 3 (Step 8.4.5) doit être configuré AVANT de pouvoir utiliser cette card**
- Le filtre Level 3 détermine quelles transactions seront considérées
- Seules les transactions avec level_3 sélectionné seront prises en compte
- Les valeurs level_1 disponibles dans le tableau seront filtrées selon les level_3 sélectionnés

**Structure du tableau** :
- **5 colonnes** :
  1. **Type** : Dropdown éditable avec "Produits d'exploitation" ou "Charges d'exploitation" (pas stocké en backend, utilisé uniquement pour filtrer les catégories)
  2. **Catégorie comptable** : Dropdown avec catégories prédéfinies (filtrées selon le type sélectionné)
  3. **Level 1 (valeurs)** : Tags bleus avec "x" pour supprimer + bouton "+ Ajouter" (optionnel) - comme dans level 1 valeurs des ammortissement

- **Une ligne = une catégorie comptable**
- **Logique de mapping** : Une transaction est mappée à une catégorie si son `level_1` est selectionnée dans les listes (logique OR)
- **Validation** : Pas d'obligation de level_1. Si une catégorie n'a aucune valeur, elle n'impacte pas le compte de résultat (comme AmortizationConfigCard)
- **Ordre** : Tri par Type puis par Catégorie comptable

**Catégories prédéfinies** :
- **Produits d'exploitation** :
  - Loyers hors charge encaissés
  - Charges locatives payées par locataires
  - Autres revenus
- **Charges d'exploitation** :
  - Charges de copropriété hors fonds travaux
  - Fluides non refacturés
  - Assurances
  - Honoraires
  - Travaux et mobilier
  - Impôts et taxes
  - Charges d'amortissements ⚠️ (données depuis table amortization_result - pas de mapping level_1)
  - Autres charges diverses
  - Coût du financement (hors remboursement du capital) ⚠️ (données depuis loan_payments - pas de mapping level_1)

**Fonctionnalités** (comme AmortizationConfigCard) :
- Bouton "🔄 Réinitialiser les mappings" (supprimer tous les mappings)
- Bouton "+ Ajouter une catégorie" en bas du tableau (création directe, pas de modal)
- Menu contextuel (clic droit) avec "🗑️ Supprimer" pour supprimer une ligne
- Sauvegarde automatique à chaque modification

---

#### Step 8.5.1 : Frontend - Structure de base du tableau
**Status**: ⏳ À FAIRE  
**Description**: Créer la structure de base du composant et du tableau (comme AmortizationConfigCard).

**Tasks**:
- [ ] Créer composant `CompteResultatConfigCard.tsx` (copier structure de base d'`AmortizationConfigCard`)
- [ ] Créer le tableau avec 3 colonnes (en-têtes) : Type, Catégorie comptable, Level 1 (valeurs)
- [ ] Charger les mappings depuis l'API (`compteResultatAPI.getMappings()`)
- [ ] Afficher les lignes existantes (lecture seule pour l'instant, sans édition)
- [ ] Déduire le Type automatiquement selon la catégorie (logique frontend)
- [ ] Trier les lignes par Type puis par Catégorie comptable
- [ ] Ajuster les largeurs des colonnes (Type: 20%, Catégorie: 30%, Level 1: 50%)
- [ ] Intégrer dans l'onglet "Compte de résultat"
- [ ] Tester dans le navigateur

**Deliverables**:
- `frontend/src/components/CompteResultatConfigCard.tsx` - Structure de base
- Mise à jour `frontend/app/dashboard/etats-financiers/page.tsx` - Intégration
- Mise à jour `frontend/src/api/client.ts` - API client de base

**Acceptance Criteria**:
- [ ] Tableau affiché avec 3 colonnes
- [ ] Mappings chargés depuis l'API
- [ ] Lignes triées par Type puis Catégorie
- [ ] Largeurs des colonnes ajustées
- [ ] Catégories spéciales affichées avec "Données calculées"
- [ ] Test visuel dans navigateur validé

---

#### Step 8.5.2 : Frontend - Colonne 1 "Type"
**Status**: ⏳ À FAIRE  
**Description**: Afficher le Type en première colonne avec un dropdown éditable pour sélectionner "Produits d'exploitation" ou "Charges d'exploitation".

**Tasks**:
- [ ] Afficher le Type en première colonne avec un dropdown
- [ ] Dropdown avec 2 options : "Produits d'exploitation" et "Charges d'exploitation"
- [ ] Permettre la modification du Type via le dropdown pour chaque ligne
- [ ] Permettre plusieurs lignes avec la même valeur de Type
- [ ] Initialiser le Type selon la catégorie (déduction automatique au chargement)
- [ ] Stocker le Type en frontend uniquement (pas en backend)
- [ ] Utiliser le Type pour filtrer les catégories disponibles lors de l'ajout d'une ligne (Step 8.5.5)
- [ ] Tester dans le navigateur

**Acceptance Criteria**:
- [ ] Type affiché avec dropdown éditable pour chaque ligne
- [ ] Modification du Type possible via dropdown
- [ ] Plusieurs lignes peuvent avoir le même Type
- [ ] Type initialisé automatiquement selon la catégorie au chargement
- [ ] Test visuel dans navigateur validé

---

#### Step 8.5.3 : Frontend - Colonne 2 "Catégorie comptable"
**Status**: ⏳ À FAIRE  
**Description**: Ajouter dropdown "Catégorie comptable" en deuxième colonne. Le dropdown doit filtrer les catégories disponibles selon le Type sélectionné en colonne 1.

**Tasks**:
- [ ] Ajouter dropdown "Catégorie comptable" en deuxième colonne
- [ ] Filtrer les catégories disponibles selon le Type sélectionné en colonne 1 :
  - Si Type = "Produits d'exploitation" → afficher seulement les catégories de `PRODUITS_CATEGORIES`
  - Si Type = "Charges d'exploitation" → afficher seulement les catégories de `CHARGES_CATEGORIES`
- [ ] Permettre la sélection d'une catégorie dans le dropdown
- [ ] Permettre plusieurs lignes avec la même catégorie comptable
- [ ] Gérer les catégories spéciales (amortissements, coût financement) :
  - Ces catégories doivent être disponibles dans le dropdown si le Type correspond
  - Afficher "Données calculées" dans la colonne Level 1 (read-only)
  - Pas de dropdown pour Level 1 pour ces catégories
- [ ] Sauvegarde automatique au changement de catégorie (mise à jour du mapping via API)
- [ ] Réinitialiser automatiquement la catégorie si elle n'est plus valide après un changement de Type
- [ ] Tester dans le navigateur

**Acceptance Criteria**:
- [ ] Dropdown visible et fonctionnel pour chaque ligne
- [ ] Catégories filtrées dynamiquement selon le Type sélectionné en colonne 1
- [ ] Changement de Type en colonne 1 met à jour les options disponibles dans le dropdown de la colonne 2
- [ ] Si la catégorie actuelle n'est plus valide après un changement de Type, elle est réinitialisée automatiquement
- [ ] Sauvegarde automatique fonctionne (mise à jour du mapping en backend)
- [ ] Plusieurs lignes peuvent avoir la même catégorie comptable
- [ ] Catégories spéciales affichées avec "Données calculées" dans Level 1
- [ ] Test visuel dans navigateur validé

---

#### Step 8.5.4 : Frontend - Colonne 3 "Level 1 (valeurs)"
**Status**: ⏳ À FAIRE  
**Description**: Implémenter l'affichage et la gestion des tags level_1 (comme AmortizationConfigCard).

**Tasks**:
- [ ] Implémenter l'affichage des tags bleus pour les valeurs level_1 sélectionnées
- [ ] Ajouter bouton "+ Ajouter" qui ouvre un dropdown avec toutes les valeurs level_1 disponibles
- [ ] Charger les valeurs level_1 depuis les transactions enrichies (valeurs uniques via `transactionsAPI.getUniqueValues('level_1')`)
- [ ] **Filtrer les valeurs level_1 selon les level_3 sélectionnés** : Seules les valeurs level_1 qui existent dans les transactions avec les level_3 sélectionnés seront disponibles
- [ ] Implémenter l'ajout d'une valeur (tag bleu avec "x")
- [ ] Implémenter la suppression d'une valeur (clic sur "x")
- [ ] Sauvegarde automatique à chaque ajout/suppression
- [ ] Filtrer les valeurs déjà assignées dans le dropdown
- [ ] Désactiver le bouton "+ Ajouter" si toutes les valeurs sont déjà assignées
- [ ] Pour les catégories spéciales ("Charges d'amortissements" et "Coût du financement (hors remboursement du capital)") :
  - Afficher "Données calculées" (read-only, grisé) au lieu des tags level_1
  - Désactiver le bouton "+ Ajouter" (pas de sélection de level_1 possible)
  - Ces catégories n'ont pas de mapping level_1, les données sont calculées automatiquement
- [ ] Tester dans le navigateur

**Acceptance Criteria**:
- [ ] Tags bleus affichés pour les valeurs level_1
- [ ] Bouton "+ Ajouter" ouvre dropdown avec valeurs disponibles
- [ ] Ajout/suppression fonctionne
- [ ] Sauvegarde automatique fonctionne (mise à jour du mapping via API)
- [ ] Valeurs déjà assignées filtrées du dropdown
- [ ] Catégories spéciales ("Charges d'amortissements" et "Coût du financement") affichent "Données calculées" (read-only, grisé)
- [ ] Bouton "+ Ajouter" désactivé pour les catégories spéciales
- [ ] Test visuel dans navigateur validé

---

#### Step 8.5.5 : Frontend - Ajout de lignes (catégories)
**Status**: ⏳ À FAIRE  
**Description**: Ajouter bouton "+ Ajouter une catégorie" en bas du tableau (comme "+ Ajouter un type" dans AmortizationConfigCard).

**Tasks**:
- [ ] Ajouter bouton "+ Ajouter une catégorie" en bas du tableau (dans une ligne spéciale, comme AmortizationConfigCard)
- [ ] **PAS DE MODAL** - Création directe d'une ligne avec catégorie par défaut (comme AmortizationConfigCard)
- [ ] Prendre la première catégorie de "Charges d'exploitation" par défaut
- [ ] Créer une nouvelle ligne avec la catégorie sélectionnée
- [ ] Sauvegarde automatique à la création
- [ ] Tester dans le navigateur

**Acceptance Criteria**:
- [ ] Bouton "+ Ajouter une catégorie" visible en bas du tableau
- [ ] Création directe sans modal (comme AmortizationConfigCard)
- [ ] Nouvelle ligne créée avec catégorie par défaut
- [ ] Sauvegarde automatique fonctionne
- [ ] Test visuel dans navigateur validé

---

#### Step 8.5.6 : Frontend - Suppression de lignes (catégories)
**Status**: ⏳ À FAIRE  
**Description**: Implémenter le menu contextuel (clic droit) pour supprimer une ligne (comme AmortizationConfigCard).

**Tasks**:
- [ ] Implémenter le menu contextuel (clic droit) sur une ligne
- [ ] Ajouter option "🗑️ Supprimer" dans le menu
- [ ] Confirmation avant suppression (comme AmortizationConfigCard)
- [ ] Supprimer le mapping depuis l'API (`compteResultatAPI.deleteMapping(id)`)
- [ ] Recharger les mappings après suppression
- [ ] Tester dans le navigateur

**Acceptance Criteria**:
- [ ] Menu contextuel s'affiche au clic droit
- [ ] Option "🗑️ Supprimer" visible
- [ ] Confirmation demandée avant suppression
- [ ] Suppression fonctionne (backend)
- [ ] Tableau se rafraîchit après suppression
- [ ] Test visuel dans navigateur validé

---

#### Step 8.5.7 : Frontend - Bouton "Réinitialiser les mappings"
**Status**: ⏳ À FAIRE  
**Description**: Ajouter bouton "🔄 Réinitialiser les mappings" dans le header de la card (comme AmortizationConfigCard).

**Tasks**:
- [ ] Ajouter bouton "🔄 Réinitialiser les mappings" dans le header de la card
- [ ] Bouton visible uniquement s'il y a des mappings
- [ ] Confirmation avant réinitialisation (comme AmortizationConfigCard)
- [ ] Supprimer tous les mappings depuis l'API (un par un)
- [ ] Afficher le nombre de mappings à supprimer dans la confirmation
- [ ] Recharger les mappings après réinitialisation
- [ ] Message de succès après réinitialisation
- [ ] Tester dans le navigateur

**Acceptance Criteria**:
- [ ] Bouton visible dans le header (uniquement si mappings existent)
- [ ] Confirmation demandée avant réinitialisation avec nombre de mappings
- [ ] Tous les mappings supprimés
- [ ] Tableau se rafraîchit après réinitialisation
- [ ] Message de succès affiché
- [ ] Test visuel dans navigateur validé

---

#### Step 8.5.8 : Frontend - Callback onConfigUpdated
**Status**: ⏳ À FAIRE  
**Description**: Implémenter un callback `onConfigUpdated` pour notifier le tableau quand les mappings changent.

**Tasks**:
- [ ] Ajouter prop `onConfigUpdated?: () => void` à `CompteResultatConfigCard`
- [ ] Appeler `onConfigUpdated()` après chaque modification (ajout/suppression mapping, changement crédits)
- [ ] Utiliser ce callback dans le composant parent pour déclencher le rechargement du tableau
- [ ] Tester dans le navigateur

**Acceptance Criteria**:
- [ ] Callback `onConfigUpdated` implémenté
- [ ] Callback appelé après chaque modification
- [ ] Rechargement du tableau déclenché automatiquement
- [ ] Test visuel dans navigateur validé

---

**Step 8.5 - Acceptance Criteria globaux**:
- [ ] Tableau affiché dans l'onglet "Compte de résultat" (structure comme AmortizationConfigCard)
- [ ] 3 colonnes : Type, Catégorie comptable, Level 1 (valeurs)
- [ ] Dropdown Type fonctionne et filtre les catégories
- [ ] Dropdown Catégorie fonctionne avec catégories prédéfinies
- [ ] Tags bleus pour level_1 avec "+ Ajouter" et "x" pour supprimer
- [ ] Catégories spéciales (amortissements et coût financement) gérées correctement
- [ ] Bouton "+ Ajouter une catégorie" fonctionne (création directe, pas de modal)
- [ ] Menu contextuel (clic droit) avec "Supprimer" fonctionne
- [ ] Bouton "🔄 Réinitialiser les mappings" fonctionne
- [ ] Catégorie spéciale "Charges d'amortissements" gérée correctement (Step 8.5.4)
- [ ] Catégorie spéciale "Coût du financement" gérée correctement (Step 8.5.4)
- [ ] Sauvegarde automatique fonctionne (comme AmortizationConfigCard)
- [ ] Callback `onConfigUpdated` fonctionne (Step 8.5.8)
- [ ] API client créé et fonctionnel
- [ ] Test visuel dans navigateur validé
- [ ] Utilisateur confirme que l'interface correspond à ses attentes

---

### Step 8.6 : Frontend - Card d'affichage (CompteResultatTable)
**Status**: ⏳ À FAIRE  
**Description**: Créer l'interface d'affichage du compte de résultat avec tableau multi-années. Structure identique à `AmortizationTable`.

**⚠️ IMPORTANT : Liaison avec CompteResultatConfigCard**
- La `CompteResultatTable` est **toujours liée** aux données affichées dans `CompteResultatConfigCard`
- Les montants affichés dans le tableau sont calculés **uniquement** à partir des mappings configurés dans la card config
- **Le filtre Level 3 (Step 8.4.5) est appliqué en premier** : Seules les transactions avec level_3 sélectionné sont considérées
- Les catégories affichées dans le tableau correspondent **exactement** aux catégories configurées dans la card config
- Les calculs pour "Charges d'amortissements" et "Coût du financement" sont effectués automatiquement (Steps 8.6.3 et 8.6.4)
- Toute modification dans la card config (ajout/suppression de mapping, changement de crédits) ou dans le filtre Level 3 doit **automatiquement** mettre à jour le tableau
- Le tableau ne doit afficher que les catégories qui ont au moins un mapping configuré dans la card config

**Structure du tableau** :
- **Colonnes** : Catégories | Année 1 | Année 2 | Année 3 | ... (jusqu'à l'année en cours)
- **Lignes** :
  - **Total des produits d'exploitation** (ligne de total, fond gris)
  - Loyers hors charge encaissés
  - Charges locatives payées par locataires
  - Autres revenus
  - **Total des charges d'exploitation** (ligne de total, fond gris)
  - Charges de copropriété hors fonds travaux
  - Fluides non refacturés
  - Assurances
  - Honoraires
  - Travaux et mobilier
  - Impôts et taxes
  - Charges d'amortissements
  - Autres charges diverses
  - Coût du financement (hors remboursement du capital)
  - **Résultat d'exploitation** (ligne de total, fond gris) = Produits - Charges
  - **Résultat net de l'exercice** (ligne de total, fond gris, texte magenta) = Résultat d'exploitation

**Fonctionnalités** :
- Calculer automatiquement pour toutes les années jusqu'à l'année en cours
- Possibilité d'ajouter des années au fur et à mesure
- Calculs spécifiques pour "Charges d'amortissements" (Step 8.6.3) et "Coût du financement" (Step 8.6.4)
- Formatage des montants (€, séparateurs de milliers, 2 décimales)
- Mise en évidence des totaux (fond gris, texte en gras)
- Résultat net en magenta (comme dans l'image)

---

#### Step 8.6.1 : Frontend - Structure de base du tableau
**Status**: ⏳ À FAIRE  
**Description**: Créer la structure de base du composant et du tableau (comme AmortizationTable).

**Tasks**:
- [ ] Créer composant `CompteResultatTable.tsx` (copier structure de base d'`AmortizationTable`)
- [ ] Créer le tableau avec colonnes : Compte de résultat | Années (dynamiques)
- [ ] Définir la liste des catégories comptables (ordre fixe, groupées par type)
- [ ] Calculer automatiquement les années à afficher (de la première transaction jusqu'à l'année en cours)
- [ ] Afficher les en-têtes de colonnes (Compte de résultat + une colonne par année)
- [ ] Afficher structure hiérarchique : ligne de type (avec totaux) + catégories indentées
- [ ] Intégrer dans l'onglet "Compte de résultat" (sous la card de config)
- [ ] Tester dans le navigateur

**Deliverables**:
- `frontend/src/components/CompteResultatTable.tsx` - Structure de base
- Mise à jour `frontend/app/dashboard/etats-financiers/page.tsx` - Intégration

**Acceptance Criteria**:
- [ ] Tableau affiché avec colonnes dynamiques (années)
- [ ] Catégories affichées dans l'ordre fixe (groupées par type)
- [ ] Structure hiérarchique : types avec totaux, catégories indentées
- [ ] Années calculées automatiquement (jusqu'à l'année en cours)
- [ ] Test visuel dans navigateur validé

---

#### Step 8.6.2 : Frontend - Chargement et affichage des montants
**Status**: ⏳ À FAIRE  
**Description**: Charger les montants depuis l'API et les afficher dans le tableau. **Les montants sont toujours liés aux mappings de la card config.**

**⚠️ Liaison avec CompteResultatConfigCard** :
- Le tableau doit se mettre à jour automatiquement quand les mappings changent dans la card config
- Utiliser le callback `onConfigUpdated` de `CompteResultatConfigCard` pour déclencher le rechargement
- Afficher uniquement les catégories qui ont des mappings configurés dans la card config

**Tasks**:
- [ ] Appeler l'API pour calculer les montants pour toutes les années (jusqu'à l'année en cours)
- [ ] Endpoint : `GET /api/compte-resultat/calculate?years={year1,year2,...}`
- [ ] Afficher les montants dans les cellules correspondantes (catégorie × année)
- [ ] Gérer l'état de chargement (spinner ou "Chargement...")
- [ ] Gérer les erreurs (affichage de message d'erreur)
- [ ] Recharger les données quand les mappings changent (via `refreshKey` déclenché par `onConfigUpdated` de la card config)
- [ ] Afficher un message si une catégorie spéciale n'a pas de données disponibles (ex: "Aucune donnée d'amortissement" / "Aucun crédit configuré")
- [ ] Tester dans le navigateur

**Acceptance Criteria**:
- [ ] Montants chargés depuis l'API
- [ ] Montants affichés dans les bonnes cellules
- [ ] État de chargement géré
- [ ] Erreurs gérées
- [ ] Rechargement automatique quand les mappings changent dans la card config
- [ ] Message affiché si données non disponibles
- [ ] Test visuel dans navigateur validé

---

#### Step 8.6.3 : Frontend - Calcul spécifique "Charges d'amortissements"
**Status**: ⏳ À FAIRE  
**Description**: Implémenter le calcul et l'affichage spécifique pour la catégorie "Charges d'amortissements" dans la card table.

**⚠️ IMPORTANT** : Cette catégorie ne provient pas des transactions mais de la table `amortization_result`.

**Tasks**:
- [ ] Détecter la catégorie "Charges d'amortissements" dans le tableau
- [ ] Pour chaque année, calculer le total d'amortissement :
  - Récupérer tous les montants depuis la table `amortization_result` pour l'année
  - Sommer tous les montants d'amortissement pour l'année (toutes les catégories)
  - Afficher le montant total dans la cellule correspondante (catégorie × année)
- [ ] Gérer le cas où aucune donnée d'amortissement n'est disponible pour une année : afficher 0,00 €
- [ ] Mettre à jour automatiquement quand les données d'amortissement changent (recalcul automatique)
- [ ] Tester dans le navigateur

**Acceptance Criteria**:
- [ ] Catégorie "Charges d'amortissements" détectée automatiquement
- [ ] Montants récupérés depuis la table `amortization_result`
- [ ] Total calculé correctement pour chaque année (somme de tous les montants d'amortissement)
- [ ] Montants corrects pour plusieurs années
- [ ] Recalcul automatique quand les données d'amortissement changent
- [ ] Test visuel dans navigateur validé
- [ ] Utilisateur confirme que les montants sont corrects

---

#### Step 8.6.4 : Frontend - Calcul spécifique "Coût du financement"
**Status**: ⏳ À FAIRE  
**Description**: Implémenter le calcul et l'affichage spécifique pour la catégorie "Coût du financement (hors remboursement du capital)" dans la card table.

**⚠️ IMPORTANT** : Cette catégorie ne provient pas des transactions mais des `loan_payments`.

**Tasks**:
- [ ] Détecter la catégorie "Coût du financement (hors remboursement du capital)" dans le tableau
- [ ] Récupérer tous les crédits configurés (via `loanConfigsAPI.getAll()`)
- [ ] Pour chaque année, calculer le coût du financement :
  - Filtrer `loan_payments` par année (date entre 01/01/année et 31/12/année)
  - **Gérer le cas d'un seul crédit** : Si un seul crédit configuré, sommer `interest` + `insurance` de ce crédit pour l'année
  - **Gérer le cas de plusieurs crédits** : Si plusieurs crédits configurés, sommer `interest` + `insurance` de **tous les crédits** pour chaque année
  - Afficher le montant total dans la cellule correspondante (catégorie × année)
- [ ] Gérer le cas où aucun crédit n'est configuré : afficher "Aucun crédit configuré" (grisé)
- [ ] Gérer le cas où un crédit n'a pas de données pour une année : afficher 0,00 €
- [ ] Mettre à jour automatiquement quand les crédits ou les loan_payments changent (recalcul automatique)
- [ ] Tester dans le navigateur

**Acceptance Criteria**:
- [ ] Catégorie "Coût du financement" détectée automatiquement
- [ ] Montants récupérés depuis tous les crédits configurés (via `loan_payments`)
- [ ] **Cas d'un seul crédit** : Total calculé correctement (somme interest + insurance de ce crédit)
- [ ] **Cas de plusieurs crédits** : Total calculé correctement pour chaque année (somme interest + insurance de **tous les crédits**)
- [ ] Message affiché si aucun crédit configuré
- [ ] Montants corrects pour plusieurs années
- [ ] Recalcul automatique quand les crédits ou loan_payments changent
- [ ] Test visuel dans navigateur validé
- [ ] Utilisateur confirme que les montants sont corrects

---

#### Step 8.6.5 : Frontend - Calcul et affichage des totaux
**Status**: ⏳ À FAIRE  
**Description**: Calculer et afficher les lignes de totaux (comme dans l'image).

**Tasks**:
- [ ] Calculer "Total des produits d'exploitation" = somme des catégories de produits (affiché sur ligne de type)
- [ ] Calculer "Total des charges d'exploitation" = somme des catégories de charges (affiché sur ligne de type)
- [ ] Calculer "Résultat de l'exercice" = Total produits - Total charges
- [ ] Afficher la ligne "Résultat de l'exercice" en bas du tableau avec fond gris
- [ ] Mettre en évidence les totaux (texte en gras, fond gris)
- [ ] Afficher en rouge si résultat négatif
- [ ] Afficher "Résultat net de l'exercice" en magenta
- [ ] Tester dans le navigateur

**Acceptance Criteria**:
- [ ] Totaux calculés correctement (par type et résultat de l'exercice)
- [ ] Lignes de totaux affichées avec fond gris
- [ ] Totaux mis en évidence (texte en gras)
- [ ] Résultat négatif affiché en rouge
- [ ] Résultat net affiché en magenta
- [ ] Test visuel dans navigateur validé

---

#### Step 8.6.6 : Frontend - Formatage des montants
**Status**: ⏳ À FAIRE  
**Description**: Formater les montants (€, séparateurs de milliers, 2 décimales).

**Tasks**:
- [ ] Formater les montants avec séparateurs de milliers (ex: 1 234,56 €)
- [ ] Afficher 2 décimales
- [ ] Afficher le symbole €
- [ ] Gérer les valeurs négatives (affichage en rouge)
- [ ] Gérer les valeurs nulles (affichage "0,00 €")
- [ ] Tester dans le navigateur

**Acceptance Criteria**:
- [ ] Montants formatés correctement (1 234,56 €)
- [ ] 2 décimales affichées
- [ ] Symbole € visible
- [ ] Valeurs négatives gérées (affichage en rouge)
- [ ] Test visuel dans navigateur validé

---

#### Step 8.6.7 : Frontend - Fonctionnalité pin/unpin pour la card de configuration
**Status**: ⏳ À FAIRE  
**Description**: Ajouter un bouton pin/unpin à côté du titre "Configuration du compte de résultat" pour replier/déplier la card.

**Tasks**:
- [ ] Ajouter un état `isCollapsed` pour gérer l'état replié/déplié
- [ ] Ajouter un bouton pin/unpin (📌/📌) à côté du titre "Configuration du compte de résultat"
- [ ] Implémenter la logique de repli/dépli : masquer/afficher le contenu de la card (tableau, boutons)
- [ ] Sauvegarder l'état dans localStorage pour persister entre les sessions
- [ ] Charger l'état depuis localStorage au montage du composant
- [ ] Tester dans le navigateur

**Acceptance Criteria**:
- [ ] Bouton pin/unpin visible à côté du titre
- [ ] Clic sur le bouton replie/déplie la card
- [ ] Le contenu (tableau, boutons) est masqué quand la card est repliée
- [ ] Seul le titre et le bouton pin restent visibles quand replié
- [ ] L'état est sauvegardé dans localStorage
- [ ] L'état est restauré au rechargement de la page
- [ ] Test visuel dans navigateur validé

---

#### Step 8.6.8 : Frontend - Ajout d'années
**Status**: ⏳ À FAIRE  
**Description**: Permettre d'ajouter des années au fur et à mesure.

**Tasks**:
- [ ] Ajouter bouton "+ Ajouter une année" dans le header
- [ ] Ouvrir un input ou dropdown pour sélectionner une année
- [ ] Calculer et afficher les montants pour la nouvelle année
- [ ] Ajouter la colonne correspondante dans le tableau
- [ ] Sauvegarder la liste des années ajoutées (localStorage ou state)
- [ ] Tester dans le navigateur

**Acceptance Criteria**:
- [ ] Bouton "+ Ajouter une année" visible
- [ ] Sélection d'année fonctionne
- [ ] Nouvelle colonne ajoutée au tableau
- [ ] Montants calculés pour la nouvelle année
- [ ] Liste des années sauvegardée
- [ ] Test visuel dans navigateur validé

---

**Step 8.6 - Acceptance Criteria globaux**:
- [ ] Tableau affiché dans l'onglet "Compte de résultat" (sous la card de config)
- [ ] **⚠️ LIAISON AVEC CompteResultatConfigCard** : Le tableau est **toujours lié** aux données de la card config
- [ ] **Seules les catégories avec mappings configurés dans la card config sont affichées**
- [ ] Structure : 1 colonne catégories + 1 colonne par année
- [ ] Années calculées automatiquement (jusqu'à l'année en cours)
- [ ] Calculs spécifiques pour "Charges d'amortissements" (Step 8.6.3) : récupération depuis la table `amortization_result`
- [ ] Calculs spécifiques pour "Coût du financement" (Step 8.6.4) : récupération depuis tous les crédits configurés
- [ ] Montants calculés et affichés correctement pour toutes les catégories configurées
- [ ] Totaux calculés et affichés (fond gris, texte en gras)
- [ ] Résultat net en magenta
- [ ] Formatage des montants correct (€, séparateurs, 2 décimales)
- [ ] Ajout d'années fonctionne
- [ ] **Rechargement automatique quand les mappings changent dans la card config**
- [ ] **Toute modification dans la card config (ajout/suppression mapping, changement crédits) met à jour le tableau automatiquement**
- [ ] Test visuel dans navigateur validé
- [ ] Utilisateur confirme que l'interface correspond à l'image

---

## Notes de développement

- **Structure identique aux amortissements** : Réutiliser autant que possible la structure et les patterns de `AmortizationConfigCard` et `AmortizationTable`
- **Liaison card config ↔ tableau** : Le tableau doit toujours refléter les configurations de la card config
- **Calculs backend** : Tous les calculs doivent être effectués côté backend pour garantir la cohérence
- **Recalcul automatique** : Les comptes de résultat doivent être invalidés et recalculés quand les données sources changent
