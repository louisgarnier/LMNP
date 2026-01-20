# Phase 13 : Dashboards de Reporting

**Status**: ⏳ À FAIRE  
**Environnement**: Local uniquement  
**Durée estimée**: 2-3 semaines

## Objectif

Créer des dashboards de reporting pour chaque propriété avec des métriques clés (cashflow, rentabilité, ROI, etc.) et des visualisations graphiques.

## Vue d'ensemble

Cette phase implique :
- Création d'endpoints backend pour calculer les métriques
- Création d'une page "Vue d'ensemble" dans le frontend
- Affichage de cards avec métriques clés
- Graphiques pour visualiser les données dans le temps
- Comparaison entre propriétés (si plusieurs)

## Étapes principales

### Step 13.1 : Backend - Endpoints de métriques (Cashflow)
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer un endpoint GET /api/metrics/cashflow
- [ ] Paramètres : property_id, start_date, end_date
- [ ] Calculer le cashflow mensuel (revenus - charges)
- [ ] Retourner les données par mois
- [ ] Tester l'endpoint

**Deliverables**:
- Endpoint cashflow fonctionnel
- Calculs corrects
- Tests validés

---

### Step 13.2 : Backend - Endpoints de métriques (Rentabilité)
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer un endpoint GET /api/metrics/rentability
- [ ] Paramètres : property_id, year
- [ ] Calculer :
  - Revenus locatifs annuels
  - Charges déductibles
  - Résultat net
  - Taux de rentabilité (ROI)
- [ ] Retourner les métriques
- [ ] Tester l'endpoint

**Deliverables**:
- Endpoint rentabilité fonctionnel
- Calculs corrects
- Tests validés

---

### Step 13.3 : Backend - Endpoints de métriques (ROI)
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer un endpoint GET /api/metrics/roi
- [ ] Paramètres : property_id, year
- [ ] Calculer :
  - Investissement initial
  - Revenus cumulés
  - ROI en pourcentage
  - ROI annualisé
- [ ] Retourner les métriques
- [ ] Tester l'endpoint

**Deliverables**:
- Endpoint ROI fonctionnel
- Calculs corrects
- Tests validés

---

### Step 13.4 : Backend - Endpoints de métriques (Synthèse)
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer un endpoint GET /api/metrics/summary
- [ ] Paramètres : property_id, year (optionnel)
- [ ] Retourner un résumé de toutes les métriques :
  - Cashflow mensuel moyen
  - Rentabilité annuelle
  - ROI
  - Dettes restantes
  - Amortissements cumulés
- [ ] Tester l'endpoint

**Deliverables**:
- Endpoint synthèse fonctionnel
- Toutes les métriques calculées
- Tests validés

---

### Step 13.5 : Frontend - API Client pour les métriques
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Ajouter les fonctions API dans `frontend/src/api/client.ts`
  - getCashflow(propertyId, startDate, endDate)
  - getRentability(propertyId, year)
  - getROI(propertyId, year)
  - getSummary(propertyId, year)
- [ ] Créer les interfaces TypeScript
- [ ] Tester les appels API

**Deliverables**:
- API client fonctionnel
- Interfaces TypeScript créées

---

### Step 13.6 : Frontend - Page "Vue d'ensemble"
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer une page "Vue d'ensemble" (`/dashboard/overview`)
- [ ] Ajouter un sélecteur de propriété
- [ ] Ajouter un sélecteur d'année (optionnel)
- [ ] Layout avec sections pour différentes métriques
- [ ] Tester la page

**Deliverables**:
- Page "Vue d'ensemble" créée
- Sélecteurs fonctionnels

---

### Step 13.7 : Frontend - Cards de métriques
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer des composants de cards pour afficher les métriques
- [ ] Cards à créer :
  - Cashflow mensuel moyen
  - Rentabilité annuelle
  - ROI
  - Dettes restantes
  - Amortissements cumulés
- [ ] Style cohérent avec le reste de l'app
- [ ] Affichage des valeurs avec formatage (€, %)

**Deliverables**:
- Cards de métriques créées
- Style cohérent
- Formatage correct

---

### Step 13.8 : Frontend - Graphique Cashflow (ligne)
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Installer une librairie de graphiques (Chart.js, Recharts, ou D3.js)
- [ ] Créer un composant de graphique en ligne
- [ ] Afficher le cashflow mensuel dans le temps
- [ ] Ajouter des tooltips
- [ ] Style cohérent

**Deliverables**:
- Graphique cashflow fonctionnel
- Visualisation claire

---

### Step 13.9 : Frontend - Graphique Rentabilité (barres)
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer un composant de graphique en barres
- [ ] Afficher la rentabilité par année
- [ ] Comparer revenus vs charges
- [ ] Ajouter des tooltips
- [ ] Style cohérent

**Deliverables**:
- Graphique rentabilité fonctionnel
- Visualisation claire

---

### Step 13.10 : Frontend - Tableau de synthèse
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer un tableau de synthèse
- [ ] Afficher les métriques clés par année
- [ ] Permettre la comparaison entre années
- [ ] Style cohérent

**Deliverables**:
- Tableau de synthèse créé
- Comparaison possible

---

### Step 13.11 : Frontend - Comparaison entre propriétés (optionnel)
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Permettre la sélection de plusieurs propriétés
- [ ] Afficher les métriques côte à côte
- [ ] Graphiques comparatifs
- [ ] Tableau comparatif

**Deliverables**:
- Comparaison entre propriétés fonctionnelle
- Visualisations comparatives

---

## Notes techniques

### Librairies de graphiques recommandées
- **Recharts** : Simple, React-native, bonne documentation
- **Chart.js** : Populaire, beaucoup d'options
- **D3.js** : Puissant mais plus complexe

### Métriques à calculer
- Cashflow mensuel (revenus - charges)
- Rentabilité annuelle (revenus - charges) / investissement
- ROI (retour sur investissement)
- Dettes restantes
- Amortissements cumulés
- Taux de rendement

### Performance
- Cache des calculs côté backend si possible
- Pagination pour les données historiques
- Lazy loading des graphiques

## Tests

- [ ] Calculs de métriques corrects
- [ ] Graphiques affichés correctement
- [ ] Sélection de propriété fonctionne
- [ ] Sélection d'année fonctionne
- [ ] Comparaison entre propriétés (si implémentée)
- [ ] Performance acceptable

## Livrables finaux

- [ ] Endpoints de métriques créés
- [ ] API client fonctionnel
- [ ] Page "Vue d'ensemble" créée
- [ ] Cards de métriques affichées
- [ ] Graphiques fonctionnels
- [ ] Tableau de synthèse créé
- [ ] Comparaison entre propriétés (optionnel)
- [ ] Tests validés

---

**Dernière mise à jour**: [Date]
