/**
 * AmortizationConfigPanel component - Panneau de configuration latéral pour les amortissements
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useRef, useEffect } from 'react';
import { amortizationAPI, transactionsAPI, mappingsAPI, AmortizationConfig } from '@/api/client';

interface AmortizationConfigPanelProps {
  onConfigUpdated?: () => void;
}

export default function AmortizationConfigPanel({ onConfigUpdated }: AmortizationConfigPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isHovering, setIsHovering] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLDivElement>(null);
  
  const [config, setConfig] = useState<AmortizationConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [level2Values, setLevel2Values] = useState<string[]>([]);
  const [level1Values, setLevel1Values] = useState<string[]>([]);
  const [loadingValues, setLoadingValues] = useState(false);

  // Charger la configuration au montage
  useEffect(() => {
    loadConfig();
    loadUniqueValues();
  }, []);

  // Nettoyer les valeurs invalides quand level1Values change
  useEffect(() => {
    if (!config || level1Values.length === 0 || !config.level_3_mapping) return;
    
    let hasInvalidValues = false;
    const cleanedMapping: typeof config.level_3_mapping = {
      part_terrain: [],
      structure_go: [],
      mobilier: [],
      igt: [],
      agencements: [],
      facade_toiture: [],
      travaux: [],
    };
    
    const categories = ['part_terrain', 'structure_go', 'mobilier', 'igt', 'agencements', 'facade_toiture', 'travaux'] as const;
    
    for (const category of categories) {
      // S'assurer que la catégorie existe dans le mapping
      const categoryValues = config.level_3_mapping[category] || [];
      const validValues = categoryValues.filter(v => level1Values.includes(v));
      const invalidValues = categoryValues.filter(v => !level1Values.includes(v));
      
      if (invalidValues.length > 0) {
        hasInvalidValues = true;
      }
      
      cleanedMapping[category] = validValues;
    }
    
    if (hasInvalidValues) {
      setConfig((prevConfig) => {
        if (!prevConfig) return prevConfig;
        // Vérifier si quelque chose a vraiment changé
        const hasChanges = categories.some(
          cat => (prevConfig.level_3_mapping[cat]?.length || 0) !== cleanedMapping[cat].length
        );
        if (hasChanges) {
          return { ...prevConfig, level_3_mapping: cleanedMapping };
        }
        return prevConfig;
      });
    }
  }, [level1Values]); // Ne pas inclure config dans les dépendances pour éviter la boucle

  const loadConfig = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await amortizationAPI.getConfig();
      setConfig(response);
    } catch (err: any) {
      console.error('Erreur lors du chargement de la configuration:', err);
      setError('Erreur lors du chargement de la configuration');
      // Créer une config par défaut si elle n'existe pas
      setConfig({
        level_2_value: 'ammortissements',
        level_3_mapping: {
          part_terrain: [],
          structure_go: [],
          mobilier: [],
          igt: [],
          agencements: [],
          facade_toiture: [],
          travaux: [],
        },
        duration_part_terrain: 0,
        duration_structure_go: 0,
        duration_mobilier: 0,
        duration_igt: 0,
        duration_agencements: 0,
        duration_facade_toiture: 0,
        duration_travaux: 0,
      });
    } finally {
      setLoading(false);
    }
  };

  const loadUniqueValues = async () => {
    try {
      setLoadingValues(true);
      const [level2Res, level1Res] = await Promise.all([
        transactionsAPI.getUniqueValues('level_2'),
        transactionsAPI.getUniqueValues('level_1'),
      ]);
      setLevel2Values(level2Res.values || []);
      setLevel1Values(level1Res.values || []);
    } catch (err: any) {
      console.error('Erreur lors du chargement des valeurs uniques:', err);
    } finally {
      setLoadingValues(false);
    }
  };

  const handleSave = async () => {
    if (!config) return;
    
    try {
      setSaving(true);
      setError(null);
      await amortizationAPI.updateConfig(config);
      if (onConfigUpdated) {
        onConfigUpdated();
      }
      alert('✅ Configuration sauvegardée avec succès !');
    } catch (err: any) {
      console.error('Erreur lors de la sauvegarde:', err);
      setError(err.message || 'Erreur lors de la sauvegarde');
      alert(`❌ Erreur lors de la sauvegarde: ${err.message || 'Erreur inconnue'}`);
    } finally {
      setSaving(false);
    }
  };

  const handleLevel2Change = (value: string) => {
    if (!config) return;
    setConfig({ ...config, level_2_value: value });
  };

  const handleLevel3MappingChange = (
    category: 'part_terrain' | 'structure_go' | 'mobilier' | 'igt' | 'agencements' | 'facade_toiture' | 'travaux',
    values: string[]
  ) => {
    if (!config) return;
    setConfig({
      ...config,
      level_3_mapping: {
        ...config.level_3_mapping,
        [category]: values,
      },
    });
  };

  const handleDurationChange = (
    category: 'part_terrain' | 'structure_go' | 'mobilier' | 'igt' | 'agencements' | 'facade_toiture' | 'travaux',
    value: number
  ) => {
    if (!config) return;
    setConfig({
      ...config,
      [`duration_${category}`]: value,
    });
  };

  // Fermer le panneau si on clique en dehors
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        panelRef.current &&
        !panelRef.current.contains(event.target as Node) &&
        triggerRef.current &&
        !triggerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
        setIsHovering(false);
      }
    };

    if (isOpen || isHovering) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [isOpen, isHovering]);

  if (loading) {
    return null; // Ne rien afficher pendant le chargement initial
  }

  if (!config) {
    return null;
  }

  return (
    <>
      {/* Trigger bar */}
      <div
        ref={triggerRef}
        onMouseEnter={() => setIsHovering(true)}
        onMouseLeave={() => {
          if (!isOpen) {
            setIsHovering(false);
          }
        }}
        onClick={() => setIsOpen(!isOpen)}
        style={{
          position: 'fixed',
          right: 0,
          top: '50%',
          transform: 'translateY(-50%)',
          width: '24px',
          height: '100px',
          backgroundColor: isHovering || isOpen ? '#3b82f6' : '#9ca3af',
          cursor: 'pointer',
          zIndex: 998,
          transition: 'all 0.2s',
          borderTopLeftRadius: '6px',
          borderBottomLeftRadius: '6px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: isHovering || isOpen ? '0 2px 8px rgba(0, 0, 0, 0.15)' : '0 1px 3px rgba(0, 0, 0, 0.1)',
        }}
        title="Configuration des amortissements"
      >
        <span
          style={{
            writingMode: 'vertical-rl',
            textOrientation: 'mixed',
            fontSize: '11px',
            fontWeight: '600',
            color: '#ffffff',
            letterSpacing: '1px',
          }}
        >
          CONFIG
        </span>
      </div>

      {/* Panneau latéral */}
      {(isOpen || isHovering) && (
        <div
          ref={panelRef}
          onMouseEnter={() => setIsHovering(true)}
          onMouseLeave={() => {
            if (!isOpen) {
              setIsHovering(false);
            }
          }}
          style={{
            position: 'fixed',
            right: 0,
            top: 0,
            bottom: 0,
            width: '400px',
            backgroundColor: '#ffffff',
            boxShadow: '-2px 0 8px rgba(0, 0, 0, 0.1)',
            zIndex: 999,
            overflowY: 'auto',
            padding: '16px',
            paddingRight: '24px',
          }}
        >
          <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#111827', margin: 0 }}>
              Configuration Amortissements
            </h3>
            <button
              onClick={() => {
                setIsOpen(false);
                setIsHovering(false);
              }}
              style={{
                padding: '4px 8px',
                fontSize: '12px',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                backgroundColor: '#f9fafb',
                cursor: 'pointer',
                color: '#6b7280',
              }}
            >
              ✕
            </button>
          </div>

          {error && (
            <div style={{ 
              padding: '8px', 
              marginBottom: '16px', 
              backgroundColor: '#fee2e2', 
              color: '#dc2626', 
              borderRadius: '4px',
              fontSize: '12px'
            }}>
              {error}
            </div>
          )}

          {/* Level 2 Selection */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#374151', marginBottom: '6px' }}>
              Level 2 (Valeur à considérer comme amortissement)
            </label>
            <select
              value={config.level_2_value}
              onChange={(e) => handleLevel2Change(e.target.value)}
              disabled={loadingValues}
              style={{
                width: '100%',
                padding: '6px',
                fontSize: '12px',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                backgroundColor: loadingValues ? '#f3f4f6' : '#ffffff',
              }}
            >
              {loadingValues ? (
                <option>Chargement...</option>
              ) : (
                level2Values.map((value) => (
                  <option key={value} value={value}>
                    {value || '(vide)'}
                  </option>
                ))
              )}
            </select>
          </div>

          {/* Level 1 Mappings */}
          {(() => {
            const categories = [
              { key: 'part_terrain', label: 'Part terrain' },
              { key: 'structure_go', label: 'Immobilisation structure/GO' },
              { key: 'mobilier', label: 'Immobilisation mobilier' },
              { key: 'igt', label: 'Immobilisation IGT' },
              { key: 'agencements', label: 'Immobilisation agencements' },
              { key: 'facade_toiture', label: 'Immobilisation Facade/Toiture' },
              { key: 'travaux', label: 'Immobilisation travaux' },
            ] as const;
            
            return categories.map(({ key, label }) => {
              const category = key;
              // S'assurer que la catégorie existe dans le mapping
              const categoryValues = config.level_3_mapping[category] || [];
              const validValues = categoryValues.filter(v => level1Values.includes(v));
              const duration = 
                category === 'part_terrain' ? config.duration_part_terrain :
                category === 'structure_go' ? config.duration_structure_go :
                category === 'mobilier' ? config.duration_mobilier :
                category === 'igt' ? config.duration_igt :
                category === 'agencements' ? config.duration_agencements :
                category === 'facade_toiture' ? config.duration_facade_toiture :
                config.duration_travaux;
              const hasValues = categoryValues.length > 0;
              
              return (
                <div key={category} style={{ marginBottom: '20px', padding: '12px', backgroundColor: '#f9fafb', borderRadius: '6px' }}>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#374151', marginBottom: '8px' }}>
                    {label}
                  </label>
                  
                  {/* Multi-select pour level_1 */}
                  <div style={{ marginBottom: '8px' }}>
                    <label style={{ display: 'block', fontSize: '11px', color: '#6b7280', marginBottom: '4px' }}>
                      Level 1 (valeurs)
                    </label>
                    <select
                      multiple
                      size={Math.min(validValues.length + 1, 4)}
                      value={validValues}
                      onChange={(e) => {
                        const selected = Array.from(e.target.selectedOptions, (option) => option.value);
                        handleLevel3MappingChange(category, selected);
                      }}
                      style={{
                        width: '100%',
                        padding: '6px',
                        fontSize: '12px',
                        border: '1px solid #d1d5db',
                        borderRadius: '4px',
                        backgroundColor: '#ffffff',
                      }}
                    >
                      {validValues.map((value) => (
                        <option key={value} value={value}>
                          {value}
                        </option>
                      ))}
                    </select>
                    {validValues.length === 0 && (
                      <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '4px', fontStyle: 'italic' }}>
                        Aucune valeur sélectionnée
                      </div>
                    )}
                    <select
                      value=""
                      onChange={(e) => {
                        if (e.target.value) {
                          const newValue = e.target.value;
                          const currentValues = config.level_3_mapping[category] || [];
                          if (!currentValues.includes(newValue)) {
                            handleLevel3MappingChange(category, [...currentValues, newValue]);
                          }
                          // Reset le select
                          e.target.value = '';
                        }
                      }}
                      style={{
                        width: '100%',
                        marginTop: '6px',
                        padding: '4px',
                        fontSize: '11px',
                        border: '1px solid #d1d5db',
                        borderRadius: '4px',
                        backgroundColor: '#ffffff',
                      }}
                    >
                      <option value="">+ Ajouter une valeur</option>
                      {level1Values
                        .filter((v) => !categoryValues.includes(v))
                        .map((value) => (
                          <option key={value} value={value}>
                            {value || '(vide)'}
                          </option>
                        ))}
                    </select>
                    {level1Values.filter((v) => !categoryValues.includes(v)).length === 0 && validValues.length > 0 && (
                      <div style={{ fontSize: '10px', color: '#9ca3af', marginTop: '4px', fontStyle: 'italic' }}>
                        Toutes les valeurs disponibles sont déjà sélectionnées
                      </div>
                    )}
                  </div>

                  {/* Durée */}
                  <div>
                    <label style={{ display: 'block', fontSize: '11px', color: '#6b7280', marginBottom: '4px' }}>
                      Durée (années)
                    </label>
                    <input
                      type="number"
                      min="0"
                      step="0.1"
                      value={duration}
                      onChange={(e) => handleDurationChange(category, Math.max(0, parseFloat(e.target.value) || 0))}
                      style={{
                        width: '100%',
                        padding: '6px',
                        fontSize: '12px',
                        border: '1px solid #d1d5db',
                        borderRadius: '4px',
                        backgroundColor: '#ffffff',
                      }}
                    />
                    {hasValues && (duration === 0 || !duration) && (
                      <div style={{ fontSize: '10px', color: '#f59e0b', marginTop: '4px', fontStyle: 'italic' }}>
                        ⚠️ Durée non configurée - les amortissements ne seront pas calculés pour cette catégorie
                      </div>
                    )}
                  </div>
                </div>
              );
            });
          })()}

          {/* Bouton Sauvegarder */}
          <button
            onClick={handleSave}
            disabled={saving}
            style={{
              width: '100%',
              padding: '10px',
              fontSize: '13px',
              fontWeight: '600',
              color: '#ffffff',
              backgroundColor: saving ? '#9ca3af' : '#3b82f6',
              border: 'none',
              borderRadius: '6px',
              cursor: saving ? 'not-allowed' : 'pointer',
              marginTop: '16px',
            }}
          >
            {saving ? '⏳ Sauvegarde...' : '💾 Sauvegarder'}
          </button>
        </div>
      )}
    </>
  );
}

