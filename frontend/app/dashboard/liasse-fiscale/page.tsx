/**
 * Liasse fiscale — réconciliation appli vs liasses déposées.
 *
 * L'application CALCULE la fiscalité (source de vérité) ; la liasse déposée sert
 * de CONTRÔLE. Chaque écart est pointé du doigt (vue contrôleur). Données :
 * GET /api/reconciliation.
 */
'use client';

import { useState, useEffect } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Ligne {
  poste: string;
  app: number;
  liasse: number;
  ecart: number;
  ok: boolean;
}
interface AnneeRec {
  annee: number;
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

const BIENS: Record<number, string> = { 25: 'Evry', 15: 'Marseille abnb', 26: 'Marseille colloc' };

export default function LiasseFiscalePage() {
  const [data, setData] = useState<RecResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState<number | null>(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/reconciliation`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d: RecResponse) => {
        setData(d);
        // ouvrir par défaut la première année avec des écarts
        const firstEcart = d.annees.find((a) => d.results[String(a)].nb_ecarts > 0);
        setOpen(firstEcart ?? d.annees[d.annees.length - 1] ?? null);
      })
      .catch((e) => setError(String(e)));
  }, []);

  if (error)
    return (
      <div style={{ padding: 24, color: '#bf2600' }}>
        Impossible de charger la réconciliation : {error}. Vérifiez que le backend tourne sur {API_BASE_URL}.
      </div>
    );
  if (!data) return <div style={{ padding: 24, color: '#5e6c84' }}>Chargement…</div>;

  const annees = [...data.annees].sort((a, b) => b - a); // plus récent d'abord

  return (
    <div style={{ padding: 24, maxWidth: 1000, margin: '0 auto' }}>
      <h1 style={{ fontSize: 20, fontWeight: 700, color: '#172b4d', margin: 0 }}>
        Liasse fiscale — réconciliation
      </h1>
      <p style={{ fontSize: 13, color: '#5e6c84', marginTop: 6, lineHeight: 1.5 }}>
        L&apos;application calcule votre fiscalité à partir des relevés bancaires. Chaque exercice est
        confronté à la liasse déposée par le cabinet. Un écart signale une divergence à vérifier —
        pas forcément une erreur de l&apos;application.
      </p>

      <div style={{ background: '#fff', border: '1px solid #dfe1e6', borderRadius: 6, overflow: 'hidden', marginTop: 16 }}>
        {annees.map((an) => {
          const r = data.results[String(an)];
          const isOpen = open === an;
          const ok = r.nb_ecarts === 0;
          return (
            <div key={an} style={{ borderBottom: '1px solid #f4f5f7' }}>
              <div
                onClick={() => setOpen(isOpen ? null : an)}
                style={{ display: 'flex', alignItems: 'center', padding: '12px 14px', cursor: 'pointer', background: isOpen ? '#f7f9ff' : '#fff' }}
              >
                <div style={{ width: 56, fontSize: 15, fontWeight: 700, color: '#172b4d' }}>{an}</div>
                <div style={{ flex: 1, fontSize: 12, color: '#5e6c84' }}>
                  {r.biens_inclus.map((b) => BIENS[b] ?? `Bien ${b}`).join(' · ')}
                </div>
                <div style={{ width: 190, textAlign: 'right' }}>
                  <span
                    style={{
                      fontSize: 9, fontWeight: 700, textTransform: 'uppercase', padding: '3px 7px', borderRadius: 3,
                      background: ok ? '#e3fcef' : '#ffebe6', color: ok ? '#006644' : '#bf2600',
                    }}
                  >
                    {ok ? '✓ conforme' : `${r.nb_ecarts} écart${r.nb_ecarts > 1 ? 's' : ''}`}
                  </span>
                </div>
              </div>

              {isOpen && (
                <div style={{ padding: '4px 14px 16px' }}>
                  {!r.composition.ok && (
                    <div style={{ background: '#fffbe6', border: '1px solid #ffe58f', borderRadius: 4, padding: '8px 12px', margin: '8px 0', fontSize: 12, color: '#7a5900' }}>
                      Composition : l&apos;application a {eur(r.composition.app)} d&apos;immobilisations fin {an}, la
                      liasse {eur(r.composition.liasse)} (écart {eur(r.composition.ecart)}). Un bien ou des travaux
                      ne sont pas datés de la même année de part et d&apos;autre.
                    </div>
                  )}
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                    <thead>
                      <tr style={{ color: '#5e6c84', fontSize: 11, textTransform: 'uppercase' }}>
                        <th style={{ textAlign: 'left', padding: '8px 10px', fontWeight: 600 }}>Poste</th>
                        <th style={{ textAlign: 'right', padding: '8px 10px', fontWeight: 600 }}>Application</th>
                        <th style={{ textAlign: 'right', padding: '8px 10px', fontWeight: 600 }}>Liasse</th>
                        <th style={{ textAlign: 'right', padding: '8px 10px', fontWeight: 600 }}>Écart</th>
                      </tr>
                    </thead>
                    <tbody style={{ color: '#172b4d' }}>
                      {r.lignes.map((l) => (
                        <tr key={l.poste} style={{ background: l.ok ? '#fff' : '#fff4f2' }}>
                          <td style={{ padding: '7px 10px', fontWeight: l.ok ? 400 : 600 }}>{l.poste}</td>
                          <td style={{ textAlign: 'right', padding: '7px 10px' }}>{eur(l.app)}</td>
                          <td style={{ textAlign: 'right', padding: '7px 10px', color: '#5e6c84' }}>{eur(l.liasse)}</td>
                          <td style={{ textAlign: 'right', padding: '7px 10px', fontWeight: 700, color: l.ok ? '#006644' : '#bf2600' }}>
                            {l.ok ? '✓' : eur(l.ecart)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <div style={{ marginTop: 8, fontSize: 11, color: '#5e6c84', fontStyle: 'italic' }}>
                    Stock de déficit reportable (application, cumulé) : {eur(r.stock_deficit_appli)}. Résultat fiscal
                    imposable : 0 € — aucun impôt dû tant que ce stock n&apos;est pas épuisé.
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
