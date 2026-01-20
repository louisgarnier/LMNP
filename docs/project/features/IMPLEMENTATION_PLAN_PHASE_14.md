# Phase 14 : Déploiement en Production (Render)

**Status**: ⏳ À FAIRE  
**Environnement**: Production (Render)  
**Durée estimée**: 1 semaine

## Objectif

Déployer l'application en production sur Render (gratuit) avec HTTPS, sécurité, et configuration appropriée.

## Vue d'ensemble

Cette phase implique :
- Configuration du backend sur Render
- Configuration du frontend sur Vercel
- Configuration des variables d'environnement
- Configuration de la base de données (SQLite ou PostgreSQL)
- Configuration HTTPS
- Tests en production
- Documentation du déploiement

## Prérequis

- Phase 11 (Multi-propriétés) terminée
- Phase 12 (Authentification) terminée
- Phase 13 (Dashboards) terminée
- Compte Render créé
- Compte Vercel créé (ou GitHub pour Vercel)

## Étapes principales

### Step 14.1 : Préparation du backend pour la production
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer un fichier `render.yaml` ou configuration Render
- [ ] Configurer le build command
- [ ] Configurer le start command
- [ ] Vérifier que toutes les dépendances sont dans `requirements.txt`
- [ ] Tester le build localement

**Deliverables**:
- Configuration Render prête
- Build testé localement

---

### Step 14.2 : Configuration de la base de données
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Décider : SQLite (fichier) ou PostgreSQL (service Render)
- [ ] Si SQLite : configurer le chemin du fichier DB (persistent disk)
- [ ] Si PostgreSQL : créer un service PostgreSQL sur Render
- [ ] Configurer la connexion à la DB via variables d'environnement
- [ ] Tester la connexion

**Options**:
- **SQLite** : Simple, gratuit, mais limité (fichier sur disque persistant)
- **PostgreSQL** : Plus robuste, service géré, mais peut nécessiter un plan payant

**Deliverables**:
- Base de données configurée
- Connexion testée

---

### Step 14.3 : Variables d'environnement
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Lister toutes les variables d'environnement nécessaires
  - DATABASE_URL (si PostgreSQL)
  - JWT_SECRET_KEY
  - JWT_ALGORITHM
  - JWT_EXPIRATION
  - API_URL (pour le frontend)
  - CORS_ORIGINS
- [ ] Configurer les variables sur Render
- [ ] Documenter les variables nécessaires

**Deliverables**:
- Variables d'environnement configurées
- Documentation créée

---

### Step 14.4 : Déploiement du backend sur Render
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Connecter le repository GitHub à Render
- [ ] Créer un nouveau service Web Service
- [ ] Configurer :
  - Build command
  - Start command
  - Environment variables
  - Health check path
- [ ] Déployer
- [ ] Vérifier que le service démarre correctement
- [ ] Tester les endpoints

**Deliverables**:
- Backend déployé sur Render
- Service accessible
- Endpoints fonctionnels

---

### Step 14.5 : Configuration CORS
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Configurer CORS dans FastAPI
- [ ] Autoriser uniquement le domaine du frontend
- [ ] Tester les requêtes cross-origin
- [ ] Vérifier que les credentials sont gérés correctement

**Deliverables**:
- CORS configuré
- Requêtes cross-origin fonctionnelles

---

### Step 14.6 : Préparation du frontend pour la production
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer un fichier `vercel.json` si nécessaire
- [ ] Configurer `NEXT_PUBLIC_API_URL` pour pointer vers Render
- [ ] Vérifier que le build fonctionne localement
- [ ] Optimiser les images et assets
- [ ] Vérifier les variables d'environnement

**Deliverables**:
- Configuration Vercel prête
- Build testé localement

---

### Step 14.7 : Déploiement du frontend sur Vercel
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Connecter le repository GitHub à Vercel
- [ ] Configurer :
  - Framework Preset (Next.js)
  - Build command
  - Output directory
  - Environment variables
- [ ] Déployer
- [ ] Vérifier que le site est accessible
- [ ] Tester les fonctionnalités

**Deliverables**:
- Frontend déployé sur Vercel
- Site accessible
- Fonctionnalités testées

---

### Step 14.8 : Configuration HTTPS
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Vérifier que HTTPS est activé sur Render (automatique)
- [ ] Vérifier que HTTPS est activé sur Vercel (automatique)
- [ ] Configurer le domaine personnalisé si nécessaire
- [ ] Vérifier les certificats SSL
- [ ] Tester que tout fonctionne en HTTPS

**Deliverables**:
- HTTPS activé sur Render
- HTTPS activé sur Vercel
- Certificats SSL valides

---

### Step 14.9 : Migration des données (si nécessaire)
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Exporter les données de la base locale
- [ ] Importer les données dans la base de production
- [ ] Vérifier l'intégrité des données
- [ ] Tester avec les données réelles

**Deliverables**:
- Données migrées
- Intégrité vérifiée

---

### Step 14.10 : Tests en production
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Tester toutes les fonctionnalités :
  - Login
  - Gestion des propriétés
  - Transactions
  - Mapping
  - États financiers
  - Dashboards
- [ ] Vérifier les performances
- [ ] Vérifier la sécurité (HTTPS, CORS, etc.)
- [ ] Tester sur différents navigateurs
- [ ] Tester sur mobile (responsive)

**Deliverables**:
- Toutes les fonctionnalités testées
- Performance acceptable
- Sécurité vérifiée

---

### Step 14.11 : Documentation du déploiement
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Documenter les étapes de déploiement
- [ ] Documenter les variables d'environnement
- [ ] Documenter la configuration Render
- [ ] Documenter la configuration Vercel
- [ ] Créer un guide de troubleshooting

**Deliverables**:
- Documentation complète
- Guide de déploiement
- Guide de troubleshooting

---

## Notes techniques

### Render (Backend)
- Plan gratuit disponible
- Le service s'endort après 15 min d'inactivité
- Premier appel après endormissement : 30-60 secondes
- HTTPS automatique
- Variables d'environnement sécurisées

### Vercel (Frontend)
- Plan gratuit (Hobby)
- HTTPS automatique
- Déploiements automatiques depuis GitHub
- Variables d'environnement sécurisées

### Base de données
- **SQLite** : Fichier sur disque persistant (gratuit, simple)
- **PostgreSQL** : Service géré (peut nécessiter un plan payant)

### Sécurité
- HTTPS obligatoire
- Variables d'environnement pour les secrets
- CORS configuré correctement
- Rate limiting (si implémenté)
- Protection CSRF (si cookie httpOnly)

## Checklist de déploiement

- [ ] Backend déployé sur Render
- [ ] Frontend déployé sur Vercel
- [ ] Base de données configurée
- [ ] Variables d'environnement configurées
- [ ] HTTPS activé
- [ ] CORS configuré
- [ ] Données migrées (si nécessaire)
- [ ] Toutes les fonctionnalités testées
- [ ] Performance acceptable
- [ ] Documentation créée

## Troubleshooting

### Problèmes courants
- Service Render qui ne démarre pas : vérifier les logs, les variables d'environnement
- CORS errors : vérifier la configuration CORS, les origines autorisées
- Base de données non accessible : vérifier la connexion, les variables d'environnement
- Frontend ne peut pas appeler l'API : vérifier NEXT_PUBLIC_API_URL

## Livrables finaux

- [ ] Backend déployé sur Render
- [ ] Frontend déployé sur Vercel
- [ ] Base de données configurée
- [ ] HTTPS activé
- [ ] Toutes les fonctionnalités testées
- [ ] Documentation complète
- [ ] Application accessible en production

---

**Dernière mise à jour**: [Date]
