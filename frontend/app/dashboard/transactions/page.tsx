/**
 * Transactions page
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useSearchParams } from 'next/navigation';
import { useState, useEffect } from 'react';
import FileUpload from '@/components/FileUpload';
import ImportLog from '@/components/ImportLog';
import TransactionsTable from '@/components/TransactionsTable';
import { transactionsAPI } from '@/api/client';
import { useImportLog } from '@/contexts/ImportLogContext';

export default function TransactionsPage() {
  const searchParams = useSearchParams();
  const filter = searchParams?.get('filter');
  const tab = searchParams?.get('tab');
  const [transactionCount, setTransactionCount] = useState<number | null>(null);
  const [isLoadingCount, setIsLoadingCount] = useState(false);
  const { clearLogs } = useImportLog();
  const [historyCleared, setHistoryCleared] = useState(false);

  const loadTransactionCount = async () => {
    setIsLoadingCount(true);
    try {
      const response = await transactionsAPI.getAll(0, 1);
      setTransactionCount(response.total);
    } catch (error) {
      console.error('Error loading transaction count:', error);
      setTransactionCount(null);
    } finally {
      setIsLoadingCount(false);
    }
  };

  useEffect(() => {
    if (tab === 'load_trades') {
      loadTransactionCount();
    }
  }, [tab]);

  const handleFileSelect = (file: File) => {
    console.log('📁 [TransactionsPage] Fichier sélectionné:', file.name);
    // Le preview est maintenant géré automatiquement dans FileUpload
  };

  const handleImportComplete = () => {
    console.log('✅ [TransactionsPage] Import terminé');
    // Recharger le compteur après import
    loadTransactionCount();
    // Le tableau se rechargera automatiquement via son propre useEffect
  };

  const handleTransactionCountChange = (count: number) => {
    setTransactionCount(count);
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* Contenu selon l'onglet actif */}
      <div style={{ 
        backgroundColor: 'white', 
        borderRadius: '8px', 
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        padding: '24px',
        minHeight: '400px'
      }}>
        {(!filter && !tab) && (
          <TransactionsTable onDelete={handleImportComplete} />
        )}

        {filter === 'unclassified' && (
          <div>
            <p style={{ fontSize: '14px', color: '#666' }}>
              Les transactions non classées seront affichées ici (à implémenter après enrichissement).
            </p>
          </div>
        )}

        {filter === 'to_validate' && (
          <div>
            <p style={{ fontSize: '14px', color: '#666' }}>
              Les transactions à valider seront affichées ici (à implémenter après enrichissement).
            </p>
          </div>
        )}

        {tab === 'load_trades' && (
          <div>
            {/* Header avec bouton Load Trades et compteur */}
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'flex-start',
              marginBottom: '24px',
              gap: '24px'
            }}>
              <div style={{ flex: 1 }}>
                {/* Le FileUpload contient déjà le bouton Load Trades */}
                <FileUpload onFileSelect={handleFileSelect} onImportComplete={handleImportComplete} />
              </div>
              <div style={{ 
                display: 'flex',
                gap: '12px',
                alignItems: 'flex-start'
              }}>
                <div style={{ 
                  padding: '12px 20px', 
                  backgroundColor: '#f5f5f5', 
                  borderRadius: '8px',
                  border: '1px solid #e5e5e5',
                  minWidth: '200px',
                  textAlign: 'center',
                  flexShrink: 0
                }}>
                  <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
                    Transactions en BDD
                  </div>
                  {isLoadingCount ? (
                    <div style={{ fontSize: '20px', fontWeight: '600', color: '#1e3a5f' }}>
                      ⏳ Chargement...
                    </div>
                  ) : transactionCount !== null ? (
                    <div style={{ fontSize: '24px', fontWeight: '600', color: '#1e3a5f' }}>
                      {transactionCount} transaction{transactionCount !== 1 ? 's' : ''}
                    </div>
                  ) : (
                    <div style={{ fontSize: '14px', color: '#dc3545' }}>
                      ❌ Erreur de chargement
                    </div>
                  )}
                  <button
                    onClick={loadTransactionCount}
                    style={{
                      marginTop: '8px',
                      padding: '4px 12px',
                      fontSize: '12px',
                      backgroundColor: '#1e3a5f',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                    }}
                  >
                    🔄 Actualiser
                  </button>
                </div>
                <button
                  onClick={() => {
                    if (confirm('Êtes-vous sûr de vouloir supprimer l\'historique des logs ?')) {
                      clearLogs();
                      setHistoryCleared(true);
                    }
                  }}
                  style={{
                    padding: '12px 20px',
                    backgroundColor: '#dc3545',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '14px',
                    fontWeight: '500',
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                    height: 'fit-content',
                  }}
                >
                  🗑️ Clear logs
                </button>
              </div>
            </div>
            
            <div style={{ 
              marginTop: '24px', 
              padding: '16px', 
              backgroundColor: '#f9f9f9', 
              borderRadius: '4px',
              fontSize: '14px',
              color: '#666',
              marginBottom: '24px'
            }}>
              <p style={{ margin: 0 }}>
                Sélectionnez un fichier CSV pour charger vos transactions. 
                Le fichier sera analysé et vous pourrez confirmer le mapping des colonnes.
              </p>
            </div>

            {/* Historique des imports */}
            <ImportLog 
              hideHeader={true} 
              onTransactionCountChange={handleTransactionCountChange}
              hideDbHistory={historyCleared}
            />
          </div>
        )}
      </div>
    </div>
  );
}

