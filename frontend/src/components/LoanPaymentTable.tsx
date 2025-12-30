/**
 * LoanPaymentTable component - Tableau d'affichage des mensualités de crédit
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect } from 'react';
import { loanPaymentsAPI, LoanPayment } from '@/api/client';

interface LoanPaymentTableProps {
  loanName?: string;
  refreshKey?: number;
}

export default function LoanPaymentTable({ loanName = 'Prêt principal', refreshKey }: LoanPaymentTableProps) {
  const [payments, setPayments] = useState<LoanPayment[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingPayment, setEditingPayment] = useState<Partial<LoanPayment> | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [isDeletingMultiple, setIsDeletingMultiple] = useState(false);

  useEffect(() => {
    loadPayments();
  }, [loanName, refreshKey]);

  const loadPayments = async () => {
    setLoading(true);
    try {
      const response = await loanPaymentsAPI.getAll({ loan_name: loanName });
      // Trier par date (plus récent en premier)
      const sorted = response.payments.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
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
      await loanPaymentsAPI.update(editingId, {
        date: editingPayment.date,
        capital: editingPayment.capital,
        interest: editingPayment.interest,
        insurance: editingPayment.insurance,
        total: editingPayment.total,
      });
      await loadPayments();
      setEditingId(null);
      setEditingPayment(null);
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
      alert('❌ Erreur lors de la sauvegarde');
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
      await loadPayments();
    } catch (error) {
      console.error('Erreur lors de la suppression:', error);
      alert(`❌ Erreur lors de la suppression de ${count} mensualité${count > 1 ? 's' : ''}`);
    } finally {
      setIsDeletingMultiple(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '20px', color: '#6b7280' }}>
        Chargement...
      </div>
    );
  }

  if (payments.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '20px', color: '#6b7280' }}>
        Aucune mensualité enregistrée pour "{loanName}".
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#111827' }}>
          Mensualités pour "{loanName}" ({payments.length} enregistrement(s))
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
                        value={editingPayment?.date?.split('T')[0] || ''}
                        onChange={(e) => setEditingPayment(prev => prev ? { ...prev, date: e.target.value } : null)}
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
                                loadPayments();
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
          </tbody>
        </table>
      </div>
    </div>
  );
}

