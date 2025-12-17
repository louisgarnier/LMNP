/**
 * Simple Navigation component - only for transactions page
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const tabs = [
  { name: 'Toutes les transactions', href: '/dashboard/transactions' },
  { name: 'Non classées', href: '/dashboard/transactions?filter=unexplained' },
  { name: 'À valider', href: '/dashboard/transactions?filter=approval' },
];

export default function Navigation() {
  const pathname = usePathname();
  const isTransactionsPage = pathname?.startsWith('/dashboard/transactions');

  if (!isTransactionsPage) {
    return null;
  }

  return (
    <nav style={{ backgroundColor: 'white', borderBottom: '1px solid #e5e7eb' }}>
      <div style={{ padding: '0 24px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          {tabs.map((tab) => {
            const isActive = pathname === tab.href || 
              (tab.href === '/dashboard/transactions' && pathname === '/dashboard/transactions' && !pathname.includes('filter'));
            return (
              <Link
                key={tab.href}
                href={tab.href}
                style={{
                  padding: '12px 16px',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: isActive ? '#111827' : '#6b7280',
                  borderBottom: isActive ? '2px solid #2563eb' : '2px solid transparent',
                  textDecoration: 'none',
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
