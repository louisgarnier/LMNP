/**
 * PivotFieldSelector component - Panneau de configuration latéral (comme pin headers Excel)
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useRef, useEffect } from 'react';
import { transactionsAPI } from '@/api/client';

// Types
export type FieldType = 'date' | 'mois' | 'annee' | 'level_1' | 'level_2' | 'level_3' | 'nom' | 'quantite';

export interface PivotFieldConfig {
  rows: FieldType[];
  columns: FieldType[];
  data: FieldType[];
  filters: Record<string, any>;
}

interface PivotFieldSelectorProps {
  config: PivotFieldConfig;
  onChange: (config: PivotFieldConfig) => void;
}

// Labels des champs
const FIELD_LABELS: Record<FieldType, string> = {
  date: 'Date',
  mois: 'Mois',
  annee: 'Année',
  level_1: 'Level 1',
  level_2: 'Level 2',
  level_3: 'Level 3',
  nom: 'Nom',
  quantite: 'Quantité',
};

// Champs disponibles pour lignes/colonnes
const AVAILABLE_FIELDS: FieldType[] = ['date', 'mois', 'annee', 'level_1', 'level_2', 'level_3', 'nom'];

// Champs disponibles pour filtres (sans quantite)
const FILTER_FIELDS: FieldType[] = ['date', 'mois', 'annee', 'level_1', 'level_2', 'level_3', 'nom'];

export default function PivotFieldSelector({ config, onChange }: PivotFieldSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isHovering, setIsHovering] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLDivElement>(null);
  const [uniqueValues, setUniqueValues] = useState<Record<string, string[]>>({});
  const [loadingValues, setLoadingValues] = useState<Record<string, boolean>>({});
  const [newFilterField, setNewFilterField] = useState<FieldType | ''>('');
  const [newFilterValue, setNewFilterValue] = useState<string>('');

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

  const handleAddField = (zone: 'rows' | 'columns' | 'data', field: FieldType) => {
    const newConfig = { ...config };
    
    // Vérifier que le champ n'est pas déjà dans cette zone
    if (newConfig[zone].includes(field)) {
      return;
    }
    
    // Retirer le champ des autres zones
    newConfig.rows = newConfig.rows.filter((f) => f !== field);
    newConfig.columns = newConfig.columns.filter((f) => f !== field);
    newConfig.data = newConfig.data.filter((f) => f !== field);
    
    // Ajouter à la zone sélectionnée
    newConfig[zone] = [...newConfig[zone], field];
    
    onChange(newConfig);
  };

  const handleRemoveField = (zone: 'rows' | 'columns' | 'data', field: FieldType) => {
    const newConfig = { ...config };
    newConfig[zone] = newConfig[zone].filter((f) => f !== field);
    onChange(newConfig);
  };

  // Charger les valeurs uniques pour un champ
  const loadUniqueValues = async (field: FieldType) => {
    if (uniqueValues[field] || loadingValues[field]) {
      return;
    }

    setLoadingValues((prev) => ({ ...prev, [field]: true }));
    try {
      const response = await transactionsAPI.getUniqueValues(field);
      setUniqueValues((prev) => ({ ...prev, [field]: response.values }));
    } catch (error) {
      console.error(`Erreur lors du chargement des valeurs pour ${field}:`, error);
      setUniqueValues((prev) => ({ ...prev, [field]: [] }));
    } finally {
      setLoadingValues((prev) => ({ ...prev, [field]: false }));
    }
  };

  // Ajouter un filtre (OR pour le même champ, AND entre champs différents)
  const handleAddFilter = () => {
    if (!newFilterField || !newFilterValue) {
      return;
    }

    const newConfig = { ...config };
    const currentFilters = newConfig.filters || {};
    
    // Si le champ existe déjà, ajouter la valeur à l'array (OR)
    // Sinon, créer un nouvel array avec la valeur
    if (currentFilters[newFilterField]) {
      const existingValues = Array.isArray(currentFilters[newFilterField]) 
        ? currentFilters[newFilterField] 
        : [currentFilters[newFilterField]];
      
      // Ne pas ajouter si la valeur existe déjà
      if (!existingValues.includes(newFilterValue)) {
        currentFilters[newFilterField] = [...existingValues, newFilterValue];
      }
    } else {
      currentFilters[newFilterField] = [newFilterValue];
    }
    
    newConfig.filters = currentFilters;
    onChange(newConfig);
    setNewFilterField('');
    setNewFilterValue('');
  };

  // Retirer une valeur spécifique d'un filtre (ou tout le filtre si c'est la dernière valeur)
  const handleRemoveFilterValue = (field: string, value?: string) => {
    const newConfig = { ...config };
    const currentFilters = { ...newConfig.filters };
    
    if (value !== undefined) {
      // Retirer une valeur spécifique
      const fieldValues = Array.isArray(currentFilters[field]) 
        ? currentFilters[field] 
        : [currentFilters[field]];
      
      const newValues = fieldValues.filter(v => v !== value);
      
      if (newValues.length === 0) {
        // Si plus de valeurs, retirer tout le filtre
        delete currentFilters[field];
      } else {
        currentFilters[field] = newValues;
      }
    } else {
      // Retirer tout le filtre (compatibilité avec l'ancien code)
      delete currentFilters[field];
    }
    
    newConfig.filters = currentFilters;
    onChange(newConfig);
  };

  // Charger les valeurs quand un champ est sélectionné
  useEffect(() => {
    if (newFilterField) {
      // Recharger si pas encore chargé ou si le champ change
      if (!uniqueValues[newFilterField] && !loadingValues[newFilterField]) {
        loadUniqueValues(newFilterField);
      }
    } else {
      // Réinitialiser la valeur si le champ est désélectionné
      setNewFilterValue('');
    }
  }, [newFilterField]);

  // Champs disponibles (non utilisés)
  const usedFields = new Set([...config.rows, ...config.columns, ...config.data]);
  const availableFields = AVAILABLE_FIELDS.filter((f) => !usedFields.has(f));
  const quantiteAvailable = !config.data.includes('quantite');

  return (
    <>
      {/* Zone de déclenchement (hover) - bordure droite */}
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
        title="Configuration du tableau croisé"
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
            width: '320px',
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
              Configuration
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

          {/* Lignes */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#374151', marginBottom: '6px' }}>
              Lignes
            </label>
            <select
              multiple
              size={Math.min(config.rows.length + 1, 4)}
              value={config.rows}
              onChange={(e) => {
                const selected = Array.from(e.target.selectedOptions, (option) => option.value as FieldType);
                const newConfig = { ...config };
                newConfig.rows = selected;
                newConfig.columns = newConfig.columns.filter((f) => !selected.includes(f));
                newConfig.data = newConfig.data.filter((f) => !selected.includes(f));
                onChange(newConfig);
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
              {config.rows.map((field) => (
                <option key={field} value={field}>
                  {FIELD_LABELS[field]}
                </option>
              ))}
            </select>
            {config.rows.length === 0 && (
              <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '4px', fontStyle: 'italic' }}>
                Aucun champ
              </div>
            )}
            {availableFields.length > 0 && (
              <select
                value=""
                onChange={(e) => {
                  if (e.target.value) {
                    handleAddField('rows', e.target.value as FieldType);
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
                  backgroundColor: '#f9fafb',
                }}
              >
                <option value="">+ Ajouter</option>
                {availableFields.map((field) => (
                  <option key={field} value={field}>
                    {FIELD_LABELS[field]}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Colonnes */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#374151', marginBottom: '6px' }}>
              Colonnes
            </label>
            <select
              multiple
              size={Math.min(config.columns.length + 1, 4)}
              value={config.columns}
              onChange={(e) => {
                const selected = Array.from(e.target.selectedOptions, (option) => option.value as FieldType);
                const newConfig = { ...config };
                newConfig.columns = selected;
                newConfig.rows = newConfig.rows.filter((f) => !selected.includes(f));
                newConfig.data = newConfig.data.filter((f) => !selected.includes(f));
                onChange(newConfig);
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
              {config.columns.map((field) => (
                <option key={field} value={field}>
                  {FIELD_LABELS[field]}
                </option>
              ))}
            </select>
            {config.columns.length === 0 && (
              <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '4px', fontStyle: 'italic' }}>
                Aucun champ
              </div>
            )}
            {availableFields.length > 0 && (
              <select
                value=""
                onChange={(e) => {
                  if (e.target.value) {
                    handleAddField('columns', e.target.value as FieldType);
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
                  backgroundColor: '#f9fafb',
                }}
              >
                <option value="">+ Ajouter</option>
                {availableFields.map((field) => (
                  <option key={field} value={field}>
                    {FIELD_LABELS[field]}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Données */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#374151', marginBottom: '6px' }}>
              Données
            </label>
            <select
              multiple
              size={Math.min(config.data.length + 1, 4)}
              value={config.data}
              onChange={(e) => {
                const selected = Array.from(e.target.selectedOptions, (option) => option.value as FieldType);
                const newConfig = { ...config };
                newConfig.data = selected;
                newConfig.rows = newConfig.rows.filter((f) => !selected.includes(f));
                newConfig.columns = newConfig.columns.filter((f) => !selected.includes(f));
                onChange(newConfig);
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
              {config.data.map((field) => (
                <option key={field} value={field}>
                  {FIELD_LABELS[field]}
                </option>
              ))}
            </select>
            {config.data.length === 0 && (
              <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '4px', fontStyle: 'italic' }}>
                Aucun champ
              </div>
            )}
            {quantiteAvailable && (
              <button
                onClick={() => handleAddField('data', 'quantite')}
                style={{
                  width: '100%',
                  marginTop: '6px',
                  padding: '4px',
                  fontSize: '11px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  backgroundColor: '#f9fafb',
                  cursor: 'pointer',
                }}
              >
                + Ajouter Quantité
              </button>
            )}
          </div>

          {/* Filtres */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#374151', marginBottom: '6px' }}>
              Filtres
            </label>
            
            {/* Liste des filtres actifs */}
            {Object.keys(config.filters || {}).length > 0 && (
              <div style={{ marginBottom: '8px' }}>
                {Object.entries(config.filters || {}).map(([field, value]) => {
                  // Convertir en array si ce n'est pas déjà le cas (compatibilité)
                  const values = Array.isArray(value) ? value : [value];
                  
                  return (
                    <div key={field} style={{ marginBottom: '4px' }}>
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '4px 8px',
                          backgroundColor: '#f3f4f6',
                          borderRadius: '4px',
                          fontSize: '11px',
                        }}
                      >
                        <span style={{ color: '#374151', fontWeight: '600' }}>
                          {FIELD_LABELS[field as FieldType]}:
                        </span>
                        <button
                          onClick={() => handleRemoveFilterValue(field)}
                          style={{
                            padding: '2px 6px',
                            fontSize: '10px',
                            border: 'none',
                            borderRadius: '3px',
                            backgroundColor: '#ef4444',
                            color: '#ffffff',
                            cursor: 'pointer',
                          }}
                          title="Retirer tout le filtre"
                        >
                          ✕
                        </button>
                      </div>
                      {/* Afficher toutes les valeurs avec possibilité de retirer individuellement */}
                      <div style={{ marginTop: '2px', paddingLeft: '8px' }}>
                        {values.map((val, idx) => (
                          <div
                            key={`${field}-${val}-${idx}`}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              padding: '2px 6px',
                              marginTop: '2px',
                              backgroundColor: '#ffffff',
                              borderRadius: '3px',
                              fontSize: '10px',
                              border: '1px solid #e5e7eb',
                            }}
                          >
                            <span style={{ color: '#6b7280' }}>
                              {String(val)}
                            </span>
                            <button
                              onClick={() => handleRemoveFilterValue(field, val)}
                              style={{
                                padding: '1px 4px',
                                fontSize: '9px',
                                border: 'none',
                                borderRadius: '2px',
                                backgroundColor: '#fca5a5',
                                color: '#ffffff',
                                cursor: 'pointer',
                                marginLeft: '4px',
                              }}
                              title="Retirer cette valeur"
                            >
                              ×
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Ajouter un nouveau filtre */}
            <div style={{ display: 'flex', gap: '4px', marginBottom: '4px' }}>
              <select
                value={newFilterField}
                onChange={(e) => {
                  setNewFilterField(e.target.value as FieldType | '');
                  setNewFilterValue('');
                }}
                style={{
                  flex: '0 0 100px',
                  padding: '4px',
                  fontSize: '11px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  backgroundColor: '#ffffff',
                }}
              >
                <option value="">Champ</option>
                {FILTER_FIELDS.map((field) => {
                  // Afficher si le champ a déjà un filtre
                  const hasFilter = config.filters && config.filters[field];
                  return (
                    <option key={field} value={field}>
                      {FIELD_LABELS[field]}{hasFilter ? ' (déjà filtré)' : ''}
                    </option>
                  );
                })}
              </select>
              <select
                value={newFilterValue}
                onChange={(e) => setNewFilterValue(e.target.value)}
                disabled={!newFilterField || loadingValues[newFilterField]}
                style={{
                  flex: '1 1 auto',
                  minWidth: '120px',
                  maxWidth: 'calc(100% - 140px)',
                  padding: '4px',
                  fontSize: '11px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  backgroundColor: newFilterField && !loadingValues[newFilterField] ? '#ffffff' : '#f9fafb',
                  cursor: newFilterField && !loadingValues[newFilterField] ? 'pointer' : 'not-allowed',
                }}
              >
                <option value="">
                  {loadingValues[newFilterField] 
                    ? 'Chargement...' 
                    : newFilterField 
                      ? uniqueValues[newFilterField]?.length === 0 
                        ? 'Aucune valeur' 
                        : 'Sélectionner une valeur'
                      : 'Sélectionner un champ'}
                </option>
                {newFilterField && uniqueValues[newFilterField]?.map((value) => {
                  // Vérifier si la valeur est déjà dans les filtres pour ce champ
                  const existingValues = config.filters && config.filters[newFilterField]
                    ? (Array.isArray(config.filters[newFilterField]) 
                        ? config.filters[newFilterField] 
                        : [config.filters[newFilterField]])
                    : [];
                  const isAlreadySelected = existingValues.includes(value);
                  
                  return (
                    <option 
                      key={value} 
                      value={value}
                      disabled={isAlreadySelected}
                      style={isAlreadySelected ? { color: '#9ca3af', fontStyle: 'italic' } : {}}
                    >
                      {value}{isAlreadySelected ? ' (déjà sélectionné)' : ''}
                    </option>
                  );
                })}
              </select>
              <button
                onClick={handleAddFilter}
                disabled={!newFilterField || !newFilterValue || loadingValues[newFilterField]}
                style={{
                  flex: '0 0 32px',
                  padding: '4px 8px',
                  fontSize: '11px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  backgroundColor: newFilterField && newFilterValue && !loadingValues[newFilterField] ? '#3b82f6' : '#f9fafb',
                  color: newFilterField && newFilterValue && !loadingValues[newFilterField] ? '#ffffff' : '#9ca3af',
                  cursor: newFilterField && newFilterValue && !loadingValues[newFilterField] ? 'pointer' : 'not-allowed',
                  zIndex: 1001,
                  position: 'relative',
                }}
                title={!newFilterField ? 'Sélectionner un champ' : !newFilterValue ? 'Sélectionner une valeur' : 'Ajouter le filtre'}
              >
                +
              </button>
            </div>
            {Object.keys(config.filters || {}).length === 0 && (
              <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '4px', fontStyle: 'italic' }}>
                Aucun filtre
              </div>
            )}
          </div>

          {/* Instructions */}
          <div style={{ marginTop: '16px', padding: '8px', backgroundColor: '#f3f4f6', borderRadius: '4px', fontSize: '11px', color: '#6b7280' }}>
            Un champ ne peut être que dans une seule zone. Utilisez Ctrl/Cmd pour sélection multiple.
          </div>
        </div>
      )}
    </>
  );
}
