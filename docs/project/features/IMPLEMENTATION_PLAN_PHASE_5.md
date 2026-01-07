# Plan d'Implémentation - Phase 5 : Mapping Obligatoire

**Status**: En cours  
**Dernière mise à jour**: 2025-01-XX

## Vue d'ensemble

**Objectif** : Refondre le système de mapping pour imposer des valeurs prédéfinies (level_1, level_2, level_3) au lieu de permettre des valeurs libres.

**Changements principaux** :

- Fichier de référence `scripts/mappings_obligatoires.xlsx` contenant toutes les valeurs autorisées (50 combinaisons)
- Validation des mappings importés contre ce fichier de référence
- Dropdowns filtrés hiérarchiquement (level_1 → level_2 → level_3) dans l'onglet Transactions
- Dropdowns filtrés dans l'onglet Mapping
- Héritage automatique : quand une transaction est mappée, toutes les transactions avec le même nom sont mises à jour immédiatement
- Recalcul automatique des modules dépendants (compte de résultat, amortissements, etc.)

**Fichier source** : `scripts/mappings_obligatoires.xlsx` (référence uniquement, peut être supprimé après chargement initial)
- 50 combinaisons autorisées initiales
- 49 valeurs uniques Level 1
- 18 valeurs uniques Level 2
- 5 valeurs uniques Level 3

**Table de base de données** : `allowed_mappings`
- Stocke toutes les combinaisons autorisées (level_1, level_2, level_3)
- Champ `is_hardcoded` (Boolean) : marque les 50 combinaisons initiales comme protégées
- Les 50 combinaisons initiales (`is_hardcoded = True`) sont **protégées** et ne peuvent **jamais être supprimées**
- Nouvelles combinaisons peuvent être ajoutées via l'interface (`is_hardcoded = False`)
- Nouvelles combinaisons ajoutées manuellement peuvent être supprimées
- Le bouton "Reset mappings autorisés par défaut" supprime uniquement les combinaisons ajoutées manuellement, garde les 50 initiales

**Valeurs Level 3 autorisées** (fixes, validation obligatoire) :
- Passif
- Produits
- Emprunt
- Charges Déductibles
- Actif

**Règle importante** : Si une transaction correspond à plusieurs mappings (même nom), elle ne doit **pas** être mappée automatiquement et se retrouve dans l'onglet "Non classées" (unassigned).

---

## Phase 5 : Mapping Obligatoire

### Step 5.1 : Backend - Création de la table de mappings autorisés

**Status**: ✅ COMPLÉTÉ  

**Description**: Créer une table en BDD pour stocker tous les mappings autorisés (combinaisons valides de level_1, level_2, level_3).

**Tasks**:

- [x] Créer un nouveau modèle SQLAlchemy `AllowedMapping` dans `backend/database/models.py` :

  - Colonnes : `id`, `level_1` (String, not null), `level_2` (String, not null), `level_3` (String, nullable), `is_hardcoded` (Boolean, default=False)

  - Contrainte unique sur (level_1, level_2, level_3) pour éviter les doublons

  - Index sur level_1, level_2, level_3 pour performance

  - **Champ `is_hardcoded`** : marque les 50 combinaisons initiales comme protégées (ne peuvent jamais être supprimées)

- [x] Créer script de migration `backend/scripts/add_is_hardcoded_column.py` pour ajouter la colonne si nécessaire

- [x] Créer `backend/api/services/mapping_obligatoire_service.py` :

  - Fonction `load_allowed_mappings_from_excel(db: Session)` : charge le fichier `scripts/mappings_obligatoires.xlsx` et insère les 50 combinaisons dans la table `allowed_mappings` avec `is_hardcoded = True`
    - **Utilisé une seule fois** pour hard coder les valeurs initiales
    - Le fichier peut être supprimé après le chargement initial

  - Fonction `get_allowed_level1_values(db: Session)` : retourne toutes les valeurs level_1 autorisées (distinct)

  - Fonction `get_allowed_level2_values(db: Session, level_1: str)` : retourne les valeurs level_2 autorisées pour un level_1 donné (distinct)

  - Fonction `get_allowed_level3_values(db: Session, level_1: str, level_2: str)` : retourne les valeurs level_3 autorisées pour un couple (level_1, level_2) (distinct)

  - Fonction `validate_mapping(db: Session, level_1: str, level_2: str, level_3: Optional[str])` : valide qu'une combinaison existe dans la table `allowed_mappings`

  - Fonction `validate_level3_value(level_3: str)` : valide que level_3 est dans la liste fixe (Passif, Produits, Emprunt, Charges Déductibles, Actif)

  - Fonction `reset_to_hardcoded_values(db: Session)` : supprime toutes les combinaisons où `is_hardcoded = False`, garde les 50 initiales (`is_hardcoded = True`)

- [ ] Créer Pydantic models dans `backend/api/models.py` :

  - `AllowedMappingBase`, `AllowedMappingCreate`, `AllowedMappingResponse`, `AllowedMappingListResponse`

- [ ] Endpoint `GET /api/mappings/allowed-level1` pour récupérer toutes les valeurs level_1 autorisées

- [ ] Endpoint `GET /api/mappings/allowed-level2?level_1={value}` pour récupérer les level_2 autorisés pour un level_1

- [ ] Endpoint `GET /api/mappings/allowed-level3?level_1={value}&level_2={value}` pour récupérer les level_3 autorisés pour un couple (level_1, level_2)

- [x] Créer script de migration `backend/scripts/load_hardcoded_mappings.py` pour charger les 50 combinaisons initiales depuis le fichier Excel
  - À exécuter une seule fois pour hard coder les valeurs initiales
  - Marque toutes les combinaisons avec `is_hardcoded = True`
  - Le fichier Excel peut être supprimé après ce chargement initial

- [x] **Tester les endpoints et la validation**

**Deliverables**:

- Nouveau modèle `AllowedMapping` dans `backend/database/models.py`

- Script de migration `backend/scripts/create_allowed_mappings_table.py`

- `backend/api/services/mapping_obligatoire_service.py` - Service de gestion des mappings autorisés

- Mise à jour `backend/api/routes/mappings.py` - Nouveaux endpoints

- Mise à jour `backend/api/models.py` - Modèles Pydantic

- Mise à jour `backend/database/connection.py` - Chargement automatique au démarrage

**Acceptance Criteria**:

- [x] Table `allowed_mappings` créée en BDD avec structure correcte (incluant champ `is_hardcoded`)

- [x] Script de migration charge correctement les 49 combinaisons uniques depuis `scripts/mappings_obligatoires.xlsx` avec `is_hardcoded = True` (50 lignes dans Excel, 1 doublon détecté)

- [x] Les combinaisons initiales sont protégées (`is_hardcoded = True`) et ne peuvent pas être supprimées

- [x] Fonctions de validation fonctionnent correctement

- [x] Endpoints API retournent les bonnes valeurs filtrées (Step 5.2 complété)

- [x] **Test script exécutable et tous les tests passent**

---

### Step 5.2 : API Backend - Endpoints pour combinaisons autorisées

**Status**: ✅ COMPLÉTÉ  

**Description**: Créer les endpoints API pour gérer les combinaisons autorisées (lecture, filtrage).

**Tasks**:

- [x] Créer Pydantic models dans `backend/api/models.py` :

  - `AllowedMappingBase`, `AllowedMappingCreate`, `AllowedMappingResponse`, `AllowedMappingListResponse`

- [x] Endpoint `GET /api/mappings/allowed-level1` pour récupérer toutes les valeurs level_1 autorisées

- [x] Endpoint `GET /api/mappings/allowed-level2?level_1={value}` pour récupérer les level_2 autorisés pour un level_1

- [x] Endpoint `GET /api/mappings/allowed-level3?level_1={value}&level_2={value}` pour récupérer les level_3 autorisés pour un couple (level_1, level_2)

- [x] Intégrer dans `main.py` (router déjà intégré via mappings.router)

- [x] **Tester les endpoints et la validation**

**Deliverables**:

- Mise à jour `backend/api/models.py` - Modèles Pydantic pour AllowedMapping

- Mise à jour `backend/api/routes/mappings.py` - Nouveaux endpoints (placés avant /mappings/{mapping_id} pour éviter conflits)

- `backend/tests/test_allowed_mappings_endpoints_step5_2.py` - Tests des endpoints

**Acceptance Criteria**:

- [x] Modèles Pydantic créés pour AllowedMapping

- [x] Endpoints API retournent les bonnes valeurs filtrées

- [x] Filtrage par level_1 et level_2 fonctionne

- [x] Validation des paramètres fonctionne (erreur 422 si paramètres manquants)

- [x] **Test script exécutable et tous les tests passent**

- [x] **Endpoints testés avec API démarrée - tous fonctionnent (49 valeurs level_1, filtrage level_2 et level_3 OK)**

---

### Step 5.3 : Backend - Validation des mappings importés

**Status**: ✅ COMPLÉTÉ  

**Description**: Modifier l'endpoint d'import de mappings pour valider les valeurs contre la table `allowed_mappings`. Le bouton "Load mapping" reste exactement le même, seule la validation change.

**Tasks**:

- [x] Modifier `POST /api/mappings/import` dans `backend/api/routes/mappings.py` :

  - **Le workflow reste identique** : détection de colonnes, preview, import

  - Pour chaque ligne du fichier importé, valider que les valeurs level_1, level_2, level_3 sont autorisées

  - Utiliser `validate_mapping()` du service créé en Step 5.1 (validation contre la table `allowed_mappings`)

  - Si une ligne contient des valeurs invalides :

    - Incrémenter `errors_count`

    - Ajouter un message "erreur - mapping inconnu" dans `errors_list`

    - **Ignorer la ligne** (ne pas créer le mapping)

  - Si toutes les valeurs sont valides, créer le mapping comme avant (pas de changement ici)

- [x] Validation de level_3 contre la liste fixe (Passif, Produits, Emprunt, Charges Déductibles, Actif)

- [x] Logger les erreurs de validation dans les logs backend avec "erreur - mapping inconnu"

- [x] **Tester avec un fichier contenant des valeurs valides et invalides**

**Deliverables**:

- Mise à jour `backend/api/routes/mappings.py` - Validation lors de l'import (workflow identique, validation ajoutée)

- Mise à jour `backend/api/models.py` - Modèle de réponse enrichi

**Acceptance Criteria**:

- [x] Le bouton "Load mapping" fonctionne exactement comme avant (même interface, même workflow)

- [x] Les lignes avec valeurs invalides sont ignorées (pas de mapping créé)

- [x] Les erreurs sont loggées avec "erreur - mapping inconnu"

- [x] Les statistiques d'import incluent le nombre d'erreurs

- [x] Les lignes valides sont importées normalement

- [x] Validation de level_3 contre la liste fixe fonctionne

- [x] **Test avec fichier mixte (valides + invalides) validé**

- [x] **Test API : 1 mapping valide importé, 1 mapping invalide rejeté avec message "erreur - mapping inconnu"**

---

### Step 5.3 : Backend - Vérification et test de la mise à jour automatique

**Status**: ✅ COMPLÉTÉ  

**Description**: Vérifier que la mise à jour automatique de toutes les transactions avec le même nom fonctionne correctement (cette fonctionnalité devrait déjà exister).

**Tasks**:

- [x] Vérifier le code actuel de `update_transaction_classification()` dans `backend/api/services/enrichment_service.py`

- [x] Vérifier le code actuel de `create_or_update_mapping_from_classification()`

- [x] Modifier `find_best_mapping()` dans `enrichment_service.py` :

  - **Nouvelle règle** : Si plusieurs mappings correspondent à une transaction (même nom), retourner `None` au lieu du meilleur mapping

  - La transaction ne sera pas mappée et se retrouvera dans l'onglet "Non classées" (unassigned)

  - Cela évite les conflits et force un mapping manuel

- [x] Corriger la mise à jour en cascade dans `backend/api/routes/enrichment.py` :

  - Utiliser correspondance exacte du nom (`Transaction.nom == transaction.nom`) au lieu de `transaction_matches_mapping_name()`

  - Re-enrichir toutes les transactions avec le même nom après mise à jour du mapping

- [x] Tester que quand on modifie le mapping d'une transaction :

  - Toutes les transactions existantes avec le même nom sont mises à jour

  - Le mapping dans la table `mappings` est créé/mis à jour

  - Les futures transactions avec le même nom héritent du mapping

- [x] **Tester la mise à jour en cascade avec plusieurs transactions du même nom**

- [x] **Tester que les transactions avec plusieurs mappings possibles restent non classées**

**Deliverables**:

- Mise à jour `backend/api/services/enrichment_service.py` - Modification de `find_best_mapping()` pour retourner `None` si plusieurs mappings correspondent

- Mise à jour `backend/api/routes/enrichment.py` - Correction de la mise à jour en cascade avec correspondance exacte

- `backend/tests/test_enrichment_cascade_step5_3.py` - Tests de mise à jour en cascade et gestion des conflits

- `backend/tests/test_step5_3_and_5_4_combined.py` - Tests combinés Step 5.3 + Step 5.4

**Acceptance Criteria**:

- [x] Quand on modifie le mapping d'une transaction, toutes les transactions avec le même nom sont mises à jour

- [x] Le mapping dans la table `mappings` est créé/mis à jour

- [x] Les futures transactions avec le même nom héritent automatiquement du mapping

- [x] **Si plusieurs mappings correspondent à une transaction, elle reste non classée (unassigned)**

- [x] **Test avec plusieurs transactions du même nom validé**

- [x] **Test que les transactions avec plusieurs mappings possibles restent non classées**

- [x] **Test combiné Step 5.3 + Step 5.4 validé**

---

### Step 5.4 : API Backend - Validation dans endpoints enrichissement transactions

**Status**: ✅ COMPLÉTÉ  

**Description**: Ajouter la validation obligatoire dans l'endpoint de modification des classifications de transactions.

**Tasks**:

- [x] Modifier `PUT /api/enrichment/transactions/{transaction_id}` :

  - Valider que level_1, level_2, level_3 (si fournis) existent dans les combinaisons autorisées

  - Retourner erreur 400 si combinaison non autorisée

  - Empêcher la création/mise à jour du mapping si combinaison invalide

- [x] Modifier la fonction `create_or_update_mapping_from_classification()` dans `enrichment_service.py` :

  - Valider la combinaison avant de créer/mettre à jour le mapping

  - Ne pas créer le mapping si combinaison invalide

  - Lever ValueError avec message explicite si combinaison invalide

- [x] Ajouter messages d'erreur explicites

- [x] **Tester la validation avec combinaisons valides et invalides**

**Deliverables**:

- Mise à jour `backend/api/routes/enrichment.py` - Validation ajoutée

- Mise à jour `backend/api/services/enrichment_service.py` - Validation dans fonction utilitaire

- `backend/tests/test_enrichment_validation_step5_4.py` - Tests de validation

**Acceptance Criteria**:

- [x] Impossible de modifier une classification avec combinaison non autorisée

- [x] Le mapping n'est pas créé/mis à jour si combinaison invalide

- [x] Messages d'erreur clairs (erreur 400 avec détails)

- [x] Validation de level_3 contre la liste fixe fonctionne

- [x] **Test script exécutable et tous les tests passent**

- [x] **Test API : combinaison valide acceptée, combinaison invalide rejetée avec erreur 400**

---

### Step 5.5 : Frontend - Dropdowns filtrés hiérarchiquement dans l'onglet Transactions

**Status**: ⏳ EN ATTENTE  

**Description**: Modifier l'interface de mapping manuel dans l'onglet Transactions pour utiliser des dropdowns filtrés hiérarchiquement avec filtrage bidirectionnel. **Garder l'option "✏️" (bouton d'édition)** - voir Step 5.9 pour les détails.

**Important** : Chaque level_1 a une combinaison unique level_2/level_3 dans `allowed_mappings`.

---

#### Step 5.5.1 : Backend - Fonctions de filtrage bidirectionnel

**Status**: ⏳ EN ATTENTE

**Description**: Créer les fonctions backend pour le filtrage bidirectionnel (level_3 → level_2, level_2 → level_1, etc.)

**Tasks**:

- [ ] Créer `get_allowed_level2_for_level3(db: Session, level_3: str)` dans `mapping_obligatoire_service.py` : retourne les level_2 qui ont ce level_3 (distinct)

- [ ] Créer `get_allowed_level1_for_level2(db: Session, level_2: str)` dans `mapping_obligatoire_service.py` : retourne les level_1 qui ont ce level_2 (distinct)

- [ ] Créer `get_allowed_level1_for_level2_and_level3(db: Session, level_2: str, level_3: str)` : retourne les level_1 qui ont ce couple (distinct, pour validation)

- [ ] Créer endpoints API correspondants dans `backend/api/routes/mappings.py` :

  - `GET /api/mappings/allowed-level2-for-level3?level_3={value}`

  - `GET /api/mappings/allowed-level1-for-level2?level_2={value}`

  - `GET /api/mappings/allowed-level1-for-level2-and-level3?level_2={value}&level_3={value}`

- [ ] **Tester les endpoints backend**

**Deliverables**:

- Mise à jour `backend/api/services/mapping_obligatoire_service.py` - Nouvelles fonctions de filtrage

- Mise à jour `backend/api/routes/mappings.py` - Nouveaux endpoints

- Tests backend pour les nouveaux endpoints

**Acceptance Criteria**:

- [ ] Les 3 fonctions retournent les bonnes valeurs filtrées

- [ ] Les 3 endpoints API fonctionnent correctement

- [ ] **Tests backend passent**

---

#### Step 5.5.2 : Frontend - API Client pour filtrage bidirectionnel

**Status**: ⏳ EN ATTENTE

**Description**: Ajouter les fonctions dans le client API frontend pour appeler les nouveaux endpoints.

**Tasks**:

- [ ] Ajouter fonctions dans `frontend/src/api/client.ts` pour les 3 nouveaux endpoints :

  - `getAllowedLevel2ForLevel3(level_3: string)`

  - `getAllowedLevel1ForLevel2(level_2: string)`

  - `getAllowedLevel1ForLevel2AndLevel3(level_2: string, level_3: string)`

- [ ] **Tester les appels API depuis le frontend (console.log ou test manuel)**

**Deliverables**:

- Mise à jour `frontend/src/api/client.ts` - Nouvelles fonctions API

**Acceptance Criteria**:

- [ ] Les 3 fonctions sont ajoutées et exportées

- [ ] Les appels API fonctionnent correctement

- [ ] **Test manuel dans console navigateur validé**

---

#### Step 5.5.3 : Frontend - Scénario 1 : Sélection level_1 → level_2 + level_3 automatiques

**Status**: ⏳ EN ATTENTE

**Description**: Implémenter le scénario où level_1 est sélectionné en premier, level_2 et level_3 sont automatiquement sélectionnés.

**Tasks**:

- [ ] Modifier `TransactionsTable.tsx` :

  - Charger les valeurs level_1 depuis `GET /api/mappings/allowed-level1` au montage

  - Remplacer l'input texte level_1 par un dropdown avec les valeurs autorisées

  - Quand level_1 est sélectionné :

    - Trouver la combinaison unique (level_2, level_3) pour ce level_1

    - Pré-remplir automatiquement level_2 et level_3

    - Les dropdowns level_2 et level_3 restent disponibles mais pré-remplis

  - Ajouter option "Unassigned" dans le dropdown level_1

- [ ] **Tester le scénario 1 dans le navigateur**

**Deliverables**:

- Mise à jour `frontend/src/components/TransactionsTable.tsx` - Scénario 1 implémenté

**Acceptance Criteria**:

- [ ] Dropdown level_1 affiche les valeurs autorisées

- [ ] Sélection level_1 → level_2 et level_3 sont automatiquement sélectionnés

- [ ] Option "Unassigned" permet de retirer le mapping

- [ ] **Test visuel dans navigateur validé**

---

#### Step 5.5.4 : Frontend - Scénario 2 : Sélection level_2 → level_3 automatique, level_1 manuel

**Status**: ⏳ EN ATTENTE

**Description**: Implémenter le scénario où level_2 est sélectionné en premier, level_3 est automatiquement sélectionné, level_1 doit être sélectionné manuellement.

**Tasks**:

- [ ] Modifier `TransactionsTable.tsx` :

  - Quand level_2 est sélectionné (sans level_1) :

    - Trouver la combinaison unique level_3 pour ce level_2

    - Pré-remplir automatiquement level_3

    - Charger les level_1 autorisés pour ce level_2 (appel à `getAllowedLevel1ForLevel2`)

    - Afficher ces level_1 dans le dropdown level_1

  - Ajouter option "Unassigned" dans le dropdown level_2

- [ ] **Tester le scénario 2 dans le navigateur**

**Deliverables**:

- Mise à jour `frontend/src/components/TransactionsTable.tsx` - Scénario 2 implémenté

**Acceptance Criteria**:

- [ ] Sélection level_2 → level_3 est automatiquement sélectionné

- [ ] Dropdown level_1 affiche les level_1 autorisés pour ce level_2

- [ ] Option "Unassigned" permet de retirer le mapping

- [ ] **Test visuel dans navigateur validé**

---

#### Step 5.5.5 : Frontend - Scénario 3 : Sélection level_3 → level_2 + level_1 manuels

**Status**: ⏳ EN ATTENTE

**Description**: Implémenter le scénario où level_3 est sélectionné en premier, level_2 et level_1 doivent être sélectionnés manuellement.

**Tasks**:

- [ ] Modifier `TransactionsTable.tsx` :

  - Quand level_3 est sélectionné (sans level_1 ni level_2) :

    - Charger les level_2 autorisés pour ce level_3 (appel à `getAllowedLevel2ForLevel3`)

    - Afficher ces level_2 dans le dropdown level_2

    - Quand level_2 est sélectionné après level_3 :

      - Charger les level_1 autorisés pour le couple (level_2, level_3) (appel à `getAllowedLevel1ForLevel2AndLevel3`)

      - Afficher ces level_1 dans le dropdown level_1

  - Ajouter option "Unassigned" dans le dropdown level_3

- [ ] **Tester le scénario 3 dans le navigateur**

**Deliverables**:

- Mise à jour `frontend/src/components/TransactionsTable.tsx` - Scénario 3 implémenté

**Acceptance Criteria**:

- [ ] Sélection level_3 → dropdown level_2 affiche les level_2 autorisés

- [ ] Sélection level_2 (après level_3) → dropdown level_1 affiche les level_1 autorisés pour le couple

- [ ] Option "Unassigned" permet de retirer le mapping

- [ ] **Test visuel dans navigateur validé**

---

#### Step 5.5.6 : Frontend - Règles de changement et suppression des inputs texte

**Status**: ⏳ EN ATTENTE

**Description**: Implémenter les règles de changement et supprimer complètement les inputs texte (mode custom).

**Tasks**:

- [ ] Modifier `TransactionsTable.tsx` :

  - **Règle 1** : Changer level_1 → level_2 et level_3 changent automatiquement (nouvelle combinaison unique)

  - **Règle 2** : Changer level_2 → level_3 change automatiquement, level_1 reste tel quel

  - **Règle 3** : Changer level_3 → level_2 et level_1 restent tels quels (pas de réinitialisation)

  - **Supprimer complètement** les inputs texte (mode custom) pour level_1, level_2, level_3

  - Supprimer les états `customLevel1`, `customLevel2`, `customLevel3`

  - Supprimer l'option "➕ Nouveau..." des dropdowns

- [ ] **Tester toutes les règles de changement dans le navigateur**

**Deliverables**:

- Mise à jour `frontend/src/components/TransactionsTable.tsx` - Règles de changement implémentées

**Acceptance Criteria**:

- [ ] Les 3 règles de changement fonctionnent correctement

- [ ] Les inputs texte sont complètement supprimés (plus de mode custom)

- [ ] Les dropdowns ne permettent que la sélection de valeurs autorisées

- [ ] **Test visuel dans navigateur validé**

---

#### Step 5.5.7 : Frontend - Tests finaux et validation complète

**Status**: ⏳ EN ATTENTE

**Description**: Tests finaux de tous les scénarios et validation que tout fonctionne ensemble.

**Tasks**:

- [ ] Tester tous les scénarios dans le navigateur :

  - Scénario 1 : level_1 → level_2 + level_3 automatiques

  - Scénario 2 : level_2 → level_3 automatique, level_1 manuel

  - Scénario 3 : level_3 → level_2 + level_1 manuels

  - Règles de changement : changer level_1, level_2, level_3

  - Option "Unassigned" dans chaque dropdown

  - Mise à jour en cascade (toutes les transactions avec le même nom sont mises à jour)

- [ ] Vérifier que le bouton "✏️" est conservé (fonctionnalité détaillée dans Step 5.9)

- [ ] **Test complet de bout en bout validé**

**Deliverables**:

- Tests manuels complets dans le navigateur

**Acceptance Criteria**:

- [ ] Tous les scénarios fonctionnent correctement

- [ ] Toutes les règles de changement fonctionnent

- [ ] Option "Unassigned" fonctionne dans tous les dropdowns

- [ ] Mise à jour en cascade fonctionne

- [ ] Bouton "✏️" conservé

- [ ] **Test visuel complet dans navigateur validé par l'utilisateur**

---

**Step 5.5 - Acceptance Criteria globaux**:

- [ ] Dropdowns remplacent les inputs texte (level_1, level_2, level_3 ne sont plus éditables en texte libre)

- [ ] **Filtrage bidirectionnel fonctionne** :

  - Sélection level_1 → level_2 et level_3 sélectionnés automatiquement

  - Sélection level_2 → level_3 sélectionné automatiquement, level_1 disponible

  - Sélection level_3 → level_2 et level_1 disponibles

- [ ] Les règles de changement fonctionnent correctement

- [ ] Option "Unassigned" permet de retirer le mapping

- [ ] Bouton "✏️" conservé (fonctionnalité détaillée dans Step 5.9)

- [ ] Mise à jour en cascade fonctionne (toutes les transactions avec le même nom sont mises à jour)

- [ ] **Test visuel complet dans navigateur validé**

---

### Step 5.6 : Frontend - Dropdowns filtrés dans l'onglet Mapping

**Status**: ⏳ EN ATTENTE  

**Description**: Modifier l'onglet Mapping pour utiliser des dropdowns filtrés au lieu d'inputs texte libres.

**Tasks**:

- [ ] Identifier l'onglet/composant Mapping dans le frontend

- [ ] Remplacer les inputs texte level_1, level_2, level_3 par des dropdowns

- [ ] Implémenter le même filtrage hiérarchique que Step 5.5

- [ ] Charger les valeurs prédéfinies depuis l'API

- [ ] Permettre la modification des mappings existants (avec validation)

- [ ] Permettre la suppression des mappings (comme actuellement)

- [ ] **Tester la modification et suppression de mappings**

**Deliverables**:

- Mise à jour du composant Mapping frontend - Dropdowns filtrés

**Acceptance Criteria**:

- [ ] Les inputs texte sont remplacés par des dropdowns

- [ ] Filtrage hiérarchique fonctionne

- [ ] Modification de mapping fonctionne avec validation

- [ ] Suppression de mapping fonctionne (transactions retournent à "unassigned")

- [ ] **Test visuel dans navigateur validé**

---

### Step 5.7 : Backend - Vérification et test du recalcul automatique

**Status**: ⏳ EN ATTENTE  

**Description**: Vérifier que le recalcul automatique des modules dépendants fonctionne correctement après une mise à jour de mapping (cette fonctionnalité devrait déjà exister).

**Tasks**:

- [ ] Vérifier le code actuel de `update_transaction_classification()` dans `backend/api/services/enrichment_service.py`

- [ ] Vérifier que l'invalidation des données calculées est déclenchée :

  - `CompteResultatData` (via fonction existante)

  - `AmortizationResult` (via fonction existante)

  - Tous les autres modules qui dépendent des transactions enrichies

- [ ] Tester que le recalcul est déclenché automatiquement après mise à jour de mapping

- [ ] Si la fonctionnalité n'existe pas ou ne fonctionne pas correctement, l'implémenter/corriger

- [ ] **Tester le recalcul automatique**

**Deliverables**:

- Vérification/correction de `backend/api/services/enrichment_service.py` si nécessaire

- Script de test pour valider le recalcul automatique

**Acceptance Criteria**:

- [ ] Après mise à jour de mapping, les données calculées sont invalidées

- [ ] Le recalcul est déclenché automatiquement

- [ ] Tous les modules dépendants sont mis à jour (compte de résultat, amortissements, etc.)

- [ ] **Test de recalcul automatique validé**

---

### Step 5.8 : Frontend - Gestion de la table allowed_mappings

**Status**: ⏳ EN ATTENTE  

**Description**: Créer un sous-onglet dans l'onglet Mapping pour gérer la table `allowed_mappings` (combinaisons autorisées de level_1/level_2/level_3).

**Structure**:

- L'onglet Mapping aura 2 sous-onglets :

  - **"Mappings existants"** : Contenu actuel de `MappingTable.tsx` (liste, création, modification, suppression des mappings de transactions)

  - **"Mappings autorisés"** : Nouveau composant pour gérer la table `allowed_mappings`

**Tasks**:

- [ ] Modifier `frontend/app/dashboard/transactions/page.tsx` pour ajouter des sous-onglets dans l'onglet Mapping

- [ ] Créer composant `AllowedMappingsTable.tsx` pour gérer les mappings autorisés :

  - Tableau pour visualiser tous les mappings autorisés (level_1, level_2, level_3)
    - Afficher une colonne "Type" indiquant "Hard codé" ou "Ajouté manuellement"
    - Les lignes hard codées doivent être visuellement distinctes (ex: fond gris)

  - Bouton "+ Ajouter" pour créer une nouvelle combinaison

  - Modal de création avec dropdowns filtrés hiérarchiquement (même logique que Step 5.5 et 5.6)

  - **Permettre de créer une nouvelle combinaison** (level_1, level_2, level_3) qui n'existe pas encore dans `allowed_mappings`

  - **Validation** : 
    - Vérifier que la combinaison n'existe pas déjà (contrainte unique)
    - **Level_3 doit être dans la liste fixe** : Passif, Produits, Emprunt, Charges Déductibles, Actif

  - Bouton de suppression avec confirmation pour chaque ligne :
    - **Désactiver le bouton de suppression** pour les combinaisons hard codées (`is_hardcoded = True`)
    - Seulement les combinaisons ajoutées manuellement peuvent être supprimées

  - Pagination et filtres

- [ ] Ajouter fonctions API dans `frontend/src/api/client.ts` pour les endpoints CRUD

- [ ] **Bouton "Reset mappings autorisés par défaut"** :

  - Endpoint backend `POST /api/mappings/allowed/reset` qui :

    - **Supprime uniquement les combinaisons ajoutées manuellement** (`is_hardcoded = False`)

    - **Garde les 50 combinaisons initiales** (`is_hardcoded = True`) - elles ne peuvent jamais être supprimées

    - **Supprime tous les `mappings` invalides** (combinaisons qui ne sont plus dans `allowed_mappings`)

    - **Marque les transactions associées comme "non assignées"** (supprime leurs `EnrichedTransaction`)

    - **Invalide les données calculées** (`CompteResultatData`, `AmortizationResult`)

  - **Note** : Le fichier Excel n'est plus nécessaire après le chargement initial, le reset ne recharge pas depuis le fichier

- [ ] **Tester l'affichage et le reset des mappings autorisés**

**Deliverables**:

- Mise à jour `frontend/app/dashboard/transactions/page.tsx` - Sous-onglets dans Mapping

- Nouveau composant `frontend/src/components/AllowedMappingsTable.tsx` - Gestion des mappings autorisés

- Endpoints backend CRUD pour la table `allowed_mappings` :

  - `GET /api/mappings/allowed` - Liste tous les mappings autorisés

  - `POST /api/mappings/allowed` - Ajouter un nouveau mapping autorisé :
    - Validation : combinaison unique (contrainte unique sur level_1, level_2, level_3)
    - Validation : level_3 doit être dans la liste fixe (Passif, Produits, Emprunt, Charges Déductibles, Actif)

  - `DELETE /api/mappings/allowed/{id}` - Supprimer un mapping autorisé :
    - **Vérification** : ne peut pas supprimer si `is_hardcoded = True` (erreur 403)
    - Seulement les combinaisons ajoutées manuellement peuvent être supprimées

  - `POST /api/mappings/allowed/reset` - Reset : supprime uniquement les combinaisons ajoutées manuellement :
    - Supprime toutes les combinaisons où `is_hardcoded = False`
    - **Garde les 50 combinaisons initiales** (`is_hardcoded = True`)
    - Supprime tous les `mappings` invalides (combinaisons qui ne sont plus dans `allowed_mappings`)
    - Marque les transactions associées comme "non assignées" (supprime leurs `EnrichedTransaction`)
    - Invalide les données calculées (`CompteResultatData`, `AmortizationResult`)
    - **Note** : Le fichier Excel n'est plus nécessaire après le chargement initial, le reset ne recharge pas depuis le fichier

**Acceptance Criteria**:

- [ ] Sous-onglets fonctionnent dans l'onglet Mapping

- [ ] Interface pour visualiser les mappings autorisés (tableau)

- [ ] Interface pour ajouter de nouvelles combinaisons (level_1, level_2, level_3) avec dropdowns filtrés

- [ ] **Permettre de créer de nouvelles combinaisons** qui n'existent pas encore dans `allowed_mappings`

- [ ] Validation lors de l'ajout :
  - Combinaison unique (contrainte unique sur level_1, level_2, level_3)
  - Level_3 doit être dans la liste fixe : Passif, Produits, Emprunt, Charges Déductibles, Actif
  - Messages d'erreur clairs si validation échoue

- [ ] Validation de la hiérarchie (même logique que Step 5.5 et 5.6)

- [ ] Suppression de mappings autorisés fonctionne (avec confirmation) :
  - **Impossible de supprimer les combinaisons hard codées** (bouton désactivé)
  - Seulement les combinaisons ajoutées manuellement peuvent être supprimées

- [ ] **Bouton "Reset mappings autorisés par défaut" fonctionne** :
  - Supprime uniquement les combinaisons ajoutées manuellement
  - Garde les 50 combinaisons initiales (protégées)

- [ ] **Reset supprime les mappings invalides et réinitialise les transactions associées**

- [ ] **Test visuel dans navigateur validé**

---

### Step 5.9 : Frontend - Fonctionnalité du bouton "✏️" dans l'onglet Transactions

**Status**: ⏳ EN ATTENTE  

**Description**: Le bouton "✏️" édite uniquement les champs `date`, `nom`, `quantite` (pas les classifications). Les classifications (level_1, level_2, level_3) sont déjà éditables via les dropdowns filtrés en cliquant directement sur les valeurs (implémenté dans Step 5.4).

**Tasks**:

- [ ] **Fonctionnalité confirmée** : Le bouton "✏️" édite les champs transaction (date, nom, quantite)

- [ ] **Édition des classifications** : Déjà implémentée dans Step 5.5 via clic sur les valeurs level_1/level_2/level_3

- [ ] Validation contre `allowed_mappings` respectée (déjà implémentée dans Step 5.4)

- [ ] Mise à jour en cascade fonctionne (déjà implémentée dans Step 5.3)

- [ ] **Test visuel dans navigateur validé**

**Deliverables**:

- Aucune modification nécessaire - fonctionnalité déjà en place

**Acceptance Criteria**:

- [ ] Fonctionnalité du bouton "✏️" définie : édite date, nom, quantite

- [ ] Édition des classifications via clic sur les valeurs avec dropdowns filtrés (Step 5.5)

- [ ] Validation contre `allowed_mappings` respectée

- [ ] Mise à jour en cascade fonctionne (toutes les transactions avec le même nom sont mises à jour)

- [ ] **Test visuel dans navigateur validé**

---

**Phase 5 - Acceptance Criteria globaux**:

- [ ] Table `allowed_mappings` créée en BDD et peuplée avec les 50 combinaisons depuis `scripts/mappings_obligatoires.xlsx`

- [ ] Tous les mappings (importés ou manuels) sont validés contre la table `allowed_mappings`

- [ ] Les lignes invalides sont ignorées avec message "erreur - mapping inconnu"

- [ ] Le bouton "Load mapping" fonctionne exactement comme avant (même interface, même workflow)

- [ ] Dropdowns filtrés hiérarchiquement dans l'onglet Transactions (level_1, level_2, level_3 ne sont plus éditables en texte libre)

- [ ] Dropdowns filtrés hiérarchiquement dans l'onglet Mapping

- [ ] Bouton "✏️" conservé avec fonctionnalité définie (Step 5.8)

- [ ] Mise à jour en cascade : toutes les transactions avec le même nom sont mises à jour (vérifiée et testée)

- [ ] Recalcul automatique des modules dépendants (vérifié et testé)

- [ ] **Test complet de bout en bout validé**

- [ ] **Utilisateur confirme que le nouveau système fonctionne correctement**

---

## Notes importantes

1. **Fichier source** : `scripts/mappings_obligatoires.xlsx` est utilisé **une seule fois** pour hard coder les 50 combinaisons initiales dans la table `allowed_mappings`
2. **Après chargement initial** : Le fichier Excel peut être supprimé, il n'est plus nécessaire
3. **Protection des valeurs hard codées** : Les 50 combinaisons initiales (`is_hardcoded = True`) sont **protégées** et ne peuvent **jamais être supprimées**
4. **Nouvelles combinaisons** : Peuvent être ajoutées via l'interface (`is_hardcoded = False`) et peuvent être supprimées
5. **Reset** : Le bouton "Reset mappings autorisés par défaut" supprime uniquement les combinaisons ajoutées manuellement, garde les 50 initiales
6. **Validation stricte** : Toutes les combinaisons (hard codées ou ajoutées) doivent respecter la validation (level_3 dans la liste fixe)
7. **Filtrage bidirectionnel** : Le système supporte la sélection dans n'importe quel ordre (level_1, level_2, ou level_3 en premier)
8. **Transactions avec plusieurs mappings** : Si une transaction correspond à plusieurs mappings, elle reste non classée (unassigned)

