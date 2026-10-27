/**
 * Le tableau des exercices : comment le résultat comptable remplit les deux
 * tirelires, année par année.
 *
 * La colonne « = avant amort » est la clé de lecture : son signe décide de tout.
 * Chaque solde APP est suivi de sa colonne de contrôle « liasse » — l'app est la
 * référence, la liasse ne sert qu'à repérer les écarts.
 * Cf. ADR « L'application est la source de vérité fiscale » (2026-07-29).
 *
 * Partagé par la carte d'accueil et le module fiscal.
 *
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */
'use client';

import type { CSSProperties } from 'react';
import type { ChaineResponse } from '@/utils/positionFiscale';

const eur = (n: number) =>
  n.toLocaleString('fr-FR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + ' €';
const eurSigned = (n: number) => (n > 0 ? '+' : '') + eur(n);

const T1 = '#a8620d', T1_BG = '#fdf5e9';
const T2 = '#0d6360', T2_BG = '#edf6f5';
const OFF_BG = '#f4f5f7', ROUGE = '#bf2600';

const th: CSSProperties = {
  fontSize: 9, textTransform: 'uppercase', letterSpacing: '.03em', color: '#5e6c84',
  padding: '6px 7px', textAlign: 'right', fontWeight: 700, verticalAlign: 'bottom',
};
const td: CSSProperties = { padding: '6px 7px', textAlign: 'right', fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap' };

export default function ChaineFiscaleTable({
  data,
  caption,
}: {
  data: ChaineResponse;
  caption?: string;
}) {
  const years = [...data.years].sort((a, b) => a - b);

  // Cellule de contrôle liasse : grisée, et rouge si l'écart dépasse l'arrondi.
  const off = (val: number | null, ecart: number | null, key: string) => (
    <td
      key={key}
      style={{
        ...td,
        background: OFF_BG,
        color: val === null ? '#97a0af' : ecart !== null && Math.abs(ecart) >= 1 ? ROUGE : '#5e6c84',
        fontWeight: ecart !== null && Math.abs(ecart) >= 1 ? 600 : 400,
        fontStyle: val === null ? 'italic' : 'normal',
      }}
    >
      {val === null ? 'pas de liasse' : eur(val)}
    </td>
  );

  return (
    <div>
      {caption && (
        <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '.08em', textTransform: 'uppercase', color: '#5e6c84', padding: '10px 0 6px' }}>
          {caption}
        </div>
      )}
      <div style={{ overflowX: 'auto', border: '1px solid #dfe1e6', borderRadius: 6, background: '#fff' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11.5, minWidth: 860 }}>
          <thead>
            <tr style={{ background: '#eceef1' }}>
              <th rowSpan={2} style={{ ...th, textAlign: 'left' }}>Exercice</th>
              <th rowSpan={2} style={th}>Résultat<br />comptable</th>
              <th rowSpan={2} style={th}>+ amort</th>
              <th rowSpan={2} style={th}>= avant<br />amort</th>
              <th rowSpan={2} style={th}>Amort<br />déduit</th>
              <th colSpan={3} style={{ ...th, textAlign: 'center', color: T1, background: T1_BG, borderLeft: `2px solid ${T1}` }}>
                Tirelire déficit
              </th>
              <th colSpan={3} style={{ ...th, textAlign: 'center', color: T2, background: T2_BG, borderLeft: `2px solid ${T2}` }}>
                Tirelire amortissements
              </th>
            </tr>
            <tr style={{ background: '#eceef1' }}>
              <th style={{ ...th, background: T1_BG, borderLeft: `2px solid ${T1}` }}>mouvement</th>
              <th style={{ ...th, background: T1_BG, color: T1 }}>solde APP</th>
              <th style={{ ...th, background: OFF_BG }}>liasse</th>
              <th style={{ ...th, background: T2_BG, borderLeft: `2px solid ${T2}` }}>mouvement</th>
              <th style={{ ...th, background: T2_BG, color: T2 }}>solde APP</th>
              <th style={{ ...th, background: OFF_BG }}>liasse</th>
            </tr>
          </thead>
          <tbody style={{ color: '#172b4d' }}>
            {years.map((y) => {
              const c = data.chain[String(y)];
              if (!c) return null;
              const mvtAmort = c.amort_mis_de_cote - c.amort_impute;
              return (
                <tr key={y} style={{ borderTop: '1px solid #f1f2f4', background: c.brouillon ? '#f7f9ff' : undefined }}>
                  <td style={{ ...td, textAlign: 'left', fontWeight: 700 }}>
                    {y}
                    {c.brouillon && (
                      <span style={{ fontSize: 8, fontWeight: 700, textTransform: 'uppercase', padding: '1px 4px', borderRadius: 3, background: '#deebff', color: '#0747a6', marginLeft: 6 }}>
                        brouillon
                      </span>
                    )}
                  </td>
                  <td style={{ ...td, color: c.resultat_comptable < 0 ? ROUGE : '#172b4d' }}>{eur(c.resultat_comptable)}</td>
                  <td style={td}>{eurSigned(c.amort_annee)}</td>
                  <td style={{ ...td, fontWeight: 700, color: c.r_ha < 0 ? ROUGE : '#006644' }}>{eur(c.r_ha)}</td>
                  <td style={{ ...td, color: c.amort_deductible > 0.5 ? '#172b4d' : '#97a0af' }}>
                    {c.amort_deductible > 0.5 ? eur(c.amort_deductible) : '0 €'}
                  </td>

                  <td style={{ ...td, background: T1_BG, borderLeft: `2px solid ${T1}`, color: Math.abs(c.deficit_mouvement) > 0.5 ? '#172b4d' : '#97a0af' }}>
                    {Math.abs(c.deficit_mouvement) > 0.5 ? eurSigned(c.deficit_mouvement) : '—'}
                  </td>
                  <td style={{ ...td, background: T1_BG, fontWeight: 700, color: T1 }}>{eur(c.deficit_fin_app)}</td>
                  {off(c.deficit_fin_officiel, c.deficit_ecart, `d${y}`)}

                  <td style={{ ...td, background: T2_BG, borderLeft: `2px solid ${T2}`, color: Math.abs(mvtAmort) > 0.5 ? '#172b4d' : '#97a0af' }}>
                    {Math.abs(mvtAmort) > 0.5 ? eurSigned(mvtAmort) : '—'}
                  </td>
                  <td style={{ ...td, background: T2_BG, fontWeight: 700, color: T2 }}>{eur(c.amort_fin_app)}</td>
                  {off(c.amort_fin_officiel, c.amort_ecart, `a${y}`)}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px 18px', fontSize: 11, color: '#5e6c84', padding: '7px 2px 0' }}>
        <span><Swatch bg={T2} /> colonnes <b>APP</b> — la référence, calculée depuis les transactions</span>
        <span><Swatch bg={OFF_BG} border /> colonne <b>liasse</b> — contrôle officiel, en lecture seule</span>
        <span><Swatch bg={ROUGE} /> écart supérieur à 1 €</span>
      </div>
    </div>
  );
}

function Swatch({ bg, border }: { bg: string; border?: boolean }) {
  return (
    <span
      style={{
        display: 'inline-block', width: 11, height: 11, borderRadius: 2, background: bg,
        border: border ? '1px solid #b6c0cd' : 'none', verticalAlign: 'middle', marginRight: 5,
      }}
    />
  );
}
