/**
 * Module « Position fiscale » — cinq onglets.
 *
 * Ordre du raisonnement : où j'en suis → comment ça s'est rempli → par
 * appartement → face à la liasse → ce qui expire. Il reprend le document de
 * référence des deux tirelires (docs/project/analysis/TIRELIRES-FISCALES-EXPLICATION.md).
 *
 * L'onglet actif est dans l'URL (?onglet=N) pour être partageable et permettre
 * à la carte d'accueil de pointer directement sur une vue.
 *
 * Données : GET /api/fiscal/chaine. L'app est la référence, la liasse un contrôle
 * (ADR 2026-07-29).
 *
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */
'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import ChaineFiscaleTable from '@/components/ChaineFiscaleTable';
import RecitExercice from '@/components/RecitExercice';
import SelecteurExercice from '@/components/SelecteurExercice';
import OngletCeQuiExpire from '@/components/OngletCeQuiExpire';
import OngletParAppartement from '@/components/OngletParAppartement';
import OngletFaceLiasse from '@/components/OngletFaceLiasse';
import { resumeFiscal, anneesAvant, type ChaineResponse } from '@/utils/positionFiscale';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const ONGLETS = [
  { n: 1, cle: 'ma-position', label: 'Ma position' },
  { n: 2, cle: 'par-appartement', label: 'Par appartement' },
  { n: 3, cle: 'face-liasse', label: 'Face à la liasse' },
  { n: 4, cle: 'ce-qui-expire', label: 'Ce qui expire' },
] as const;

export default function PositionFiscalePage() {
  return (
    <Suspense fallback={<div style={{ padding: 24, color: '#5e6c84' }}>Chargement…</div>}>
      <Contenu />
    </Suspense>
  );
}

function Contenu() {
  const router = useRouter();
  const params = useSearchParams();
  const actif = Number(params.get('onglet') ?? 1);

  const [chaine, setChaine] = useState<ChaineResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/fiscal/chaine`)
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(setChaine)
      .catch((e) => setError(String(e)));
  }, []);

  const aller = (n: number) => router.push(`/dashboard/position-fiscale?onglet=${n}`);

  return (
    <div style={{ padding: 24, maxWidth: 1180, margin: '0 auto' }}>
      <h1 style={{ fontSize: 20, fontWeight: 700, color: '#172b4d', margin: 0 }}>Position fiscale</h1>
      <p style={{ fontSize: 13, color: '#5e6c84', marginTop: 6, lineHeight: 1.5, maxWidth: '70ch' }}>
        Tous appartements confondus. L&apos;application calcule depuis tes transactions ; la liasse
        déposée ne sert que de contrôle.
      </p>

      {/* onglets */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3, borderBottom: '1px solid #dfe1e6', marginTop: 18 }}>
        {ONGLETS.map((o) => {
          const on = o.n === actif;
          return (
            <button
              key={o.n}
              onClick={() => aller(o.n)}
              style={{
                fontSize: 13, padding: '8px 12px', border: 'none', cursor: 'pointer',
                background: on ? '#fff' : 'transparent',
                color: on ? '#172b4d' : '#5e6c84',
                fontWeight: on ? 600 : 400,
                borderBottom: `2px solid ${on ? '#1e3a5f' : 'transparent'}`,
              }}
            >
              <span style={{ fontFamily: 'ui-monospace, Menlo, monospace', fontSize: 11, color: '#97a0af', marginRight: 6 }}>
                {o.n}
              </span>
              {o.label}
            </button>
          );
        })}
      </div>

      <div style={{ marginTop: 20 }}>
        {error && <div style={{ color: '#bf2600', fontSize: 13 }}>Impossible de charger : {error}</div>}
        {!error && !chaine && <div style={{ color: '#5e6c84', fontSize: 13 }}>Chargement…</div>}
        {chaine && actif === 1 && <OngletMaPosition chaine={chaine} />}
        {chaine && actif === 2 && <OngletParAppartement chaine={chaine} />}
        {chaine && actif === 3 && <OngletFaceLiasse chaine={chaine} />}
        {chaine && actif === 4 && <OngletCeQuiExpire chaine={chaine} />}
      </div>
    </div>
  );
}


const eur = (n: number) =>
  n.toLocaleString('fr-FR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + ' €';
const eurSigned = (n: number) => (n > 0 ? '+' : '') + eur(n);

/**
 * Onglet 1 — deux cartes empilées : où j'en suis à l'exercice choisi, puis
 * comment on y est arrivé sur toute la période. Le sélecteur pilote la
 * première ; la seconde donne la vue d'ensemble.
 */
function OngletMaPosition({ chaine }: { chaine: ChaineResponse }) {
  const annees = [...chaine.years].sort((a, b) => a - b);
  const [annee, setAnnee] = useState<number>(annees[annees.length - 1]);
  const c = chaine.chain[String(annee)];
  const brouillons = new Set(annees.filter((y) => chaine.chain[String(y)]?.brouillon));

  if (!c) return null;

  // Le millésime menacé se lit à l'exercice affiché, pas au dernier connu.
  const millesimes = [...(c.deficit_millesimes ?? [])].sort((a, b) => a.expire_fin - b.expire_fin);
  const menace = millesimes.length ? millesimes[0] : null;
  const restant = menace ? anneesAvant(menace.expire_fin) : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
      {/* ═══ CARTE 1 : où j'en suis ═══ */}
      <Carte
        titre={`Où j'en suis au 31/12/${annee}`}
        sous_titre={c.brouillon ? 'Exercice en cours — aucune liasse déposée' : undefined}
        entete={<SelecteurExercice annees={annees} actif={annee} brouillons={brouillons} onChange={setAnnee} />}
      >
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 12 }}>
          <div style={{ background: '#fdf5e9', border: '1px solid #e6d0a8', borderRadius: 6, padding: '14px 16px' }}>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '.08em', textTransform: 'uppercase', color: '#a8620d' }}>
              Tirelire déficit
            </div>
            <div style={{ fontSize: 28, fontWeight: 700, color: '#a8620d', fontVariantNumeric: 'tabular-nums', lineHeight: 1.2 }}>
              {eur(c.deficit_fin_app)}
            </div>
            <div style={{ fontSize: 12, color: '#5e6c84', marginTop: 4 }}>
              départ {eur(c.deficit_depart)} · mouvement {eurSigned(c.deficit_mouvement)}
            </div>
            <div style={{ fontSize: 12, color: menace ? '#bf2600' : '#5e6c84', marginTop: 4, fontWeight: menace ? 600 : 400 }}>
              {menace
                ? `⏳ ${eur(menace.montant)} expirent fin ${menace.expire_fin}${restant !== null ? ` — dans ${restant} ans` : ''}`
                : 'tirelire vide'}
            </div>
          </div>

          <div style={{ background: '#edf6f5', border: '1px solid #b0d5d2', borderRadius: 6, padding: '14px 16px' }}>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '.08em', textTransform: 'uppercase', color: '#0d6360' }}>
              Tirelire amortissements
            </div>
            <div style={{ fontSize: 28, fontWeight: 700, color: '#0d6360', fontVariantNumeric: 'tabular-nums', lineHeight: 1.2 }}>
              {eur(c.amort_fin_app)}
            </div>
            <div style={{ fontSize: 12, color: '#5e6c84', marginTop: 4 }}>
              départ {eur(c.amort_depart)} · mis de côté {eurSigned(c.amort_mis_de_cote)}
              {c.amort_impute > 0.5 && ` · puisé ${eur(c.amort_impute)}`}
            </div>
            <div style={{ fontSize: 12, color: '#5e6c84', marginTop: 4 }}>
              ♾️ n&apos;expire jamais · preuve à la revente
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px 28px', marginTop: 12, padding: '10px 14px', background: '#fff', border: '1px solid #dfe1e6', borderRadius: 6 }}>
          <Chiffre label="En réserve" valeur={eur(c.deficit_fin_app + c.amort_fin_app)} />
          <Chiffre label="Total amorti à ce jour" valeur={eur(c.amort_total_cumul)} />
          <Chiffre label="dont déjà déduit" valeur={eur(c.amort_deduit_cumul)} />
          <Chiffre
            label="Résultat imposable"
            valeur={eur(c.resultat_fiscal_imposable)}
            couleur={c.resultat_fiscal_imposable > 0 ? '#bf2600' : '#006644'}
          />
        </div>

        <h3 style={{ fontSize: 13.5, fontWeight: 700, color: '#172b4d', margin: '16px 0 8px' }}>
          Ce qui s&apos;est passé en {annee}
        </h3>
        <RecitExercice ligne={c} />
      </Carte>

      {/* ═══ CARTE 2 : comment on en est arrivé là ═══ */}
      <Carte
        titre="Comment ça s'est rempli"
        sous_titre={`Les ${annees.length} exercices depuis ${annees[0]} — la colonne « avant amort » décide de tout`}
      >
        <pre style={{ margin: '0 0 10px', fontFamily: 'ui-monospace, Menlo, monospace', fontSize: 11.5, lineHeight: 1.75, background: '#fafbfc', border: '1px solid #dfe1e6', borderRadius: 6, padding: '11px 14px', overflowX: 'auto', color: '#172b4d' }}>
{`Résultat comptable + amortissement de l'année = RÉSULTAT AVANT AMORTISSEMENT

   négatif            →  déduit 0 ; la perte va en tirelire déficit,
                         tout l'amortissement en tirelire amortissements
   positif, < amort   →  l'amortissement efface le bénéfice jusqu'à zéro ;
                         le surplus part en tirelire amortissements
   positif, ≥ amort   →  tout passe, puis ON PUISE dans une tirelire`}
        </pre>
        <p style={{ fontSize: 12.5, color: '#5e6c84', margin: '0 0 6px', lineHeight: 1.5, maxWidth: '72ch' }}>
          L&apos;amortissement ne peut jamais créer de perte : il descend le résultat jusqu&apos;à zéro,
          jamais en dessous. Ce qui ne rentre pas est mis de côté — et les deux tirelires se
          remplissent en même temps, à partir du même chiffre.
        </p>
        <ChaineFiscaleTable data={chaine} />
        <p style={{ fontSize: 12, color: '#5e6c84', marginTop: 10, lineHeight: 1.5 }}>
          Choisis un exercice ci-dessus pour lire son récit en détail dans la première carte.
        </p>
      </Carte>
    </div>
  );
}

/** Coquille de carte, pour empiler les deux blocs de l'onglet. */
function Carte({ titre, sous_titre, entete, children }: {
  titre: string; sous_titre?: string; entete?: React.ReactNode; children: React.ReactNode;
}) {
  return (
    <section style={{ background: '#fff', border: '1px solid #c1c7d0', borderRadius: 8, overflow: 'hidden' }}>
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'baseline', justifyContent: 'space-between', gap: 10, padding: '11px 16px', borderBottom: '1px solid #dfe1e6', background: '#fafbfc' }}>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, color: '#172b4d' }}>{titre}</div>
          {sous_titre && <div style={{ fontSize: 12, color: '#5e6c84', marginTop: 2 }}>{sous_titre}</div>}
        </div>
        {entete}
      </div>
      <div style={{ padding: '14px 16px' }}>{children}</div>
    </section>
  );
}

function Chiffre({ label, valeur, couleur }: { label: string; valeur: string; couleur?: string }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '.07em', textTransform: 'uppercase', color: '#5e6c84' }}>
        {label}
      </span>
      <span style={{ fontSize: 15, fontWeight: 700, color: couleur ?? '#172b4d', fontVariantNumeric: 'tabular-nums' }}>
        {valeur}
      </span>
    </div>
  );
}


