/**
 * TransactionsTable component - Tableau des transactions avec tri, pagination et suppression
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect } from 'react';
import { transactionsAPI, Transaction, TransactionUpdate } from '@/api/client';

interface TransactionsTableProps {
  onDelete?: () => void;
}

type SortColumn = 'date' | 'quantite' | 'nom' | 'solde';
type SortDirection = 'asc' | 'desc';

export default function TransactionsTable({ onDelete }: TransactionsTableProps) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [sortColumn, setSortColumn] = useState<SortColumn>('date');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [searchTerm, setSearchTerm] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingValues, setEditingValues] = useState<{ date?: string; nom?: string; quantite?: number }>({});
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [isDeletingMultiple, setIsDeletingMultiple] = useState(false);

  const loadTransactions = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const skip = (page - 1) * pageSize;
      const response = await transactionsAPI.getAll(
        skip,
        pageSize,
        startDate || undefined,
        endDate || undefined
      );
      
      // Filtrer par terme de recherche si présent
      let filtered = response.transactions;
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        filtered = filtered.filter(t => 
          t.nom.toLowerCase().includes(searchLower)
        );
      }

      // Trier les transactions
      filtered.sort((a, b) => {
        let aValue: any;
        let bValue: any;

        switch (sortColumn) {
          case 'date':
            aValue = new Date(a.date).getTime();
            bValue = new Date(b.date).getTime();
            break;
          case 'quantite':
            aValue = a.quantite;
            bValue = b.quantite;
            break;
          case 'nom':
            aValue = a.nom.toLowerCase();
            bValue = b.nom.toLowerCase();
            break;
          case 'solde':
            aValue = a.solde;
            bValue = b.solde;
            break;
          default:
            return 0;
        }

        if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
        if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
        return 0;
      });

      setTransactions(filtered);
      setTotal(response.total);
      
      // Réinitialiser la sélection si les transactions chargées ne contiennent plus les IDs sélectionnés
      setSelectedIds(prev => {
        const loadedIds = new Set(filtered.map(t => t.id));
        const newSet = new Set<number>();
        prev.forEach(id => {
          if (loadedIds.has(id)) {
            newSet.add(id);
          }
        });
        return newSet;
      });
    } catch (err) {
      console.error('Error loading transactions:', err);
      setError(err instanceof Error ? err.message : 'Erreur lors du chargement');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadTransactions();
  }, [page, pageSize, sortColumn, sortDirection, startDate, endDate]);

  // Recharger quand le terme de recherche change (avec debounce)
  useEffect(() => {
    const timer = setTimeout(() => {
      loadTransactions();
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  const handleSort = (column: SortColumn) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette transaction ?')) {
      return;
    }

    setDeletingId(id);
    try {
      await transactionsAPI.delete(id);
      setSelectedIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
      await loadTransactions();
      if (onDelete) {
        onDelete();
      }
    } catch (err) {
      console.error('Error deleting transaction:', err);
      alert('Erreur lors de la suppression de la transaction');
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
    if (selectedIds.size === transactions.length) {
      // Tout désélectionner
      setSelectedIds(new Set());
    } else {
      // Tout sélectionner
      setSelectedIds(new Set(transactions.map(t => t.id)));
    }
  };

  const handleDeleteMultiple = async () => {
    if (selectedIds.size === 0) {
      return;
    }

    const count = selectedIds.size;
    if (!confirm(`Êtes-vous sûr de vouloir supprimer ${count} transaction${count > 1 ? 's' : ''} ?`)) {
      return;
    }

    setIsDeletingMultiple(true);
    try {
      // Supprimer toutes les transactions sélectionnées
      const deletePromises = Array.from(selectedIds).map(id => transactionsAPI.delete(id));
      await Promise.all(deletePromises);
      
      setSelectedIds(new Set());
      await loadTransactions();
      if (onDelete) {
        onDelete();
      }
    } catch (err) {
      console.error('Error deleting transactions:', err);
      alert(`Erreur lors de la suppression de ${count} transaction${count > 1 ? 's' : ''}`);
    } finally {
      setIsDeletingMultiple(false);
    }
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
  };

  const formatAmount = (amount: number): string => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const handleEdit = (transaction: Transaction) => {
    setEditingId(transaction.id);
    // Convertir la date au format YYYY-MM-DD pour l'input
    const dateObj = new Date(transaction.date);
    const year = dateObj.getFullYear();
    const month = String(dateObj.getMonth() + 1).padStart(2, '0');
    const day = String(dateObj.getDate()).padStart(2, '0');
    setEditingValues({
      date: `${year}-${month}-${day}`,
      nom: transaction.nom,
      quantite: transaction.quantite,
    });
  };

  const handleSaveEdit = async (transaction: Transaction) => {
    try {
      const updates: TransactionUpdate = {};
      
      // Vérifier si les valeurs ont changé
      const dateObj = new Date(transaction.date);
      const year = dateObj.getFullYear();
      const month = String(dateObj.getMonth() + 1).padStart(2, '0');
      const day = String(dateObj.getDate()).padStart(2, '0');
      const currentDateStr = `${year}-${month}-${day}`;
      
      if (editingValues.date && editingValues.date !== currentDateStr) {
        updates.date = editingValues.date;
      }
      if (editingValues.nom !== undefined && editingValues.nom !== transaction.nom) {
        updates.nom = editingValues.nom;
      }
      if (editingValues.quantite !== undefined && editingValues.quantite !== transaction.quantite) {
        updates.quantite = editingValues.quantite;
      }

      // Si des modifications ont été faites, sauvegarder
      if (Object.keys(updates).length > 0) {
        await transactionsAPI.update(transaction.id, updates);
        setEditingId(null);
        setEditingValues({});
        await loadTransactions();
        if (onDelete) {
          onDelete();
        }
      } else {
        // Aucune modification, juste annuler l'édition
        setEditingId(null);
        setEditingValues({});
      }
    } catch (err: any) {
      console.error('Error updating transaction:', err);
      alert(`Erreur lors de la modification: ${err.message || 'Erreur inconnue'}`);
    }
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditingValues({});
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div>
      {/* Filtres et recherche */}
      <div style={{ 
        marginBottom: '24px', 
        padding: '16px', 
        backgroundColor: '#f5f5f5', 
        borderRadius: '8px',
        display: 'flex',
        flexWrap: 'wrap',
        gap: '12px',
        alignItems: 'flex-end'
      }}>
        <div style={{ flex: 1, minWidth: '200px' }}>
          <label style={{ display: 'block', fontSize: '12px', color: '#666', marginBottom: '4px' }}>
            Recherche par nom
          </label>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Rechercher une transaction..."
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              fontSize: '14px',
            }}
          />
        </div>
        <div style={{ minWidth: '150px' }}>
          <label style={{ display: 'block', fontSize: '12px', color: '#666', marginBottom: '4px' }}>
            Date début
          </label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              fontSize: '14px',
            }}
          />
        </div>
        <div style={{ minWidth: '150px' }}>
          <label style={{ display: 'block', fontSize: '12px', color: '#666', marginBottom: '4px' }}>
            Date fin
          </label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              fontSize: '14px',
            }}
          />
        </div>
        <div>
          <button
            onClick={() => {
              setSearchTerm('');
              setStartDate('');
              setEndDate('');
              setPage(1);
            }}
            style={{
              padding: '8px 16px',
              backgroundColor: '#6b7280',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '14px',
              cursor: 'pointer',
            }}
          >
            Réinitialiser
          </button>
        </div>
      </div>

      {/* Statistiques et actions de sélection */}
      <div style={{ 
        marginBottom: '16px', 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div style={{ fontSize: '14px', color: '#666' }}>
          {total} transaction{total !== 1 ? 's' : ''} au total
          {searchTerm && ` (filtrées par "${searchTerm}")`}
          {(startDate || endDate) && ` (période: ${startDate || 'début'} - ${endDate || 'fin'})`}
        </div>
        {selectedIds.size > 0 && (
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <span style={{ fontSize: '14px', color: '#1e3a5f', fontWeight: '500' }}>
              {selectedIds.size} transaction{selectedIds.size > 1 ? 's' : ''} sélectionnée{selectedIds.size > 1 ? 's' : ''}
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

      {/* Tableau */}
      {isLoading ? (
        <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
          ⏳ Chargement des transactions...
        </div>
      ) : error ? (
        <div style={{ padding: '40px', textAlign: 'center', color: '#dc3545' }}>
          ❌ {error}
        </div>
      ) : transactions.length === 0 ? (
        <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
          Aucune transaction trouvée
        </div>
      ) : (
        <>
          <div style={{ 
            backgroundColor: 'white', 
            borderRadius: '8px', 
            border: '1px solid #e5e5e5',
            overflow: 'auto'
          }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
              <thead>
                <tr style={{ backgroundColor: '#f5f5f5', borderBottom: '2px solid #e5e5e5' }}>
                  <th style={{ 
                    padding: '12px', 
                    textAlign: 'center', 
                    fontWeight: '600', 
                    color: '#1a1a1a',
                    width: '50px'
                  }}>
                    <input
                      type="checkbox"
                      checked={transactions.length > 0 && selectedIds.size === transactions.length}
                      onChange={handleSelectAll}
                      style={{
                        width: '18px',
                        height: '18px',
                        cursor: 'pointer',
                      }}
                    />
                  </th>
                  <th
                    onClick={() => handleSort('date')}
                    style={{
                      padding: '12px',
                      textAlign: 'left',
                      fontWeight: '600',
                      color: '#1a1a1a',
                      cursor: 'pointer',
                      userSelect: 'none',
                    }}
                  >
                    Date {sortColumn === 'date' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    onClick={() => handleSort('quantite')}
                    style={{
                      padding: '12px',
                      textAlign: 'right',
                      fontWeight: '600',
                      color: '#1a1a1a',
                      cursor: 'pointer',
                      userSelect: 'none',
                    }}
                  >
                    Quantité {sortColumn === 'quantite' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    onClick={() => handleSort('nom')}
                    style={{
                      padding: '12px',
                      textAlign: 'left',
                      fontWeight: '600',
                      color: '#1a1a1a',
                      cursor: 'pointer',
                      userSelect: 'none',
                    }}
                  >
                    Nom {sortColumn === 'nom' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    onClick={() => handleSort('solde')}
                    style={{
                      padding: '12px',
                      textAlign: 'right',
                      fontWeight: '600',
                      color: '#1a1a1a',
                      cursor: 'pointer',
                      userSelect: 'none',
                    }}
                  >
                    Solde {sortColumn === 'solde' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#1a1a1a' }}>
                    Level 1
                  </th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#1a1a1a' }}>
                    Level 2
                  </th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#1a1a1a' }}>
                    Level 3
                  </th>
                  <th style={{ padding: '12px', textAlign: 'center', fontWeight: '600', color: '#1a1a1a' }}>
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((transaction) => (
                  <tr
                    key={transaction.id}
                    style={{
                      borderBottom: '1px solid #e5e5e5',
                      transition: 'background-color 0.2s',
                      backgroundColor: selectedIds.has(transaction.id) ? '#e3f2fd' : 'white',
                    }}
                    onMouseEnter={(e) => {
                      if (!selectedIds.has(transaction.id)) {
                        e.currentTarget.style.backgroundColor = '#f9f9f9';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!selectedIds.has(transaction.id)) {
                        e.currentTarget.style.backgroundColor = 'white';
                      } else {
                        e.currentTarget.style.backgroundColor = '#e3f2fd';
                      }
                    }}
                  >
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      <input
                        type="checkbox"
                        checked={selectedIds.has(transaction.id)}
                        onChange={() => handleToggleSelect(transaction.id)}
                        style={{
                          width: '18px',
                          height: '18px',
                          cursor: 'pointer',
                        }}
                      />
                    </td>
                    <td style={{ padding: '12px', color: '#1a1a1a' }}>
                      {editingId === transaction.id ? (
                        <input
                          type="date"
                          value={editingValues.date || ''}
                          onChange={(e) => setEditingValues({ ...editingValues, date: e.target.value })}
                          style={{ width: '100%', padding: '4px', border: '1px solid #ddd', borderRadius: '2px' }}
                        />
                      ) : (
                        formatDate(transaction.date)
                      )}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'right', color: transaction.quantite >= 0 ? '#10b981' : '#ef4444' }}>
                      {editingId === transaction.id ? (
                        <input
                          type="number"
                          step="0.01"
                          value={editingValues.quantite !== undefined ? editingValues.quantite : ''}
                          onChange={(e) => setEditingValues({ ...editingValues, quantite: parseFloat(e.target.value) || 0 })}
                          style={{ width: '100%', padding: '4px', border: '1px solid #ddd', borderRadius: '2px', textAlign: 'right' }}
                        />
                      ) : (
                        formatAmount(transaction.quantite)
                      )}
                    </td>
                    <td style={{ padding: '12px', maxWidth: '400px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {editingId === transaction.id ? (
                        <input
                          type="text"
                          value={editingValues.nom !== undefined ? editingValues.nom : ''}
                          onChange={(e) => setEditingValues({ ...editingValues, nom: e.target.value })}
                          style={{ width: '100%', padding: '4px', border: '1px solid #ddd', borderRadius: '2px' }}
                        />
                      ) : (
                        <span style={{ 
                          color: transaction.nom.startsWith('nom_a_justifier_') ? '#dc3545' : '#666',
                          fontWeight: transaction.nom.startsWith('nom_a_justifier_') ? '500' : 'normal',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px'
                        }}>
                          {transaction.nom.startsWith('nom_a_justifier_') && (
                            <span style={{ fontSize: '14px' }}>⚠️</span>
                          )}
                          {transaction.nom}
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'right', color: '#1a1a1a', fontWeight: '500' }}>
                      {formatAmount(transaction.solde)}
                    </td>
                    <td style={{ padding: '12px', color: transaction.level_1 ? '#666' : '#999', fontStyle: transaction.level_1 ? 'normal' : 'italic' }}>
                      {transaction.level_1 || 'à remplir'}
                    </td>
                    <td style={{ padding: '12px', color: transaction.level_2 ? '#666' : '#999', fontStyle: transaction.level_2 ? 'normal' : 'italic' }}>
                      {transaction.level_2 || 'à remplir'}
                    </td>
                    <td style={{ padding: '12px', color: transaction.level_3 ? '#666' : '#999', fontStyle: transaction.level_3 ? 'normal' : 'italic' }}>
                      {transaction.level_3 || 'à remplir'}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                        {editingId === transaction.id ? (
                          <button
                            onClick={() => handleSaveEdit(transaction)}
                            style={{
                              padding: '6px 12px',
                              backgroundColor: '#28a745',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              fontSize: '12px',
                              cursor: 'pointer',
                            }}
                          >
                            ✓
                          </button>
                        ) : (
                          <button
                            onClick={() => handleEdit(transaction)}
                            style={{
                              padding: '6px 12px',
                              backgroundColor: '#1e3a5f',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              fontSize: '12px',
                              cursor: 'pointer',
                            }}
                          >
                            ✏️
                          </button>
                        )}
                        {editingId === transaction.id ? (
                          <button
                            onClick={handleCancelEdit}
                            style={{
                              padding: '6px 12px',
                              backgroundColor: '#6c757d',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              fontSize: '12px',
                              cursor: 'pointer',
                            }}
                          >
                            ✗
                          </button>
                        ) : (
                          <button
                            onClick={() => handleDelete(transaction.id)}
                            disabled={deletingId === transaction.id}
                            style={{
                              padding: '6px 12px',
                              backgroundColor: deletingId === transaction.id ? '#ccc' : '#dc3545',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              fontSize: '12px',
                              cursor: deletingId === transaction.id ? 'not-allowed' : 'pointer',
                              opacity: deletingId === transaction.id ? 0.6 : 1,
                            }}
                          >
                            {deletingId === transaction.id ? '⏳' : '🗑️'}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div style={{ 
              marginTop: '24px', 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '12px'
            }}>
              <div style={{ fontSize: '14px', color: '#666' }}>
                Page {page} sur {totalPages} ({total} transaction{total !== 1 ? 's' : ''})
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={() => setPage(1)}
                  disabled={page === 1}
                  style={{
                    padding: '8px 12px',
                    backgroundColor: page === 1 ? '#e5e5e5' : '#1e3a5f',
                    color: page === 1 ? '#999' : 'white',
                    border: 'none',
                    borderRadius: '4px',
                    fontSize: '14px',
                    cursor: page === 1 ? 'not-allowed' : 'pointer',
                  }}
                >
                  « Première
                </button>
                <button
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                  style={{
                    padding: '8px 12px',
                    backgroundColor: page === 1 ? '#e5e5e5' : '#1e3a5f',
                    color: page === 1 ? '#999' : 'white',
                    border: 'none',
                    borderRadius: '4px',
                    fontSize: '14px',
                    cursor: page === 1 ? 'not-allowed' : 'pointer',
                  }}
                >
                  ‹ Précédente
                </button>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={page >= totalPages}
                  style={{
                    padding: '8px 12px',
                    backgroundColor: page >= totalPages ? '#e5e5e5' : '#1e3a5f',
                    color: page >= totalPages ? '#999' : 'white',
                    border: 'none',
                    borderRadius: '4px',
                    fontSize: '14px',
                    cursor: page >= totalPages ? 'not-allowed' : 'pointer',
                  }}
                >
                  Suivante ›
                </button>
                <button
                  onClick={() => setPage(totalPages)}
                  disabled={page >= totalPages}
                  style={{
                    padding: '8px 12px',
                    backgroundColor: page >= totalPages ? '#e5e5e5' : '#1e3a5f',
                    color: page >= totalPages ? '#999' : 'white',
                    border: 'none',
                    borderRadius: '4px',
                    fontSize: '14px',
                    cursor: page >= totalPages ? 'not-allowed' : 'pointer',
                  }}
                >
                  Dernière »
                </button>
              </div>
              <div>
                <label style={{ fontSize: '14px', color: '#666', marginRight: '8px' }}>
                  Par page:
                </label>
                <select
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setPage(1);
                  }}
                  style={{
                    padding: '6px 12px',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                    fontSize: '14px',
                  }}
                >
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                  <option value={200}>200</option>
                </select>
              </div>
            </div>
          )}
        </>
      )}

    </div>
  );
}

