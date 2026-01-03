# Différences Bilan vs Compte de Résultat

## Résumé des différences identifiées

### ✅ Différences normales (structure hiérarchique)

1. **Modèles de données** :
   - **Bilan** : `type`, `sub_category`, `is_special`, `special_source`
   - **Compte de résultat** : `level_2_values`, `level_3_values`, `selected_loan_ids`
   - **Raison** : Structure hiérarchique différente (3 niveaux vs 2 niveaux)

2. **Services de calcul** :
   - **Bilan** : `calculate_bilan(year, ...)` → structure hiérarchique complète
   - **Compte de résultat** : `calculate_amounts_by_category_and_year(years, ...)` → dict simple
   - **Raison** : Besoins différents (bilan nécessite totaux par sous-catégorie et type)

### ✅ Pas de différence (fonctionnement identique)

1. **Endpoints** : Les deux ont `/calculate` (GET) - calcul à la volée ✅
2. **API Client** : Les deux ont `calculateAmounts()` ✅
3. **Frontend** : Les deux utilisent `calculateAmounts()` ✅
4. **Format de retour** : Identique `Record<string, Record<string, number>>` ✅
5. **CORS** : Configuré de la même manière ✅

## ❌ Problème identifié : Erreur CORS

### Symptômes
- Erreur dans la console : `Access to fetch at 'http://localhost:8000/api/bilan/calculate?...' from origin 'http://localhost:3000' has been blocked by CORS policy`
- Parfois fonctionne (`📥 [API] Réponse 200`), parfois échoue (erreur CORS)
- Le compte de résultat fonctionne sans problème

### Causes possibles
1. **Backend redémarre** : Avec `--reload`, le backend redémarre et l'endpoint n'est pas disponible pendant quelques millisecondes
2. **Problème de timing** : Le frontend appelle l'endpoint avant que le backend soit complètement prêt
3. **Cache du navigateur** : Le navigateur cache une ancienne réponse sans headers CORS

### Solutions

#### Solution 1 : Vérifier que le backend est démarré
```bash
cd backend && python3 -m uvicorn api.main:app --reload --port 8000
```

#### Solution 2 : Utiliser le script de vérification
```bash
python3 scripts/fix_cors_and_test_bilan.py
```

#### Solution 3 : Redémarrer le backend
Si le problème persiste, redémarrer le backend complètement :
1. Arrêter le backend (Ctrl+C)
2. Redémarrer : `cd backend && python3 -m uvicorn api.main:app --reload --port 8000`

#### Solution 4 : Vider le cache du navigateur
- Chrome/Edge : Ctrl+Shift+Delete → Vider le cache
- Ou ouvrir en navigation privée

## Logs à vérifier

Dans la console du navigateur, vérifier :
1. ✅ `📥 [API] Réponse 200 pour /api/bilan/calculate` → Backend accessible
2. ❌ `Access to fetch... blocked by CORS policy` → Problème CORS
3. ✅ `✅ [BilanTable] Montants calculés pour X année(s)` → Données reçues
4. ✅ `✅ [BilanTable] 1 catégorie(s) à afficher` → Catégories chargées

## Conclusion

**Les deux systèmes fonctionnent de manière identique**. La seule différence est la structure hiérarchique (3 niveaux pour le bilan, 2 pour le compte de résultat).

Le problème CORS est probablement dû à un redémarrage du backend ou à un problème de timing. Si le problème persiste, redémarrer le backend complètement.

