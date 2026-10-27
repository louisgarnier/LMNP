/**
 * Onglet « Ce qui expire » — la seule tirelire qui peut disparaître.
 *
 * Ouvre sur le délai restant, explique pourquoi cet argent meurt, montre les
 * tranches, puis dit ce qu'il faudrait exactement pour ne rien perdre.
 * Cf. TIRELIRES-FISCALES-EXPLICATION.md, partie 10.
 *
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */
'use client';

import { echeancierDeficit } from '@/utils/echeancier';
import type { ChaineResponse } from '@/utils/positionFiscale';

const eur = (n: number) =>
  n.toLocaleString('fr-FR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + ' €';

const T1 = '#a8620d', T1_BG = '#fdf5e9', T1_LINE = '#e6d0a8';
const ROUGE = '#bf2600';

export default function OngletCeQuiExpire({ chaine }: { chaine: ChaineResponse }) {
  const annees = [...chaine.years].sort((a, b) => a - b);
  const dernier = chaine.chain[String(annees[annees.length - 1])];
  const tranches = echeancierDeficit(dernier?.deficit_millesimes ?? []);
  const total = tranches.reduce((s, t) => s + t.montant, 0);
  const urgente = tranches[0];

  if (!tranches.length) {
    return (
      <section style={{ background: '#fff', border: '1px solid #c1c7d0', borderRadius: 8, padding: '22px 18px' }}>
        <div style={{ fontSize: 15, fontWeight: 700, color: '#172b4d' }}>Rien n&apos;expire</div>
        <p style={{ fontSize: 13, color: '#5e6c84', marginTop: 6, lineHeight: 1.55, maxWidth: '70ch' }}>
          La tirelire déficit est vide. Seule celle-ci se périme : les amortissements reportés sont
          utilisables sans limite de durée.
        </p>
      </section>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
      {/* ═══ le délai, en gros ═══ */}
      <section style={{ background: '#fff', border: '1px solid #c1c7d0', borderRadius: 8, padding: '18px 20px', borderLeft: `4px solid ${ROUGE}` }}>
        <div style={{ fontSize: 34, fontWeight: 700, color: ROUGE, lineHeight: 1.1, fontVariantNumeric: 'tabular-nums' }}>
          {urgente.annees} ans {urgente.mois} mois
        </div>
        <div style={{ fontSize: 13.5, color: '#172b4d', marginTop: 6, lineHeight: 1.5, maxWidth: '70ch' }}>
          c&apos;est le temps qu&apos;il te reste pour utiliser <b>{eur(urgente.montant)}</b> — soit{' '}
          <b>{Math.round(urgente.part)} %</b> de ta tirelire déficit. Passé le 31/12/{urgente.expire_fin},
          ils sont perdus sans contrepartie.
        </div>
      </section>

      {/* ═══ pourquoi ═══ */}
      <section style={{ background: '#fff', border: '1px solid #c1c7d0', borderRadius: 8, overflow: 'hidden' }}>
        <Entete titre="Pourquoi cet argent peut disparaître" />
        <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 12 }}>
          <p style={{ margin: 0, fontSize: 13, color: '#172b4d', lineHeight: 1.6, maxWidth: '72ch' }}>
            Le déficit reportable a une durée de vie. Chaque euro naît l&apos;année où la perte est
            constatée, et meurt un certain nombre d&apos;années plus tard — <b>qu&apos;il ait servi ou
            non</b>. L&apos;amortissement reporté, lui, ne meurt jamais : c&apos;est pour ça qu&apos;une
            seule des deux tirelires figure sur cet écran.
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: 10 }}>
            <Encart bg={T1_BG} line={T1_LINE} fg={T1} titre="Tirelire déficit" texte="se périme · c'est elle qui est ici" />
            <Encart bg="#edf6f5" line="#b0d5d2" fg="#0d6360" titre="Tirelire amortissements" texte="n'expire jamais · rien à surveiller" />
          </div>
        </div>
      </section>

      {/* ═══ les tranches ═══ */}
      <section style={{ background: '#fff', border: '1px solid #c1c7d0', borderRadius: 8, overflow: 'hidden' }}>
        <Entete
          titre="Les tranches de ta tirelire déficit"
          sous={`${eur(total)} au total · servies de la plus ancienne à la plus récente`}
        />
        <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 9 }}>
          {tranches.map((t) => (
            <div key={t.annee} style={{ display: 'grid', gridTemplateColumns: '5.5rem 1fr auto', gap: 12, alignItems: 'center' }}>
              <span style={{ fontSize: 11.5, color: '#5e6c84', fontFamily: 'ui-monospace, Menlo, monospace' }}>
                née en {t.annee}
              </span>
              <div style={{ position: 'relative', height: 26, background: T1_BG, border: `1px solid ${T1_LINE}`, borderRadius: 3, overflow: 'hidden' }}>
                <div style={{ position: 'absolute', inset: 0, width: `${t.part}%`, background: T1, opacity: 0.22 }} />
                <span style={{ position: 'absolute', left: 9, top: '50%', transform: 'translateY(-50%)', fontFamily: 'ui-monospace, Menlo, monospace', fontSize: 12, fontWeight: 700, color: T1 }}>
                  {eur(t.montant)}
                </span>
              </div>
              <span style={{ fontSize: 11.5, fontFamily: 'ui-monospace, Menlo, monospace', whiteSpace: 'nowrap', color: t.urgent ? ROUGE : '#5e6c84', fontWeight: t.urgent ? 700 : 400 }}>
                meurt fin {t.expire_fin} · dans {t.annees} ans {t.mois} mois
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ comment éviter la perte ═══ */}
      <section style={{ background: '#fff', border: '1px solid #c1c7d0', borderRadius: 8, overflow: 'hidden' }}>
        <Entete titre="Comment éviter la perte" />
        <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ background: '#eef6f1', border: '1px solid #c8e0d2', borderRadius: 6, padding: '12px 14px' }}>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '.07em', textTransform: 'uppercase', color: '#1c6440' }}>
              Ce qu&apos;il faudrait, concrètement
            </div>
            <p style={{ margin: '5px 0 0', fontSize: 13, color: '#172b4d', lineHeight: 1.55, maxWidth: '72ch' }}>
              Un <b>bénéfice fiscal de {eur(urgente.montant)}</b> avant fin {urgente.expire_fin} suffirait
              à consommer entièrement la tranche menacée. Le moteur sert toujours la plus ancienne en
              premier — le premier euro de bénéfice attaque donc celle qui va mourir.
            </p>
          </div>

          <div>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '.07em', textTransform: 'uppercase', color: ROUGE, marginBottom: 7 }}>
              Si tu ne fais rien
            </div>
            <div style={{ overflowX: 'auto', border: '1px solid #dfe1e6', borderRadius: 6 }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, fontVariantNumeric: 'tabular-nums' }}>
                <thead>
                  <tr style={{ background: '#eceef1' }}>
                    <th style={cellHead}>Fin</th>
                    <th style={{ ...cellHead, textAlign: 'right' }}>Montant perdu</th>
                    <th style={{ ...cellHead, textAlign: 'right' }}>Il resterait</th>
                  </tr>
                </thead>
                <tbody style={{ color: '#172b4d' }}>
                  {tranches.map((t) => (
                    <tr key={t.annee} style={{ borderTop: '1px solid #f1f2f4' }}>
                      <td style={cell}>{t.expire_fin}</td>
                      <td style={{ ...cell, textAlign: 'right', color: ROUGE, fontWeight: 600 }}>{eur(t.montant)}</td>
                      <td style={{ ...cell, textAlign: 'right' }}>{eur(t.resteApres)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <p style={{ margin: 0, fontSize: 12.5, color: '#5e6c84', lineHeight: 1.55, maxWidth: '72ch' }}>
            <b>Le levier que tu pilotes déjà.</b> Sur un exercice bénéficiaire, le choix « imputer en
            priorité » décide quelle tirelire est vidée. <i>Déficit d&apos;abord</i> vide celle qui
            pourrit ; <i>amortissement d&apos;abord</i> la laisse vieillir. C&apos;est ce réglage qui
            décide si cet écran affiche une alerte ou non.
          </p>
        </div>
      </section>
    </div>
  );
}

const cellHead: React.CSSProperties = {
  fontSize: 9.5, textTransform: 'uppercase', letterSpacing: '.04em', color: '#5e6c84',
  padding: '7px 10px', textAlign: 'left', fontWeight: 700,
};
const cell: React.CSSProperties = { padding: '7px 10px' };

function Entete({ titre, sous }: { titre: string; sous?: string }) {
  return (
    <div style={{ padding: '11px 16px', borderBottom: '1px solid #dfe1e6', background: '#fafbfc' }}>
      <div style={{ fontSize: 15, fontWeight: 700, color: '#172b4d' }}>{titre}</div>
      {sous && <div style={{ fontSize: 12, color: '#5e6c84', marginTop: 2 }}>{sous}</div>}
    </div>
  );
}

function Encart({ bg, line, fg, titre, texte }: { bg: string; line: string; fg: string; titre: string; texte: string }) {
  return (
    <div style={{ background: bg, border: `1px solid ${line}`, borderRadius: 6, padding: '10px 12px' }}>
      <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '.07em', textTransform: 'uppercase', color: fg }}>{titre}</div>
      <div style={{ fontSize: 12.5, color: '#5e6c84', marginTop: 3 }}>{texte}</div>
    </div>
  );
}
