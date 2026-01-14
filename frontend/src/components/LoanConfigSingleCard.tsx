/**
 * LoanConfigSingleCard - Card de configuration pour UN seul crédit
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect, useMemo } from 'react';
import { loanConfigsAPI, LoanConfig } from '@/api/client';
import LoanPaymentFileUpload from './LoanPaymentFileUpload';
import { PMT, IPMT, PPMT, formatCurrency, roundTo2Decimals } from '@/utils/financial';

interface LoanConfigSingleCardProps {
  loanConfig: LoanConfig;
  onConfigUpdated?: () => void;
}

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

export default function LoanConfigSingleCard({ loanConfig: initialConfig, onConfigUpdated }: LoanConfigSingleCardProps) {
  const [config, setConfig] = useState<LoanConfig>(initialConfig);
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  // Mettre à jour le config si le prop change
  useEffect(() => {
    setConfig(initialConfig);
  }, [initialConfig]);

  // Calculer les valeurs de simulation pour chaque mensualité
  const simulationData = useMemo(() => {
    // Calculer la durée crédit (années) incluant différé
    // Utiliser les dates si disponibles, sinon utiliser duration_years
    let durationYearsIncludingDeferral: number | null = null;
    
    if (config.loan_start_date && config.loan_end_date) {
      const yearfracValue = yearfrac(config.loan_start_date, config.loan_end_date);
      if (yearfracValue !== null) {
        durationYearsIncludingDeferral = yearfracValue - (config.initial_deferral_months / 12);
      }
    }
    
    // Si pas de dates, utiliser duration_years + initial_deferral_months/12
    if (durationYearsIncludingDeferral === null || durationYearsIncludingDeferral <= 0) {
      durationYearsIncludingDeferral = config.duration_years + (config.initial_deferral_months / 12);
    }
    
    const monthlyRate = config.interest_rate / 100 / 12; // Taux mensuel
    const totalMonths = durationYearsIncludingDeferral * 12; // Durée totale en mois (incluant différé)
    const loanAmount = -config.credit_amount; // Montant négatif pour PMT
    const insurance = config.monthly_insurance || 0;

    // Logs pour déboguer
    console.log('📊 Calcul simulation crédit:', {
      'Crédit accordé (€)': config.credit_amount,
      'Taux fixe (%)': config.interest_rate,
      'Taux mensuel': monthlyRate,
      'Durée crédit (années) incluant différé': durationYearsIncludingDeferral,
      'Durée totale (mois)': totalMonths,
      'Assurance mensuelle (€)': insurance,
      'Montant pour PMT (négatif)': loanAmount
    });

    // Vérifier si on a les données nécessaires
    if (!config.credit_amount || !config.interest_rate || totalMonths <= 0) {
      console.warn('⚠️ Données insuffisantes pour le calcul:', {
        credit_amount: config.credit_amount,
        interest_rate: config.interest_rate,
        totalMonths
      });
      return null;
    }

    const months = [1, 50, 100, 150, 200];
    
    return months.map((month) => {
      if (month > totalMonths) {
        return {
          month,
          payment: 0,
          interest: 0,
          capital: 0,
          insurance: 0,
          total: 0
        };
      }

      try {
        const payment = Math.abs(PMT(monthlyRate, totalMonths, loanAmount));
        const interest = Math.abs(IPMT(monthlyRate, month, totalMonths, loanAmount));
        const capital = Math.abs(PPMT(monthlyRate, month, totalMonths, loanAmount));
        const totalPerMonth = roundTo2Decimals(insurance + interest + capital);
        const totalPerYear = roundTo2Decimals(totalPerMonth * 12);

        // Log pour la première mensualité
        if (month === 1) {
          console.log(`📊 Calcul mensualité ${month}:`, {
            'PMT(rate, nper, pv)': `PMT(${monthlyRate}, ${totalMonths}, ${loanAmount})`,
            'Mensualité crédit': payment,
            'Intérêt': interest,
            'Capital': capital,
            'Assurance': insurance,
            'Total (par mois)': totalPerMonth,
            'Total (par an)': totalPerYear
          });
        }

        return {
          month,
          payment: roundTo2Decimals(payment),
          interest: roundTo2Decimals(interest),
          capital: roundTo2Decimals(capital),
          insurance: roundTo2Decimals(insurance),
          totalPerMonth,
          totalPerYear
        };
      } catch (error) {
        console.error(`Erreur lors du calcul pour la mensualité ${month}:`, error);
        return {
          month,
          payment: 0,
          interest: 0,
          capital: 0,
          insurance: 0,
          total: 0
        };
      }
    });
  }, [config.credit_amount, config.interest_rate, config.duration_years, config.initial_deferral_months, config.monthly_insurance]);

  const handleFieldChange = (field: string, value: string | number | null) => {
    setConfig(prev => ({ ...prev, [field]: value }));
  };

  const handleFieldBlur = async (field: string, value: string | number | null) => {
    if (saving) return; // Éviter les appels multiples

    try {
      setSaving(true);
      setError('');

      const updateData: any = { [field]: value };
      
      const updated = await loanConfigsAPI.update(config.id, updateData);
      
      // Mettre à jour le config local avec la réponse
      setConfig(updated);
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (error: any) {
      console.error(`Erreur lors de la sauvegarde du champ ${field}:`, error);
      setError(error.message || 'Erreur lors de la sauvegarde');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ 
      backgroundColor: 'white', 
      borderRadius: '8px', 
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      padding: '24px'
    }}>
      {/* Header avec titre et bouton Load Mensualités */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '24px',
        paddingBottom: '16px',
        borderBottom: '1px solid #e5e7eb'
      }}>
        <h3 style={{
          fontSize: '18px',
          fontWeight: '600',
          color: '#1a1a1a',
          margin: 0
        }}>
          Configurations de crédit
        </h3>
        <div style={{ flexShrink: 0 }}>
          <LoanPaymentFileUpload
            loanName={config.name}
            onImportComplete={onConfigUpdated}
          />
        </div>
      </div>

      {error && (
        <div style={{
          padding: '12px',
          backgroundColor: '#fee2e2',
          color: '#dc2626',
          borderRadius: '4px',
          marginBottom: '16px',
          fontSize: '14px'
        }}>
          {error}
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
            onChange={(e) => handleFieldChange('name', e.target.value)}
            onBlur={(e) => handleFieldBlur('name', e.target.value)}
            disabled={saving}
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid #d1d5db',
              borderRadius: '4px',
              fontSize: '14px',
              backgroundColor: saving ? '#f3f4f6' : 'white'
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
              onChange={(e) => handleFieldChange('credit_amount', parseFloat(e.target.value) || 0)}
              onBlur={(e) => handleFieldBlur('credit_amount', parseFloat(e.target.value) || 0)}
              disabled={saving}
              style={{
                flex: 1,
                padding: '8px 12px',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                fontSize: '14px',
                backgroundColor: saving ? '#f3f4f6' : 'white'
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
              onChange={(e) => handleFieldChange('interest_rate', parseFloat(e.target.value) || 0)}
              onBlur={(e) => handleFieldBlur('interest_rate', parseFloat(e.target.value) || 0)}
              disabled={saving}
              style={{
                flex: 1,
                padding: '8px 12px',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                fontSize: '14px',
                backgroundColor: saving ? '#f3f4f6' : 'white'
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
              onChange={(e) => handleFieldChange('duration_years', parseInt(e.target.value) || 0)}
              onBlur={(e) => handleFieldBlur('duration_years', parseInt(e.target.value) || 0)}
              disabled={saving}
              style={{
                flex: 1,
                padding: '8px 12px',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                fontSize: '14px',
                backgroundColor: saving ? '#f3f4f6' : 'white'
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
              onChange={(e) => handleFieldChange('initial_deferral_months', parseInt(e.target.value) || 0)}
              onBlur={(e) => handleFieldBlur('initial_deferral_months', parseInt(e.target.value) || 0)}
              disabled={saving}
              style={{
                flex: 1,
                padding: '8px 12px',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                fontSize: '14px',
                backgroundColor: saving ? '#f3f4f6' : 'white'
              }}
            />
            <span style={{ fontSize: '14px', color: '#6b7280' }}>mois</span>
          </div>
        </div>

        {/* Assurance mensuelle */}
        <div>
          <label style={{ 
            display: 'block', 
            fontSize: '12px', 
            fontWeight: '500', 
            color: '#374151',
            marginBottom: '6px'
          }}>
            Assurance mensuelle (€/mois)
          </label>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <input
              type="number"
              step="0.01"
              min="0"
              value={config.monthly_insurance || 0}
              onChange={(e) => handleFieldChange('monthly_insurance', parseFloat(e.target.value) || 0)}
              onBlur={(e) => handleFieldBlur('monthly_insurance', parseFloat(e.target.value) || 0)}
              disabled={saving}
              style={{
                flex: 1,
                padding: '8px 12px',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                fontSize: '14px',
                backgroundColor: saving ? '#f3f4f6' : 'white'
              }}
            />
            <span style={{ fontSize: '14px', color: '#6b7280' }}>€</span>
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
            onChange={(e) => handleFieldChange('loan_start_date', e.target.value || null)}
            onBlur={(e) => handleFieldBlur('loan_start_date', e.target.value || null)}
            disabled={saving}
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid #d1d5db',
              borderRadius: '4px',
              fontSize: '14px',
              backgroundColor: saving ? '#f3f4f6' : 'white'
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
            onChange={(e) => handleFieldChange('loan_end_date', e.target.value || null)}
            onBlur={(e) => handleFieldBlur('loan_end_date', e.target.value || null)}
            disabled={saving}
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid #d1d5db',
              borderRadius: '4px',
              fontSize: '14px',
              backgroundColor: saving ? '#f3f4f6' : 'white'
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

      {/* Tableau de simulation */}
      <div style={{ 
        marginTop: '24px',
        padding: '16px',
        backgroundColor: '#f9fafb',
        borderRadius: '8px',
        border: '1px solid #e5e7eb'
      }}>
        <h4 style={{ 
          fontSize: '14px', 
          fontWeight: '600', 
          color: '#374151',
          marginBottom: '16px',
          marginTop: 0
        }}>
          Simulations crédit
        </h4>
        <div style={{
          overflowX: 'auto',
          border: '1px solid #e5e7eb',
          borderRadius: '4px',
          backgroundColor: 'white'
        }}>
          <table style={{
            width: '100%',
            borderCollapse: 'collapse',
            fontSize: '13px'
          }}>
            <thead>
              <tr style={{
                backgroundColor: '#f3f4f6',
                borderBottom: '2px solid #e5e7eb'
              }}>
                <th style={{
                  padding: '10px 12px',
                  textAlign: 'left',
                  fontWeight: '600',
                  color: '#374151',
                  borderRight: '1px solid #e5e7eb'
                }}>
                  Mensualité
                </th>
                <th style={{
                  padding: '10px 12px',
                  textAlign: 'right',
                  fontWeight: '600',
                  color: '#374151',
                  borderRight: '1px solid #e5e7eb'
                }}>
                  Mensualité crédit
                </th>
                <th style={{
                  padding: '10px 12px',
                  textAlign: 'right',
                  fontWeight: '600',
                  color: '#374151',
                  borderRight: '1px solid #e5e7eb'
                }}>
                  Intérêt
                </th>
                <th style={{
                  padding: '10px 12px',
                  textAlign: 'right',
                  fontWeight: '600',
                  color: '#374151',
                  borderRight: '1px solid #e5e7eb'
                }}>
                  Capital
                </th>
                <th style={{
                  padding: '10px 12px',
                  textAlign: 'right',
                  fontWeight: '600',
                  color: '#374151',
                  borderRight: '1px solid #e5e7eb'
                }}>
                  Assurance
                </th>
                <th style={{
                  padding: '10px 12px',
                  textAlign: 'right',
                  fontWeight: '600',
                  color: '#374151',
                  borderRight: '1px solid #e5e7eb'
                }}>
                  Total (par mois)
                </th>
                <th style={{
                  padding: '10px 12px',
                  textAlign: 'right',
                  fontWeight: '600',
                  color: '#374151'
                }}>
                  Total (par an)
                </th>
              </tr>
            </thead>
            <tbody>
              {simulationData ? (
                simulationData.map((data) => (
                  <tr key={data.month} style={{
                    borderBottom: '1px solid #e5e7eb'
                  }}>
                    <td style={{
                      padding: '10px 12px',
                      color: '#374151',
                      borderRight: '1px solid #e5e7eb',
                      fontWeight: '500'
                    }}>
                      {data.month}
                    </td>
                    <td style={{
                      padding: '10px 12px',
                      textAlign: 'right',
                      color: '#374151',
                      borderRight: '1px solid #e5e7eb'
                    }}>
                      {data.payment > 0 ? formatCurrency(data.payment) : '-'}
                    </td>
                    <td style={{
                      padding: '10px 12px',
                      textAlign: 'right',
                      color: '#374151',
                      borderRight: '1px solid #e5e7eb'
                    }}>
                      {data.interest > 0 ? formatCurrency(data.interest) : '-'}
                    </td>
                    <td style={{
                      padding: '10px 12px',
                      textAlign: 'right',
                      color: '#374151',
                      borderRight: '1px solid #e5e7eb'
                    }}>
                      {data.capital > 0 ? formatCurrency(data.capital) : '-'}
                    </td>
                    <td style={{
                      padding: '10px 12px',
                      textAlign: 'right',
                      color: '#374151',
                      borderRight: '1px solid #e5e7eb'
                    }}>
                      {data.insurance > 0 ? formatCurrency(data.insurance) : '-'}
                    </td>
                    <td style={{
                      padding: '10px 12px',
                      textAlign: 'right',
                      color: '#374151',
                      borderRight: '1px solid #e5e7eb',
                      fontWeight: '500'
                    }}>
                      {data.totalPerMonth > 0 ? formatCurrency(data.totalPerMonth) : '-'}
                    </td>
                    <td style={{
                      padding: '10px 12px',
                      textAlign: 'right',
                      color: '#374151',
                      fontWeight: '500'
                    }}>
                      {data.totalPerYear > 0 ? formatCurrency(data.totalPerYear) : '-'}
                    </td>
                  </tr>
                ))
              ) : (
                [1, 50, 100, 150, 200].map((month) => (
                  <tr key={month} style={{
                    borderBottom: '1px solid #e5e7eb'
                  }}>
                    <td style={{
                      padding: '10px 12px',
                      color: '#374151',
                      borderRight: '1px solid #e5e7eb',
                      fontWeight: '500'
                    }}>
                      {month}
                    </td>
                    <td colSpan={6} style={{
                      padding: '10px 12px',
                      textAlign: 'center',
                      color: '#6b7280',
                      fontStyle: 'italic'
                    }}>
                      Données insuffisantes pour le calcul
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {saving && (
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
  );
}
