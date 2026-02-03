/**
 * Card de configuration Pro Rata & Forecast
 * 
 * Affiche un tableau avec :
 * - Colonnes de référence : Réel {year}, Année {year-1}
 * - Colonnes configurables : Prévu {year}, Évolution %/an
 * - Catégories calculées en lecture seule (amortissements, intérêts, etc.)
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useProperty } from '@/contexts/PropertyContext';
import { 
  prorataAPI, 
  ProRataSettings, 
  AnnualForecastConfig, 
  AnnualForecastConfigCreate,
  CategoryReferenceData 
} from '@/api/client';

interface Props {
  targetType: 'compte_resultat' | 'bilan_actif' | 'bilan_passif';
  year: number;
  sectionTitle?: string;  // Optionnel: "ACTIF" ou "PASSIF" pour le bilan
  onConfigChange?: () => void;  // Callback pour rafraîchir le tableau parent
  refreshKey?: number;  // Clé pour forcer le rechargement (quand config card change)
}

export default function ProRataForecastCard({ targetType, year, sectionTitle, onConfigChange, refreshKey }: Props) {
  const { activeProperty } = useProperty();
  const [settings, setSettings] = useState<ProRataSettings | null>(null);
  const [referenceData, setReferenceData] = useState<CategoryReferenceData[]>([]);
  const [localConfigs, setLocalConfigs] = useState<Record<string, { amount: number; rate: number }>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPinned, setIsPinned] = useState(false); // Carte réduite par défaut
  
  // Charger les données
  useEffect(() => {
    if (!activeProperty?.id) return;
    
    const loadData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        console.log(`[ProRataCard] Loading data for property=${activeProperty.id}, year=${year}, type=${targetType}`);
        
        const [settingsData, refData, configsData] = await Promise.all([
          prorataAPI.getSettings(activeProperty.id),
          prorataAPI.getReferenceData(activeProperty.id, year, targetType),
          prorataAPI.getConfigs(activeProperty.id, year, targetType),
        ]);
        
        console.log(`[ProRataCard] Settings:`, settingsData);
        console.log(`[ProRataCard] Reference data:`, refData);
        console.log(`[ProRataCard] Configs:`, configsData);
        
        setSettings(settingsData);
        setReferenceData(refData.categories);
        
        // Initialiser localConfigs avec les valeurs existantes
        const local: Record<string, { amount: number; rate: number }> = {};
        refData.categories.forEach((cat: CategoryReferenceData) => {
          if (!cat.is_calculated) {
            const existing = configsData.find((c: AnnualForecastConfig) => c.level_1 === cat.level_1);
            local[cat.level_1] = {
              amount: existing?.base_annual_amount || 0,
              rate: (existing?.annual_growth_rate || 0) * 100,
            };
          }
        });
        
        // Si pas de référence data, initialiser avec les configs existantes
        if (refData.categories.length === 0 && configsData.length > 0) {
          configsData.forEach((config: AnnualForecastConfig) => {
            local[config.level_1] = {
              amount: config.base_annual_amount || 0,
              rate: (config.annual_growth_rate || 0) * 100,
            };
          });
        }
        
        setLocalConfigs(local);
      } catch (err) {
        console.error('[ProRataCard] Error loading data:', err);
        setError('Erreur lors du chargement des données');
      } finally {
        setIsLoading(false);
      }
    };
    
    loadData();
  }, [activeProperty?.id, year, targetType, refreshKey]);
  
  // Pré-remplir avec les valeurs de l'année précédente
  const handlePrefillFromPreviousYear = useCallback(() => {
    const newConfigs = { ...localConfigs };
    referenceData.forEach(cat => {
      if (!cat.is_calculated) {
        newConfigs[cat.level_1] = {
          ...newConfigs[cat.level_1],
          amount: cat.real_previous_year || 0
        };
      }
    });
    setLocalConfigs(newConfigs);
  }, [localConfigs, referenceData]);
  
  // Sauvegarder les settings
  const handleSettingsChange = async (field: keyof ProRataSettings, value: boolean | number) => {
    if (!activeProperty?.id || !settings) return;
    
    try {
      console.log(`[ProRataCard] Updating settings: ${field}=${value}`);
      const updated = await prorataAPI.updateSettings(activeProperty.id, {
        ...settings,
        [field]: value,
      });
      setSettings(updated);
      onConfigChange?.();
    } catch (err) {
      console.error('[ProRataCard] Error updating settings:', err);
      setError('Erreur lors de la mise à jour des paramètres');
    }
  };
  
  // Sauvegarder les configs (uniquement les catégories non calculées)
  const handleSaveConfigs = async () => {
    if (!activeProperty?.id) return;
    
    setIsSaving(true);
    setError(null);
    try {
      // Récupérer les catégories à sauvegarder
      const categories = referenceData.length > 0 
        ? referenceData.filter(cat => !cat.is_calculated).map(cat => cat.level_1)
        : Object.keys(localConfigs);
      
      const configsToSave: AnnualForecastConfigCreate[] = categories.map(level1 => ({
        property_id: activeProperty.id,
        year,
        level_1: level1,
        target_type: targetType,
        base_annual_amount: localConfigs[level1]?.amount || 0,
        annual_growth_rate: (localConfigs[level1]?.rate || 0) / 100,
      }));
      
      console.log(`[ProRataCard] Saving ${configsToSave.length} configs`);
      await prorataAPI.bulkUpsertConfigs(activeProperty.id, configsToSave);
      onConfigChange?.();
      alert('Configuration sauvegardée !');
    } catch (err) {
      console.error('[ProRataCard] Error saving configs:', err);
      setError('Erreur lors de la sauvegarde');
      alert('Erreur lors de la sauvegarde');
    } finally {
      setIsSaving(false);
    }
  };
  
  // Formater un montant en euros
  const formatEuro = (amount: number) => {
    return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(amount);
  };
  
  // Titre dynamique
  const getTitle = () => {
    if (sectionTitle) return `⚙️ Prévisions annuelles - ${sectionTitle}`;
    if (targetType === 'compte_resultat') return '⚙️ Prévisions annuelles - Compte de Résultat';
    if (targetType === 'bilan_actif') return '⚙️ Prévisions annuelles - ACTIF';
    if (targetType === 'bilan_passif') return '⚙️ Prévisions annuelles - PASSIF';
    return '⚙️ Prévisions annuelles';
  };
  
  if (isLoading) {
    return (
      <div style={{ 
        padding: '20px', 
        backgroundColor: 'white', 
        borderRadius: '8px', 
        border: '1px solid #e5e7eb',
        marginTop: '24px',
        color: '#666' 
      }}>
        ⏳ Chargement des prévisions...
      </div>
    );
  }
  
  return (
    <div style={{ 
      backgroundColor: 'white', 
      borderRadius: '8px', 
      border: '1px solid #e5e7eb',
      marginTop: '24px',
      padding: '20px'
    }}>
      {/* En-tête de la card */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: isPinned ? '16px' : 0,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            flex: 1,
            cursor: 'pointer',
          }}
          onClick={() => setIsPinned(!isPinned)}
        >
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '600', color: '#1e3a5f' }}>
            {getTitle()}
          </h3>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setIsPinned(!isPinned);
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '32px',
              height: '32px',
              padding: '0',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              backgroundColor: '#ffffff',
              cursor: 'pointer',
              fontSize: '16px',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#f9fafb';
              e.currentTarget.style.borderColor = '#9ca3af';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = '#ffffff';
              e.currentTarget.style.borderColor = '#d1d5db';
            }}
            title={isPinned ? 'Replier la card' : 'Déplier la card'}
          >
            {isPinned ? '📌' : '📍'}
          </button>
        </div>
      </div>
      
      {/* Contenu (visible seulement si épinglé) */}
      {isPinned && (
        <>
      {error && (
        <div style={{ 
          padding: '10px', 
          backgroundColor: '#fef2f2', 
          color: '#dc2626', 
          borderRadius: '4px',
          marginBottom: '16px'
        }}>
          ❌ {error}
        </div>
      )}
      
      {/* Checkboxes - Afficher seulement pour compte_resultat ou bilan_actif (pas pour bilan_passif) */}
      {targetType !== 'bilan_passif' && (
        <div style={{ display: 'flex', gap: '24px', marginBottom: '20px', flexWrap: 'wrap' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={settings?.prorata_enabled || false}
              onChange={(e) => handleSettingsChange('prorata_enabled', e.target.checked)}
            />
            <span>Activer prévisions année en cours ({year})</span>
          </label>
          
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={settings?.forecast_enabled || false}
              onChange={(e) => handleSettingsChange('forecast_enabled', e.target.checked)}
            />
            <span>Projeter sur</span>
            <input
              type="number"
              min="1"
              max="10"
              value={settings?.forecast_years || 3}
              onChange={(e) => handleSettingsChange('forecast_years', parseInt(e.target.value) || 3)}
              style={{ width: '50px', padding: '4px', border: '1px solid #ccc', borderRadius: '4px' }}
              disabled={!settings?.forecast_enabled}
            />
            <span>années futures</span>
          </label>
        </div>
      )}
      
      {/* Tableau de configuration - toujours visible pour permettre la saisie */}
      {(settings?.prorata_enabled || settings?.forecast_enabled || referenceData.length === 0) && (
        <>
          {/* Bouton pré-remplir */}
          {referenceData.length > 0 && (
            <div style={{ marginBottom: '12px' }}>
              <button
                onClick={handlePrefillFromPreviousYear}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#f0f9ff',
                  color: '#0369a1',
                  border: '1px solid #0ea5e9',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '13px',
                }}
              >
                📋 Pré-remplir avec {year - 1}
              </button>
            </div>
          )}
          
          {/* Message si pas de données de référence */}
          {referenceData.length === 0 && (
            <div style={{ 
              padding: '16px', 
              backgroundColor: '#fefce8', 
              borderRadius: '6px',
              marginBottom: '16px',
              color: '#854d0e'
            }}>
              ℹ️ Les données de référence seront disponibles après l'implémentation du Step 11bis.2.
              <br />
              Vous pouvez quand même saisir des prévisions manuellement ci-dessous.
            </div>
          )}
          
          {/* Formulaire de saisie manuelle si pas de référence */}
          {referenceData.length === 0 && (
            <div style={{ marginBottom: '16px' }}>
              <button
                onClick={() => {
                  const newLevel1 = prompt('Nom de la catégorie comptable (level_1):');
                  if (newLevel1 && newLevel1.trim()) {
                    setLocalConfigs(prev => ({
                      ...prev,
                      [newLevel1.trim()]: { amount: 0, rate: 0 }
                    }));
                  }
                }}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#1e3a5f',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '13px',
                }}
              >
                ➕ Ajouter une catégorie
              </button>
            </div>
          )}
          
          {/* Tableau */}
          {(referenceData.length > 0 || Object.keys(localConfigs).length > 0) && (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
              <thead>
                <tr style={{ backgroundColor: '#f9fafb' }}>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '2px solid #e5e7eb' }}>
                    Catégorie
                  </th>
                  {referenceData.length > 0 && (
                    <>
                      <th style={{ padding: '10px', textAlign: 'right', borderBottom: '2px solid #e5e7eb', width: '120px' }}>
                        Réel {year}
                      </th>
                      <th style={{ padding: '10px', textAlign: 'right', borderBottom: '2px solid #e5e7eb', width: '120px' }}>
                        Année {year - 1}
                      </th>
                    </>
                  )}
                  <th style={{ padding: '10px', textAlign: 'right', borderBottom: '2px solid #e5e7eb', width: '150px' }}>
                    Prévu {year} (€)
                  </th>
                  {referenceData.length > 0 && (
                    <th style={{ padding: '10px', textAlign: 'right', borderBottom: '2px solid #e5e7eb', width: '90px' }}>
                      % Réalisé
                    </th>
                  )}
                  {/* Évol. %/an - seulement si forecast activé */}
                  {settings?.forecast_enabled && (
                    <th style={{ padding: '10px', textAlign: 'right', borderBottom: '2px solid #e5e7eb', width: '100px' }}>
                      Évol. %/an
                    </th>
                  )}
                  {/* Colonnes des années futures si forecast activé */}
                  {settings?.forecast_enabled && Array.from({ length: settings.forecast_years }, (_, i) => (
                    <th key={`year-${year + i + 1}`} style={{ padding: '10px', textAlign: 'right', borderBottom: '2px solid #e5e7eb', width: '110px', backgroundColor: '#f0f9ff' }}>
                      {year + i + 1}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {referenceData.length > 0 ? (
                  // Affichage avec données de référence
                  referenceData.map(cat => (
                    <tr 
                      key={cat.level_1}
                      style={{ 
                        backgroundColor: cat.is_calculated ? '#f8fafc' : 'white',
                      }}
                    >
                      <td style={{ 
                        padding: '10px', 
                        borderBottom: '1px solid #e5e7eb',
                        fontWeight: cat.is_calculated ? 'normal' : '500',
                        fontStyle: cat.is_calculated ? 'italic' : 'normal',
                        color: cat.is_calculated ? '#64748b' : '#1e293b',
                      }}>
                        {cat.level_1}
                        {cat.is_calculated && (
                          <span style={{ 
                            marginLeft: '8px', 
                            fontSize: '11px', 
                            color: '#94a3b8',
                            backgroundColor: '#f1f5f9',
                            padding: '2px 6px',
                            borderRadius: '4px',
                          }}>
                            calculé
                          </span>
                        )}
                      </td>
                      
                      {/* Réel année en cours */}
                      <td style={{ 
                        padding: '10px', 
                        textAlign: 'right', 
                        borderBottom: '1px solid #e5e7eb',
                        color: cat.real_current_year >= 0 ? '#059669' : '#dc2626',
                        fontWeight: '500',
                      }}>
                        {formatEuro(cat.real_current_year)}
                      </td>
                      
                      {/* Année précédente OU "donnée calculée" */}
                      <td style={{ 
                        padding: '10px', 
                        textAlign: 'right', 
                        borderBottom: '1px solid #e5e7eb',
                        color: cat.is_calculated ? '#94a3b8' : '#6b7280',
                        fontStyle: cat.is_calculated ? 'italic' : 'normal',
                      }}>
                        {cat.is_calculated ? 'donnée calculée' : formatEuro(cat.real_previous_year)}
                      </td>
                      
                      {/* Prévu année en cours */}
                      <td style={{ padding: '10px', borderBottom: '1px solid #e5e7eb' }}>
                        {cat.is_calculated ? (
                          <span style={{ 
                            display: 'block', 
                            textAlign: 'right', 
                            color: '#94a3b8',
                            fontStyle: 'italic',
                          }}>
                            —
                          </span>
                        ) : (
                          <input
                            type="number"
                            value={localConfigs[cat.level_1]?.amount || ''}
                            onChange={(e) => setLocalConfigs(prev => ({
                              ...prev,
                              [cat.level_1]: { ...prev[cat.level_1], amount: parseFloat(e.target.value) || 0 }
                            }))}
                            style={{ 
                              width: '100%', 
                              padding: '6px', 
                              border: '1px solid #d1d5db', 
                              borderRadius: '4px',
                              textAlign: 'right',
                            }}
                            placeholder="0"
                          />
                        )}
                      </td>
                      
                      {/* % Réalisé (réel / prévu) */}
                      <td style={{ 
                        padding: '10px', 
                        textAlign: 'right', 
                        borderBottom: '1px solid #e5e7eb',
                      }}>
                        {(() => {
                          if (cat.is_calculated) {
                            return <span style={{ color: '#94a3b8', fontStyle: 'italic' }}>—</span>;
                          }
                          const planned = localConfigs[cat.level_1]?.amount || 0;
                          const real = Math.abs(cat.real_current_year);
                          if (planned === 0) {
                            return <span style={{ color: '#6b7280' }}>—</span>;
                          }
                          const pct = (real / Math.abs(planned)) * 100;
                          const color = pct >= 100 ? '#059669' : pct >= 50 ? '#d97706' : '#dc2626';
                          return (
                            <span style={{ 
                              color, 
                              fontWeight: '600',
                              fontSize: '13px',
                            }}>
                              {pct.toFixed(0)}%
                            </span>
                          );
                        })()}
                      </td>
                      
                      {/* Évolution %/an - seulement si forecast activé */}
                      {settings?.forecast_enabled && (
                        <td style={{ padding: '10px', borderBottom: '1px solid #e5e7eb' }}>
                          {cat.is_calculated ? (
                            <span style={{ 
                              display: 'block', 
                              textAlign: 'right', 
                              color: '#94a3b8',
                              fontStyle: 'italic',
                            }}>
                              —
                            </span>
                          ) : (
                            <input
                              type="number"
                              step="0.5"
                              value={localConfigs[cat.level_1]?.rate || ''}
                              onChange={(e) => setLocalConfigs(prev => ({
                                ...prev,
                                [cat.level_1]: { ...prev[cat.level_1], rate: parseFloat(e.target.value) || 0 }
                              }))}
                              style={{ 
                                width: '100%', 
                                padding: '6px', 
                                border: '1px solid #d1d5db', 
                                borderRadius: '4px',
                                textAlign: 'right',
                              }}
                              placeholder="0"
                            />
                          )}
                        </td>
                      )}
                      
                      {/* Colonnes des années futures si forecast activé */}
                      {settings?.forecast_enabled && Array.from({ length: settings.forecast_years }, (_, i) => {
                        const futureYear = year + i + 1;
                        const yearsAhead = i + 1;
                        const baseAmount = localConfigs[cat.level_1]?.amount || 0;
                        const growthRate = (localConfigs[cat.level_1]?.rate || 0) / 100;
                        // Formule: base × (1 + rate)^years
                        const projectedAmount = cat.is_calculated 
                          ? cat.real_current_year  // Catégorie calculée: on garde la valeur actuelle
                          : baseAmount * Math.pow(1 + growthRate, yearsAhead);
                        
                        return (
                          <td 
                            key={`${cat.level_1}-${futureYear}`}
                            style={{ 
                              padding: '10px', 
                              textAlign: 'right', 
                              borderBottom: '1px solid #e5e7eb',
                              backgroundColor: '#f0f9ff',
                              color: cat.is_calculated ? '#94a3b8' : '#1e3a5f',
                              fontStyle: cat.is_calculated ? 'italic' : 'normal',
                            }}
                          >
                            {cat.is_calculated ? '—' : formatEuro(projectedAmount)}
                          </td>
                        );
                      })}
                    </tr>
                  ))
                ) : (
                  // Affichage sans données de référence (saisie manuelle)
                  Object.entries(localConfigs).map(([level1, config]) => (
                    <tr key={level1}>
                      <td style={{ 
                        padding: '10px', 
                        borderBottom: '1px solid #e5e7eb',
                        fontWeight: '500',
                        color: '#1e293b',
                      }}>
                        {level1}
                        <button
                          onClick={() => {
                            const newConfigs = { ...localConfigs };
                            delete newConfigs[level1];
                            setLocalConfigs(newConfigs);
                          }}
                          style={{
                            marginLeft: '8px',
                            padding: '2px 6px',
                            fontSize: '11px',
                            backgroundColor: '#fef2f2',
                            color: '#dc2626',
                            border: '1px solid #fecaca',
                            borderRadius: '4px',
                            cursor: 'pointer',
                          }}
                        >
                          ✕
                        </button>
                      </td>
                      
                      {/* Prévu année en cours */}
                      <td style={{ padding: '10px', borderBottom: '1px solid #e5e7eb' }}>
                        <input
                          type="number"
                          value={config.amount || ''}
                          onChange={(e) => setLocalConfigs(prev => ({
                            ...prev,
                            [level1]: { ...prev[level1], amount: parseFloat(e.target.value) || 0 }
                          }))}
                          style={{ 
                            width: '100%', 
                            padding: '6px', 
                            border: '1px solid #d1d5db', 
                            borderRadius: '4px',
                            textAlign: 'right',
                          }}
                          placeholder="0"
                        />
                      </td>
                      
                      {/* Évolution %/an */}
                      <td style={{ padding: '10px', borderBottom: '1px solid #e5e7eb' }}>
                        <input
                          type="number"
                          step="0.5"
                          value={config.rate || ''}
                          onChange={(e) => setLocalConfigs(prev => ({
                            ...prev,
                            [level1]: { ...prev[level1], rate: parseFloat(e.target.value) || 0 }
                          }))}
                          style={{ 
                            width: '100%', 
                            padding: '6px', 
                            border: '1px solid #d1d5db', 
                            borderRadius: '4px',
                            textAlign: 'right',
                          }}
                          placeholder="0"
                          disabled={!settings?.forecast_enabled}
                        />
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
          
          {/* Bouton sauvegarder */}
          {(referenceData.length > 0 || Object.keys(localConfigs).length > 0) && (
            <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '12px', color: '#6b7280' }}>
                💡 Les catégories "calculé" utilisent les valeurs réelles du système
              </span>
              <button
                onClick={handleSaveConfigs}
                disabled={isSaving}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#1e3a5f',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: isSaving ? 'wait' : 'pointer',
                  opacity: isSaving ? 0.7 : 1,
                }}
              >
                {isSaving ? '⏳ Sauvegarde...' : '💾 Sauvegarder'}
              </button>
            </div>
          )}
        </>
      )}
      
      {/* Message si ni prorata ni forecast activé */}
      {!settings?.prorata_enabled && !settings?.forecast_enabled && referenceData.length > 0 && (
        <div style={{ 
          padding: '16px', 
          backgroundColor: '#f3f4f6', 
          borderRadius: '6px',
          color: '#6b7280',
          textAlign: 'center'
        }}>
          Activez les prévisions pour configurer les montants annuels prévisionnels.
        </div>
      )}
        </>
      )}
    </div>
  );
}
