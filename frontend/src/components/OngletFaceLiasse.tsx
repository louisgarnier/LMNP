/**
 * Onglet « Face à la liasse » — l'application est la référence, la liasse un contrôle.
 *
 * La colonne App est calculée depuis les transactions, sans jamais lire la
 * liasse. La colonne Liasse est un fichier importé : elle sert à repérer les
 * écarts et à questionner le cabinet — jamais à corriger l'application.
 * Cf. ADR « L'application est la source de vérité fiscale » (2026-07-29).
 *
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */
'use client';

import { Fragment, useEffect, useState } from 'react';
import SelecteurExercice from '@/components/SelecteurExercice';
import type { ChaineResponse, ReconResponse, LigneRecon, ExplicationEcart } from '@/utils/positionFiscale';

type Explication = ExplicationEcart;

/** Couleurs par nature d'écart — le ton vient du serveur, pas de l'écran. */
const TON: Record<string, { fg: string; bg: string; line: string }> = {
  rouge:  { fg: '#bf2600', bg: '#fdf0f0', line: '#eec6c6' },
  neutre: { fg: '#5e6c84', bg: '#f4f5f7', line: '#dfe1e6' },
  info:   { fg: '#0747a6', bg: '#deebff', line: '#b3d4ff' },
};

interface LigneCerfa {
  bloc: 'ACTIF' | 'PASSIF';
  case: string;
  libelle: string;
  app: number;
  liasse: number | null;
  ecart: number | null;
  ok: boolean | null;
  total: boolean;
  explication: Explication | null;
}
interface BilanCerfa {
  annee: number;
  brouillon: boolean;
  equilibre: number;
  nb_ecarts: number;
  lignes: LigneCerfa[];
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const eur = (n: number | null) =>
  n === null ? '—' : n.toLocaleString('fr-FR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + ' €';
const eurSigned = (n: number) => (n > 0 ? '+' : '') + eur(n);

const VERT = '#1c6440', VERT_BG = '#eef6f1';
const ROUGE = '#bf2600', ROUGE_BG = '#fdf0f0';

export default function OngletFaceLiasse({ chaine }: { chaine: ChaineResponse }) {
  const annees = [...chaine.years].sort((a, b) => a - b);
  const brouillons = new Set(annees.filter((y) => chaine.chain[String(y)]?.brouillon));
  // On ouvre sur le dernier exercice comparable, pas sur un brouillon.
  const comparables = annees.filter((y) => !brouillons.has(y));
  const [annee, setAnnee] = useState<number>(
    comparables.length ? comparables[comparables.length - 1] : annees[annees.length - 1]
  );

  const [recon, setRecon] = useState<ReconResponse | null>(null);
  const [bilan, setBilan] = useState<BilanCerfa | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/reconciliation`)
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(setRecon)
      .catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/fiscal/bilan-cerfa?year=${annee}`)
      .then((r) => (r.ok ? r.json() : null))
      .then(setBilan)
      .catch(() => setBilan(null));
  }, [annee]);

  if (error) return <div style={{ color: ROUGE, fontSize: 13 }}>Impossible de charger : {error}</div>;
  if (!recon) return <div style={{ color: '#5e6c84', fontSize: 13 }}>Chargement…</div>;

  const r = recon.results[String(annee)];
  const sansLiasse = annees.filter((y) => recon.results[String(y)]?.brouillon);
  const enEcart = r ? r.lignes.filter((l) => l.ok === false) : [];
  const erreursCR = enEcart.filter((l) => l.explication?.ton === 'rouge');
  const methodeCR = enEcart.length - erreursCR.length;
  const erreursBilan = bilan ? bilan.lignes.filter((l) => l.ok === false && l.explication?.ton === 'rouge') : [];
  const methodeBilan = bilan ? bilan.lignes.filter((l) => l.ok === false).length - erreursBilan.length : 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
      {/* sens de lecture */}
      <div style={{ background: VERT_BG, border: `1px solid #c8e0d2`, borderRadius: 6, padding: '11px 14px' }}>
        <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: '.07em', textTransform: 'uppercase', color: VERT }}>
          Sens de lecture
        </div>
        <p style={{ margin: '4px 0 0', fontSize: 12.5, color: '#172b4d', lineHeight: 1.55, maxWidth: '76ch' }}>
          <b>La colonne « App » est la référence.</b> Elle est calculée depuis tes transactions,
          exercice après exercice, sans jamais lire la liasse. La colonne « Liasse » est un fichier
          de contrôle importé : elle sert à repérer les écarts et à questionner le cabinet — jamais
          à corriger l&apos;application.
        </p>
      </div>

      <section style={{ background: '#fff', border: '1px solid #c1c7d0', borderRadius: 8, overflow: 'hidden' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'baseline', justifyContent: 'space-between', gap: 10, padding: '11px 16px', borderBottom: '1px solid #dfe1e6', background: '#fafbfc' }}>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#172b4d' }}>
              Compte de résultat {annee} <span style={{ fontWeight: 400, color: '#5e6c84', fontSize: 12 }}>· CERFA 2033-B</span>
            </div>
            <div style={{ fontSize: 12, color: '#5e6c84', marginTop: 2 }}>
              {r
                ? r.brouillon
                  ? 'Aucune liasse déposée — la position est calculée, rien à comparer'
                  : `${r.biens_inclus.length} appartement${r.biens_inclus.length > 1 ? 's' : ''} · ` +
                    (erreursCR.length > 0
                      ? `${erreursCR.length} erreur${erreursCR.length > 1 ? 's' : ''} du cabinet`
                      : 'aucune erreur') +
                    (methodeCR > 0 ? ` · ${methodeCR} écart${methodeCR > 1 ? 's' : ''} de méthode (expliqué${methodeCR > 1 ? 's' : ''})` : '')
                : 'exercice inconnu'}
            </div>
          </div>
          <SelecteurExercice annees={annees} actif={annee} brouillons={brouillons} onChange={setAnnee} />
        </div>

        <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 13 }}>
          {r ? (
            <>
              <div style={{ overflowX: 'auto', border: '1px solid #dfe1e6', borderRadius: 6 }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, fontVariantNumeric: 'tabular-nums' }}>
                  <thead>
                    <tr style={{ background: '#eceef1' }}>
                      <th style={th}>Poste</th>
                      <th style={{ ...th, textAlign: 'right', background: VERT_BG, color: VERT }}>
                        App <span style={{ fontSize: 8.5, border: `1px solid ${VERT}`, borderRadius: 2, padding: '0 3px', marginLeft: 3 }}>référence</span>
                      </th>
                      <th style={{ ...th, textAlign: 'right' }}>Liasse déposée</th>
                      <th style={{ ...th, textAlign: 'right' }}>Écart</th>
                    </tr>
                  </thead>
                  <tbody style={{ color: '#172b4d' }}>
                    {r.lignes.map((l) => <Ligne key={l.poste} l={l} />)}
                  </tbody>
                </table>
              </div>

              {r.brouillon ? (
                <Note fg="#0747a6" bg="#deebff" line="#b3d4ff" titre="Exercice en cours">
                  La liasse {annee} n&apos;est pas encore déposée. L&apos;application affiche quand même
                  sa position — charger la liasse plus tard remplira la colonne de contrôle
                  <b> sans rien recalculer</b>.
                </Note>
              ) : enEcart.length > 0 ? (
                <Explications
                  items={enEcart.map((l) => ({
                    nom: l.poste,
                    ecart: l.ecart,
                    e: l.explication ?? {
                      statut: 'a_investiguer', libelle: 'Non expliqué', ton: 'info',
                      action: 'cause non établie', cause: 'Aucune explication enregistrée pour cet écart.',
                    },
                  }))}
                />
              ) : (
                <Note fg={VERT} bg={VERT_BG} line="#c8e0d2" titre="Aucun écart">
                  La liasse {annee} concorde avec le calcul de l&apos;application sur tous les postes.
                </Note>
              )}
            </>
          ) : (
            <div style={{ color: '#5e6c84', fontSize: 13 }}>Aucune donnée pour cet exercice.</div>
          )}
        </div>
      </section>

      {/* ═══ BILAN 2033-A ═══ */}
      {bilan && (
        <section style={{ background: '#fff', border: '1px solid #c1c7d0', borderRadius: 8, overflow: 'hidden' }}>
          <div style={{ padding: '11px 16px', borderBottom: '1px solid #dfe1e6', background: '#fafbfc' }}>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#172b4d' }}>
              Bilan {bilan.annee} <span style={{ fontWeight: 400, color: '#5e6c84', fontSize: 12 }}>· CERFA 2033-A</span>
            </div>
            <div style={{ fontSize: 12, color: '#5e6c84', marginTop: 2 }}>
              {Math.abs(bilan.equilibre) < 0.01
                ? 'Actif = passif à l’euro près'
                : `⚠️ déséquilibre de ${eur(bilan.equilibre)}`}
              {!bilan.brouillon &&
                ` · ${erreursBilan.length > 0 ? `${erreursBilan.length} erreur${erreursBilan.length > 1 ? 's' : ''} du cabinet` : 'aucune erreur'}` +
                (methodeBilan > 0 ? ` · ${methodeBilan} écart${methodeBilan > 1 ? 's' : ''} de méthode (expliqué${methodeBilan > 1 ? 's' : ''})` : '')}
            </div>
          </div>
          <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 13 }}>
            <div style={{ overflowX: 'auto', border: '1px solid #dfe1e6', borderRadius: 6 }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, fontVariantNumeric: 'tabular-nums' }}>
                <thead>
                  <tr style={{ background: '#eceef1' }}>
                    <th style={{ ...th, width: '3.5rem' }}>Case</th>
                    <th style={th}>Poste</th>
                    <th style={{ ...th, textAlign: 'right', background: VERT_BG, color: VERT }}>
                      App <span style={{ fontSize: 8.5, border: `1px solid ${VERT}`, borderRadius: 2, padding: '0 3px', marginLeft: 3 }}>référence</span>
                    </th>
                    <th style={{ ...th, textAlign: 'right' }}>Liasse déposée</th>
                    <th style={{ ...th, textAlign: 'right' }}>Écart</th>
                  </tr>
                </thead>
                <tbody style={{ color: '#172b4d' }}>
                  {bilan.lignes.map((l, i) => {
                    const nouveauBloc = i === 0 || bilan.lignes[i - 1].bloc !== l.bloc;
                    const ecart = l.ok === false;
                    const grave = ecart && l.explication?.ton === 'rouge';
                    return (
                      <Fragment key={l.case}>
                        {nouveauBloc && (
                          <tr style={{ background: '#f4f5f7' }}>
                            <td colSpan={5} style={{ ...td, fontSize: 10, fontWeight: 700, letterSpacing: '.07em', textTransform: 'uppercase', color: '#5e6c84' }}>
                              {l.bloc}
                            </td>
                          </tr>
                        )}
                        <tr
                          style={{
                            borderTop: l.total ? '2px solid #172b4d' : '1px solid #f1f2f4',
                            background: grave ? ROUGE_BG : l.total ? '#fafbfc' : undefined,
                            fontWeight: l.total ? 700 : 400,
                          }}
                        >
                          <td style={{ ...td, color: '#97a0af', fontFamily: 'ui-monospace, Menlo, monospace', fontSize: 11 }}>{l.case}</td>
                          <td style={td}>{l.libelle}</td>
                          <td style={{ ...td, textAlign: 'right', background: VERT_BG, fontWeight: 700 }}>{eur(l.app)}</td>
                          <td style={{ ...td, textAlign: 'right', color: '#5e6c84', fontStyle: l.liasse === null ? 'italic' : 'normal' }}>
                            {l.liasse === null ? 'non renseigné' : eur(l.liasse)}
                          </td>
                          <td style={{ ...td, textAlign: 'right', fontWeight: grave ? 700 : 400, color: grave ? ROUGE : ecart ? '#5e6c84' : VERT, whiteSpace: 'nowrap' }}>
                            {l.ok === null ? '—' : l.ok ? '✓' : eurSigned(l.ecart as number)}
                            {ecart && l.explication && <Pastille e={l.explication} />}
                          </td>
                        </tr>
                      </Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <Explications
              items={bilan.lignes
                .filter((l) => l.ok === false)
                .map((l) => ({
                  nom: `${l.case} — ${l.libelle}`,
                  ecart: l.ecart,
                  e: l.explication ?? {
                    statut: 'a_investiguer', libelle: 'Non expliqué', ton: 'info',
                    action: 'cause non établie', cause: 'Aucune explication enregistrée pour cet écart.',
                  },
                }))}
            />

            <Note fg="#5e6c84" bg="#fafbfc" line="#dfe1e6" titre="Lire les lignes « non renseigné »">
              L&apos;application détaille des postes que la liasse regroupe : d&apos;où des cases
              vides côté liasse en face de montants côté app. Ce ne sont pas des écarts de calcul.
            </Note>
          </div>
        </section>
      )}

      {sansLiasse.length > 0 && (
        <Note fg="#5e6c84" bg="#fafbfc" line="#dfe1e6" titre="Exercices sans liasse">
          {sansLiasse.join(', ')} — pas encore de liasse déposée. La position y est calculée
          normalement ; seule la colonne de contrôle reste vide.
        </Note>
      )}
    </div>
  );
}

function Pastille({ e }: { e: Explication }) {
  const t = TON[e.ton] ?? TON.neutre;
  return (
    <span style={{
      display: 'inline-block', fontSize: 9, fontWeight: 700, letterSpacing: '.03em',
      textTransform: 'uppercase', padding: '1px 5px', borderRadius: 3, whiteSpace: 'nowrap',
      background: t.bg, color: t.fg, border: `1px solid ${t.line}`, marginLeft: 6,
    }}>
      {e.libelle}
    </span>
  );
}

/** Le détail des causes, sous le tableau : un écart sans explication est inexploitable. */
function Explications({ items }: { items: Array<{ nom: string; ecart: number | null; e: Explication }> }) {
  if (!items.length) return null;
  const erreurs = items.filter((it) => it.e.ton === 'rouge');
  const methode = items.filter((it) => it.e.ton !== 'rouge');
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {erreurs.length > 0 && (
        <>
          <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: '.07em', textTransform: 'uppercase', color: ROUGE }}>
            À corriger par le cabinet
          </div>
          <Blocs items={erreurs} />
        </>
      )}
      {methode.length > 0 && (
        <details>
          <summary style={{ cursor: 'pointer', fontSize: 12, color: '#5e6c84', padding: '4px 0' }}>
            {methode.length} écart{methode.length > 1 ? 's' : ''} de méthode expliqué{methode.length > 1 ? 's' : ''} —
            différences de classement ou de date, <b>rien à corriger</b>. Cliquer pour le détail.
          </summary>
          <div style={{ marginTop: 8 }}>
            <Blocs items={methode} />
          </div>
        </details>
      )}
    </div>
  );
}

function Blocs({ items }: { items: Array<{ nom: string; ecart: number | null; e: Explication }> }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {items.map((it, i) => {
        const t = TON[it.e.ton] ?? TON.neutre;
        return (
          <div key={i} style={{ background: t.bg, border: `1px solid ${t.line}`, borderRadius: 6, padding: '9px 12px' }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'baseline', gap: 8 }}>
              <span style={{ fontSize: 12.5, fontWeight: 700, color: '#172b4d' }}>{it.nom}</span>
              {it.ecart !== null && (
                <span style={{ fontFamily: 'ui-monospace, Menlo, monospace', fontSize: 12, fontWeight: 700, color: t.fg }}>
                  {eurSigned(it.ecart)}
                </span>
              )}
              <span style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', color: t.fg }}>
                {it.e.libelle} — {it.e.action}
              </span>
            </div>
            <p style={{ margin: '4px 0 0', fontSize: 12.5, color: '#172b4d', lineHeight: 1.5, maxWidth: '80ch' }}>
              {it.e.cause}
            </p>
          </div>
        );
      })}
    </div>
  );
}


function Ligne({ l }: { l: LigneRecon }) {
  const ecart = l.ok === false;
  // Le rouge est réservé aux erreurs du cabinet. Un écart expliqué (méthode,
  // date) est un NON-problème : il reste discret, pastille grise à l'appui.
  const grave = ecart && l.explication?.ton === 'rouge';
  return (
    <tr style={{ borderTop: '1px solid #f1f2f4', background: grave ? ROUGE_BG : undefined }}>
      <td style={td}>{l.poste}</td>
      <td style={{ ...td, textAlign: 'right', background: VERT_BG, fontWeight: 700 }}>{eur(l.app)}</td>
      <td style={{ ...td, textAlign: 'right', color: '#5e6c84', fontStyle: l.liasse === null ? 'italic' : 'normal' }}>
        {l.liasse === null ? 'pas de liasse' : eur(l.liasse)}
      </td>
      <td style={{ ...td, textAlign: 'right', fontWeight: grave ? 700 : 400, color: grave ? ROUGE : ecart ? '#5e6c84' : VERT, whiteSpace: 'nowrap' }}>
        {l.ok ? '✓' : l.ecart !== null ? eurSigned(l.ecart) : '—'}
        {ecart && l.explication && <Pastille e={l.explication} />}
      </td>
    </tr>
  );
}

const th: React.CSSProperties = {
  fontSize: 9.5, textTransform: 'uppercase', letterSpacing: '.04em', color: '#5e6c84',
  padding: '7px 10px', textAlign: 'left', fontWeight: 700,
};
const td: React.CSSProperties = { padding: '7px 10px' };

function Note({ fg, bg, line, titre, children }: { fg: string; bg: string; line: string; titre: string; children: React.ReactNode }) {
  return (
    <div style={{ background: bg, border: `1px solid ${line}`, borderRadius: 6, padding: '10px 13px' }}>
      <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: '.07em', textTransform: 'uppercase', color: fg }}>{titre}</div>
      <p style={{ margin: '4px 0 0', fontSize: 12.5, color: '#172b4d', lineHeight: 1.55, maxWidth: '76ch' }}>{children}</p>
    </div>
  );
}
