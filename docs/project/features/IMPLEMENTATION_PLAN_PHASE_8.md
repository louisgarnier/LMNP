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
**Status**: ✅ TERMINÉ  
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
- [x] Créer table `compte_resultat_mappings` avec colonnes :
  - `id` (PK)
  - `category_name` (nom de la catégorie comptable, ex: "Loyers hors charge encaissés")
  - `type` (Type: "Produits d'exploitation" ou "Charges d'exploitation" pour les catégories personnalisées)
  - `level_1_values` (JSON array optionnel des level_1 à inclure, NULL par défaut)
  - `created_at`, `updated_at`
- [x] Créer table `compte_resultat_data` avec colonnes :
  - `id` (PK)
  - `annee` (année du compte de résultat)
  - `category_name` (nom de la catégorie comptable)
  - `amount` (montant pour cette catégorie et cette année)
  - `created_at`, `updated_at`
- [x] Créer table `compte_resultat_config` avec colonnes :
  - `id` (PK)
  - `level_3_values` (JSON array des level_3 sélectionnés)
  - `created_at`, `updated_at`
- [x] Créer modèles SQLAlchemy dans `backend/database/models.py`
- [x] Créer modèles Pydantic dans `backend/api/models.py`
- [x] Créer test unitaire pour les modèles
- [x] Valider avec l'utilisateur

**Deliverables**:
- `backend/database/models.py` - Modèles `CompteResultatMapping`, `CompteResultatData` et `CompteResultatConfig`
- `backend/api/models.py` - Modèles Pydantic
- `backend/tests/test_compte_resultat_models.py` - Test unitaire
- `backend/database/__init__.py` - Export des modèles
- `backend/database/migrations/add_type_to_compte_resultat_mappings.py` - Migration pour ajouter colonne `type`

**Acceptance Criteria**:
- [x] Tables créées en BDD (compte_resultat_mappings, compte_resultat_data, compte_resultat_config)
- [x] Modèles SQLAlchemy fonctionnels
- [x] Modèles Pydantic créés
- [x] Tests unitaires passent
- [x] Migration pour ajouter colonne `type` dans `compte_resultat_mappings`

---

### Step 8.2 : Backend - Service compte de résultat (calculs)
**Status**: ✅ TERMINÉ  
**Description**: Implémenter la logique de calcul du compte de résultat.

**Sources de données** :
- **Produits/Charges** : Transactions enrichies via `level_1` (logique OR, filtrer par date pour l'année)
- **Amortissements** : Depuis la table `amortization_result` (sélectionner le total pour chaque année)
- **Intérêts/Assurance crédit** : Depuis `loan_payments` (filtrer par année, sommer `interest` + `insurance` de **tous les crédits configurés**)

**Tasks**:
- [x] Créer fichier `backend/api/services/compte_resultat_service.py`
- [x] Implémenter fonction `get_mappings()` : Charger les mappings depuis la table
- [x] Implémenter fonction `get_level_3_values()` : Charger les level_3_values depuis `compte_resultat_config`
- [x] Implémenter fonction `calculate_produits_exploitation(year, mappings, level_3_values)` :
  - **Filtrer d'abord par level_3** : Seules les transactions dont le `level_3` est dans `level_3_values` (depuis `compte_resultat_config`)
  - Filtrer transactions par année (date entre 01/01/année et 31/12/année)
  - Grouper par catégorie selon les mappings level_1 
  - Sommer les montants par catégorie
  - Prendre en compte transactions positives ET négatives (revenus positifs - remboursements négatifs)
- [x] Implémenter fonction `calculate_charges_exploitation(year, mappings, level_3_values)` :
  - **Filtrer d'abord par level_3** : Seules les transactions dont le `level_3` est dans `level_3_values` (depuis `compte_resultat_config`)
  - Filtrer transactions par année
  - Grouper par catégorie selon les mappings level_1
  - Sommer les montants par catégorie
  - Prendre en compte transactions positives ET négatives (dépenses négatives - remboursements/crédits positifs)
- [x] Implémenter fonction `get_amortissements(year)` :
  - Récupérer le total d'amortissement pour l'année depuis la table `amortization_result`
  - Sommer tous les montants d'amortissement pour l'année (toutes les catégories)
- [x] Implémenter fonction `get_cout_financement(year)` :
  - Récupérer tous les crédits configurés depuis la base de données
  - Filtrer `loan_payments` par année (date entre 01/01/année et 31/12/année)
  - **Gérer le cas d'un seul crédit** : Si un seul crédit configuré, sommer `interest` + `insurance` de ce crédit pour l'année
  - **Gérer le cas de plusieurs crédits** : Si plusieurs crédits configurés, sommer `interest` + `insurance` de **tous les crédits** pour chaque année
  - Retourner le total (somme de tous les crédits pour l'année)
- [x] Implémenter fonction `calculate_compte_resultat(year, mappings, level_3_values)` :
  - Récupérer `level_3_values` depuis `compte_resultat_config`
  - Calculer tous les produits d'exploitation (avec filtrage par level_3)
  - Calculer toutes les charges d'exploitation (incluant amortissements et coût financement, avec filtrage par level_3)
  - Calculer Résultat d'exploitation = Produits - Charges
  - Calculer Résultat net = Résultat d'exploitation
- [x] Regrouper tous les mappings d'une même catégorie avec OR pour éviter de compter plusieurs fois les mêmes transactions
- [x] Créer test complet avec données réelles
- [x] Valider avec l'utilisateur

**Deliverables**:
- `backend/api/services/compte_resultat_service.py` - Service de calcul
- `backend/tests/test_compte_resultat_service.py` - Tests du service

**Tests**:
- [x] Test calcul produits d'exploitation (avec mappings)
- [x] Test calcul charges d'exploitation (avec mappings)
- [x] Test récupération amortissements depuis table amortization_result
- [x] Test calcul coût du financement depuis loan_payments (cas 1 crédit et cas plusieurs crédits)
- [x] Test calcul résultat d'exploitation
- [x] Test calcul résultat net
- [x] Test avec données réelles (année complète)
- [x] Test regroupement des mappings (éviter doublons)

**Acceptance Criteria**:
- [x] Tous les calculs fonctionnent correctement
- [x] **Filtrage par level_3 appliqué en premier** (seules les transactions avec level_3 sélectionné sont considérées)
- [x] Mappings level_1 appliqués correctement sur les transactions filtrées par level_3
- [x] Regroupement des mappings d'une même catégorie avec OR pour éviter les doublons
- [x] Transactions positives ET négatives prises en compte pour toutes les catégories
- [x] Amortissements récupérés depuis AmortizationResult
- [x] Coût du financement calculé depuis loan_payments (somme de **tous les crédits configurés** pour chaque année)
- [x] Gestion correcte du cas d'un seul crédit et du cas de plusieurs crédits
- [x] Test script exécutable et tous les tests passent
- [x] Utilisateur confirme que les calculs sont corrects

---

### Step 8.3 : Backend - Endpoints API pour compte de résultat
**Status**: ✅ TERMINÉ  
**Description**: Créer les endpoints API pour gérer les mappings et générer/récupérer les comptes de résultat.

**Tasks**:
- [x] Créer fichier `backend/api/routes/compte_resultat.py`
- [x] Créer endpoint `GET /api/compte-resultat/mappings` : Liste des mappings
- [x] Créer endpoint `POST /api/compte-resultat/mappings` : Créer un mapping
- [x] Créer endpoint `PUT /api/compte-resultat/mappings/{id}` : Mettre à jour un mapping
- [x] Créer endpoint `DELETE /api/compte-resultat/mappings/{id}` : Supprimer un mapping
- [x] Créer endpoint `POST /api/compte-resultat/generate` : Générer un compte de résultat
  - Paramètres : `year`
  - Retourne : Compte de résultat calculé et stocké en DB
- [x] Créer endpoint `GET /api/compte-resultat/calculate?years={year1,year2,...}` : Calculer les montants pour plusieurs années
  - Retourne : Montants par catégorie et année (basé sur les mappings configurés)
- [x] Créer endpoint `GET /api/compte-resultat` : Récupérer les comptes de résultat
  - Paramètres : `year` (optionnel), `start_year`, `end_year` (pour plusieurs années)
  - Retourne : Liste des comptes de résultat (plusieurs années possibles)
- [x] Créer endpoint `GET /api/compte-resultat/data` : Récupérer les données brutes
- [x] Créer endpoint `DELETE /api/compte-resultat/data/{id}` : Supprimer une donnée
- [x] Créer endpoint `DELETE /api/compte-resultat/year/{year}` : Supprimer toutes les données d'une année
- [x] Créer endpoints `GET /api/compte-resultat/config` et `PUT /api/compte-resultat/config` : Gérer la configuration (level_3_values)
- [x] Enregistrer router dans `backend/api/main.py`
- [x] Créer test manuel pour les endpoints
- [x] Valider avec l'utilisateur

**Deliverables**:
- `backend/api/routes/compte_resultat.py` - Endpoints API
- Mise à jour `backend/api/main.py` - Enregistrement du router
- `backend/tests/test_compte_resultat_endpoints_manual.py` - Test manuel

**Acceptance Criteria**:
- [x] Tous les endpoints fonctionnent correctement
- [x] Génération de compte de résultat fonctionne
- [x] Calcul pour plusieurs années fonctionne
- [x] Récupération de plusieurs années fonctionne
- [x] Gestion d'erreur correcte
- [x] Endpoints de configuration (GET/PUT) pour level_3_values fonctionnent
- [x] Tests manuels créés (à exécuter avec serveur backend démarré)

---

### Step 8.4 : Backend - Recalcul automatique
**Status**: ✅ TERMINÉ  
**Description**: Implémenter le recalcul automatique des comptes de résultat quand les données sources changent.

**Déclencheurs de recalcul** :
- Transactions ajoutées/modifiées/supprimées
- Données d'amortissement modifiées
- Crédits ajoutés/modifiés (mensualités loan_payments)
- Mappings modifiés

**Tasks**:
- [x] Créer fonction `invalidate_compte_resultat_for_year(year)` : Supprimer les comptes de résultat pour une année
- [x] Créer fonction `invalidate_compte_resultat_for_date_range(start_date, end_date)` : Supprimer pour une plage de dates
- [x] Créer fonction `invalidate_all_compte_resultat()` : Supprimer tous les comptes de résultat
- [x] Créer fonction `invalidate_compte_resultat_for_transaction_date(date)` : Supprimer pour une date spécifique
- [x] Implémenter recalcul automatique dans :
  - Endpoints de transactions (POST, PUT, DELETE, import)
  - Endpoints d'amortissement (recalculate_amortizations)
  - Endpoints de loan_payments (POST, PUT, DELETE, import)
  - Endpoints de mappings (POST, PUT, DELETE)
  - Endpoints d'amortization (recalculate_amortizations)
- [x] Créer test pour vérifier le recalcul automatique
- [x] Valider avec l'utilisateur

**Deliverables**:
- Mise à jour `backend/api/services/compte_resultat_service.py` - Fonctions de recalcul
- Mise à jour des endpoints concernés (transactions, amortization, loan_payments, mappings)
- `backend/tests/test_compte_resultat_recalcul.py` - Tests de recalcul

**Acceptance Criteria**:
- [x] Recalcul déclenché quand transactions changent (create, update, delete, import)
- [x] Recalcul déclenché quand amortissements changent (recalculate_amortizations)
- [x] Recalcul déclenché quand loan_payments changent (create, update, delete, import)
- [x] Recalcul déclenché quand mappings changent (create, update, delete)
- [x] Recalcul déclenché quand les données d'amortissement changent (recalculate_amortizations)
- [x] Tests de recalcul passent
- [x] Utilisateur confirme que le recalcul fonctionne

---

### Step 8.4.5 : Backend + Frontend - Filtre Level 3 (Valeur à considérer dans le compte de résultat)
**Status**: ✅ TERMINÉ  
**Description**: Implémenter le filtre Level 3 qui détermine quelles transactions seront considérées dans les calculs du compte de résultat. Ce filtre est appliqué EN PREMIER, avant les mappings level_1.

**⚠️ IMPORTANT : Logique de filtrage**
- Le filtre Level 3 est appliqué EN PREMIER
- Seules les transactions dont le `level_3` est dans la liste sélectionnée seront prises en compte
- Ensuite, dans le tableau de mapping, on pourra sélectionner des `level_1` parmi celles qui sont concernées par ces `level_3`
- Si aucune valeur level_3 n'est sélectionnée, aucune transaction ne sera considérée (obligatoire de sélectionner au moins une valeur)

**Tasks Backend**:
- [x] Créer table `compte_resultat_config` avec colonnes :
  - `id` (PK)
  - `level_3_values` (JSON array des level_3 sélectionnés, ex: ["VALEUR1", "VALEUR2"])
  - `created_at`, `updated_at`
- [x] Créer modèle SQLAlchemy `CompteResultatConfig` dans `backend/database/models.py`
- [x] Créer modèles Pydantic dans `backend/api/models.py` :
  - `CompteResultatConfigBase`, `CompteResultatConfigCreate`, `CompteResultatConfigUpdate`, `CompteResultatConfigResponse`
- [x] Créer endpoint `GET /api/compte-resultat/config` : Récupérer la configuration (level_3_values)
- [x] Créer endpoint `PUT /api/compte-resultat/config` : Mettre à jour la configuration (level_3_values)
- [x] Mettre à jour `compte_resultat_service.py` pour filtrer les transactions par `level_3` en premier :
  - Dans `calculate_produits_exploitation` et `calculate_charges_exploitation`, filtrer d'abord par `level_3_values` de la config
  - Seules les transactions avec `level_3` dans la liste sélectionnée seront considérées
- [x] Créer test unitaire pour vérifier le filtrage par level_3
- [x] Valider avec l'utilisateur

**Tasks Frontend**:
- [x] Ajouter champ "Level 3 (Valeur à considérer dans le compte de résultat)" en haut de `CompteResultatConfigCard.tsx`
- [x] Dropdown avec checkboxes (multi-sélection) pour sélectionner les valeurs level_3
- [x] Charger les valeurs level_3 depuis les transactions enrichies (valeurs uniques via `transactionsAPI.getUniqueValues('level_3')`)
- [x] Si aucune transaction chargée : afficher "Aucune valeur disponible" (grisé)
- [x] Afficher les valeurs level_3 disponibles avec checkboxes
- [x] Permettre la sélection de plusieurs valeurs level_3
- [x] Sauvegarde automatique sur changement (mise à jour via API `PUT /api/compte-resultat/config`)
- [x] Charger la configuration au montage du composant (récupérer les level_3_values depuis l'API)
- [x] Masquer le tableau de mapping si aucune valeur level_3 n'est sélectionnée
- [x] Filtrer les valeurs level_1 disponibles dans le tableau selon les level_3 sélectionnés :
  - Seules les transactions avec `level_3` dans la liste sélectionnée seront considérées
  - Les valeurs level_1 disponibles dans le dropdown seront filtrées pour ne montrer que celles qui existent dans les transactions avec les level_3 sélectionnés
- [x] Persistance dans localStorage (optionnel, pour améliorer l'UX)
- [x] Tester dans le navigateur

**Deliverables**:
- `backend/database/models.py` - Modèle `CompteResultatConfig`
- `backend/api/models.py` - Modèles Pydantic
- `backend/api/routes/compte_resultat.py` - Endpoints GET/PUT pour la config
- Mise à jour `backend/api/services/compte_resultat_service.py` - Filtrage par level_3
- `backend/tests/test_compte_resultat_config.py` - Test unitaire
- Mise à jour `frontend/src/components/CompteResultatConfigCard.tsx` - Champ Level 3
- Mise à jour `frontend/src/api/client.ts` - API client pour la config

**Acceptance Criteria**:
- [x] Table `compte_resultat_config` créée en BDD
- [x] Modèles SQLAlchemy et Pydantic créés
- [x] Endpoints GET/PUT fonctionnent correctement
- [x] Service filtre correctement les transactions par level_3 en premier
- [x] Dropdown avec checkboxes fonctionne (multi-sélection)
- [x] Valeurs level_3 chargées depuis les transactions enrichies
- [x] Sauvegarde automatique fonctionne (mise à jour via API)
- [x] Tableau de mapping masqué si aucune valeur level_3 sélectionnée
- [x] Valeurs level_1 filtrées selon les level_3 sélectionnés
- [x] Tests unitaires passent
- [x] Test visuel dans navigateur validé
- [x] Utilisateur confirme que le filtrage fonctionne correctement

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
**Status**: ✅ TERMINÉ  
**Description**: Créer la structure de base du composant et du tableau (comme AmortizationConfigCard).

**Tasks**:
- [x] Créer composant `CompteResultatConfigCard.tsx` (copier structure de base d'`AmortizationConfigCard`)
- [x] Créer le tableau avec 3 colonnes (en-têtes) : Type, Catégorie comptable, Level 1 (valeurs)
- [x] Charger les mappings depuis l'API (`compteResultatAPI.getMappings()`)
- [x] Afficher les lignes existantes (lecture seule pour l'instant, sans édition)
- [x] Déduire le Type automatiquement selon la catégorie (logique frontend)
- [x] Trier les lignes par Type puis par Catégorie comptable
- [x] Ajuster les largeurs des colonnes (Type: 20%, Catégorie: 30%, Level 1: 50%)
- [x] Intégrer dans l'onglet "Compte de résultat"
- [x] Tester dans le navigateur

**Deliverables**:
- `frontend/src/components/CompteResultatConfigCard.tsx` - Structure de base
- Mise à jour `frontend/app/dashboard/etats-financiers/page.tsx` - Intégration
- Mise à jour `frontend/src/api/client.ts` - API client de base

**Acceptance Criteria**:
- [x] Tableau affiché avec 3 colonnes
- [x] Mappings chargés depuis l'API
- [x] Lignes triées par Type puis Catégorie
- [x] Largeurs des colonnes ajustées
- [x] Catégories spéciales affichées avec "Données calculées"
- [x] Test visuel dans navigateur validé

---

#### Step 8.5.2 : Frontend - Colonne 1 "Type"
**Status**: ✅ TERMINÉ  
**Description**: Afficher le Type en première colonne avec un dropdown éditable pour sélectionner "Produits d'exploitation" ou "Charges d'exploitation".

**Tasks**:
- [x] Afficher le Type en première colonne avec un dropdown
- [x] Dropdown avec 2 options : "Produits d'exploitation" et "Charges d'exploitation"
- [x] Permettre la modification du Type via le dropdown pour chaque ligne
- [x] Permettre plusieurs lignes avec la même valeur de Type
- [x] Initialiser le Type selon la catégorie (déduction automatique au chargement)
- [x] Stocker le Type en frontend uniquement (pas en backend)
- [x] Utiliser le Type pour filtrer les catégories disponibles lors de l'ajout d'une ligne (Step 8.5.5)
- [x] Tester dans le navigateur

**Acceptance Criteria**:
- [x] Type affiché avec dropdown éditable pour chaque ligne
- [x] Modification du Type possible via dropdown
- [x] Plusieurs lignes peuvent avoir le même Type
- [x] Type initialisé automatiquement selon la catégorie au chargement
- [x] Test visuel dans navigateur validé

---

#### Step 8.5.3 : Frontend - Colonne 2 "Catégorie comptable"
**Status**: ✅ TERMINÉ  
**Description**: Ajouter dropdown "Catégorie comptable" en deuxième colonne. Le dropdown doit filtrer les catégories disponibles selon le Type sélectionné en colonne 1.

**Tasks**:
- [x] Ajouter dropdown "Catégorie comptable" en deuxième colonne
- [x] Filtrer les catégories disponibles selon le Type sélectionné en colonne 1 :
  - Si Type = "Produits d'exploitation" → afficher seulement les catégories de `PRODUITS_CATEGORIES`
  - Si Type = "Charges d'exploitation" → afficher seulement les catégories de `CHARGES_CATEGORIES`
- [x] Permettre la sélection d'une catégorie dans le dropdown
- [x] Permettre plusieurs lignes avec la même catégorie comptable
- [x] Gérer les catégories spéciales (amortissements, coût financement) :
  - Ces catégories doivent être disponibles dans le dropdown si le Type correspond
  - Afficher "Données calculées" dans la colonne Level 1 (read-only)
  - Pas de dropdown pour Level 1 pour ces catégories
- [x] Sauvegarde automatique au changement de catégorie (mise à jour du mapping via API)
- [x] Réinitialiser automatiquement la catégorie si elle n'est plus valide après un changement de Type
- [x] Tester dans le navigateur

**Acceptance Criteria**:
- [x] Dropdown visible et fonctionnel pour chaque ligne
- [x] Catégories filtrées dynamiquement selon le Type sélectionné en colonne 1
- [x] Changement de Type en colonne 1 met à jour les options disponibles dans le dropdown de la colonne 2
- [x] Si la catégorie actuelle n'est plus valide après un changement de Type, elle est réinitialisée automatiquement
- [x] Sauvegarde automatique fonctionne (mise à jour du mapping en backend)
- [x] Plusieurs lignes peuvent avoir la même catégorie comptable
- [x] Catégories spéciales affichées avec "Données calculées" dans Level 1
- [x] Test visuel dans navigateur validé

---

#### Step 8.5.4 : Frontend - Colonne 3 "Level 1 (valeurs)"
**Status**: ✅ TERMINÉ  
**Description**: Implémenter l'affichage et la gestion des tags level_1 (identique à AmortizationConfigCard, mais filtré par level_3 au lieu de level_2).

**⚠️ IMPORTANT : S'inspirer exactement de AmortizationConfigCard pour la colonne "Level 1 (valeurs)"**
- Dans AmortizationConfigCard : un seul `level_2` est sélectionné → on charge les `level_1` associés à ce `level_2`
- Dans CompteResultatConfigCard : plusieurs `level_3` sont sélectionnés → on charge les `level_1` associés à ces `level_3`

**Tasks Backend** (à faire en premier) :
- [x] Modifier endpoint `/api/transactions/unique-values` dans `backend/api/routes/transactions.py` :
  - Ajouter paramètre `filter_level_3: Optional[List[str]] = Query(None, description="Filtrer par level_3 (array, pour filtrer les level_1 par plusieurs level_3)")`
  - Implémenter le filtrage SQL avec `IN` clause : `query.filter(EnrichedTransaction.level_3.in_(filter_level_3))`
  - Appliquer le filtre uniquement si `filter_level_3` est fourni et non vide
  - Tester avec plusieurs valeurs level_3

**Tasks Frontend** :
- [x] Modifier `transactionsAPI.getUniqueValues()` dans `frontend/src/api/client.ts` :
  - Ajouter paramètre `filterLevel3?: string[]` (après `filterLevel2`)
  - Passer le paramètre au backend : `if (filterLevel3 && filterLevel3.length > 0) params.append('filter_level_3', filterLevel3.join(','))`
  - Note : Backend recevra comme query param (peut nécessiter parsing côté backend si FastAPI ne gère pas automatiquement les arrays)
- [x] Créer fonction `loadLevel1Values()` qui charge les `level_1` filtrés par les `level_3` sélectionnés :
  - Si aucun `level_3` sélectionné → `level1Values = []`
  - Si `level_3` sélectionnés → appeler `transactionsAPI.getUniqueValues('level_1', undefined, undefined, undefined, selectedLevel3Values)`
  - Stocker dans état `level1Values: string[]`
- [x] Appeler `loadLevel1Values()` quand `selectedLevel3Values` change (useEffect)
- [x] Implémenter l'affichage des tags bleus pour les valeurs level_1 sélectionnées (identique à AmortizationConfigCard) :
  - Tags bleus (`backgroundColor: '#3b82f6'`, `color: '#ffffff'`)
  - Chaque tag affiche la valeur avec un bouton "×" pour supprimer
  - Bouton "×" appelle `handleLevel1Remove(categoryName, mappingId, level1Value)`
- [x] Ajouter bouton "+ Ajouter" qui ouvre un dropdown (identique à AmortizationConfigCard) :
  - Bouton avec style identique (`color: '#3b82f6'`, `backgroundColor: '#eff6ff'`, `border: '1px solid #3b82f6'`)
  - Gérer état `openLevel1DropdownId: number | string | null` pour savoir quel dropdown est ouvert
  - Gérer position du dropdown (top/bottom selon position dans viewport)
- [x] Dans le dropdown, afficher les valeurs level_1 disponibles :
  - **Filtrer les `level1Values` pour exclure ceux déjà sélectionnés dans TOUTES les catégories** (comme dans AmortizationConfigCard) :
    - Collecter toutes les valeurs level_1 déjà sélectionnées pour TOUTES les catégories (parcourir tous les mappings)
    - Créer un Set `allSelectedValues` avec toutes ces valeurs
    - Filtrer `level1Values` pour exclure celles dans `allSelectedValues`
  - Si toutes les valeurs sont déjà sélectionnées → afficher "Toutes les valeurs sont déjà sélectionnées"
  - Chaque valeur est cliquable (label avec checkbox) pour l'ajouter
- [x] Implémenter fonction `handleLevel1Toggle(categoryName, level1Value, mappingId?)` :
  - Si `mappingId` n'est pas fourni → créer le mapping avec la catégorie et le premier level_1
  - Si la valeur est déjà dans `mapping.level_1_values` → la supprimer
  - Sinon → l'ajouter
  - Mettre à jour le mapping via API (`compteResultatAPI.updateMapping(mappingId, { level_1_values: JSON.stringify(newValues) })` ou `createMapping`)
  - Recharger les mappings après mise à jour
- [x] Implémenter fonction `handleLevel1Remove(categoryName, mappingId, level1Value)` :
  - Appelle `handleLevel1Toggle` pour supprimer
- [x] Sauvegarde automatique à chaque ajout/suppression (déjà géré dans `handleLevel1Toggle`)
- [x] Afficher le bouton "+ Ajouter" même si la catégorie n'a pas encore de mapping (création automatique au premier ajout)
- [x] Pour les catégories spéciales ("Charges d'amortissements" et "Coût du financement (hors remboursement du capital)") :
  - Afficher "Données calculées" (read-only, grisé) au lieu des tags level_1
  - Désactiver le bouton "+ Ajouter" (pas de sélection de level_1 possible)
  - Ces catégories n'ont pas de mapping level_1, les données sont calculées automatiquement
- [x] Gérer le clic en dehors du dropdown pour le fermer (useEffect avec event listener)
- [x] Tester dans le navigateur

**Deliverables**:
- Mise à jour `backend/api/routes/transactions.py` - Ajouter support `filter_level_3` (array) à `/api/transactions/unique-values`
- Mise à jour `frontend/src/api/client.ts` - Ajouter paramètre `filterLevel3` à `transactionsAPI.getUniqueValues()`
- Mise à jour `frontend/src/components/CompteResultatConfigCard.tsx` - Colonne Level 1 (valeurs)

**Acceptance Criteria**:
- [x] Tags bleus affichés pour les valeurs level_1 sélectionnées (style identique à AmortizationConfigCard)
- [x] Bouton "+ Ajouter" ouvre dropdown avec valeurs disponibles
- [x] Dropdown liste uniquement les level_1 qui existent dans les transactions avec les level_3 sélectionnés
- [x] Dropdown exclut les level_1 déjà sélectionnés dans TOUTES les catégories (pas seulement la catégorie courante)
- [x] Ajout/suppression fonctionne (clic sur valeur dans dropdown ou "×" sur tag)
- [x] Sauvegarde automatique fonctionne (mise à jour du mapping via API ou création si mapping n'existe pas)
- [x] Bouton "+ Ajouter" affiché même si la catégorie n'a pas encore de mapping (création automatique au premier ajout)
- [x] Catégories spéciales ("Charges d'amortissements" et "Coût du financement") affichent "Données calculées" (read-only, grisé)
- [x] Bouton "+ Ajouter" désactivé pour les catégories spéciales
- [x] Dropdown se ferme quand on clique en dehors
- [x] Test visuel dans navigateur validé

---

#### Step 8.5.5 : Frontend - Ajout de lignes (catégories)
**Status**: ✅ TERMINÉ  
**Description**: Ajouter bouton "+ Ajouter une catégorie" en bas du tableau. Le bouton crée toujours une nouvelle ligne, même si toutes les catégories prédéfinies ont déjà un mapping. La nouvelle ligne permet de créer une catégorie personnalisée.

**⚠️ IMPORTANT : La nouvelle ligne créée permet de saisir une catégorie personnalisée (pas limitée aux catégories prédéfinies)**

**Tasks**:
- [x] Ajouter bouton "+ Ajouter une catégorie" en bas du tableau (dans une ligne spéciale, comme AmortizationConfigCard)
- [x] **PAS DE MODAL** - Création directe d'une ligne (comme AmortizationConfigCard)
- [x] Le bouton crée TOUJOURS une nouvelle ligne, même si toutes les catégories prédéfinies ont déjà un mapping
- [x] Créer le mapping en BDD avec :
  - `category_name`: "nouvelle categorie" (valeur par défaut, champ texte libre éditable)
  - `type`: "Charges d'exploitation" (par défaut, stocké en BDD)
  - `level_1_values`: `null`
- [x] **Colonne "Type"** : Dropdown éditable avec 2 options :
  - "Produits d'exploitation"
  - "Charges d'exploitation" (par défaut)
  - Stocké en backend (champ `type` dans la table `compte_resultat_mappings`)
  - Permet de changer le Type librement (sauvegarde automatique via API)
- [x] **Colonne "Catégorie comptable"** : Champ texte libre (input text) éditable :
  - Valeur par défaut : "nouvelle categorie"
  - Permet de saisir n'importe quel nom de catégorie (pas limité aux catégories prédéfinies)
  - Sauvegarde automatique au changement (mise à jour du mapping via API)
  - Validation : Le champ ne peut pas être vide (garder "nouvelle categorie" si vide)
- [x] **Colonne "Level 1 (valeurs)"** : Identique aux autres lignes :
  - Bouton "+ Ajouter" avec dropdown
  - Dropdown liste les level_1 filtrés par les level_3 sélectionnés
  - Tags bleus avec "×" pour supprimer
  - Fonctionne exactement comme pour les autres catégories
- [x] La nouvelle ligne apparaît dans le tableau avec les 3 colonnes éditables
- [x] Sauvegarde automatique à chaque modification (Type, Catégorie, Level 1)
- [x] Tester dans le navigateur

**Acceptance Criteria**:
- [x] Bouton "+ Ajouter une catégorie" visible en bas du tableau
- [x] Création directe sans modal (comme AmortizationConfigCard)
- [x] Le bouton crée toujours une nouvelle ligne, même si toutes les catégories prédéfinies ont déjà un mapping
- [x] Nouvelle ligne créée avec :
  - Type : "Charges d'exploitation" par défaut (dropdown éditable, stocké en BDD)
  - Catégorie comptable : "nouvelle categorie" par défaut (champ texte libre éditable)
  - Level 1 (valeurs) : Vide, avec bouton "+ Ajouter" fonctionnel
- [x] Colonne "Catégorie comptable" permet de saisir n'importe quel texte (pas limité aux catégories prédéfinies)
- [x] Sauvegarde automatique fonctionne pour Type, Catégorie et Level 1
- [x] Le Type est stocké en base de données (champ `type` dans `compte_resultat_mappings`)
- [x] Test visuel dans navigateur validé

---

#### Step 8.5.6 : Frontend - Suppression de lignes (catégories)
**Status**: ✅ TERMINÉ  
**Description**: Implémenter le menu contextuel (clic droit) pour supprimer une ligne (comme AmortizationConfigCard).

**Tasks**:
- [x] Implémenter le menu contextuel (clic droit) sur une ligne
- [x] Ajouter option "🗑️ Supprimer" dans le menu
- [x] Confirmation avant suppression (comme AmortizationConfigCard)
- [x] Supprimer le mapping depuis l'API (`compteResultatAPI.deleteMapping(id)`)
- [x] Recharger les mappings après suppression
- [x] Tester dans le navigateur

**Acceptance Criteria**:
- [x] Menu contextuel s'affiche au clic droit
- [x] Option "🗑️ Supprimer" visible
- [x] Confirmation demandée avant suppression
- [x] Suppression fonctionne (backend)
- [x] Tableau se rafraîchit après suppression
- [x] Le menu ne s'affiche pas pour les catégories spéciales (Charges d'amortissements, Coût du financement)
- [x] Test visuel dans navigateur validé

---

#### Step 8.5.7 : Frontend - Bouton "Réinitialiser les mappings"
**Status**: ✅ TERMINÉ  
**Description**: Ajouter bouton "🔄 Réinitialiser les mappings" dans le header de la card (comme AmortizationConfigCard).

**Tasks**:
- [x] Ajouter bouton "🔄 Réinitialiser les mappings" dans le header de la card
- [x] Bouton visible uniquement s'il y a des mappings
- [x] Confirmation avant réinitialisation (comme AmortizationConfigCard)
- [x] Supprimer tous les mappings depuis l'API (un par un)
- [x] Afficher le nombre de mappings à supprimer dans la confirmation
- [x] Recharger les mappings après réinitialisation
- [x] Message de succès après réinitialisation
- [x] Tester dans le navigateur

**Acceptance Criteria**:
- [x] Bouton visible dans le header (uniquement si mappings existent)
- [x] Confirmation demandée avant réinitialisation avec nombre de mappings
- [x] Tous les mappings supprimés
- [x] Tableau se rafraîchit après réinitialisation
- [x] Message de succès affiché
- [x] Test visuel dans navigateur validé

---

#### Step 8.5.8 : Frontend - Callback onConfigUpdated
**Status**: ✅ TERMINÉ  
**Description**: Implémenter un callback `onConfigUpdated` pour notifier le tableau quand les mappings changent.

**Tasks**:
- [x] Ajouter prop `onConfigUpdated?: () => void` à `CompteResultatConfigCard`
- [x] Appeler `onConfigUpdated()` après chaque modification (ajout/suppression mapping, changement crédits)
- [x] Utiliser ce callback dans le composant parent pour déclencher le rechargement du tableau
- [x] Tester dans le navigateur

**Acceptance Criteria**:
- [x] Callback `onConfigUpdated` implémenté
- [x] Callback appelé après chaque modification (8 endroits : sauvegarde Level 3, création mapping, modification level_1, création catégorie, sauvegarde catégorie, changement Type, suppression mapping, réinitialisation)
- [x] Callback utilisé dans le composant parent (`page.tsx`)
- [x] Le callback sera utilisé pour recharger `CompteResultatTable` dans Step 8.6
- [x] Test visuel dans navigateur validé

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
**Status**: ✅ TERMINÉ  
**Description**: Créer la structure de base du composant et du tableau (comme AmortizationTable).

**Tasks**:
- [x] Créer composant `CompteResultatTable.tsx` (copier structure de base d'`AmortizationTable`)
- [x] Créer le tableau avec colonnes : Compte de résultat | Années (dynamiques)
- [x] Définir la liste des catégories comptables (ordre fixe, groupées par type)
- [x] Calculer automatiquement les années à afficher (de la première transaction jusqu'à l'année en cours)
- [x] Afficher les en-têtes de colonnes (Compte de résultat + une colonne par année)
- [x] Afficher structure hiérarchique : ligne de type (avec totaux) + catégories indentées
- [x] **Connecter le tableau à la card config** : Charger les mappings depuis l'API
- [x] **Filtrer les catégories** : Afficher uniquement les catégories avec mappings configurés (ou catégories spéciales)
- [x] **Support des catégories personnalisées** : Afficher les catégories personnalisées avec leur type depuis le mapping
- [x] Intégrer dans l'onglet "Compte de résultat" (sous la card de config)
- [x] Mise à jour automatique via `refreshKey` quand les mappings changent
- [x] Tester dans le navigateur

**Deliverables**:
- `frontend/src/components/CompteResultatTable.tsx` - Structure de base
- Mise à jour `frontend/app/dashboard/etats-financiers/page.tsx` - Intégration

**Acceptance Criteria**:
- [x] Tableau affiché avec colonnes dynamiques (années)
- [x] Catégories affichées dans l'ordre fixe (groupées par type)
- [x] Structure hiérarchique : types avec totaux, catégories indentées
- [x] Années calculées automatiquement (jusqu'à l'année en cours)
- [x] **Tableau connecté à la card config** : Charge les mappings depuis l'API
- [x] **Filtrage des catégories** : Affiche uniquement les catégories avec mappings configurés (ou catégories spéciales)
- [x] **Catégories personnalisées** : Affichées avec leur type depuis le mapping
- [x] **Mise à jour automatique** : Le tableau se met à jour quand les mappings changent (via `refreshKey`)
- [x] Message informatif si aucune catégorie n'est configurée
- [x] Test visuel dans navigateur validé

---

#### Step 8.6.2 : Frontend - Chargement et affichage des montants
**Status**: ✅ TERMINÉ  
**Description**: Charger les montants depuis l'API et les afficher dans le tableau. **Les montants sont toujours liés aux mappings de la card config.**

**⚠️ Liaison avec CompteResultatConfigCard** :
- Le tableau doit se mettre à jour automatiquement quand les mappings changent dans la card config
- Utiliser le callback `onConfigUpdated` de `CompteResultatConfigCard` pour déclencher le rechargement
- Afficher uniquement les catégories qui ont des mappings configurés dans la card config

**Tasks**:
- [x] Appeler l'API pour calculer les montants pour toutes les années (jusqu'à l'année en cours)
- [x] Endpoint : `GET /api/compte-resultat/calculate?years={year1,year2,...}`
- [x] Afficher les montants dans les cellules correspondantes (catégorie × année)
- [x] Gérer l'état de chargement (spinner ou "Chargement...")
- [x] Gérer les erreurs (affichage de message d'erreur)
- [x] Recharger les données quand les mappings changent (via `refreshKey` déclenché par `onConfigUpdated` de la card config)
- [x] Afficher un message si une catégorie spéciale n'a pas de données disponibles (ex: "Aucune donnée d'amortissement" / "Aucun crédit configuré")
- [x] **Années calculées dynamiquement** depuis la première transaction (au lieu de hardcodé 2020)
- [x] **Catégories spéciales toujours affichées** même sans mapping (Charges d'amortissements, Coût du financement)
- [x] **Calcul des totaux corrigé** : sommation des valeurs affichées dans le tableau
- [x] **Coût du financement filtré** : uniquement les crédits configurés (pas les données de test)
- [x] Tester dans le navigateur

**Acceptance Criteria**:
- [x] Montants chargés depuis l'API
- [x] Montants affichés dans les bonnes cellules
- [x] État de chargement géré
- [x] Erreurs gérées
- [x] Rechargement automatique quand les mappings changent dans la card config
- [x] Message affiché si données non disponibles
- [x] **Années dynamiques** : calculées depuis la première transaction
- [x] **Catégories spéciales affichées** même sans mapping
- [x] **Totaux corrects** : calculés en sommant les valeurs affichées
- [x] Test visuel dans navigateur validé

---

#### Step 8.6.3 : Frontend - Calcul spécifique "Charges d'amortissements"
**Status**: ✅ TERMINÉ  
**Description**: Implémenter le calcul et l'affichage spécifique pour la catégorie "Charges d'amortissements" dans la card table.

**⚠️ IMPORTANT** : Cette catégorie ne provient pas des transactions mais de la table `amortization_result`.

**Tasks**:
- [x] Détecter la catégorie "Charges d'amortissements" dans le tableau
- [x] Pour chaque année, calculer le total d'amortissement :
  - Récupérer tous les montants depuis la table `amortization_result` pour l'année
  - Sommer tous les montants d'amortissement pour l'année (toutes les catégories)
  - Afficher le montant total dans la cellule correspondante (catégorie × année)
- [x] Gérer le cas où aucune donnée d'amortissement n'est disponible pour une année : afficher "Aucune donnée d'amortissement"
- [x] Mettre à jour automatiquement quand les données d'amortissement changent (recalcul automatique via refreshKey)
- [x] Tester dans le navigateur

**Acceptance Criteria**:
- [x] Catégorie "Charges d'amortissements" détectée automatiquement (dans getAmount())
- [x] Montants récupérés depuis la table `amortization_result` (via get_amortissements() dans le backend)
- [x] Total calculé correctement pour chaque année (somme de tous les montants d'amortissement)
- [x] Montants corrects pour plusieurs années
- [x] Recalcul automatique quand les données d'amortissement changent (via refreshKey)
- [x] Message "Aucune donnée d'amortissement" affiché si pas de données
- [x] Test visuel dans navigateur validé
- [ ] Utilisateur confirme que les montants sont corrects

---

#### Step 8.6.4 : Frontend - Calcul spécifique "Coût du financement"
**Status**: ✅ TERMINÉ  
**Description**: Implémenter le calcul et l'affichage spécifique pour la catégorie "Coût du financement (hors remboursement du capital)" dans la card table.

**⚠️ IMPORTANT** : Cette catégorie ne provient pas des transactions mais des `loan_payments`.

**Tasks**:
- [x] Détecter la catégorie "Coût du financement (hors remboursement du capital)" dans le tableau
- [x] Récupérer tous les crédits configurés (via backend `get_cout_financement()` qui filtre par crédits configurés)
- [x] Pour chaque année, calculer le coût du financement :
  - Filtrer `loan_payments` par année (date entre 01/01/année et 31/12/année)
  - **Gérer le cas d'un seul crédit** : Si un seul crédit configuré, sommer `interest` + `insurance` de ce crédit pour l'année
  - **Gérer le cas de plusieurs crédits** : Si plusieurs crédits configurés, sommer `interest` + `insurance` de **tous les crédits** pour chaque année
  - Afficher le montant total dans la cellule correspondante (catégorie × année)
- [x] Gérer le cas où aucun crédit n'est configuré : afficher "Aucun crédit configuré" (grisé)
- [x] Gérer le cas où un crédit n'a pas de données pour une année : afficher 0,00 €
- [x] Mettre à jour automatiquement quand les crédits ou les loan_payments changent (recalcul automatique via refreshKey)
- [x] **Filtrage par crédits configurés uniquement** : Le backend filtre maintenant les paiements par les noms des crédits configurés
- [x] Tester dans le navigateur

**Acceptance Criteria**:
- [x] Catégorie "Coût du financement" détectée automatiquement (dans getAmount())
- [x] Montants récupérés depuis tous les crédits configurés (via `loan_payments` filtrés par crédits configurés)
- [x] **Cas d'un seul crédit** : Total calculé correctement (somme interest + insurance de ce crédit)
- [x] **Cas de plusieurs crédits** : Total calculé correctement pour chaque année (somme interest + insurance de **tous les crédits**)
- [x] Message affiché si aucun crédit configuré ("Aucun crédit configuré")
- [x] Montants corrects pour plusieurs années
- [x] Recalcul automatique quand les crédits ou loan_payments changent (via refreshKey)
- [x] Test visuel dans navigateur validé

---

#### Step 8.6.5 : Frontend - Calcul et affichage des totaux
**Status**: ✅ TERMINÉ  
**Description**: Calculer et afficher les lignes de totaux (comme dans l'image).

**Tasks**:
- [x] Calculer "Total des produits d'exploitation" = somme des catégories de produits (affiché sur ligne de type)
- [x] Calculer "Total des charges d'exploitation" = somme des catégories de charges (affiché sur ligne de type)
- [x] Calculer "Résultat de l'exercice" = Total produits - Total charges
- [x] Afficher la ligne "Résultat de l'exercice" en bas du tableau avec fond gris
- [x] Mettre en évidence les totaux (texte en gras, fond gris)
- [x] Afficher en rouge si résultat négatif (à vérifier si implémenté)
- [x] Afficher "Résultat net de l'exercice" en magenta
- [x] Tester dans le navigateur

**Acceptance Criteria**:
- [x] Totaux calculés correctement (par type et résultat de l'exercice)
- [x] Lignes de totaux affichées avec fond gris (#e5e7eb)
- [x] Totaux mis en évidence (texte en gras, fontWeight: '700')
- [x] Résultat négatif affiché en rouge (à vérifier si implémenté)
- [x] Résultat net affiché en magenta (color: '#d946ef')
- [x] Test visuel dans navigateur validé

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
