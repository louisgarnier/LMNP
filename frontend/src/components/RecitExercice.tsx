/**
 * Un exercice raconté : le calcul, la phrase, les mouvements vers les tirelires.
 *
 * Le texte vient de recitAnnee() — trois gabarits fixes remplis avec les
 * montants de l'application. Ce composant ne fait que mettre en forme.
 *
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */
'use client';

import type { CSSProperties } from 'react';
import { recitAnnee, type Cible } from '@/utils/recitAnnee';
import type { ChaineLigne } from '@/utils/positionFiscale';

const eur = (n: number) =>
  n.toLocaleString('fr-FR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + ' €';
const eurSigned = (n: number) => (n > 0 ? '+' : '') + eur(n);

const COULEUR: Record<Cible, { bg: string; fg: string }> = {
  t1: { bg: '#fdf5e9', fg: '#a8620d' },
  t2: { bg: '#edf6f5', fg: '#0d6360' },
  deduit: { bg: '#eef6f1', fg: '#1c6440' },
  aucun: { bg: '#f7f8fa', fg: '#5e6c84' },
};

const pad = (s: string, n: number) => s.padStart(n, ' ');

export default function RecitExercice({ ligne }: { ligne: ChaineLigne }) {
  const r = recitAnnee(ligne);
  const negatif = r.cas === 'negatif';

  const badge: CSSProperties = {
    fontSize: 9, fontWeight: 700, letterSpacing: '.05em', textTransform: 'uppercase',
    padding: '2px 6px', borderRadius: 3,
    background: negatif ? '#fdf0f0' : '#eef6f1',
    color: negatif ? '#bf2600' : '#1c6440',
    border: `1px solid ${negatif ? '#eec6c6' : '#c8e0d2'}`,
  };

  return (
    <article style={{ border: '1px solid #dfe1e6', borderRadius: 6, overflow: 'hidden', background: '#fff' }}>
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'baseline', gap: 10, padding: '9px 14px', background: '#fafbfc', borderBottom: '1px solid #dfe1e6' }}>
        <span style={{ fontSize: 18, fontWeight: 700, color: '#172b4d' }}>{r.annee}</span>
        <span style={badge}>{r.etiquette}</span>
        <span style={{ fontSize: 12.5, color: '#5e6c84' }}>{r.titre}</span>
        {ligne.brouillon && (
          <span style={{ fontSize: 9, fontWeight: 700, textTransform: 'uppercase', padding: '1px 5px', borderRadius: 3, background: '#deebff', color: '#0747a6' }}>
            brouillon
          </span>
        )}
      </div>

      <div style={{ padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 10 }}>
        <pre style={{ margin: 0, fontFamily: 'ui-monospace, Menlo, monospace', fontSize: 11.5, lineHeight: 1.7, background: '#f7f8fa', border: '1px solid #dfe1e6', borderRadius: 4, padding: '8px 11px', overflowX: 'auto' }}>
{`Résultat comptable   ${pad(eur(r.calcul.resultatComptable), 12)}
+ amortissement      ${pad(eurSigned(r.calcul.amort), 12)}
─────────────────────────────────
= AVANT AMORT        ${pad(eur(r.calcul.avantAmort), 12)}`}
        </pre>

        <p style={{ margin: 0, fontSize: 13, color: '#172b4d', lineHeight: 1.55 }}>{r.phrase}</p>

        <div style={{ display: 'grid', gap: 5 }}>
          {r.mouvements.map((m, i) => (
            <div
              key={i}
              style={{
                display: 'grid', gridTemplateColumns: '1fr auto', gap: 12, alignItems: 'baseline',
                padding: '5px 9px', borderRadius: 3,
                background: COULEUR[m.cible].bg, color: COULEUR[m.cible].fg, fontSize: 12.5,
              }}
            >
              <span>{m.texte}</span>
              <span style={{ fontFamily: 'ui-monospace, Menlo, monospace', fontWeight: 700, whiteSpace: 'nowrap' }}>
                {m.montant === 0 ? '0 €' : eurSigned(m.montant)}
              </span>
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px 22px', paddingTop: 7, borderTop: '1px solid #f1f2f4', fontSize: 12.5 }}>
          <span style={{ color: '#a8620d' }}>
            Tirelire déficit <b style={{ fontFamily: 'ui-monospace, Menlo, monospace' }}>{eur(r.soldeDeficit)}</b>
          </span>
          <span style={{ color: '#0d6360' }}>
            Tirelire amortissements <b style={{ fontFamily: 'ui-monospace, Menlo, monospace' }}>{eur(r.soldeAmort)}</b>
          </span>
        </div>
      </div>
    </article>
  );
}
