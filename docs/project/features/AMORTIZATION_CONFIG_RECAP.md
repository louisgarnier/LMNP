# Récapitulatif - Nouvelle Configuration Amortissements

## Vue d'ensemble

Remplacement du panneau latéral de configuration par une **card au-dessus du tableau année par année** avec un tableau de configuration des types d'amortissement.

---

## Structure de la Card de Configuration

### Position
- **Au-dessus** de la card actuelle (tableau année par année)
- **Suppression complète** du panneau latéral actuel

### Contenu de la Card

#### 1. Champ "Level 2" (en haut de la card)
- **Type** : Dropdown/Select
- **Label** : "Level 2 (Valeur à considérer comme amortissement)"
- **Valeurs** : Liste des valeurs uniques de `level_2` depuis les transactions
- **Comportement** : Filtre global pour tous les types d'amortissement

#### 2. Tableau des Types d'Amortissement

**Colonnes du tableau** :

| Colonne | Type | Éditable | Calculé | Description |
|---------|------|----------|---------|-------------|
| **Type d'immobilisation** | Texte | ✅ Oui | ❌ | Nom du type (ex: "Part terrain", "Immobilisation mobilier", "Immobilisation mobilier 2") |
| **Level 1 (valeurs)** | Multi-select | ✅ Oui | ❌ | Liste des valeurs `level_1` mappées à ce type |
| **Date de début** | Date | ✅ Oui | ❌ | Date override (NULL = utiliser dates transactions) |
| **Montant d'immobilisation** | Nombre | ❌ | ✅ | Somme des transactions (level_2 match + level_1 dans mapping) |
| **Durée d'amortissement** | Nombre | ✅ Oui | ❌ | Durée en années (obligatoire) |
| **Annuité d'amortissement** | Nombre | ✅ Oui | ✅ | Montant annuel (calculé = Montant / Durée, puis éditable) |
| **Montant cumulé** | Nombre | ❌ | ✅ | Somme des `AmortizationResult` pour ce type |
| **VNC** | Nombre | ❌ | ✅ | Valeur Nette Comptable = Montant - Cumulé |

**Actions** :
- **Bouton "+"** : Ajouter un nouveau type d'amortissement
- **Clic droit > Supprimer** : Supprimer un type (avec confirmation)

---

## Types d'Amortissement Initiaux

Les **7 catégories initiales** sont pré-remplies automatiquement au premier chargement :

1. **Part terrain**
2. **Immobilisation structure/GO**
3. **Immobilisation mobilier**
4. **Immobilisation IGT**
5. **Immobilisation agencements**
6. **Immobilisation Facade/Toiture**
7. **Immobilisation travaux**

Chaque type initial a :
- `level_1_values` : `[]` (vide)
- `start_date` : `NULL`
- `duration` : `0`
- `annual_amount` : `NULL`

---

## Logique de Calcul

### Montant d'immobilisation
```
Somme de toutes les transactions où :
- transaction.enriched_transaction.level_2 = level_2_value (du champ en haut)
- transaction.enriched_transaction.level_1 IN level_1_values (du type)
```

### Date de début (Override)

**Si `start_date` est NULL** :
- Utiliser la **date de chaque transaction individuelle**
- Calculer les amortissements transaction par transaction (logique actuelle)

**Si `start_date` est renseignée** (ex: "14 March, 2024") :
- Utiliser cette date comme **date de début commune** pour toutes les transactions
- **MAIS** : Seulement pour les transactions de **la même année** que la date override
- Les transactions d'autres années nécessitent un **nouveau type d'amortissement** séparé

**Exemple** :
- Type "Immobilisation mobilier" avec `start_date = "2024-03-14"` :
  - ✅ Transactions de 2024 → utilisent `start_date = "2024-03-14"`
  - ❌ Transactions de 2025 → nécessitent un nouveau type "Immobilisation mobilier 2"

### Annuité d'amortissement

1. **Calcul automatique** : `Annuité = Montant / Durée` (si Montant et Durée renseignés)
2. **Éditable** : Peut être modifiée manuellement
3. **Obligatoire** : Pas de calcul d'amortissement si annuité vide

### Montant cumulé

```
Somme de tous les AmortizationResult où :
- AmortizationResult.category = nom_du_type
- AmortizationResult.year <= année_courante
```

**Note** : Le `category` dans `AmortizationResult` doit correspondre au `name` du type d'amortissement.

### VNC (Valeur Nette Comptable)

```
VNC = Montant d'immobilisation - Montant cumulé
```

---

## Structure de Données Backend

### Option B : Nouvelle Table `AmortizationType`

```sql
CREATE TABLE amortization_types (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(100) NOT NULL,  -- "Part terrain", "Immobilisation mobilier", etc.
  level_2_value VARCHAR(100) NOT NULL,  -- "ammortissements" (référence au champ en haut)
  level_1_values JSON NOT NULL,  -- ["value1", "value2", ...]
  start_date DATE NULL,  -- NULL = utiliser dates transactions, sinon override
  duration FLOAT NOT NULL,  -- Durée en années (obligatoire)
  annual_amount FLOAT NULL,  -- NULL = calculer (Montant/Durée), sinon override
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_amortization_types_level2 ON amortization_types(level_2_value);
```

### Migration depuis `AmortizationConfig`

- **Supprimer** : `AmortizationConfig.level_3_mapping` et les 7 durées fixes
- **Créer** : 7 lignes initiales dans `amortization_types` avec les noms des catégories
- **Conserver** : `AmortizationConfig.level_2_value` (ou le déplacer dans la nouvelle table)

---

## Comportements UI

### Sauvegarde
- **Automatique** : Après chaque modification de champ (`onBlur`)
- **Pas de debounce** : Sauvegarde immédiate

### Ajout de Type
- **Bouton "+"** : Ajoute une nouvelle ligne avec :
  - `name` : Champ texte vide (à renseigner)
  - `level_1_values` : `[]`
  - `start_date` : `NULL`
  - `duration` : `0`
  - `annual_amount` : `NULL`

### Suppression de Type
- **Clic droit > Supprimer** : Affiche confirmation
- **Après confirmation** : Supprime le type et recalcule les amortissements

### Calculs en Temps Réel
- **Montant** : Recalculé automatiquement quand `level_1_values` change
- **Annuité** : Recalculée automatiquement quand `Montant` ou `Durée` change
- **Cumulé** : Recalculé automatiquement après chaque calcul d'amortissement
- **VNC** : Recalculée automatiquement quand `Montant` ou `Cumulé` change

---

## Questions Résolues

✅ **Structure de données** : Option B (nouvelle table `AmortizationType`)  
✅ **Types initiaux** : 7 catégories pré-remplies automatiquement  
✅ **Date override** : Filtre par année (transactions de la même année seulement)  
✅ **Annuité** : Calculée automatiquement (`Montant / Durée`), puis éditable  
✅ **Sauvegarde** : Automatique sur `onBlur`  
✅ **Suppression** : Clic droit > Supprimer avec confirmation  
✅ **Panneau latéral** : Supprimé complètement

