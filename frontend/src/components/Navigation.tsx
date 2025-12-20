/**
 * Simple Navigation component - only for transactions page
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import Link from 'next/link';
import { usePathname, useSearchParams } from 'next/navigation';

const tabs = [
  { name: 'Toutes les transactions', href: '/dashboard/transactions' },
  { name: 'Non classées', href: '/dashboard/transactions?filter=unclassified' },
  { name: 'À valider', href: '/dashboard/transactions?filter=to_validate' },
  { name: 'Load Trades/Mappings', href: '/dashboard/transactions?tab=load_trades' },
  { name: 'Mapping', href: '/dashboard/transactions?tab=mapping' },
];

export default function Navigation() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const isTransactionsPage = pathname?.startsWith('/dashboard/transactions');

  if (!isTransactionsPage) {
    return null;
  }

  const filter = searchParams?.get('filter');
  const tabParam = searchParams?.get('tab');

  return (
    <nav style={{ backgroundColor: 'white', borderBottom: '1px solid #e5e7eb' }}>
      <div style={{ padding: '0 24px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          {tabs.map((tab) => {
            // Déterminer si l'onglet est actif
            let isActive = false;
            if (tab.href === '/dashboard/transactions' && !filter && !tabParam) {
              isActive = true; // "Toutes les transactions" par défaut
            } else if (tab.href.includes('filter=unclassified') && filter === 'unclassified') {
              isActive = true;
            } else if (tab.href.includes('filter=to_validate') && filter === 'to_validate') {
              isActive = true;
            } else if (tab.href.includes('tab=load_trades') && tabParam === 'load_trades') {
              isActive = true;
            } else if (tab.href.includes('tab=mapping') && tabParam === 'mapping') {
              isActive = true;
            }
            
            return (
              <Link
                key={tab.href}
                href={tab.href}
                style={{
                  padding: '12px 16px',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: isActive ? '#1e3a5f' : '#6b7280',
                  borderBottom: isActive ? '2px solid #1e3a5f' : '2px solid transparent',
                  textDecoration: 'none',
                  transition: 'all 0.2s',
                }}
              >
                {tab.name}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
