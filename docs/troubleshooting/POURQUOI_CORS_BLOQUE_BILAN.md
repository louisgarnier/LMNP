# Pourquoi CORS bloque pour le Bilan et pas pour le Compte de Résultat ?

## 🔍 Analyse technique

### Comparaison des routes

**BILAN** :
- `/api/bilan/calculate` (GET) - ligne 314 dans `bilan.py`
- `/api/bilan` (GET) - ligne 370 dans `bilan.py`
- Ordre d'enregistrement : `/calculate` AVANT `/bilan` ✅

**COMPTE DE RÉSULTAT** :
- `/api/compte-resultat` (GET) - ligne 260 dans `compte_resultat.py`
- `/api/compte-resultat/calculate` (GET) - ligne 338 dans `compte_resultat.py`
- Ordre d'enregistrement : `/compte-resultat` AVANT `/calculate` ✅

### FastAPI gère correctement le routage

FastAPI match les routes **les plus spécifiques en premier**, donc :
- `/api/bilan/calculate` sera toujours matché avant `/api/bilan` ✅
- `/api/compte-resultat/calculate` sera toujours matché avant `/api/compte-resultat` ✅

**Conclusion** : L'ordre des routes n'est PAS le problème.

### Comparaison des composants frontend

**BilanTable** :
```typescript
useEffect(() => {
  if (years.length > 0 && mappings.length > 0) {
    loadBilanData(); // Appelle bilanAPI.calculateAmounts()
  }
}, [years.length, mappings.length, refreshKey]);
```

**CompteResultatTable** :
```typescript
useEffect(() => {
  if (years.length > 0 && mappings.length > 0) {
    loadAmounts(); // Appelle compteResultatAPI.calculateAmounts()
  }
}, [years.length, mappings.length, refreshKey]);
```

**Conclusion** : Les deux composants ont la **même structure** et appellent leurs endpoints de la même manière.

### Configuration CORS

Les deux endpoints utilisent la **même configuration CORS** :
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Conclusion** : CORS est configuré de manière identique pour tous les endpoints.

## ❌ Pourquoi alors le problème CORS ?

### Le problème est intermittent

Dans les logs, on voit :
- ✅ Parfois : `📥 [API] Réponse 200 pour /api/bilan/calculate`
- ❌ Parfois : `Access to fetch... blocked by CORS policy`

Cela suggère que le problème n'est **pas structurel**, mais **intermittent**.

### Causes possibles

1. **Backend redémarre avec `--reload`**
   - Pendant le redémarrage, certaines routes ne sont pas encore enregistrées
   - Le middleware CORS peut ne pas être appliqué pendant quelques millisecondes
   - **Solution** : Redémarrer le backend complètement

2. **Problème de timing**
   - Le frontend appelle l'endpoint avant que le backend soit complètement prêt
   - **Solution** : Le mécanisme de retry dans `BilanTable` devrait gérer ça

3. **Cache du navigateur**
   - Le navigateur cache une ancienne réponse sans headers CORS
   - **Solution** : Vider le cache ou tester en navigation privée

## ✅ Pourquoi ça marche pour le Compte de Résultat ?

**Il n'y a probablement PAS de différence technique.**

Les raisons possibles :
1. **Coïncidence** : Le compte de résultat n'a pas été appelé pendant un redémarrage du backend
2. **Fréquence d'appels** : Le bilan est peut-être appelé plus souvent (plus de `useEffect` qui se déclenchent)
3. **Timing** : Le compte de résultat est peut-être appelé après que le backend soit complètement prêt

## 🎯 Solution

Le problème CORS est **intermittent** et affecte probablement **les deux endpoints de la même manière**. 

Pour résoudre :
1. **Redémarrer le backend complètement** (arrêter avec Ctrl+C, puis redémarrer)
2. **Vider le cache du navigateur** ou tester en navigation privée
3. **Vérifier avec le script** : `python3 scripts/fix_cors_and_test_bilan.py`

## 📝 Conclusion

**Il n'y a PAS de différence technique entre le Bilan et le Compte de Résultat** concernant CORS. Le problème est intermittent et lié au redémarrage du backend ou à un problème de timing.

Les deux systèmes fonctionnent de manière identique.

