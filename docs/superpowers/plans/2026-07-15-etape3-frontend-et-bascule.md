# Étape 3 §5 — Écrans (Boîte de réception + Règles) + bascule legacy — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal :** Construire les 2 écrans front — **Boîte de réception** (classer en 1 clic, remplace « Non classées ») et **Règles** (table unique + préversion, remplace « Mapping ») — branchés sur l'API déjà livrée (`/api/inbox`, `/api/rules`), puis **retirer l'ancien système** (front + back + tables) en un seul geste cohérent, sans bouger un centime (golden master + non-régression bloquants).

**Architecture :** Next.js App Router (composants clients, styles inline, fetch via `src/api/client.ts`, `useProperty()` pour la propriété active). Le back expose déjà `/api/rules` et `/api/inbox` (étape 3 §5 backend). Ce plan ajoute un endpoint catégories (référentiel), les namespaces API front, un sélecteur de catégorie réutilisable, les 2 écrans, puis supprime l'ancien code/tables. Maquette validée : `docs/files/maquette-etape3.html`.

**Tech Stack :** FastAPI/SQLAlchemy (back), Next.js 16 + React 19 + TypeScript (front, styles inline), pytest (back, harnais isolé), Jest + React Testing Library (front, `frontend/__tests__/`).

**Spec / maquette :** `docs/superpowers/specs/2026-07-13-etape3-regles-inbox-design.md` ; maquette validée par Louis le 2026-07-15.

## Global Constraints

- **Golden master bloquant** : après toute bascule back, `python3 backend/scripts/golden_master.py --compare --tag v4-etape2-referentiel` = exit 0 (backend :8000 à jour requis).
- **Non-régression bloquante** avant tout drop : `python3 backend/scripts/check_rules_no_regression.py` = 0 divergence (exit 0).
- **Jamais reclasser l'historique** ; l'app doit **booter** à chaque commit (`python3 -c "import backend.api.main"`).
- **Sauvegarde** `.db` horodatée dans `backups/` avant tout drop de table.
- **Tests back** : harnais isolé (`db_session`/`client`), jamais `SessionLocal`/`next(get_db())` littéraux dans un fichier de test.
- **Tests front** : Jest + RTL dans `frontend/__tests__/`, lancés par `npm test` (depuis `frontend/`). Mocker `src/api/client`.
- **Style front** : styles **inline** (pas de Tailwind en pratique), tokens `#1e3a5f` (marine), `#f9fafb` (fond), `#e5e5e5` (bordures), `#1a1a1a` (texte). Copier le patron de `AllowedMappingsTable.tsx` (CRUD table compacte).
- **Property** : chaque appel API prend `activeProperty.id` via `useProperty()` ; garder le garde `if (!activeProperty || activeProperty.id <= 0) return`.
- **Commits** : git natif scellé (PAS `git_ops.py` qui fait `git add .` — le CSV `trades_evry_2025.csv` doit rester non commité). Format `[REFONTE] type: description`.
- **Interim déjà en place** : `classification_rules` peuplée en prod (366 règles, 48 `strict_ratio=False`), moteur rules live. Les routes legacy `mappings`/`enrichment` existent encore jusqu'à la Phase C.

## File Structure

**Backend (nouveau / modifié) :**
- `backend/api/routes/categories.py` (créé) — `GET /api/categories`.
- `backend/api/services/mapping_obligatoire_service.py` (modifié Phase A puis nettoyé Phase C) — `validate_mapping` bascule sur le référentiel.
- Phase C : suppression `routes/mappings.py`, `routes/mappings_allowed_endpoints.py`, `routes/enrichment.py` ; modèles `Mapping`/`AllowedMapping`/`MappingImport` retirés ; fonctions mortes d'`enrichment_service.py` retirées ; scripts/Excel legacy supprimés ; `create_classification_rules` + migration + drop tables.

**Frontend (nouveau / modifié) :**
- `frontend/src/api/client.ts` (modifié) — namespaces `categoriesAPI`, `rulesAPI`, `inboxAPI` + interfaces.
- `frontend/src/components/CategorySelector.tsx` (créé) — sélecteur catégorie depuis le référentiel.
- `frontend/src/components/InboxScreen.tsx` (créé) — écran ①.
- `frontend/src/components/RulesScreen.tsx` (créé) — écran ②.
- `frontend/src/components/Navigation.tsx` (modifié) — onglets « Boîte de réception » / « Règles ».
- `frontend/app/dashboard/transactions/page.tsx` (modifié) — rend les nouveaux écrans, retire les blocs `filter=unclassified` + `tab=mapping`.
- Phase C : suppression `MappingTable.tsx`, `AllowedMappingsTable.tsx`, `UnclassifiedTransactionsTable.tsx`, `MappingFileUpload.tsx`, `MappingColumnMappingModal.tsx`, `MappingImportLog.tsx` + usages de `mappingsAPI`.

---

## PHASE A — Prérequis backend (réversible, testable seul)

### Task 1 : Endpoint `GET /api/categories` (référentiel)

**Files :**
- Create : `backend/api/routes/categories.py`
- Modify : `backend/api/main.py` (import + include_router)
- Test : `backend/tests/test_categories_api.py`

**Interfaces :**
- Produces : `GET /api/categories` → `{"items": [{"id", "label", "group_label", "nature"}]}` trié par groupe puis label. Sert le sélecteur front et le mapping `category_id → label`.

- [ ] **Step 1 : Test qui échoue**
```python
# backend/tests/test_categories_api.py
from backend.database.models import Category, CategoryGroup

def _seed(db):
    g = CategoryGroup(label="Produits", nature="produits"); db.add(g); db.flush()
    db.add(Category(label="Encaissement locataire et CAF", group_id=g.id)); db.commit()

def test_list_categories(client, db_session):
    _seed(db_session)
    body = client.get("/api/categories").json()
    assert any(c["label"] == "Encaissement locataire et CAF"
               and c["group_label"] == "Produits" and c["nature"] == "produits"
               for c in body["items"])
```

- [ ] **Step 2 : Lancer, vérifier l'échec** — `python3 -m pytest backend/tests/test_categories_api.py -v` → 404.

- [ ] **Step 3 : Implémenter**
```python
# backend/api/routes/categories.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import Category, CategoryGroup

router = APIRouter()

@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    rows = (db.query(Category, CategoryGroup)
            .join(CategoryGroup, Category.group_id == CategoryGroup.id)
            .order_by(CategoryGroup.label, Category.label).all())
    return {"items": [{"id": c.id, "label": c.label,
                       "group_label": g.label, "nature": g.nature}
                      for c, g in rows]}
```
Enregistrer dans `main.py` : ajouter `categories` à l'import ligne 61 et `app.include_router(categories.router, prefix="/api", tags=["categories"])`.

- [ ] **Step 4 : Lancer, vérifier le succès** — 1 passed ; puis `python3 -m pytest backend/tests -q` reste vert ; `python3 -c "import backend.api.main"` OK.

- [ ] **Step 5 : Commit**
```bash
git add backend/api/routes/categories.py backend/api/main.py backend/tests/test_categories_api.py
git commit -m "[REFONTE] feat: endpoint GET /api/categories (référentiel)"
```

---

### Task 2 : `validate_mapping` bascule sur le référentiel (sever allowed_mappings)

**Files :**
- Modify : `backend/api/services/mapping_obligatoire_service.py` (`validate_mapping`)
- Test : `backend/tests/test_validate_mapping_referentiel.py`

**Interfaces :**
- Consumes : `resolve_category` (`category_service`, étape 2).
- Produces : `validate_mapping(db, level_1, level_2, level_3, property_id)` renvoie True ssi le triplet **résout dans le référentiel** (au lieu d'interroger `allowed_mappings`). Sévère la dépendance vivante à `allowed_mappings` pour permettre son drop en Phase C. Signature inchangée (appelée par `enrichment_service` classification manuelle).

- [ ] **Step 1 : Test qui échoue**
```python
# backend/tests/test_validate_mapping_referentiel.py
from backend.database.models import Category, CategoryGroup
from backend.api.services.mapping_obligatoire_service import validate_mapping

def _seed(db):
    g = CategoryGroup(label="Produits", nature="produits"); db.add(g); db.flush()
    db.add(Category(label="Encaissement locataire et CAF", group_id=g.id)); db.commit()

def test_valid_triple_resolves(db_session):
    _seed(db_session)
    assert validate_mapping(db_session, "Encaissement locataire et CAF", "Produits", "Produits", property_id=25) is True

def test_unknown_triple_false(db_session):
    _seed(db_session)
    assert validate_mapping(db_session, "Inexistant", "Produits", "Produits", property_id=25) is False
```

- [ ] **Step 2 : Lancer, vérifier l'échec** — le test échoue (l'implémentation interroge encore `allowed_mappings`, table vide en test → False au 1er cas).

- [ ] **Step 3 : Implémenter** — remplacer le corps de `validate_mapping` :
```python
# backend/api/services/mapping_obligatoire_service.py
from backend.api.services.category_service import resolve_category

def validate_mapping(db, level_1, level_2, level_3=None, property_id=None):
    """Valide qu'un triplet existe dans le RÉFÉRENTIEL (categories/category_groups).
    Remplace l'ancienne interrogation de allowed_mappings (supprimée en étape 3)."""
    if property_id is None:
        raise ValueError("property_id est obligatoire pour valider un mapping")
    if level_3 is None:
        return False  # le référentiel exige les 3 niveaux (nature)
    return resolve_category(db, level_1, level_2, level_3) is not None
```

- [ ] **Step 4 : Lancer, vérifier le succès** — 2 passed ; `python3 -m pytest backend/tests -q` vert ; `import backend.api.main` OK.

- [ ] **Step 5 : Golden (sécurité — le chemin manuel ne doit pas bouger un chiffre)** — backend :8000 à jour, `python3 backend/scripts/golden_master.py --compare --tag v4-etape2-referentiel` = exit 0.

- [ ] **Step 6 : Commit**
```bash
git add backend/api/services/mapping_obligatoire_service.py backend/tests/test_validate_mapping_referentiel.py
git commit -m "[REFONTE] refactor: validate_mapping valide via le référentiel (sever allowed_mappings)"
```

---

## PHASE B — Construction des écrans (front)

### Task 3 : Client API — `categoriesAPI`, `rulesAPI`, `inboxAPI`

**Files :**
- Modify : `frontend/src/api/client.ts` (ajouter interfaces + 3 namespaces, à la suite des namespaces existants)
- Test : `frontend/__tests__/rulesInboxApi.test.ts`

**Interfaces :**
- Produces (typés) :
  - `categoriesAPI.list(): Promise<Category[]>` (`{id, label, group_label, nature}`)
  - `rulesAPI.list(propertyId): Promise<Rule[]>` ; `.create(propertyId, RuleInput)` ; `.update(id, RuleInput)` ; `.remove(id)` ; `.preview(propertyId, RuleInput): Promise<{would_classify, conflicts}>`
  - `inboxAPI.list(propertyId): Promise<InboxItem[]>` ; `.validate(body)` ; `.validateAll(propertyId)`
  - Le back reçoit `property_id` en query (GET) ou body (POST). Les routes existent déjà (`/api/rules`, `/api/inbox`, `/api/categories`).

- [ ] **Step 1 : Test qui échoue**
```ts
// frontend/__tests__/rulesInboxApi.test.ts
import { rulesAPI, inboxAPI, categoriesAPI } from '@/api/client';

beforeEach(() => {
  global.fetch = jest.fn().mockResolvedValue({
    ok: true, status: 200, json: async () => ({ items: [] }),
  }) as unknown as typeof fetch;
});

test('rulesAPI.list appelle /api/rules avec property_id', async () => {
  await rulesAPI.list(25);
  expect(global.fetch).toHaveBeenCalledWith(
    expect.stringContaining('/api/rules?property_id=25'), expect.anything());
});

test('inboxAPI.validate poste sur /api/inbox/validate', async () => {
  await inboxAPI.validate({ transaction_id: 1, category_id: 2 });
  const [url, opts] = (global.fetch as jest.Mock).mock.calls[0];
  expect(url).toContain('/api/inbox/validate');
  expect(opts.method).toBe('POST');
});

test('categoriesAPI.list appelle /api/categories', async () => {
  await categoriesAPI.list();
  expect(global.fetch).toHaveBeenCalledWith(
    expect.stringContaining('/api/categories'), expect.anything());
});
```

- [ ] **Step 2 : Lancer, vérifier l'échec** — `cd frontend && npm test -- rulesInboxApi` → import échoue (namespaces absents).

- [ ] **Step 3 : Implémenter** — ajouter dans `client.ts` (réutiliser le helper `fetchAPI` existant) :
```ts
// --- Catégories (référentiel) ---
export interface Category { id: number; label: string; group_label: string; nature: string; }
export const categoriesAPI = {
  list: async (): Promise<Category[]> =>
    (await fetchAPI<{ items: Category[] }>('/api/categories')).items,
};

// --- Règles ---
export interface Rule {
  id: number; pattern: string; match_type: 'exact'|'prefix'|'contains';
  category_id: number; property_id: number|null; priority: number;
  source: string; strict_ratio: boolean; tx_count?: number;
}
export interface RuleInput {
  pattern: string; match_type: 'exact'|'prefix'|'contains';
  category_id: number; property_id: number|null; priority?: number; strict_ratio?: boolean;
}
export const rulesAPI = {
  list: async (propertyId: number): Promise<Rule[]> =>
    (await fetchAPI<{ items: Rule[] }>(`/api/rules?property_id=${propertyId}`)).items,
  create: (propertyId: number, r: RuleInput) =>
    fetchAPI<{ id: number }>('/api/rules', { method: 'POST', body: JSON.stringify(r) }),
  update: (id: number, r: RuleInput) =>
    fetchAPI<{ id: number }>(`/api/rules/${id}`, { method: 'PUT', body: JSON.stringify(r) }),
  remove: (id: number) =>
    fetchAPI<void>(`/api/rules/${id}`, { method: 'DELETE' }),
  preview: (propertyId: number, r: RuleInput) =>
    fetchAPI<{ would_classify: number; conflicts: { transaction_id: number; current_category_id: number }[] }>(
      '/api/rules/preview', { method: 'POST', body: JSON.stringify(r) }),
};

// --- Inbox ---
export interface InboxItem {
  transaction_id: number; nom: string; date: string; montant: number;
  suggestion: { category_id: number | null };
  proposed_rule: { pattern: string; match_type: 'exact'|'prefix'|'contains' };
}
export const inboxAPI = {
  list: async (propertyId: number): Promise<InboxItem[]> =>
    (await fetchAPI<{ items: InboxItem[] }>(`/api/inbox?property_id=${propertyId}`)).items,
  validate: (body: { transaction_id: number; category_id: number;
                     rule?: { pattern: string; match_type: string; property_id?: number|null } }) =>
    fetchAPI('/api/inbox/validate', { method: 'POST', body: JSON.stringify(body) }),
  validateAll: (propertyId: number) =>
    fetchAPI(`/api/inbox/validate-all?property_id=${propertyId}`, { method: 'POST' }),
};
```
> Note : le back attend `property_id` dans le body pour `POST /api/rules` (cf. `RuleIn`). `create` doit donc inclure `property_id` dans `r` (le composant le passe). Vérifier la forme exacte attendue par `rules.py` et aligner (ne pas inventer).

- [ ] **Step 4 : Lancer, vérifier le succès** — `cd frontend && npm test -- rulesInboxApi` → 3 passed.

- [ ] **Step 5 : Commit**
```bash
git add frontend/src/api/client.ts frontend/__tests__/rulesInboxApi.test.ts
git commit -m "[REFONTE] feat(front): client API categories/rules/inbox"
```

---

### Task 4 : Composant `CategorySelector`

**Files :**
- Create : `frontend/src/components/CategorySelector.tsx`
- Test : `frontend/__tests__/categorySelector.test.tsx`

**Interfaces :**
- Consumes : `categoriesAPI.list`.
- Produces : `<CategorySelector value={category_id|null} onChange={(id)=>...} />` — `<select>` groupé par `group_label`, chargé une fois via `categoriesAPI.list()`. Réutilisé par Inbox et Règles.

- [ ] **Step 1 : Test qui échoue**
```tsx
// frontend/__tests__/categorySelector.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import CategorySelector from '@/components/CategorySelector';
jest.mock('@/api/client', () => ({
  categoriesAPI: { list: jest.fn().mockResolvedValue([
    { id: 2, label: 'Énergie', group_label: 'Charges Déductibles', nature: 'charges_deductibles' },
    { id: 1, label: 'Encaissement locataire et CAF', group_label: 'Produits', nature: 'produits' },
  ]) },
}));
test('affiche les catégories chargées', async () => {
  render(<CategorySelector value={null} onChange={() => {}} />);
  await waitFor(() => expect(screen.getByText('Énergie')).toBeInTheDocument());
  expect(screen.getByText('Encaissement locataire et CAF')).toBeInTheDocument();
});
```

- [ ] **Step 2 : Lancer, vérifier l'échec** — composant absent.

- [ ] **Step 3 : Implémenter** — `<select>` natif (style inline, bordure `#e5e5e5`, radius 4px), `<optgroup label={group_label}>`, chargement `useEffect` une fois. `onChange` renvoie `Number(e.target.value) || null`.

- [ ] **Step 4 : Lancer, vérifier le succès** — 1 passed.

- [ ] **Step 5 : Commit**
```bash
git add frontend/src/components/CategorySelector.tsx frontend/__tests__/categorySelector.test.tsx
git commit -m "[REFONTE] feat(front): CategorySelector depuis le référentiel"
```

---

### Task 5 : Écran Boîte de réception (`InboxScreen`)

**Files :**
- Create : `frontend/src/components/InboxScreen.tsx`
- Test : `frontend/__tests__/inboxScreen.test.tsx`

**Interfaces :**
- Consumes : `inboxAPI` (list/validate/validateAll), `categoriesAPI.list` (id→label), `CategorySelector`, `useProperty()`.
- Produces : `<InboxScreen />` — liste les items (date, libellé, montant, suggestion=label ou `CategorySelector` si null), boutons **Valider** (envoie `validate` avec `rule = proposed_rule`, portée bien courant), **Modifier** (édite catégorie/motif/portée avant), **Tout valider** (`validateAll`). Recharge après action. Bannière d'erreur si l'API échoue (jamais avalée).

- [ ] **Step 1 : Test qui échoue**
```tsx
// frontend/__tests__/inboxScreen.test.tsx
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import InboxScreen from '@/components/InboxScreen';
jest.mock('@/contexts/PropertyContext', () => ({ useProperty: () => ({ activeProperty: { id: 25 } }) }));
jest.mock('@/api/client', () => ({
  inboxAPI: {
    list: jest.fn().mockResolvedValue([{
      transaction_id: 1, nom: 'VIR AIRBNB PAYMENTS LUXEMBOU G-ZE', date: '2025-06-28',
      montant: 540, suggestion: { category_id: 1 },
      proposed_rule: { pattern: 'VIR AIRBNB PAYMENTS LUXEMBOU', match_type: 'prefix' } }]),
    validate: jest.fn().mockResolvedValue({}),
    validateAll: jest.fn().mockResolvedValue({ rules_created: 1, transactions_validated: 1 }),
  },
  categoriesAPI: { list: jest.fn().mockResolvedValue([{ id: 1, label: 'Encaissement locataire et CAF', group_label: 'Produits', nature: 'produits' }]) },
}));
test('liste un item et valide', async () => {
  const { inboxAPI } = require('@/api/client');
  render(<InboxScreen />);
  await waitFor(() => expect(screen.getByText(/VIR AIRBNB/)).toBeInTheDocument());
  expect(screen.getByText('Encaissement locataire et CAF')).toBeInTheDocument();
  fireEvent.click(screen.getAllByText('Valider')[0]);
  await waitFor(() => expect(inboxAPI.validate).toHaveBeenCalledWith(
    expect.objectContaining({ transaction_id: 1, category_id: 1,
      rule: expect.objectContaining({ pattern: 'VIR AIRBNB PAYMENTS LUXEMBOU', match_type: 'prefix' }) })));
});
```

- [ ] **Step 2 : Lancer, vérifier l'échec** — composant absent.

- [ ] **Step 3 : Implémenter** — patron `AllowedMappingsTable` (useEffect load, isLoading/error). Rendu : header (compteur + « Tout valider »), lignes maquette. « Valider » appelle `inboxAPI.validate({transaction_id, category_id: suggestion ?? selected, rule: {pattern, match_type, property_id: activeProperty.id}})`. Si `suggestion.category_id` null → `CategorySelector` requis avant activer Valider. Recharger après chaque action.

- [ ] **Step 4 : Lancer, vérifier le succès** — passed.

- [ ] **Step 5 : Commit**
```bash
git add frontend/src/components/InboxScreen.tsx frontend/__tests__/inboxScreen.test.tsx
git commit -m "[REFONTE] feat(front): écran Boîte de réception"
```

---

### Task 6 : Écran Règles (`RulesScreen`)

**Files :**
- Create : `frontend/src/components/RulesScreen.tsx`
- Test : `frontend/__tests__/rulesScreen.test.tsx`

**Interfaces :**
- Consumes : `rulesAPI` (list/create/update/remove/preview), `categoriesAPI.list`, `CategorySelector`, `useProperty()`.
- Produces : `<RulesScreen />` — table (motif, type, catégorie=label, portée bien/global, `tx_count`, source, actions ✎/🗑). Éditeur « Nouvelle règle » avec **préversion live** (`rulesAPI.preview` au changement → « classerait N · M conflits »), case « Appliquer aux existantes » (défaut off). Supprimer = `rulesAPI.remove` (ne déclasse pas). Portée bascule bien/global.

- [ ] **Step 1 : Test qui échoue**
```tsx
// frontend/__tests__/rulesScreen.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import RulesScreen from '@/components/RulesScreen';
jest.mock('@/contexts/PropertyContext', () => ({ useProperty: () => ({ activeProperty: { id: 25 } }) }));
jest.mock('@/api/client', () => ({
  rulesAPI: { list: jest.fn().mockResolvedValue([
      { id: 1, pattern: 'VIR AIRBNB PAYMENTS LUXEMBOU', match_type: 'prefix', category_id: 1,
        property_id: 25, priority: 0, source: 'migrated', strict_ratio: true, tx_count: 37 }]),
    preview: jest.fn().mockResolvedValue({ would_classify: 3, conflicts: [] }),
    create: jest.fn(), update: jest.fn(), remove: jest.fn() },
  categoriesAPI: { list: jest.fn().mockResolvedValue([{ id: 1, label: 'Encaissement locataire et CAF', group_label: 'Produits', nature: 'produits' }]) },
}));
test('affiche une règle avec son libellé de catégorie et son compte', async () => {
  render(<RulesScreen />);
  await waitFor(() => expect(screen.getByText('VIR AIRBNB PAYMENTS LUXEMBOU')).toBeInTheDocument());
  expect(screen.getByText('Encaissement locataire et CAF')).toBeInTheDocument();
  expect(screen.getByText('37')).toBeInTheDocument();
});
```

- [ ] **Step 2 : Lancer, vérifier l'échec** — composant absent.

- [ ] **Step 3 : Implémenter** — table style maquette (motif en monospace, pills portée bien/global, `strict_ratio=false` → mention « garde 70 % désactivée »). Éditeur : `CategorySelector` + inputs motif/type/portée, `preview` débattu sur changement. Erreurs API en bannière (jamais avalées).

- [ ] **Step 4 : Lancer, vérifier le succès** — passed.

- [ ] **Step 5 : Commit**
```bash
git add frontend/src/components/RulesScreen.tsx frontend/__tests__/rulesScreen.test.tsx
git commit -m "[REFONTE] feat(front): écran Règles + préversion live"
```

---

### Task 7 : Navigation + branchement des pages

**Files :**
- Modify : `frontend/src/components/Navigation.tsx` (onglets)
- Modify : `frontend/app/dashboard/transactions/page.tsx` (rendu des nouveaux écrans)
- Test : `frontend/__tests__/navigation.test.tsx`

**Interfaces :**
- Produces : onglet **« Boîte de réception »** (`?tab=inbox`, badge compteur) et **« Règles »** (`?tab=rules`) ; les blocs `filter=unclassified` et `tab=mapping` sont **remplacés** par `<InboxScreen/>` / `<RulesScreen/>`.

- [ ] **Step 1 : Test qui échoue**
```tsx
// frontend/__tests__/navigation.test.tsx
import { render, screen } from '@testing-library/react';
import Navigation from '@/components/Navigation';
jest.mock('next/navigation', () => ({
  usePathname: () => '/dashboard/transactions',
  useSearchParams: () => new URLSearchParams('tab=rules'),
}));
test('les onglets Boîte de réception et Règles sont présents', () => {
  render(<Navigation />);
  expect(screen.getByText('Boîte de réception')).toBeInTheDocument();
  expect(screen.getByText('Règles')).toBeInTheDocument();
});
```

- [ ] **Step 2 : Lancer, vérifier l'échec** — les libellés n'existent pas encore.

- [ ] **Step 3 : Implémenter** — dans `Navigation.tsx`, remplacer les entrées : `{ name: 'Boîte de réception', href: '/dashboard/transactions?tab=inbox' }` et `{ name: 'Règles', href: '/dashboard/transactions?tab=rules' }` (retirer « Non classées » et « Mapping » ; garder « Toutes les transactions » et « Load Trades/Mappings » → renommer « Import relevés » si besoin). Gérer l'état actif pour `tab=inbox`/`tab=rules`. Dans `transactions/page.tsx`, rendre `{tab === 'inbox' && <InboxScreen/>}` et `{tab === 'rules' && <RulesScreen/>}` ; **retirer** les blocs `filter === 'unclassified'` (l.220-231) et `tab === 'mapping'` (l.494-649).

- [ ] **Step 4 : Lancer, vérifier le succès** — passed ; `cd frontend && npm test` reste vert ; `npm run build` réussit (ou `npx tsc --noEmit` propre).

- [ ] **Step 5 : Commit**
```bash
git add frontend/src/components/Navigation.tsx frontend/app/dashboard/transactions/page.tsx frontend/__tests__/navigation.test.tsx
git commit -m "[REFONTE] feat(front): onglets Boîte de réception + Règles, branchement des écrans"
```

---

## PHASE C — Bascule (retrait de l'ancien, destructif, sous portes)

### Task 8 : Retrait de l'ancien front (mapping + non classées)

**Files :**
- Delete : `frontend/src/components/MappingTable.tsx`, `AllowedMappingsTable.tsx`, `UnclassifiedTransactionsTable.tsx`, `MappingFileUpload.tsx`, `MappingColumnMappingModal.tsx`, `MappingImportLog.tsx`
- Modify : `frontend/app/dashboard/transactions/page.tsx` (retirer imports + le sous-flux mapping/allowed du `tab=load_trades` s'il en dépend), `frontend/src/api/client.ts` (retirer le namespace `mappingsAPI` et `enrichmentAPI` s'ils ne servent plus)

**Interfaces :** supprime les surfaces front legacy. Aucune nouvelle.

- [ ] **Step 1 : Grep des usages restants** — `grep -rn "MappingTable\|AllowedMappingsTable\|UnclassifiedTransactionsTable\|MappingFileUpload\|MappingImportLog\|mappingsAPI\|enrichmentAPI" frontend/app frontend/src --include=*.tsx --include=*.ts | grep -v __tests__` → lister ce qui pointe encore dessus.

- [ ] **Step 2 : Supprimer les composants + usages** — retirer les imports/JSX dans `transactions/page.tsx`, supprimer les 6 fichiers, retirer `mappingsAPI`/`enrichmentAPI` de `client.ts` **seulement si** plus aucun usage (sinon garder et noter). Supprimer/adapter les tests front qui les ciblaient.

- [ ] **Step 3 : Vérifier** — `cd frontend && npm test` vert ; `npm run build` réussit ; grep de contrôle = 0 usage résiduel (hors tests supprimés).

- [ ] **Step 4 : Commit**
```bash
git add -A frontend
git status --short   # aucun fichier hors frontend
git commit -m "[REFONTE] refactor(front): retrait écrans mapping/non-classées legacy"
```

---

### Task 9 : Retrait de l'ancien back (routes, modèles, code mort)

**Files :**
- Delete : `backend/api/routes/mappings.py`, `backend/api/routes/mappings_allowed_endpoints.py`, `backend/api/routes/enrichment.py`, `scripts/mappings_obligatoires.xlsx`, scripts legacy (`backend/scripts/*hardcoded*`, `*allowed_mappings*`, `migrate_mappings.py`, `migrate_mappings_phase*`, `validate_mappings_migration_phase*`, `check_mapping_types.py`, `add_is_hardcoded_column.py`)
- Modify : `backend/api/main.py` (dé-enregistrer `mappings`, `enrichment`), `backend/database/models.py` (retirer `Mapping`, `AllowedMapping`, `MappingImport`), `backend/api/services/enrichment_service.py` (retirer `find_best_mapping`, `create_or_update_mapping_from_classification`, `transaction_matches_mapping_name` si inutilisés ; retirer l'import `Mapping`), `backend/api/services/mapping_obligatoire_service.py` (retirer les fonctions touchant `AllowedMapping`/`Mapping` désormais mortes), `backend/api/models.py` (retirer `MappingImportResponse`/`MappingImportHistory`/`AllowedMappingResponse` si inutilisés)

**Interfaces :** supprime les surfaces back legacy. L'app doit booter.

- [ ] **Step 1 : Grep dépendances** — `grep -rn "from backend.database.models import.*\b(Mapping|AllowedMapping|MappingImport)\b\|routes import.*\b(mappings|enrichment)\b\|find_best_mapping\|create_or_update_mapping_from_classification\|import mappings_obligatoires" backend/api backend/scripts | grep -v test` → tout ce qui pointe encore.

- [ ] **Step 2 : Retirer** — dé-enregistrer les routers dans `main.py` ; supprimer les fichiers de routes/scripts/Excel ; retirer les classes ORM + fonctions mortes ; nettoyer les imports. Adapter/supprimer les tests back devenus obsolètes (ceux qui n'exercent que du legacy déjà quarantiné).

- [ ] **Step 3 : Vérifier le boot + suite** — `python3 -c "import backend.api.main"` OK ; `python3 -m pytest backend/tests -q` vert (le compte peut baisser : suppression de tests legacy sans couverture réelle) ; grep de contrôle = 0 référence active.

- [ ] **Step 4 : Commit**
```bash
git add -A backend
git status --short   # trades_evry_2025.csv NON stagé
git commit -m "[REFONTE] refactor(back): retrait routes/modèles/scripts mapping legacy"
```

---

### Task 10 : Drop des tables + portes finales

**Files :**
- Create : `backend/database/migrations/drop_legacy_mapping_tables.py`

**Interfaces :** supprime les tables physiques `mappings`, `allowed_mappings`, `mapping_imports`.

> ⚠️ Écrit sur la base de prod. Chaque sous-étape vérifiée avant la suivante.

- [ ] **Step 1 : Backup**
```bash
cp backend/database/lmnp.db "backups/lmnp_avant_drop_$(python3 -c 'import datetime;print(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))').db"
```

- [ ] **Step 2 : Non-régression AVANT drop (garde-fou)** — backend :8000 à jour, `python3 backend/scripts/check_rules_no_regression.py; echo exit=$?` = **0 divergence, exit 0**. Si ≠ 0 : STOP, ne rien dropper.

- [ ] **Step 3 : Migration de suppression**
```python
# backend/database/migrations/drop_legacy_mapping_tables.py
from backend.database.connection import engine
from sqlalchemy import text
LEGACY = ["mappings", "allowed_mappings", "mapping_imports"]
def main():
    with engine.begin() as conn:
        for t in LEGACY:
            conn.execute(text(f"DROP TABLE IF EXISTS {t}")); print(f"[migration] {t} supprimée.")
if __name__ == "__main__":
    main()
```
```bash
PYTHONPATH="$PWD" python3 backend/database/migrations/drop_legacy_mapping_tables.py
```

- [ ] **Step 4 : Portes finales** — relancer backend :8000 (code à jour), puis :
```bash
python3 -m pytest backend/tests -q
python3 backend/scripts/golden_master.py --compare --tag v4-etape2-referentiel; echo "golden=$?"
```
Attendu : suite verte, golden exit 0. Tables absentes de `sqlite_master` (vérifier).

- [ ] **Step 5 : Commit**
```bash
git add -A backend docs
git status --short   # trades_evry_2025.csv NON stagé
git commit -m "[REFONTE] refactor: drop tables mappings/allowed_mappings/mapping_imports + golden 0"
```

---

## Self-Review (rempli)

- **Couverture spec/maquette** : écran ① → Task 5 ; écran ② → Task 6 ; sélecteur catégorie → Task 4 ; endpoint catégories manquant → Task 1 ; sever allowed_mappings (validation) → Task 2 ; onglets/branchement → Task 7 ; retrait legacy front → Task 8 ; back → Task 9 ; drop + golden → Task 10.
- **Placeholders** : aucun step sans code réel ou commande concrète.
- **Cohérence des types** : `rulesAPI`/`inboxAPI`/`categoriesAPI` (Task 3) réutilisés identiquement par Tasks 4-7 ; `RuleInput`/`InboxItem`/`Category` stables.
- **Points de vigilance** : (a) Task 3 — vérifier la forme exacte que `rules.py` attend pour `property_id` (body) avant de figer `create`. (b) Task 9 — l'ordre importe : retirer le code AVANT de dropper les tables (Task 10), sinon boot cassé. (c) Pas de Playwright dans le repo → couverture E2E assurée par tests RTL (Tasks 4-7) + portes golden/non-régression ; un vrai E2E Playwright serait un suivi séparé (setup infra).

## Ordre d'exécution

Phase A (1→2) → Phase B (3→7) → Phase C (8→9→10). Les portes non-régression + golden (Tasks 2, 10) sont bloquantes. Rien n'est droppé tant que la non-régression n'est pas à 0.
