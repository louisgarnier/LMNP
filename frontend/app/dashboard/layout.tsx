/**
 * Simple Dashboard layout
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Header from '@/components/Header';
import Navigation from '@/components/Navigation';
import { ImportLogProvider } from '@/contexts/ImportLogContext';
import { useProperty } from '@/contexts/PropertyContext';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { activeProperty, loading, isRestoring } = useProperty();

  // Redirect to home if no property is selected
  // IMPORTANT: Wait for loading to complete AND check if property was restored from localStorage
  // Don't redirect if we're still restoring from localStorage
  useEffect(() => {
    // Only redirect if:
    // 1. Loading is complete (not loading)
    // 2. Not currently restoring from localStorage
    // 3. No property is active
    if (!loading && !isRestoring && !activeProperty) {
      console.log('[DashboardLayout] Aucune propriété active, redirection vers page d\'accueil');
      router.push('/');
    }
  }, [activeProperty, loading, isRestoring, router]);

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

  // Don't render if no property (will redirect)
  if (!activeProperty) {
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
