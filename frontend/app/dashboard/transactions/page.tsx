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
import { useProperty } from '@/contexts/PropertyContext';

// Helper function to download a blob as a file
const downloadBlob = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
};

export default function TransactionsPage() {
  const { activeProperty } = useProperty();
  
  // Log pour déboguer les changements de activeProperty
  useEffect(() => {
    console.log('[TransactionsPage] 🔍 activeProperty changé:', activeProperty);
    console.log('[TransactionsPage] 🔍 activeProperty?.id:', activeProperty?.id, 'type:', typeof activeProperty?.id);
    if (activeProperty) {
      console.log('[TransactionsPage] 🔍 activeProperty complet:', JSON.stringify(activeProperty, null, 2));
    }
  }, [activeProperty]);
  
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
  const [isExportingMappings, setIsExportingMappings] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const [backendStatus, setBackendStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');

  const checkBackendConnection = async () => {
    setBackendStatus('checking');
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000), // 5 secondes timeout
      });
      if (response.ok) {
        setBackendStatus('connected');
      } else {
        setBackendStatus('disconnected');
      }
    } catch (error) {
      console.error('Error checking backend connection:', error);
      setBackendStatus('disconnected');
    }
  };

  const loadTransactionCount = async () => {
    console.log('[TransactionsPage] loadTransactionCount - activeProperty:', activeProperty);
    console.log('[TransactionsPage] loadTransactionCount - activeProperty?.id:', activeProperty?.id);
    
    if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
      console.warn('[TransactionsPage] loadTransactionCount - PROPERTY INVALIDE:', {
        activeProperty,
        id: activeProperty?.id,
        reason: !activeProperty ? 'activeProperty is null/undefined' : 
                !activeProperty.id ? 'activeProperty.id is null/undefined' : 
                'activeProperty.id <= 0'
      });
      setTransactionCount(null);
      setIsLoadingCount(false);
      return;
    }
    
    console.log('[TransactionsPage] loadTransactionCount - Appel API avec property_id:', activeProperty.id);
    setIsLoadingCount(true);
    try {
      const response = await transactionsAPI.getAll(activeProperty.id, 0, 1);
      console.log('[TransactionsPage] loadTransactionCount - Réponse:', response.total);
      setTransactionCount(response.total);
    } catch (error) {
      console.error('Error loading transaction count:', error);
      setTransactionCount(null);
    } finally {
      setIsLoadingCount(false);
    }
  };

  const loadMappingCount = async () => {
    if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
      console.warn('[TransactionsPage] loadMappingCount - PROPERTY INVALIDE. Skipping API call.');
      setMappingCount(null);
      setIsLoadingMappingCount(false);
      return;
    }
    
    console.log('[TransactionsPage] loadMappingCount - Appel avec propertyId:', activeProperty.id);
    setIsLoadingMappingCount(true);
    try {
      const response = await mappingsAPI.getCount(activeProperty.id);
      console.log('[TransactionsPage] loadMappingCount - Réponse:', { count: response.count, propertyId: activeProperty.id });
      setMappingCount(response.count);
    } catch (error) {
      console.error('[TransactionsPage] loadMappingCount - Erreur:', error);
      setMappingCount(null);
    } finally {
      setIsLoadingMappingCount(false);
    }
  };

  useEffect(() => {
    if (tab === 'load_trades' && activeProperty && activeProperty.id && activeProperty.id > 0) {
      loadTransactionCount();
      loadMappingCount();
    } else if (tab === 'load_trades') {
      // Pas de propriété valide, réinitialiser les compteurs
      setTransactionCount(null);
      setMappingCount(null);
      setIsLoadingCount(false);
      setIsLoadingMappingCount(false);
    }
  }, [tab, activeProperty?.id]);

  // Vérifier la connexion au backend au montage et périodiquement
  useEffect(() => {
    if (tab === 'load_trades') {
      checkBackendConnection();
      
      // Vérifier la connexion toutes les 30 secondes
      const interval = setInterval(() => {
        checkBackendConnection();
      }, 30000);
      
      return () => clearInterval(interval);
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

  const handleExportMappings = async (format: 'excel' | 'csv') => {
    setIsExportingMappings(true);
    setExportError(null);
    try {
      if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
        alert('❌ Aucune propriété active sélectionnée. Veuillez sélectionner une propriété avant d\'exporter.');
        return;
      }
      const blob = await mappingsAPI.export(activeProperty.id, format);
      const extension = format === 'excel' ? 'xlsx' : 'csv';
      const today = new Date().toISOString().split('T')[0];
      const filename = `mappings_${today}.${extension}`;
      downloadBlob(blob, filename);
    } catch (error) {
      console.error('Erreur lors de l\'export des mappings:', error);
      setExportError(error instanceof Error ? error.message : 'Erreur lors de l\'export');
    } finally {
      setIsExportingMappings(false);
    }
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
                {/* Card API Backend Status */}
                <div style={{ 
                  padding: '12px 20px', 
                  backgroundColor: backendStatus === 'connected' ? '#f0fdf4' : backendStatus === 'disconnected' ? '#fef2f2' : '#f5f5f5',
                  borderRadius: '8px',
                  border: `1px solid ${backendStatus === 'connected' ? '#86efac' : backendStatus === 'disconnected' ? '#fca5a5' : '#e5e5e5'}`,
                  minWidth: '200px',
                  textAlign: 'center',
                  flexShrink: 0
                }}>
                  <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
                    API Backend
                  </div>
                  {backendStatus === 'checking' ? (
                    <div style={{ fontSize: '20px', fontWeight: '600', color: '#666' }}>
                      ⏳ Vérification...
                    </div>
                  ) : backendStatus === 'connected' ? (
                    <div style={{ fontSize: '20px', fontWeight: '600', color: '#16a34a' }}>
                      ✅ Connecté
                    </div>
                  ) : (
                    <div style={{ fontSize: '20px', fontWeight: '600', color: '#dc2626' }}>
                      ❌ Déconnecté
                    </div>
                  )}
                  <button
                    onClick={checkBackendConnection}
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

                {/* Card Transactions en BDD */}
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
                      if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
                        alert('❌ Aucune propriété active sélectionnée. Veuillez sélectionner une propriété avant de supprimer les imports.');
                        return;
                      }
                      try {
                        // Supprimer tous les imports de transactions pour cette propriété
                        await fileUploadAPI.deleteAllImports(activeProperty.id);
                        console.log('✅ Tous les imports de transactions supprimés pour property_id:', activeProperty.id);
                        
                        // Supprimer tous les imports de mappings pour cette propriété
                        await mappingsAPI.deleteAllImports(activeProperty.id);
                        console.log('✅ Tous les imports de mappings supprimés pour property_id:', activeProperty.id);
                        
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
            
            {/* Bouton Extraire pour les mappings existants */}
            {mappingSubTab === 'existing' && (
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                marginBottom: '16px'
              }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <button
                    onClick={() => handleExportMappings('excel')}
                    disabled={isExportingMappings}
                    style={{
                      padding: '8px 16px',
                      fontSize: '14px',
                      fontWeight: '500',
                      color: '#fff',
                      backgroundColor: isExportingMappings ? '#9ca3af' : '#1e3a5f',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: isExportingMappings ? 'not-allowed' : 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      transition: 'background-color 0.2s',
                    }}
                    onMouseEnter={(e) => {
                      if (!isExportingMappings) {
                        e.currentTarget.style.backgroundColor = '#2d4a6f';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isExportingMappings) {
                        e.currentTarget.style.backgroundColor = '#1e3a5f';
                      }
                    }}
                  >
                    {isExportingMappings ? (
                      <>
                        <span>⏳</span>
                        <span>Export en cours...</span>
                      </>
                    ) : (
                      <>
                        <span>📥</span>
                        <span>Extraire (Excel)</span>
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => handleExportMappings('csv')}
                    disabled={isExportingMappings}
                    style={{
                      padding: '8px 16px',
                      fontSize: '14px',
                      fontWeight: '500',
                      color: '#fff',
                      backgroundColor: isExportingMappings ? '#9ca3af' : '#1e3a5f',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: isExportingMappings ? 'not-allowed' : 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      transition: 'background-color 0.2s',
                    }}
                    onMouseEnter={(e) => {
                      if (!isExportingMappings) {
                        e.currentTarget.style.backgroundColor = '#2d4a6f';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isExportingMappings) {
                        e.currentTarget.style.backgroundColor = '#1e3a5f';
                      }
                    }}
                  >
                    {isExportingMappings ? (
                      <>
                        <span>⏳</span>
                        <span>Export en cours...</span>
                      </>
                    ) : (
                      <>
                        <span>📥</span>
                        <span>Extraire (CSV)</span>
                      </>
                    )}
                  </button>
                </div>
                {exportError && (
                  <div style={{
                    padding: '8px 12px',
                    backgroundColor: '#fee2e2',
                    color: '#991b1b',
                    borderRadius: '6px',
                    fontSize: '14px',
                  }}>
                    ❌ Erreur: {exportError}
                  </div>
                )}
              </div>
            )}
            
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

