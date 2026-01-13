/**
 * LoanConfigCard - Card de configuration des crédits
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect } from 'react';
import { loanConfigsAPI, LoanConfig, LoanConfigCreate, loanPaymentsAPI } from '@/api/client';

interface LoanConfigCardProps {
  onConfigUpdated?: () => void;
}

const STORAGE_KEY_LOAN_CONFIG_COLLAPSED = 'loan_config_card_collapsed';

export default function LoanConfigCard({ onConfigUpdated }: LoanConfigCardProps) {
  const [configs, setConfigs] = useState<LoanConfig[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<{ [key: number]: boolean }>({});
  const [errors, setErrors] = useState<{ [key: number]: string; global?: string }>({});
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);

  // Charger les configurations au montage
  useEffect(() => {
    loadConfigs();
    
    // Charger l'état collapsed depuis localStorage
    try {
      const savedCollapsed = localStorage.getItem(STORAGE_KEY_LOAN_CONFIG_COLLAPSED);
      if (savedCollapsed !== null) {
        setIsCollapsed(savedCollapsed === 'true');
      }
    } catch (err) {
      console.error('Erreur lors du chargement de l\'état collapsed:', err);
    }
  }, []);

  const loadConfigs = async () => {
    try {
      setLoading(true);
      const response = await loanConfigsAPI.getAll();
      setConfigs(response.items);
    } catch (error) {
      console.error('Erreur lors du chargement des configurations:', error);
      setErrors({ global: 'Erreur lors du chargement des configurations' });
    } finally {
      setLoading(false);
    }
  };

  const handleFieldChange = (id: number | 'new', field: string, value: string | number) => {
    if (id === 'new') {
      // Pour une nouvelle configuration, on ne fait rien ici
      // Elle sera créée lors du blur
      return;
    }

    setConfigs(prevConfigs =>
      prevConfigs.map(config =>
        config.id === id
          ? { ...config, [field]: value }
          : config
      )
    );
  };

  const handleFieldBlur = async (id: number, field: string, value: string | number) => {
    if (saving[id]) return; // Éviter les appels multiples

    try {
      setSaving(prev => ({ ...prev, [id]: true }));
      setErrors(prev => ({ ...prev, [id]: '' }));

      const config = configs.find(c => c.id === id);
      if (!config) return;

      const updateData: any = { [field]: value };
      
      await loanConfigsAPI.update(id, updateData);
      
      // Recharger pour avoir les données à jour
      await loadConfigs();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (error: any) {
      console.error(`Erreur lors de la sauvegarde du champ ${field}:`, error);
      setErrors(prev => ({
        ...prev,
        [id]: error.message || 'Erreur lors de la sauvegarde'
      }));
    } finally {
      setSaving(prev => ({ ...prev, [id]: false }));
    }
  };

  const handleAddConfig = async () => {
    try {
      const newConfig: LoanConfigCreate = {
        name: 'Nouveau crédit',
        credit_amount: 0,
        interest_rate: 0,
        duration_years: 0,
        initial_deferral_months: 0
      };

      const created = await loanConfigsAPI.create(newConfig);
      await loadConfigs();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (error: any) {
      console.error('Erreur lors de la création de la configuration:', error);
      setErrors(prev => ({
        ...prev,
        global: error.message || 'Erreur lors de la création'
      }));
    }
  };

  const handleDeleteConfig = async (id: number) => {
    const config = configs.find(c => c.id === id);
    if (!config) return;

    // Vérifier s'il y a des mensualités associées
    let hasPayments = false;
    try {
      const paymentsResponse = await loanPaymentsAPI.getAll({ loan_name: config.name, limit: 1 });
      hasPayments = paymentsResponse.items.length > 0;
    } catch (err) {
      console.error('Erreur lors de la vérification des mensualités:', err);
    }

    // Message de confirmation avec information sur les mensualités
    const confirmMessage = hasPayments
      ? `Êtes-vous sûr de vouloir supprimer le crédit "${config.name}" ?\n\nToutes les mensualités associées (${hasPayments ? 'au moins une' : 'aucune'}) seront également supprimées.`
      : `Êtes-vous sûr de vouloir supprimer le crédit "${config.name}" ?`;

    if (!window.confirm(confirmMessage)) {
      return;
    }

    try {
      // Supprimer toutes les mensualités associées
      if (hasPayments) {
        try {
          const allPayments = await loanPaymentsAPI.getAll({ loan_name: config.name, limit: 1000 });
          const deletePromises = allPayments.items.map(payment => loanPaymentsAPI.delete(payment.id));
          await Promise.all(deletePromises);
          console.log(`✅ ${allPayments.items.length} mensualité(s) supprimée(s) pour le crédit "${config.name}"`);
        } catch (err) {
          console.error('Erreur lors de la suppression des mensualités:', err);
          // Continuer quand même avec la suppression de la config
        }
      }

      // Supprimer la configuration
      await loanConfigsAPI.delete(id);
      await loadConfigs();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (error: any) {
      console.error('Erreur lors de la suppression:', error);
      setErrors(prev => ({
        ...prev,
        [id]: error.message || 'Erreur lors de la suppression'
      }));
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center', color: '#6b7280' }}>
        Chargement des configurations...
      </div>
    );
  }

  const handleToggleCollapse = () => {
    const newCollapsed = !isCollapsed;
    setIsCollapsed(newCollapsed);
    try {
      localStorage.setItem(STORAGE_KEY_LOAN_CONFIG_COLLAPSED, String(newCollapsed));
    } catch (err) {
      console.error('Erreur lors de la sauvegarde de l\'état collapsed:', err);
    }
  };

  return (
    <div style={{ 
      backgroundColor: 'white', 
      borderRadius: '8px', 
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      padding: '24px'
    }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: isCollapsed ? '0' : '24px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <h3 style={{ 
            fontSize: '18px', 
            fontWeight: '600', 
            color: '#1a1a1a',
            margin: 0
          }}>
            Configurations de crédit
          </h3>
          <button
            onClick={handleToggleCollapse}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '32px',
              height: '32px',
              backgroundColor: 'transparent',
              border: '1px solid #e5e7eb',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '16px',
              transition: 'all 0.2s',
              padding: 0
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.backgroundColor = '#f9fafb';
              e.currentTarget.style.borderColor = '#d1d5db';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.borderColor = '#e5e7eb';
            }}
            title={isCollapsed ? 'Déplier la card' : 'Replier la card'}
          >
            {isCollapsed ? '📍' : '📌'}
          </button>
        </div>
        {!isCollapsed && (
          <button
            onClick={handleAddConfig}
            style={{
              padding: '8px 16px',
              backgroundColor: '#1e3a5f',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'background-color 0.2s'
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#2d4a6f'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#1e3a5f'}
          >
            + Ajouter un crédit
          </button>
        )}
      </div>

      {!isCollapsed && (
        <>
          {errors.global && (
            <div style={{
              padding: '12px',
              backgroundColor: '#fee2e2',
              color: '#dc2626',
              borderRadius: '4px',
              marginBottom: '16px',
              fontSize: '14px'
            }}>
              {errors.global}
            </div>
          )}

          {configs.length === 0 ? (
            <div style={{ 
              padding: '24px', 
              textAlign: 'center', 
              color: '#6b7280',
              fontSize: '14px'
            }}>
              Aucune configuration de crédit. Cliquez sur "Ajouter un crédit" pour en créer une.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {configs.map((config) => (
            <div
              key={config.id}
              style={{
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                padding: '20px',
                backgroundColor: '#f9fafb'
              }}
            >
              <div style={{ 
                display: 'flex', 
                justifyContent: 'flex-end',
                alignItems: 'center',
                marginBottom: '16px'
              }}>
                <button
                  onClick={() => handleDeleteConfig(config.id)}
                  style={{
                    padding: '6px 12px',
                    backgroundColor: '#dc2626',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    fontSize: '12px',
                    fontWeight: '500',
                    cursor: 'pointer',
                    transition: 'background-color 0.2s'
                  }}
                  onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#b91c1c'}
                  onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#dc2626'}
                >
                  Supprimer
                </button>
              </div>

              {errors[config.id] && (
                <div style={{
                  padding: '8px',
                  backgroundColor: '#fee2e2',
                  color: '#dc2626',
                  borderRadius: '4px',
                  marginBottom: '12px',
                  fontSize: '12px'
                }}>
                  {errors[config.id]}
                </div>
              )}

              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '16px'
              }}>
                {/* Nom du crédit */}
                <div>
                  <label style={{ 
                    display: 'block', 
                    fontSize: '12px', 
                    fontWeight: '500', 
                    color: '#374151',
                    marginBottom: '6px'
                  }}>
                    Nom du crédit
                  </label>
                  <input
                    type="text"
                    value={config.name}
                    onChange={(e) => handleFieldChange(config.id, 'name', e.target.value)}
                    onBlur={(e) => handleFieldBlur(config.id, 'name', e.target.value)}
                    disabled={saving[config.id]}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '4px',
                      fontSize: '14px',
                      backgroundColor: saving[config.id] ? '#f3f4f6' : 'white'
                    }}
                  />
                </div>

                {/* Crédit accordé */}
                <div>
                  <label style={{ 
                    display: 'block', 
                    fontSize: '12px', 
                    fontWeight: '500', 
                    color: '#374151',
                    marginBottom: '6px'
                  }}>
                    Crédit accordé (€)
                  </label>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={config.credit_amount}
                      onChange={(e) => handleFieldChange(config.id, 'credit_amount', parseFloat(e.target.value) || 0)}
                      onBlur={(e) => handleFieldBlur(config.id, 'credit_amount', parseFloat(e.target.value) || 0)}
                      disabled={saving[config.id]}
                      style={{
                        flex: 1,
                        padding: '8px 12px',
                        border: '1px solid #d1d5db',
                        borderRadius: '4px',
                        fontSize: '14px',
                        backgroundColor: saving[config.id] ? '#f3f4f6' : 'white'
                      }}
                    />
                    <span style={{ fontSize: '14px', color: '#6b7280' }}>€</span>
                  </div>
                </div>

                {/* Taux fixe */}
                <div>
                  <label style={{ 
                    display: 'block', 
                    fontSize: '12px', 
                    fontWeight: '500', 
                    color: '#374151',
                    marginBottom: '6px'
                  }}>
                    Taux fixe (hors assurance) (%)
                  </label>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      max="100"
                      value={config.interest_rate}
                      onChange={(e) => handleFieldChange(config.id, 'interest_rate', parseFloat(e.target.value) || 0)}
                      onBlur={(e) => handleFieldBlur(config.id, 'interest_rate', parseFloat(e.target.value) || 0)}
                      disabled={saving[config.id]}
                      style={{
                        flex: 1,
                        padding: '8px 12px',
                        border: '1px solid #d1d5db',
                        borderRadius: '4px',
                        fontSize: '14px',
                        backgroundColor: saving[config.id] ? '#f3f4f6' : 'white'
                      }}
                    />
                    <span style={{ fontSize: '14px', color: '#6b7280' }}>%</span>
                  </div>
                </div>

                {/* Durée emprunt */}
                <div>
                  <label style={{ 
                    display: 'block', 
                    fontSize: '12px', 
                    fontWeight: '500', 
                    color: '#374151',
                    marginBottom: '6px'
                  }}>
                    Durée emprunt (années)
                  </label>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <input
                      type="number"
                      step="1"
                      min="0"
                      value={config.duration_years}
                      onChange={(e) => handleFieldChange(config.id, 'duration_years', parseInt(e.target.value) || 0)}
                      onBlur={(e) => handleFieldBlur(config.id, 'duration_years', parseInt(e.target.value) || 0)}
                      disabled={saving[config.id]}
                      style={{
                        flex: 1,
                        padding: '8px 12px',
                        border: '1px solid #d1d5db',
                        borderRadius: '4px',
                        fontSize: '14px',
                        backgroundColor: saving[config.id] ? '#f3f4f6' : 'white'
                      }}
                    />
                    <span style={{ fontSize: '14px', color: '#6b7280' }}>ans</span>
                  </div>
                </div>

                {/* Décalage initial */}
                <div>
                  <label style={{ 
                    display: 'block', 
                    fontSize: '12px', 
                    fontWeight: '500', 
                    color: '#374151',
                    marginBottom: '6px'
                  }}>
                    Décalage initial (mois)
                  </label>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <input
                      type="number"
                      step="1"
                      min="0"
                      value={config.initial_deferral_months}
                      onChange={(e) => handleFieldChange(config.id, 'initial_deferral_months', parseInt(e.target.value) || 0)}
                      onBlur={(e) => handleFieldBlur(config.id, 'initial_deferral_months', parseInt(e.target.value) || 0)}
                      disabled={saving[config.id]}
                      style={{
                        flex: 1,
                        padding: '8px 12px',
                        border: '1px solid #d1d5db',
                        borderRadius: '4px',
                        fontSize: '14px',
                        backgroundColor: saving[config.id] ? '#f3f4f6' : 'white'
                      }}
                    />
                    <span style={{ fontSize: '14px', color: '#6b7280' }}>mois</span>
                  </div>
                </div>
              </div>

              {saving[config.id] && (
                <div style={{
                  marginTop: '12px',
                  fontSize: '12px',
                  color: '#6b7280',
                  fontStyle: 'italic'
                }}>
                  Sauvegarde en cours...
                </div>
              )}
            </div>
          ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
