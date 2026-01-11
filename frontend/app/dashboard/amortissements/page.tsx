/**
 * Amortizations page - Tableau croisé des amortissements
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import AmortizationConfigCard from '@/components/AmortizationConfigCard';
import AmortizationTable from '@/components/AmortizationTable';

export default function AmortissementsPage() {
  const [level2Value, setLevel2Value] = useState<string>('');
  const [level2ValuesCount, setLevel2ValuesCount] = useState<number>(0);
  const [refreshKey, setRefreshKey] = useState(0);
  const refreshConfigCardRef = useRef<(() => Promise<void>) | null>(null);

  const handleConfigUpdated = () => {
    // Forcer le rechargement du tableau
    setRefreshKey(prev => prev + 1);
  };

  const handleLevel2Change = (newLevel2Value: string) => {
    setLevel2Value(newLevel2Value);
    // Recharger le tableau quand le Level 2 change
    setRefreshKey(prev => prev + 1);
  };

  const handleLevel2ValuesLoaded = (count: number) => {
    setLevel2ValuesCount(count);
  };

  // Exposer la fonction refreshAll depuis AmortizationConfigCard
  const handleRefreshRequested = (refreshFn: () => Promise<void>) => {
    refreshConfigCardRef.current = refreshFn;
  };

  // Écouter l'événement transactionCreated pour rafraîchir automatiquement les cards
  useEffect(() => {
    const handleTransactionCreated = async (event: Event) => {
      const customEvent = event as CustomEvent;
      console.log('📢 [AmortissementsPage] Événement transactionCreated reçu:', customEvent.detail);
      
      // Rafraîchir la card de configuration
      if (refreshConfigCardRef.current) {
        try {
          await refreshConfigCardRef.current();
          console.log('✅ [AmortissementsPage] Card config rafraîchie');
        } catch (err) {
          console.error('❌ [AmortissementsPage] Erreur lors du rafraîchissement de la card config:', err);
        }
      }
      
      // Rafraîchir le tableau
      setRefreshKey(prev => prev + 1);
      console.log('✅ [AmortissementsPage] Tableau rafraîchi');
    };

    window.addEventListener('transactionCreated', handleTransactionCreated);
    
    return () => {
      window.removeEventListener('transactionCreated', handleTransactionCreated);
    };
  }, []);

  return (
    <div style={{ padding: '24px' }}>
    <div className="space-y-6">
        {/* Card de configuration */}
        <AmortizationConfigCard
          onConfigUpdated={handleConfigUpdated}
          onLevel2Change={handleLevel2Change}
          onLevel2ValuesLoaded={handleLevel2ValuesLoaded}
          onRefreshRequested={handleRefreshRequested}
        />

        {/* Tableau croisé - Masqué si aucune valeur Level 2 disponible */}
        {level2ValuesCount > 0 && (
          <AmortizationTable
            onCellClick={(year, category) => {
              console.log('Cell clicked:', year, category);
              // TODO: Implémenter le drill-down dans Step 6.6.1
            }}
            refreshKey={refreshKey}
            level2Value={level2Value}
          />
        )}
      </div>
    </div>
  );
}

