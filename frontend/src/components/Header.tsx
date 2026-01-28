/**
 * Simple Header component
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useProperty } from '@/contexts/PropertyContext';

const navItems = [
  { name: 'Vue d\'ensemble', href: '/dashboard' },
  { name: 'Transactions', href: '/dashboard/transactions' },
  { name: 'Tableau croisé dynamique', href: '/dashboard/pivot' },
  { name: 'États financiers', href: '/dashboard/etats-financiers' },
  { name: 'Amortissements', href: '/dashboard/amortissements' },
  { name: 'Cashflow', href: '/dashboard/cashflow' },
];

export default function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const { activeProperty, setActiveProperty } = useProperty();

  const handleChangeProperty = () => {
    setActiveProperty(null);
    router.push('/');
  };

  return (
    <header style={{ backgroundColor: '#1e3a5f', color: 'white', height: '48px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: '100%', padding: '0 24px' }}>
        {/* Left: Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '14px', fontWeight: '600' }}>LMNP</span>
          <span style={{ fontSize: '12px', opacity: 0.8 }}>Gestion Comptable</span>
        </div>

        {/* Center: Navigation */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          {navItems.map((item) => {
            const isActive = pathname === item.href || 
              (item.href !== '/dashboard' && pathname?.startsWith(item.href));
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

        {/* Right: Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {activeProperty && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '4px 12px', backgroundColor: 'rgba(255, 255, 255, 0.1)', borderRadius: '4px' }}>
              <span style={{ fontSize: '12px', fontWeight: '500' }}>{activeProperty.name}</span>
              <button
                onClick={handleChangeProperty}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'rgba(255, 255, 255, 0.8)',
                  cursor: 'pointer',
                  padding: '2px 4px',
                  fontSize: '11px',
                  textDecoration: 'underline',
                }}
                title="Changer de propriété"
              >
                Changer
              </button>
            </div>
          )}
          <button style={{ background: 'none', border: 'none', color: 'rgba(255, 255, 255, 0.8)', cursor: 'pointer', padding: '4px' }}>
            🔍
          </button>
          <button style={{ background: 'none', border: 'none', color: 'rgba(255, 255, 255, 0.8)', cursor: 'pointer', padding: '4px' }}>
            🔔
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '4px 8px', backgroundColor: 'rgba(255, 255, 255, 0.1)', borderRadius: '4px', cursor: 'pointer' }}>
            <span style={{ fontSize: '12px' }}>Régime réel</span>
            <span>▼</span>
          </div>
        </div>
      </div>
    </header>
  );
}
