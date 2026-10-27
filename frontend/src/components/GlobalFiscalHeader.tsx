/**
 * Header des vues fiscales GLOBALES (niveau entité, tous biens confondus).
 *
 * Remplace le Header par-appartement sur les routes globales : pas d'onglets
 * d'appartement (Transactions, Amortissements…), pas de nom de bien actif.
 * Nav entre les 3 vues fiscales + retour accueil.
 */
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

// Les onglets vivent DANS la page (?onglet=N) : la nav du haut n'a qu'une entrée.
const fiscalNav = [
  { name: 'Position fiscale', href: '/dashboard/position-fiscale' },
];

export default function GlobalFiscalHeader() {
  const pathname = usePathname();

  return (
    <header style={{ backgroundColor: '#1e3a5f', color: 'white', height: '48px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: '100%', padding: '0 24px' }}>
        {/* Gauche : logo -> accueil */}
        <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: '8px', textDecoration: 'none', color: 'white' }}>
          <span style={{ fontSize: '14px', fontWeight: 600 }}>LMNP</span>
          <span style={{ fontSize: '12px', opacity: 0.8 }}>· Position fiscale</span>
        </Link>

        {/* Centre : navigation entre les vues fiscales globales */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          {fiscalNav.map((item) => {
            const isActive = pathname?.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                style={{
                  padding: '8px 12px',
                  fontSize: '14px',
                  color: isActive ? 'white' : 'rgba(255, 255, 255, 0.8)',
                  backgroundColor: isActive ? 'rgba(255, 255, 255, 0.15)' : 'transparent',
                  textDecoration: 'none',
                  borderRadius: '4px',
                }}
              >
                {item.name}
              </Link>
            );
          })}
        </nav>

        {/* Droite : retour accueil */}
        <Link href="/" style={{ fontSize: '13px', color: 'rgba(255, 255, 255, 0.85)', textDecoration: 'none' }}>
          ← Accueil
        </Link>
      </div>
    </header>
  );
}
