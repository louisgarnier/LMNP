# Phase 12 : Authentification (Mono-utilisateur)

**Status**: ⏳ À FAIRE  
**Environnement**: Local uniquement  
**Durée estimée**: 1-2 semaines

## Objectif

Implémenter un système d'authentification simple et sécurisé pour un seul utilisateur. Permettre la connexion avec email/password et protéger toutes les routes de l'application.

## Vue d'ensemble

Cette phase implique :
- Création d'une table `users` pour stocker l'utilisateur
- Implémentation de JWT pour l'authentification
- Protection de tous les endpoints backend
- Création d'une page de login
- Protection des routes frontend
- Stockage du token (localStorage ou cookie httpOnly)

## Étapes principales

### Step 12.1 : Backend - Table et modèle User
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer la table `users` dans la base de données
- [ ] Créer le modèle SQLAlchemy `User`
- [ ] Ajouter les champs : id, email (unique), hashed_password, created_at, updated_at
- [ ] Créer une migration pour la table
- [ ] Créer un script pour créer l'utilisateur initial

**Deliverables**:
- Table `users` créée
- Modèle `User` dans `backend/database/models.py`
- Migration créée et testée
- Script de création d'utilisateur initial

---

### Step 12.2 : Backend - Utilitaires d'authentification
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Installer les dépendances (python-jose, passlib, bcrypt)
- [ ] Créer des fonctions utilitaires :
  - Hash password (bcrypt)
  - Verify password
  - Create JWT token
  - Decode JWT token
- [ ] Configurer les variables d'environnement (JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION)

**Deliverables**:
- Utilitaires d'authentification créés
- Variables d'environnement configurées
- Tests des fonctions utilitaires

---

### Step 12.3 : Backend - Endpoints d'authentification
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer les endpoints :
  - POST /api/auth/register (créer un utilisateur - optionnel pour mono-user)
  - POST /api/auth/login (email + password → JWT)
  - POST /api/auth/logout (invalider le token - optionnel)
  - GET /api/auth/me (vérifier le token actuel, retourner l'utilisateur)
- [ ] Créer les modèles Pydantic (LoginRequest, LoginResponse, UserResponse)
- [ ] Implémenter la logique de login (vérifier email/password, générer JWT)
- [ ] Tester tous les endpoints

**Deliverables**:
- Endpoints d'authentification fonctionnels
- Modèles Pydantic créés
- Tests validés

---

### Step 12.4 : Backend - Middleware de protection des endpoints
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer une dépendance FastAPI pour vérifier le JWT
- [ ] Extraire le token depuis le header Authorization
- [ ] Vérifier et décoder le token
- [ ] Retourner l'utilisateur si valide, erreur 401 si invalide
- [ ] Appliquer la dépendance à tous les endpoints (sauf /api/auth/*)

**Deliverables**:
- Middleware de protection créé
- Tous les endpoints protégés (sauf auth)
- Tests validés

---

### Step 12.5 : Backend - Rate limiting (optionnel mais recommandé)
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Installer slowapi ou similar
- [ ] Limiter les tentatives de login (ex: 5 par minute)
- [ ] Protéger contre les attaques brute force
- [ ] Tester le rate limiting

**Deliverables**:
- Rate limiting configuré
- Protection contre brute force
- Tests validés

---

### Step 12.6 : Frontend - API Client pour l'authentification
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Ajouter les fonctions API dans `frontend/src/api/client.ts`
  - login(email, password)
  - logout()
  - getCurrentUser()
- [ ] Modifier fetchAPI pour inclure le token dans les headers
- [ ] Gérer les erreurs 401 (redirection vers login)
- [ ] Créer les interfaces TypeScript

**Deliverables**:
- API client d'authentification fonctionnel
- Token inclus dans tous les appels API
- Gestion des erreurs 401

---

### Step 12.7 : Frontend - Contexte d'authentification
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer un contexte React pour l'authentification
- [ ] Stocker le token dans localStorage (ou cookie httpOnly)
- [ ] Gérer l'état de l'utilisateur (connecté/déconnecté)
- [ ] Fournir des fonctions : login, logout, isAuthenticated

**Deliverables**:
- Contexte d'authentification créé
- Token stocké et géré
- État d'authentification géré

---

### Step 12.8 : Frontend - Page de login
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer une page de login (`/login`)
- [ ] Formulaire email/password
- [ ] Validation des champs
- [ ] Appel API de login
- [ ] Stockage du token après login réussi
- [ ] Redirection vers l'app après login
- [ ] Gestion des erreurs (mauvais credentials)

**Deliverables**:
- Page de login créée
- Formulaire fonctionnel
- Redirection après login

---

### Step 12.9 : Frontend - Protection des routes
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Créer un composant/middleware pour protéger les routes
- [ ] Vérifier le token au chargement de l'app
- [ ] Rediriger vers /login si non authentifié
- [ ] Protéger toutes les pages (sauf /login)
- [ ] Gérer l'expiration du token

**Deliverables**:
- Routes protégées
- Redirection automatique si non authentifié
- Gestion de l'expiration du token

---

### Step 12.10 : Frontend - Bouton de déconnexion
**Status**: ⏳ À FAIRE

**Tasks**:
- [ ] Ajouter un bouton de déconnexion dans la navigation
- [ ] Implémenter la fonction de logout
- [ ] Supprimer le token
- [ ] Rediriger vers /login

**Deliverables**:
- Bouton de déconnexion fonctionnel
- Logout implémenté

---

## Notes techniques

### JWT
- Algorithme : HS256
- Expiration : 24h (configurable)
- Secret key : variable d'environnement (très longue et aléatoire)

### Stockage du token
- Option recommandée : localStorage (simple pour commencer)
- Alternative : cookie httpOnly (plus sécurisé, nécessite configuration CORS)

### Sécurité
- Hash password avec bcrypt (salt rounds: 12)
- HTTPS obligatoire en production
- Rate limiting sur /api/auth/login
- Protection CSRF (si cookie httpOnly)

### Variables d'environnement
```env
JWT_SECRET_KEY=<clé secrète très longue et aléatoire>
JWT_ALGORITHM=HS256
JWT_EXPIRATION=24h
```

## Tests

- [ ] Création d'utilisateur initial
- [ ] Login avec bonnes credentials
- [ ] Login avec mauvaises credentials
- [ ] Accès aux endpoints protégés avec token valide
- [ ] Accès aux endpoints protégés sans token (erreur 401)
- [ ] Expiration du token
- [ ] Logout
- [ ] Protection des routes frontend

## Livrables finaux

- [ ] Table `users` créée
- [ ] Utilitaires d'authentification créés
- [ ] Endpoints d'authentification fonctionnels
- [ ] Tous les endpoints protégés
- [ ] API client d'authentification
- [ ] Contexte d'authentification
- [ ] Page de login
- [ ] Routes protégées
- [ ] Bouton de déconnexion
- [ ] Tests validés

---

**Dernière mise à jour**: [Date]
