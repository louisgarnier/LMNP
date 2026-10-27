/**
 * Onglet « Par appartement » — les trois chiffres de la tirelire amortissements,
 * puis leur ventilation bien par bien, puis le compte de résultat par bien.
 *
 * Le découpage du « déjà déduit » est EXACT quand un seul bien amortissait
 * l'année de la déduction ; sinon c'est un prorata, et l'écran le dit.
 * Cf. TIRELIRES-FISCALES-EXPLICATION.md, parties 6 et 7.
 *
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */
'use client';

import { useEffect, useState } from 'react';
import SelecteurExercice from '@/components/SelecteurExercice';
import type { ChaineResponse, ReconResponse } from '@/utils/positionFiscale';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const eur = (n: number) =>
  n.toLocaleString('fr-FR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + ' €';

const T2 = '#0d6360', T2_BG = '#edf6f5', T2_LINE = '#b0d5d2';
const VERT = '#1c6440', VERT_BG = '#eef6f1';

interface BienRepartition {
  property_id: number;
  nom: string;
  premiere_annee: number | null;
  total: number;
  deduit: number;
  tirelire: number;
}
interface Repartition {
  total: number; deduit: number; tirelire: number;
  exact: boolean; annees_au_prorata: number[];
  biens: BienRepartition[]; annees: number[];
}

export default function OngletParAppartement({ chaine }: { chaine: ChaineResponse }) {
  const annees = [...chaine.years].sort((a, b) => a - b);
  const [annee, setAnnee] = useState<number>(annees[annees.length - 1]);
  const [rep, setRep] = useState<Repartition | null>(null);
  const [recon, setRecon] = useState<ReconResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const brouillons = new Set(annees.filter((y) => chaine.chain[String(y)]?.brouillon));

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/fiscal/repartition?jusqua=${annee}`)
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(setRep)
      .catch((e) => setError(String(e)));
  }, [annee]);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/reconciliation`)
      .then((r) => (r.ok ? r.json() : null))
      .then(setRecon)
      .catch(() => setRecon(null));
  }, []);

  if (error) return <div style={{ color: '#bf2600', fontSize: 13 }}>Impossible de charger : {error}</div>;
  if (!rep) return <div style={{ color: '#5e6c84', fontSize: 13 }}>Chargement…</div>;

  const r = recon?.results?.[String(annee)];
  const lignesCR = r?.lignes.filter((l) => l.par_bien !== null) ?? [];
  const biensCR = r?.biens_inclus ?? [];
  const nomDe = (id: number) => rep.biens.find((b) => b.property_id === id)?.nom ?? `Bien ${id}`;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
      {/* ═══ CARTE 1 : les trois chiffres et leur ventilation ═══ */}
      <section style={{ background: '#fff', border: '1px solid #c1c7d0', borderRadius: 8, overflow: 'hidden' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'baseline', justifyContent: 'space-between', gap: 10, padding: '11px 16px', borderBottom: '1px solid #dfe1e6', background: '#fafbfc' }}>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#172b4d' }}>La tirelire amortissements, bien par bien</div>
            <div style={{ fontSize: 12, color: '#5e6c84', marginTop: 2 }}>Cumul à fin {annee}</div>
          </div>
          <SelecteurExercice annees={annees} actif={annee} brouillons={brouillons} onChange={setAnnee} />
        </div>

        <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* l'identité, en une ligne */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 10 }}>
            <Bloc titre="Total amorti" valeur={eur(rep.total)} bg="#fafbfc" line="#dfe1e6" fg="#172b4d" note="depuis le premier exercice" />
            <Bloc titre="dont déjà déduit" valeur={eur(rep.deduit)} bg={VERT_BG} line="#c8e0d2" fg={VERT} note="a vraiment baissé l'impôt" />
            <Bloc titre="dont en tirelire" valeur={eur(rep.tirelire)} bg={T2_BG} line={T2_LINE} fg={T2} note="n'a encore rien fait" />
          </div>

          {/* la barre de répartition */}
          <div>
            <div style={{ display: 'flex', height: 30, borderRadius: 4, overflow: 'hidden', border: '1px solid #dfe1e6' }}>
              <div style={{ flex: Math.max(rep.deduit, 0.001), background: VERT_BG, color: VERT, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11.5, fontWeight: 700, fontFamily: 'ui-monospace, Menlo, monospace', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                {eur(rep.deduit)} déduits
              </div>
              <div style={{ flex: Math.max(rep.tirelire, 0.001), background: T2_BG, color: T2, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11.5, fontWeight: 700, fontFamily: 'ui-monospace, Menlo, monospace', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                {eur(rep.tirelire)} en tirelire
              </div>
            </div>
          </div>

          {/* le tableau par bien */}
          <div style={{ overflowX: 'auto', border: '1px solid #dfe1e6', borderRadius: 6 }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, fontVariantNumeric: 'tabular-nums' }}>
              <thead>
                <tr style={{ background: '#eceef1' }}>
                  <th style={th}>Appartement</th>
                  <th style={{ ...th, textAlign: 'right' }}>Total amorti</th>
                  <th style={{ ...th, textAlign: 'right' }}>dont déjà déduit</th>
                  <th style={{ ...th, textAlign: 'right' }}>dont en tirelire</th>
                </tr>
              </thead>
              <tbody style={{ color: '#172b4d' }}>
                {rep.biens.map((b) => (
                  <tr key={b.property_id} style={{ borderTop: '1px solid #f1f2f4' }}>
                    <td style={td}>
                      <b>{b.nom}</b>
                      {b.premiere_annee !== null && (
                        <span style={{ color: '#97a0af', marginLeft: 6 }}>depuis {b.premiere_annee}</span>
                      )}
                    </td>
                    <td style={{ ...td, textAlign: 'right' }}>{eur(b.total)}</td>
                    <td style={{ ...td, textAlign: 'right', color: b.deduit > 0.5 ? VERT : '#97a0af', fontWeight: b.deduit > 0.5 ? 600 : 400 }}>
                      {eur(b.deduit)}
                    </td>
                    <td style={{ ...td, textAlign: 'right', background: T2_BG, color: T2, fontWeight: 700 }}>{eur(b.tirelire)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr style={{ borderTop: '1px solid #b6c0cd', fontWeight: 700 }}>
                  <td style={td}>Total</td>
                  <td style={{ ...td, textAlign: 'right' }}>{eur(rep.total)}</td>
                  <td style={{ ...td, textAlign: 'right' }}>{eur(rep.deduit)}</td>
                  <td style={{ ...td, textAlign: 'right', background: T2_BG, color: T2 }}>{eur(rep.tirelire)}</td>
                </tr>
              </tfoot>
            </table>
          </div>

          {/* fiabilité du découpage */}
          {rep.exact ? (
            <Note fg={VERT} bg={VERT_BG} line="#c8e0d2" titre="Découpage exact">
              Toutes les déductions sont tombées sur des exercices où un seul appartement amortissait.
              Aucune règle de répartition n&apos;a été nécessaire : ces chiffres sont opposables tels quels.
            </Note>
          ) : (
            <Note fg="#bf2600" bg="#fdf0f0" line="#eec6c6" titre="Découpage conventionnel">
              Sur {rep.annees_au_prorata.join(', ')}, une déduction a porté sur un exercice comptant
              plusieurs appartements. La colonne « déjà déduit » est donc répartie <b>au prorata de
              l&apos;amortissement de l&apos;année</b> — c&apos;est une convention, pas un fait.
              À faire valider par un fiscaliste avant de s&apos;en servir dans un acte de vente.
            </Note>
          )}
        </div>
      </section>

      {/* ═══ CARTE 2 : compte de résultat par bien ═══ */}
      {lignesCR.length > 0 && (
        <section style={{ background: '#fff', border: '1px solid #c1c7d0', borderRadius: 8, overflow: 'hidden' }}>
          <div style={{ padding: '11px 16px', borderBottom: '1px solid #dfe1e6', background: '#fafbfc' }}>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#172b4d' }}>Compte de résultat {annee}, appartement par appartement</div>
            <div style={{ fontSize: 12, color: '#5e6c84', marginTop: 2 }}>
              {biensCR.length} appartement{biensCR.length > 1 ? 's' : ''} sur cet exercice
            </div>
          </div>
          <div style={{ padding: '14px 16px' }}>
            <div style={{ overflowX: 'auto', border: '1px solid #dfe1e6', borderRadius: 6 }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, fontVariantNumeric: 'tabular-nums' }}>
                <thead>
                  <tr style={{ background: '#eceef1' }}>
                    <th style={th}>Poste</th>
                    {biensCR.map((id) => (
                      <th key={id} style={{ ...th, textAlign: 'right' }}>{nomDe(id)}</th>
                    ))}
                    <th style={{ ...th, textAlign: 'right', background: VERT_BG, color: VERT }}>Total app</th>
                  </tr>
                </thead>
                <tbody style={{ color: '#172b4d' }}>
                  {lignesCR.map((l) => {
                    const fort = l.poste === 'Résultat comptable';
                    return (
                      <tr key={l.poste} style={{ borderTop: fort ? '2px solid #172b4d' : '1px solid #f1f2f4', background: fort ? '#f4f5f7' : undefined, fontWeight: fort ? 700 : 400 }}>
                        <td style={td}>{l.poste}</td>
                        {biensCR.map((id) => (
                          <td key={id} style={{ ...td, textAlign: 'right' }}>{eur(l.par_bien?.[String(id)] ?? 0)}</td>
                        ))}
                        <td style={{ ...td, textAlign: 'right', background: VERT_BG, fontWeight: 700 }}>{eur(l.app)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}

const th: React.CSSProperties = {
  fontSize: 9.5, textTransform: 'uppercase', letterSpacing: '.04em', color: '#5e6c84',
  padding: '7px 10px', textAlign: 'left', fontWeight: 700,
};
const td: React.CSSProperties = { padding: '7px 10px' };

function Bloc({ titre, valeur, bg, line, fg, note }: { titre: string; valeur: string; bg: string; line: string; fg: string; note: string }) {
  return (
    <div style={{ background: bg, border: `1px solid ${line}`, borderRadius: 6, padding: '10px 12px' }}>
      <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '.07em', textTransform: 'uppercase', color: fg }}>{titre}</div>
      <div style={{ fontSize: 21, fontWeight: 700, color: fg, fontVariantNumeric: 'tabular-nums', lineHeight: 1.25 }}>{valeur}</div>
      <div style={{ fontSize: 11.5, color: '#5e6c84' }}>{note}</div>
    </div>
  );
}

function Note({ fg, bg, line, titre, children }: { fg: string; bg: string; line: string; titre: string; children: React.ReactNode }) {
  return (
    <div style={{ background: bg, border: `1px solid ${line}`, borderRadius: 6, padding: '10px 13px' }}>
      <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: '.07em', textTransform: 'uppercase', color: fg }}>{titre}</div>
      <p style={{ margin: '4px 0 0', fontSize: 12.5, color: '#172b4d', lineHeight: 1.55, maxWidth: '74ch' }}>{children}</p>
    </div>
  );
}
