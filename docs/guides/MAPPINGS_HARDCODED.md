# Guide : Modifier ou Ajouter des Mappings Hardcodés

Ce guide explique comment modifier ou ajouter des mappings hardcodés dans l'application.

## 📋 Vue d'ensemble

Les **mappings hardcodés** sont des combinaisons de `Level 1`, `Level 2` et `Level 3` qui sont définies dans un fichier Excel et qui apparaissent dans l'onglet **Transactions > Mapping > Mappings autorisés**.

Ces mappings sont **protégés** (`is_hardcoded = True`) et ne peuvent être supprimés que via la mise à jour depuis le fichier Excel.

## 🎯 Cas d'usage

### Ajouter un nouveau mapping hardcodé
Exemple : Ajouter la combinaison `(Assurance habitation, Assurances, Charges Déductibles)`

### Modifier un mapping existant
Exemple : Changer `Level 2` de `(Frais postaux, Frais d'acquisition, Charges Déductibles)` en `(Frais postaux, Frais administratifs, Charges Déductibles)`

### Supprimer un mapping hardcodé
Exemple : Retirer `(Frais de notaire, Frais d'acquisition, Charges Déductibles)` de la liste

## 📝 Étape 1 : Modifier le fichier Excel

### Localisation du fichier
```
scripts/mappings_obligatoires.xlsx
```

### Format du fichier

Le fichier Excel doit contenir **exactement 3 colonnes** :
- `Level 1` (obligatoire)
- `Level 2` (obligatoire)
- `Level 3` (optionnel)

### Règles à respecter

#### 1. Colonnes obligatoires
- ✅ `Level 1` : **Obligatoire** - Ne peut pas être vide
- ✅ `Level 2` : **Obligatoire** - Ne peut pas être vide
- ⚠️ `Level 3` : **Optionnel** - Peut être vide (sera traité comme `NULL`)

#### 2. Valeurs `Level 3` autorisées

Si `Level 3` est renseigné, il **DOIT** être une des valeurs suivantes :
- `Passif`
- `Produits`
- `Emprunt`
- `Charges Déductibles`
- `Actif`

⚠️ **Attention** : Toute autre valeur sera **ignorée** lors de la mise à jour.

#### 3. Format des données
- Les valeurs sont **trimées** automatiquement (espaces en début/fin supprimés)
- Les lignes avec `Level 1` ou `Level 2` vides sont **ignorées**
- Les lignes avec `Level 3` invalide sont **ignorées** (avec un message d'avertissement)

### Exemple de fichier Excel

| Level 1 | Level 2 | Level 3 |
|---------|---------|---------|
| Cotisation Foncière des Entreprises (CFE) | Taxes | Charges Déductibles |
| Taxe foncière | Taxes | Charges Déductibles |
| Eau, électricité, gaz | Charges courantes | Charges Déductibles |
| Frais postaux | Frais d'acquisition | Charges Déductibles |
| Assurance habitation | Assurances | Charges Déductibles |
| Assurance CREDIT | Mensualités | Emprunt |

## 🔄 Étape 2 : Exécuter le script de mise à jour

### Commande à exécuter

```bash
python3 backend/scripts/update_hardcoded_mappings.py
```

### Ce que fait le script

Le script effectue les opérations suivantes :

1. **Lecture du fichier Excel**
   - Vérifie que le fichier existe
   - Vérifie le format (colonnes attendues)
   - Valide les valeurs `Level 3`
   - Charge toutes les combinaisons valides

2. **Suppression des mappings obsolètes**
   - Identifie tous les mappings hardcodés actuels (`is_hardcoded = True`)
   - Supprime ceux qui ne sont **plus** dans le fichier Excel
   - ⚠️ **Les mappings manuels** (`is_hardcoded = False`) sont **conservés**

3. **Ajout/Mise à jour des mappings du fichier Excel**
   - Pour chaque combinaison du fichier Excel :
     - Si le mapping existe déjà : le marque comme hardcodé (`is_hardcoded = True`) si nécessaire
     - Si le mapping n'existe pas : le crée avec `is_hardcoded = True`

4. **Conservation des mappings manuels**
   - Tous les mappings avec `is_hardcoded = False` sont **conservés** (non modifiés)

### Sortie du script

Le script affiche :
- ✅ Nombre de mappings supprimés
- ✅ Nombre de nouveaux mappings ajoutés
- ✅ Nombre de mappings existants marqués comme hardcodés
- ✅ Nombre de mappings manuels conservés
- ✅ Total des mappings hardcodés après mise à jour

**Exemple de sortie :**
```
============================================================
Mise à jour des mappings hardcodés depuis Excel
============================================================

1. Initialisation de la base de données...
   ✓ Base de données initialisée

2. Lecture du fichier Excel...
   Fichier : /path/to/scripts/mappings_obligatoires.xlsx
   ✓ 53 combinaisons trouvées dans le fichier Excel

3. Mise à jour de la base de données...
🗑️  Suppression : ('Frais de notaire', "Frais d'acquisition", 'Charges Déductibles')
➕ Ajouté : (Assurance habitation, Assurances, Charges Déductibles)

4. Résultat :
   ✓ 1 mappings hardcodés supprimés (absents du fichier Excel)
   ✓ 1 nouveaux mappings hardcodés ajoutés
   ✓ 0 mappings existants marqués comme hardcodés
   ✓ 0 mappings manuels conservés (is_hardcoded = False)

   Total mappings hardcodés après mise à jour : 53
   Total mappings manuels : 0
```

## ✅ Étape 3 : Vérifier la mise à jour

### Vérification dans l'application

1. Ouvrir l'application
2. Aller dans **Transactions > Mapping > Mappings autorisés**
3. Vérifier que :
   - Les nouveaux mappings apparaissent
   - Les mappings supprimés n'apparaissent plus
   - Les modifications sont bien reflétées

### Vérification dans la base de données (optionnel)

Si tu veux vérifier directement dans la base de données :

```bash
python3 -c "
from backend.database.connection import SessionLocal
from backend.database.models import AllowedMapping

db = SessionLocal()
hardcoded = db.query(AllowedMapping).filter(AllowedMapping.is_hardcoded == True).all()
print(f'Total mappings hardcodés : {len(hardcoded)}')
for m in hardcoded[:10]:  # Afficher les 10 premiers
    print(f'  - {m.level_1} | {m.level_2} | {m.level_3}')
db.close()
"
```

## 🔍 Cas particuliers

### Ajouter un mapping qui existe déjà comme manuel

Si tu ajoutes dans le fichier Excel une combinaison qui existe déjà avec `is_hardcoded = False` (ajoutée manuellement), le script la **marquera comme hardcodée** (`is_hardcoded = True`).

### Supprimer un mapping hardcodé

Pour supprimer un mapping hardcodé :
1. Retire la ligne correspondante du fichier Excel
2. Exécute le script de mise à jour
3. Le mapping sera supprimé de la base de données

⚠️ **Attention** : Cette action est **irréversible** (sauf si tu réajoutes la ligne dans le fichier Excel).

### Mapping avec Level 3 vide

Si tu veux un mapping sans `Level 3`, laisse la colonne `Level 3` vide dans le fichier Excel. Le script traitera cela comme `NULL` dans la base de données.

**Exemple :**
| Level 1 | Level 2 | Level 3 |
|---------|---------|---------|
| Autre dépense | Divers | *(vide)* |

## ⚠️ Points d'attention

### 1. Sauvegarde avant modification
Il est recommandé de faire une **sauvegarde de la base de données** avant d'exécuter le script, surtout si tu supprimes des mappings.

### 2. Valeurs Level 3 invalides
Si une ligne contient une valeur `Level 3` non autorisée, elle sera **ignorée** avec un message d'avertissement :
```
⚠️  Ignoré : level_3 invalide 'Valeur invalide' pour (Level 1, Level 2)
```

### 3. Doublons
Le script gère automatiquement les doublons (contrainte unique sur `level_1`, `level_2`, `level_3`). Si un doublon est détecté, il sera ignoré.

### 4. Mappings manuels
Les mappings avec `is_hardcoded = False` (ajoutés manuellement dans l'interface) sont **toujours conservés**, même s'ils ne sont pas dans le fichier Excel.

## 📚 Références

- **Script de mise à jour** : `backend/scripts/update_hardcoded_mappings.py`
- **Service de validation** : `backend/api/services/mapping_obligatoire_service.py`
- **Modèle de données** : `backend/database/models.py` (classe `AllowedMapping`)

## 🆘 Dépannage

### Erreur : "Le fichier Excel n'existe pas"
- Vérifie que le fichier est bien dans `scripts/mappings_obligatoires.xlsx`
- Vérifie le chemin absolu dans le message d'erreur

### Erreur : "Le fichier Excel doit contenir les colonnes : ['Level 1', 'Level 2', 'Level 3']"
- Vérifie que les colonnes s'appellent exactement `Level 1`, `Level 2`, `Level 3` (avec espaces)
- Vérifie qu'il n'y a pas de fautes de frappe

### Des mappings ne sont pas ajoutés
- Vérifie les messages d'avertissement dans la sortie du script
- Vérifie que `Level 1` et `Level 2` ne sont pas vides
- Vérifie que `Level 3` est dans la liste autorisée (ou vide)

### Les mappings manuels ont disparu
- ⚠️ Cela ne devrait **jamais** arriver - le script conserve toujours les mappings avec `is_hardcoded = False`
- Si cela arrive, vérifie la base de données directement

---

**Dernière mise à jour** : 2024
