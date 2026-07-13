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

## ⚠️ BUG (Task 4, 2026-07-10) : capital restant dû basé sur une date de config au lieu de l'échéancier réel

**Symptôme :** bilan Evry déséquilibré (ACTIF ≠ PASSIF) pour 2022-2025,
écarts de -2 814,69 € (2022) à -37 201,47 € (2025) sur le PASSIF.

**Cause :** `calculate_capital_restant_du`
(`backend/api/services/bilan_service.py`) décidait qu'un prêt était
« actif » pour l'année N via `LoanConfig.loan_start_date`, un champ de
config saisi séparément de l'échéancier réel des paiements
(`LoanPayment`). Pour Evry, `loan_start_date = 2026-05-08` alors que le
premier `LoanPayment` réel est daté de 2021 — le filtre excluait donc le
prêt de `active_loans` pour toutes les années 2021-2025, et le capital
remboursé n'était jamais déduit du `credit_amount` affiché.

**Fix :** remplacer le filtre sur `LoanConfig.loan_start_date` par une
sous-requête corrélée `exists()` vérifiant au moins un `LoanPayment` daté
`<= 31/12/N`. Puis recaler la donnée elle-même
(`backend/scripts/fix_loan_start_dates.py`, idempotent) :
`loan_start_date = MIN(LoanPayment.date)` par prêt, pour que la config
cesse de diverger de la réalité.

**Règle de prévention :** ne jamais dériver un état métier (« ce prêt
est-il actif à telle date ? ») d'un champ de configuration saisi à la
main quand une source de vérité transactionnelle existe déjà (ici,
l'échéancier `LoanPayment`). Si un nouveau `LoanConfig` est créé, vérifier
immédiatement qu'il a au moins un `LoanPayment` cohérent, ou s'attendre à
ce que le prêt soit traité comme inactif dans tous les calculs bilan.
Voir ADR-002 (`docs/workflow/ADR.md`).

---

## ⚠️ BUG (Task 5, 2026-07-10) : mappings d'amortissement Evry copiés d'un autre gabarit (catégories croisées)

**Symptôme :** aucun symptôme visible côté CR/bilan (les montants
agrégés — annuité totale, base amortissable — étaient déjà corrects), mais
les libellés de catégorie (`amortization_types.name`) d'Evry ne
correspondaient pas à leur `level_1_values` mappé, et 3 types
« orphelins » (`level_1_values == []`) polluaient la table.

**Cause :** `amortization_types` pour Evry (property_id=25) était une
copie défectueuse du gabarit Marseille : les NOMS de composant
(`Immobilisation agencements`, `Immobilisation mobilier`,
`Immobilisation Facade/Toiture`, ...) ne correspondaient plus à la valeur
`level_1` réellement mappée pour ce composant (ex. le type nommé
« agencements » était en réalité mappé sur `level_1 = "Immeuble (hors
terrain)"`, c.-à-d. la construction). Cause racine probable : copie
manuelle du gabarit d'une propriété à l'autre sans réaligner les libellés
sur les catégories `level_1` propres à chaque propriété.

**Fix :** `backend/scripts/fix_amortization_evry.py` recrée 4 types
propres pour Evry, un par catégorie `level_1` réellement documentée
(Terrain 0 an, Immeuble 30 ans, Travaux 10 ans, Mobilier 10 ans, sourcés
depuis `docs/files/appartements/Evry/Immobilisations_Evry.pdf`), avec
`name == level_1_values[0]`, supprime les 3 types orphelins, et régénère
les 108 `amortization_results` avec les bons libellés. **48 diffs golden,
toutes des renommages de catégorie, montant préservé** (voir `ECARTS.md`).

**Règle de prévention :** quand un gabarit `amortization_types` est copié
d'une propriété à une autre (nouvelle propriété, ou correctif), vérifier
systématiquement que `name == level_1_values[0]` (ou au moins qu'ils
désignent le même composant) pour CHAQUE type, et qu'aucun type n'a
`level_1_values == []` (orphelin, jamais mappé à rien). Croiser au moins
un test contre un document source (PDF/Excel d'immobilisations) avant de
considérer la configuration fiable — ne pas se fier au seul fait que les
totaux agrégés (CR, bilan) semblent corrects, car un mauvais libellé de
catégorie peut coexister avec des montants totaux justes (comme ici).

---

## ⚠️ BUG (Task 7, 2026-07-10) : caches CR/Bilan morts (jamais peuplés/jamais invalidés)

**Symptôme :** aucun symptôme utilisateur direct observé (les valeurs
lues restaient justes car un autre chemin de calcul les produisait déjà),
mais un risque latent de désynchronisation : deux tables de cache
(`compte_resultat_data`, `bilan_data`) et un mécanisme d'invalidation
existaient dans le code sans jamais fonctionner.

**Cause :** `bilan_data` n'avait aucun writer dans tout le code (0 ligne
en base). `compte_resultat_data` n'était peuplée que par
`POST /compte-resultat/generate`, jamais appelé par le frontend (aucune
référence à `generate` côté client). Tous les appels d'invalidation
(après création/modification de transaction, mapping, config
d'amortissement, échéance de prêt...) passaient de mauvais arguments
(ex. `invalidate_all_compte_resultat(db)` sans le `property_id`
obligatoire de sa signature) → `TypeError` systématiquement avalée par un
`try/except` loggé (jamais un `except: pass` silencieux, mais un log
noyé parmi d'autres, jamais remonté ni testé).

**Fix :** suppression complète des caches (`CompteResultatData`,
`BilanData`, modèles ORM + tables SQL via
`backend/scripts/drop_cache_tables.py`), des fonctions d'invalidation, et
de tous leurs call sites. Les `GET` plats calculent désormais en direct
(calcul à la lecture, voir ADR-001), avec mémoïsation de requête (pas de
persistance) pour la performance. Golden re-comparé après bascule : zéro
écart.

**Règle de prévention :** un `try/except` autour d'un appel de fonction
métier (ici, l'invalidation de cache) doit soit re-lancer l'exception,
soit être accompagné d'un test qui vérifie explicitement que l'appel
réussit avec les VRAIS arguments de signature — un `except Exception as e:
logger.error(...)` qui avale silencieusement une erreur de signature
(`TypeError` sur un argument manquant) peut masquer un mécanisme
entièrement mort pendant des mois. Avant d'ajouter un cache/une
invalidation, écrire un test qui prouve que l'invalidation est
effectivement déclenchée (pas seulement que l'écriture initiale réussit).

---

## ⚠️ QUASI-INCIDENT (Task 8, 2026-07-10) : `dependency_overrides[get_db]` partagé entre fichiers de test → risque d'écriture en base de PRODUCTION

**Contexte :** clôture Bloc A. En corrigeant `test_pivot_configs.py`
(échouait avec 422 car il n'envoyait pas le `property_id` désormais
obligatoire — ajouté après l'écriture initiale du test, support
multi-propriété), le test est repassé au vert **isolément**, mais
échouait encore dans le run complet `pytest backend/tests/` avec une
erreur différente : `400 "Property ID 1 n'existe pas"`.

**Cause :** `test_pivot_configs.py` faisait
`app.dependency_overrides[get_db] = override_get_db` **une seule fois, à
l'import du module** (niveau module, pas dans une fixture). `app` est un
singleton FastAPI partagé par TOUT le process pytest. Un autre fichier
(`test_realtime_states.py`, via la fixture `client` de `conftest.py`)
fait légitimement `app.dependency_overrides.pop(get_db, None)` dans son
propre teardown après ses propres tests — ce qui efface aussi
l'override posé par `test_pivot_configs.py`, puisque FastAPI résout les
overrides au moment de la requête HTTP, pas à la construction du
`TestClient`. Résultat : les requêtes de `test_pivot_configs.py`, exécutées
après coup, retombaient sur le VRAI `get_db()` — la base de
PRODUCTION (`backend/database/lmnp.db`) — au lieu de la base de test
SQLite isolée du fichier.

**Ce qui a été vérifié (aucune corruption) :** le `property_id` créé par
le test (id=1, premier row d'une table fraîchement créée) ne correspond à
aucune propriété réelle (Evry=25, mars=15, colloc=26) → l'appel a échoué
en 400 (validation), sans écrire aucune ligne. Vérifié directement en
base : `pivot_configs` contient toujours exactement les 3 lignes
pré-existantes (ids 5/6/7, dates de février 2026, aucune trace d'une
exécution de test). **Mais si un test avait par coïncidence utilisé un
`property_id` réel (15/25/26), il aurait pu créer/modifier/supprimer une
vraie ligne `pivot_configs` en production.**

**Fix :** l'override est maintenant posé/retiré dans la fixture
`setup_test_db` (autouse), scopée à chaque test (sauvegarde et restaure
l'override précédent au lieu de le poser une fois pour tout le module).

**Règle de prévention :** ne JAMAIS faire
`app.dependency_overrides[get_db] = ...` au niveau module dans un fichier
de test FastAPI — toujours le faire dans une fixture avec
`try/finally` (setup au début du test, restauration de l'état précédent à
la fin), exactement comme le fait déjà `conftest.py::client`. Un override
posé au niveau module reste actif jusqu'à ce qu'un AUTRE fichier de test
le retire, ce qui dépend de l'ordre de collection/exécution — un
comportement fragile et invisible tant qu'aucun test ne coïncide
accidentellement avec un vrai `property_id` de production.

---

## ⚠️ INCIDENT (Étape 2, Task 5, 2026-07-12) : un test hérité `SessionLocal` NOMMÉ EXPLICITEMENT contourne la quarantaine de répertoire → écriture en base de PRODUCTION

**Contexte :** pendant l'étape 2 Task 5 (bascule du service CR sur
`category_id`), un test hérité utilisant le sessionmaker de PRODUCTION
(bindé sur `backend/database/lmnp.db`) a été **nommé explicitement** sur la
ligne de commande pytest (au lieu de lancer le répertoire complet
`backend/tests/`). Il a **contaminé la base de production**.

**Cause :** la quarantaine de l'époque (`pytest_ignore_collect`, ADR-003 /
ADR-007) ne garde que les **scans de répertoire** — elle lit le texte des
fichiers découverts en scannant `backend/tests/` et ignore ceux qui matchent
les regex `SessionLocal`/`next(get_db())`. Mais lorsqu'un fichier est
**nommé explicitement** (`pytest backend/tests/test_xxx.py`), pytest le
collecte par son chemin et `pytest_ignore_collect` ne l'écarte pas de la
même façon : le module est importé/exécuté, son `SessionLocal` ouvre une
connexion sur le VRAI moteur de prod, et ses écritures atteignent `lmnp.db`.

**Remédiation :** base de production **restaurée depuis backup**, puis
**vérifiée byte-identique** (hash) après restauration. Aucune perte de
données résiduelle.

**Durcissement (Task 10, voir ADR-007) :** `conftest.py` installe désormais,
à l'import, un **garde sur l'objet moteur de PRODUCTION**
(`event.listens_for(backend.database.connection.engine, "connect")`) qui
**lève une `RuntimeError` claire** dès qu'une connexion est ouverte via ce
moteur, tant que `LMNP_ALLOW_PROD_DB_TESTS != "1"`. Ce garde intercepte
l'accès QUEL QUE SOIT le mode de découverte du test (scanné, nommé
explicitement, ou important le moteur directement) — il ne dépend plus de la
collecte. Ciblé sur l'objet moteur de prod uniquement : les tests golden en
lecture seule (moteur propre `?mode=ro` / copie temporaire) et le harnais
isolé (moteur mémoire) ne sont pas affectés. Couvert par
`backend/tests/test_prod_db_guard.py`.

**Règle de prévention :** un test ne doit **JAMAIS** utiliser `SessionLocal`
ni le moteur de PRODUCTION (`backend.database.connection.engine`) —
uniquement les fixtures isolées `db_session`/`client` (moteur mémoire) ou un
moteur dédié en lecture seule pour les tests golden. Le garde moteur-prod est
actif en permanence sous pytest ; **ne forcer** l'accès
(`LMNP_ALLOW_PROD_DB_TESTS=1`) **qu'après un backup frais** de `lmnp.db`, et
jamais globalement (uniquement dans un test précis via `monkeypatch.setenv`).

---

## Cas — Étape 3 §5 : 63 divergences de classification à la bascule (2026-07-13)

**Symptôme :** à la vérification réversible de la bascule (migration des
`mappings` → `classification_rules` puis contrôle de non-régression), **63
transactions déjà classées ressortaient `moteur=None`** — le nouveau moteur
ne les rangeait plus. Toutes des prélèvements SEPA récurrents
(`PRLV SEPA FREE TELECOM ...`, TotalEnergies, syndics, MACIF, DGFiP…).

**Cause :** le nouveau moteur unifié (`classification_engine`) appliquait la
garde de similarité 70 % à **tous** les préfixes. L'ancien
`find_best_mapping` (enrichment_service.py:104-113) avait des branches
spéciales `PRLV SEPA` / `VIR STRIPE` qui **contournent** cette garde. Ces
prélèvements ont un préfixe stable court + un long suffixe variable (n° de
contrat) → ratio `len(pattern)/len(label)` ≈ 0,46 < 0,70 → rejetés à tort.
En supprimant les cas spéciaux (Task 3), on a supprimé le contournement.

**Ce qui a marché :** le **contrôle de non-régression** a fait son travail —
il a attrapé l'écart AVANT tout drop de table (rien n'a été supprimé, prod
réversible). Diagnostic par simulation : bypasser la garde pour
`'PRLV SEPA' in pattern or pattern=='VIR STRIPE'` → 63 → **0 divergence**.
Fix : drapeau `strict_ratio` par règle (cf. ADR étape 3), littéraux confinés
à la migration one-shot, moteur runtime générique. Re-vérif : non-régression
0, golden 0.

**Règle de prévention :** quand on réécrit un moteur de matching censé
**reproduire** un existant, ne jamais supposer qu'un « cas spécial » est
redondant — vérifier ce qu'il change vraiment. **Toujours** valider une
migration de classification par un rejeu sur les données réelles
(non-régression = 0) AVANT de supprimer l'ancien système ; ne jamais dropper
sur la foi des seuls tests unitaires isolés.

---

## 🔗 Références

- [BEST_PRACTICES.md](./BEST_PRACTICES.md) - Pratiques générales du projet
- [GIT_WORKFLOW.md](./GIT_WORKFLOW.md) - Workflow Git
- [ADR.md](./ADR.md) - Décisions d'architecture (Bloc A + Étape 2)

---

**Dernière mise à jour :** 2026-07-12 (Étape 2, Task 10 — clôture)
**Cas d'étude :** Quarantaine tests / contamination base de production
