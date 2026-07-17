/**
 * Liasse fiscale — réconciliation appli vs liasses déposées (vue globale/entité).
 *
 * L'application CALCULE la fiscalité (source de vérité), la liasse déposée sert
 * de CONTRÔLE. Détail par appartement (comme le tableur de Louis) + total + liasse
 * + écart. L'année en cours apparaît en brouillon. Données : GET /api/reconciliation.
 */
'use client';

import { useState, useEffect } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const BIENS: Record<number, string> = { 25: 'Evry', 15: 'Marseille abnb', 26: 'Marseille colloc' };

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
  composition: Ligne;
  lignes: Ligne[];
  stock_deficit_appli: number;
  nb_ecarts: number;
}
interface RecResponse {
  annees: number[];
  results: Record<string, AnneeRec>;
}

const eur = (n: number) =>
  n.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €';

export default function LiasseFiscalePage() {
  const [data, setData] = useState<RecResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState<number | null>(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/reconciliation`)
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then((d: RecResponse) => {
        setData(d);
        const firstEcart = [...d.annees].reverse().find((a) => d.results[String(a)].nb_ecarts > 0);
        setOpen(firstEcart ?? d.annees[d.annees.length - 1] ?? null);
      })
      .catch((e) => setError(String(e)));
  }, []);

  if (error)
    return <div style={{ padding: 24, color: '#bf2600' }}>Impossible de charger : {error}. Backend sur {API_BASE_URL} ?</div>;
  if (!data) return <div style={{ padding: 24, color: '#5e6c84' }}>Chargement…</div>;

  const annees = [...data.annees].sort((a, b) => b - a);

  return (
    <div style={{ padding: 24, maxWidth: 1100, margin: '0 auto' }}>
      <h1 style={{ fontSize: 20, fontWeight: 700, color: '#172b4d', margin: 0 }}>Liasse fiscale — données globales</h1>
      <p style={{ fontSize: 13, color: '#5e6c84', marginTop: 6, lineHeight: 1.5 }}>
        Vue de l&apos;entière activité (tous appartements). Chaque exercice est calculé par l&apos;application à
        partir des relevés bancaires, puis confronté à la liasse déposée. Les lignes sont détaillées par
        appartement : la somme des biens = le total. Un écart signale une divergence à vérifier.
      </p>

      <div style={{ background: '#fff', border: '1px solid #dfe1e6', borderRadius: 6, overflow: 'hidden', marginTop: 16 }}>
        {annees.map((an) => {
          const r = data.results[String(an)];
          const isOpen = open === an;
          const biens = r.biens_inclus;
          const compare = !r.brouillon;
          return (
            <div key={an} style={{ borderBottom: '1px solid #f4f5f7' }}>
              {/* En-tête d'exercice */}
              <div onClick={() => setOpen(isOpen ? null : an)}
                style={{ display: 'flex', alignItems: 'center', padding: '12px 14px', cursor: 'pointer', background: isOpen ? '#f7f9ff' : '#fff' }}>
                <div style={{ width: 56, fontSize: 15, fontWeight: 700, color: '#172b4d' }}>{an}</div>
                <div style={{ flex: 1, fontSize: 12, color: '#5e6c84' }}>
                  {biens.map((b) => BIENS[b] ?? `Bien ${b}`).join(' · ')}
                </div>
                <div style={{ width: 210, textAlign: 'right' }}>
                  <span style={{
                    fontSize: 9, fontWeight: 700, textTransform: 'uppercase', padding: '3px 7px', borderRadius: 3,
                    background: r.brouillon ? '#deebff' : r.nb_ecarts === 0 ? '#e3fcef' : '#ffebe6',
                    color: r.brouillon ? '#0747a6' : r.nb_ecarts === 0 ? '#006644' : '#bf2600',
                  }}>
                    {r.brouillon ? 'brouillon · exercice en cours' : r.nb_ecarts === 0 ? '✓ conforme' : `${r.nb_ecarts} écart${r.nb_ecarts > 1 ? 's' : ''}`}
                  </span>
                </div>
              </div>

              {/* Détail */}
              {isOpen && (
                <div style={{ padding: '4px 14px 16px', overflowX: 'auto' }}>
                  {r.brouillon && (
                    <div style={{ background: '#deebff', border: '1px solid #b3d4ff', borderRadius: 4, padding: '8px 12px', margin: '8px 0', fontSize: 12, color: '#0747a6' }}>
                      Exercice en cours, pas encore de liasse. Ces chiffres sont ceux que l&apos;application calcule —
                      à transmettre au comptable. Ils évoluent tant que l&apos;année n&apos;est pas close.
                    </div>
                  )}
                  {!r.composition.ok && r.composition.ecart !== null && (
                    <div style={{ background: '#fffbe6', border: '1px solid #ffe58f', borderRadius: 4, padding: '8px 12px', margin: '8px 0', fontSize: 12, color: '#7a5900' }}>
                      Composition : {eur(r.composition.app)} d&apos;immobilisations côté appli fin {an}, {eur(r.composition.liasse!)} liasse
                      (écart {eur(r.composition.ecart)}). Un bien ou des travaux ne sont pas datés de la même année de part et d&apos;autre.
                    </div>
                  )}

                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, minWidth: 640 }}>
                    <thead>
                      <tr style={{ color: '#5e6c84', fontSize: 11, textTransform: 'uppercase' }}>
                        <th style={{ textAlign: 'left', padding: '8px 8px', fontWeight: 600 }}>Poste</th>
                        {biens.map((b) => (
                          <th key={b} style={{ textAlign: 'right', padding: '8px 8px', fontWeight: 600 }}>{BIENS[b] ?? `Bien ${b}`}</th>
                        ))}
                        <th style={{ textAlign: 'right', padding: '8px 8px', fontWeight: 600, borderLeft: '2px solid #dfe1e6' }}>Total appli</th>
                        {compare && <th style={{ textAlign: 'right', padding: '8px 8px', fontWeight: 600 }}>Liasse</th>}
                        {compare && <th style={{ textAlign: 'right', padding: '8px 8px', fontWeight: 600 }}>Écart</th>}
                      </tr>
                    </thead>
                    <tbody style={{ color: '#172b4d' }}>
                      {r.lignes.map((l) => {
                        const isEcart = l.ok === false;
                        return (
                          <tr key={l.poste} style={{ background: isEcart ? '#fff4f2' : '#fff' }}>
                            <td style={{ padding: '7px 8px', fontWeight: isEcart ? 600 : 400 }}>{l.poste}</td>
                            {biens.map((b) => (
                              <td key={b} style={{ textAlign: 'right', padding: '7px 8px', color: l.par_bien ? '#172b4d' : '#97a0af' }}>
                                {l.par_bien ? (l.par_bien[String(b)] !== undefined ? eur(l.par_bien[String(b)]) : '—') : (b === biens[0] ? 'entité →' : '')}
                              </td>
                            ))}
                            <td style={{ textAlign: 'right', padding: '7px 8px', fontWeight: 600, borderLeft: '2px solid #dfe1e6' }}>{eur(l.app)}</td>
                            {compare && <td style={{ textAlign: 'right', padding: '7px 8px', color: '#5e6c84' }}>{l.liasse !== null ? eur(l.liasse) : '—'}</td>}
                            {compare && (
                              <td style={{ textAlign: 'right', padding: '7px 8px', fontWeight: 700, color: isEcart ? '#bf2600' : '#006644' }}>
                                {l.ok ? '✓' : (l.ecart !== null ? eur(l.ecart) : '')}
                              </td>
                            )}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>

                  <div style={{ marginTop: 8, fontSize: 11, color: '#5e6c84', fontStyle: 'italic' }}>
                    Stock de déficit reportable (cumulé, entité) : {eur(r.stock_deficit_appli)}. Résultat fiscal imposable 0 €
                    — aucun impôt dû tant que ce stock n&apos;est pas épuisé. Le déficit et les amortissements reportés sont
                    des stocks d&apos;entité, non ventilables par bien.
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
