/**
 * AmortizationTable component - Tableau croisé des amortissements
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect } from 'react';
import { amortizationAPI, AmortizationAggregatedResponse } from '@/api/client';

interface AmortizationTableProps {
  onCellClick?: (year: number, category: string) => void;
  refreshKey?: number; // Pour forcer le rechargement
  level2Value?: string; // Level 2 sélectionné
}

export default function AmortizationTable({ onCellClick, refreshKey, level2Value }: AmortizationTableProps) {
  const [data, setData] = useState<AmortizationAggregatedResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [refreshKey, level2Value]); // Recharger quand refreshKey ou level2Value change

  const loadData = async () => {
    // Si aucun Level 2 n'est sélectionné, ne pas charger les données
    if (!level2Value) {
      setData(null);
      setLoading(false);
      setError(null);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await amortizationAPI.getResultsAggregated();
      setData(response);
    } catch (err: any) {
      console.error('Erreur lors du chargement des amortissements:', err);
      setError(err.message || 'Erreur lors du chargement des amortissements');
    } finally {
      setLoading(false);
    }
  };

  const formatAmount = (amount: number): string => {
    return amount.toFixed(2);
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
        ⏳ Chargement des amortissements...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ color: '#dc2626', marginBottom: '8px' }}>❌ Erreur</div>
        <div style={{ color: '#6b7280', fontSize: '14px' }}>{error}</div>
        <button
          onClick={loadData}
          style={{
            marginTop: '16px',
            padding: '8px 16px',
            backgroundColor: '#3b82f6',
            color: '#ffffff',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          Réessayer
        </button>
      </div>
    );
  }

  if (!data || data.categories.length === 0 || data.years.length === 0) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
        <div style={{ marginBottom: '8px', fontSize: '16px', fontWeight: '600' }}>ℹ️ Aucun résultat d'amortissement</div>
        <div style={{ fontSize: '14px', marginBottom: '16px' }}>
          Configurez les amortissements dans le panneau de configuration (bouton CONFIG à droite),<br />
          puis cliquez sur "🔄 Calculer les amortissements" en haut à droite pour générer les résultats.
        </div>
      </div>
    );
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table
        style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '13px',
        }}
      >
        <thead>
          <tr>
            <th
              style={{
                padding: '12px',
                textAlign: 'left',
                backgroundColor: '#f3f4f6',
                border: '1px solid #e5e7eb',
                fontWeight: '600',
                color: '#111827',
              }}
            >
              Catégorie
            </th>
            {data.years.map((year) => (
              <th
                key={year}
                style={{
                  padding: '12px',
                  textAlign: 'right',
                  backgroundColor: '#f3f4f6',
                  border: '1px solid #e5e7eb',
                  fontWeight: '600',
                  color: '#111827',
                }}
              >
                {year}
              </th>
            ))}
            <th
              style={{
                padding: '12px',
                textAlign: 'right',
                backgroundColor: '#e5e7eb',
                border: '1px solid #d1d5db',
                fontWeight: '700',
                color: '#111827',
              }}
            >
              Total
            </th>
          </tr>
        </thead>
        <tbody>
          {data.categories.map((category, rowIndex) => (
            <tr key={category}>
              <td
                style={{
                  padding: '12px',
                  backgroundColor: '#ffffff',
                  border: '1px solid #e5e7eb',
                  fontWeight: '600',
                  color: '#111827',
                }}
              >
                {category.charAt(0).toUpperCase() + category.slice(1)}
              </td>
              {data.years.map((year, colIndex) => {
                const amount = data.data[rowIndex][colIndex];
                const isNegative = amount < 0;
                return (
                  <td
                    key={year}
                    onClick={() => onCellClick && onCellClick(year, category)}
                    style={{
                      padding: '12px',
                      textAlign: 'right',
                      backgroundColor: '#ffffff',
                      border: '1px solid #e5e7eb',
                      color: isNegative ? '#dc2626' : '#111827',
                      cursor: onCellClick ? 'pointer' : 'default',
                    }}
                    title={onCellClick ? `Cliquer pour voir les détails` : undefined}
                  >
                    {formatAmount(amount)}
                  </td>
                );
              })}
              <td
                style={{
                  padding: '12px',
                  textAlign: 'right',
                  backgroundColor: '#f9fafb',
                  border: '1px solid #e5e7eb',
                  fontWeight: '600',
                  color: data.row_totals[rowIndex] < 0 ? '#dc2626' : '#111827',
                }}
              >
                {formatAmount(data.row_totals[rowIndex])}
              </td>
            </tr>
          ))}
          {/* Ligne Total */}
          <tr>
            <td
              style={{
                padding: '12px',
                backgroundColor: '#e5e7eb',
                border: '1px solid #d1d5db',
                fontWeight: '700',
                color: '#111827',
              }}
            >
              Total
            </td>
            {data.years.map((year, colIndex) => {
              const amount = data.column_totals[colIndex];
              return (
                <td
                  key={year}
                  style={{
                    padding: '12px',
                    textAlign: 'right',
                    backgroundColor: '#e5e7eb',
                    border: '1px solid #d1d5db',
                    fontWeight: '700',
                    color: amount < 0 ? '#dc2626' : '#111827',
                  }}
                >
                  {formatAmount(amount)}
                </td>
              );
            })}
            <td
              style={{
                padding: '12px',
                textAlign: 'right',
                backgroundColor: '#d1d5db',
                border: '1px solid #9ca3af',
                fontWeight: '700',
                color: data.grand_total < 0 ? '#dc2626' : '#111827',
              }}
            >
              {formatAmount(data.grand_total)}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

