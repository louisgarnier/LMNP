/**
 * PivotDetailsTable component - Affichage des transactions détaillées d'une cellule du tableau croisé
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect } from 'react';
import { analyticsAPI, Transaction, TransactionListResponse } from '@/api/client';
import { PivotFieldConfig } from './PivotFieldSelector';

interface PivotDetailsTableProps {
  config: PivotFieldConfig;
  rowValues: (string | number)[];
  columnValues: (string | number)[];
  onClose?: () => void;
}

export default function PivotDetailsTable({ 
  config, 
  rowValues, 
  columnValues, 
  onClose 
}: PivotDetailsTableProps) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);

  // Charger les transactions quand les paramètres changent
  useEffect(() => {
    const loadTransactions = async () => {
      // Ne pas charger si pas de valeurs
      if (rowValues.length === 0 && columnValues.length === 0) {
        setTransactions([]);
        setTotal(0);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const skip = (page - 1) * pageSize;
        
        // Construire les valeurs pour correspondre exactement au nombre de champs
        // Si config.rows = [level_1, level_2, level_3] mais qu'on clique sur un nœud de niveau 1,
        // rowValues sera ['Daily'] (1 valeur), mais on doit envoyer ['Daily', null, null] (3 valeurs)
        const filteredRowValues: (string | number | null)[] = [];
        if (config.rows.length > 0) {
          for (let i = 0; i < config.rows.length; i++) {
            filteredRowValues.push(i < rowValues.length ? rowValues[i] : null);
          }
        }
        
        const filteredColumnValues: (string | number | null)[] = [];
        if (config.columns.length > 0) {
          for (let i = 0; i < config.columns.length; i++) {
            filteredColumnValues.push(i < columnValues.length ? columnValues[i] : null);
          }
        }
        
        // Préparer les paramètres pour l'API
        const params = {
          rows: config.rows.length > 0 ? config.rows.join(',') : undefined,
          columns: config.columns.length > 0 ? config.columns.join(',') : undefined,
          row_values: filteredRowValues.length > 0 ? JSON.stringify(filteredRowValues) : undefined,
          column_values: filteredColumnValues.length > 0 ? JSON.stringify(filteredColumnValues) : undefined,
          filters: config.filters && Object.keys(config.filters).length > 0 
            ? JSON.stringify(config.filters) 
            : undefined,
        };

        const response: TransactionListResponse = await analyticsAPI.getPivotDetails(
          params,
          skip,
          pageSize
        );

        setTransactions(response.transactions);
        setTotal(response.total);
      } catch (err: any) {
        setError(err.message || 'Erreur lors du chargement des transactions');
        console.error('Erreur chargement transactions:', err);
        setTransactions([]);
        setTotal(0);
      } finally {
        setIsLoading(false);
      }
    };

    loadTransactions();
  }, [config, rowValues, columnValues, page, pageSize]);

  // Réinitialiser la page quand les valeurs changent
  useEffect(() => {
    setPage(1);
  }, [rowValues, columnValues]);

  const totalPages = Math.ceil(total / pageSize);

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('fr-FR');
    } catch {
      return dateString;
    }
  };

  if (rowValues.length === 0 && columnValues.length === 0) {
    return null;
  }

  return (
    <div style={{ 
      marginTop: '24px', 
      padding: '16px', 
      backgroundColor: '#ffffff', 
      borderRadius: '8px',
      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
    }}>
      {/* En-tête */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: '16px' 
      }}>
        <h3 style={{ 
          fontSize: '16px', 
          fontWeight: '600', 
          color: '#111827', 
          margin: 0 
        }}>
          Transactions détaillées
          {total > 0 && (
            <span style={{ 
              fontSize: '14px', 
              fontWeight: '400', 
              color: '#6b7280', 
              marginLeft: '8px' 
            }}>
              ({total} transaction{total > 1 ? 's' : ''})
            </span>
          )}
        </h3>
        {onClose && (
          <button
            onClick={onClose}
            style={{
              padding: '6px 12px',
              fontSize: '12px',
              border: '1px solid #d1d5db',
              borderRadius: '4px',
              backgroundColor: '#ffffff',
              color: '#374151',
              cursor: 'pointer',
            }}
          >
            Fermer
          </button>
        )}
      </div>

      {/* Erreur */}
      {error && (
        <div style={{ 
          padding: '12px', 
          backgroundColor: '#fee2e2', 
          color: '#991b1b', 
          borderRadius: '4px', 
          marginBottom: '16px' 
        }}>
          {error}
        </div>
      )}

      {/* Chargement */}
      {isLoading && (
        <div style={{ 
          padding: '24px', 
          textAlign: 'center', 
          color: '#6b7280' 
        }}>
          ⏳ Chargement des transactions...
        </div>
      )}

      {/* Tableau */}
      {!isLoading && !error && (
        <>
          {transactions.length === 0 ? (
            <div style={{ 
              padding: '24px', 
              textAlign: 'center', 
              color: '#6b7280' 
            }}>
              Aucune transaction trouvée
            </div>
          ) : (
            <>
              {/* Tableau */}
              <div style={{ overflowX: 'auto', marginBottom: '16px' }}>
                <table style={{ 
                  width: '100%', 
                  borderCollapse: 'collapse', 
                  fontSize: '13px' 
                }}>
                  <thead>
                    <tr style={{ backgroundColor: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
                      <th style={{ 
                        padding: '10px 12px', 
                        textAlign: 'left', 
                        fontWeight: '600', 
                        color: '#374151',
                        borderRight: '1px solid #e5e7eb'
                      }}>
                        Date
                      </th>
                      <th style={{ 
                        padding: '10px 12px', 
                        textAlign: 'left', 
                        fontWeight: '600', 
                        color: '#374151',
                        borderRight: '1px solid #e5e7eb'
                      }}>
                        Nom
                      </th>
                      <th style={{ 
                        padding: '10px 12px', 
                        textAlign: 'right', 
                        fontWeight: '600', 
                        color: '#374151',
                        borderRight: '1px solid #e5e7eb'
                      }}>
                        Quantité
                      </th>
                      <th style={{ 
                        padding: '10px 12px', 
                        textAlign: 'right', 
                        fontWeight: '600', 
                        color: '#374151',
                        borderRight: '1px solid #e5e7eb'
                      }}>
                        Solde
                      </th>
                      <th style={{ 
                        padding: '10px 12px', 
                        textAlign: 'left', 
                        fontWeight: '600', 
                        color: '#374151',
                        borderRight: '1px solid #e5e7eb'
                      }}>
                        Level 1
                      </th>
                      <th style={{ 
                        padding: '10px 12px', 
                        textAlign: 'left', 
                        fontWeight: '600', 
                        color: '#374151',
                        borderRight: '1px solid #e5e7eb'
                      }}>
                        Level 2
                      </th>
                      <th style={{ 
                        padding: '10px 12px', 
                        textAlign: 'left', 
                        fontWeight: '600', 
                        color: '#374151'
                      }}>
                        Level 3
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map((transaction) => (
                      <tr 
                        key={transaction.id}
                        style={{ 
                          borderBottom: '1px solid #e5e7eb',
                          backgroundColor: '#ffffff'
                        }}
                      >
                        <td style={{ 
                          padding: '10px 12px', 
                          color: '#111827',
                          borderRight: '1px solid #e5e7eb'
                        }}>
                          {formatDate(transaction.date)}
                        </td>
                        <td style={{ 
                          padding: '10px 12px', 
                          color: '#111827',
                          borderRight: '1px solid #e5e7eb'
                        }}>
                          {transaction.nom}
                        </td>
                        <td style={{ 
                          padding: '10px 12px', 
                          textAlign: 'right', 
                          color: '#111827',
                          borderRight: '1px solid #e5e7eb'
                        }}>
                          {transaction.quantite.toLocaleString('fr-FR', { 
                            minimumFractionDigits: 2, 
                            maximumFractionDigits: 2 
                          })}
                        </td>
                        <td style={{ 
                          padding: '10px 12px', 
                          textAlign: 'right', 
                          color: '#111827',
                          borderRight: '1px solid #e5e7eb'
                        }}>
                          {transaction.solde.toLocaleString('fr-FR', { 
                            minimumFractionDigits: 2, 
                            maximumFractionDigits: 2 
                          })}
                        </td>
                        <td style={{ 
                          padding: '10px 12px', 
                          color: transaction.level_1 ? '#111827' : '#9ca3af',
                          borderRight: '1px solid #e5e7eb'
                        }}>
                          {transaction.level_1 || 'unassigned'}
                        </td>
                        <td style={{ 
                          padding: '10px 12px', 
                          color: transaction.level_2 ? '#111827' : '#9ca3af',
                          borderRight: '1px solid #e5e7eb'
                        }}>
                          {transaction.level_2 || 'unassigned'}
                        </td>
                        <td style={{ 
                          padding: '10px 12px', 
                          color: transaction.level_3 ? '#111827' : '#9ca3af'
                        }}>
                          {transaction.level_3 || 'unassigned'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center',
                  padding: '12px 0',
                  borderTop: '1px solid #e5e7eb'
                }}>
                  <div style={{ fontSize: '13px', color: '#6b7280' }}>
                    Page {page} sur {totalPages} (total: {total} transaction{total > 1 ? 's' : ''})
                  </div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <button
                      onClick={() => setPage(1)}
                      disabled={page === 1}
                      style={{
                        padding: '6px 12px',
                        fontSize: '12px',
                        border: '1px solid #d1d5db',
                        borderRadius: '4px',
                        backgroundColor: page === 1 ? '#f9fafb' : '#ffffff',
                        color: page === 1 ? '#9ca3af' : '#374151',
                        cursor: page === 1 ? 'not-allowed' : 'pointer',
                      }}
                    >
                      « Première
                    </button>
                    <button
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                      disabled={page === 1}
                      style={{
                        padding: '6px 12px',
                        fontSize: '12px',
                        border: '1px solid #d1d5db',
                        borderRadius: '4px',
                        backgroundColor: page === 1 ? '#f9fafb' : '#ffffff',
                        color: page === 1 ? '#9ca3af' : '#374151',
                        cursor: page === 1 ? 'not-allowed' : 'pointer',
                      }}
                    >
                      ‹ Précédente
                    </button>
                    <button
                      onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                      style={{
                        padding: '6px 12px',
                        fontSize: '12px',
                        border: '1px solid #d1d5db',
                        borderRadius: '4px',
                        backgroundColor: page === totalPages ? '#f9fafb' : '#ffffff',
                        color: page === totalPages ? '#9ca3af' : '#374151',
                        cursor: page === totalPages ? 'not-allowed' : 'pointer',
                      }}
                    >
                      Suivante ›
                    </button>
                    <button
                      onClick={() => setPage(totalPages)}
                      disabled={page === totalPages}
                      style={{
                        padding: '6px 12px',
                        fontSize: '12px',
                        border: '1px solid #d1d5db',
                        borderRadius: '4px',
                        backgroundColor: page === totalPages ? '#f9fafb' : '#ffffff',
                        color: page === totalPages ? '#9ca3af' : '#374151',
                        cursor: page === totalPages ? 'not-allowed' : 'pointer',
                      }}
                    >
                      Dernière »
                    </button>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span style={{ fontSize: '13px', color: '#6b7280' }}>Par page:</span>
                    <select
                      value={pageSize}
                      onChange={(e) => {
                        setPageSize(Number(e.target.value));
                        setPage(1);
                      }}
                      style={{
                        padding: '6px 8px',
                        fontSize: '12px',
                        border: '1px solid #d1d5db',
                        borderRadius: '4px',
                        backgroundColor: '#ffffff',
                        color: '#374151',
                      }}
                    >
                      <option value={50}>50</option>
                      <option value={100}>100</option>
                      <option value={200}>200</option>
                    </select>
                  </div>
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}

