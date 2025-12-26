/**
 * AmortizationConfigCard component - Card de configuration des amortissements
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect } from 'react';
import { transactionsAPI } from '@/api/client';

interface AmortizationConfigCardProps {
  onConfigUpdated?: () => void;
}

export default function AmortizationConfigCard({ onConfigUpdated }: AmortizationConfigCardProps) {
  const [level2Value, setLevel2Value] = useState<string>('');
  const [level2Values, setLevel2Values] = useState<string[]>([]);
  const [loadingValues, setLoadingValues] = useState(false);

  // Charger les valeurs uniques de level_2 au montage
  useEffect(() => {
    loadLevel2Values();
  }, []);

  const loadLevel2Values = async () => {
    try {
      setLoadingValues(true);
      const response = await transactionsAPI.getUniqueValues('level_2');
      setLevel2Values(response.values || []);
      
      // Si une valeur existe déjà, la sélectionner par défaut
      if (response.values && response.values.length > 0 && !level2Value) {
        // Chercher "ammortissements" en priorité, sinon prendre la première
        const defaultValue = response.values.find(v => v === 'ammortissements') || response.values[0];
        setLevel2Value(defaultValue);
      }
    } catch (err: any) {
      console.error('Erreur lors du chargement des valeurs level_2:', err);
    } finally {
      setLoadingValues(false);
    }
  };

  const handleLevel2Change = (value: string) => {
    setLevel2Value(value);
    // Sauvegarde automatique : on mettra à jour tous les types d'amortissement plus tard
    // Pour l'instant, on garde juste l'état local
    if (onConfigUpdated) {
      onConfigUpdated();
    }
  };

  return (
    <div
      style={{
        backgroundColor: '#ffffff',
        borderRadius: '8px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        padding: '24px',
        marginBottom: '24px',
      }}
    >
      <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#111827', marginBottom: '16px' }}>
        Configuration des amortissements
      </h2>
      
      {/* Champ Level 2 */}
      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '8px' }}>
          Level 2 (Valeur à considérer comme amortissement)
        </label>
        <select
          value={level2Value}
          onChange={(e) => handleLevel2Change(e.target.value)}
          disabled={loadingValues}
          style={{
            width: '100%',
            maxWidth: '400px',
            padding: '8px 12px',
            fontSize: '14px',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            backgroundColor: loadingValues ? '#f3f4f6' : '#ffffff',
            color: '#111827',
            cursor: loadingValues ? 'not-allowed' : 'pointer',
          }}
        >
          {loadingValues ? (
            <option>Chargement...</option>
          ) : level2Values.length === 0 ? (
            <option value="">Aucune valeur disponible</option>
          ) : (
            <>
              <option value="">-- Sélectionner une valeur --</option>
              {level2Values.map((value) => (
                <option key={value} value={value}>
                  {value || '(vide)'}
                </option>
              ))}
            </>
          )}
        </select>
      </div>
    </div>
  );
}

