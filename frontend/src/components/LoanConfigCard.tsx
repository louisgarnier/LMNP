/**
 * LoanConfigCard component - Card de configuration des crédits
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect } from 'react';
import { loanConfigsAPI, loanPaymentsAPI, LoanConfig } from '@/api/client';

interface LoanConfigCardProps {
  onConfigsChange?: () => void;
}

export default function LoanConfigCard({ onConfigsChange }: LoanConfigCardProps) {
  const [loanConfigs, setLoanConfigs] = useState<LoanConfig[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState<Record<number, boolean>>({});
  const [editingNameId, setEditingNameId] = useState<number | null>(null);
  const [editingNameValue, setEditingNameValue] = useState<string>('');
  const [editingCreditAmountId, setEditingCreditAmountId] = useState<number | null>(null);
  const [editingCreditAmountValue, setEditingCreditAmountValue] = useState<string>('');
  const [editingInterestRateId, setEditingInterestRateId] = useState<number | null>(null);
  const [editingInterestRateValue, setEditingInterestRateValue] = useState<string>('');
  const [editingDurationId, setEditingDurationId] = useState<number | null>(null);
  const [editingDurationValue, setEditingDurationValue] = useState<string>('');
  const [editingDeferralId, setEditingDeferralId] = useState<number | null>(null);
  const [editingDeferralValue, setEditingDeferralValue] = useState<string>('');

  // Charger les configurations au montage
  useEffect(() => {
    loadLoanConfigs();
  }, []);

  const loadLoanConfigs = async () => {
    setLoading(true);
    try {
      const response = await loanConfigsAPI.getAll();
      setLoanConfigs(response.configs);
    } catch (error) {
      console.error('Erreur lors du chargement des configurations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (config: LoanConfig) => {
    if (saving[config.id]) return;
    
    setSaving(prev => ({ ...prev, [config.id]: true }));
    try {
      await loanConfigsAPI.update(config.id, {
        name: config.name,
        credit_amount: config.credit_amount,
        interest_rate: config.interest_rate,
        duration_years: config.duration_years,
        initial_deferral_months: config.initial_deferral_months,
      });
      await loadLoanConfigs();
      if (onConfigsChange) {
        onConfigsChange();
      }
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
      alert('❌ Erreur lors de la sauvegarde');
    } finally {
      setSaving(prev => ({ ...prev, [config.id]: false }));
    }
  };

  const handleCreate = async () => {
    try {
      const newConfig = await loanConfigsAPI.create({
        name: 'Nouveau crédit',
        credit_amount: 100000, // Valeur par défaut valide (> 0)
        interest_rate: 1.5, // Valeur par défaut valide (> 0)
        duration_years: 20, // Valeur par défaut valide (> 0)
        initial_deferral_months: 0, // Peut être 0
      });
      await loadLoanConfigs();
      // Mettre en mode édition pour le nom
      setEditingNameId(newConfig.id);
      setEditingNameValue(newConfig.name);
      if (onConfigsChange) {
        onConfigsChange();
      }
    } catch (error) {
      console.error('Erreur lors de la création:', error);
      alert('❌ Erreur lors de la création');
    }
  };

  const handleDelete = async (id: number) => {
    const configToDelete = loanConfigs.find(c => c.id === id);
    if (!configToDelete) return;

    // Vérifier s'il y a des mensualités associées
    try {
      const paymentsResponse = await loanPaymentsAPI.getAll({ loan_name: configToDelete.name });
      const hasPayments = paymentsResponse.payments.length > 0;

      let confirmMessage = 'Êtes-vous sûr de vouloir supprimer cette configuration de crédit ?';
      if (hasPayments) {
        confirmMessage = `⚠️ Cette configuration de crédit a ${paymentsResponse.payments.length} mensualité(s) associée(s).\n\nToutes les mensualités seront également supprimées.\n\nÊtes-vous sûr de vouloir continuer ?`;
      }

      if (!confirm(confirmMessage)) {
        return;
      }

      // Supprimer toutes les mensualités associées
      if (hasPayments) {
        const deletePromises = paymentsResponse.payments.map(p => loanPaymentsAPI.delete(p.id));
        await Promise.all(deletePromises);
      }

      // Supprimer la configuration
      await loanConfigsAPI.delete(id);
      await loadLoanConfigs();
      
      if (onConfigsChange) {
        onConfigsChange();
      }
    } catch (error) {
      console.error('Erreur lors de la suppression:', error);
      alert('❌ Erreur lors de la suppression');
    }
  };

  const handleNameEditStart = (config: LoanConfig) => {
    setEditingNameId(config.id);
    setEditingNameValue(config.name);
  };

  const handleNameEditSave = async (config: LoanConfig) => {
    const updatedConfig = { ...config, name: editingNameValue };
    setLoanConfigs(prev => prev.map(c => c.id === config.id ? updatedConfig : c));
    setEditingNameId(null);
    await handleSave(updatedConfig);
  };

  const handleCreditAmountEditStart = (config: LoanConfig) => {
    setEditingCreditAmountId(config.id);
    setEditingCreditAmountValue(config.credit_amount.toString());
  };

  const handleCreditAmountEditSave = async (config: LoanConfig) => {
    const value = parseFloat(editingCreditAmountValue) || 0;
    const updatedConfig = { ...config, credit_amount: value };
    setLoanConfigs(prev => prev.map(c => c.id === config.id ? updatedConfig : c));
    setEditingCreditAmountId(null);
    await handleSave(updatedConfig);
  };

  const handleInterestRateEditStart = (config: LoanConfig) => {
    setEditingInterestRateId(config.id);
    setEditingInterestRateValue(config.interest_rate.toString());
  };

  const handleInterestRateEditSave = async (config: LoanConfig) => {
    const value = parseFloat(editingInterestRateValue) || 0;
    const updatedConfig = { ...config, interest_rate: value };
    setLoanConfigs(prev => prev.map(c => c.id === config.id ? updatedConfig : c));
    setEditingInterestRateId(null);
    await handleSave(updatedConfig);
  };

  const handleDurationEditStart = (config: LoanConfig) => {
    setEditingDurationId(config.id);
    setEditingDurationValue(config.duration_years.toString());
  };

  const handleDurationEditSave = async (config: LoanConfig) => {
    const value = parseInt(editingDurationValue) || 0;
    const updatedConfig = { ...config, duration_years: value };
    setLoanConfigs(prev => prev.map(c => c.id === config.id ? updatedConfig : c));
    setEditingDurationId(null);
    await handleSave(updatedConfig);
  };

  const handleDeferralEditStart = (config: LoanConfig) => {
    setEditingDeferralId(config.id);
    setEditingDeferralValue(config.initial_deferral_months.toString());
  };

  const handleDeferralEditSave = async (config: LoanConfig) => {
    const value = parseInt(editingDeferralValue) || 0;
    const updatedConfig = { ...config, initial_deferral_months: value };
    setLoanConfigs(prev => prev.map(c => c.id === config.id ? updatedConfig : c));
    setEditingDeferralId(null);
    await handleSave(updatedConfig);
  };

  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '8px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      padding: '24px',
      marginBottom: '24px'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h2 style={{ fontSize: '18px', fontWeight: '600', color: '#111827' }}>
          Configuration des crédits
        </h2>
        <button
          onClick={handleCreate}
          style={{
            padding: '8px 16px',
            fontSize: '14px',
            fontWeight: '600',
            color: '#ffffff',
            backgroundColor: '#3b82f6',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
          }}
        >
          + Ajouter un crédit
        </button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '20px', color: '#6b7280' }}>
          Chargement...
        </div>
      ) : loanConfigs.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '20px', color: '#6b7280' }}>
          Aucune configuration de crédit. Cliquez sur "Ajouter un crédit" pour en créer une.
        </div>
      ) : (
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
                <th style={{ padding: '8px', textAlign: 'left', fontWeight: '600', color: '#374151', borderRight: '1px solid #e5e7eb' }}>
                  Nom du crédit
                </th>
                <th style={{ padding: '8px', textAlign: 'right', fontWeight: '600', color: '#374151', borderRight: '1px solid #e5e7eb' }}>
                  Crédit accordé (€)
                </th>
                <th style={{ padding: '8px', textAlign: 'right', fontWeight: '600', color: '#374151', borderRight: '1px solid #e5e7eb' }}>
                  Taux fixe (hors assurance) (%)
                </th>
                <th style={{ padding: '8px', textAlign: 'right', fontWeight: '600', color: '#374151', borderRight: '1px solid #e5e7eb' }}>
                  Durée emprunt (ans)
                </th>
                <th style={{ padding: '8px', textAlign: 'right', fontWeight: '600', color: '#374151', borderRight: '1px solid #e5e7eb' }}>
                  Décalage initial (mois)
                </th>
                <th style={{ padding: '8px', textAlign: 'center', fontWeight: '600', color: '#374151' }}>
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {loanConfigs.map((config) => (
                <tr key={config.id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                  {/* Nom du crédit */}
                  <td style={{ padding: '8px', borderRight: '1px solid #e5e7eb' }}>
                    {editingNameId === config.id ? (
                      <input
                        type="text"
                        value={editingNameValue}
                        onChange={(e) => setEditingNameValue(e.target.value)}
                        onBlur={() => handleNameEditSave(config)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            handleNameEditSave(config);
                          } else if (e.key === 'Escape') {
                            setEditingNameId(null);
                          }
                        }}
                        autoFocus
                        style={{
                          width: '100%',
                          padding: '4px 8px',
                          fontSize: '14px',
                          border: '1px solid #3b82f6',
                          borderRadius: '4px',
                        }}
                      />
                    ) : (
                      <span
                        onClick={() => handleNameEditStart(config)}
                        style={{
                          cursor: 'pointer',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          display: 'inline-block',
                          width: '100%',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = '#f3f4f6';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'transparent';
                        }}
                      >
                        {config.name}
                      </span>
                    )}
                  </td>

                  {/* Crédit accordé */}
                  <td style={{ padding: '8px', textAlign: 'right', borderRight: '1px solid #e5e7eb' }}>
                    {editingCreditAmountId === config.id ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <input
                          type="number"
                          step="0.01"
                          value={editingCreditAmountValue}
                          onChange={(e) => setEditingCreditAmountValue(e.target.value)}
                          onBlur={() => handleCreditAmountEditSave(config)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              handleCreditAmountEditSave(config);
                            } else if (e.key === 'Escape') {
                              setEditingCreditAmountId(null);
                            }
                          }}
                          autoFocus
                          style={{
                            width: '100%',
                            padding: '4px 8px',
                            fontSize: '14px',
                            border: '1px solid #3b82f6',
                            borderRadius: '4px',
                            textAlign: 'right',
                          }}
                        />
                        <span style={{ fontSize: '12px', color: '#6b7280' }}>€</span>
                      </div>
                    ) : (
                      <span
                        onClick={() => handleCreditAmountEditStart(config)}
                        style={{
                          cursor: 'pointer',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          display: 'inline-block',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = '#f3f4f6';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'transparent';
                        }}
                      >
                        {config.credit_amount.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €
                      </span>
                    )}
                  </td>

                  {/* Taux fixe */}
                  <td style={{ padding: '8px', textAlign: 'right', borderRight: '1px solid #e5e7eb' }}>
                    {editingInterestRateId === config.id ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <input
                          type="number"
                          step="0.01"
                          value={editingInterestRateValue}
                          onChange={(e) => setEditingInterestRateValue(e.target.value)}
                          onBlur={() => handleInterestRateEditSave(config)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              handleInterestRateEditSave(config);
                            } else if (e.key === 'Escape') {
                              setEditingInterestRateId(null);
                            }
                          }}
                          autoFocus
                          style={{
                            width: '100%',
                            padding: '4px 8px',
                            fontSize: '14px',
                            border: '1px solid #3b82f6',
                            borderRadius: '4px',
                            textAlign: 'right',
                          }}
                        />
                        <span style={{ fontSize: '12px', color: '#6b7280' }}>%</span>
                      </div>
                    ) : (
                      <span
                        onClick={() => handleInterestRateEditStart(config)}
                        style={{
                          cursor: 'pointer',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          display: 'inline-block',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = '#f3f4f6';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'transparent';
                        }}
                      >
                        {config.interest_rate.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} %
                      </span>
                    )}
                  </td>

                  {/* Durée emprunt */}
                  <td style={{ padding: '8px', textAlign: 'right', borderRight: '1px solid #e5e7eb' }}>
                    {editingDurationId === config.id ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <input
                          type="number"
                          step="1"
                          value={editingDurationValue}
                          onChange={(e) => setEditingDurationValue(e.target.value)}
                          onBlur={() => handleDurationEditSave(config)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              handleDurationEditSave(config);
                            } else if (e.key === 'Escape') {
                              setEditingDurationId(null);
                            }
                          }}
                          autoFocus
                          style={{
                            width: '100%',
                            padding: '4px 8px',
                            fontSize: '14px',
                            border: '1px solid #3b82f6',
                            borderRadius: '4px',
                            textAlign: 'right',
                          }}
                        />
                        <span style={{ fontSize: '12px', color: '#6b7280' }}>ans</span>
                      </div>
                    ) : (
                      <span
                        onClick={() => handleDurationEditStart(config)}
                        style={{
                          cursor: 'pointer',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          display: 'inline-block',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = '#f3f4f6';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'transparent';
                        }}
                      >
                        {config.duration_years} ans
                      </span>
                    )}
                  </td>

                  {/* Décalage initial */}
                  <td style={{ padding: '8px', textAlign: 'right', borderRight: '1px solid #e5e7eb' }}>
                    {editingDeferralId === config.id ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <input
                          type="number"
                          step="1"
                          value={editingDeferralValue}
                          onChange={(e) => setEditingDeferralValue(e.target.value)}
                          onBlur={() => handleDeferralEditSave(config)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              handleDeferralEditSave(config);
                            } else if (e.key === 'Escape') {
                              setEditingDeferralId(null);
                            }
                          }}
                          autoFocus
                          style={{
                            width: '100%',
                            padding: '4px 8px',
                            fontSize: '14px',
                            border: '1px solid #3b82f6',
                            borderRadius: '4px',
                            textAlign: 'right',
                          }}
                        />
                        <span style={{ fontSize: '12px', color: '#6b7280' }}>mois</span>
                      </div>
                    ) : (
                      <span
                        onClick={() => handleDeferralEditStart(config)}
                        style={{
                          cursor: 'pointer',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          display: 'inline-block',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = '#f3f4f6';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'transparent';
                        }}
                      >
                        {config.initial_deferral_months} mois
                      </span>
                    )}
                  </td>

                  {/* Actions */}
                  <td style={{ padding: '8px', textAlign: 'center' }}>
                    <button
                      onClick={() => handleDelete(config.id)}
                      style={{
                        padding: '4px 8px',
                        fontSize: '12px',
                        color: '#dc2626',
                        backgroundColor: 'transparent',
                        border: '1px solid #dc2626',
                        borderRadius: '4px',
                        cursor: 'pointer',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = '#fee2e2';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = 'transparent';
                      }}
                    >
                      Supprimer
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

