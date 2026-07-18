/**
 * Détail par appartement — Maquette 2.
 *
 * Compte de résultat par appartement : produits, charges externes, impôts,
 * amortissements, intérêts, résultat. Colonnes Total app / Liasse / Écart
 * sur les postes comptables (ceux dont par_bien !== null). Les lignes
 * fiscales (par_bien === null) sont ignorées ici — elles vont sur la
 * Maquette 1 (vue globale). Données : GET /api/reconciliation.
 */
'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const BIENS: Record<number, string> = { 25: 'Evry', 15: 'Marseille abnb', 26: 'Marseille colloc' };
const eur = (n: number) =>
  n.toLocaleString('fr-FR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + ' €';

interface Ligne {
  poste: string;
  par_bien: Record<string, number> | null;
  app: number;
  liasse: number | null;
  ecart: number | null;
  ok: boolean | null;
}
interface AnneeRec {
  annee: number;
  brouillon: boolean;
  biens_inclus: number[];
  lignes: Ligne[];
}
interface RecResponse {
  annees: number[];
  results: Record<string, AnneeRec>;
}

export default function DetailPage() {
  const [data, setData] = useState<RecResponse | null>(null);
  const [year, setYear] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [realized, setRealized] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/reconciliation?realized=${realized}`)
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then((d: RecResponse) => { setData(d); setYear((prev) => prev ?? d.annees[d.annees.length - 1]); })
      .catch((e) => setError(String(e)));
  }, [realized]);

  if (error)
    return <div style={{ padding: 24, color: '#bf2600' }}>Erreur : {error}</div>;
  if (!data || year === null)
    return <div style={{ padding: 24, color: '#5e6c84' }}>Chargement…</div>;

  const r = data.results[String(year)];
  const biens = r.biens_inclus;
  const compare = !r.brouillon;
  // uniquement les lignes comptables (ventilées par bien) ; les lignes fiscales
  // (par_bien null) sont ignorées ici
  const lignes = r.lignes.filter((l) => l.par_bien !== null);

  return (
    <div style={{ padding: 24, maxWidth: 1000, margin: '0 auto' }}>
      <Link
        href="/dashboard/liasse-fiscale"
        style={{ fontSize: 12, color: '#0052cc', cursor: 'pointer', marginBottom: 6, display: 'inline-block' }}
      >
        ← Retour à la vision globale
      </Link>
      <h1 style={{ fontSize: 20, fontWeight: 700, color: '#172b4d', margin: 0 }}>
        Détail par appartement — {year}
      </h1>
      <div style={{ marginTop: 4, fontSize: 12, color: '#5e6c84' }}>
        Compte de résultat par appartement · App / Liasse / Écart sur les postes comparables
      </div>

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

      <div style={{ display: 'flex', gap: 6, margin: '14px 0' }}>
        <span style={{ fontSize: 12, color: '#5e6c84', alignSelf: 'center', marginRight: 4 }}>Année :</span>
        {[...data.annees].map((a) => (
          <span
            key={a}
            onClick={() => setYear(a)}
            style={{
              fontSize: 12,
              padding: '4px 10px',
              borderRadius: 4,
              cursor: 'pointer',
              background: a === year ? '#0052cc' : '#fff',
              color: a === year ? '#fff' : '#5e6c84',
              border: a === year ? '1px solid #0052cc' : '1px solid #dfe1e6',
              fontWeight: a === year ? 600 : 400,
            }}
          >
            {a}
          </span>
        ))}
      </div>

      <div style={{ background: '#fff', border: '1px solid #dfe1e6', borderRadius: 6, overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, minWidth: 720 }}>
          <thead>
            <tr style={{ background: '#f4f5f7', color: '#5e6c84', fontSize: 10, textTransform: 'uppercase' }}>
              <th style={{ padding: 9, textAlign: 'left' }}>Poste</th>
              {biens.map((b) => (
                <th key={b} style={{ padding: 9, textAlign: 'right' }}>{BIENS[b] ?? `Bien ${b}`}</th>
              ))}
              <th style={{ padding: 9, textAlign: 'right', borderLeft: '2px solid #172b4d', fontWeight: 700, color: '#172b4d' }}>
                Total app
              </th>
              {compare && <th style={{ padding: 9, textAlign: 'right' }}>Liasse</th>}
              {compare && <th style={{ padding: 9, textAlign: 'right' }}>Écart</th>}
            </tr>
          </thead>
          <tbody style={{ color: '#172b4d' }}>
            {lignes.map((lg) => {
              const isResult = lg.poste === 'Résultat comptable';
              const isEcart = lg.ok === false;
              return (
                <tr
                  key={lg.poste}
                  style={{
                    borderTop: isResult ? '2px solid #172b4d' : '1px solid #f4f5f7',
                    background: isResult ? '#f4f5f7' : isEcart ? '#fff4f2' : '#fff',
                  }}
                >
                  <td style={{ padding: 9, fontWeight: isResult ? 700 : 600 }}>
                    {isResult ? '= Résultat comptable' : lg.poste}
                  </td>
                  {biens.map((b) => (
                    <td key={b} style={{ padding: 9, textAlign: 'right', fontWeight: isResult ? 700 : 400 }}>
                      {eur(lg.par_bien?.[String(b)] ?? 0)}
                    </td>
                  ))}
                  <td style={{ padding: 9, textAlign: 'right', borderLeft: '2px solid #172b4d', fontWeight: 700 }}>
                    {eur(lg.app)}
                  </td>
                  {compare && (
                    <td style={{ padding: 9, textAlign: 'right', color: '#5e6c84' }}>
                      {lg.liasse != null ? eur(lg.liasse) : '—'}
                    </td>
                  )}
                  {compare && (
                    <td style={{ padding: 9, textAlign: 'right', fontWeight: 700, color: isEcart ? '#bf2600' : '#006644' }}>
                      {lg.ok ? '✓' : lg.ecart != null ? eur(lg.ecart) : ''}
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
