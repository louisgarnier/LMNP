/**
 * Position fiscale — vision globale (Maquette 1).
 *
 * Page fine : navigation + titre + intro, le tableau lui-même vit dans
 * le composant partagé VisionGlobaleTable (aussi embarqué sur la home).
 * Détail par appartement (Maquette 2) : /liasse-fiscale/detail.
 */
'use client';

import Link from 'next/link';
import VisionGlobaleTable from '@/components/VisionGlobaleTable';

export default function LiasseFiscalePage() {
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

      <VisionGlobaleTable />
    </div>
  );
}
