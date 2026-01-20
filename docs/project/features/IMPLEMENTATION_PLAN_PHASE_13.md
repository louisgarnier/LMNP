# Phase 13 : Dashboards de Reporting

**Status**: ⏳ À FAIRE  
**Environnement**: Local uniquement  
**Durée estimée**: 2-3 semaines

## Objectif

Créer des dashboards de reporting pour chaque propriété avec des métriques clés (cashflow, rentabilité, ROI, etc.) et des visualisations graphiques. Inclure également des dashboards mixtes pour agréger les données de plusieurs propriétés (ex: somme de tous les crédits, total de tous les résultats pour liasse fiscale).

## Vue d'ensemble

Cette phase implique :
- Création d'endpoints backend pour calculer les métriques par propriété
- Création d'endpoints backend pour calculer les métriques agrégées (multi-propriétés)
- Création d'une page "Vue d'ensemble" dans le frontend
- Affichage de cards avec métriques clés
- Graphiques pour visualiser les données dans le temps
- Dashboards par propriété (isolation)
- Dashboards mixtes (agrégation de plusieurs propriétés)

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

### Step 13.11 : Backend - Endpoints de métriques agrégées (multi-propriétés)
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer un endpoint GET /api/metrics/loans/aggregated
- [ ] Paramètres : property_ids (array) ou "all"
- [ ] Calculer la somme de tous les crédits des propriétés sélectionnées
- [ ] Retourner les données agrégées
- [ ] Créer un endpoint GET /api/metrics/compte-resultat/aggregated
- [ ] Paramètres : property_ids (array) ou "all", year
- [ ] Calculer le total de tous les résultats des propriétés sélectionnées (pour liasse fiscale)
- [ ] Retourner les données agrégées
- [ ] Créer des scripts de test pour valider les endpoints
- [ ] Tester les endpoints

**Deliverables**:
- Endpoints agrégés fonctionnels
- Calculs corrects
- Scripts de test : `backend/scripts/test_aggregated_metrics_step13_11.py`
- Tests validés

**Tests**:
- [ ] GET /api/metrics/loans/aggregated retourne la somme de tous les crédits
- [ ] GET /api/metrics/compte-resultat/aggregated retourne le total de tous les résultats
- [ ] Filtrage par property_ids fonctionne
- [ ] Option "all" retourne toutes les propriétés
- [ ] Calculs corrects

---

### Step 13.12 : Frontend - Dashboards mixtes (agrégation multi-propriétés)
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer une section "Vue globale" dans la page "Vue d'ensemble"
- [ ] Permettre la sélection de plusieurs propriétés (ou "Toutes")
- [ ] Afficher les métriques agrégées :
  - Somme de tous les crédits
  - Total de tous les résultats (liasse fiscale)
- [ ] Graphiques comparatifs entre propriétés
- [ ] Tableau comparatif
- [ ] Ajouter des validations frontend
- [ ] Tester manuellement

**Deliverables**:
- Section "Vue globale" créée
- Sélection multiple de propriétés
- Métriques agrégées affichées
- Visualisations comparatives
- Validations frontend implémentées

**Tests**:
- [ ] Sélection de plusieurs propriétés fonctionne
- [ ] Option "Toutes" fonctionne
- [ ] Métriques agrégées affichées correctement
- [ ] Graphiques comparatifs fonctionnels
- [ ] Tableau comparatif fonctionnel
- [ ] Validation : données correctes pour chaque propriété

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

### Tests backend
- [ ] Calculs de métriques corrects (par propriété)
- [ ] Calculs de métriques agrégées corrects (multi-propriétés)
- [ ] Endpoints agrégés fonctionnent
- [ ] Performance acceptable

### Tests frontend
- [ ] Graphiques affichés correctement
- [ ] Sélection de propriété fonctionne
- [ ] Sélection d'année fonctionne
- [ ] Dashboards par propriété fonctionnent
- [ ] Dashboards mixtes fonctionnent
- [ ] Comparaison entre propriétés fonctionne
- [ ] Validation : données correctes affichées

## Livrables finaux

- [ ] Endpoints de métriques créés (par propriété)
- [ ] Endpoints de métriques agrégées créés (multi-propriétés)
- [ ] API client fonctionnel
- [ ] Page "Vue d'ensemble" créée
- [ ] Cards de métriques affichées (par propriété)
- [ ] Graphiques fonctionnels (par propriété)
- [ ] Tableau de synthèse créé (par propriété)
- [ ] Section "Vue globale" créée (dashboards mixtes)
- [ ] Comparaison entre propriétés fonctionnelle
- [ ] Tests validés

---

**Dernière mise à jour**: [Date]
