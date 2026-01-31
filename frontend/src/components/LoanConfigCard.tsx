/**
 * LoanConfigCard - Card de configuration des crédits
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect } from 'react';
import { loanConfigsAPI, LoanConfig, LoanConfigCreate, loanPaymentsAPI, transactionsAPI } from '@/api/client';

interface LoanConfigCardProps {
  onConfigUpdated?: () => void;
}

const STORAGE_KEY_LOAN_CONFIG_COLLAPSED = 'loan_config_card_collapsed';

/**
 * Fonction équivalente à YEARFRAC(date1, date2, 3) d'Excel
 * Base 3 = année réelle/365 (nombre réel de jours dans l'année)
 */
function yearfrac(date1: string | null | undefined, date2: string | null | undefined): number | null {
  if (!date1 || !date2) return null;
  
  const d1 = new Date(date1);
  const d2 = new Date(date2);
  
  if (isNaN(d1.getTime()) || isNaN(d2.getTime())) return null;
  
  // Différence en millisecondes
  const diffMs = d2.getTime() - d1.getTime();
  // Convertir en jours
  const diffDays = diffMs / (1000 * 60 * 60 * 24);
  // Diviser par 365 (année réelle)
  return diffDays / 365;
}

/**
 * Calcule le nombre de mois écoulés depuis la date d'emprunt
 * ROUND(YEARFRAC(date_emprunt, date_du_jour, 3) * 12, 0)
 */
function calculateMonthsElapsed(startDate: string | null | undefined): number | null {
  if (!startDate) return null;
  
  const today = new Date();
  const start = new Date(startDate);
  
  if (isNaN(start.getTime())) return null;
  
  const years = yearfrac(startDate, today.toISOString().split('T')[0]);
  if (years === null) return null;
  
  return Math.round(years * 12);
}

/**
 * Calcule le nombre de mois restants jusqu'à la date de fin
 * ROUND(YEARFRAC(date_du_jour, date_fin, 3) * 12, 0)
 */
function calculateMonthsRemaining(endDate: string | null | undefined): number | null {
  if (!endDate) return null;
  
  const today = new Date();
  const end = new Date(endDate);
  
  if (isNaN(end.getTime())) return null;
  
  const years = yearfrac(today.toISOString().split('T')[0], endDate);
  if (years === null) return null;
  
  return Math.round(years * 12);
}

/**
 * Formate la durée restante en "X ans et Y mois"
 */
function formatRemainingDuration(months: number | null): string {
  if (months === null || months < 0) return '-';
  
  const years = Math.floor(months / 12);
  const remainingMonths = Math.round(((months / 12) - Math.floor(months / 12)) * 12);
  
  if (years === 0) {
    return `${remainingMonths} mois`;
  } else if (remainingMonths === 0) {
    return `${years} ans`;
  } else {
    return `${years} ans et ${remainingMonths} mois`;
  }
}

export default function LoanConfigCard({ onConfigUpdated }: LoanConfigCardProps) {
  const [configs, setConfigs] = useState<LoanConfig[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<{ [key: number]: boolean }>({});
  const [errors, setErrors] = useState<{ [key: number]: string; global?: string }>({});
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);
  const [incoherenceWarning, setIncoherenceWarning] = useState<string | null>(null);

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
      
      // Vérifier l'incohérence entre montant crédits et transactions
      await checkIncoherence(response.items);
    } catch (error) {
      console.error('Erreur lors du chargement des configurations:', error);
      setErrors({ global: 'Erreur lors du chargement des configurations' });
    } finally {
      setLoading(false);
    }
  };

  const checkIncoherence = async (configs: LoanConfig[]) => {
    try {
      // Calculer le montant total des crédits
      const totalCreditAmount = configs.reduce((sum, config) => sum + (config.credit_amount || 0), 0);
      console.log(`🔍 [LoanConfigCard] checkIncoherence: Total crédits = ${totalCreditAmount.toFixed(2)} €`);
      
      // Récupérer le montant total des transactions avec level_1 = "Dettes financières (emprunt bancaire)"
      // Note: Cette fonction nécessite property_id pour l'isolation multi-propriétés
      // Pour l'instant, on utilise property_id=1 par défaut (à améliorer si nécessaire)
      const transactionsSum = await transactionsAPI.getSumByLevel1(1, 'Dettes financières (emprunt bancaire)');
      const totalTransactions = Math.abs(transactionsSum.total || 0);
      console.log(`🔍 [LoanConfigCard] checkIncoherence: Total transactions = ${totalTransactions.toFixed(2)} €`);
      
      // Vérifier l'incohérence (tolérance de 0.01 €)
      const difference = Math.abs(totalCreditAmount - totalTransactions);
      console.log(`🔍 [LoanConfigCard] checkIncoherence: Différence = ${difference.toFixed(2)} €`);
      
      if (difference > 0.01) {
        const warningMessage = `Incohérence détectée entre le montant configuré (${totalCreditAmount.toFixed(2)} €) et les transactions (${totalTransactions.toFixed(2)} €). Différence: ${difference.toFixed(2)} €`;
        console.log(`⚠️ [LoanConfigCard] checkIncoherence: ${warningMessage}`);
        setIncoherenceWarning(warningMessage);
      } else {
        console.log('✅ [LoanConfigCard] checkIncoherence: Pas d\'incohérence détectée');
        setIncoherenceWarning(null);
      }
    } catch (error) {
      console.error('❌ [LoanConfigCard] Erreur lors de la vérification d\'incohérence:', error);
      // Ne pas bloquer si la vérification échoue
      setIncoherenceWarning(null);
    }
  };

  const handleFieldChange = (id: number | 'new', field: string, value: string | number | null) => {
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

  const handleFieldBlur = async (id: number, field: string, value: string | number | null) => {
    if (saving[id]) return; // Éviter les appels multiples

    try {
      setSaving(prev => ({ ...prev, [id]: true }));
      setErrors(prev => ({ ...prev, [id]: '' }));

      const config = configs.find(c => c.id === id);
      if (!config) return;

      const updateData: any = { [field]: value };
      
      await loanConfigsAPI.update(id, updateData);
      
      // Recharger pour avoir les données à jour
      const response = await loanConfigsAPI.getAll();
      setConfigs(response.items);
      
      // Vérifier l'incohérence après modification
      if (field === 'credit_amount') {
        await checkIncoherence(response.items);
      }
      
      // Émettre un événement pour rafraîchir le bilan
      window.dispatchEvent(new CustomEvent('loanConfigUpdated', { detail: { id, action: 'update' } }));
      
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
        initial_deferral_months: 0,
        loan_start_date: null,
        loan_end_date: null
      };

      const created = await loanConfigsAPI.create(newConfig);
      const response = await loanConfigsAPI.getAll();
      setConfigs(response.items);
      
      // Vérifier l'incohérence après création
      await checkIncoherence(response.items);
      
      // Émettre un événement pour rafraîchir le bilan
      window.dispatchEvent(new CustomEvent('loanConfigUpdated', { detail: { id: created.id, action: 'create' } }));
      
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
          
          // Émettre un événement pour chaque paiement supprimé (pour rafraîchir le bilan)
          allPayments.items.forEach(payment => {
            const paymentYear = new Date(payment.date).getFullYear();
            window.dispatchEvent(new CustomEvent('loanPaymentUpdated', { 
              detail: { id: payment.id, action: 'delete', year: paymentYear } 
            }));
          });
        } catch (err) {
          console.error('Erreur lors de la suppression des mensualités:', err);
          // Continuer quand même avec la suppression de la config
        }
      }

      // Supprimer la configuration
      await loanConfigsAPI.delete(id);
      const response = await loanConfigsAPI.getAll();
      setConfigs(response.items);
      
      // Vérifier l'incohérence après suppression
      await checkIncoherence(response.items);
      
      // Émettre un événement pour rafraîchir le bilan
      window.dispatchEvent(new CustomEvent('loanConfigUpdated', { detail: { id, action: 'delete' } }));
      
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

      {/* Warning d'incohérence */}
      {!isCollapsed && incoherenceWarning && (
        <div style={{
          padding: '12px 16px',
          backgroundColor: '#fef3c7',
          border: '1px solid #fbbf24',
          borderRadius: '6px',
          marginBottom: '16px',
          color: '#92400e',
          fontSize: '14px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <span style={{ fontSize: '18px' }}>⚠️</span>
          <span>{incoherenceWarning}</span>
        </div>
      )}

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

                {/* Date d'emprunt */}
                <div>
                  <label style={{ 
                    display: 'block', 
                    fontSize: '12px', 
                    fontWeight: '500', 
                    color: '#374151',
                    marginBottom: '6px'
                  }}>
                    Date d'emprunt
                  </label>
                  <input
                    type="date"
                    value={config.loan_start_date || ''}
                    onChange={(e) => handleFieldChange(config.id, 'loan_start_date', e.target.value || null)}
                    onBlur={(e) => handleFieldBlur(config.id, 'loan_start_date', e.target.value || null)}
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

                {/* Date de fin prévisionnelle */}
                <div>
                  <label style={{ 
                    display: 'block', 
                    fontSize: '12px', 
                    fontWeight: '500', 
                    color: '#374151',
                    marginBottom: '6px'
                  }}>
                    Date de fin prévisionnelle
                  </label>
                  <input
                    type="date"
                    value={config.loan_end_date || ''}
                    onChange={(e) => handleFieldChange(config.id, 'loan_end_date', e.target.value || null)}
                    onBlur={(e) => handleFieldBlur(config.id, 'loan_end_date', e.target.value || null)}
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
              </div>

              {/* Champs calculés */}
              <div style={{ 
                marginTop: '20px',
                padding: '16px',
                backgroundColor: '#f3f4f6',
                borderRadius: '8px',
                border: '1px solid #e5e7eb'
              }}>
                <h4 style={{ 
                  fontSize: '14px', 
                  fontWeight: '600', 
                  color: '#374151',
                  marginBottom: '12px',
                  marginTop: 0
                }}>
                  Calculs automatiques
                </h4>
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '16px'
                }}>
                  {/* Durée crédit (années) */}
                  <div>
                    <label style={{ 
                      display: 'block', 
                      fontSize: '12px', 
                      fontWeight: '500', 
                      color: '#6b7280',
                      marginBottom: '6px'
                    }}>
                      Durée crédit (années)
                    </label>
                    <div style={{
                      padding: '8px 12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '4px',
                      fontSize: '14px',
                      backgroundColor: 'white',
                      color: '#374151'
                    }}>
                      {yearfrac(config.loan_start_date, config.loan_end_date) !== null
                        ? yearfrac(config.loan_start_date, config.loan_end_date)!.toFixed(2)
                        : '-'} ans
                    </div>
                  </div>

                  {/* Durée crédit (années) incluant différé */}
                  <div>
                    <label style={{ 
                      display: 'block', 
                      fontSize: '12px', 
                      fontWeight: '500', 
                      color: '#6b7280',
                      marginBottom: '6px'
                    }}>
                      Durée crédit (années) incluant différé
                    </label>
                    <div style={{
                      padding: '8px 12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '4px',
                      fontSize: '14px',
                      backgroundColor: 'white',
                      color: '#374151'
                    }}>
                      {yearfrac(config.loan_start_date, config.loan_end_date) !== null
                        ? (yearfrac(config.loan_start_date, config.loan_end_date)! - (config.initial_deferral_months / 12)).toFixed(2)
                        : '-'} ans
                    </div>
                  </div>

                  {/* Nombre de mois écoulés */}
                  <div>
                    <label style={{ 
                      display: 'block', 
                      fontSize: '12px', 
                      fontWeight: '500', 
                      color: '#6b7280',
                      marginBottom: '6px'
                    }}>
                      Nombre de mois écoulés
                    </label>
                    <div style={{
                      padding: '8px 12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '4px',
                      fontSize: '14px',
                      backgroundColor: 'white',
                      color: '#374151'
                    }}>
                      {calculateMonthsElapsed(config.loan_start_date) !== null
                        ? calculateMonthsElapsed(config.loan_start_date)
                        : '-'} mois
                    </div>
                  </div>

                  {/* Nombre de mois restants */}
                  <div>
                    <label style={{ 
                      display: 'block', 
                      fontSize: '12px', 
                      fontWeight: '500', 
                      color: '#6b7280',
                      marginBottom: '6px'
                    }}>
                      Nombre de mois restants
                    </label>
                    <div style={{
                      padding: '8px 12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '4px',
                      fontSize: '14px',
                      backgroundColor: 'white',
                      color: '#374151'
                    }}>
                      {calculateMonthsRemaining(config.loan_end_date) !== null
                        ? calculateMonthsRemaining(config.loan_end_date)
                        : '-'} mois
                    </div>
                  </div>

                  {/* Durée restante */}
                  <div>
                    <label style={{ 
                      display: 'block', 
                      fontSize: '12px', 
                      fontWeight: '500', 
                      color: '#6b7280',
                      marginBottom: '6px'
                    }}>
                      Durée restante
                    </label>
                    <div style={{
                      padding: '8px 12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '4px',
                      fontSize: '14px',
                      backgroundColor: 'white',
                      color: '#374151'
                    }}>
                      {formatRemainingDuration(calculateMonthsRemaining(config.loan_end_date))}
                    </div>
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
