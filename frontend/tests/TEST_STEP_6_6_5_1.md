# Test Step 6.6.5.1: Frontend - Bouton "Réinitialiser aux valeurs par défaut"

## Objectif
Tester le bouton "↻ Réinitialiser" qui supprime tous les types d'amortissement et recrée les 7 types par défaut avec des valeurs vides.

## Prérequis
- Serveur backend démarré
- Serveur frontend démarré
- Au moins un type d'amortissement existe pour un Level 2 sélectionné

## Test 1: Affichage du bouton

### Étapes
1. Ouvrir l'onglet "Amortissements" dans le navigateur
2. Vérifier que la card "Configuration des amortissements" s'affiche
3. Vérifier que le bouton "↻ Réinitialiser" est visible à côté du titre

### Résultat attendu
- ✅ Le bouton "↻ Réinitialiser" s'affiche à droite du titre "Configuration des amortissements"
- ✅ Le bouton contient l'icône "↻" et le texte "Réinitialiser"

---

## Test 2: Bouton désactivé si aucun Level 2 sélectionné

### Étapes
1. S'assurer qu'aucun Level 2 n'est sélectionné (déselectionner si nécessaire)
2. Vérifier l'état du bouton "↻ Réinitialiser"

### Résultat attendu
- ✅ Le bouton est désactivé (grisé, cursor: not-allowed)
- ✅ Le bouton n'est pas cliquable

---

## Test 3: Bouton désactivé si aucun type n'existe pour le Level 2 sélectionné

### Étapes
1. Sélectionner un Level 2 qui n'a aucun type d'amortissement (ex: "Assurance")
2. Vérifier l'état du bouton "↻ Réinitialiser"

### Résultat attendu
- ✅ Le bouton est désactivé (grisé, cursor: not-allowed)
- ✅ Le bouton n'est pas cliquable

---

## Test 4: Bouton activé si des types existent

### Étapes
1. Sélectionner le Level 2 "Immobilisations"
2. Vérifier que des types d'amortissement s'affichent dans le tableau
3. Vérifier l'état du bouton "↻ Réinitialiser"

### Résultat attendu
- ✅ Le bouton est activé (couleur normale, cursor: pointer)
- ✅ Le bouton est cliquable

---

## Test 5: Popup d'avertissement

### Étapes
1. Sélectionner le Level 2 "Immobilisations" (avec des types existants)
2. Cliquer sur le bouton "↻ Réinitialiser"
3. Vérifier le popup de confirmation

### Résultat attendu
- ✅ Un popup de confirmation s'affiche avec le message : "Attention, toutes les données d'amortissement vont être supprimées. Cette action est irréversible. Êtes-vous sûr ?"
- ✅ Le popup contient les boutons "OK" et "Annuler"

---

## Test 6: Annulation de la réinitialisation

### Étapes
1. Sélectionner le Level 2 "Immobilisations" (avec des types existants)
2. Cliquer sur le bouton "↻ Réinitialiser"
3. Dans le popup, cliquer sur "Annuler"
4. Vérifier que rien n'a changé

### Résultat attendu
- ✅ Le popup se ferme
- ✅ Les types d'amortissement restent inchangés dans le tableau
- ✅ Les données en base de données restent inchangées

---

## Test 7: Réinitialisation complète (confirmation OK)

### Étapes
1. Sélectionner le Level 2 "Immobilisations"
2. Modifier quelques types (ajouter des Level 1, modifier des durées, etc.)
3. Noter les IDs et noms des types actuels
4. Cliquer sur le bouton "↻ Réinitialiser"
5. Dans le popup, cliquer sur "OK"
6. Attendre la fin de l'opération
7. Vérifier le tableau
8. Vérifier la base de données

### Résultat attendu
- ✅ Le popup se ferme
- ✅ Un message de chargement peut apparaître brièvement
- ✅ Le tableau se recharge automatiquement
- ✅ **TOUS les types de TOUS les Level 2 sont supprimés de la base de données**
- ✅ **Les 7 types par défaut sont créés avec des valeurs vides** pour le Level 2 "Immobilisations" :
  - "Part terrain"
  - "Immobilisation structure/GO"
  - "Immobilisation mobilier"
  - "Immobilisation IGT"
  - "Immobilisation agencements"
  - "Immobilisation Facade/Toiture"
  - "Immobilisation travaux"
- ✅ Chaque type a les valeurs suivantes :
  - `level_1_values` : `[]` (vide)
  - `start_date` : `null`
  - `duration` : `0.0`
  - `annual_amount` : `null`
- ✅ Les types sont triés par nom dans le tableau
- ✅ Les IDs des types ont changé (nouveaux types créés)

---

## Test 8: Vérification en base de données

### Étapes
1. Après une réinitialisation, exécuter :
```bash
python3 backend/scripts/check_amortization_types.py
```

### Résultat attendu
- ✅ Seuls les 7 types par défaut existent pour "Immobilisations"
- ✅ Aucun type n'existe pour d'autres Level 2
- ✅ Tous les types ont des valeurs vides (level_1_values = [], duration = 0.0, etc.)

---

## Test 9: Réinitialisation lors du changement de Level 2

### Étapes
1. Sélectionner le Level 2 "Immobilisations"
2. Modifier quelques types (ajouter des Level 1, modifier des durées, etc.)
3. Noter les modifications
4. Sélectionner un autre Level 2 (ex: "Assurance")
5. Vérifier ce qui se passe
6. Re-sélectionner "Immobilisations"
7. Vérifier le tableau

### Résultat attendu
- ✅ **Lors du changement de Level 2, la réinitialisation est automatiquement déclenchée** (sans popup)
- ✅ Tous les types sont supprimés
- ✅ Les 7 types par défaut sont recréés avec des valeurs vides pour le nouveau Level 2 sélectionné
- ✅ Le tableau se recharge automatiquement
- ✅ Si on re-sélectionne "Immobilisations", les types par défaut sont recréés pour "Immobilisations"

---

## Test 10: Gestion d'erreur

### Étapes
1. Arrêter le serveur backend
2. Sélectionner le Level 2 "Immobilisations" (avec des types existants)
3. Cliquer sur le bouton "↻ Réinitialiser"
4. Dans le popup, cliquer sur "OK"
5. Vérifier le comportement

### Résultat attendu
- ✅ Une alerte d'erreur s'affiche avec un message d'erreur
- ✅ Les types dans le tableau restent inchangés
- ✅ Les données en base de données restent inchangées

---

## Test 11: Console logs

### Étapes
1. Ouvrir la console du navigateur (F12)
2. Sélectionner le Level 2 "Immobilisations"
3. Cliquer sur le bouton "↻ Réinitialiser"
4. Dans le popup, cliquer sur "OK"
5. Vérifier les logs dans la console

### Résultat attendu
- ✅ Les logs suivants apparaissent :
  - `[AmortizationConfigCard] Réinitialisation des types d'amortissement pour Level 2: Immobilisations...`
  - `[AmortizationConfigCard] ✓ Tous les types supprimés`
  - `[AmortizationConfigCard] ✓ 7 types par défaut recréés avec valeurs vides`

---

## Notes
- ⚠️ **IMPORTANT** : La réinitialisation supprime **TOUS les types de TOUS les Level 2** (toute la table)
- ⚠️ **IMPORTANT** : Cette action est irréversible
- ⚠️ **IMPORTANT** : Les `AmortizationResult` associés sont également supprimés
- Le bouton ne fonctionne que si des types existent déjà pour le Level 2 sélectionné
- Le changement de Level 2 déclenche automatiquement la même réinitialisation (sans popup)

