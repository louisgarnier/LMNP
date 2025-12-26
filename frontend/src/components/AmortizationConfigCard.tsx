/**
 * AmortizationConfigCard component - Card de configuration des amortissements
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect } from 'react';
import { transactionsAPI, amortizationTypesAPI, AmortizationType } from '@/api/client';

interface AmortizationConfigCardProps {
  onConfigUpdated?: () => void;
}

export default function AmortizationConfigCard({ onConfigUpdated }: AmortizationConfigCardProps) {
  const [level2Value, setLevel2Value] = useState<string>('');
  const [level2Values, setLevel2Values] = useState<string[]>([]);
  const [loadingValues, setLoadingValues] = useState(false);
  const [amortizationTypes, setAmortizationTypes] = useState<AmortizationType[]>([]);
  const [loadingTypes, setLoadingTypes] = useState(false);
  const [editingNameId, setEditingNameId] = useState<number | null>(null);
  const [editingNameValue, setEditingNameValue] = useState<string>('');
  const [level1Values, setLevel1Values] = useState<string[]>([]);
  const [editingLevel1Id, setEditingLevel1Id] = useState<number | null>(null);
  const [editingDateId, setEditingDateId] = useState<number | null>(null);
  const [editingDateValue, setEditingDateValue] = useState<string>('');
  const [amounts, setAmounts] = useState<Record<number, number>>({});
  const [loadingAmounts, setLoadingAmounts] = useState<Record<number, boolean>>({});
  const [editingDurationId, setEditingDurationId] = useState<number | null>(null);
  const [editingDurationValue, setEditingDurationValue] = useState<string>('');

  // Charger les valeurs uniques de level_2 au montage
  useEffect(() => {
    loadLevel2Values();
  }, []);

  // Recharger les valeurs level_1 quand level2Value change
  useEffect(() => {
    if (level2Value) {
      loadLevel1Values();
    } else {
      setLevel1Values([]);
    }
  }, [level2Value]);

  // Charger les types d'amortissement après le chargement de level2Value
  useEffect(() => {
    if (level2Value) {
      loadAmortizationTypes();
    }
  }, [level2Value]);

  // Recharger les montants quand les types changent ou quand level2Value change
  useEffect(() => {
    console.log('🔄 [AmortizationConfigCard] useEffect loadAmounts déclenché', { 
      typesCount: amortizationTypes.length, 
      level2Value,
      shouldLoad: amortizationTypes.length > 0 && level2Value 
    });
    if (amortizationTypes.length > 0 && level2Value) {
      loadAmounts();
    } else {
      console.log('⚠️ [AmortizationConfigCard] loadAmounts non déclenché:', { 
        typesCount: amortizationTypes.length, 
        level2Value 
      });
    }
  }, [amortizationTypes, level2Value]);

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

  const loadLevel1Values = async () => {
    try {
      console.log('🔍 [AmortizationConfigCard] Chargement des valeurs level_1...', level2Value ? `(filtré par level_2=${level2Value})` : '');
      const response = await transactionsAPI.getUniqueValues('level_1', undefined, undefined, level2Value || undefined);
      console.log('✅ [AmortizationConfigCard] Valeurs level_1 reçues:', response.values);
      setLevel1Values(response.values || []);
    } catch (err: any) {
      console.error('❌ [AmortizationConfigCard] Erreur lors du chargement des valeurs level_1:', err);
      alert(`❌ Erreur lors du chargement des valeurs level_1: ${err.message || 'Erreur inconnue'}`);
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

  const loadAmortizationTypes = async () => {
    try {
      setLoadingTypes(true);
      const response = await amortizationTypesAPI.getAll();
      
      // Si aucun type n'existe, créer les 7 types initiaux
      if (response.types.length === 0 && level2Value) {
        await createInitialTypes();
        // Recharger après création
        const newResponse = await amortizationTypesAPI.getAll();
        setAmortizationTypes(newResponse.types);
      } else {
        setAmortizationTypes(response.types);
      }
    } catch (err: any) {
      console.error('Erreur lors du chargement des types d\'amortissement:', err);
    } finally {
      setLoadingTypes(false);
    }
  };

  const createInitialTypes = async () => {
    const initialTypes = [
      'Part terrain',
      'Immobilisation structure/GO',
      'Immobilisation mobilier',
      'Immobilisation IGT',
      'Immobilisation agencements',
      'Immobilisation Facade/Toiture',
      'Immobilisation travaux',
    ];

    for (const name of initialTypes) {
      try {
        await amortizationTypesAPI.create({
          name,
          level_2_value: level2Value,
          level_1_values: [],
          start_date: null,
          duration: 0,
          annual_amount: null,
        });
      } catch (err: any) {
        console.error(`Erreur lors de la création du type ${name}:`, err);
      }
    }
  };

  const handleNameEditStart = (type: AmortizationType) => {
    setEditingNameId(type.id);
    setEditingNameValue(type.name);
  };

  const handleNameEditSave = async (typeId: number) => {
    try {
      await amortizationTypesAPI.update(typeId, {
        name: editingNameValue,
      });
      // Recharger les types
      await loadAmortizationTypes();
      setEditingNameId(null);
      setEditingNameValue('');
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('Erreur lors de la sauvegarde du nom:', err);
      alert(`❌ Erreur lors de la sauvegarde: ${err.message || 'Erreur inconnue'}`);
    }
  };

  const handleNameEditCancel = () => {
    setEditingNameId(null);
    setEditingNameValue('');
  };

  const handleLevel1Add = async (typeId: number, value: string) => {
    if (!value) return;
    
    const type = amortizationTypes.find(t => t.id === typeId);
    if (!type) return;
    
    // Vérifier que la valeur n'est pas déjà présente
    const currentValues = type.level_1_values && Array.isArray(type.level_1_values) ? type.level_1_values : [];
    if (currentValues.includes(value)) return;
    
    try {
      const updatedValues = [...currentValues, value];
      console.log('💾 [AmortizationConfigCard] Ajout de valeur level_1:', value, 'pour type:', typeId, '→', updatedValues);
      await amortizationTypesAPI.update(typeId, {
        level_1_values: updatedValues,
      });
      await loadAmortizationTypes();
      // Recharger les montants après modification des level_1_values
      await loadAmounts();
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [AmortizationConfigCard] Erreur lors de l\'ajout de la valeur level_1:', err);
      alert(`❌ Erreur lors de l'ajout: ${err.message || 'Erreur inconnue'}`);
    }
  };

  const handleLevel1Remove = async (typeId: number, value: string) => {
    const type = amortizationTypes.find(t => t.id === typeId);
    if (!type) return;
    
    try {
      const currentValues = type.level_1_values && Array.isArray(type.level_1_values) ? type.level_1_values : [];
      const updatedValues = currentValues.filter(v => v !== value);
      console.log('🗑️ [AmortizationConfigCard] Suppression de valeur level_1:', value, 'pour type:', typeId, '→', updatedValues);
      await amortizationTypesAPI.update(typeId, {
        level_1_values: updatedValues,
      });
      await loadAmortizationTypes();
      // Recharger les montants après modification des level_1_values
      await loadAmounts();
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [AmortizationConfigCard] Erreur lors de la suppression de la valeur level_1:', err);
      alert(`❌ Erreur lors de la suppression: ${err.message || 'Erreur inconnue'}`);
    }
  };

  const handleDateEditStart = (type: AmortizationType) => {
    setEditingDateId(type.id);
    // Convertir la date en format YYYY-MM-DD pour l'input date
    if (type.start_date) {
      const date = new Date(type.start_date);
      setEditingDateValue(date.toISOString().split('T')[0]);
    } else {
      setEditingDateValue('');
    }
  };

  const handleDateEditSave = async (typeId: number) => {
    try {
      const dateValue = editingDateValue ? editingDateValue : null;
      console.log('💾 [AmortizationConfigCard] Sauvegarde de date de début:', dateValue, 'pour type:', typeId);
      await amortizationTypesAPI.update(typeId, {
        start_date: dateValue,
      });
      await loadAmortizationTypes();
      setEditingDateId(null);
      setEditingDateValue('');
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [AmortizationConfigCard] Erreur lors de la sauvegarde de la date:', err);
      alert(`❌ Erreur lors de la sauvegarde: ${err.message || 'Erreur inconnue'}`);
    }
  };

  const handleDateEditCancel = () => {
    setEditingDateId(null);
    setEditingDateValue('');
  };

  const handleDurationEditStart = (type: AmortizationType) => {
    setEditingDurationId(type.id);
    setEditingDurationValue(type.duration.toString());
  };

  const handleDurationEditSave = async (typeId: number) => {
    try {
      const durationValue = parseFloat(editingDurationValue);
      if (isNaN(durationValue) || durationValue < 0) {
        alert('⚠️ La durée doit être un nombre positif');
        setEditingDurationId(null);
        setEditingDurationValue('');
        return;
      }
      
      console.log('💾 [AmortizationConfigCard] Sauvegarde de durée:', durationValue, 'pour type:', typeId);
      
      // Recalculer l'annuité si le montant est disponible
      const type = amortizationTypes.find(t => t.id === typeId);
      const amount = amounts[typeId] || 0;
      let annualAmount: number | null = null;
      
      if (amount > 0 && durationValue > 0) {
        annualAmount = amount / durationValue;
        console.log('💰 [AmortizationConfigCard] Annuité recalculée:', annualAmount, '(Montant:', amount, '/ Durée:', durationValue, ')');
      }
      
      await amortizationTypesAPI.update(typeId, {
        duration: durationValue,
        annual_amount: annualAmount,
      });
      await loadAmortizationTypes();
      setEditingDurationId(null);
      setEditingDurationValue('');
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [AmortizationConfigCard] Erreur lors de la sauvegarde de la durée:', err);
      alert(`❌ Erreur lors de la sauvegarde: ${err.message || 'Erreur inconnue'}`);
    }
  };

  const handleDurationEditCancel = () => {
    setEditingDurationId(null);
    setEditingDurationValue('');
  };

  const loadAmounts = async () => {
    console.log('🔍 [AmortizationConfigCard] loadAmounts appelé', { level2Value, typesCount: amortizationTypes.length });
    if (!level2Value || amortizationTypes.length === 0) {
      console.log('⚠️ [AmortizationConfigCard] loadAmounts annulé: level2Value ou types manquants');
      return;
    }
    
    const newAmounts: Record<number, number> = {};
    const newLoadingAmounts: Record<number, boolean> = {};
    
    // Marquer tous les types comme en cours de chargement
    amortizationTypes.forEach(type => {
      newLoadingAmounts[type.id] = true;
    });
    setLoadingAmounts(newLoadingAmounts);
    
    console.log('📊 [AmortizationConfigCard] Calcul des montants pour', amortizationTypes.length, 'types');
    
    // Charger les montants pour tous les types en parallèle
    const promises = amortizationTypes.map(async (type) => {
      try {
        console.log(`📤 [AmortizationConfigCard] Appel API pour type ${type.id} (${type.name})`);
        const response = await amortizationTypesAPI.getAmount(type.id);
        console.log(`✅ [AmortizationConfigCard] Montant reçu pour type ${type.id}:`, response.amount);
        newAmounts[type.id] = response.amount;
      } catch (err: any) {
        console.error(`❌ [AmortizationConfigCard] Erreur lors du calcul du montant pour type ${type.id}:`, err);
        newAmounts[type.id] = 0;
      } finally {
        newLoadingAmounts[type.id] = false;
      }
    });
    
    await Promise.all(promises);
    console.log('💾 [AmortizationConfigCard] Montants calculés:', newAmounts);
    setAmounts(newAmounts);
    setLoadingAmounts(newLoadingAmounts);
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
      <div style={{ marginBottom: '24px' }}>
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

      {/* Tableau des types d'amortissement */}
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
              <th style={{ padding: '6px 8px', textAlign: 'left', fontWeight: '600', color: '#374151', borderRight: '1px solid #e5e7eb', fontSize: '13px' }}>
                Type d'immobilisation
              </th>
              <th style={{ padding: '6px 8px', textAlign: 'left', fontWeight: '600', color: '#374151', borderRight: '1px solid #e5e7eb', fontSize: '13px' }}>
                Level 1 (valeurs)
              </th>
              <th style={{ padding: '6px 8px', textAlign: 'left', fontWeight: '600', color: '#374151', borderRight: '1px solid #e5e7eb', fontSize: '13px' }}>
                Date de début
              </th>
              <th style={{ padding: '6px 8px', textAlign: 'right', fontWeight: '600', color: '#374151', borderRight: '1px solid #e5e7eb', fontSize: '13px' }}>
                Montant d'immobilisation
              </th>
              <th style={{ padding: '6px 8px', textAlign: 'right', fontWeight: '600', color: '#374151', borderRight: '1px solid #e5e7eb', fontSize: '13px' }}>
                Durée d'amortissement
              </th>
              <th style={{ padding: '6px 8px', textAlign: 'right', fontWeight: '600', color: '#374151', borderRight: '1px solid #e5e7eb', fontSize: '13px' }}>
                Annuité d'amortissement
              </th>
              <th style={{ padding: '6px 8px', textAlign: 'right', fontWeight: '600', color: '#374151', borderRight: '1px solid #e5e7eb', fontSize: '13px' }}>
                Montant cumulé
              </th>
              <th style={{ padding: '6px 8px', textAlign: 'right', fontWeight: '600', color: '#374151', fontSize: '13px' }}>
                VNC
              </th>
            </tr>
          </thead>
          <tbody>
            {loadingTypes ? (
              <tr>
                <td colSpan={8} style={{ padding: '24px', textAlign: 'center', color: '#6b7280', fontSize: '14px' }}>
                  ⏳ Chargement des types d'amortissement...
                </td>
              </tr>
            ) : amortizationTypes.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ padding: '24px', textAlign: 'center', color: '#6b7280', fontSize: '14px', fontStyle: 'italic' }}>
                  Aucun type d'amortissement configuré
                </td>
              </tr>
            ) : (
              amortizationTypes.map((type) => (
                <tr key={type.id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                  {/* Colonne Type d'immobilisation */}
                  <td style={{ padding: '6px 8px', borderRight: '1px solid #e5e7eb' }}>
                    {editingNameId === type.id ? (
                      <input
                        type="text"
                        value={editingNameValue}
                        onChange={(e) => setEditingNameValue(e.target.value)}
                        onBlur={() => handleNameEditSave(type.id)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            handleNameEditSave(type.id);
                          } else if (e.key === 'Escape') {
                            handleNameEditCancel();
                          }
                        }}
                        autoFocus
                        style={{
                          width: '100%',
                          padding: '4px 6px',
                          fontSize: '13px',
                          border: '1px solid #3b82f6',
                          borderRadius: '4px',
                          backgroundColor: '#ffffff',
                        }}
                      />
                    ) : (
                      <div
                        onClick={() => handleNameEditStart(type)}
                        style={{
                          padding: '4px 6px',
                          cursor: 'pointer',
                          borderRadius: '4px',
                          transition: 'background-color 0.2s',
                          fontSize: '13px',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = '#f3f4f6';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'transparent';
                        }}
                        title="Cliquer pour éditer"
                      >
                        {type.name}
                      </div>
                    )}
                  </td>
                  {/* Colonne Level 1 (valeurs) */}
                  <td style={{ padding: '6px 8px', borderRight: '1px solid #e5e7eb', fontSize: '13px' }}>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', alignItems: 'center' }}>
                      {/* Tags des valeurs sélectionnées */}
                      {type.level_1_values && Array.isArray(type.level_1_values) && type.level_1_values.length > 0 ? (
                        type.level_1_values.map((value) => (
                          <span
                            key={value}
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              padding: '2px 6px',
                              backgroundColor: '#3b82f6',
                              color: '#ffffff',
                              borderRadius: '4px',
                              fontSize: '11px',
                              gap: '4px',
                            }}
                          >
                            {value}
                            <button
                              onClick={() => handleLevel1Remove(type.id, value)}
                              style={{
                                background: 'none',
                                border: 'none',
                                color: '#ffffff',
                                cursor: 'pointer',
                                padding: '0',
                                marginLeft: '4px',
                                fontSize: '12px',
                                fontWeight: 'bold',
                                lineHeight: '1',
                              }}
                              title="Supprimer"
                            >
                              ×
                            </button>
                          </span>
                        ))
                      ) : (
                        <span style={{ color: '#9ca3af', fontStyle: 'italic', fontSize: '12px' }}>
                          Aucune valeur
                        </span>
                      )}
                      {/* Dropdown pour ajouter une valeur */}
                      {editingLevel1Id === type.id ? (
                        <select
                          onChange={(e) => {
                            if (e.target.value) {
                              handleLevel1Add(type.id, e.target.value);
                              setEditingLevel1Id(null);
                            }
                          }}
                          onBlur={() => setEditingLevel1Id(null)}
                          autoFocus
                          style={{
                            padding: '2px 6px',
                            fontSize: '12px',
                            border: '1px solid #3b82f6',
                            borderRadius: '4px',
                            backgroundColor: '#ffffff',
                            minWidth: '120px',
                          }}
                        >
                          <option value="">Sélectionner...</option>
                          {level1Values
                            .filter(v => !(type.level_1_values && Array.isArray(type.level_1_values) && type.level_1_values.includes(v)))
                            .map((value) => (
                              <option key={value} value={value}>
                                {value}
                              </option>
                            ))}
                        </select>
                      ) : (
                        <button
                          onClick={() => {
                            console.log('🔍 [AmortizationConfigCard] Clic sur "+ Ajouter" pour type:', type.id);
                            console.log('🔍 [AmortizationConfigCard] level1Values:', level1Values);
                            console.log('🔍 [AmortizationConfigCard] type.level_1_values:', type.level_1_values);
                            const currentValues = type.level_1_values && Array.isArray(type.level_1_values) ? type.level_1_values : [];
                            const availableValues = level1Values.filter(v => !currentValues.includes(v));
                            console.log('🔍 [AmortizationConfigCard] Valeurs disponibles:', availableValues);
                            if (availableValues.length > 0) {
                              setEditingLevel1Id(type.id);
                            } else {
                              alert('⚠️ Toutes les valeurs level_1 sont déjà assignées à ce type, ou aucune valeur level_1 n\'est disponible dans les transactions.');
                            }
                          }}
                          disabled={level1Values.length === 0 || level1Values.filter(v => !(type.level_1_values && Array.isArray(type.level_1_values) && type.level_1_values.includes(v))).length === 0}
                          style={{
                            padding: '2px 6px',
                            fontSize: '11px',
                            border: '1px solid #d1d5db',
                            borderRadius: '4px',
                            backgroundColor: '#f9fafb',
                            color: '#374151',
                            cursor: (level1Values.length > 0 && level1Values.filter(v => !(type.level_1_values && Array.isArray(type.level_1_values) && type.level_1_values.includes(v))).length > 0) ? 'pointer' : 'not-allowed',
                            opacity: (level1Values.length > 0 && level1Values.filter(v => !(type.level_1_values && Array.isArray(type.level_1_values) && type.level_1_values.includes(v))).length > 0) ? 1 : 0.5,
                          }}
                          title={level1Values.length === 0 
                            ? "Aucune valeur level_1 disponible dans les transactions" 
                            : level1Values.filter(v => !(type.level_1_values && Array.isArray(type.level_1_values) && type.level_1_values.includes(v))).length === 0
                            ? "Toutes les valeurs sont déjà assignées"
                            : "Ajouter une valeur"}
                        >
                          + Ajouter
                        </button>
                      )}
                    </div>
                  </td>
                  {/* Colonne Date de début */}
                  <td style={{ padding: '6px 8px', borderRight: '1px solid #e5e7eb', fontSize: '13px' }}>
                    {editingDateId === type.id ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <input
                          type="date"
                          value={editingDateValue}
                          onChange={(e) => setEditingDateValue(e.target.value)}
                          onBlur={() => handleDateEditSave(type.id)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              handleDateEditSave(type.id);
                            } else if (e.key === 'Escape') {
                              handleDateEditCancel();
                            }
                          }}
                          autoFocus
                          style={{
                            flex: '1',
                            padding: '4px 6px',
                            fontSize: '12px',
                            border: '1px solid #3b82f6',
                            borderRadius: '4px',
                            backgroundColor: '#ffffff',
                          }}
                        />
                        <button
                          onClick={() => {
                            setEditingDateValue('');
                            handleDateEditSave(type.id);
                          }}
                          style={{
                            padding: '2px 6px',
                            fontSize: '11px',
                            border: '1px solid #dc2626',
                            borderRadius: '4px',
                            backgroundColor: '#fee2e2',
                            color: '#dc2626',
                            cursor: 'pointer',
                          }}
                          title="Supprimer la date"
                        >
                          ×
                        </button>
                      </div>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <div
                          onClick={() => handleDateEditStart(type)}
                          style={{
                            flex: '1',
                            padding: '4px 6px',
                            cursor: 'pointer',
                            borderRadius: '4px',
                            transition: 'background-color 0.2s',
                            fontSize: '13px',
                            color: type.start_date ? '#111827' : '#9ca3af',
                            fontStyle: type.start_date ? 'normal' : 'italic',
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.backgroundColor = '#f3f4f6';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.backgroundColor = 'transparent';
                          }}
                          title="Cliquer pour éditer"
                        >
                          {type.start_date 
                            ? new Date(type.start_date).toLocaleDateString('fr-FR', { year: 'numeric', month: '2-digit', day: '2-digit' })
                            : 'Aucune date'}
                        </div>
                        {type.start_date && (
                          <button
                            onClick={async (e) => {
                              e.stopPropagation();
                              try {
                                console.log('🗑️ [AmortizationConfigCard] Suppression de date pour type:', type.id);
                                const updateData: { start_date: null } = { start_date: null };
                                console.log('📤 [AmortizationConfigCard] Données envoyées:', JSON.stringify(updateData));
                                await amortizationTypesAPI.update(type.id, updateData);
                                console.log('✅ [AmortizationConfigCard] Date supprimée avec succès');
                                await loadAmortizationTypes();
                                if (onConfigUpdated) {
                                  onConfigUpdated();
                                }
                              } catch (err: any) {
                                console.error('❌ [AmortizationConfigCard] Erreur lors de la suppression de la date:', err);
                                alert(`❌ Erreur lors de la suppression: ${err.message || 'Erreur inconnue'}`);
                              }
                            }}
                            style={{
                              padding: '2px 6px',
                              fontSize: '11px',
                              border: '1px solid #dc2626',
                              borderRadius: '4px',
                              backgroundColor: '#fee2e2',
                              color: '#dc2626',
                              cursor: 'pointer',
                            }}
                            title="Supprimer la date"
                          >
                            ×
                          </button>
                        )}
                      </div>
                    )}
                  </td>
                  {/* Colonne Montant d'immobilisation */}
                  <td style={{ padding: '6px 8px', borderRight: '1px solid #e5e7eb', textAlign: 'right', fontSize: '13px', fontWeight: '500' }}>
                    {loadingAmounts[type.id] ? (
                      <span style={{ color: '#9ca3af', fontStyle: 'italic' }}>⏳ Calcul...</span>
                    ) : (
                      <span style={{ color: '#111827' }}>
                        {amounts[type.id] !== undefined 
                          ? new Intl.NumberFormat('fr-FR', { 
                              style: 'currency', 
                              currency: 'EUR',
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2
                            }).format(amounts[type.id])
                          : '0,00 €'}
                      </span>
                    )}
                  </td>
                  {/* Colonne Durée d'amortissement */}
                  <td style={{ padding: '6px 8px', borderRight: '1px solid #e5e7eb', textAlign: 'right', fontSize: '13px' }}>
                    {editingDurationId === type.id ? (
                      <input
                        type="number"
                        value={editingDurationValue}
                        onChange={(e) => setEditingDurationValue(e.target.value)}
                        onBlur={() => handleDurationEditSave(type.id)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            handleDurationEditSave(type.id);
                          } else if (e.key === 'Escape') {
                            handleDurationEditCancel();
                          }
                        }}
                        autoFocus
                        min="0"
                        step="0.1"
                        style={{
                          width: '100%',
                          padding: '4px 6px',
                          fontSize: '12px',
                          border: '1px solid #3b82f6',
                          borderRadius: '4px',
                          backgroundColor: '#ffffff',
                          textAlign: 'right',
                        }}
                      />
                    ) : (
                      <div
                        onClick={() => handleDurationEditStart(type)}
                        style={{
                          padding: '4px 6px',
                          cursor: 'pointer',
                          borderRadius: '4px',
                          transition: 'background-color 0.2s',
                          fontSize: '13px',
                          color: type.duration > 0 ? '#111827' : '#9ca3af',
                          fontStyle: type.duration > 0 ? 'normal' : 'italic',
                          textAlign: 'right',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = '#f3f4f6';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'transparent';
                        }}
                        title="Cliquer pour éditer"
                      >
                        {type.duration > 0 ? `${type.duration} ans` : '0 ans'}
                      </div>
                    )}
                  </td>
                  {/* Colonnes suivantes à venir dans les prochaines étapes */}
                  <td style={{ padding: '6px 8px', borderRight: '1px solid #e5e7eb', textAlign: 'right', color: '#9ca3af', fontSize: '13px' }}>
                    -
                  </td>
                  <td style={{ padding: '6px 8px', borderRight: '1px solid #e5e7eb', textAlign: 'right', color: '#9ca3af', fontSize: '13px' }}>
                    -
                  </td>
                  <td style={{ padding: '6px 8px', textAlign: 'right', color: '#9ca3af', fontSize: '13px' }}>
                    -
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

