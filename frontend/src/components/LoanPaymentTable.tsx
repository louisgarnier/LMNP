/**
 * LoanPaymentTable component - Tableau des mensualités de crédit avec édition inline et sous-onglets multi-crédits
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { loanPaymentsAPI, LoanPayment, LoanPaymentUpdate, loanConfigsAPI, LoanConfig } from '@/api/client';

interface LoanPaymentTableProps {
  loanConfigs?: LoanConfig[]; // Liste des configurations de crédit (optionnel, si non fourni, charge depuis l'API)
  onUpdate?: () => void; // Callback après mise à jour
  refreshTrigger?: number; // Trigger pour forcer le rafraîchissement
  onConfigsChange?: (configs: LoanConfig[]) => void; // Callback quand les configs changent
  onActiveLoanChange?: (loanName: string | null) => void; // Callback quand le crédit actif change
  initialActiveLoanName?: string | null; // Crédit actif initial
}

export default function LoanPaymentTable({ loanConfigs: externalLoanConfigs, onUpdate, refreshTrigger, onConfigsChange, onActiveLoanChange, initialActiveLoanName }: LoanPaymentTableProps) {
  // État pour les configurations de crédit
  const [loanConfigs, setLoanConfigs] = useState<LoanConfig[]>([]);
  const [isLoadingConfigs, setIsLoadingConfigs] = useState(false);
  
  // État pour l'onglet actif (nom du crédit)
  const [activeLoanName, setActiveLoanName] = useState<string | null>(initialActiveLoanName || null);
  
  // Mettre à jour activeLoanName si initialActiveLoanName change (mais seulement si différent)
  useEffect(() => {
    if (initialActiveLoanName !== undefined && initialActiveLoanName !== activeLoanName) {
      setActiveLoanName(initialActiveLoanName);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialActiveLoanName]);
  
  // Notifier le parent quand le crédit actif change (seulement si vraiment changé)
  const prevActiveLoanNameRef = useRef<string | null>(null);
  useEffect(() => {
    if (onActiveLoanChange && activeLoanName !== prevActiveLoanNameRef.current) {
      prevActiveLoanNameRef.current = activeLoanName;
      onActiveLoanChange(activeLoanName);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeLoanName]);
  
  // État pour les mensualités
  const [payments, setPayments] = useState<LoanPayment[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingValues, setEditingValues] = useState<{
    date?: string;
    capital?: number;
    interest?: number;
    insurance?: number;
    total?: number;
  }>({});
  const [savingId, setSavingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [isDeletingMultiple, setIsDeletingMultiple] = useState(false);

  // Charger les configurations de crédit - version stable sans callback
  useEffect(() => {
    const loadLoanConfigs = async () => {
      // Si des configs sont fournies en props, les utiliser
      if (externalLoanConfigs !== undefined) {
        const sortedConfigs = [...externalLoanConfigs].sort((a, b) => {
          // Trier par created_at si disponible, sinon par id
          const aDate = (a as any).created_at ? new Date((a as any).created_at).getTime() : a.id;
          const bDate = (b as any).created_at ? new Date((b as any).created_at).getTime() : b.id;
          return aDate - bDate;
        });
        setLoanConfigs(sortedConfigs);
        
        // Si aucun crédit actif et qu'il y a des configs, sélectionner le premier
        setActiveLoanName(prev => {
          if (!prev && sortedConfigs.length > 0) {
            return sortedConfigs[0].name;
          }
          return prev;
        });
        return;
      }
      
      // Sinon, charger depuis l'API
      setIsLoadingConfigs(true);
      try {
        const response = await loanConfigsAPI.getAll();
        const sortedConfigs = response.items.sort((a, b) => {
          const aDate = (a as any).created_at ? new Date((a as any).created_at).getTime() : a.id;
          const bDate = (b as any).created_at ? new Date((b as any).created_at).getTime() : b.id;
          return aDate - bDate;
        });
        setLoanConfigs(sortedConfigs);
        
        // Si aucun crédit actif et qu'il y a des configs, sélectionner le premier
        setActiveLoanName(prev => {
          if (!prev && sortedConfigs.length > 0) {
            return sortedConfigs[0].name;
          }
          return prev;
        });
      } catch (err) {
        console.error('Erreur lors du chargement des configurations:', err);
      } finally {
        setIsLoadingConfigs(false);
      }
    };

    loadLoanConfigs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshTrigger, externalLoanConfigs?.length, externalLoanConfigs?.map(c => c.id).join(',')]);

  // Charger les mensualités pour le crédit actif
  const loadPayments = async () => {
    if (!activeLoanName || activeLoanName.trim() === '') {
      console.log('🔍 [LoanPaymentTable] Pas de crédit actif, vidage du tableau');
      setPayments([]);
      setIsLoading(false);
      setError(null);
      return;
    }

    console.log(`🔍 [LoanPaymentTable] Chargement des mensualités pour: "${activeLoanName}"`);
    setIsLoading(true);
    setError(null);
    try {
      const response = await loanPaymentsAPI.getAll({
        loan_name: activeLoanName,
        sort_by: 'date',
        sort_direction: 'desc',
        limit: 1000,
      });
      console.log(`✅ [LoanPaymentTable] ${response.items.length} mensualité(s) chargée(s) pour "${activeLoanName}"`);
      setPayments(response.items);
    } catch (err) {
      console.error('❌ [LoanPaymentTable] Erreur lors du chargement des mensualités:', err);
      setError(err instanceof Error ? err.message : 'Erreur lors du chargement');
    } finally {
      setIsLoading(false);
    }
  };

  // Recharger les mensualités quand le crédit actif change ou après un refresh
  useEffect(() => {
    // Réinitialiser les sélections quand on change de crédit
    setSelectedIds(new Set());
    setEditingId(null);
    setEditingValues({});
    // Charger les nouvelles mensualités
    loadPayments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeLoanName, refreshTrigger]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', { year: 'numeric', month: '2-digit', day: '2-digit' });
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('fr-FR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const handleEditStart = (payment: LoanPayment) => {
    setEditingId(payment.id);
    setEditingValues({
      date: payment.date.split('T')[0], // Format YYYY-MM-DD pour input date
      capital: payment.capital,
      interest: payment.interest,
      insurance: payment.insurance,
      total: payment.total,
    });
  };

  const handleEditCancel = () => {
    setEditingId(null);
    setEditingValues({});
  };

  const handleEditSave = async (payment: LoanPayment) => {
    if (savingId === payment.id) return;

    try {
      setSavingId(payment.id);

      // Recalculer le total si capital, interest ou insurance ont changé
      const capital = editingValues.capital !== undefined ? editingValues.capital : payment.capital;
      const interest = editingValues.interest !== undefined ? editingValues.interest : payment.interest;
      const insurance = editingValues.insurance !== undefined ? editingValues.insurance : payment.insurance;
      const calculatedTotal = capital + interest + insurance;

      const updateData: LoanPaymentUpdate = {};
      if (editingValues.date !== undefined) updateData.date = editingValues.date;
      if (editingValues.capital !== undefined) updateData.capital = capital;
      if (editingValues.interest !== undefined) updateData.interest = interest;
      if (editingValues.insurance !== undefined) updateData.insurance = insurance;
      // Toujours mettre à jour le total (recalculé)
      updateData.total = calculatedTotal;

      await loanPaymentsAPI.update(payment.id, updateData);
      
      // Recharger les données
      await loadPayments();
      
      setEditingId(null);
      setEditingValues({});
      
      if (onUpdate) {
        onUpdate();
      }
    } catch (err) {
      console.error('Erreur lors de la sauvegarde:', err);
      alert(err instanceof Error ? err.message : 'Erreur lors de la sauvegarde');
    } finally {
      setSavingId(null);
    }
  };

  const handleDelete = async (payment: LoanPayment) => {
    if (!window.confirm(`Êtes-vous sûr de vouloir supprimer la mensualité du ${formatDate(payment.date)} ?`)) {
      return;
    }

    try {
      setDeletingId(payment.id);
      await loanPaymentsAPI.delete(payment.id);
      await loadPayments();
      
      if (onUpdate) {
        onUpdate();
      }
    } catch (err) {
      console.error('Erreur lors de la suppression:', err);
      alert(err instanceof Error ? err.message : 'Erreur lors de la suppression');
    } finally {
      setDeletingId(null);
    }
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
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(payments.map(p => p.id)));
    }
  };

  const handleDeleteMultiple = async () => {
    if (selectedIds.size === 0) {
      return;
    }

    const count = selectedIds.size;
    if (!window.confirm(`Êtes-vous sûr de vouloir supprimer ${count} mensualité${count > 1 ? 's' : ''} ?`)) {
      return;
    }

    setIsDeletingMultiple(true);
    try {
      // Supprimer les mensualités une par une et ignorer les erreurs 404 (déjà supprimées)
      const deleteResults = await Promise.allSettled(
        Array.from(selectedIds).map(id => loanPaymentsAPI.delete(id))
      );
      
      // Compter les suppressions réussies et les erreurs
      const successful = deleteResults.filter(r => r.status === 'fulfilled').length;
      const failed = deleteResults.filter(r => r.status === 'rejected').length;
      
      if (failed > 0) {
        console.warn(`⚠️ ${failed} mensualité(s) n'ont pas pu être supprimée(s) (peut-être déjà supprimées)`);
      }
      
      setSelectedIds(new Set());
      await loadPayments();
      
      if (onUpdate) {
        onUpdate();
      }
    } catch (err) {
      console.error('Erreur lors de la suppression multiple:', err);
      alert(`Erreur lors de la suppression de ${count} mensualité${count > 1 ? 's' : ''}`);
    } finally {
      setIsDeletingMultiple(false);
    }
  };

  // Calculer les totaux
  const totals = payments.reduce(
    (acc, p) => ({
      capital: acc.capital + p.capital,
      interest: acc.interest + p.interest,
      insurance: acc.insurance + p.insurance,
      total: acc.total + p.total,
    }),
    { capital: 0, interest: 0, insurance: 0, total: 0 }
  );

  // Si pas de configurations, afficher un message
  if (isLoadingConfigs) {
    return (
      <div style={{ padding: '24px', textAlign: 'center', color: '#6b7280' }}>
        Chargement des configurations de crédit...
      </div>
    );
  }

  if (loanConfigs.length === 0) {
    return (
      <div style={{ 
        backgroundColor: 'white', 
        borderRadius: '8px', 
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        padding: '40px',
        textAlign: 'center',
        color: '#6b7280'
      }}>
        Aucune configuration de crédit trouvée. Créez-en une dans la card de configuration ci-dessus.
      </div>
    );
  }

  return (
    <div style={{ 
      backgroundColor: 'white', 
      borderRadius: '8px', 
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      overflow: 'hidden'
    }}>
      {/* Sous-onglets pour chaque crédit */}
      <div style={{ 
        borderBottom: '1px solid #e5e7eb',
        backgroundColor: '#f9fafb'
      }}>
        <div style={{ 
          display: 'flex', 
          gap: '4px',
          padding: '0 16px',
          overflowX: 'auto'
        }}>
          {loanConfigs.map((config) => {
            const isActive = activeLoanName === config.name;
            return (
              <button
                key={config.id}
                onClick={() => {
                  console.log(`🔄 [LoanPaymentTable] Changement d'onglet: "${activeLoanName}" → "${config.name}"`);
                  setActiveLoanName(config.name);
                }}
                style={{
                  padding: '12px 16px',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: isActive ? '#1e3a5f' : '#6b7280',
                  border: 'none',
                  borderBottom: isActive ? '2px solid #1e3a5f' : '2px solid transparent',
                  backgroundColor: 'transparent',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  whiteSpace: 'nowrap',
                }}
                onMouseOver={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.color = '#1e3a5f';
                  }
                }}
                onMouseOut={(e) => {
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

      {/* Contenu du tableau pour le crédit actif */}
      {activeLoanName ? (
        <>
          <div style={{ padding: '16px', borderBottom: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ 
              fontSize: '16px', 
              fontWeight: '600', 
              color: '#1a1a1a',
              margin: 0
            }}>
              Mensualités - {activeLoanName} ({payments.length})
            </h3>
            {selectedIds.size > 0 && (
              <button
                onClick={handleDeleteMultiple}
                disabled={isDeletingMultiple}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#dc2626',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: isDeletingMultiple ? 'not-allowed' : 'pointer',
                  opacity: isDeletingMultiple ? 0.6 : 1,
                }}
              >
                {isDeletingMultiple ? '⏳ Suppression...' : `🗑️ Supprimer ${selectedIds.size} sélectionnée${selectedIds.size > 1 ? 's' : ''}`}
              </button>
            )}
          </div>

          {isLoading ? (
            <div style={{ padding: '24px', textAlign: 'center', color: '#6b7280' }}>
              Chargement des mensualités...
            </div>
          ) : error ? (
            <div style={{ padding: '24px', color: '#dc2626' }}>
              ❌ Erreur: {error}
            </div>
          ) : payments.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
              Aucune mensualité trouvée pour ce crédit. Importez un fichier Excel pour commencer.
            </div>
          ) : (
            <>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
                      <th style={{ padding: '12px', textAlign: 'center', fontWeight: '600', color: '#374151', width: '50px' }}>
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
                      <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>
                        Date
                      </th>
                      <th style={{ padding: '12px', textAlign: 'right', fontWeight: '600', color: '#374151' }}>
                        Capital (€)
                      </th>
                      <th style={{ padding: '12px', textAlign: 'right', fontWeight: '600', color: '#374151' }}>
                        Intérêts (€)
                      </th>
                      <th style={{ padding: '12px', textAlign: 'right', fontWeight: '600', color: '#374151' }}>
                        Assurance (€)
                      </th>
                      <th style={{ padding: '12px', textAlign: 'right', fontWeight: '600', color: '#374151' }}>
                        Total (€)
                      </th>
                      <th style={{ padding: '12px', textAlign: 'center', fontWeight: '600', color: '#374151' }}>
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {payments.map((payment) => {
                      const isEditing = editingId === payment.id;
                      const isSaving = savingId === payment.id;
                      const isDeleting = deletingId === payment.id;
                      const isSelected = selectedIds.has(payment.id);

                      // Calculer le total en temps réel pendant l'édition
                      const currentCapital = editingValues.capital !== undefined ? editingValues.capital : payment.capital;
                      const currentInterest = editingValues.interest !== undefined ? editingValues.interest : payment.interest;
                      const currentInsurance = editingValues.insurance !== undefined ? editingValues.insurance : payment.insurance;
                      const currentTotal = isEditing ? currentCapital + currentInterest + currentInsurance : payment.total;

                      return (
                        <tr 
                          key={payment.id} 
                          style={{ 
                            borderBottom: '1px solid #e5e7eb',
                            backgroundColor: isEditing ? '#f0f9ff' : isSelected ? '#e3f2fd' : 'white',
                            transition: 'background-color 0.2s',
                          }}
                          onMouseEnter={(e) => {
                            if (!isEditing && !isSelected) {
                              e.currentTarget.style.backgroundColor = '#f9f9f9';
                            }
                          }}
                          onMouseLeave={(e) => {
                            if (!isEditing && !isSelected) {
                              e.currentTarget.style.backgroundColor = 'white';
                            } else if (isSelected) {
                              e.currentTarget.style.backgroundColor = '#e3f2fd';
                            }
                          }}
                        >
                          <td style={{ padding: '12px', textAlign: 'center' }}>
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => handleToggleSelect(payment.id)}
                              style={{
                                width: '18px',
                                height: '18px',
                                cursor: 'pointer',
                              }}
                            />
                          </td>
                          <td style={{ padding: '12px', color: '#1a1a1a' }}>
                            {isEditing ? (
                              <input
                                type="date"
                                value={editingValues.date || ''}
                                onChange={(e) => setEditingValues({ ...editingValues, date: e.target.value })}
                                style={{
                                  width: '100%',
                                  padding: '6px 8px',
                                  border: '1px solid #3b82f6',
                                  borderRadius: '4px',
                                  fontSize: '14px'
                                }}
                              />
                            ) : (
                              formatDate(payment.date)
                            )}
                          </td>
                          <td style={{ padding: '12px', textAlign: 'right', color: '#1a1a1a' }}>
                            {isEditing ? (
                              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', justifyContent: 'flex-end' }}>
                                <input
                                  type="number"
                                  step="0.01"
                                  value={editingValues.capital !== undefined ? editingValues.capital : ''}
                                  onChange={(e) => {
                                    const value = parseFloat(e.target.value) || 0;
                                    setEditingValues({ ...editingValues, capital: value });
                                  }}
                                  style={{
                                    width: '120px',
                                    padding: '6px 8px',
                                    border: '1px solid #3b82f6',
                                    borderRadius: '4px',
                                    fontSize: '14px',
                                    textAlign: 'right'
                                  }}
                                />
                                <span style={{ fontSize: '14px', color: '#6b7280' }}>€</span>
                              </div>
                            ) : (
                              formatAmount(payment.capital) + ' €'
                            )}
                          </td>
                          <td style={{ padding: '12px', textAlign: 'right', color: '#1a1a1a' }}>
                            {isEditing ? (
                              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', justifyContent: 'flex-end' }}>
                                <input
                                  type="number"
                                  step="0.01"
                                  value={editingValues.interest !== undefined ? editingValues.interest : ''}
                                  onChange={(e) => {
                                    const value = parseFloat(e.target.value) || 0;
                                    setEditingValues({ ...editingValues, interest: value });
                                  }}
                                  style={{
                                    width: '120px',
                                    padding: '6px 8px',
                                    border: '1px solid #3b82f6',
                                    borderRadius: '4px',
                                    fontSize: '14px',
                                    textAlign: 'right'
                                  }}
                                />
                                <span style={{ fontSize: '14px', color: '#6b7280' }}>€</span>
                              </div>
                            ) : (
                              formatAmount(payment.interest) + ' €'
                            )}
                          </td>
                          <td style={{ padding: '12px', textAlign: 'right', color: '#1a1a1a' }}>
                            {isEditing ? (
                              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', justifyContent: 'flex-end' }}>
                                <input
                                  type="number"
                                  step="0.01"
                                  value={editingValues.insurance !== undefined ? editingValues.insurance : ''}
                                  onChange={(e) => {
                                    const value = parseFloat(e.target.value) || 0;
                                    setEditingValues({ ...editingValues, insurance: value });
                                  }}
                                  style={{
                                    width: '120px',
                                    padding: '6px 8px',
                                    border: '1px solid #3b82f6',
                                    borderRadius: '4px',
                                    fontSize: '14px',
                                    textAlign: 'right'
                                  }}
                                />
                                <span style={{ fontSize: '14px', color: '#6b7280' }}>€</span>
                              </div>
                            ) : (
                              formatAmount(payment.insurance) + ' €'
                            )}
                          </td>
                          <td style={{ padding: '12px', textAlign: 'right', color: '#1a1a1a', fontWeight: '500' }}>
                            {isEditing ? (
                              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', justifyContent: 'flex-end' }}>
                                <span style={{ 
                                  fontSize: '14px',
                                  color: '#1e3a5f',
                                  fontWeight: '500',
                                  padding: '6px 8px',
                                  backgroundColor: '#e0f2fe',
                                  borderRadius: '4px',
                                  minWidth: '120px',
                                  textAlign: 'right',
                                  display: 'inline-block'
                                }}>
                                  {formatAmount(currentTotal)} €
                                </span>
                                <span style={{ fontSize: '12px', color: '#6b7280', fontStyle: 'italic' }}>
                                  (auto)
                                </span>
                              </div>
                            ) : (
                              formatAmount(payment.total) + ' €'
                            )}
                          </td>
                          <td style={{ padding: '12px', textAlign: 'center' }}>
                            {isEditing ? (
                              <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                                <button
                                  onClick={() => handleEditSave(payment)}
                                  disabled={isSaving}
                                  style={{
                                    padding: '6px 12px',
                                    backgroundColor: '#10b981',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    fontSize: '12px',
                                    fontWeight: '500',
                                    cursor: isSaving ? 'not-allowed' : 'pointer',
                                    opacity: isSaving ? 0.6 : 1,
                                  }}
                                >
                                  {isSaving ? '⏳' : '✓'}
                                </button>
                                <button
                                  onClick={handleEditCancel}
                                  disabled={isSaving}
                                  style={{
                                    padding: '6px 12px',
                                    backgroundColor: '#6c757d',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    fontSize: '12px',
                                    fontWeight: '500',
                                    cursor: isSaving ? 'not-allowed' : 'pointer',
                                    opacity: isSaving ? 0.6 : 1,
                                  }}
                                >
                                  ✕
                                </button>
                              </div>
                            ) : (
                              <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                                <button
                                  onClick={() => handleEditStart(payment)}
                                  style={{
                                    padding: '6px 12px',
                                    backgroundColor: '#3b82f6',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    fontSize: '12px',
                                    fontWeight: '500',
                                    cursor: 'pointer',
                                  }}
                                >
                                  ✏️
                                </button>
                                <button
                                  onClick={() => handleDelete(payment)}
                                  disabled={isDeleting}
                                  style={{
                                    padding: '6px 12px',
                                    backgroundColor: '#dc2626',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    fontSize: '12px',
                                    fontWeight: '500',
                                    cursor: isDeleting ? 'not-allowed' : 'pointer',
                                    opacity: isDeleting ? 0.6 : 1,
                                  }}
                                >
                                  {isDeleting ? '⏳' : '🗑️'}
                                </button>
                              </div>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                  {/* Ligne de totaux */}
                  {payments.length > 0 && (
                    <tfoot>
                      <tr style={{ backgroundColor: '#f9fafb', borderTop: '2px solid #e5e7eb', fontWeight: '600' }}>
                        <td style={{ padding: '12px' }}></td>
                        <td style={{ padding: '12px', color: '#1a1a1a' }}>
                          <strong>Total</strong>
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right', color: '#1a1a1a' }}>
                          {formatAmount(totals.capital)} €
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right', color: '#1a1a1a' }}>
                          {formatAmount(totals.interest)} €
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right', color: '#1a1a1a' }}>
                          {formatAmount(totals.insurance)} €
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right', color: '#1e3a5f', fontSize: '16px' }}>
                          {formatAmount(totals.total)} €
                        </td>
                        <td style={{ padding: '12px' }}></td>
                      </tr>
                    </tfoot>
                  )}
                </table>
              </div>
            </>
          )}
        </>
      ) : (
        <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
          Sélectionnez un crédit dans les onglets ci-dessus.
        </div>
      )}
    </div>
  );
}
