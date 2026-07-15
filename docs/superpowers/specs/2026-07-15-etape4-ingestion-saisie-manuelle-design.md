# Étape 4 — Ingestion unifiée + saisie manuelle

**Statut** : Design validé (brainstorm 2026-07-15) — à relire par Louis avant plan d'implémentation.
**Réf. spec mère** : `2026-07-10-refonte-lmnp-design.md` §4 (modèle), §7 partie 1 (ingestion), §11 point 4 (ordre).
**Branche** : `refonte` (jamais mergée — filet de rollback).

---

## 1. Périmètre

Cette spec couvre l'**étape 4** de la refonte : le **service d'ingestion unifié** (point d'entrée unique pour toutes les transactions entrantes), les **champs de compte bancaire** sur le modèle, la table `bank_accounts`, le **rebranchement de l'import CSV** existant sur ce service, et la **saisie manuelle** de transactions (création simple, éclatement d'une ligne, écriture croisée qui s'annule).

**Objectif** : poser la plomberie d'ingestion propre et réutilisable — un seul chemin `normalisation → dédoublonnage → insertion → classification → recalculs`, en une seule transaction DB — sur lequel se branchera l'étape 5 (Enable Banking), tout en donnant dès maintenant à l'utilisateur la saisie manuelle nécessaire à une comptabilité juste.

**Hors périmètre (chantiers séparés)** :
- **Connexion bancaire réelle** (client Enable Banking, JWT RS256, flux OAuth/consentement, synchro API, écran Sources maquette ③, remplissage de `bank_accounts`) → **étape 5** (§7 partie 2 de la spec mère).
- **Restylage / dashboard** (§8bis) → chantier UI séparé.
- **Création d'une catégorie inexistante** dans le référentiel : le plan de comptes actuel (56 catégories) est complet pour les besoins connus ; ajouter une catégorie au référentiel est une opération rare traitée hors de ce périmètre (YAGNI).
- **Drop physique** des tables legacy (`mappings`, `allowed_mappings`, `mapping_imports`) → tâche de clôture différée (décision Louis 2026-07-15 : conserver jusqu'à validation front complète).

---

## 2. Décisions verrouillées (brainstorm 2026-07-15)

1. **Périmètre** : « plomberie invisible » + saisie manuelle. L'import CSV doit rester, à l'écran, **strictement identique** pour l'utilisateur.
2. **Cardinalité compte/bien** : un bien = **un seul compte bancaire** réel. Les mouvements passés par un autre compte se représentent par des **écritures croisées manuelles** (voir §6.3), pas par plusieurs comptes. La FK `transactions.account_id` reste néanmoins nullable (l'historique CSV et le manuel n'ont pas de compte tant que la banque n'est pas branchée).
3. **Historique CSV** : les transactions existantes ne sont **pas** rattachées à un compte synthétique — elles restent `account_id = NULL`, marquées `source = csv`. Aucune donnée déplacée.
4. **Éclatement d'une ligne** : la ligne d'origine devient une **ligne parente masquée** (conservée et liée pour le rapprochement bancaire + anti-reduplication), **exclue des listes et de tous les totaux** ; elle est remplacée à l'affichage par ses lignes enfants. **Garde-fou dur** : la somme des enfants doit égaler le montant de la parente, sinon l'opération est refusée.
5. **Saisie manuelle** posée sur l'onglet existant « Toutes les transactions » (bouton ➕ + action « éclater » sur une ligne), pas de nouvel onglet.
6. **Classification des transactions manuelles** : même pipeline que les autres. Soit l'utilisateur choisit une catégorie existante à la création, soit la transaction reste non classée et apparaît dans la **Boîte de réception** (étape 3), où la valider crée la règle. Pas de mécanisme de mapping parallèle.
7. **Invariant chiffres** : golden master à **0 écart** et **0 divergence** de non-régression, comme à chaque étape.

---

## 3. Modèle de données

### 3.1 Nouvelle table `bank_accounts`

Créée mais **non peuplée** en étape 4 (aucune ligne insérée ; le remplissage vient avec la connexion bancaire en étape 5). Champs (spec mère §4) :

| Champ | Type | Note |
|---|---|---|
| `id` | Integer PK | |
| `property_id` | Integer FK → `properties.id` | un compte par bien |
| `bank_name` | String | |
| `iban_masked` | String | IBAN masqué (jamais en clair complet) |
| `eb_account_uid` | String nullable | id compte Enable Banking (étape 5) |
| `eb_session_id` | String nullable | session Enable Banking (étape 5) |
| `session_valid_until` | Date nullable | échéance consentement (étape 5) |
| `last_sync_at` | DateTime nullable | dernière synchro (étape 5) |
| `last_tx_cursor` | String nullable | curseur de pagination (étape 5) |

### 3.2 Champs ajoutés à `transactions`

| Champ | Type | Défaut / migration | Rôle |
|---|---|---|---|
| `account_id` | Integer FK → `bank_accounts.id`, **nullable** | NULL sur l'existant | compte bancaire (rempli en étape 5 pour les tx API) |
| `external_id` | String, **nullable** | NULL sur l'existant | id transaction côté banque (anti-doublon API) |
| `source` | Enum `csv \| api \| manual` | **`csv`** pour tout l'existant | provenance de la transaction |
| `parent_transaction_id` | Integer FK → `transactions.id` (auto-référence), **nullable** | NULL | pour un enfant d'éclatement : pointe la ligne d'origine |
| `is_split_parent` | Boolean | `False` | marque la ligne d'origine éclatée : masquée + exclue de tous les totaux |

**Contrainte d'unicité** : index unique **partiel** `CREATE UNIQUE INDEX ... ON transactions(account_id, external_id) WHERE external_id IS NOT NULL` (SQLite supporte les index partiels). N'entrave pas les lignes CSV/manuelles (`external_id` NULL), empêche qu'une transaction bancaire déjà connue soit réinsérée (étape 5). Doublée d'un contrôle applicatif dans le service d'ingestion.

**Migration** : ajout de colonnes seulement (aucune valeur monétaire touchée → golden trivialement préservé). Sauvegarde `.db` horodatée dans `backups/` avant exécution. Backfill : `source = 'csv'` sur toutes les transactions existantes, le reste NULL/False.

### 3.3 Modèle d'éclatement (résumé)

Une transaction éclatée T (ex. +280 €, `source=csv`) :
- reçoit `is_split_parent = True` → **disparaît** des listes API et de tous les agrégats (CR, bilan, solde catégorisé) ;
- ses enfants C1…Cn (`source=manual`, `parent_transaction_id = T.id`) ont chacun leur `category_id`, et **∑ montants(Ci) = montant(T)** ;
- le solde reste cohérent : la somme des enfants égalant la parente, retirer T et ajouter les Ci ne change pas le solde net du bien.

---

## 4. Service d'ingestion unifié

### 4.1 Signature

```python
def ingest_transactions(
    db: Session,
    property_id: int,
    account_id: int | None,
    rows: list[IngestRow],
    source: str,  # "csv" | "api" | "manual"
) -> IngestResult:
    ...
```

`IngestRow` : forme normalisée `{date, montant_centimes, nom, external_id?}`.
`IngestResult` : `{inserted, deduplicated, classified, unclassified, errors}` (remonté à l'UI).

### 4.2 Pipeline (une seule transaction DB, rollback complet sur erreur)

`normalisation → dédoublonnage → insertion → classification par règles → recalcul soldes → recalcul amortissements concernés`

- **Normalisation** : dates, montants en **centimes** (Integer), trim des noms.
- **Dédoublonnage** :
  - si `external_id` présent (source `api`) → clé `(account_id, external_id)` ;
  - sinon (source `csv`/`manual`) → clé de repli `(property_id, date, montant_centimes, nom)` (l'égalité au centime remplace l'égalité float).
  - À la 1re synchro API d'un compte ayant un historique CSV (étape 5), la fenêtre de recouvrement est dédupliquée par la clé de repli — prévu ici, exercé en étape 5.
- **Classification** : réutilise le moteur de l'étape 3 (`classification_engine` / `enrichment_service`) — pose `category_id` si une règle matche, sinon laisse NULL (→ Boîte de réception).
- **Recalcul soldes** : solde courant par bien, recalculé sur la plage impactée.
- **Recalcul amortissements** : uniquement les amortissements des transactions d'immobilisation concernées.
- **Atomicité** : tout dans un `begin`/`commit` ; toute erreur → `rollback` complet + erreur remontée (jamais avalée), conformément à §7 et §9 de la spec mère.

### 4.3 Rebranchement de l'import CSV

La route `POST /api/transactions/import` (actuellement à `transactions.py:951`) est réécrite pour :
1. parser le CSV (logique de parsing conservée),
2. appeler `ingest_transactions(db, property_id, account_id=None, rows, source="csv")`.

Comportement utilisateur **inchangé**. Le suivi `FileImport` (historique des imports) est conservé. Réimporter un CSV déjà importé → 0 insertion (dédoublonnage) → **aucun chiffre modifié**.

---

## 5. Classification (rappel, réutilisation étape 3)

Aucune nouveauté de moteur. Toute transaction entrante (CSV, API, manuelle) passe par le moteur de règles unifié :
- match → `category_id` posé ;
- pas de match → `category_id` NULL → apparaît dans la **Boîte de réception**, où « Valider » crée la règle (`source=auto_from_inbox`).

Pour une transaction **manuelle**, l'utilisateur peut aussi fixer directement la catégorie via le `CategorySelector` (étape 3) au moment de la création — court-circuit équivalent à une classification immédiate.

---

## 6. Saisie manuelle (backend + UI minimale)

Toutes les actions produisent des transactions `source="manual"` et **passent par le tuyau d'ingestion** (donc classées + recalculées comme le reste). UI posée sur « Toutes les transactions ».

### 6.1 Créer une transaction (➕ Ajouter)

Formulaire : date, montant (€ → centimes), nom, catégorie (optionnelle via `CategorySelector`). Crée une transaction manuelle unique. Sans catégorie → Boîte de réception.

### 6.2 Éclater une ligne (✂️)

Depuis une transaction existante (ex. +280 € matera) :
- l'utilisateur saisit N lignes `{montant, nom, catégorie}` ;
- **garde-fou dur** : ∑ montants = montant de la ligne d'origine, sinon **refus** (erreur affichée, rien créé) ;
- effet : la ligne d'origine reçoit `is_split_parent=True` (masquée + hors totaux) ; N enfants créés (`source=manual`, `parent_transaction_id` = ligne d'origine), chacun classé ;
- **annulable** : « défaire l'éclatement » remet la parente visible et supprime les enfants (recalcul).

### 6.3 Écriture croisée / paire qui s'annule (⇄)

Mini-formulaire pour un mouvement payé/reçu via un autre compte (ex. frais de notaire payés ailleurs) :
- crée **deux** transactions manuelles opposées sur le même bien : `−X` (la dépense réelle, ex. *Frais de notaire*) et `+X` (la contrepartie, ex. *Compte courant d'associé*), chacune avec sa catégorie ;
- **garde-fou** : les deux montants s'annulent (net 0 sur le solde du compte) ;
- les deux lignes sont des transactions manuelles indépendantes, mais **créées ensemble** par le formulaire. Pas de champ de liaison en base (YAGNI) ; l'intégrité est protégée au niveau UI : supprimer l'une propose de supprimer aussi l'autre (sinon les livres se déséquilibrent).

---

## 7. API (backend)

| Méthode | Route | Rôle |
|---|---|---|
| `POST` | `/api/transactions/import` | **réécrit** : parse CSV → `ingest_transactions(source=csv)` |
| `POST` | `/api/transactions/manual` | crée une transaction manuelle (§6.1) |
| `POST` | `/api/transactions/{id}/split` | éclate une ligne en N enfants (§6.2), garde-fou somme |
| `DELETE` | `/api/transactions/{id}/split` | défait l'éclatement (§6.2) |
| `POST` | `/api/transactions/cross-entry` | crée la paire qui s'annule (§6.3), garde-fou net 0 |

Toutes valident `property_id` explicite, montants en centimes, erreurs remontées (jamais avalées). Les listes de transactions (`GET /api/transactions`) **excluent** les lignes `is_split_parent=True`.

---

## 8. Tests & validation

- **Ingestion** : dédoublonnage par `external_id` ; dédoublonnage par clé de repli CSV ; insertion + classification par règle existante ; transaction non matchée → NULL (inbox).
- **Réimport CSV** : réimporter le même fichier → 0 insertion ; **golden master 0 écart**.
- **Atomicité** : une erreur en milieu de lot → rollback complet (aucune insertion partielle).
- **Éclatement** : somme correcte → parente masquée + hors totaux + enfants classés + solde inchangé + CR reflète les N catégories ; somme incorrecte → refus, rien créé ; annulation → état initial restauré.
- **Écriture croisée** : net 0 sur le solde ; les deux lignes classées (charge + passif) ; suppression conjointe.
- **Non-régression** : `check_rules_no_regression.py` → 0 ; **golden master** (tag courant) → 0.
- Tests dans le **harnais isolé** (fixtures `db_session`/`client`), jamais sur la base de prod.

---

## 9. Risques & parades

| Risque | Parade |
|---|---|
| Double comptage d'une ligne éclatée | `is_split_parent` exclu de **tous** les agrégats + des listes ; tests dédiés CR/solde |
| Éclatement dont la somme ≠ original | Garde-fou dur côté service (refus + erreur), pas seulement UI |
| Réimport CSV qui modifie les chiffres | Dédoublonnage clé de repli au centime + golden 0 en test |
| Insertion partielle sur erreur de lot | Une seule transaction DB, rollback complet |
| Historique CSV redupliqué à la 1re synchro API (étape 5) | Fenêtre de recouvrement dédupliquée par clé de repli (prévu §4.2) |
| Migration de schéma corrompt la base | Backup `.db` horodaté avant migration ; ajout de colonnes only |
| IBAN en clair | `iban_masked` uniquement ; secrets/clés hors repo (rappel étape 5) |

---

## 10. Livrable de fin d'étape

- Table `bank_accounts` créée (vide) ; `transactions` + `account_id`/`external_id`/`source`/`parent_transaction_id`/`is_split_parent`.
- Service `ingest_transactions` unique, atomique ; import CSV rebranché (comportement inchangé).
- Saisie manuelle : créer / éclater / écriture croisée, sur « Toutes les transactions ».
- Suite de tests verte ; non-régression 0 ; **golden master 0 écart**.
- Prêt pour l'étape 5 (Enable Banking) : il ne restera qu'à brancher le client API sur `ingest_transactions(source="api")` et remplir `bank_accounts`.
