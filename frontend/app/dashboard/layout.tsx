/**
 * Simple Dashboard layout
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import Header from '@/components/Header';
import Navigation from '@/components/Navigation';
import { ImportLogProvider } from '@/contexts/ImportLogContext';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
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
