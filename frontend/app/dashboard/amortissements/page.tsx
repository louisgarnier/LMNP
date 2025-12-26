/**
 * Amortizations page
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState } from 'react';
import AmortizationConfigCard from '@/components/AmortizationConfigCard';
import AmortizationTable from '@/components/AmortizationTable';
import { amortizationAPI } from '@/api/client';

export default function AmortissementsPage() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [isCalculating, setIsCalculating] = useState(false);

  const handleConfigUpdated = () => {
    // Force refresh du tableau après mise à jour de la config
    setRefreshKey((prev) => prev + 1);
  };

  const handleCalculate = async () => {
    try {
      setIsCalculating(true);
      const response = await amortizationAPI.recalculate();
      alert(`✅ ${response.message}`);
      // Recharger les données après le calcul
      setRefreshKey((prev) => prev + 1);
    } catch (err: any) {
      console.error('Erreur lors du calcul des amortissements:', err);
      alert(`❌ Erreur lors du calcul: ${err.message || 'Erreur inconnue'}`);
    } finally {
      setIsCalculating(false);
    }
  };

  const handleCellClick = (year: number, category: string) => {
    // TODO: Afficher les transactions détaillées (Step 5.6.1)
    console.log(`Clic sur cellule: année=${year}, catégorie=${category}`);
  };

  return (
    <div style={{ padding: '24px', minHeight: '100vh', backgroundColor: '#f9fafb' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: '700', color: '#111827', marginBottom: '8px' }}>
            Amortissements
          </h1>
          <p style={{ fontSize: '14px', color: '#6b7280' }}>
            Suivi des amortissements par catégorie et année
          </p>
        </div>
        <button
          onClick={handleCalculate}
          disabled={isCalculating}
          style={{
            padding: '10px 20px',
            fontSize: '14px',
            fontWeight: '600',
            color: '#ffffff',
            backgroundColor: isCalculating ? '#9ca3af' : '#3b82f6',
            border: 'none',
            borderRadius: '6px',
            cursor: isCalculating ? 'not-allowed' : 'pointer',
            boxShadow: isCalculating ? 'none' : '0 2px 4px rgba(0, 0, 0, 0.1)',
          }}
          title="Calcule les amortissements pour toutes les transactions correspondant à la configuration"
        >
          {isCalculating ? '⏳ Calcul en cours...' : '🔄 Calculer les amortissements'}
        </button>
      </div>

      {/* Card de configuration */}
      <AmortizationConfigCard onConfigUpdated={handleConfigUpdated} />

      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '8px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
          padding: '24px',
        }}
      >
        <AmortizationTable key={refreshKey} onCellClick={handleCellClick} />
      </div>
    </div>
  );
}

