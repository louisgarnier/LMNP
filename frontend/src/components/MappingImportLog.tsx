/**
 * MappingImportLog component - Display mapping import history and detailed logs
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect } from 'react';
import { useImportLog, ImportLogEntry } from '@/contexts/ImportLogContext';
import { useProperty } from '@/contexts/PropertyContext';
import { mappingsAPI, MappingImportHistory } from '@/api/client';

interface MappingImportLogProps {
  hideHeader?: boolean;
  onMappingCountChange?: (count: number) => void;
  hideDbHistory?: boolean; // Prop pour masquer définitivement l'historique de la base de données
}

export default function MappingImportLog({ hideHeader = false, onMappingCountChange, hideDbHistory = false }: MappingImportLogProps) {
  const { activeProperty } = useProperty();
  const { logs: memoryLogs, updateLog } = useImportLog();
  const [dbHistory, setDbHistory] = useState<MappingImportHistory[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedLog, setSelectedLog] = useState<ImportLogEntry | null>(null);
  const [selectedHistory, setSelectedHistory] = useState<MappingImportHistory | null>(null);
  const [mappingCount, setMappingCount] = useState<number | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  // Si hideDbHistory est true, ne jamais charger ni afficher l'historique de la base de données
  const showDbHistory = !hideDbHistory;
  
  // Réagir à hideDbHistory pour vider l'historique si on le masque
  useEffect(() => {
    if (hideDbHistory) {
      setDbHistory([]);
      setSelectedHistory(null);
    }
  }, [hideDbHistory]);

  // Load database history
  const loadHistory = async () => {
    setIsLoading(true);
    if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
      console.warn('[MappingImportLog] loadHistory - Aucune propriété active ou ID invalide, ne charge pas l\'historique.');
      setDbHistory([]);
      setIsLoading(false);
      return;
    }
    try {
      console.log('[MappingImportLog] loadHistory - Appel API avec propertyId:', activeProperty.id);
      const data = await mappingsAPI.getImportsHistory(activeProperty.id);
      setDbHistory(data);
      console.log('[MappingImportLog] loadHistory - Réponse:', { count: data.length, propertyId: activeProperty.id });
    } catch (error) {
      console.error('Error loading mapping import history:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Load mapping count
  const loadMappingCount = async () => {
    if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
      console.warn('[MappingImportLog] loadMappingCount - PROPERTY INVALIDE. Skipping API call.');
      setMappingCount(null);
      return;
    }
    
    console.log('[MappingImportLog] loadMappingCount - Appel avec propertyId:', activeProperty.id);
    try {
      const response = await mappingsAPI.getCount(activeProperty.id);
      console.log('[MappingImportLog] loadMappingCount - Réponse:', { count: response.count, propertyId: activeProperty.id });
      setMappingCount(response.count);
      if (onMappingCountChange) {
        onMappingCountChange(response.count);
      }
    } catch (error) {
      console.error('[MappingImportLog] loadMappingCount - Erreur:', error);
    }
  };

  // Initial load (only if showDbHistory is true)
  useEffect(() => {
    if (showDbHistory) {
      loadHistory();
    }
    loadMappingCount();
  }, [activeProperty?.id, showDbHistory]);

  // Auto-refresh selected log if in progress
  useEffect(() => {
    if (!selectedLog || selectedLog.status !== 'in_progress') {
      return;
    }

    const interval = setInterval(() => {
      // Refresh the log from memory (it's updated by MappingColumnMappingModal)
      const updatedLog = memoryLogs.find(l => l.id === selectedLog.id);
      if (updatedLog) {
        setSelectedLog(updatedLog);
      }
      
      // Also refresh history (only if showDbHistory is true) and count
      if (showDbHistory) {
        loadHistory();
      }
      loadMappingCount();
    }, 2500); // Every 2.5 seconds

    return () => clearInterval(interval);
  }, [selectedLog, memoryLogs]);

  const handleLogClick = (log: ImportLogEntry) => {
    setSelectedLog(log);
    setSelectedHistory(null);
  };

  const handleHistoryClick = async (history: MappingImportHistory) => {
    setSelectedHistory(history);
    setSelectedLog(null);
    
    // Try to find corresponding memory log
    const memoryLog = memoryLogs.find(l => l.filename === history.filename);
    if (memoryLog) {
      setSelectedLog(memoryLog);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    const promises = [loadMappingCount()];
    if (showDbHistory) {
      promises.push(loadHistory());
    }
    await Promise.all(promises);
    setIsRefreshing(false);
  };

  const handleDeleteHistory = async (historyId: number) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cet import de l\'historique ?')) {
      return;
    }
    if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
      console.error('[MappingImportLog] Property ID invalide pour deleteImport');
      return;
    }
    
    try {
      await mappingsAPI.deleteImport(activeProperty.id, historyId);
      // Reload history
      if (showDbHistory) {
        loadHistory();
      }
    } catch (error) {
      console.error('Error deleting import:', error);
      alert('Erreur lors de la suppression de l\'import');
    }
  };

  // Combine memory logs and DB history (only if showDbHistory is true)
  // Filter to only show mapping-related logs (Excel files)
  const allLogs = [
    ...memoryLogs
      .filter(log => log.filename.toLowerCase().endsWith('.xlsx') || log.filename.toLowerCase().endsWith('.xls'))
      .map(log => ({
        type: 'memory' as const,
        data: log,
        key: log.id,
      })),
    ...(showDbHistory ? dbHistory
      .filter(h => !memoryLogs.some(m => m.filename === h.filename))
      .map(history => ({
        type: 'db' as const,
        data: history,
        key: `db_${history.id}`,
      })) : []),
  ].sort((a, b) => {
    const dateA = a.type === 'memory' 
      ? a.data.startTime.getTime() 
      : new Date(a.data.imported_at).getTime();
    const dateB = b.type === 'memory'
      ? b.data.startTime.getTime()
      : new Date(b.data.imported_at).getTime();
    return dateB - dateA; // Most recent first
  });

  return (
    <div>
      {/* Header with mapping count - only if not hidden */}
      {!hideHeader && (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: '24px',
          padding: '16px',
          backgroundColor: 'white',
          borderRadius: '8px',
          border: '1px solid #e5e5e5'
        }}>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: '600', margin: 0, color: '#1a1a1a' }}>
              Historique des imports de mappings
            </h2>
            <p style={{ fontSize: '14px', color: '#666', margin: '4px 0 0 0' }}>
              Suivi des imports de fichiers Excel de mappings
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ 
              padding: '12px 20px', 
              backgroundColor: '#f5f5f5', 
              borderRadius: '8px',
              border: '1px solid #e5e5e5',
              minWidth: '150px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
                Mappings en BDD
              </div>
              {mappingCount !== null ? (
                <div style={{ fontSize: '20px', fontWeight: '600', color: '#1e3a5f' }}>
                  {mappingCount} mapping{mappingCount !== 1 ? 's' : ''}
                </div>
              ) : (
                <div style={{ fontSize: '14px', color: '#dc3545' }}>
                  ❌ Erreur
                </div>
              )}
            </div>
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              style={{
                padding: '8px 16px',
                fontSize: '14px',
                backgroundColor: '#1e3a5f',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: isRefreshing ? 'not-allowed' : 'pointer',
                opacity: isRefreshing ? 0.6 : 1,
              }}
            >
              {isRefreshing ? '⏳ Actualisation...' : '🔄 Actualiser'}
            </button>
          </div>
        </div>
      )}

      {/* Logs list */}
      <div style={{ 
        backgroundColor: 'white', 
        borderRadius: '8px', 
        border: '1px solid #e5e5e5',
        overflow: 'hidden'
      }}>
        {isLoading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
            ⏳ Chargement de l'historique...
          </div>
        ) : allLogs.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
            Aucun import de mapping pour le moment
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: '#f5f5f5', borderBottom: '2px solid #e5e5e5' }}>
                <th style={{ padding: '12px', textAlign: 'left', fontSize: '14px', fontWeight: '600', color: '#1a1a1a' }}>
                  Fichier
                </th>
                <th style={{ padding: '12px', textAlign: 'left', fontSize: '14px', fontWeight: '600', color: '#1a1a1a' }}>
                  Date/Heure
                </th>
                <th style={{ padding: '12px', textAlign: 'center', fontSize: '14px', fontWeight: '600', color: '#1a1a1a' }}>
                  Statut
                </th>
                <th style={{ padding: '12px', textAlign: 'center', fontSize: '14px', fontWeight: '600', color: '#1a1a1a' }}>
                  Importés
                </th>
                <th style={{ padding: '12px', textAlign: 'center', fontSize: '14px', fontWeight: '600', color: '#1a1a1a' }}>
                  Doublons
                </th>
                <th style={{ padding: '12px', textAlign: 'center', fontSize: '14px', fontWeight: '600', color: '#1a1a1a' }}>
                  Erreurs
                </th>
                {showDbHistory && (
                  <th style={{ padding: '12px', textAlign: 'center', fontSize: '14px', fontWeight: '600', color: '#1a1a1a' }}>
                    Actions
                  </th>
                )}
              </tr>
            </thead>
            <tbody>
              {allLogs.map((item) => {
                const isMemory = item.type === 'memory';
                const log = isMemory ? item.data : null;
                const history = !isMemory ? item.data : null;
                
                const status = isMemory 
                  ? log!.status 
                  : (history!.errors_count > 0 ? 'error' : 'completed');
                const statusLabel = {
                  pending: '⏳ En attente',
                  in_progress: '🔄 En cours',
                  completed: '✅ Terminé',
                  error: '❌ Erreur',
                }[status];

                const dateTime = isMemory
                  ? log!.startTime.toLocaleString('fr-FR')
                  : new Date(history!.imported_at).toLocaleString('fr-FR');

                const imported = isMemory
                  ? log!.result?.imported_count ?? 0
                  : history!.imported_count;
                const duplicates = isMemory
                  ? log!.result?.duplicates_count ?? 0
                  : history!.duplicates_count;
                const errors = isMemory
                  ? log!.result?.errors_count ?? 0
                  : history!.errors_count;

                return (
                  <tr
                    key={item.key}
                    onClick={() => {
                      if (isMemory) {
                        handleLogClick(log!);
                      } else {
                        handleHistoryClick(history!);
                      }
                    }}
                    style={{
                      cursor: 'pointer',
                      borderBottom: '1px solid #e5e5e5',
                      transition: 'background-color 0.2s',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = '#f9f9f9';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'white';
                    }}
                  >
                    <td style={{ padding: '12px', fontSize: '14px', color: '#1a1a1a' }}>
                      <strong>{isMemory ? log!.filename : history!.filename}</strong>
                    </td>
                    <td style={{ padding: '12px', fontSize: '14px', color: '#666' }}>
                      {dateTime}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center', fontSize: '14px' }}>
                      {statusLabel}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center', fontSize: '14px', color: '#10b981' }}>
                      {imported}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center', fontSize: '14px', color: '#f59e0b' }}>
                      {duplicates}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center', fontSize: '14px', color: errors > 0 ? '#ef4444' : '#666' }}>
                      {errors}
                    </td>
                    {showDbHistory && !isMemory && (
                      <td style={{ padding: '12px', textAlign: 'center' }}>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteHistory(history!.id);
                          }}
                          style={{
                            padding: '4px 8px',
                            fontSize: '12px',
                            backgroundColor: '#dc3545',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                          }}
                        >
                          🗑️ Supprimer
                        </button>
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Detail modal */}
      {(selectedLog || selectedHistory) && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => {
            setSelectedLog(null);
            setSelectedHistory(null);
          }}
        >
          <div
            style={{
              backgroundColor: 'white',
              borderRadius: '8px',
              padding: '24px',
              maxWidth: '800px',
              maxHeight: '90vh',
              overflow: 'auto',
              width: '90%',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1a1a1a', margin: 0 }}>
                Détails de l'import de mapping
                {selectedLog && ` - ${selectedLog.filename}`}
                {selectedHistory && ` - ${selectedHistory.filename}`}
              </h2>
              <button
                onClick={() => {
                  setSelectedLog(null);
                  setSelectedHistory(null);
                }}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '24px',
                  cursor: 'pointer',
                  color: '#666',
                  padding: '0',
                  width: '32px',
                  height: '32px',
                }}
              >
                ×
              </button>
            </div>

            {selectedLog && (
              <div>
                {/* Status */}
                <div style={{ marginBottom: '24px', padding: '16px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
                  <div style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>
                    <strong>Statut:</strong> {
                      selectedLog.status === 'pending' ? '⏳ En attente' :
                      selectedLog.status === 'in_progress' ? '🔄 En cours' :
                      selectedLog.status === 'completed' ? '✅ Terminé' :
                      '❌ Erreur'
                    }
                  </div>
                  {selectedLog.result && (
                    <div style={{ fontSize: '14px', color: '#666' }}>
                      <div><strong>Importés:</strong> {selectedLog.result.imported_count}</div>
                      <div><strong>Doublons:</strong> {selectedLog.result.duplicates_count}</div>
                      <div><strong>Erreurs:</strong> {selectedLog.result.errors_count}</div>
                    </div>
                  )}
                  {selectedLog.error && (
                    <div style={{ marginTop: '8px', padding: '8px', backgroundColor: '#fee2e2', borderRadius: '4px', color: '#dc2626' }}>
                      <strong>Erreur:</strong> {selectedLog.error}
                    </div>
                  )}
                </div>

                {/* Step-by-step logs */}
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: '#1a1a1a' }}>
                    Logs étape par étape
                  </h3>
                  {selectedLog.logs.length === 0 ? (
                    <div style={{ padding: '16px', textAlign: 'center', color: '#666' }}>
                      Aucun log pour le moment
                    </div>
                  ) : (
                    <div style={{ 
                      maxHeight: '400px', 
                      overflowY: 'auto',
                      border: '1px solid #e5e5e5',
                      borderRadius: '4px',
                      padding: '12px'
                    }}>
                      {selectedLog.logs.map((logEntry, idx) => {
                        const color = {
                          info: '#666',
                          success: '#10b981',
                          warning: '#f59e0b',
                          error: '#ef4444',
                        }[logEntry.level];

                        return (
                          <div
                            key={idx}
                            style={{
                              marginBottom: '12px',
                              padding: '12px',
                              backgroundColor: '#f9fafb',
                              borderRadius: '4px',
                              borderLeft: `4px solid ${color}`,
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                              <div style={{ fontSize: '14px', fontWeight: '600', color: '#1a1a1a' }}>
                                {logEntry.step}
                              </div>
                              <div style={{ fontSize: '12px', color: '#666' }}>
                                {logEntry.timestamp.toLocaleTimeString('fr-FR')}
                              </div>
                            </div>
                            <div style={{ fontSize: '14px', color: color }}>
                              {logEntry.message}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {/* Duplicates list */}
                  {selectedLog.result && selectedLog.result.duplicates && selectedLog.result.duplicates.length > 0 && (
                    <div style={{ marginTop: '24px' }}>
                      <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: '#1a1a1a' }}>
                        Doublons détectés ({selectedLog.result.duplicates.length})
                      </h3>
                      <div style={{ 
                        maxHeight: '200px', 
                        overflowY: 'auto',
                        border: '1px solid #e5e5e5',
                        borderRadius: '4px',
                        padding: '12px',
                        backgroundColor: '#fffbf0'
                      }}>
                        {selectedLog.result.duplicates.map((dup: any, idx: number) => (
                          <div key={idx} style={{ marginBottom: '8px', fontSize: '13px', color: '#856404' }}>
                            • {dup.nom}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {selectedHistory && !selectedLog && (
              <div>
                <div style={{ marginBottom: '24px', padding: '16px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
                  <div style={{ fontSize: '14px', color: '#666' }}>
                    <div><strong>Date d'import:</strong> {new Date(selectedHistory.imported_at).toLocaleString('fr-FR')}</div>
                    <div><strong>Importés:</strong> {selectedHistory.imported_count}</div>
                    <div><strong>Doublons:</strong> {selectedHistory.duplicates_count}</div>
                    <div><strong>Erreurs:</strong> {selectedHistory.errors_count}</div>
                  </div>
                </div>
                <div style={{ padding: '16px', textAlign: 'center', color: '#666' }}>
                  Les logs détaillés ne sont disponibles que pour les imports en cours ou récents.
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

