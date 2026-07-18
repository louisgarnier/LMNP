/**
 * La chaîne fiscale, année par année — Maquette 3.
 *
 * Trois tableaux chaînés : Étape 1 (résultat comptable → résultat fiscal),
 * Étape 2 (tirelire déficit reportable), Étape 3 (tirelire amortissements
 * reportés). Colonne App = calcul de l'application, colonne Officiel = ce
 * qui a été déposé en liasse, Écart = App − Officiel. Sur les années
 * bénéficiaires, un sélecteur « Imputer en priorité » permet de choisir
 * l'ordre d'imputation (déficit d'abord vs amortissement d'abord) ; le
 * choix est persisté côté backend et recalcule toute la chaîne.
 * Route globale (pas de propriété active). Données : GET /api/fiscal/chaine,
 * écriture : PUT /api/fiscal/imputation/{year}.
 */
'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import type { CSSProperties } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const eur = (n: number) =>
  n.toLocaleString('fr-FR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + ' €';
const eurSigned = (n: number) => (n > 0 ? '+' : '') + eur(n);
const posColor = (n: number) => (n > 0 ? '#006644' : '#172b4d');

type Mode = 'deficit' | 'amort';

interface Ligne {
  year: number;
  brouillon: boolean;
  profitable: boolean;
  mode: Mode;
  resultat_comptable: number;
  amort_annee: number;
  r_ha: number;
  amort_deductible: number;
  amort_mis_de_cote: number;
  resultat_fiscal_app: number;
  resultat_fiscal_officiel: number | null;
  deficit_depart: number;
  deficit_mouvement: number;
  deficit_fin_app: number;
  deficit_fin_officiel: number | null;
  deficit_ecart: number | null;
  amort_depart: number;
  amort_impute: number;
  amort_fin_app: number;
  amort_fin_officiel: number | null;
  amort_ecart: number | null;
}
interface Reprise {
  annee: number;
  deficit: number;
  amort: number;
}
interface ChaineResponse {
  years: number[];
  chain: Record<string, Ligne>;
  reprise: Reprise;
}

// ---- styles réutilisés (repris de la maquette maquette3-chaine-fiscale.html) ----
const cardStyle: CSSProperties = {
  background: '#fff', border: '1px solid #dfe1e6', borderRadius: 8, overflowX: 'auto', marginTop: 14,
};
const tableStyle: CSSProperties = { width: '100%', borderCollapse: 'collapse', fontSize: 11.5, minWidth: 760 };
const theadRowStyle: CSSProperties = { background: '#eceef1' };
const thBase: CSSProperties = {
  fontSize: 9, textTransform: 'uppercase', letterSpacing: '.02em', color: '#5e6c84', padding: '7px 7px', textAlign: 'left',
};
const thNum: CSSProperties = { ...thBase, textAlign: 'right' };
const tdBase: CSSProperties = { padding: '7px 7px' };
const tdNum: CSSProperties = { ...tdBase, textAlign: 'right', fontVariantNumeric: 'tabular-nums' };
const trBase: CSSProperties = { borderTop: '1px solid #f1f2f4' };
const calcCell: CSSProperties = { ...tdNum, background: '#fbfbfc' };
const calcHead: CSSProperties = { ...thNum, background: '#fbfbfc' };
const offHead: CSSProperties = { ...thNum, background: '#eceef0', borderLeft: '2px solid #97a0af' };
const offCell: CSSProperties = { ...tdNum, background: '#f6f7f9', color: '#5e6c84' };
const defHead: CSSProperties = { ...thNum, background: '#ffeceb', borderLeft: '2px solid #bf2600' };
const defCell: CSSProperties = { ...tdNum, background: '#fff6f5' };
const amoHead: CSSProperties = { ...thNum, background: '#e9f1ff', borderLeft: '2px solid #0052cc' };
const amoCell: CSSProperties = { ...tdNum, background: '#f4f8ff' };
const sepCell: CSSProperties = { ...tdNum, borderLeft: '2px solid #172b4d' };
const sepHead: CSSProperties = { ...thNum, borderLeft: '2px solid #172b4d' };
const mutedCell: CSSProperties = { color: '#97a0af' };
const repriseRow: CSSProperties = {
  background: '#e3fcef', fontWeight: 600, color: '#006644', borderTop: '2px solid #00875a', borderBottom: '2px solid #00875a',
};
const brouillonRow: CSSProperties = { background: '#eef3ff' };
const stepBadge: CSSProperties = {
  display: 'inline-block', fontSize: 11, fontWeight: 700, color: '#fff', background: '#0052cc', borderRadius: 5,
  padding: '2px 9px', marginRight: 8,
};
const chipWarn: CSSProperties = {
  fontSize: 8, fontWeight: 700, textTransform: 'uppercase', padding: '1px 5px', borderRadius: 3,
  background: '#fffae6', color: '#974f0c', marginLeft: 6,
};
const chipBrouillon: CSSProperties = {
  fontSize: 8, fontWeight: 700, textTransform: 'uppercase', padding: '1px 5px', borderRadius: 3,
  background: '#deebff', color: '#0747a6', marginLeft: 6,
};

function ecartColor(e: number | null): string {
  if (e == null) return '#97a0af';
  return Math.abs(e) >= 1000 ? '#bf2600' : '#00875a';
}
function ecartText(e: number | null): string {
  return e == null ? '—' : eurSigned(e);
}

export default function ChaineFiscalePage() {
  const [data, setData] = useState<ChaineResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState<number | null>(null);
  const [putError, setPutError] = useState<string | null>(null);
  const [realized, setRealized] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/fiscal/chaine?realized=${realized}`)
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then((d: ChaineResponse) => setData(d))
      .catch((e) => setError(String(e)));
  }, [realized]);

  async function handleModeChange(year: number, mode: Mode) {
    setSaving(year);
    setPutError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/fiscal/imputation/${year}?realized=${realized}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const updated: ChaineResponse = await res.json();
      setData(updated);
    } catch (e) {
      setPutError(String(e));
    } finally {
      setSaving(null);
    }
  }

  if (error)
    return <div style={{ padding: 24, color: '#bf2600' }}>Impossible de charger : {error}. Backend sur {API_BASE_URL} ?</div>;
  if (!data) return <div style={{ padding: 24, color: '#5e6c84' }}>Chargement…</div>;

  const years = [...data.years].sort((a, b) => a - b); // plus ancien en haut
  const { chain, reprise } = data;

  return (
    <div style={{ padding: 24, maxWidth: 1180, margin: '0 auto' }}>
      <Link
        href="/dashboard/liasse-fiscale"
        style={{ fontSize: 12, color: '#0052cc', cursor: 'pointer', marginBottom: 6, display: 'inline-block' }}
      >
        ← Retour à la vision globale
      </Link>
      <h1 style={{ fontSize: 20, fontWeight: 700, color: '#172b4d', margin: 0 }}>
        Position fiscale — la chaîne année par année
      </h1>
      <p style={{ fontSize: 13, color: '#5e6c84', marginTop: 6, lineHeight: 1.5 }}>
        Comment le résultat comptable devient le « résultat fiscal », puis remplit les deux tirelires
        (déficit reportable · amortissements reportés). Colonne <b>App</b> = ce que l&apos;appli calcule ·
        colonne <b>Officiel</b> = ce qui a été déposé en liasse.
      </p>

      <div
        style={{ display: 'inline-flex', alignItems: 'center', gap: 8, marginTop: 12 }}
        title="Ne change que l'année en cours (2026) : Réel = coût du financement à ce jour ; Prévisionnel = plein an."
      >
        <span style={{ fontSize: 12, color: '#5e6c84' }}>Base 2026 :</span>
        <button
          type="button"
          onClick={() => setRealized(true)}
          style={
            realized
              ? { fontSize: 12, padding: '4px 10px', borderRadius: 4, cursor: 'pointer', background: '#0052cc', color: '#fff', border: '1px solid #0052cc' }
              : { fontSize: 12, padding: '4px 10px', borderRadius: 4, cursor: 'pointer', background: '#fff', color: '#5e6c84', border: '1px solid #dfe1e6' }
          }
        >
          Réel
        </button>
        <button
          type="button"
          onClick={() => setRealized(false)}
          style={
            !realized
              ? { fontSize: 12, padding: '4px 10px', borderRadius: 4, cursor: 'pointer', background: '#0052cc', color: '#fff', border: '1px solid #0052cc' }
              : { fontSize: 12, padding: '4px 10px', borderRadius: 4, cursor: 'pointer', background: '#fff', color: '#5e6c84', border: '1px solid #dfe1e6' }
          }
        >
          Prévisionnel
        </button>
      </div>

      {putError && (
        <div style={{ marginTop: 12, padding: '8px 12px', background: '#fff6f5', border: '1px solid #bf2600', borderRadius: 4, color: '#bf2600', fontSize: 12 }}>
          Échec de la mise à jour : {putError}
        </div>
      )}

      {/* ===================== TABLEAU A — Étape 1 ===================== */}
      <div style={{ marginTop: 24 }}>
        <h2 style={{ fontSize: 15, margin: '0 0 4px' }}>
          <span style={stepBadge}>Étape 1</span>Du résultat comptable au « résultat fiscal »
        </h2>
        <p style={{ fontSize: 13, color: '#5e6c84', lineHeight: 1.5, margin: 0 }}>
          L&apos;amortissement n&apos;a pas le droit de faire passer sous 0. On regarde d&apos;abord le résultat
          <i> avant</i> amort ; ce qu&apos;on ne peut pas déduire est mis de côté (→ tirelire n°2).
          <b> Cette étape ne dépend pas du toggle.</b>
        </p>
      </div>
      <div style={cardStyle}>
        <table style={tableStyle}>
          <thead>
            <tr style={theadRowStyle}>
              <th style={{ ...thBase, fontWeight: 700, whiteSpace: 'nowrap' }}>Année</th>
              <th style={thNum}>Résultat<br />comptable</th>
              <th style={calcHead}>+ Amort.<br />de l&apos;année</th>
              <th style={calcHead}>= Avant<br />amort.</th>
              <th style={calcHead}>Amort.<br />déduit</th>
              <th style={calcHead}>Amort. mis<br />de côté →</th>
              <th style={sepHead}>= Résultat<br />fiscal (App)</th>
              <th style={offHead}>Rappel officiel<br />rés. fiscal</th>
            </tr>
          </thead>
          <tbody style={{ color: '#172b4d' }}>
            {years.map((y) => {
              const l = chain[String(y)];
              return (
                <tr key={y} style={{ ...trBase, ...(l.brouillon ? brouillonRow : {}) }}>
                  <td style={{ ...tdBase, fontWeight: 700, whiteSpace: 'nowrap' }}>
                    {y}
                    {l.brouillon && <span style={chipBrouillon}>brouillon</span>}
                  </td>
                  <td style={{ ...tdNum, color: posColor(l.resultat_comptable), fontWeight: l.resultat_comptable > 0 ? 600 : 400 }}>
                    {eurSigned(l.resultat_comptable)}
                  </td>
                  <td style={calcCell}>+{eur(l.amort_annee)}</td>
                  <td style={{ ...calcCell, color: posColor(l.r_ha), fontWeight: l.r_ha > 0 ? 600 : 400 }}>{eurSigned(l.r_ha)}</td>
                  <td style={{ ...calcCell, ...(l.amort_deductible === 0 ? mutedCell : {}) }}>{eur(l.amort_deductible)}</td>
                  <td style={{ ...calcCell, ...(l.amort_mis_de_cote === 0 ? mutedCell : {}) }}>{eur(l.amort_mis_de_cote)}</td>
                  <td style={{ ...sepCell, fontWeight: 700, color: posColor(l.resultat_fiscal_app) }}>
                    {eurSigned(l.resultat_fiscal_app)}
                  </td>
                  <td style={offCell}>
                    {l.resultat_fiscal_officiel != null ? eurSigned(l.resultat_fiscal_officiel) : '—'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* ===================== TABLEAU B — Étape 2 ===================== */}
      <div style={{ marginTop: 30 }}>
        <h2 style={{ fontSize: 15, margin: '0 0 4px' }}>
          <span style={stepBadge}>Étape 2</span>Tirelire n°1 — déficit reportable
        </h2>
        <p style={{ fontSize: 13, color: '#5e6c84', lineHeight: 1.5, margin: 0 }}>
          Une perte <b>ajoute</b> à la tirelire ; un bénéfice <b>retire</b> — mais seulement si le toggle dit
          « déficit d&apos;abord ». Le menu <b>« Imputer en priorité »</b> n&apos;apparaît que sur les années
          bénéficiaires (résultat fiscal positif).
        </p>
      </div>
      <div style={cardStyle}>
        <table style={tableStyle}>
          <thead>
            <tr style={theadRowStyle}>
              <th style={{ ...thBase, fontWeight: 700, whiteSpace: 'nowrap' }}>Année</th>
              <th style={{ ...amoHead, textAlign: 'center' }}>Imputer<br />en priorité</th>
              <th style={defHead}>Déficit<br />au départ</th>
              <th style={{ ...thNum, background: '#fff6f5' }}>Résultat<br />fiscal</th>
              <th style={{ ...thNum, background: '#fff6f5' }}>Mouvement</th>
              <th style={defHead}>= Déficit<br />fin (App)</th>
              <th style={offHead}>Déficit fin<br />(Officiel)</th>
              <th style={offHead}>Écart</th>
            </tr>
          </thead>
          <tbody style={{ color: '#172b4d' }}>
            {years.map((y) => {
              const l = chain[String(y)];
              const rows = [
                <tr key={y} style={{ ...trBase, ...(l.brouillon ? brouillonRow : {}) }}>
                  <td style={{ ...tdBase, fontWeight: 700, whiteSpace: 'nowrap' }}>
                    {y}
                    {l.profitable && <span style={chipWarn}>choix</span>}
                    {l.brouillon && <span style={chipBrouillon}>brouillon</span>}
                  </td>
                  <td style={{ ...amoCell, textAlign: 'center' }}>
                    {l.profitable ? (
                      <select
                        value={l.mode}
                        disabled={saving === y}
                        onChange={(e) => handleModeChange(y, e.target.value as Mode)}
                        style={{
                          fontSize: 11, padding: '4px 7px', border: '1.5px solid #0052cc', borderRadius: 5,
                          background: '#fff', color: '#172b4d', fontWeight: 600,
                          cursor: saving === y ? 'wait' : 'pointer', opacity: saving === y ? 0.6 : 1,
                        }}
                      >
                        <option value="amort">Amort. d&apos;abord (comptable)</option>
                        <option value="deficit">Déficit d&apos;abord (reco)</option>
                      </select>
                    ) : (
                      <span style={{ ...mutedCell, fontSize: 10 }}>
                        {l.resultat_fiscal_app < 0 ? 'perte' : 'neutre'}
                      </span>
                    )}
                  </td>
                  <td style={{ ...defCell, ...(l.deficit_depart === 0 ? mutedCell : {}) }}>{eur(l.deficit_depart)}</td>
                  <td style={{ ...defCell, color: posColor(l.resultat_fiscal_app), fontWeight: l.resultat_fiscal_app > 0 ? 600 : 400 }}>
                    {eurSigned(l.resultat_fiscal_app)}
                  </td>
                  <td style={{ ...defCell, ...(l.deficit_mouvement === 0 ? mutedCell : {}) }}>
                    {l.deficit_mouvement === 0 ? '—' : eurSigned(l.deficit_mouvement)}
                  </td>
                  <td style={{ ...defHead, borderLeft: 'none', fontWeight: 700 }}>{eur(l.deficit_fin_app)}</td>
                  <td style={offCell}>
                    {l.brouillon ? <span style={mutedCell}>pas de liasse</span> : l.deficit_fin_officiel != null ? eur(l.deficit_fin_officiel) : '—'}
                  </td>
                  <td style={{ ...offCell, fontWeight: 700, color: ecartColor(l.deficit_ecart) }}>
                    {ecartText(l.deficit_ecart)}
                  </td>
                </tr>,
              ];
              if (y === reprise.annee) {
                rows.push(
                  <tr key={`reprise-b-${y}`} style={repriseRow}>
                    <td colSpan={8} style={tdBase}>
                      ↳ REPRISE fin {reprise.annee} — on repart de l&apos;<b>officiel</b> : déficit reportable = <b>{eur(reprise.deficit)}</b>
                    </td>
                  </tr>
                );
              }
              return rows;
            })}
          </tbody>
        </table>
      </div>

      {/* ===================== TABLEAU C — Étape 3 ===================== */}
      <div style={{ marginTop: 30 }}>
        <h2 style={{ fontSize: 15, margin: '0 0 4px' }}>
          <span style={stepBadge}>Étape 3</span>Tirelire n°2 — amortissements reportés
        </h2>
        <p style={{ fontSize: 13, color: '#5e6c84', lineHeight: 1.5, margin: 0 }}>
          Alimentée par « Amort. mis de côté » (étape 1). Un bénéfice y est <b>retiré</b> seulement si le toggle
          dit « amort d&apos;abord ». Ne s&apos;efface jamais.
        </p>
      </div>
      <div style={cardStyle}>
        <table style={tableStyle}>
          <thead>
            <tr style={theadRowStyle}>
              <th style={{ ...thBase, fontWeight: 700, whiteSpace: 'nowrap' }}>Année</th>
              <th style={amoHead}>Amort. reporté<br />au départ</th>
              <th style={{ ...thNum, background: '#f4f8ff' }}>+ Mis de côté<br />(étape 1)</th>
              <th style={{ ...thNum, background: '#f4f8ff' }}>− Imputation<br />bénéfice</th>
              <th style={amoHead}>= Amort. reporté<br />fin (App)</th>
              <th style={offHead}>Amort. fin<br />(Officiel)</th>
              <th style={offHead}>Écart</th>
            </tr>
          </thead>
          <tbody style={{ color: '#172b4d' }}>
            {years.map((y) => {
              const l = chain[String(y)];
              const rows = [
                <tr key={y} style={{ ...trBase, ...(l.brouillon ? brouillonRow : {}) }}>
                  <td style={{ ...tdBase, fontWeight: 700, whiteSpace: 'nowrap' }}>
                    {y}
                    {l.profitable && <span style={chipWarn}>choix</span>}
                    {l.brouillon && <span style={chipBrouillon}>brouillon</span>}
                  </td>
                  <td style={{ ...amoCell, ...(l.amort_depart === 0 ? mutedCell : {}) }}>{eur(l.amort_depart)}</td>
                  <td style={{ ...amoCell, ...(l.amort_mis_de_cote === 0 ? mutedCell : {}) }}>+{eur(l.amort_mis_de_cote)}</td>
                  <td style={{ ...amoCell, ...(l.amort_impute === 0 ? mutedCell : {}) }}>
                    {l.amort_impute === 0 ? '—' : `−${eur(l.amort_impute)}`}
                  </td>
                  <td style={{ ...amoHead, background: '#f4f8ff', borderLeft: 'none', fontWeight: 700 }}>{eur(l.amort_fin_app)}</td>
                  <td style={offCell}>
                    {l.brouillon ? <span style={mutedCell}>pas de liasse</span> : l.amort_fin_officiel != null ? eur(l.amort_fin_officiel) : '—'}
                  </td>
                  <td style={{ ...offCell, fontWeight: 700, color: ecartColor(l.amort_ecart) }}>
                    {ecartText(l.amort_ecart)}
                  </td>
                </tr>,
              ];
              if (y === reprise.annee) {
                rows.push(
                  <tr key={`reprise-c-${y}`} style={repriseRow}>
                    <td colSpan={7} style={tdBase}>
                      ↳ REPRISE fin {reprise.annee} — on repart de l&apos;<b>officiel</b> : amort. reporté = <b>{eur(reprise.amort)}</b>
                    </td>
                  </tr>
                );
              }
              return rows;
            })}
          </tbody>
        </table>
      </div>

      <div style={{ borderRadius: 8, padding: '14px 16px', fontSize: 13, lineHeight: 1.55, marginTop: 14, background: '#e3fcef', border: '1px solid #57d9a3', borderLeft: '4px solid #00875a' }}>
        <b>Le principe de reprise.</b> Jusqu&apos;à fin {reprise.annee} on <b>accepte les chiffres officiels</b> (déposés).
        Au 1ᵉʳ janvier {reprise.annee + 1} l&apos;appli <b>repart de l&apos;officiel</b> : déficit <b>{eur(reprise.deficit)}</b> +
        amort. reporté <b>{eur(reprise.amort)}</b> = <b>{eur(reprise.deficit + reprise.amort)}</b> à déduire.
        Ensuite c&apos;est l&apos;appli qui calcule, et qui te permet de <b>challenger le comptable</b>.
      </div>

      <div style={{ borderRadius: 8, padding: '14px 16px', fontSize: 13, lineHeight: 1.55, marginTop: 14, background: '#fff', border: '1px solid #dfe1e6', borderLeft: '4px solid #0052cc', color: '#42526e' }}>
        <b>Le toggle « Imputer en priorité » — même mécanique pour toutes les années.</b> Il apparaît sur chaque
        année bénéficiaire. <b>Déficit d&apos;abord</b> = méthode prudente (le déficit expire à 10 ans, l&apos;amort
        jamais). <b>Amort d&apos;abord</b> = ce qu&apos;a fait le comptable. Le changer recalcule tout en direct
        (App + les deux tirelires), immédiatement, côté backend.
      </div>
    </div>
  );
}
