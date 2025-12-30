/**
 * LoanPaymentTable component - Tableau d'affichage des mensualités de crédit avec sous-onglets multi-crédits
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect, useRef, useMemo } from 'react';
import { loanPaymentsAPI, loanConfigsAPI, LoanPayment, LoanConfig } from '@/api/client';

interface LoanPaymentTableProps {
  refreshKey?: number;
  onActiveLoanNameChange?: (loanName: string) => void;
}

export default function LoanPaymentTable({ refreshKey, onActiveLoanNameChange }: LoanPaymentTableProps) {
  const [loanConfigs, setLoanConfigs] = useState<LoanConfig[]>([]);
  const [activeLoanConfigId, setActiveLoanConfigId] = useState<number | null>(null);
  const [payments, setPayments] = useState<LoanPayment[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingConfigs, setLoadingConfigs] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingPayment, setEditingPayment] = useState<Partial<LoanPayment> | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [isDeletingMultiple, setIsDeletingMultiple] = useState(false);
  const initializedRef = useRef(false);

  // Charger la liste des crédits
  useEffect(() => {
    loadLoanConfigs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey]);

  // Recharger les mensualités quand refreshKey change (après un import)
  useEffect(() => {
    if (activeLoanName && refreshKey !== undefined) {
      console.log('🔄 [LoanPaymentTable] RefreshKey changé, rechargement des mensualités pour:', activeLoanName);
      loadPayments(activeLoanName);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey]);

  // Sélectionner le premier crédit par défaut au chargement OU si le crédit actif n'existe plus
  useEffect(() => {
    if (loanConfigs.length > 0) {
      const activeConfigExists = activeLoanConfigId !== null && loanConfigs.find(c => c.id === activeLoanConfigId);
      
      if (!activeConfigExists || !initializedRef.current) {
        // Trier par created_at et prendre le premier
        const sorted = [...loanConfigs].sort((a, b) => 
          new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        );
        setActiveLoanConfigId(sorted[0].id);
        initializedRef.current = true;
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loanConfigs]);

  // Mémoriser le nom du crédit actif pour éviter les re-renders
  const activeLoanName = useMemo(() => {
    if (activeLoanConfigId !== null && loanConfigs.length > 0) {
      const activeConfig = loanConfigs.find(c => c.id === activeLoanConfigId);
      return activeConfig?.name || null;
    }
    return null;
  }, [activeLoanConfigId, loanConfigs]);

  // Charger les mensualités quand le crédit actif change
  useEffect(() => {
    if (activeLoanName) {
      // Réinitialiser les payments avant de charger les nouvelles données
      setPayments([]);
      loadPayments(activeLoanName);
      if (onActiveLoanNameChange) {
        onActiveLoanNameChange(activeLoanName);
      }
    } else {
      // Si pas de crédit actif, vider les payments
      setPayments([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeLoanName]);

  const loadLoanConfigs = async () => {
    setLoadingConfigs(true);
    try {
      const response = await loanConfigsAPI.getAll();
      // Trier par created_at (ordre de création)
      const sorted = response.configs.sort((a, b) => 
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      );
      setLoanConfigs(sorted);
      
      // Note: La gestion du crédit actif qui n'existe plus est faite dans le useEffect
      // pour éviter les boucles infinies
      
      // Ne pas appeler onLoanConfigsChange ici car cela peut créer une boucle infinie
      // Le parent (LoanConfigCard) gère déjà ses propres changements
    } catch (error) {
      console.error('Erreur lors du chargement des configurations:', error);
    } finally {
      setLoadingConfigs(false);
    }
  };

  const loadPayments = async (loanName: string) => {
    setLoading(true);
    try {
      console.log('🔍 [LoanPaymentTable] Chargement des mensualités pour:', loanName);
      const response = await loanPaymentsAPI.getAll({ loan_name: loanName });
      console.log('📊 [LoanPaymentTable] Réponse API:', {
        total: response.total,
        count: response.payments.length,
        loanNames: [...new Set(response.payments.map(p => p.loan_name))]
      });
      
      // Filtrer strictement par loan_name (sécurité supplémentaire côté frontend)
      const filtered = response.payments.filter(p => p.loan_name === loanName);
      console.log('✅ [LoanPaymentTable] Après filtrage strict:', {
        count: filtered.length,
        loanNames: [...new Set(filtered.map(p => p.loan_name))]
      });
      
      // Trier par date (plus récent en premier)
      const sorted = filtered.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
      setPayments(sorted);
    } catch (error) {
      console.error('Erreur lors du chargement des mensualités:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (payment: LoanPayment) => {
    setEditingId(payment.id);
    setEditingPayment({ ...payment });
  };

  const handleSave = async () => {
    if (!editingId || !editingPayment) return;

    try {
      // Préparer les données à envoyer
      const updateData: any = {};
      
      // Date : s'assurer qu'elle est au format YYYY-MM-DD et non vide
      if (editingPayment.date) {
        let dateStr = '';
        if (typeof editingPayment.date === 'string') {
          // Si c'est déjà une string, extraire la partie date (avant le T si présent)
          dateStr = editingPayment.date.split('T')[0].trim();
        } else {
          // Si c'est un objet Date, le convertir
          dateStr = editingPayment.date.toISOString().split('T')[0];
        }
        // Ne l'envoyer que si elle est valide (format YYYY-MM-DD)
        if (dateStr && dateStr.length === 10 && /^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
          updateData.date = dateStr;
        } else {
          console.warn('⚠️ [LoanPaymentTable] Date invalide, ignorée:', dateStr);
        }
      }
      
      // Autres champs - toujours envoyer capital, interest, insurance pour recalculer le total
      if (editingPayment.capital !== undefined && editingPayment.capital !== null) {
        updateData.capital = Number(editingPayment.capital);
      }
      if (editingPayment.interest !== undefined && editingPayment.interest !== null) {
        updateData.interest = Number(editingPayment.interest);
      }
      if (editingPayment.insurance !== undefined && editingPayment.insurance !== null) {
        updateData.insurance = Number(editingPayment.insurance);
      }
      // Ne pas envoyer total - le backend le recalcule automatiquement
      
      console.log('💾 [LoanPaymentTable] Sauvegarde avec données:', updateData);
      
      await loanPaymentsAPI.update(editingId, updateData);
      const activeConfig = loanConfigs.find(c => c.id === activeLoanConfigId);
      if (activeConfig) {
        await loadPayments(activeConfig.name);
      }
      setEditingId(null);
      setEditingPayment(null);
    } catch (error: any) {
      console.error('❌ [LoanPaymentTable] Erreur lors de la sauvegarde:', error);
      const errorMessage = error?.message || error?.detail || 'Erreur inconnue';
      console.error('❌ [LoanPaymentTable] Détails de l\'erreur:', errorMessage);
      alert(`❌ Erreur lors de la sauvegarde: ${errorMessage}`);
    }
  };

  const handleCancel = () => {
    setEditingId(null);
    setEditingPayment(null);
  };

  const handleToggleSelect = (id: number) => {
    setSelectedIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    if (selectedIds.size === payments.length) {
      // Tout désélectionner
      setSelectedIds(new Set());
    } else {
      // Tout sélectionner
      setSelectedIds(new Set(payments.map(p => p.id)));
    }
  };

  const handleDeleteMultiple = async () => {
    if (selectedIds.size === 0) {
      return;
    }

    const count = selectedIds.size;
    if (!confirm(`Êtes-vous sûr de vouloir supprimer ${count} mensualité${count > 1 ? 's' : ''} ?`)) {
      return;
    }

    setIsDeletingMultiple(true);
    try {
      // Supprimer toutes les mensualités sélectionnées
      const deletePromises = Array.from(selectedIds).map(id => loanPaymentsAPI.delete(id));
      await Promise.all(deletePromises);
      
      setSelectedIds(new Set());
      const activeConfig = loanConfigs.find(c => c.id === activeLoanConfigId);
      if (activeConfig) {
        await loadPayments(activeConfig.name);
      }
    } catch (error) {
      console.error('Erreur lors de la suppression:', error);
      alert(`❌ Erreur lors de la suppression de ${count} mensualité${count > 1 ? 's' : ''}`);
    } finally {
      setIsDeletingMultiple(false);
    }
  };

  const activeConfig = loanConfigs.find(c => c.id === activeLoanConfigId);

  if (loadingConfigs) {
    return (
      <div style={{ textAlign: 'center', padding: '20px', color: '#6b7280' }}>
        Chargement des configurations...
      </div>
    );
  }

  if (loanConfigs.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '20px', color: '#6b7280' }}>
        Aucune configuration de crédit. Créez d'abord un crédit dans la section "Configuration des crédits".
      </div>
    );
  }

  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '8px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      padding: '24px',
    }}>
      {/* Sous-onglets pour les crédits */}
      <div style={{ marginBottom: '24px', borderBottom: '1px solid #e5e7eb' }}>
        <div style={{ display: 'flex', gap: '8px', overflowX: 'auto' }}>
          {loanConfigs.map((config) => {
            const isActive = activeLoanConfigId === config.id;
            return (
              <button
                key={config.id}
                onClick={() => setActiveLoanConfigId(config.id)}
                style={{
                  padding: '12px 16px',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: isActive ? '#1e3a5f' : '#6b7280',
                  borderTop: '0',
                  borderLeft: '0',
                  borderRight: '0',
                  borderBottom: isActive ? '2px solid #1e3a5f' : '2px solid transparent',
                  backgroundColor: 'transparent',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.color = '#1e3a5f';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.color = '#6b7280';
                  }
                }}
              >
                {config.name}
              </button>
            );
          })}
        </div>
      </div>

      {/* Tableau des mensualités pour le crédit actif */}
      {activeConfig && (
        <>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '20px', color: '#6b7280' }}>
              Chargement...
            </div>
          ) : payments.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '20px', color: '#6b7280' }}>
              Aucune mensualité enregistrée pour "{activeConfig.name}".
            </div>
          ) : (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#111827' }}>
                  Mensualités pour "{activeConfig.name}" ({payments.length} enregistrement(s))
                </h3>
                {selectedIds.size > 0 && (
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span style={{ fontSize: '14px', color: '#1e3a5f', fontWeight: '500' }}>
                      {selectedIds.size} mensualité{selectedIds.size > 1 ? 's' : ''} sélectionnée{selectedIds.size > 1 ? 's' : ''}
                    </span>
                    <button
                      onClick={handleDeleteMultiple}
                      disabled={isDeletingMultiple}
                      style={{
                        padding: '8px 16px',
                        backgroundColor: isDeletingMultiple ? '#ccc' : '#dc3545',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        fontSize: '14px',
                        cursor: isDeletingMultiple ? 'not-allowed' : 'pointer',
                        opacity: isDeletingMultiple ? 0.6 : 1,
                      }}
                    >
                      {isDeletingMultiple ? '⏳ Suppression...' : `🗑️ Supprimer ${selectedIds.size}`}
                    </button>
                  </div>
                )}
              </div>
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
                      <th style={{ padding: '8px', textAlign: 'center', fontWeight: '600', color: '#374151', width: '50px' }}>
                        <input
                          type="checkbox"
                          checked={payments.length > 0 && selectedIds.size === payments.length}
                          onChange={handleSelectAll}
                          style={{
                            width: '18px',
                            height: '18px',
                            cursor: 'pointer',
                          }}
                        />
                      </th>
                      <th style={{ padding: '8px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>Date</th>
                      <th style={{ padding: '8px', textAlign: 'right', fontWeight: '600', color: '#374151' }}>Capital (€)</th>
                      <th style={{ padding: '8px', textAlign: 'right', fontWeight: '600', color: '#374151' }}>Intérêts (€)</th>
                      <th style={{ padding: '8px', textAlign: 'right', fontWeight: '600', color: '#374151' }}>Assurance (€)</th>
                      <th style={{ padding: '8px', textAlign: 'right', fontWeight: '600', color: '#374151' }}>Total (€)</th>
                      <th style={{ padding: '8px', textAlign: 'center', fontWeight: '600', color: '#374151' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {payments.map((payment) => (
                      <tr 
                        key={payment.id} 
                        style={{ 
                          borderBottom: '1px solid #e5e7eb',
                          backgroundColor: selectedIds.has(payment.id) ? '#e3f2fd' : 'white',
                          transition: 'background-color 0.2s',
                        }}
                        onMouseEnter={(e) => {
                          if (!selectedIds.has(payment.id)) {
                            e.currentTarget.style.backgroundColor = '#f9f9f9';
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (!selectedIds.has(payment.id)) {
                            e.currentTarget.style.backgroundColor = 'white';
                          } else {
                            e.currentTarget.style.backgroundColor = '#e3f2fd';
                          }
                        }}
                      >
                        {editingId === payment.id ? (
                          <>
                            <td style={{ padding: '8px', textAlign: 'center' }}>
                              <input
                                type="checkbox"
                                checked={selectedIds.has(payment.id)}
                                onChange={() => handleToggleSelect(payment.id)}
                                style={{
                                  width: '18px',
                                  height: '18px',
                                  cursor: 'pointer',
                                }}
                              />
                            </td>
                            <td style={{ padding: '8px' }}>
                              <input
                                type="date"
                                value={editingPayment?.date ? (editingPayment.date.includes('T') ? editingPayment.date.split('T')[0] : editingPayment.date) : ''}
                                onChange={(e) => {
                                  const dateValue = e.target.value || undefined;
                                  setEditingPayment(prev => prev ? { ...prev, date: dateValue } : null);
                                }}
                                style={{
                                  width: '100%',
                                  padding: '4px 8px',
                                  fontSize: '14px',
                                  border: '1px solid #3b82f6',
                                  borderRadius: '4px',
                                }}
                              />
                            </td>
                            <td style={{ padding: '8px', textAlign: 'right' }}>
                              <input
                                type="number"
                                step="0.01"
                                value={editingPayment?.capital || 0}
                                onChange={(e) => {
                                  const capital = parseFloat(e.target.value) || 0;
                                  const interest = editingPayment?.interest || 0;
                                  const insurance = editingPayment?.insurance || 0;
                                  setEditingPayment(prev => prev ? {
                                    ...prev,
                                    capital,
                                    total: capital + interest + insurance
                                  } : null);
                                }}
                                style={{
                                  width: '100%',
                                  padding: '4px 8px',
                                  fontSize: '14px',
                                  border: '1px solid #3b82f6',
                                  borderRadius: '4px',
                                  textAlign: 'right',
                                }}
                              />
                            </td>
                            <td style={{ padding: '8px', textAlign: 'right' }}>
                              <input
                                type="number"
                                step="0.01"
                                value={editingPayment?.interest || 0}
                                onChange={(e) => {
                                  const interest = parseFloat(e.target.value) || 0;
                                  const capital = editingPayment?.capital || 0;
                                  const insurance = editingPayment?.insurance || 0;
                                  setEditingPayment(prev => prev ? {
                                    ...prev,
                                    interest,
                                    total: capital + interest + insurance
                                  } : null);
                                }}
                                style={{
                                  width: '100%',
                                  padding: '4px 8px',
                                  fontSize: '14px',
                                  border: '1px solid #3b82f6',
                                  borderRadius: '4px',
                                  textAlign: 'right',
                                }}
                              />
                            </td>
                            <td style={{ padding: '8px', textAlign: 'right' }}>
                              <input
                                type="number"
                                step="0.01"
                                value={editingPayment?.insurance || 0}
                                onChange={(e) => {
                                  const insurance = parseFloat(e.target.value) || 0;
                                  const capital = editingPayment?.capital || 0;
                                  const interest = editingPayment?.interest || 0;
                                  setEditingPayment(prev => prev ? {
                                    ...prev,
                                    insurance,
                                    total: capital + interest + insurance
                                  } : null);
                                }}
                                style={{
                                  width: '100%',
                                  padding: '4px 8px',
                                  fontSize: '14px',
                                  border: '1px solid #3b82f6',
                                  borderRadius: '4px',
                                  textAlign: 'right',
                                }}
                              />
                            </td>
                            <td style={{ padding: '8px', textAlign: 'right', fontWeight: '600' }}>
                              {(editingPayment?.total || 0).toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €
                            </td>
                            <td style={{ padding: '8px', textAlign: 'center' }}>
                              <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                                <button
                                  onClick={handleSave}
                                  style={{
                                    padding: '4px 8px',
                                    fontSize: '12px',
                                    color: '#ffffff',
                                    backgroundColor: '#10b981',
                                    border: 'none',
                                    borderRadius: '4px',
                                    cursor: 'pointer',
                                  }}
                                >
                                  ✓
                                </button>
                                <button
                                  onClick={handleCancel}
                                  style={{
                                    padding: '4px 8px',
                                    fontSize: '12px',
                                    color: '#ffffff',
                                    backgroundColor: '#6b7280',
                                    border: 'none',
                                    borderRadius: '4px',
                                    cursor: 'pointer',
                                  }}
                                >
                                  ✕
                                </button>
                              </div>
                            </td>
                          </>
                        ) : (
                          <>
                            <td style={{ padding: '8px', textAlign: 'center' }}>
                              <input
                                type="checkbox"
                                checked={selectedIds.has(payment.id)}
                                onChange={() => handleToggleSelect(payment.id)}
                                style={{
                                  width: '18px',
                                  height: '18px',
                                  cursor: 'pointer',
                                }}
                              />
                            </td>
                            <td style={{ padding: '8px' }}>
                              {new Date(payment.date).toLocaleDateString('fr-FR')}
                            </td>
                            <td style={{ padding: '8px', textAlign: 'right' }}>
                              {payment.capital.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €
                            </td>
                            <td style={{ padding: '8px', textAlign: 'right' }}>
                              {payment.interest.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €
                            </td>
                            <td style={{ padding: '8px', textAlign: 'right' }}>
                              {payment.insurance.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €
                            </td>
                            <td style={{ padding: '8px', textAlign: 'right', fontWeight: '600' }}>
                              {payment.total.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €
                            </td>
                            <td style={{ padding: '8px', textAlign: 'center' }}>
                              <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                                <button
                                  onClick={() => handleEdit(payment)}
                                  style={{
                                    padding: '6px 12px',
                                    backgroundColor: '#3b82f6',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    fontSize: '16px',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                  }}
                                  title="Modifier"
                                >
                                  ✏️
                                </button>
                                <button
                                  onClick={() => {
                                    if (confirm('Êtes-vous sûr de vouloir supprimer cette mensualité ?')) {
                                      loanPaymentsAPI.delete(payment.id).then(() => {
                                        if (activeConfig) {
                                          loadPayments(activeConfig.name);
                                        }
                                        setSelectedIds(prev => {
                                          const newSet = new Set(prev);
                                          newSet.delete(payment.id);
                                          return newSet;
                                        });
                                      }).catch(error => {
                                        console.error('Erreur lors de la suppression:', error);
                                        alert('❌ Erreur lors de la suppression');
                                      });
                                    }
                                  }}
                                  style={{
                                    padding: '6px 12px',
                                    backgroundColor: '#dc3545',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    fontSize: '16px',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                  }}
                                  title="Supprimer"
                                >
                                  🗑️
                                </button>
                              </div>
                            </td>
                          </>
                        )}
                      </tr>
                    ))}
                    {/* Ligne de totaux */}
                    {payments.length > 0 && (
                      <tr style={{ 
                        backgroundColor: '#f9fafb', 
                        borderTop: '2px solid #e5e7eb',
                        borderBottom: '2px solid #e5e7eb',
                        fontWeight: '600'
                      }}>
                        <td style={{ padding: '12px 8px', textAlign: 'center' }}></td>
                        <td style={{ padding: '12px 8px', fontWeight: '600', color: '#111827' }}>
                          TOTAL
                        </td>
                        <td style={{ padding: '12px 8px', textAlign: 'right', fontWeight: '600', color: '#111827' }}>
                          {payments.reduce((sum, p) => sum + (p.capital || 0), 0).toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €
                        </td>
                        <td style={{ padding: '12px 8px', textAlign: 'right', fontWeight: '600', color: '#111827' }}>
                          {payments.reduce((sum, p) => sum + (p.interest || 0), 0).toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €
                        </td>
                        <td style={{ padding: '12px 8px', textAlign: 'right', fontWeight: '600', color: '#111827' }}>
                          {payments.reduce((sum, p) => sum + (p.insurance || 0), 0).toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €
                        </td>
                        <td style={{ padding: '12px 8px', textAlign: 'right', fontWeight: '700', color: '#1e3a5f', fontSize: '15px' }}>
                          {payments.reduce((sum, p) => sum + (p.total || 0), 0).toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €
                        </td>
                        <td style={{ padding: '12px 8px', textAlign: 'center' }}></td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}
