# Étape 5 — Intégration Enable Banking

**Statut** : Design validé (brainstorm 2026-07-15) — à relire par Louis avant plan d'implémentation.
**Réf.** : spec mère `2026-07-10-refonte-lmnp-design.md` §7 partie 2, §11 point 5 ; mémoire `project-enable-banking-lmnp` ; blueprint `~/Claude/compta_sasu` (`backend/services/banking.py`, `routes/banking.py`, `frontend/app/banking/page.tsx`, `docs/integrations/enablebanking.md`).
**Branche** : `refonte`. **Prérequis** : étape 4 livrée (service `ingest_transactions`, table `bank_accounts`, champs `account_id/external_id/source` sur transactions) — OK (HEAD 3d65219).

---

## 1. Périmètre

Porter le module Enable Banking éprouvé de `compta_sasu` et l'adapter à LMNP : client PSD2 (JWT RS256), flux de connexion bancaire avec **page de retour automatique**, **onglet « Paramètres »** dans Transactions pour configurer **par appartement** la banque et le compte, moteur de **synchro incrémentale** branché sur `ingest_transactions(source="api")`, et **alerte de renouvellement** du consentement.

**Approche : mock-first.** Toute l'intégration est construite et testée contre le **simulateur** (seam `is_live()` du blueprint) — golden 0, sans jamais manipuler ni committer les secrets de Louis. Louis branche sa vraie banque lui-même ensuite (sa clé privée dans un `.env`/`secrets/` gitignoré).

**Hors périmètre** :
- Webhooks Enable Banking (documentés mais jamais codés dans le blueprint) → non implémentés.
- Synchro automatique à l'ouverture de l'app (>6 h) → **bouton manuel d'abord** ; auto-sync = suivi facile ultérieur.
- Logique métier SASU du blueprint (factures, FX réalisé, `reconcile_payments`, `allocate_fx_realized`) → non portée ; remplacée par le pipeline LMNP (`ingest_transactions`).
- Fiscalité 39C, dashboard → étapes 6 / §8bis.
- Drop des tables legacy (étape 3 Task 10) → toujours différé.

---

## 2. Décisions verrouillées (brainstorm 2026-07-15)

1. **Mock-first** : dev/test en mock ; Louis branche le réel avec ses secrets. Je ne manipule ni ne commite aucun secret.
2. **Onglet « Paramètres »** dans Transactions (pas de page top-level séparée) : configuration **par appartement** (banque + compte).
3. **Un compte bancaire par appartement** (décision étape 4) : la liaison rattache **un** compte à un `property_id`.
4. **Page de retour automatique** (localhost capte le code OAuth) — pas de copier-coller manuel (amélioration vs blueprint).
5. **Bouton « Synchroniser » manuel** d'abord.
6. **Import CSV conservé** à côté (historique).
7. **Corrections vs blueprint** : synchro **incrémentale** (curseur `last_tx_cursor` / `last_sync_at`, plus de `date_from` figé) ; **filtrer les transactions `pending`**.
8. **Golden** : re-extraire un tag `v5-avant-enable-banking` avant tout branchement réel ; golden 0 sur l'existant à chaque étape.

---

## 3. Architecture

```
Frontend (onglet Paramètres, par bien)
  └─ bankingAPI (client.ts)  ──► Routes /api/banking (property-scoped)
                                    └─ services/banking_service.py (porté de compta_sasu)
                                          ├─ seam is_live() : mock | live
                                          ├─ client PSD2 : JWT RS256, /aspsps, /auth, /sessions, /accounts
                                          └─ sync ──► ingest_transactions(db, property_id, account_id, rows, "api")  [étape 4]
                                                        └─ dédoublonnage (account_id, external_id) + règles + recalculs
```

Le service `banking_service.py` est **isolé** : il ne connaît que Enable Banking et délègue **toute** l'insertion/classification/recalcul à `ingest_transactions`. Aucune logique de calcul financier dedans.

---

## 4. Config & secrets (mock/live seam)

Variables d'environnement (fichier `.env` gitignoré, jamais commité) :
- `ENABLE_BANKING_APP_ID` — l'application_id Enable Banking de Louis.
- `ENABLE_BANKING_PRIVATE_KEY_PATH` — chemin du PEM (défaut `./secrets/eb_private.pem`, dossier `secrets/` gitignoré).
- `ENABLE_BANKING_REDIRECT_URL` — URL de retour (défaut `http://localhost:3000/dashboard/transactions?tab=parametres&eb_callback=1`).

`is_live()` (porté) = `app_id` non vide **ET** fichier clé présent **ET** `pyjwt` importable. Sinon **mock** (données déterministes : banques FR, comptes, transactions de test incluant une paire FX partageant un `transaction_id` sur 2 comptes, pour prouver le dédoublonnage par `(account_id, external_id)`). `.gitignore` doit couvrir `.env`, `secrets/`, `*.pem`. JWT RS256 forgé à chaque appel (`iss=enablebanking.com`, `aud=api.enablebanking.com`, `exp=+3600`, header `kid=app_id`). Base API `https://api.enablebanking.com`.

`GET /api/banking/status` → `{live, message}` (message explique pourquoi mock : app_id manquant / clé introuvable / pyjwt absent).

---

## 5. Modèle de données

**Réutilise `bank_accounts` de l'étape 4** (déjà : `id, property_id (FK), bank_name, iban_masked, eb_account_uid, eb_session_id, session_valid_until, last_sync_at, last_tx_cursor`). Aucun nouveau champ nécessaire a priori ; si un champ manque au portage (ex. `currency`, `bank_balance`, `provider`), l'ajouter par migration additive (golden neutre).

**Transactions** : `account_id`, `external_id`, `source="api"` (étape 4). Dédoublonnage **composite `(account_id, external_id)`** (index partiel unique + contrôle applicatif dans `ingest_transactions`) — jamais `external_id` seul (piège FX). Déjà en place.

**State CSRF** : en mémoire process (`set` de states), suffisant en mono-poste localhost (comme le blueprint). Documenté comme limite (pas multi-instance).

---

## 6. Flux de connexion (par appartement)

1. **Lister les banques** — `GET /api/banking/aspsps?country=FR` → liste ASPSP France.
2. **Démarrer** — `POST /api/banking/connect {property_id, aspsp_name}` : génère `state` (anti-CSRF, associé au `property_id`), POST `/auth` (access valid ~180 j, `redirect_url`, `psu_type` adapté), renvoie `{authorization_url, state}`.
3. **Consentement** — l'utilisateur est redirigé vers sa banque, approuve.
4. **Retour automatique** — la banque redirige vers `redirect_url` (page Paramètres avec `?code=...&state=...`). Le frontend **lit le code+state automatiquement** et appelle `POST /api/banking/sessions {code, state}`.
5. **Preview comptes** — `create_session` vérifie le `state`, POST `/sessions`, retourne `{session_id, session_valid_until, accounts:[{account_uid, name, iban_masked, currency}, ...]}` (preview non persistée).
6. **Sélection (un compte)** — `POST /api/banking/connections/select {property_id, account_uid, session_id, session_valid_until}` : upsert **une** ligne `bank_accounts` pour ce `property_id` (remplace si déjà lié), stocke `eb_account_uid`, `eb_session_id`, `session_valid_until`. Une première synchro peut être déclenchée juste après.

---

## 7. Moteur de synchro

`POST /api/banking/sync {property_id}` (ou tous les biens) → pour chaque `bank_accounts` concerné, **en SAVEPOINT isolé** (un compte en échec ne bloque pas les autres) :
1. **Fenêtre incrémentale** : depuis `last_sync_at`/`last_tx_cursor` (plus de `date_from` figé). Pagination par `continuation_key`.
2. **Filtrer les `pending`** (transactions non comptabilisées ignorées jusqu'à confirmation).
3. **Normaliser** en lignes `{date, quantite, nom, external_id}` (montants en euros → EuroCents géré en aval).
4. **Ingestion** : `ingest_transactions(db, property_id, account_id, rows, "api")` — dédoublonnage `(account_id, external_id)` + classement par règles + recalcul soldes + amortissements (tout le pipeline étape 4).
5. **Mettre à jour** `last_sync_at`, `last_tx_cursor`, et le solde banque du compte (live : GET `/accounts/{uid}/balances` ; mock : dérivé).
6. Retour `{par compte : {inserted, deduplicated, errors}}` affiché dans l'UI (erreurs jamais avalées).

Une **sauvegarde `.db` horodatée** est prise avant tout `sync` réel (fail-closed, comme le blueprint).

---

## 8. Renouvellement du consentement

`session_valid_until` est stocké à la sélection du compte. L'onglet Paramètres affiche, par compte, l'échéance ; **dès J‑30**, un bandeau orange « consentement à renouveler » avec un bouton qui relance le flux de connexion (§6) pour ce bien. Une expiration détectée en synchro (401) est remontée clairement (pas avalée) et invite au renouvellement.

---

## 9. UI — onglet « Paramètres » (dans Transactions)

Nouvel onglet `?tab=parametres` (via `Navigation.tsx`). Contenu, **cadré par le bien actif** :
- **Carte statut** : live/mock + message (rappel : mets `ENABLE_BANKING_APP_ID` + clé pour passer en réel).
- **Connecter une banque** : liste ASPSP → bouton → redirection consentement → **retour auto** → liste des comptes (preview) → **sélection d'un compte** pour ce bien.
- **Compte connecté** (carte) : nom, IBAN masqué, solde banque, dernière synchro, **échéance consentement** (+ alerte J‑30), bouton **Déconnecter** (conserve les transactions), bouton **Synchroniser**.
- **Import CSV** : section conservée (historique).
Erreurs en bannière `role="alert"`, style cohérent (navy #1e3a5f).

---

## 10. API (backend, préfixe `/api/banking`)

| Méthode | Path | Rôle |
|---|---|---|
| GET | `/aspsps?country=FR` | liste banques |
| POST | `/connect` `{property_id, aspsp_name}` | démarre OAuth → `{authorization_url, state}` |
| POST | `/sessions` `{code, state}` | échange code → preview comptes + `session_valid_until` |
| POST | `/connections/select` `{property_id, account_uid, session_id, session_valid_until}` | lie **un** compte au bien |
| GET | `/connections?property_id=` | compte(s) lié(s) à un bien |
| POST | `/sync` `{property_id}` | synchro (via ingest_transactions) |
| DELETE | `/connections/{account_id}` | déconnecte (garde les transactions) |
| GET | `/status` | `{live, message}` |

Tous property-scoped, erreurs remontées (jamais avalées), `property_id` explicite.

---

## 11. Tests & validation

- **Mock** : flux complet testé sans credentials — liste banques, connect (state), sessions (preview), select (upsert 1 compte/bien), sync (pagination mock, filtrage pending, dédoublonnage `(account_id, external_id)` y compris la paire FX partagée, classement par règles, recalculs), déconnexion, statut.
- **Incrémental** : 2e sync ne réingère pas les mêmes transactions (curseur/dédoublonnage).
- **Consentement** : `session_valid_until` stocké ; alerte J‑30 calculée correctement.
- **Golden** : re-extraire `v5-avant-enable-banking` ; golden 0 sur l'existant après le portage (le mock n'écrit pas dans les données réelles des tests golden). Non-régression règles 0.
- Harnais isolé (`db_session`/`client`), jamais la base de prod.

---

## 12. Risques & parades

| Risque | Parade |
|---|---|
| Secrets committés | `.env`/`secrets/`/`*.pem` gitignorés ; jamais manipulés côté assistant ; seam mock par défaut |
| Historique CSV redupliqué à la 1re synchro API | Dédoublonnage `(account_id, external_id)` + clé de repli CSV (étape 4) ; fenêtre de recouvrement gérée |
| FX : même `transaction_id` sur 2 comptes | Dédoublonnage **composite** `(account_id, external_id)`, jamais `external_id` seul (test mock dédié) |
| `date_from` figé (bug blueprint) | Synchro incrémentale via `last_sync_at`/`last_tx_cursor` |
| Transactions `pending` comptées trop tôt | Filtrées jusqu'à comptabilisation |
| Consentement expiré silencieusement | `session_valid_until` stocké + alerte J‑30 + 401 remonté |
| Un compte en échec bloque les autres | SAVEPOINT par compte |
| Chiffres des années passées modifiés | Golden `v5-avant-enable-banking` pour distinguer nouvelles transactions (légitimes) vs régressions |

---

## 13. Livrable de fin d'étape

- Service `banking_service.py` (mock/live) + routes `/api/banking` property-scoped.
- Onglet Paramètres : connexion (retour auto) + sélection d'un compte par bien + carte compte + synchro manuelle + alerte J‑30.
- Synchro branchée sur `ingest_transactions(source="api")`, incrémentale, filtrage pending, SAVEPOINT par compte.
- Secrets 100% côté Louis (gitignorés) ; app fonctionnelle en mock sans credentials.
- Tests mock verts ; golden 0 ; non-régression 0 ; tag `v5-avant-enable-banking` extrait.
- Prêt : Louis met sa clé + son app_id, connecte sa vraie banque via l'onglet Paramètres, synchronise.
