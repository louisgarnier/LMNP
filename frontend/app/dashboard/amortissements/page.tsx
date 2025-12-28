/**
 * Amortizations page
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect } from 'react';
import AmortizationConfigCard from '@/components/AmortizationConfigCard';
import AmortizationTable from '@/components/AmortizationTable';
import { amortizationAPI } from '@/api/client';

export default function AmortissementsPage() {
  // Récupérer la valeur sauvegardée depuis localStorage
  const getSavedLevel2Value = (): string => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('amortization_level2_value');
      return saved || '';
    }
    return '';
  };

  const [refreshKey, setRefreshKey] = useState(0);
  const [isCalculating, setIsCalculating] = useState(false);
  const [level2Value, setLevel2Value] = useState<string>(getSavedLevel2Value());

  const handleConfigUpdated = () => {
    // Force refresh du tableau après mise à jour de la config
    setRefreshKey((prev) => prev + 1);
  };

  const handleLevel2Change = (value: string) => {
    setLevel2Value(value);
    // Sauvegarder dans localStorage
    if (typeof window !== 'undefined') {
      if (value) {
        localStorage.setItem('amortization_level2_value', value);
      } else {
        localStorage.removeItem('amortization_level2_value');
      }
    }
    // Force refresh du tableau quand le Level 2 change
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
      <AmortizationConfigCard onConfigUpdated={handleConfigUpdated} onLevel2Change={handleLevel2Change} />

      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '8px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
          padding: '24px',
        }}
      >
        <AmortizationTable key={refreshKey} onCellClick={handleCellClick} level2Value={level2Value} />
      </div>
    </div>
  );
}

