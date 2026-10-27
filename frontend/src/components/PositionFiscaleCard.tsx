/**
 * Carte « Position fiscale » de la page d'accueil.
 *
 * Ce qu'il faut savoir d'un coup d'œil : les deux tirelires, ce qui est menacé
 * de péremption, le total en réserve, l'impôt payé et le nombre d'écarts avec
 * la dernière liasse. Le détail vit dans le module fiscal.
 *
 * Aucun montant ni nom d'appartement en dur : tout vient de
 * GET /api/fiscal/chaine et GET /api/reconciliation.
 * Cf. ADR « L'application est la source de vérité fiscale » (2026-07-29).
 *
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  resumeFiscal, compterEcarts, anneesAvant, cumulImposable,
  type ChaineResponse, type ReconResponse, type ResumeFiscal,
} from '@/utils/positionFiscale';
import ChaineFiscaleTable from '@/components/ChaineFiscaleTable';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const eur = (n: number) =>
  n.toLocaleString('fr-FR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + ' €';

// Raccourcis vers les onglets du module fiscal.
const RACCOURCIS = [
  { label: 'Ma position', href: '/dashboard/position-fiscale?onglet=1' },
  { label: 'Par appartement', href: '/dashboard/position-fiscale?onglet=2' },
  { label: 'Face à la liasse', href: '/dashboard/position-fiscale?onglet=3' },
  { label: 'Ce qui expire', href: '/dashboard/position-fiscale?onglet=4' },
];

export default function PositionFiscaleCard() {
  const [chaine, setChaine] = useState<ChaineResponse | null>(null);
  const [recon, setRecon] = useState<ReconResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE_URL}/api/fiscal/chaine`).then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json() as Promise<ChaineResponse>;
      }),
      fetch(`${API_BASE_URL}/api/reconciliation`).then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json() as Promise<ReconResponse>;
      }),
    ])
      .then(([c, r]) => { setChaine(c); setRecon(r); })
      .catch((e) => setError(String(e)));
  }, []);

  if (error)
    return (
      <div style={{ padding: 16, background: '#fff', border: '1px solid #dfe1e6', borderRadius: 8, color: '#bf2600', fontSize: 13 }}>
        Position fiscale indisponible : {error}
      </div>
    );
  if (!chaine || !recon)
    return (
      <div style={{ padding: 16, background: '#fff', border: '1px solid #dfe1e6', borderRadius: 8, color: '#5e6c84', fontSize: 13 }}>
        Chargement de la position fiscale…
      </div>
    );

  const r: ResumeFiscal = resumeFiscal(chaine);
  const ecarts = compterEcarts(recon);
  const restant = r.menace ? anneesAvant(r.menace.expire_fin) : null;
  const premierExercice = chaine.years.length ? Math.min(...chaine.years) : null;
  const imposable = cumulImposable(chaine);

  return (
    <div style={{ background: '#fff', border: '1px solid #c1c7d0', borderRadius: 8, overflow: 'hidden' }}>
      {/* en-tête */}
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'baseline', justifyContent: 'space-between', gap: 8, padding: '12px 16px', borderBottom: '1px solid #dfe1e6' }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 700, color: '#172b4d' }}>Position fiscale</div>
          <div style={{ fontSize: 12, color: '#5e6c84', marginTop: 2 }}>
            Tous appartements confondus
            {r.exercice !== null && ` · exercice ${r.exercice}${r.brouillon ? ' (brouillon)' : ''}`}
            {ecarts.annee !== null && ` — dernière liasse déposée : ${ecarts.annee}`}
          </div>
        </div>
        <Link href="/dashboard/position-fiscale" style={{ fontSize: 13, color: '#0052cc', fontWeight: 600, textDecoration: 'none' }}>
          Ouvrir le détail →
        </Link>
      </div>

      {/* les deux tirelires */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 12, padding: '14px 16px' }}>
        <div style={{ background: '#fdf5e9', border: '1px solid #e6d0a8', borderRadius: 6, padding: '12px 14px' }}>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '.08em', textTransform: 'uppercase', color: '#a8620d' }}>
            Tirelire déficit
          </div>
          <div style={{ fontSize: 26, fontWeight: 700, color: '#a8620d', fontVariantNumeric: 'tabular-nums', lineHeight: 1.2 }}>
            {eur(r.deficit)}
          </div>
          <div style={{ fontSize: 12, color: '#5e6c84', marginTop: 2 }}>
            {r.menace
              ? `⏳ ${eur(r.menace.montant)} expirent fin ${r.menace.expire_fin}${restant !== null ? ` — dans ${restant} ans` : ''}`
              : 'aucune échéance connue'}
          </div>
        </div>

        <div style={{ background: '#edf6f5', border: '1px solid #b0d5d2', borderRadius: 6, padding: '12px 14px' }}>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '.08em', textTransform: 'uppercase', color: '#0d6360' }}>
            Tirelire amortissements
          </div>
          <div style={{ fontSize: 26, fontWeight: 700, color: '#0d6360', fontVariantNumeric: 'tabular-nums', lineHeight: 1.2 }}>
            {eur(r.amort)}
          </div>
          <div style={{ fontSize: 12, color: '#5e6c84', marginTop: 2 }}>
            ♾️ n&apos;expire jamais · preuve à la revente
          </div>
        </div>
      </div>

      {/* chiffres clés */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px 32px', padding: '10px 16px', borderTop: '1px solid #dfe1e6', background: '#fafbfc' }}>
        <Stat label="En réserve" value={eur(r.total)} />
        <Stat
          label={premierExercice !== null ? `Résultat imposable depuis ${premierExercice}` : 'Résultat imposable'}
          value={eur(imposable)}
          color={imposable > 0 ? '#bf2600' : '#006644'}
        />
        <Stat
          label={ecarts.annee !== null ? `Écarts liasse ${ecarts.annee}` : 'Écarts liasse'}
          value={String(ecarts.nombre)}
          color={ecarts.nombre > 0 ? '#bf2600' : '#006644'}
        />
      </div>

      {/* raccourcis */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, padding: '10px 16px', borderTop: '1px solid #dfe1e6' }}>
        {RACCOURCIS.map((x) => (
          <Link
            key={x.label}
            href={x.href}
            style={{ fontSize: 12, color: '#0052cc', border: '1px solid #dfe1e6', borderRadius: 4, padding: '3px 10px', background: '#fff', textDecoration: 'none' }}
          >
            {x.label}
          </Link>
        ))}
      </div>

      {/* d'où viennent les deux soldes */}
      <div style={{ padding: '0 16px 16px' }}>
        <ChaineFiscaleTable data={chaine} caption="D'où viennent les deux soldes ci-dessus" />
      </div>
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '.08em', textTransform: 'uppercase', color: '#5e6c84' }}>
        {label}
      </span>
      <span style={{ fontSize: 16, fontWeight: 700, color: color ?? '#172b4d', fontVariantNumeric: 'tabular-nums' }}>
        {value}
      </span>
    </div>
  );
}
