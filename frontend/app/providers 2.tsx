/**
 * Client-side providers
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { PropertyProvider } from '@/contexts/PropertyContext';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <PropertyProvider>
      {children}
    </PropertyProvider>
  );
}
