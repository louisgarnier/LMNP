# Plan d'Implémentation - Phase 10 : Extraction de données (Mappings et Transactions)

**Status**: ⏳ À FAIRE  
**Dernière mise à jour**: 2025-01-27

## Vue d'ensemble

**Objectif** : Ajouter des fonctionnalités d'extraction/export de données pour les mappings et les transactions, permettant aux utilisateurs de télécharger leurs données au format Excel ou CSV.

**Fonctionnalités principales** :
- Bouton "Extraire" dans l'onglet Mapping pour exporter les mappings
- Bouton "Extraire" dans l'onglet Transactions pour exporter les transactions
- Support des formats Excel (.xlsx) et CSV (.csv)
- Filtres appliqués respectés lors de l'extraction (si applicable)

---

## Step 10.1 : Backend - Endpoint d'extraction des mappings

**Status**: ✅ COMPLETED  
**Description**: Créer un endpoint backend pour exporter les mappings au format Excel ou CSV.

**Tasks**:
- [x] Créer un endpoint `GET /api/mappings/export` dans `backend/api/routes/mappings.py`
- [x] Paramètres de l'endpoint :
  - `format` (query param) : "excel" ou "csv" (défaut: "excel")
  - Optionnel : filtres (si nécessaire pour l'extraction filtrée)
- [x] Générer le fichier :
  - **Format Excel** : Utiliser `pandas` ou `openpyxl` pour créer un fichier .xlsx
  - **Format CSV** : Utiliser `pandas` ou générer directement un CSV
- [x] Colonnes à inclure :
  - `id`
  - `nom`
  - `level_1`
  - `level_2`
  - `level_3`
  - `is_prefix_match`
  - `priority`
  - `created_at`
  - `updated_at`
- [x] Retourner le fichier avec les headers appropriés :
  - `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (Excel)
  - `Content-Type: text/csv; charset=utf-8` (CSV)
  - `Content-Disposition: attachment; filename="mappings_YYYY-MM-DD.xlsx"`

**Deliverables**:
- Endpoint `GET /api/mappings/export` dans `backend/api/routes/mappings.py`
- Support Excel et CSV
- Génération de fichier avec nom de fichier daté
- Script de test : `backend/scripts/test_mappings_export_step10_1.py`

**Acceptance Criteria**:
- [x] Endpoint accessible et fonctionnel
- [x] Fichier Excel généré correctement avec toutes les colonnes
- [x] Fichier CSV généré correctement avec toutes les colonnes
- [x] Nom de fichier contient la date d'export
- [x] Headers HTTP corrects pour le téléchargement
- [x] Intégrité des données vérifiée (tous les mappings exportés)

---

## Step 10.2 : Backend - Endpoint d'extraction des transactions

**Status**: ✅ COMPLETED  
**Description**: Créer un endpoint backend pour exporter les transactions au format Excel ou CSV.

**Tasks**:
- [x] Créer un endpoint `GET /api/transactions/export` dans `backend/api/routes/transactions.py`
- [x] Paramètres de l'endpoint :
  - `format` (query param) : "excel" ou "csv" (défaut: "excel")
  - Optionnel : mêmes filtres que `GET /api/transactions` (start_date, end_date, filter_level_1, etc.)
- [x] Générer le fichier :
  - **Format Excel** : Utiliser `pandas` ou `openpyxl` pour créer un fichier .xlsx
  - **Format CSV** : Utiliser `pandas` ou générer directement un CSV
- [x] Colonnes à inclure :
  - `id`
  - `date`
  - `quantite`
  - `nom`
  - `solde`
  - `level_1` (depuis EnrichedTransaction)
  - `level_2` (depuis EnrichedTransaction)
  - `level_3` (depuis EnrichedTransaction)
  - `source_file`
  - `created_at`
  - `updated_at`
- [x] Retourner le fichier avec les headers appropriés :
  - `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (Excel)
  - `Content-Type: text/csv; charset=utf-8` (CSV)
  - `Content-Disposition: attachment; filename="transactions_YYYY-MM-DD.xlsx"`

**Deliverables**:
- Endpoint `GET /api/transactions/export` dans `backend/api/routes/transactions.py`
- Support Excel et CSV
- Support des filtres (start_date, end_date, filter_level_1, filter_level_2, filter_level_3, filter_nom)
- Génération de fichier avec nom de fichier daté
- Script de test : `backend/scripts/test_transactions_export_step10_2.py`

**Acceptance Criteria**:
- [x] Endpoint accessible et fonctionnel
- [x] Fichier Excel généré correctement avec toutes les colonnes
- [x] Fichier CSV généré correctement avec toutes les colonnes
- [x] Filtres appliqués correctement (si fournis)
- [x] Nom de fichier contient la date d'export
- [x] Headers HTTP corrects pour le téléchargement
- [x] Intégrité des données vérifiée (toutes les transactions exportées)

---

## Step 10.3 : Frontend - Bouton "Extraire" dans l'onglet Mapping

**Status**: ✅ COMPLETED  
**Description**: Ajouter un bouton "Extraire" dans l'onglet Mapping pour télécharger les mappings.

**Tasks**:
- [x] Modifier `frontend/app/dashboard/transactions/page.tsx` ou `frontend/src/components/MappingTable.tsx`
- [x] Ajouter un bouton "Extraire" dans l'interface de l'onglet Mapping
- [x] Position du bouton :
  - Option B : Dans le composant `MappingTable.tsx` en haut du tableau (implémenté dans la page, juste au-dessus du MappingTable)
- [x] Fonctionnalité du bouton :
  - Deux boutons séparés : "Extraire (Excel)" et "Extraire (CSV)"
- [x] Implémenter la fonction d'extraction :
  - Appeler l'API `GET /api/mappings/export?format=excel` ou `?format=csv`
  - Gérer le téléchargement du fichier
  - Afficher un message de confirmation ou un loader pendant le téléchargement
- [x] Gestion des erreurs :
  - Afficher un message d'erreur si l'extraction échoue
  - Logger l'erreur dans la console

**Deliverables**:
- Bouton "Extraire" dans l'onglet Mapping (deux boutons : Excel et CSV)
- Fonctionnalité de téléchargement Excel et CSV
- Gestion des erreurs
- Fonction `mappingsAPI.export()` ajoutée dans `frontend/src/api/client.ts`

**Acceptance Criteria**:
- [x] Bouton visible et accessible dans l'onglet Mapping (sous-onglet "Mappings existants")
- [x] Choix du format (Excel ou CSV) fonctionne (deux boutons séparés)
- [x] Téléchargement du fichier fonctionne correctement
- [x] Nom du fichier téléchargé est correct (`mappings_YYYY-MM-DD.xlsx` ou `.csv`)
- [x] Gestion des erreurs appropriée (affichage d'un message d'erreur en cas d'échec)

---

## Step 10.4 : Frontend - Bouton "Extraire" dans l'onglet Transactions

**Status**: ✅ COMPLETED  
**Description**: Ajouter un bouton "Extraire" dans l'onglet Transactions pour télécharger les transactions.

**Tasks**:
- [x] Modifier `frontend/app/dashboard/transactions/page.tsx` ou `frontend/src/components/TransactionsTable.tsx`
- [x] Ajouter un bouton "Extraire" dans l'interface de l'onglet Transactions
- [x] Position du bouton :
  - Option B : Dans le composant `TransactionsTable.tsx` en haut du tableau (juste au-dessus des statistiques)
- [x] Fonctionnalité du bouton :
  - Deux boutons séparés : "Extraire (Excel)" et "Extraire (CSV)"
  - Support des filtres actuels du tableau (date, level_1, level_2, level_3, nom)
- [x] Implémenter la fonction d'extraction :
  - Appeler l'API `GET /api/transactions/export?format=excel` ou `?format=csv`
  - Passer les paramètres de filtres à l'API (start_date, end_date, filter_level_1, filter_level_2, filter_level_3, filter_nom)
  - Gérer le téléchargement du fichier
  - Afficher un loader pendant le téléchargement
- [x] Gestion des erreurs :
  - Afficher un message d'erreur si l'extraction échoue
  - Logger l'erreur dans la console

**Deliverables**:
- Bouton "Extraire" dans l'onglet Transactions (deux boutons : Excel et CSV)
- Fonctionnalité de téléchargement Excel et CSV
- Support des filtres (date, level_1, level_2, level_3, nom)
- Gestion des erreurs
- Fonction `transactionsAPI.export()` ajoutée dans `frontend/src/api/client.ts`

**Acceptance Criteria**:
- [x] Bouton visible et accessible dans l'onglet Transactions
- [x] Choix du format (Excel ou CSV) fonctionne (deux boutons séparés)
- [x] Téléchargement du fichier fonctionne correctement
- [x] Nom du fichier téléchargé est correct (`transactions_YYYY-MM-DD.xlsx` ou `.csv`)
- [x] Filtres appliqués correctement (date, level_1, level_2, level_3, nom)
- [x] Gestion des erreurs appropriée (affichage d'un message d'erreur en cas d'échec)

---

## Notes techniques

### Bibliothèques recommandées

**Backend (Python)** :
- `pandas` : Pour créer les DataFrames et exporter en Excel/CSV
- `openpyxl` : Alternative pour Excel (si pandas n'est pas disponible)
- `fastapi.responses` : Pour retourner les fichiers avec les bons headers

**Frontend (TypeScript/React)** :
- Utiliser `fetch` pour appeler l'API
- Créer un blob à partir de la réponse et déclencher le téléchargement
- Exemple :
  ```typescript
  const response = await fetch(`/api/mappings/export?format=excel`);
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'mappings.xlsx';
  a.click();
  ```

### Format des fichiers

**Excel (.xlsx)** :
- Première ligne : En-têtes des colonnes
- Formatage optionnel : Largeur des colonnes, styles, etc.

**CSV (.csv)** :
- Séparateur : virgule (`,`)
- Encodage : UTF-8 avec BOM (pour Excel) ou UTF-8
- Première ligne : En-têtes des colonnes

### Nommage des fichiers

- Format : `{type}_{date}.{extension}`
- Exemples :
  - `mappings_2025-01-27.xlsx`
  - `transactions_2025-01-27.csv`
- Date : Date du jour de l'export (format YYYY-MM-DD)

---

## Légende Status

- ⏳ À FAIRE - Pas encore commencé
- ⏸️ EN ATTENTE - En attente de validation
- 🔄 EN COURS - En cours d'implémentation
- ✅ COMPLETED - Terminé et validé par l'utilisateur
