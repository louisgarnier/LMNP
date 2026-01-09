/**
 * AmortizationConfigCard - Card de configuration des amortissements
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 * 
 * Steps implémentés:
 * - Step 6.6.2: Structure de base de la card
 * - Step 6.6.3: Champ Level 2 avec localStorage
 * - Step 6.6.4: Tableau (structure vide)
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { transactionsAPI } from '@/api/client';

interface AmortizationConfigCardProps {
  onConfigUpdated?: () => void;
  onLevel2Change?: (level2Value: string) => void;
  onLevel2ValuesLoaded?: (count: number) => void;
}

const STORAGE_KEY_LEVEL2 = 'amortization_config_level2';

export default function AmortizationConfigCard({
  onConfigUpdated,
  onLevel2Change,
  onLevel2ValuesLoaded,
}: AmortizationConfigCardProps) {
  const [selectedLevel2Values, setSelectedLevel2Values] = useState<string[]>([]);
  const [level2Values, setLevel2Values] = useState<string[]>([]);
  const [loadingValues, setLoadingValues] = useState<boolean>(false);
  const [level2ValuesLoaded, setLevel2ValuesLoaded] = useState<boolean>(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState<boolean>(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Charger les valeurs Level 2 depuis l'API
  const loadLevel2Values = async () => {
    try {
      setLoadingValues(true);
      const response = await transactionsAPI.getUniqueValues('level_2');
      const values = response.values || [];
      setLevel2Values(values);
      setLevel2ValuesLoaded(true);
      
      // Notifier le parent du nombre de valeurs disponibles
      if (onLevel2ValuesLoaded) {
        onLevel2ValuesLoaded(values.length);
      }
      
      // Restaurer les valeurs depuis localStorage si disponibles
      const savedLevel2 = localStorage.getItem(STORAGE_KEY_LEVEL2);
      if (savedLevel2) {
        try {
          const savedValues: string[] = JSON.parse(savedLevel2);
          const validValues = savedValues.filter(v => values.includes(v));
          if (validValues.length > 0) {
            setSelectedLevel2Values(validValues);
            // Notifier le parent avec la première valeur (pour compatibilité)
            if (onLevel2Change) {
              onLevel2Change(validValues[0] || '');
            }
          }
        } catch (e) {
          // Si ce n'est pas du JSON, essayer comme string simple (ancien format)
          if (values.includes(savedLevel2)) {
            setSelectedLevel2Values([savedLevel2]);
            if (onLevel2Change) {
              onLevel2Change(savedLevel2);
            }
          }
        }
      }
    } catch (err: any) {
      console.error('Erreur lors du chargement des valeurs level_2:', err);
      setLevel2ValuesLoaded(true);
      if (onLevel2ValuesLoaded) {
        onLevel2ValuesLoaded(0);
      }
    } finally {
      setLoadingValues(false);
    }
  };

  // Charger les valeurs au montage
  useEffect(() => {
    loadLevel2Values();
  }, []);

  // Fermer le dropdown si on clique en dehors
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };

    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isDropdownOpen]);

  // Gérer le changement d'une checkbox Level 2
  const handleLevel2CheckboxChange = (value: string, checked: boolean) => {
    let newSelectedValues: string[];
    
    if (checked) {
      // Ajouter la valeur si elle n'est pas déjà sélectionnée
      newSelectedValues = [...selectedLevel2Values, value];
    } else {
      // Retirer la valeur
      newSelectedValues = selectedLevel2Values.filter(v => v !== value);
    }
    
    setSelectedLevel2Values(newSelectedValues);
    
    // Sauvegarder dans localStorage
    if (newSelectedValues.length > 0) {
      localStorage.setItem(STORAGE_KEY_LEVEL2, JSON.stringify(newSelectedValues));
    } else {
      localStorage.removeItem(STORAGE_KEY_LEVEL2);
    }
    
    // Notifier le parent avec la première valeur (pour compatibilité avec l'ancien code)
    if (onLevel2Change) {
      onLevel2Change(newSelectedValues.length > 0 ? newSelectedValues[0] : '');
    }
    
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
      
      {/* Champ Level 2 - Dropdown avec checkboxes */}
      <div style={{ marginBottom: '24px' }}>
        <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '8px' }}>
          Level 2 (Valeur à considérer comme amortissement)
        </label>
        {loadingValues ? (
          <div style={{ color: '#6b7280', fontSize: '14px' }}>Chargement...</div>
        ) : level2Values.length === 0 ? (
          <div style={{ color: '#6b7280', fontSize: '14px' }}>Aucune valeur disponible</div>
        ) : (
          <div ref={dropdownRef} style={{ position: 'relative', maxWidth: '400px' }}>
            {/* Bouton du dropdown */}
            <button
              type="button"
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              style={{
                width: '100%',
                padding: '8px 12px',
                fontSize: '14px',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                backgroundColor: '#ffffff',
                color: '#111827',
                cursor: 'pointer',
                textAlign: 'left',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {selectedLevel2Values.length === 0
                  ? '-- Sélectionner une valeur --'
                  : selectedLevel2Values.length === 1
                  ? selectedLevel2Values[0]
                  : `${selectedLevel2Values.length} valeur(s) sélectionnée(s)`}
              </span>
              <span style={{ marginLeft: '8px', fontSize: '12px', color: '#6b7280' }}>
                {isDropdownOpen ? '▲' : '▼'}
              </span>
            </button>

            {/* Menu déroulant avec checkboxes */}
            {isDropdownOpen && (
              <div
                style={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  right: 0,
                  marginTop: '4px',
                  backgroundColor: '#ffffff',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                  zIndex: 1000,
                  maxHeight: '200px',
                  overflowY: 'auto',
                }}
              >
                {level2Values.map((value) => (
                  <label
                    key={value}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      cursor: 'pointer',
                      fontSize: '14px',
                      color: '#111827',
                      padding: '8px 12px',
                      borderBottom: '1px solid #f3f4f6',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = '#f9fafb';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = '#ffffff';
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={selectedLevel2Values.includes(value)}
                      onChange={(e) => handleLevel2CheckboxChange(value, e.target.checked)}
                      style={{
                        width: '16px',
                        height: '16px',
                        cursor: 'pointer',
                      }}
                    />
                    <span>{value}</span>
                  </label>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Tableau (structure vide) - Step 6.6.4 */}
      {selectedLevel2Values.length > 0 && (
        <div style={{ overflowX: 'auto' }}>
          <table
            style={{
              width: '100%',
              borderCollapse: 'collapse',
              fontSize: '14px',
            }}
          >
            <thead>
              <tr style={{ backgroundColor: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
                <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>
                  Type d'immobilisation
                </th>
                <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>
                  Level 1 (valeurs)
                </th>
                <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>
                  Nombre de transactions
                </th>
                <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>
                  Date de début
                </th>
                <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>
                  Montant
                </th>
                <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>
                  Durée
                </th>
                <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>
                  Annuité
                </th>
                <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>
                  Cumulé
                </th>
                <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>
                  VNC
                </th>
              </tr>
            </thead>
            <tbody>
              {/* Pas de données pour l'instant - Step 6.6.4 */}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

