# Test Step 6.6.5 - Colonne "Type d'immobilisation"

## Objectif
Vérifier que les 7 types initiaux s'affichent et que l'édition du nom fonctionne correctement.

## Prérequis
- Serveur backend démarré
- Serveur frontend démarré (`npm run dev`)
- Base de données initialisée

## Instructions de test

### Test 1 : Affichage des 7 types initiaux (création automatique)

1. **Ouvrir le navigateur** et aller sur la page `/dashboard/amortissements`

2. **Sélectionner le Level 2 "Immobilisations"** dans le dropdown "Level 2 (Valeur à considérer comme amortissement)"
   - ⚠️ **IMPORTANT** : Les 7 types sont créés automatiquement UNIQUEMENT pour "Immobilisations"
   - Si aucun type n'existe pour "Immobilisations", les 7 types doivent être créés automatiquement

3. **Vérifier dans le tableau** :
   - ✅ Les 7 types suivants s'affichent :
     - Part terrain
     - Immobilisation structure/GO
     - Immobilisation mobilier
     - Immobilisation IGT
     - Immobilisation agencements
     - Immobilisation Facade/Toiture
     - Immobilisation travaux
   - ✅ Les types sont triés par ordre alphabétique
   - ✅ Les autres colonnes affichent "-" (pas encore implémentées)

4. **Vérifier dans la console du navigateur** :
   - ✅ Message : `[AmortizationConfigCard] Aucun type trouvé pour Level 2 "Immobilisations", création des 7 types initiaux...`
   - ✅ Message : `[AmortizationConfigCard] ✓ 7 types initiaux créés avec succès`

### Test 1b : Pas de création automatique pour les autres Level 2

1. **Sélectionner un autre Level 2** (différent de "Immobilisations") dans le dropdown
   - Exemple : "Produit", "Charges", etc.

2. **Vérifier dans le tableau** :
   - ✅ Si aucun type n'existe pour ce Level 2, le tableau affiche "Aucun type d'amortissement trouvé"
   - ✅ Aucun type n'est créé automatiquement
   - ✅ Pas de message de création dans la console

### Test 2 : Édition du nom d'un type

1. **Cliquer sur le nom d'un type** (ex: "Part terrain")
   - ✅ Le nom devient un champ texte éditable avec bordure bleue
   - ✅ Le champ est en focus automatiquement

2. **Modifier le nom** (ex: "Part terrain" → "Terrain")
   - ✅ Le texte peut être modifié

3. **Sauvegarder** :
   - **Option A** : Appuyer sur `Enter`
   - **Option B** : Cliquer en dehors du champ (`onBlur`)
   - ✅ Le nom est sauvegardé en base de données
   - ✅ Le tableau se recharge avec le nouveau nom
   - ✅ Le champ redevient un texte non-éditable

4. **Annuler l'édition** :
   - Cliquer sur un nom pour éditer
   - Appuyer sur `Escape`
   - ✅ L'édition est annulée, le nom original est conservé
   - ✅ Le champ redevient un texte non-éditable

### Test 3 : Vérification en base de données

1. **Vérifier que les types sont bien créés en BDD** :
   ```bash
   python3 backend/scripts/check_amortization_types.py
   ```
   - ✅ Les 7 types doivent être présents
   - ✅ Chaque type a le `level_2_value` correspondant au Level 2 sélectionné

2. **Vérifier qu'un nom modifié est bien sauvegardé** :
   - Après avoir modifié un nom dans l'interface
   - Exécuter à nouveau le script de vérification
   - ✅ Le nom modifié doit apparaître en BDD

## Résultats attendus

- ✅ Les 7 types initiaux sont créés automatiquement UNIQUEMENT pour "Immobilisations" si aucun type n'existe
- ✅ Pour les autres Level 2, aucun type n'est créé automatiquement
- ✅ Les types s'affichent dans le tableau
- ✅ L'édition du nom fonctionne (clic pour éditer)
- ✅ La sauvegarde fonctionne (Enter ou onBlur)
- ✅ L'annulation fonctionne (Escape)
- ✅ Les modifications sont persistées en base de données

## Notes

- ⚠️ **IMPORTANT** : Les 7 types par défaut sont créés automatiquement UNIQUEMENT pour le Level 2 = "Immobilisations"
- Pour les autres valeurs Level 2, aucun type n'est créé automatiquement
- Si des types existent déjà pour le Level 2 sélectionné, ils s'affichent directement (pas de création)
- Les types sont créés avec des valeurs vides par défaut :
  - `level_1_values`: []
  - `duration`: 0.0
  - `start_date`: null
  - `annual_amount`: null

