# Test manuel de l'API Client pour les vues d'amortissement

## Instructions

1. Démarrer le serveur backend : `python3 -m uvicorn backend.api.main:app --reload`
2. Démarrer le frontend : `npm run dev`
3. Ouvrir la console du navigateur (F12) sur la page Amortissements
4. Exécuter les commandes suivantes dans la console :

## Tests

### Test 1: Lister les vues (sans filtre)
```javascript
import { amortizationViewsAPI } from './src/api/client';
const views = await amortizationViewsAPI.getAll();
console.log('✅ Vues récupérées:', views);
```

### Test 2: Lister les vues (avec filtre Level 2)
```javascript
const views = await amortizationViewsAPI.getAll('ammortissements');
console.log('✅ Vues pour "ammortissements":', views);
```

### Test 3: Créer une vue
```javascript
const newView = await amortizationViewsAPI.create({
  name: 'Test View',
  level_2_value: 'ammortissements',
  view_data: {
    level_2_value: 'ammortissements',
    amortization_types: [
      {
        name: 'Part terrain',
        level_1_values: ['Caution entree'],
        start_date: '2024-01-01',
        duration: 30,
        annual_amount: 1000
      }
    ]
  }
});
console.log('✅ Vue créée:', newView);
```

### Test 4: Récupérer une vue par ID
```javascript
// Utiliser l'ID de la vue créée dans Test 3
const view = await amortizationViewsAPI.getById(1);
console.log('✅ Vue récupérée:', view);
```

### Test 5: Mettre à jour une vue
```javascript
const updated = await amortizationViewsAPI.update(1, {
  name: 'Test View Updated'
});
console.log('✅ Vue mise à jour:', updated);
```

### Test 6: Supprimer une vue
```javascript
await amortizationViewsAPI.delete(1);
console.log('✅ Vue supprimée');
```

## Test via l'import direct (si disponible)

Si vous avez accès à l'API directement dans la console :

```javascript
// Dans la console du navigateur, après avoir importé le module
const API = await import('/src/api/client.ts');
const views = await API.amortizationViewsAPI.getAll('ammortissements');
console.log(views);
```

## Résultats attendus

- ✅ Tous les appels API doivent retourner des données valides
- ✅ Pas d'erreurs dans la console
- ✅ Les types TypeScript sont corrects (pas d'erreurs de compilation)

