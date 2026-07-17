/**
 * Simple Dashboard layout
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Header from '@/components/Header';
import Navigation from '@/components/Navigation';
import { ImportLogProvider } from '@/contexts/ImportLogContext';
import { useProperty } from '@/contexts/PropertyContext';

// Pages GLOBALES (niveau entité, tous biens confondus) : elles ne dépendent
// d'aucun appartement actif et ne doivent donc PAS être redirigées vers l'accueil
// quand aucun bien n'est sélectionné.
const GLOBAL_ROUTES = ['/dashboard/liasse-fiscale'];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { activeProperty, loading, isRestoring } = useProperty();
  const isGlobalRoute = GLOBAL_ROUTES.some((r) => pathname?.startsWith(r));

  // Redirect to home if no property is selected — sauf sur une page globale.
  useEffect(() => {
    if (!loading && !isRestoring && !activeProperty && !isGlobalRoute) {
      console.log('[DashboardLayout] Aucune propriété active, redirection vers page d\'accueil');
      router.push('/');
    }
  }, [activeProperty, loading, isRestoring, router, isGlobalRoute]);

  // Show loading while checking property
  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f9fafb' }}>
        <div style={{ textAlign: 'center' }}>
          <p style={{ color: '#6b7280' }}>Chargement...</p>
        </div>
      </div>
    );
  }

  // Don't render if no property (will redirect) — sauf page globale.
  if (!activeProperty && !isGlobalRoute) {
    return null;
  }

  return (
    <ImportLogProvider>
      <div style={{ minHeight: '100vh', backgroundColor: '#f9fafb' }}>
        <Header />
        <Navigation />
        <main>
          {children}
        </main>
      </div>
    </ImportLogProvider>
  );
}
