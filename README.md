# Application LMNP - Gestion Comptable

Application web pour la gestion comptable LMNP (Location Meublée Non Professionnelle).

⚠️ **IMPORTANT: Avant toute modification, lire `docs/workflow/BEST_PRACTICES.md`**

---

## 📖 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture globale](#architecture-globale)
3. [Comment tout fonctionne ensemble](#comment-tout-fonctionne-ensemble)
4. [Structure détaillée du projet](#structure-détaillée-du-projet)
5. [Flux de données](#flux-de-données)
6. [Démarrage rapide](#démarrage-rapide)

---

## 🎯 Vue d'ensemble

Cette application permet de :
- **Importer** des transactions bancaires depuis des fichiers CSV
- **Visualiser** toutes les transactions dans un tableau
- **Modifier** ou **supprimer** des transactions
- **Calculer automatiquement** les soldes bancaires
- **Suivre l'historique** des imports

L'application est composée de **3 parties principales** qui communiquent entre elles :
1. **Frontend** (interface utilisateur dans le navigateur)
2. **Backend** (serveur qui traite les données)
3. **Base de données** (stockage des informations)

---

## 🏗️ Architecture globale

### Schéma simplifié

```
┌─────────────────────────────────────────────────────────────┐
│                    NAVIGATEUR WEB (Frontend)                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Pages Next.js                                        │  │
│  │  - Dashboard                                          │  │
│  │  - Transactions                                       │  │
│  │  - Amortissements, Bilan, Cashflow, Pivot            │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Composants React                                    │  │
│  │  - FileUpload (upload fichier)                       │  │
│  │  - TransactionsTable (tableau transactions)          │  │
│  │  - ImportLog (historique imports)                   │  │
│  │  - EditTransactionModal (édition)                   │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API Client (client.ts)                              │  │
│  │  - Communication avec le backend                    │  │
│  │  - Envoi de requêtes HTTP                            │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Requêtes HTTP (JSON)
                        │ http://localhost:8000/api/...
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                    SERVEUR BACKEND (FastAPI)                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Routes API (routes/transactions.py)                 │  │
│  │  - GET /api/transactions (liste)                     │  │
│  │  - POST /api/transactions/import (import CSV)        │  │
│  │  - PUT /api/transactions/{id} (modifier)              │  │
│  │  - DELETE /api/transactions/{id} (supprimer)          │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Utilitaires (utils/)                                │  │
│  │  - csv_utils.py (lecture fichiers CSV)              │  │
│  │  - balance_utils.py (calcul des soldes)              │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Modèles Pydantic (models.py)                        │  │
│  │  - Validation des données                           │  │
│  │  - Format des réponses API                           │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ SQLAlchemy ORM
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                  BASE DE DONNÉES (SQLite)                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Tables principales                                  │  │
│  │  - transactions (transactions bancaires)            │  │
│  │  - file_imports (historique des imports)             │  │
│  │  - enriched_transactions (données enrichies)         │  │
│  │  - ... (autres tables pour enrichissement)          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Explication simple

**Frontend (Next.js/React)** = Ce que vous voyez dans votre navigateur
- Les pages, les boutons, les tableaux
- C'est l'interface utilisateur

**Backend (FastAPI)** = Le cerveau de l'application
- Reçoit les demandes du frontend
- Traite les fichiers CSV
- Calcule les soldes
- Gère la logique métier

**Base de données (SQLite)** = La mémoire de l'application
- Stocke toutes les transactions
- Garde l'historique des imports
- Persiste les données même après fermeture

---

## 🔄 Comment tout fonctionne ensemble

### Exemple concret : Importer un fichier CSV

Voici ce qui se passe étape par étape quand vous importez un fichier :

#### 1️⃣ **Vous sélectionnez un fichier** (Frontend)
```
FileUpload.tsx
  ↓
Ouvre le sélecteur de fichiers
  ↓
Fichier sélectionné : trades_evry_2021.csv
```

#### 2️⃣ **Le frontend envoie le fichier au backend** (Communication)
```
FileUpload.tsx
  ↓
client.ts (API Client)
  ↓
POST http://localhost:8000/api/transactions/preview
  ↓
Envoie le fichier CSV au serveur
```

#### 3️⃣ **Le backend analyse le fichier** (Backend)
```
routes/transactions.py (endpoint preview)
  ↓
csv_utils.py (read_csv_safely)
  - Détecte l'encodage (UTF-8, Latin-1...)
  - Détecte le séparateur (; ou ,)
  - Lit le fichier ligne par ligne
  ↓
csv_utils.py (detect_column_mapping)
  - Identifie automatiquement les colonnes
  - Date → colonne 1
  - Montant → colonne 2
  - Nom → colonne 3
  ↓
Retourne au frontend :
  - Les 10 premières lignes (aperçu)
  - Le mapping proposé
  - Les statistiques (nombre de lignes, dates min/max)
```

#### 4️⃣ **Vous confirmez le mapping** (Frontend)
```
ColumnMappingModal.tsx
  - Affiche l'aperçu
  - Vous pouvez modifier le mapping si besoin
  - Vous cliquez sur "Confirmer et importer"
```

#### 5️⃣ **Le backend importe les transactions** (Backend)
```
routes/transactions.py (endpoint import)
  ↓
csv_utils.py (read_csv_safely)
  - Relit le fichier
  ↓
csv_utils.py (validate_transactions)
  - Vérifie que les dates sont valides
  - Vérifie que les montants sont numériques
  - Nettoie les données
  ↓
Pour chaque ligne valide :
  - Vérifie si c'est un doublon (même date + montant + nom)
  - Si nom vide → génère "nom_a_justifier_N"
  - Calcule le solde (solde précédent + montant)
  - Prépare la transaction à insérer
  ↓
Insère toutes les transactions en BDD
  ↓
balance_utils.py (recalculate_all_balances)
  - Recalcule TOUS les soldes depuis le début
  - Garantit la cohérence même si dates non chronologiques
  ↓
Enregistre dans file_imports (historique)
  ↓
Retourne au frontend :
  - Nombre de transactions importées
  - Nombre de doublons
  - Nombre d'erreurs
  - Liste des erreurs détaillées
```

#### 6️⃣ **Le frontend affiche les résultats** (Frontend)
```
ColumnMappingModal.tsx
  ↓
ImportLogContext (ajoute un log en mémoire)
  - Étape 1: Fichier sélectionné
  - Étape 2: Analyse du fichier
  - Étape 3: Import en cours
  - Étape 4: Import terminé
  ↓
ImportLog.tsx
  - Affiche le log dans l'historique
  - Affiche les erreurs ligne par ligne si présentes
```

#### 7️⃣ **Le tableau se met à jour** (Frontend)
```
TransactionsTable.tsx
  ↓
client.ts (GET /api/transactions)
  ↓
Backend récupère les transactions depuis la BDD
  ↓
Frontend affiche le nouveau tableau avec toutes les transactions
```

### Exemple concret : Modifier une transaction

#### 1️⃣ **Vous cliquez sur ✏️** (Frontend)
```
TransactionsTable.tsx
  ↓
Ouvre EditTransactionModal.tsx
  - Pré-remplit les champs (date, quantité, nom)
```

#### 2️⃣ **Vous modifiez et sauvegardez** (Frontend)
```
EditTransactionModal.tsx
  ↓
client.ts (PUT /api/transactions/{id})
  - Envoie les nouvelles valeurs
```

#### 3️⃣ **Le backend met à jour** (Backend)
```
routes/transactions.py (endpoint PUT)
  ↓
Met à jour la transaction en BDD
  ↓
balance_utils.py (recalculate_balances_from_date)
  - Recalcule les soldes depuis la date modifiée
  - Met à jour toutes les transactions suivantes
  ↓
Retourne la transaction mise à jour
```

#### 4️⃣ **Le tableau se rafraîchit** (Frontend)
```
TransactionsTable.tsx
  - Recharge la liste depuis la BDD
  - Affiche les nouveaux soldes
```

---

## 📁 Structure détaillée du projet

### Backend (`backend/`)

Le backend est le serveur qui traite toutes les demandes.

```
backend/
├── api/                          # Code de l'API
│   ├── main.py                   # Point d'entrée de l'application FastAPI
│   │                             # - Crée l'application
│   │                             # - Configure CORS (autorise le frontend)
│   │                             # - Enregistre les routes
│   │
│   ├── models.py                 # Modèles Pydantic (validation des données)
│   │                             # - TransactionCreate, TransactionUpdate
│   │                             # - FilePreviewResponse, FileImportResponse
│   │                             # - Définit le format des données API
│   │
│   ├── routes/                   # Routes API (endpoints)
│   │   └── transactions.py      # Toutes les routes liées aux transactions
│   │                             # - GET /api/transactions (liste)
│   │                             # - POST /api/transactions/preview (aperçu CSV)
│   │                             # - POST /api/transactions/import (import CSV)
│   │                             # - PUT /api/transactions/{id} (modifier)
│   │                             # - DELETE /api/transactions/{id} (supprimer)
│   │
│   └── utils/                   # Utilitaires (fonctions réutilisables)
│       ├── csv_utils.py         # Gestion des fichiers CSV
│       │                         # - read_csv_safely (lit un CSV)
│       │                         # - detect_column_mapping (détecte les colonnes)
│       │                         # - validate_transactions (valide les données)
│       │
│       └── balance_utils.py    # Calcul des soldes
│                               # - recalculate_balances_from_date
│                               # - recalculate_all_balances
│
├── database/                    # Base de données
│   ├── connection.py           # Connexion à la base de données
│   │                           # - get_db() (obtient une session)
│   │                           # - init_database() (crée les tables)
│   │
│   ├── models.py               # Modèles SQLAlchemy (structure BDD)
│   │                           # - Transaction (table transactions)
│   │                           # - FileImport (table file_imports)
│   │                           # - Définit les colonnes de chaque table
│   │
│   ├── schema.sql             # Schéma SQL (structure des tables)
│   │                           # - Définition des tables
│   │                           # - Index pour performance
│   │
│   └── lmnp.db                # Fichier de base de données SQLite
│                               # - Contient toutes les données
│                               # - Créé automatiquement au premier démarrage
│
├── data/                       # Données (fichiers CSV importés)
│   └── input/
│       └── trades/            # Fichiers CSV archivés après import
│
└── tests/                     # Tests automatiques
    ├── test_api.py           # Tests des endpoints API
    ├── test_csv_utils.py     # Tests de la lecture CSV
    └── ...
```

**Pourquoi cette structure ?**
- **Séparation des responsabilités** : Chaque dossier a un rôle précis
- **Réutilisabilité** : Les utilitaires peuvent être utilisés partout
- **Maintenabilité** : Facile de trouver où modifier quelque chose

### Frontend (`frontend/`)

Le frontend est ce que vous voyez dans votre navigateur.

```
frontend/
├── app/                        # Pages Next.js (App Router)
│   ├── layout.tsx             # Layout principal (en-tête, navigation)
│   ├── page.tsx               # Page d'accueil
│   │
│   └── dashboard/            # Pages du dashboard
│       ├── layout.tsx        # Layout du dashboard
│       │                     # - Enveloppe avec ImportLogProvider
│       │                     # - Rend Header et Navigation disponibles partout
│       │
│       ├── page.tsx          # Page principale du dashboard
│       │                     # - Affiche les statistiques
│       │
│       ├── transactions/
│       │   └── page.tsx      # Page de gestion des transactions
│       │                     # - Onglet "Load Trades" (import)
│       │                     # - Onglet "All Transactions" (tableau)
│       │
│       ├── amortissements/
│       │   └── page.tsx      # Page des amortissements (à venir)
│       │
│       ├── bilan/
│       │   └── page.tsx       # Page du bilan (à venir)
│       │
│       ├── cashflow/
│       │   └── page.tsx      # Page du cashflow (à venir)
│       │
│       └── pivot/
│           └── page.tsx      # Page du tableau pivot (à venir)
│
└── src/                       # Code source réutilisable
    ├── api/
    │   └── client.ts         # Client API (communication avec backend)
    │                         # - fetchAPI() (fonction générique)
    │                         # - transactionsAPI (CRUD transactions)
    │                         # - fileUploadAPI (import fichiers)
    │                         # - Toutes les fonctions pour appeler le backend
    │
    ├── components/           # Composants React réutilisables
    │   ├── Header.tsx        # En-tête de l'application
    │   │
    │   ├── Navigation.tsx    # Navigation entre les pages
    │   │                     # - Onglets : Transactions, Pivot, Bilan...
    │   │
    │   ├── FileUpload.tsx    # Composant d'upload de fichier
    │   │                     # - Bouton "Load Trades"
    │   │                     # - Sélection de fichier
    │   │                     # - Appelle preview API automatiquement
    │   │
    │   ├── ColumnMappingModal.tsx  # Modal de mapping et import
    │   │                           # - Affiche l'aperçu du fichier
    │   │                           # - Permet de modifier le mapping
    │   │                           # - Lance l'import
    │   │                           # - Affiche les résultats et erreurs
    │   │
    │   ├── ImportLog.tsx    # Historique des imports
    │   │                     # - Affiche la liste des imports (mémoire + BDD)
    │   │                     # - Modal avec logs détaillés
    │   │                     # - Auto-refresh si import en cours
    │   │
    │   ├── TransactionsTable.tsx  # Tableau des transactions
    │   │                          # - Affichage paginé
    │   │                          # - Tri par colonnes
    │   │                          # - Filtrage par date et recherche
    │   │                          # - Édition (✏️) et suppression (🗑️)
    │   │                          # - Sélection multiple avec checkboxes
    │   │
    │   └── EditTransactionModal.tsx  # Modal d'édition
    │                                 # - Permet de modifier date, quantité, nom
    │                                 # - Validation des champs
    │                                 # - Sauvegarde et recalcul automatique
    │
    ├── contexts/             # Contextes React (état global)
    │   └── ImportLogContext.tsx  # Gestion des logs d'import
    │                             # - Stocke les logs en mémoire
    │                             # - Fonctions : addLog, updateLog, addLogEntry
    │                             # - Disponible dans tout le dashboard
    │
    └── types/                # Types TypeScript
        └── index.ts          # Définitions de types partagés
```

**Pourquoi cette structure ?**
- **Composants réutilisables** : Chaque composant a une responsabilité unique
- **Séparation pages/composants** : Les pages utilisent les composants
- **Contextes pour l'état global** : Les logs sont partagés entre composants

---

## 🔀 Flux de données

### Flux 1 : Import d'un fichier CSV

```
1. Utilisateur sélectionne fichier
   ↓
2. FileUpload.tsx → client.ts → POST /api/transactions/preview
   ↓
3. Backend : csv_utils.py analyse le fichier
   ↓
4. Backend retourne : preview + mapping proposé
   ↓
5. ColumnMappingModal.tsx affiche l'aperçu
   ↓
6. Utilisateur confirme
   ↓
7. ColumnMappingModal.tsx → client.ts → POST /api/transactions/import
   ↓
8. Backend : 
   - Lit le CSV
   - Valide les données
   - Détecte les doublons
   - Calcule les soldes
   - Insère en BDD
   - Recalcule tous les soldes
   ↓
9. Backend retourne : résultats (imported, duplicates, errors)
   ↓
10. ColumnMappingModal.tsx :
    - Ajoute des logs dans ImportLogContext
    - Affiche les résultats
    - Appelle onImportComplete()
    ↓
11. TransactionsTable.tsx recharge la liste
```

### Flux 2 : Affichage des transactions

```
1. TransactionsTable.tsx se monte (chargement initial)
   ↓
2. useEffect → client.ts → GET /api/transactions
   ↓
3. Backend : 
   - Récupère les transactions depuis la BDD
   - Applique les filtres (date, recherche)
   - Retourne la liste paginée
   ↓
4. TransactionsTable.tsx affiche le tableau
```

### Flux 3 : Modification d'une transaction

```
1. Utilisateur clique sur ✏️
   ↓
2. TransactionsTable.tsx ouvre EditTransactionModal.tsx
   ↓
3. Utilisateur modifie et sauvegarde
   ↓
4. EditTransactionModal.tsx → client.ts → PUT /api/transactions/{id}
   ↓
5. Backend :
   - Met à jour la transaction en BDD
   - Recalcule les soldes depuis la date modifiée
   ↓
6. Backend retourne : transaction mise à jour
   ↓
7. EditTransactionModal.tsx appelle onSave()
   ↓
8. TransactionsTable.tsx recharge la liste
```

### Flux 4 : Suppression d'une transaction

```
1. Utilisateur clique sur 🗑️
   ↓
2. TransactionsTable.tsx → confirmation
   ↓
3. client.ts → DELETE /api/transactions/{id}
   ↓
4. Backend :
   - Supprime la transaction de la BDD
   - Recalcule les soldes depuis la date supprimée
   ↓
5. TransactionsTable.tsx recharge la liste
```

---

## 🎨 Rôles des composants principaux

### Backend

#### `api/main.py`
**Rôle** : Point d'entrée de l'application
- Crée l'application FastAPI
- Configure CORS (autorise le frontend à communiquer)
- Enregistre toutes les routes
- Initialise la base de données au démarrage

#### `api/routes/transactions.py`
**Rôle** : Gère toutes les opérations sur les transactions
- **GET /api/transactions** : Liste les transactions (avec pagination, filtres)
- **POST /api/transactions/preview** : Analyse un fichier CSV et propose un mapping
- **POST /api/transactions/import** : Importe un fichier CSV dans la BDD
- **PUT /api/transactions/{id}** : Modifie une transaction
- **DELETE /api/transactions/{id}** : Supprime une transaction

#### `api/utils/csv_utils.py`
**Rôle** : Gestion des fichiers CSV
- **read_csv_safely()** : Lit un CSV en détectant automatiquement l'encodage et le séparateur
- **detect_column_mapping()** : Identifie automatiquement les colonnes (date, montant, nom)
- **validate_transactions()** : Vérifie que les données sont valides
- **preview_transactions()** : Retourne les premières lignes pour aperçu

#### `api/utils/balance_utils.py`
**Rôle** : Calcul des soldes bancaires
- **recalculate_balances_from_date()** : Recalcule les soldes depuis une date donnée
- **recalculate_all_balances()** : Recalcule tous les soldes depuis le début
- Utilisé après chaque modification/suppression/import

#### `database/models.py`
**Rôle** : Définit la structure des tables
- **Transaction** : Table des transactions (date, quantité, nom, solde...)
- **FileImport** : Table de l'historique des imports
- Utilise SQLAlchemy ORM (Object-Relational Mapping)

#### `database/connection.py`
**Rôle** : Gestion de la connexion à la base de données
- **get_db()** : Obtient une session de base de données
- **init_database()** : Crée les tables si elles n'existent pas

### Frontend

#### `src/api/client.ts`
**Rôle** : Point de communication unique avec le backend
- **fetchAPI()** : Fonction générique pour toutes les requêtes HTTP
- **transactionsAPI** : Fonctions pour les transactions (getAll, update, delete...)
- **fileUploadAPI** : Fonctions pour l'import (preview, import, getImportsHistory)
- Gère les erreurs et les transforme en messages compréhensibles

#### `app/dashboard/layout.tsx`
**Rôle** : Layout commun à toutes les pages du dashboard
- Enveloppe toutes les pages avec `ImportLogProvider`
- Rend Header et Navigation disponibles partout
- Structure de base de l'interface

#### `app/dashboard/transactions/page.tsx`
**Rôle** : Page principale de gestion des transactions
- Gère les onglets (Load Trades, All Transactions)
- Affiche le compteur de transactions
- Intègre FileUpload, ImportLog, TransactionsTable

#### `src/components/FileUpload.tsx`
**Rôle** : Composant d'upload de fichier
- Bouton "Load Trades"
- Sélection de fichier
- Appelle automatiquement l'API preview
- Ouvre ColumnMappingModal avec les résultats

#### `src/components/ColumnMappingModal.tsx`
**Rôle** : Modal de confirmation et import
- Affiche l'aperçu du fichier (10 premières lignes)
- Permet de modifier le mapping des colonnes
- Lance l'import et affiche les résultats
- Ajoute des logs détaillés dans ImportLogContext
- Affiche les erreurs ligne par ligne

#### `src/components/ImportLog.tsx`
**Rôle** : Historique des imports
- Affiche la liste des imports (mémoire + base de données)
- Modal avec logs détaillés étape par étape
- Auto-refresh toutes les 2-3 secondes si import en cours
- Affiche le compteur de transactions

#### `src/components/TransactionsTable.tsx`
**Rôle** : Tableau des transactions
- Affichage paginé (25, 50, 100, 200 par page)
- Tri par colonnes (date, quantité, nom, solde)
- Filtrage par date (début/fin) et recherche par nom
- Édition (✏️) et suppression (🗑️) individuelles
- Sélection multiple avec checkboxes
- Suppression en masse

#### `src/components/EditTransactionModal.tsx`
**Rôle** : Modal d'édition de transaction
- Permet de modifier date, quantité, nom
- Validation des champs
- Appelle l'API PUT pour sauvegarder
- Déclenche le recalcul automatique des soldes

#### `src/contexts/ImportLogContext.tsx`
**Rôle** : Gestion de l'état global des logs
- Stocke les logs en mémoire (pas seulement en BDD)
- Fonctions : addLog, updateLog, addLogEntry, clearLogs
- Disponible dans tout le dashboard via le Provider

---

## 🚀 Démarrage rapide

### Prérequis
- Python 3.8+
- Node.js 18+
- npm ou yarn

### Installation

1. **Cloner le projet** (si nécessaire)
```bash
git clone <url-du-repo>
cd LMNP
```

2. **Installer les dépendances backend**
```bash
cd backend
pip install -r requirements.txt
```

3. **Installer les dépendances frontend**
```bash
cd frontend
npm install
```

### Démarrer l'application

**Terminal 1 - Backend** :
```bash
cd backend
python3 -m uvicorn api.main:app --reload --port 8000
```

**Terminal 2 - Frontend** :
```bash
cd frontend
npm run dev
```

L'application sera accessible sur :
- **Frontend** : http://localhost:3000
- **Backend API** : http://localhost:8000
- **Documentation API** : http://localhost:8000/docs (Swagger UI)

### Vérifier que tout fonctionne

1. Ouvrez http://localhost:3000 dans votre navigateur
2. Vous devriez voir le dashboard
3. Cliquez sur l'onglet "Transactions" → "Load Trades"
4. Sélectionnez un fichier CSV
5. L'aperçu devrait s'afficher

---

## 📚 Documentation complémentaire

- **[BEST_PRACTICES.md](docs/workflow/BEST_PRACTICES.md)** - ⚠️ **À LIRE AVANT TOUTE MODIFICATION**
- **[GIT_WORKFLOW.md](docs/workflow/GIT_WORKFLOW.md)** - Guide de workflow Git
- **[IMPLEMENTATION_PLAN.md](docs/project/features/IMPLEMENTATION_PLAN.md)** - Plan d'implémentation détaillé
- **[START_SERVERS.md](START_SERVERS.md)** - Guide de démarrage des serveurs

---

## 🔍 Pourquoi cette architecture ?

### Séparation Frontend/Backend
- **Avantage** : Le frontend et le backend peuvent évoluer indépendamment
- **Avantage** : Facile de changer de technologie (ex: remplacer React par Vue)
- **Avantage** : Le backend peut servir plusieurs frontends (web, mobile...)

### Base de données SQLite
- **Avantage** : Simple, pas besoin de serveur de base de données séparé
- **Avantage** : Fichier unique, facile à sauvegarder
- **Limitation** : Pour la production, on pourrait migrer vers PostgreSQL

### Utilisation de Contextes React
- **Avantage** : Les logs d'import sont partagés entre plusieurs composants
- **Avantage** : Pas besoin de passer des props partout
- **Exemple** : ColumnMappingModal et ImportLog utilisent le même contexte

### Calcul automatique des soldes
- **Pourquoi** : Les fichiers CSV peuvent ne pas avoir de colonne solde
- **Pourquoi** : Garantit la cohérence même si fichiers importés dans le désordre
- **Comment** : Recalcul complet après chaque import/modification

---

## 🎓 Concepts importants

### API REST
- **GET** : Récupérer des données (liste des transactions)
- **POST** : Créer quelque chose (importer un fichier)
- **PUT** : Modifier quelque chose (modifier une transaction)
- **DELETE** : Supprimer quelque chose (supprimer une transaction)

### ORM (Object-Relational Mapping)
- **SQLAlchemy** : Permet d'utiliser Python au lieu de SQL brut
- **Exemple** : `db.query(Transaction).filter(Transaction.date == date).first()`
- **Avantage** : Code plus lisible et plus sûr

### React Context
- **Problème** : Comment partager des données entre composants distants ?
- **Solution** : ImportLogContext fournit les logs à tous les composants enfants
- **Exemple** : ColumnMappingModal et ImportLog utilisent les mêmes logs

### CORS (Cross-Origin Resource Sharing)
- **Problème** : Le frontend (port 3000) veut communiquer avec le backend (port 8000)
- **Solution** : Le backend autorise les requêtes depuis le frontend
- **Configuration** : Dans `api/main.py`, middleware CORS

---

## ❓ Questions fréquentes

**Q : Pourquoi recalculer tous les soldes après chaque import ?**
R : Pour garantir la cohérence même si les fichiers sont importés dans un ordre non chronologique (ex: 2021, 2023, 2022).

**Q : Pourquoi deux types de logs (mémoire + base de données) ?**
R : Les logs en mémoire sont pour l'affichage en temps réel pendant l'import. Les logs en base de données sont pour l'historique permanent.

**Q : Pourquoi générer "nom_a_justifier_N" pour les transactions sans nom ?**
R : Pour permettre l'import même si certaines lignes n'ont pas de nom, et les identifier visuellement (en rouge avec ⚠️) pour correction ultérieure.

**Q : Comment fonctionne la détection de doublons ?**
R : Pour les transactions avec nom : vérifie date + quantité + nom. Pour les transactions sans nom : vérifie seulement date + quantité (car le nom généré change à chaque import).

---

**Dernière mise à jour** : 2025-12-19
