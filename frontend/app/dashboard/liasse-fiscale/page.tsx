/**
 * Position fiscale — vision globale (Maquette 1).
 *
 * Vue globale par année : liasse déposée (vérif officielle, à gauche),
 * résultat comptable par appartement + entité (au milieu), tirelires
 * calculées par l'application — déficit et amortissements reportés
 * cumulés (à droite). La colonne "Imputer en priorité" est FONCTIONNELLE :
 * elle pilote le même choix backend que la page "chaîne année par année"
 * (PUT /api/fiscal/imputation/{year}) ; changer le menu recalcule les
 * tirelires. Détail par appartement (Maquette 2) : /liasse-fiscale/detail.
 * Données : GET /api/reconciliation + GET /api/fiscal/chaine (mode + année
 * bénéficiaire, source unique partagée avec la page chaîne).
 */
'use client';

import Link from 'next/link';
import { useState, useEffect, useCallback } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const BIENS: Record<number, string> = { 25: 'Evry', 15: 'Marseille abnb', 26: 'Marseille colloc' };
// Ordre fixe (Object.keys trierait les clés numériques par valeur, pas par insertion).
const BIEN_IDS = [25, 15, 26];

const eur = (n: number) =>
  n.toLocaleString('fr-FR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + ' €';
const eurSigned = (n: number) => (n > 0 ? '+' : '') + eur(n);

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

// De /api/fiscal/chaine : on ne consomme ici que le mode et le flag bénéficiaire
// (source de vérité unique du choix d'imputation, partagée avec la page chaîne).
interface ChaineLigne {
  profitable: boolean;
  mode: 'deficit' | 'amort';
  resultat_fiscal_app: number;
}
interface ChaineResponse {
  years: number[];
  chain: Record<string, ChaineLigne>;
}

function findLigne(lignes: Ligne[], poste: string): Ligne | undefined {
  return lignes.find((l) => l.poste === poste);
}

export default function LiasseFiscalePage() {
  const [data, setData] = useState<RecResponse | null>(null);
  const [chaine, setChaine] = useState<ChaineResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState<number | null>(null);
  const [realized, setRealized] = useState(true);

  const loadReconciliation = useCallback(async () => {
    const r = await fetch(`${API_BASE_URL}/api/reconciliation?realized=${realized}`);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return (await r.json()) as RecResponse;
  }, [realized]);

  useEffect(() => {
    Promise.all([
      loadReconciliation(),
      fetch(`${API_BASE_URL}/api/fiscal/chaine?realized=${realized}`).then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json() as Promise<ChaineResponse>;
      }),
    ])
      .then(([rec, ch]) => { setData(rec); setChaine(ch); })
      .catch((e) => setError(String(e)));
  }, [loadReconciliation, realized]);

  // Change le choix d'imputation d'une année : PUT (renvoie la chaîne recalculée)
  // puis re-fetch de la réconciliation, car les tirelires cumulées changent.
  async function changeMode(year: number, mode: 'deficit' | 'amort') {
    setSaving(year);
    try {
      const res = await fetch(`${API_BASE_URL}/api/fiscal/imputation/${year}?realized=${realized}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const updatedChaine = (await res.json()) as ChaineResponse;
      const rec = await loadReconciliation();
      setChaine(updatedChaine);
      setData(rec);
    } catch (e) {
      setError(String(e));
    } finally {
      setSaving(null);
    }
  }

  if (error)
    return <div style={{ padding: 24, color: '#bf2600' }}>Impossible de charger : {error}. Backend sur {API_BASE_URL} ?</div>;
  if (!data || !chaine) return <div style={{ padding: 24, color: '#5e6c84' }}>Chargement…</div>;

  const annees = [...data.annees].sort((a, b) => a - b); // plus ancien en haut

  return (
    <div style={{ padding: 24, maxWidth: 1300, margin: '0 auto' }}>
      <Link
        href="/dashboard/liasse-fiscale/detail"
        style={{ fontSize: 12, color: '#0052cc', cursor: 'pointer', marginBottom: 6, display: 'inline-block' }}
      >
        Voir le détail par appartement →
      </Link>
      <Link href="/dashboard/liasse-fiscale/chaine" style={{ fontSize: 12, color: '#0052cc', marginLeft: 16 }}>
        Voir la chaîne fiscale année par année →
      </Link>
      <h1 style={{ fontSize: 20, fontWeight: 700, color: '#172b4d', margin: 0 }}>Position fiscale — vision globale</h1>
      <p style={{ fontSize: 13, color: '#5e6c84', marginTop: 6, lineHeight: 1.5 }}>
        Liasse déposée = vérif officielle (gauche) · résultat comptable par appartement et entité (milieu) ·
        tirelires calculées par l&apos;application — déficit et amortissements reportés cumulés (droite).
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

      <div style={{ background: '#fff', border: '1px solid #dfe1e6', borderRadius: 6, overflowX: 'auto', marginTop: 16 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11, minWidth: 1150 }}>
          <thead>
            <tr style={{ background: '#eceef1', color: '#5e6c84', fontSize: 9, textTransform: 'uppercase' }}>
              <th style={{ padding: '7px 6px', textAlign: 'left' }} rowSpan={2}>Année</th>
              <th
                style={{ padding: '7px 6px', textAlign: 'center', background: '#f1f3f5', borderLeft: '2px solid #868e96' }}
                colSpan={2}
              >
                Liasse (vérif officielle)
              </th>
              <th
                style={{ padding: '7px 6px', textAlign: 'center', borderLeft: '2px solid #172b4d' }}
                colSpan={BIEN_IDS.length + 1}
              >
                Résultat comptable par appartement
              </th>
              <th
                style={{ padding: '7px 6px', textAlign: 'center', borderLeft: '2px solid #bf2600', background: '#fff5f4' }}
                colSpan={2}
              >
                Tirelires app
              </th>
              <th
                style={{ padding: '7px 6px', textAlign: 'center', borderLeft: '2px solid #0052cc', background: '#f4f8ff' }}
                rowSpan={2}
              >
                Imputer<br />en priorité
              </th>
            </tr>
            <tr style={{ background: '#eceef1', color: '#5e6c84', fontSize: 9, textTransform: 'uppercase' }}>
              <th style={{ padding: '5px 6px', textAlign: 'right', background: '#f1f3f5', borderLeft: '2px solid #868e96' }}>Déficit</th>
              <th style={{ padding: '5px 6px', textAlign: 'right', background: '#f1f3f5' }}>Amort</th>
              {BIEN_IDS.map((b, i) => (
                <th key={b} style={{ padding: '5px 6px', textAlign: 'right', borderLeft: i === 0 ? '2px solid #172b4d' : undefined }}>
                  {BIENS[b]}
                </th>
              ))}
              <th style={{ padding: '5px 6px', textAlign: 'right', fontWeight: 700, color: '#172b4d' }}>Entité</th>
              <th style={{ padding: '5px 6px', textAlign: 'right', borderLeft: '2px solid #bf2600', background: '#fff5f4' }}>Déficit</th>
              <th style={{ padding: '5px 6px', textAlign: 'right', background: '#fff5f4' }}>Amort</th>
            </tr>
          </thead>
          <tbody style={{ color: '#172b4d' }}>
            {annees.map((an) => {
              const r = data.results[String(an)];
              const resultat = findLigne(r.lignes, 'Résultat comptable');
              const deficitCum = findLigne(r.lignes, 'Déficit reportable (cumulé)');
              const amortCum = findLigne(r.lignes, 'Amortissements reportés (cumulé)');
              const resultatEntite = resultat?.app ?? 0;
              // Année bénéficiaire + mode courant : source unique = /api/fiscal/chaine.
              const c = chaine.chain[String(an)];
              const profitable = c?.profitable ?? false;
              const mode = c?.mode ?? 'deficit';

              return (
                <tr key={an} style={{ borderTop: '1px solid #f4f5f7', background: r.brouillon ? '#eef3ff' : undefined }}>
                  <td style={{ padding: 6, fontWeight: 700, whiteSpace: 'nowrap' }}>
                    {an}
                    {r.brouillon && (
                      <span
                        style={{
                          fontSize: 8, fontWeight: 700, textTransform: 'uppercase', padding: '1px 4px', borderRadius: 3,
                          background: '#deebff', color: '#0747a6', marginLeft: 6,
                        }}
                      >
                        brouillon
                      </span>
                    )}
                  </td>
                  <td style={{ padding: 6, textAlign: 'right', background: '#f8f9fa', borderLeft: '2px solid #868e96', color: '#495057' }}>
                    {r.brouillon ? '— pas de liasse' : deficitCum?.liasse != null ? eur(deficitCum.liasse) : '—'}
                  </td>
                  <td style={{ padding: 6, textAlign: 'right', background: '#f8f9fa', color: '#495057' }}>
                    {r.brouillon ? '—' : amortCum?.liasse != null ? eur(amortCum.liasse) : '—'}
                  </td>
                  {BIEN_IDS.map((b, i) => {
                    const included = r.biens_inclus.includes(b);
                    const v = resultat?.par_bien?.[String(b)];
                    return (
                      <td
                        key={b}
                        style={{
                          padding: 6, textAlign: 'right', borderLeft: i === 0 ? '2px solid #172b4d' : undefined,
                          color: !included || v === undefined ? '#c1c7d0' : v > 0 ? '#006644' : '#172b4d',
                        }}
                      >
                        {included && v !== undefined ? eurSigned(v) : '—'}
                      </td>
                    );
                  })}
                  <td style={{ padding: 6, textAlign: 'right', fontWeight: 700, color: resultatEntite > 0 ? '#006644' : '#172b4d' }}>
                    {eurSigned(resultatEntite)}
                  </td>
                  <td style={{ padding: 6, textAlign: 'right', borderLeft: '2px solid #bf2600', background: '#fff5f4', fontWeight: 600 }}>
                    {eur(deficitCum?.app ?? 0)}
                  </td>
                  <td style={{ padding: 6, textAlign: 'right', background: '#fff5f4' }}>
                    {eur(amortCum?.app ?? 0)}
                  </td>
                  <td
                    style={{ padding: 6, textAlign: 'center', borderLeft: '2px solid #0052cc', background: '#f4f8ff' }}
                    title="Choix d'imputation par année (déficit d'abord = prudent ; amort d'abord = méthode du comptable)"
                  >
                    {profitable ? (
                      <select
                        value={mode}
                        disabled={saving === an}
                        onChange={(e) => changeMode(an, e.target.value as 'deficit' | 'amort')}
                        style={{ fontSize: 10, padding: '2px 4px', border: '1px solid #0052cc', borderRadius: 4, background: '#fff', color: '#172b4d', cursor: 'pointer' }}
                      >
                        <option value="deficit">Déficit (reco)</option>
                        <option value="amort">Amort (comptable)</option>
                      </select>
                    ) : (
                      <span style={{ color: '#c1c7d0' }}>—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: 12, display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: 11, color: '#5e6c84' }}>
        <div>
          <span style={{ display: 'inline-block', width: 12, height: 12, background: '#f1f3f5', border: '1px solid #868e96', verticalAlign: 'middle' }} />{' '}
          Liasse = officiel, en lecture seule (vérif)
        </div>
        <div>
          <span style={{ display: 'inline-block', width: 12, height: 12, background: '#fff5f4', border: '1px solid #bf2600', verticalAlign: 'middle' }} />{' '}
          Tirelires calculées par l&apos;app
        </div>
        <div>
          <span style={{ display: 'inline-block', width: 12, height: 12, background: '#f4f8ff', border: '1px solid #0052cc', verticalAlign: 'middle' }} />{' '}
          Choix d&apos;imputation (années bénéficiaires)
        </div>
      </div>

      <div
        style={{
          marginTop: 16, padding: '12px 14px', background: '#fff', border: '1px solid #dfe1e6', borderLeft: '3px solid #0052cc',
          borderRadius: 4, fontSize: 12, color: '#5e6c84', lineHeight: 1.6,
        }}
      >
        La colonne « Imputer en priorité » n&apos;apparaît que sur les années de bénéfice. Le menu est le
        <b> même choix</b> que sur la page « chaîne année par année » : le changer ici recalcule les tirelires
        (déficit d&apos;abord = prudent, le déficit expire à 10 ans ; amort d&apos;abord = méthode du comptable).
      </div>
    </div>
  );
}
