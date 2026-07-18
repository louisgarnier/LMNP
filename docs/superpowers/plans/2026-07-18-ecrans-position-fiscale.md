# Écrans de position fiscale (Maquettes 1 & 2) — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Afficher la position fiscale de l'entité dans l'appli : une **vision globale** (résultat par appartement + les deux tirelires déficit/amortissements, App vs Officiel) et un **détail par appartement** (compte de résultat groupé, App/Liasse/Écart). Données réelles via `/api/reconciliation`.

**Architecture:** Le backend `reconciliation_service.py` calcule déjà par exercice le détail par bien (produits/résultat/amortissements) et les lignes fiscales d'entité (déficit de l'exercice, déficit reportable cumulé App/Officiel/Écart, imposable). Ce plan (1) enrichit ce service avec le CR groupé par bien (charges externes, impôts, intérêts) et une ligne comparée "Amortissements reportés (cumulé)", puis (2) ajoute deux pages Next.js qui consomment ce service, fidèles aux maquettes validées.

**Tech Stack:** Python 3.10 / FastAPI / SQLAlchemy / pytest (backend) ; Next.js App Router / React / TypeScript (frontend).

## Global Constraints

- **Maquettes de référence (rendu cible EXACT)** dans `docs/project/analysis/maquettes-position-fiscale/` : `maquette1-globale.html` (vision globale), `maquette2-detaillee.html` (détail par appartement). L'implémenteur DOIT les ouvrir et reproduire la structure/les couleurs.
- **Aucune donnée en dur** : parcours dynamique des propriétés (`db.query(Property)`), années dérivées des transactions. Ajouter un bien ne casse rien.
- **Fiscal = niveau ENTITÉ** (déficit, imposable, tirelires) : jamais ventilé par bien. Seul le CR (produits, charges, résultat) est ventilé par bien.
- **Tolérance d'arrondi** : liasses en euros entiers → écart de ligne ≤ 1 € = conforme (`ok=True`), affiché `✓`.
- **Lecture seule sur la vraie base** : les tests backend touchant la base utilisent le moteur `?mode=ro` (motif sanctionné, cf. `test_reconciliation_service.py`), jamais `SessionLocal` (garde de quarantaine prod).
- **Positionnement GLOBAL** : ces vues ne dépendent d'aucun appartement actif (cf. `GLOBAL_ROUTES` dans `frontend/app/dashboard/layout.tsx`, déjà en place pour `/dashboard/liasse-fiscale`).
- **HORS PÉRIMÈTRE de ce plan** (plans suivants) : le choix d'imputation par année (toggle déficit/amort qui recalcule le moteur), la refonte de la page d'accueil, le chargement de liasse + pièces jointes, la "reprise des reports" (calcul 2026+ depuis la position officielle). Les vues de ce plan affichent le calcul actuel (déficit-d'abord) + la comparaison ; le toggle viendra ensuite.

---

## Fichiers

- Modifier : `backend/api/services/reconciliation_service.py` — CR groupé par bien + ligne "Amortissements reportés (cumulé)".
- Modifier : `docs/project/reference/liasses/liasse-2021.json` … `liasse-2025.json` — ajout `stock_amort_reporte_reconstitue`.
- Modifier : `backend/tests/test_reconciliation_service.py` — tests des nouveautés.
- Créer : `frontend/app/dashboard/liasse-fiscale/detail/page.tsx` — Maquette 2 (détail par appartement).
- Modifier : `frontend/app/dashboard/liasse-fiscale/page.tsx` — remplacer par la Maquette 1 (vision globale) + lien vers le détail.
- Modifier : `frontend/app/dashboard/layout.tsx` — étendre `GLOBAL_ROUTES` à la sous-route détail.

---

## Task 1 : CR groupé par appartement dans la réconciliation

Maquette 2 a besoin, par bien, de : produits, charges externes (total), impôts et taxes, amortissements, intérêts d'emprunt, résultat. Le service expose déjà produits/résultat/amortissements par bien ; on ajoute charges externes, impôts, intérêts.

**Files:**
- Modify: `backend/api/services/reconciliation_service.py` (fonction `_per_bien_cr`, lignes ~45-58)
- Test: `backend/tests/test_reconciliation_service.py`

**Interfaces:**
- Consumes: `calculate_compte_resultat(db, year, property_id)` → dict avec `total_produits: float`, `resultat_net: float`, `amortissements: float`, `cout_financement: float`, et `charges: dict[str, float]` dont les clés incluent `"Impôts et taxes"`, `"Charges d'amortissements"`, `"Coût du financement (hors remboursement du capital)"`, et les charges externes (`"Fluides non refacturés"`, `"Travaux et mobilier"`, `"Honoraires"`, `"Charges de copropriété hors fonds travaux"`, `"Assurances"`, `"Autres charges diverses"`).
- Produces: `_per_bien_cr(db, year)` retourne `{pid: {"produits", "charges_externes", "impots", "amortissements", "interets", "resultat"}}` (tous des floats arrondis à 2 décimales ; charges/impôts/intérêts/amortissements en valeur NÉGATIVE comme des charges).

- [ ] **Step 1 : Écrire le test (doit échouer)**

```python
# à ajouter dans backend/tests/test_reconciliation_service.py
def test_per_bien_cr_groupe_les_charges():
    from backend.api.services.reconciliation_service import _per_bien_cr
    db = _ROSession()
    try:
        cr = _per_bien_cr(db, 2025)
    finally:
        db.close()
    evry = cr[25]
    # clés attendues
    assert set(evry) == {"produits", "charges_externes", "impots", "amortissements", "interets", "resultat"}
    # 2025 Evry (valeurs réelles connues, signe charges = négatif)
    assert evry["produits"] == pytest.approx(23803.02, abs=1.0)
    assert evry["impots"] == pytest.approx(-2323, abs=1.0)
    assert evry["amortissements"] == pytest.approx(-11119, abs=1.0)
    assert evry["interets"] == pytest.approx(-2489, abs=1.0)
    # charges externes = toutes charges hors impôts/amort/intérêts
    assert evry["charges_externes"] == pytest.approx(-11263, abs=2.0)
    # cohérence : produits + charges_externes + impots + amortissements + interets == resultat
    somme = (evry["produits"] + evry["charges_externes"] + evry["impots"]
             + evry["amortissements"] + evry["interets"])
    assert somme == pytest.approx(evry["resultat"], abs=0.5)
```

- [ ] **Step 2 : Lancer, vérifier l'échec**

Run : `cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/TEST/LMNP" && python3 -m pytest backend/tests/test_reconciliation_service.py::test_per_bien_cr_groupe_les_charges -q -p no:cacheprovider`
Expected : FAIL — `KeyError: 'charges_externes'`.

- [ ] **Step 3 : Modifier `_per_bien_cr`**

Remplacer le corps de `_per_bien_cr` par :

```python
def _per_bien_cr(db, year):
    """{pid: {produits, charges_externes, impots, amortissements, interets, resultat}}
    pour les biens ACTIFS l'année. Charges en valeur négative. Aucun bien codé en dur.
    """
    # catégories de charges NON externes (traitées à part)
    IMPOTS = "Impôts et taxes"
    AMORT = "Charges d'amortissements"
    FIN = "Coût du financement (hors remboursement du capital)"
    out = {}
    for prop in db.query(Property).all():
        cr = calculate_compte_resultat(db, year, property_id=prop.id)
        produits = cr.get("total_produits", 0.0)
        resultat = cr.get("resultat_net", 0.0)
        charges = cr.get("charges", {})
        impots = charges.get(IMPOTS, 0.0)
        amort = -abs(cr.get("amortissements", 0.0))
        interets = -abs(cr.get("cout_financement", 0.0))
        charges_externes = sum(v for k, v in charges.items()
                               if k not in (IMPOTS, AMORT, FIN))
        if (abs(produits) > _EPS or abs(resultat) > _EPS or abs(amort) > _EPS):
            out[prop.id] = {
                "produits": round(produits, 2),
                "charges_externes": round(charges_externes, 2),
                "impots": round(impots, 2),
                "amortissements": round(amort, 2),
                "interets": round(interets, 2),
                "resultat": round(resultat, 2),
            }
    return out
```

Puis dans `reconcile()`, adapter l'extraction des dicts par bien (les lignes ~123-125) :

```python
        produits_bien = {pid: v["produits"] for pid, v in cr_bien.items()}
        resultat_bien = {pid: v["resultat"] for pid, v in cr_bien.items()}
        amort_bien = {pid: -v["amortissements"] for pid, v in cr_bien.items()}  # ligne "Amortissements" attend une valeur positive comme avant
```

⚠️ La ligne `_ligne("Amortissements", amort_bien, cr["dotations_amortissements"])` comparait une valeur POSITIVE (`abs`) à la liasse positive. `_per_bien_cr` renvoie désormais l'amortissement en négatif ; on remet en positif via `-v["amortissements"]` ci-dessus pour ne pas changer le contrat de la ligne "Amortissements" existante (Task 3 lira le CR groupé complet, pas cette ligne).

- [ ] **Step 4 : Lancer, vérifier PASS**

Run : `cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/TEST/LMNP" && python3 -m pytest backend/tests/test_reconciliation_service.py -q -p no:cacheprovider`
Expected : PASS (tous les tests, dont l'existant `test_detail_par_bien_2025_somme_egale_total` qui vérifie que Produits par bien somme au total — inchangé).

- [ ] **Step 5 : Produire les 6 lignes comptables groupées (par bien + comparaison liasse)**

Remplacer, dans `reconcile()`, les 3 lignes comptables actuelles (Produits, Résultat comptable, Amortissements) par les **6 lignes groupées**, chacune avec `par_bien` (issu de `cr_bien`) et comparaison à la liasse. ⚠️ **Signe** : la liasse stocke les charges en POSITIF (`autres_charges_externes: 40278`) mais l'appli en NÉGATIF ; on compare donc à `-liasse` pour les postes de charges. Le résultat comptable est négatif des deux côtés (pas de négation).

Construire les dicts par bien pour chaque poste et les lignes (branche AVEC liasse) :

```python
        produits_bien = {pid: v["produits"] for pid, v in cr_bien.items()}
        cext_bien = {pid: v["charges_externes"] for pid, v in cr_bien.items()}
        impots_bien = {pid: v["impots"] for pid, v in cr_bien.items()}
        amort_bien_neg = {pid: v["amortissements"] for pid, v in cr_bien.items()}  # négatif
        interets_bien = {pid: v["interets"] for pid, v in cr_bien.items()}
        resultat_bien = {pid: v["resultat"] for pid, v in cr_bien.items()}

        # branche AVEC liasse :
            lignes = [
                _ligne("Produits", produits_bien, cr["produits"]),
                _ligne("Charges externes", cext_bien, -cr["autres_charges_externes"]),
                _ligne("Impôts et taxes", impots_bien, -cr["impots_et_taxes"]),
                _ligne("Amortissements", amort_bien_neg, -cr["dotations_amortissements"]),
                _ligne("Intérêts d'emprunt", interets_bien, -cr["charges_financieres"]),
                _ligne("Résultat comptable", resultat_bien, cr["resultat_comptable"]),
                _ligne_entite("Déficit de l'exercice", fisc.get("deficit_annee", 0.0),
                              fis.get("deficit_reportable_de_lannee", 0)),
                _ligne_entite("Déficit reportable (cumulé)",
                              fisc.get("stock_deficit_fin", 0.0),
                              fis.get("stock_deficit_reportable_fin")),
                _ligne_entite("Amortissements reportés (cumulé)",
                              fisc.get("stock_amort_fin", 0.0),
                              fis.get("stock_amort_reporte_reconstitue")),
                _ligne_entite("Résultat fiscal imposable",
                              fisc.get("resultat_fiscal_imposable", 0.0),
                              fis["resultat_fiscal_imposable"]),
            ]
```

Branche BROUILLON (sans liasse) : mêmes 6 lignes comptables + fiscales avec `None` comme valeur liasse (via `_ligne(..., None)` / `_ligne_entite(..., None)`).

Puis ajouter `cr_par_bien` au dict de sortie :

```python
        out[year] = {
            "annee": year, "brouillon": brouillon, "biens_inclus": biens,
            "cr_par_bien": cr_bien,
            "composition": composition, "lignes": lignes,
            "stock_deficit_appli": round(fisc.get("stock_deficit_fin", 0.0), 2),
            "nb_ecarts": nb_ecarts,
        }
```

- [ ] **Step 6 : Tests des lignes groupées**

Adapter/ajouter (les anciens tests référençant "Amortissements" avec valeur positive doivent devenir négatifs, et "Déficit de l'exercice" existe toujours) :

```python
def test_lignes_groupees_2025_signe_et_ecart(rec):
    lignes = {l["poste"]: l for l in rec[2025]["lignes"]}
    assert set(lignes) >= {"Produits", "Charges externes", "Impôts et taxes",
                           "Amortissements", "Intérêts d'emprunt", "Résultat comptable",
                           "Déficit reportable (cumulé)", "Amortissements reportés (cumulé)"}
    # charges externes : app négatif, comparé à −liasse, écart ~0
    ce = lignes["Charges externes"]
    assert ce["app"] == pytest.approx(-40278, abs=2.0)
    assert ce["liasse"] == pytest.approx(-40278, abs=2.0)
    assert ce["ok"] is True
    # intérêts : l'erreur cabinet de 64 €
    it = lignes["Intérêts d'emprunt"]
    assert it["ok"] is False
    assert abs(it["ecart"]) == pytest.approx(64, abs=2.0)
    # somme par bien = total app sur chaque ligne comptable
    for poste in ("Produits", "Charges externes", "Résultat comptable"):
        l = lignes[poste]
        assert round(sum(l["par_bien"].values()), 2) == pytest.approx(l["app"], abs=0.5)

def test_reconcile_expose_cr_par_bien(rec):
    assert "charges_externes" in rec[2025]["cr_par_bien"][25]
```

Ajuster les tests existants devenus faux (ex. un test qui asserte "Amortissements" > 0). Run : `python3 -m pytest backend/tests/test_reconciliation_service.py -q -p no:cacheprovider` → PASS.

- [ ] **Step 7 : Commit**

```bash
cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/TEST/LMNP"
git add backend/api/services/reconciliation_service.py backend/tests/test_reconciliation_service.py
git commit -m "[REFONTE] feat: CR groupé par appartement (charges externes/impôts/intérêts) dans la réconciliation"
```

---

## Task 2 : Valeurs officielles reconstituées de la 2e tirelire (amort. reportés)

La ligne "Amortissements reportés (cumulé)" est déjà produite par `reconcile()` (Task 1, Step 5) et compare `fisc.stock_amort_fin` (App) à `liasse.fiscal.stock_amort_reporte_reconstitue` (Officiel). Tant que cette clé est absente des JSON, la colonne Officiel/Écart affiche `—`. Cette tâche **ajoute les valeurs reconstituées** aux 5 liasses pour activer la comparaison.

**Files:**
- Modify: `docs/project/reference/liasses/liasse-2021.json` … `liasse-2025.json`
- Test: `backend/tests/test_reconciliation_service.py`

**Interfaces:**
- Produces: clé `stock_amort_reporte_reconstitue` (float) dans le bloc `fiscal` de chaque liasse 2021-2025.

- [ ] **Step 1 : Ajouter la valeur reconstituée aux 5 liasses**

Dans le bloc `"fiscal"` de chaque fichier, ajouter la clé `stock_amort_reporte_reconstitue` (valeurs calculées des FEC/liasses, cf. REPRENDRE-ICI.md) :
- `liasse-2021.json` : `"stock_amort_reporte_reconstitue": 332`
- `liasse-2022.json` : `"stock_amort_reporte_reconstitue": 4550`
- `liasse-2023.json` : `"stock_amort_reporte_reconstitue": 473`
- `liasse-2024.json` : `"stock_amort_reporte_reconstitue": 15026`
- `liasse-2025.json` : `"stock_amort_reporte_reconstitue": 35364`

Vérifier après édition que chaque fichier reste un JSON valide :
`for f in docs/project/reference/liasses/liasse-202*.json; do python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$f" || echo "INVALIDE $f"; done`

- [ ] **Step 2 : Écrire le test (doit échouer)**

```python
def test_amort_reporte_cumule_compare(rec):
    l = next(x for x in rec[2025]["lignes"] if x["poste"] == "Amortissements reportés (cumulé)")
    assert l["par_bien"] is None            # entité, pas de ventilation
    assert l["app"] == pytest.approx(39933, abs=1.0)
    assert l["liasse"] == pytest.approx(35364, abs=1.0)
    assert l["ecart"] == pytest.approx(4569, abs=1.0)
    assert l["ok"] is False
```

Run : `python3 -m pytest backend/tests/test_reconciliation_service.py::test_amort_reporte_cumule_compare -q -p no:cacheprovider` → FAIL avant l'ajout des valeurs (la ligne existe déjà via Task 1 mais `liasse`/`ecart` valent `None`, donc l'assertion sur `liasse ≈ 35364` échoue).

- [ ] **Step 3 : (rien à coder — la ligne est déjà produite par Task 1)**

Vérifier seulement que `reconcile()` contient bien la ligne `_ligne_entite("Amortissements reportés (cumulé)", fisc.get("stock_amort_fin", 0.0), fis.get("stock_amort_reporte_reconstitue"))` (ajoutée en Task 1). Sinon, l'ajouter.

- [ ] **Step 4 : Lancer, vérifier PASS**

Run : `python3 -m pytest backend/tests/test_reconciliation_service.py -q -p no:cacheprovider`
Expected : PASS. Note : `nb_ecarts` de plusieurs années augmente (l'amort reporté diverge) — c'est correct. Si `test_2024_annee_conforme...` casse sur un compte d'écarts, l'ajuster pour refléter que l'amort reporté cumulé 2024 diverge aussi (l'anomalie 2023 se propage aux deux tirelires).

- [ ] **Step 5 : Commit**

```bash
cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/TEST/LMNP"
git add docs/project/reference/liasses/liasse-202*.json backend/api/services/reconciliation_service.py backend/tests/test_reconciliation_service.py
git commit -m "[REFONTE] feat: ligne Amortissements reportés (cumulé) comparée (2e tirelire)"
```

---

## Task 3 : Page Maquette 2 — détail par appartement

Nouvelle page `/dashboard/liasse-fiscale/detail`. Sélecteur d'année ; par appartement : produits, charges externes, impôts, amortissements, intérêts, résultat ; colonnes Total app / Liasse / Écart. Rendu cible EXACT : `docs/project/analysis/maquettes-position-fiscale/maquette2-detaillee.html`.

**Files:**
- Create: `frontend/app/dashboard/liasse-fiscale/detail/page.tsx`
- Modify: `frontend/app/dashboard/layout.tsx` (ajouter `/dashboard/liasse-fiscale/detail` à `GLOBAL_ROUTES` — déjà couvert si `startsWith('/dashboard/liasse-fiscale')` ; vérifier)

**Interfaces:**
- Consumes: `GET /api/reconciliation` → `{annees, results}`. Après Task 1, chaque ligne comptable de `lignes` porte `par_bien: {[pid]: number}` + `app` (total) + `liasse` + `ecart` + `ok`. Les 6 postes comptables : "Produits", "Charges externes", "Impôts et taxes", "Amortissements", "Intérêts d'emprunt", "Résultat comptable". **La page rend donc directement `lignes` (chacune a déjà `par_bien` + comparaison)** — pas besoin de croiser avec `cr_par_bien`. Filtrer les lignes comptables (celles dont `par_bien !== null`) pour le tableau ; les lignes fiscales (`par_bien === null`) sont ignorées ici (elles vont sur la Maquette 1).

- [ ] **Step 1 : Ouvrir la maquette de référence**

Lire `docs/project/analysis/maquettes-position-fiscale/maquette2-detaillee.html` pour la structure exacte (tableau, sélecteur d'année, colonnes, couleurs `#bf2600` écart, `#006644` ✓).

- [ ] **Step 2 : Écrire la page**

Créer `frontend/app/dashboard/liasse-fiscale/detail/page.tsx`. Structure : `'use client'`, `fetch(\`${API_BASE_URL}/api/reconciliation\`)`, un `useState` pour l'année (défaut = dernière), un sélecteur d'années (boutons), et le tableau. **On rend directement les lignes comptables** (`par_bien !== null`) — chacune a déjà `par_bien`, `app`, `liasse`, `ecart`, `ok`. Le libellé "Résultat comptable" est la ligne de total (fond gris, gras).

```tsx
'use client';
import { useState, useEffect } from 'react';
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const BIENS: Record<number, string> = { 25: 'Evry', 15: 'Marseille abnb', 26: 'Marseille colloc' };
const eur = (n: number) => n.toLocaleString('fr-FR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + ' €';

interface Ligne { poste: string; par_bien: Record<string, number> | null; app: number; liasse: number | null; ecart: number | null; ok: boolean | null; }
interface AnneeRec { annee: number; brouillon: boolean; biens_inclus: number[]; lignes: Ligne[]; }

export default function DetailPage() {
  const [data, setData] = useState<{annees: number[]; results: Record<string, AnneeRec>} | null>(null);
  const [year, setYear] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/reconciliation`).then(r => { if(!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(d => { setData(d); setYear(d.annees[d.annees.length - 1]); }).catch(e => setError(String(e)));
  }, []);
  if (error) return <div style={{ padding: 24, color: '#bf2600' }}>Erreur : {error}</div>;
  if (!data || year === null) return <div style={{ padding: 24, color: '#5e6c84' }}>Chargement…</div>;
  const r = data.results[String(year)];
  const biens = r.biens_inclus;
  const compare = !r.brouillon;
  // uniquement les lignes comptables (ventilées par bien) ; les lignes fiscales (par_bien null) sont ignorées ici
  const lignes = r.lignes.filter(l => l.par_bien !== null);

  return (
    <div style={{ padding: 24, maxWidth: 1000, margin: '0 auto' }}>
      <h1 style={{ fontSize: 20, fontWeight: 700, color: '#172b4d' }}>Détail par appartement — {year}</h1>
      <div style={{ display: 'flex', gap: 6, margin: '12px 0' }}>
        {[...data.annees].map(a => (
          <span key={a} onClick={() => setYear(a)} style={{ fontSize: 12, padding: '4px 10px', borderRadius: 4, cursor: 'pointer',
            background: a === year ? '#0052cc' : '#fff', color: a === year ? '#fff' : '#5e6c84', border: '1px solid #dfe1e6' }}>{a}</span>
        ))}
      </div>
      <div style={{ background: '#fff', border: '1px solid #dfe1e6', borderRadius: 6, overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, minWidth: 720 }}>
          <thead><tr style={{ background: '#f4f5f7', color: '#5e6c84', fontSize: 10, textTransform: 'uppercase' }}>
            <th style={{ padding: 9, textAlign: 'left' }}>Poste</th>
            {biens.map(b => <th key={b} style={{ padding: 9, textAlign: 'right' }}>{BIENS[b] ?? `Bien ${b}`}</th>)}
            <th style={{ padding: 9, textAlign: 'right', borderLeft: '2px solid #172b4d', fontWeight: 700, color: '#172b4d' }}>Total app</th>
            {compare && <th style={{ padding: 9, textAlign: 'right' }}>Liasse</th>}
            {compare && <th style={{ padding: 9, textAlign: 'right' }}>Écart</th>}
          </tr></thead>
          <tbody style={{ color: '#172b4d' }}>
            {lignes.map(lg => {
              const isResult = lg.poste === 'Résultat comptable';
              const isEcart = lg.ok === false;
              return (
                <tr key={lg.poste} style={{ borderTop: isResult ? '2px solid #172b4d' : '1px solid #f4f5f7', background: isResult ? '#f4f5f7' : (isEcart ? '#fff4f2' : '#fff') }}>
                  <td style={{ padding: 9, fontWeight: isResult ? 700 : 600 }}>{isResult ? '= Résultat comptable' : lg.poste}</td>
                  {biens.map(b => <td key={b} style={{ padding: 9, textAlign: 'right', fontWeight: isResult ? 700 : 400 }}>{eur(lg.par_bien?.[String(b)] ?? 0)}</td>)}
                  <td style={{ padding: 9, textAlign: 'right', borderLeft: '2px solid #172b4d', fontWeight: 700 }}>{eur(lg.app)}</td>
                  {compare && <td style={{ padding: 9, textAlign: 'right', color: '#5e6c84' }}>{lg.liasse != null ? eur(lg.liasse) : '—'}</td>}
                  {compare && <td style={{ padding: 9, textAlign: 'right', fontWeight: 700, color: isEcart ? '#bf2600' : '#006644' }}>{lg.ok ? '✓' : (lg.ecart != null ? eur(lg.ecart) : '')}</td>}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

- [ ] **Step 3 : Vérifier le typecheck + build**

Run : `cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/TEST/LMNP/frontend" && npx tsc --noEmit 2>&1 | grep -v "^__tests__/" | grep -i "detail" ; npm run build 2>&1 | grep -E "Compiled successfully|Failed|liasse-fiscale/detail"`
Expected : pas d'erreur sur la page, build OK, route `/dashboard/liasse-fiscale/detail` listée.

- [ ] **Step 4 : Vérifier la route servie**

Run : `curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:3000/dashboard/liasse-fiscale/detail"` → 200. (Le backend 8000 sert déjà `/api/reconciliation` avec la clé `cr_par_bien` après Tasks 1-2 ; si le backend live ne l'a pas rechargée, demander à Louis un redémarrage — NE PAS tuer le process sans accord.)

- [ ] **Step 5 : Commit**

```bash
cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/TEST/LMNP"
git add frontend/app/dashboard/liasse-fiscale/detail/page.tsx frontend/app/dashboard/layout.tsx
git commit -m "[REFONTE] feat(front): page détail par appartement (Maquette 2)"
```

---

## Task 4 : Page Maquette 1 — vision globale

Remplacer le contenu de `/dashboard/liasse-fiscale` par la vision globale : liasse (vérif) à gauche, résultat par appartement au milieu, tirelires app (déficit + amort) à droite, badge d'état, + lien vers le détail. Colonne "Imputer en priorité" affichée en **lecture seule** (désactivée) avec une note "bientôt configurable" — le toggle interactif est un plan suivant. Rendu cible : `maquette1-globale.html`.

**Files:**
- Modify: `frontend/app/dashboard/liasse-fiscale/page.tsx` (remplacer le contenu actuel)

**Interfaces:**
- Consumes: `GET /api/reconciliation`. Par année : `lignes` contient "Résultat comptable" (avec `par_bien`), "Déficit reportable (cumulé)" (app/liasse/ecart), "Amortissements reportés (cumulé)" (app/liasse/ecart). `biens_inclus`, `brouillon`.

- [ ] **Step 1 : Ouvrir la maquette de référence**

Lire `docs/project/analysis/maquettes-position-fiscale/maquette1-globale.html` : ordre des colonnes (Année | Liasse déficit/amort en gris à gauche | résultat par bien + entité | tirelires app déficit/amort à droite | colonne imputation), couleurs.

- [ ] **Step 2 : Écrire la page**

Remplacer le contenu de `frontend/app/dashboard/liasse-fiscale/page.tsx`. Pour chaque année (plus récent en bas ou en haut — suivre la maquette : plus ancien en haut), extraire :
- résultat par bien : `lignes.find(l=>l.poste==='Résultat comptable').par_bien` + `.app` pour l'entité.
- tirelire déficit app cumulé : `lignes.find(l=>l.poste==='Déficit reportable (cumulé)').app` ; liasse = `.liasse`.
- tirelire amort app cumulé : `lignes.find(l=>l.poste==='Amortissements reportés (cumulé)').app` ; liasse = `.liasse`.
- La colonne "Imputer en priorité" : afficher un `<select disabled>` avec "Déficit (reco)" sur les années bénéficiaires (résultat entité de l'année > 0 avant report ; approximation : afficher le select seulement si `deficit_annee===0 && résultat comptable + amort > 0` — sinon "— perte"). Pour ce plan, `disabled` + titre "configurable bientôt".

Fournir le composant complet (mêmes conventions que la page actuelle et que Task 3 : fetch, BIENS, eur, colonnes dynamiques selon `biens_inclus`, gestion `brouillon`). Reproduire les 3 blocs de couleur de la maquette (gris liasse, rouge déficit, bleu amort). Inclure en haut un lien "Voir le détail par appartement →" vers `/dashboard/liasse-fiscale/detail`.

[L'implémenteur écrit le JSX complet en suivant la maquette et le pattern de Task 3. Colonnes : Année ; Liasse déficit cumulé ; Liasse amort cumulé ; (par bien) Evry/abnb/colloc ; Entité résultat ; App déficit cumulé ; App amort cumulé ; Imputation (select disabled).]

- [ ] **Step 3 : Typecheck + build**

Run : `cd frontend && npx tsc --noEmit 2>&1 | grep -v "^__tests__/" | grep -i "liasse-fiscale" ; npm run build 2>&1 | grep -E "Compiled successfully|Failed"`
Expected : pas d'erreur, build OK.

- [ ] **Step 4 : Vérifier la route + données**

Run : `curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:3000/dashboard/liasse-fiscale"` → 200.
Vérifier visuellement (Louis) : liasse à gauche, résultat par bien, tirelires app à droite, lien vers le détail.

- [ ] **Step 5 : Commit**

```bash
cd "/Users/louisgarnier/Library/Mobile Documents/com~apple~CloudDocs/Python/TEST/LMNP"
git add frontend/app/dashboard/liasse-fiscale/page.tsx
git commit -m "[REFONTE] feat(front): vision globale position fiscale (Maquette 1, imputation en lecture seule)"
```

---

## Résultat livré par ce plan

Louis voit sa **position fiscale** dans l'appli : la vision globale (résultat par appartement + les deux tirelires App vs Officiel, avec les écarts) et le détail par appartement, sur données réelles. Positionné en contexte global.

**Plans suivants (déjà cadrés dans `docs/project/analysis/maquettes-position-fiscale/REPRENDRE-ICI.md`) :**
1. **Choix d'imputation par année** — toggle déficit/amort qui rend `compute_fiscal_timeline` paramétrable par exercice + config stockée + recalcul.
2. **Refonte page d'accueil** — 2 sections (Appartements + Liasse/données globales), maquette `accueil.html`.
3. **Chargement de liasse + pièces jointes** — téléversement PDF archivé + saisie manuelle des ~10 chiffres → crée `liasse-YYYY.json`, l'année passe en comparée ; coffre de documents par exercice.
4. **Reprise des reports** — calcul 2026+ à partir de la position officielle fin 2025 (déficit 39 913 ferme, amort ≈35 364), au lieu du recalcul depuis 2021.
