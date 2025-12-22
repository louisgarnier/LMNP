/**
 * PivotFieldSelector component - Panneau de configuration latéral (comme pin headers Excel)
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useRef, useEffect } from 'react';

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

export default function PivotFieldSelector({ config, onChange }: PivotFieldSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isHovering, setIsHovering] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLDivElement>(null);

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
          zIndex: 1000,
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

          {/* Instructions */}
          <div style={{ marginTop: '16px', padding: '8px', backgroundColor: '#f3f4f6', borderRadius: '4px', fontSize: '11px', color: '#6b7280' }}>
            Un champ ne peut être que dans une seule zone. Utilisez Ctrl/Cmd pour sélection multiple.
          </div>
        </div>
      )}
    </>
  );
}
