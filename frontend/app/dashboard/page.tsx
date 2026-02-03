/**
 * Dashboard page - redirect to transactions
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function DashboardPage() {
  const router = useRouter();

  useEffect(() => {
    // Rediriger automatiquement vers la page Transactions
    router.replace('/dashboard/transactions');
  }, [router]);

  return (
    <div style={{ padding: '24px', textAlign: 'center' }}>
      <p style={{ color: '#6b7280' }}>Redirection...</p>
    </div>
  );
}
