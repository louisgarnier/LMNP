/**
 * Transactions page
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useSearchParams } from 'next/navigation';
import { useState, useEffect, useRef } from 'react';
import FileUpload from '@/components/FileUpload';
import ImportLog from '@/components/ImportLog';
import TransactionsTable from '@/components/TransactionsTable';
import UnclassifiedTransactionsTable from '@/components/UnclassifiedTransactionsTable';
import MappingTable, { MappingTableRef } from '@/components/MappingTable';
import MappingFileUpload from '@/components/MappingFileUpload';
import MappingImportLog from '@/components/MappingImportLog';
import AllowedMappingsTable from '@/components/AllowedMappingsTable';
import { transactionsAPI, mappingsAPI, fileUploadAPI } from '@/api/client';
import { useImportLog } from '@/contexts/ImportLogContext';

export default function TransactionsPage() {
  const searchParams = useSearchParams();
  const filter = searchParams?.get('filter');
  const tab = searchParams?.get('tab');
  const [transactionCount, setTransactionCount] = useState<number | null>(null);
  const [isLoadingCount, setIsLoadingCount] = useState(false);
  const [mappingCount, setMappingCount] = useState<number | null>(null);
  const [isLoadingMappingCount, setIsLoadingMappingCount] = useState(false);
  const { clearLogs } = useImportLog();
  const mappingTableRef = useRef<MappingTableRef>(null);
  const [mappingSubTab, setMappingSubTab] = useState<'existing' | 'allowed'>('existing');

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

  const loadMappingCount = async () => {
    setIsLoadingMappingCount(true);
    try {
      const response = await mappingsAPI.getCount();
      setMappingCount(response.count);
    } catch (error) {
      console.error('Error loading mapping count:', error);
      setMappingCount(null);
    } finally {
      setIsLoadingMappingCount(false);
    }
  };

  useEffect(() => {
    if (tab === 'load_trades') {
      loadTransactionCount();
      loadMappingCount();
    }
  }, [tab]);

  const handleFileSelect = (file: File) => {
    console.log('📁 [TransactionsPage] Fichier sélectionné:', file.name);
    // Le preview est maintenant géré automatiquement dans FileUpload
  };

  const handleImportComplete = () => {
    console.log('✅ [TransactionsPage] Import terminé');
    // Recharger les compteurs après import
    loadTransactionCount();
    loadMappingCount();
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
          <TransactionsTable 
            onDelete={handleImportComplete} 
            onUpdate={() => {
              // Rafraîchir MappingTable après mise à jour d'une transaction
              // Réinitialiser la page à 1 pour voir le nouveau mapping s'il correspond aux filtres
              if (mappingTableRef.current) {
                mappingTableRef.current.loadMappings(true);
              }
            }}
          />
        )}

        {filter === 'unclassified' && (
          <UnclassifiedTransactionsTable 
            onDelete={handleImportComplete}
            onUpdate={() => {
              // Rafraîchir MappingTable après mise à jour d'une transaction
              // Réinitialiser la page à 1 pour voir le nouveau mapping s'il correspond aux filtres
              if (mappingTableRef.current) {
                mappingTableRef.current.loadMappings(true);
              }
            }}
          />
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
                    Mappings en BDD
                  </div>
                  {isLoadingMappingCount ? (
                    <div style={{ fontSize: '20px', fontWeight: '600', color: '#1e3a5f' }}>
                      ⏳ Chargement...
                    </div>
                  ) : mappingCount !== null ? (
                    <div style={{ fontSize: '24px', fontWeight: '600', color: '#1e3a5f' }}>
                      {mappingCount} mapping{mappingCount !== 1 ? 's' : ''}
                    </div>
                  ) : (
                    <div style={{ fontSize: '14px', color: '#dc3545' }}>
                      ❌ Erreur de chargement
                    </div>
                  )}
                  <button
                    onClick={loadMappingCount}
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
                  onClick={async () => {
                    if (confirm('⚠️ Êtes-vous sûr de vouloir supprimer DÉFINITIVEMENT tous les historiques d\'imports ?\n\nCette action est irréversible et supprimera tous les logs de transactions ET de mappings de la base de données.')) {
                      try {
                        // Supprimer tous les imports de transactions
                        await fileUploadAPI.deleteAllImports();
                        console.log('✅ Tous les imports de transactions supprimés');
                        
                        // Supprimer tous les imports de mappings
                        await mappingsAPI.deleteAllImports();
                        console.log('✅ Tous les imports de mappings supprimés');
                        
                        // Vider les logs en mémoire
                        clearLogs();
                        
                        // Recharger les compteurs
                        loadTransactionCount();
                        loadMappingCount();
                        
                        alert('✅ Tous les historiques d\'imports ont été supprimés définitivement.');
                      } catch (error) {
                        console.error('❌ Erreur lors de la suppression des imports:', error);
                        alert('❌ Erreur lors de la suppression des imports. Veuillez réessayer.');
                      }
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
            />

            {/* Section Import de mappings */}
            <div style={{ 
              marginTop: '48px', 
              paddingTop: '24px', 
              borderTop: '2px solid #e5e5e5'
            }}>
              <h3 style={{ 
                fontSize: '18px', 
                fontWeight: '600', 
                color: '#1a1a1a', 
                marginBottom: '16px' 
              }}>
                Import de mappings
              </h3>
              
              <MappingFileUpload 
                onFileSelect={handleFileSelect} 
                onImportComplete={handleImportComplete} 
              />
              
              <div style={{ 
                marginTop: '16px', 
                padding: '16px', 
                backgroundColor: '#f9f9f9', 
                borderRadius: '4px',
                fontSize: '14px',
                color: '#666',
                marginBottom: '24px'
              }}>
                <p style={{ margin: 0 }}>
                  Sélectionnez un fichier Excel (.xlsx ou .xls) pour charger vos mappings. 
                  Le fichier sera analysé et vous pourrez confirmer le mapping des colonnes (nom, level_1, level_2, level_3).
                </p>
              </div>

              {/* Historique des imports de mappings */}
              <MappingImportLog 
                hideHeader={true} 
                onMappingCountChange={(count) => {
                  setMappingCount(count);
                }}
              />
            </div>
          </div>
        )}

        {tab === 'mapping' && (
          <div>
            {/* Sous-onglets pour Mapping */}
            <div style={{ 
              display: 'flex', 
              gap: '8px', 
              marginBottom: '24px',
              borderBottom: '2px solid #e5e5e5'
            }}>
              <button
                onClick={() => setMappingSubTab('existing')}
                style={{
                  padding: '12px 24px',
                  fontSize: '16px',
                  fontWeight: mappingSubTab === 'existing' ? '600' : '400',
                  color: mappingSubTab === 'existing' ? '#1e3a5f' : '#666',
                  backgroundColor: 'transparent',
                  border: 'none',
                  borderBottom: mappingSubTab === 'existing' ? '3px solid #1e3a5f' : '3px solid transparent',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                Mappings existants
              </button>
              <button
                onClick={() => setMappingSubTab('allowed')}
                style={{
                  padding: '12px 24px',
                  fontSize: '16px',
                  fontWeight: mappingSubTab === 'allowed' ? '600' : '400',
                  color: mappingSubTab === 'allowed' ? '#1e3a5f' : '#666',
                  backgroundColor: 'transparent',
                  border: 'none',
                  borderBottom: mappingSubTab === 'allowed' ? '3px solid #1e3a5f' : '3px solid transparent',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                Mappings autorisés
              </button>
            </div>
            
            {/* Contenu selon le sous-onglet */}
            {mappingSubTab === 'existing' && (
              <MappingTable ref={mappingTableRef} onMappingChange={handleImportComplete} />
            )}
            {mappingSubTab === 'allowed' && (
              <AllowedMappingsTable />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

