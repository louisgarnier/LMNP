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

**Status**: ⏳ À FAIRE  
**Description**: Créer un endpoint backend pour exporter les mappings au format Excel ou CSV.

**Tasks**:
- [ ] Créer un endpoint `GET /api/mappings/export` dans `backend/api/routes/mappings.py`
- [ ] Paramètres de l'endpoint :
  - `format` (query param) : "excel" ou "csv" (défaut: "excel")
  - Optionnel : filtres (si nécessaire pour l'extraction filtrée)
- [ ] Générer le fichier :
  - **Format Excel** : Utiliser `pandas` ou `openpyxl` pour créer un fichier .xlsx
  - **Format CSV** : Utiliser `pandas` ou générer directement un CSV
- [ ] Colonnes à inclure :
  - `id`
  - `level_1`
  - `level_2`
  - `level_3`
  - `created_at`
  - `updated_at`
- [ ] Retourner le fichier avec les headers appropriés :
  - `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (Excel)
  - `Content-Type: text/csv` (CSV)
  - `Content-Disposition: attachment; filename="mappings_YYYY-MM-DD.xlsx"`

**Deliverables**:
- Endpoint `GET /api/mappings/export` dans `backend/api/routes/mappings.py`
- Support Excel et CSV
- Génération de fichier avec nom de fichier daté

**Acceptance Criteria**:
- [ ] Endpoint accessible et fonctionnel
- [ ] Fichier Excel généré correctement avec toutes les colonnes
- [ ] Fichier CSV généré correctement avec toutes les colonnes
- [ ] Nom de fichier contient la date d'export
- [ ] Headers HTTP corrects pour le téléchargement

---

## Step 10.2 : Backend - Endpoint d'extraction des transactions

**Status**: ⏳ À FAIRE  
**Description**: Créer un endpoint backend pour exporter les transactions au format Excel ou CSV.

**Tasks**:
- [ ] Créer un endpoint `GET /api/transactions/export` dans `backend/api/routes/transactions.py`
- [ ] Paramètres de l'endpoint :
  - `format` (query param) : "excel" ou "csv" (défaut: "excel")
  - Optionnel : mêmes filtres que `GET /api/transactions` (start_date, end_date, filter_level_1, etc.)
- [ ] Générer le fichier :
  - **Format Excel** : Utiliser `pandas` ou `openpyxl` pour créer un fichier .xlsx
  - **Format CSV** : Utiliser `pandas` ou générer directement un CSV
- [ ] Colonnes à inclure :
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
- [ ] Retourner le fichier avec les headers appropriés :
  - `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (Excel)
  - `Content-Type: text/csv` (CSV)
  - `Content-Disposition: attachment; filename="transactions_YYYY-MM-DD.xlsx"`

**Deliverables**:
- Endpoint `GET /api/transactions/export` dans `backend/api/routes/transactions.py`
- Support Excel et CSV
- Support des filtres (optionnel)
- Génération de fichier avec nom de fichier daté

**Acceptance Criteria**:
- [ ] Endpoint accessible et fonctionnel
- [ ] Fichier Excel généré correctement avec toutes les colonnes
- [ ] Fichier CSV généré correctement avec toutes les colonnes
- [ ] Filtres appliqués correctement (si fournis)
- [ ] Nom de fichier contient la date d'export
- [ ] Headers HTTP corrects pour le téléchargement

---

## Step 10.3 : Frontend - Bouton "Extraire" dans l'onglet Mapping

**Status**: ⏳ À FAIRE  
**Description**: Ajouter un bouton "Extraire" dans l'onglet Mapping pour télécharger les mappings.

**Tasks**:
- [ ] Modifier `frontend/app/dashboard/transactions/page.tsx` ou `frontend/src/components/MappingTable.tsx`
- [ ] Ajouter un bouton "Extraire" dans l'interface de l'onglet Mapping
- [ ] Position du bouton :
  - Option A : À côté du titre "Mapping" ou dans la barre d'outils
  - Option B : Dans le composant `MappingTable.tsx` en haut du tableau
- [ ] Fonctionnalité du bouton :
  - Ouvrir un menu/dropdown pour choisir le format (Excel ou CSV)
  - Ou deux boutons séparés : "Extraire (Excel)" et "Extraire (CSV)"
- [ ] Implémenter la fonction d'extraction :
  - Appeler l'API `GET /api/mappings/export?format=excel` ou `?format=csv`
  - Gérer le téléchargement du fichier
  - Afficher un message de confirmation ou un loader pendant le téléchargement
- [ ] Gestion des erreurs :
  - Afficher un message d'erreur si l'extraction échoue
  - Logger l'erreur dans la console

**Deliverables**:
- Bouton "Extraire" dans l'onglet Mapping
- Fonctionnalité de téléchargement Excel et CSV
- Gestion des erreurs

**Acceptance Criteria**:
- [ ] Bouton visible et accessible dans l'onglet Mapping
- [ ] Choix du format (Excel ou CSV) fonctionne
- [ ] Téléchargement du fichier fonctionne correctement
- [ ] Nom du fichier téléchargé est correct
- [ ] Gestion des erreurs appropriée

---

## Step 10.4 : Frontend - Bouton "Extraire" dans l'onglet Transactions

**Status**: ⏳ À FAIRE  
**Description**: Ajouter un bouton "Extraire" dans l'onglet Transactions pour télécharger les transactions.

**Tasks**:
- [ ] Modifier `frontend/app/dashboard/transactions/page.tsx` ou `frontend/src/components/TransactionsTable.tsx`
- [ ] Ajouter un bouton "Extraire" dans l'interface de l'onglet Transactions
- [ ] Position du bouton :
  - Option A : À côté du titre "Toutes les transactions" ou dans la barre d'outils
  - Option B : Dans le composant `TransactionsTable.tsx` en haut du tableau
- [ ] Fonctionnalité du bouton :
  - Ouvrir un menu/dropdown pour choisir le format (Excel ou CSV)
  - Ou deux boutons séparés : "Extraire (Excel)" et "Extraire (CSV)"
  - Optionnel : Permettre d'appliquer les filtres actuels du tableau à l'extraction
- [ ] Implémenter la fonction d'extraction :
  - Appeler l'API `GET /api/transactions/export?format=excel` ou `?format=csv`
  - Si filtres appliqués : passer les paramètres de filtres à l'API
  - Gérer le téléchargement du fichier
  - Afficher un message de confirmation ou un loader pendant le téléchargement
- [ ] Gestion des erreurs :
  - Afficher un message d'erreur si l'extraction échoue
  - Logger l'erreur dans la console

**Deliverables**:
- Bouton "Extraire" dans l'onglet Transactions
- Fonctionnalité de téléchargement Excel et CSV
- Support des filtres (optionnel)
- Gestion des erreurs

**Acceptance Criteria**:
- [ ] Bouton visible et accessible dans l'onglet Transactions
- [ ] Choix du format (Excel ou CSV) fonctionne
- [ ] Téléchargement du fichier fonctionne correctement
- [ ] Nom du fichier téléchargé est correct
- [ ] Filtres appliqués correctement (si implémenté)
- [ ] Gestion des erreurs appropriée

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
