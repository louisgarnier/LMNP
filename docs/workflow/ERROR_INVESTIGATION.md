# Best Practices - Investigation d'Erreurs

## ⚠️ CRITICAL: Lire avant de résoudre une erreur

Ce document contient les leçons apprises lors de l'investigation d'erreurs complexes, notamment les problèmes de récursion avec Pydantic.

---

## 🎯 Principes Fondamentaux

### 1. **Simplifier AVANT de Complexifier**

**❌ MAUVAISE APPROCHE :**
- Ajouter des solutions complexes (forward references, `model_rebuild()`, `from __future__ import annotations`)
- Chercher des solutions avancées avant d'avoir testé la version simple

**✅ BONNE APPROCHE :**
- Créer d'abord une version minimale qui fonctionne
- Ajouter progressivement les fonctionnalités
- Tester à chaque étape

**Exemple :**
```python
# ❌ Commencer avec tout
class LoanPaymentBase(BaseModel):
    date: date = Field(..., description="Date de la mensualité")
    capital: float = Field(..., description="Montant du capital remboursé")
    # ... beaucoup de descriptions

# ✅ Commencer simple
class LoanPaymentBase(BaseModel):
    date: date
    capital: float
    # Ajouter les descriptions après avoir vérifié que ça fonctionne
```

---

### 2. **Comparer avec le Code Existant**

**❌ MAUVAISE APPROCHE :**
- Créer du nouveau code sans regarder comment c'est fait ailleurs
- Supposer que tous les patterns fonctionnent de la même manière

**✅ BONNE APPROCHE :**
- Chercher des exemples similaires dans le codebase
- Copier exactement le pattern qui fonctionne
- Ne dévier que si nécessaire et après avoir testé

**Exemple :**
```python
# Regarder comment TransactionListResponse est défini
class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]  # Pas de forward reference
    total: int
    page: int = 1
    page_size: int = 100

# Utiliser le même pattern pour LoanPaymentListResponse
class LoanPaymentListResponse(BaseModel):
    items: List[LoanPaymentResponse]  # Même pattern
    total: int
    page: int = 1
    page_size: int = 100
```

---

### 3. **Tester Progressivement**

**❌ MAUVAISE APPROCHE :**
- Créer tous les modèles d'un coup
- Tester seulement à la fin
- Ne pas savoir quel modèle cause le problème

**✅ BONNE APPROCHE :**
- Créer un modèle à la fois
- Tester après chaque ajout
- Identifier immédiatement le modèle problématique

**Exemple :**
```python
# Étape 1 : Créer LoanPaymentBase seul
class LoanPaymentBase(BaseModel):
    date: date
    capital: float
# Test : from backend.api.models import LoanPaymentBase

# Étape 2 : Ajouter LoanPaymentResponse
class LoanPaymentResponse(LoanPaymentBase):
    id: int
# Test : from backend.api.models import LoanPaymentResponse

# Étape 3 : Ajouter LoanPaymentListResponse
class LoanPaymentListResponse(BaseModel):
    items: List[LoanPaymentResponse]
# Test : from backend.api.models import LoanPaymentListResponse
```

---

### 4. **Isoler le Problème**

**❌ MAUVAISE APPROCHE :**
- Modifier plusieurs choses en même temps
- Ne pas savoir quelle modification cause le problème
- Faire des suppositions sans vérifier

**✅ BONNE APPROCHE :**
- Tester si le problème existait avant vos modifications
- Utiliser `git stash` pour isoler vos changements
- Vérifier chaque hypothèse une par une

**Exemple :**
```bash
# Tester si le problème existait avant
git stash
python3 -c "from backend.api.models import TransactionBase"
# Si ça fonctionne, le problème vient de vos modifications

# Restaurer et tester progressivement
git stash pop
# Tester chaque modèle un par un
```

---

### 5. **Ne Pas Casser l'Application**

**❌ MAUVAISE APPROCHE :**
- Continuer à modifier même si l'app ne fonctionne plus
- Ne pas restaurer immédiatement si l'app est cassée
- Essayer plusieurs solutions complexes en même temps

**✅ BONNE APPROCHE :**
- **TOUJOURS** restaurer immédiatement si l'app est cassée
- Utiliser `git checkout` pour revenir à l'état fonctionnel
- Recommencer avec une approche plus simple

**Exemple :**
```bash
# Si l'app ne fonctionne plus, restaurer IMMÉDIATEMENT
git checkout backend/api/models.py

# Vérifier que ça fonctionne
python3 -c "from backend.api.models import TransactionBase"

# Recommencer avec une approche plus simple
```

---

## 🔍 Processus d'Investigation Systématique

### Étape 1 : Comprendre l'Erreur
1. Lire l'erreur complète (pas juste le type)
2. Identifier où elle se produit (import, création, utilisation)
3. Vérifier si c'est une erreur connue (recherche web si nécessaire)

### Étape 2 : Isoler le Problème
1. Tester si le problème existait avant vos modifications
2. Identifier le code exact qui cause le problème
3. Créer un test minimal qui reproduit l'erreur

### Étape 3 : Comparer avec le Code Existant
1. Chercher des exemples similaires dans le codebase
2. Copier exactement le pattern qui fonctionne
3. Ne dévier que si absolument nécessaire

### Étape 4 : Simplifier
1. Retirer toutes les fonctionnalités non essentielles
2. Créer une version minimale qui fonctionne
3. Ajouter progressivement les fonctionnalités

### Étape 5 : Tester à Chaque Étape
1. Tester après chaque modification
2. Ne pas accumuler plusieurs changements non testés
3. Utiliser des tests simples et rapides

---

## 🚨 Erreurs Courantes à Éviter

### 1. **Récursion avec Pydantic**

**Symptôme :** `RecursionError: maximum recursion depth exceeded` lors de l'import

**Causes possibles :**
- Forward references mal gérées
- Descriptions dans `Field()` qui causent des problèmes
- Ordre de définition des modèles
- Interaction entre plusieurs modèles

**Solution :**
1. Simplifier les modèles (retirer les descriptions)
2. Utiliser le même pattern que les modèles existants
3. Tester un modèle à la fois

### 2. **Modifications qui Cassent l'App**

**Symptôme :** L'application ne démarre plus ou ne fonctionne plus

**Solution immédiate :**
```bash
# Restaurer le fichier problématique
git checkout <fichier>

# Vérifier que ça fonctionne
# Recommencer avec une approche plus simple
```

### 3. **Tourner en Rond**

**Symptôme :** Essayer plusieurs solutions complexes sans résultat

**Solution :**
1. **ARRÊTER** immédiatement
2. Restaurer à l'état fonctionnel
3. Recommencer avec une approche plus simple
4. Tester progressivement

---

## 📝 Checklist Avant de Modifier du Code

- [ ] J'ai lu le code existant pour comprendre le pattern
- [ ] J'ai trouvé des exemples similaires dans le codebase
- [ ] Je vais créer une version minimale d'abord
- [ ] Je vais tester après chaque modification
- [ ] Je sais comment restaurer si ça casse
- [ ] Je ne vais pas ajouter de complexité inutile

---

## 🎓 Leçons Apprises (Cas Réel : Pydantic Récursion)

### Ce qui s'est passé :
1. Création de modèles Pydantic avec descriptions dans `Field()`
2. Récursion infinie lors de l'import du module
3. Tentatives de solutions complexes (forward references, `model_rebuild()`, etc.)
4. Application cassée
5. Solution : simplification en retirant les descriptions

### Ce qui aurait dû être fait :
1. ✅ Regarder comment `TransactionListResponse` est défini
2. ✅ Créer une version minimale sans descriptions
3. ✅ Tester après chaque ajout
4. ✅ Restaurer immédiatement quand l'app est cassée
5. ✅ Recommencer avec une approche plus simple

### Résultat :
- Temps perdu : ~30 minutes à tourner en rond
- Temps avec bonne approche : ~5 minutes
- **Leçon : Simplifier AVANT de complexifier**

---

## 🔧 Outils de Vérification

### Script de Vérification Frontend

Un script `docs/workflow/check_frontend_errors.js` a été créé pour vérifier automatiquement :
- ✅ Erreurs de compilation TypeScript
- ✅ Erreurs ESLint
- ✅ Exports manquants
- ✅ Composants manquants
- ✅ Client API valide

**Usage :**
```bash
node docs/workflow/check_frontend_errors.js
```

**⚠️ IMPORTANT :** Toujours exécuter ce script avant de dire que le code est "OK". Ne jamais affirmer que tout fonctionne sans avoir vérifié.

### Script de Vérification des Exports

Un script `scripts/verify_exports.js` vérifie que tous les imports correspondent à des exports existants.

**Usage :**
```bash
node scripts/verify_exports.js
```

---

## ⚠️ INCIDENT (2026-07-10) : `test_database_complete.py` vide la base de PRODUCTION

**Contexte :** Tâche 4 (fix `loan_start_date` Evry). Après avoir corrigé
`calculate_capital_restant_du` et écrit un nouveau test isolé
(`backend/tests/test_capital_restant_du.py`, harnais Tâche 3 —
`db_session`/`client`, base SQLite en mémoire), j'ai lancé par précaution
d'autres fichiers de tests "liés" pour détecter des régressions :

```bash
python3 -m pytest backend/tests/test_capital_restant_du.py \
    backend/tests/test_database_complete.py \
    backend/tests/test_conftest_isolation.py -v
```

**Ce qui s'est passé :** `test_database_complete.py::test_complete_workflow`
n'utilise PAS les fixtures isolées de la Tâche 3. Il appelle
`next(get_db())` (donc `SessionLocal`/le moteur de PRODUCTION,
`backend/database/lmnp.db`) et exécute en tout début de test :

```python
db.query(ConsolidatedFinancialStatement).delete()
db.query(FinancialStatement).delete()
db.query(Amortization).delete()
db.query(EnrichedTransaction).delete()
db.query(Transaction).delete()
db.query(Mapping).delete()
db.query(Parameter).delete()
```

Résultat : les 880 lignes de `transactions`/`enriched_transactions` de la
base de PRODUCTION (604 Evry + 216 mars + 60 mars colloc) ont été
supprimées et remplacées par les 4 lignes du scénario de test. Détecté
immédiatement car le bilan Evry est passé de valeurs réelles à
`actif_total = 0`.

**Pourquoi ce n'était pas totalement imprévisible :** le docstring de
`backend/tests/conftest.py` (Tâche 3, lignes 17-19) prévient explicitement
que *"les 46 fichiers de tests existants qui importent directement
`SessionLocal` / `init_database` continuent de fonctionner tels quels"* —
c.-à-d. qu'ils touchent la vraie base. Je ne l'ai pas vérifié avant de
lancer ce fichier précis.

**Récupération :** restauration complète de `backend/database/lmnp.db`
depuis le backup pris en Step 1 de la Tâche 4
(`backups/lmnp_2026-07-10_1651_avant-fix-pret.db`, antérieur à
l'incident), puis ré-application du script `fix_loan_start_dates.py`
(idempotent) pour ré-obtenir l'état corrigé de `loan_configs`. Vérifié :
604/216/60 transactions restaurées, bilan Evry 2022-2025 équilibré
(écart ≤ 0,01 €), capital restant dû 2025 = 194 613,53 € (conforme à
l'ancre attendue).

**Règle de prévention :**
- ⚠️ **NE JAMAIS** exécuter `backend/tests/test_database_complete.py` (ni
  aucun autre fichier de tests qui appelle `get_db()`/`SessionLocal`
  directement sans passer par les fixtures `db_session`/`client` de
  `conftest.py`) tant qu'il n'a pas été migré vers le harnais isolé de la
  Tâche 3. Avant de lancer un fichier de test "pour vérifier les
  régressions", **grep d'abord** ce fichier pour `SessionLocal|get_db()`
  sans `db_session`/`client` en paramètre de fixture — si trouvé, ne pas
  l'exécuter sans isolation supplémentaire (ou l'exécuter uniquement après
  un backup frais de `lmnp.db`).
- Toujours reprendre un backup **juste avant** toute commande qui touche la
  base de production, même une commande "de vérification" a priori
  read-only (ex: lancer une suite de tests).

---

## 🔗 Références

- [BEST_PRACTICES.md](./BEST_PRACTICES.md) - Pratiques générales du projet
- [GIT_WORKFLOW.md](./GIT_WORKFLOW.md) - Workflow Git

---

**Dernière mise à jour :** 2026-01-11  
**Cas d'étude :** Récursion Pydantic avec modèles LoanPayment
