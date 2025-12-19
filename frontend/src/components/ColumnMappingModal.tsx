/**
 * ColumnMappingModal component - Popup pour mapper les colonnes et prévisualiser les données
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState } from 'react';
import { fileUploadAPI, ColumnMapping, FilePreviewResponse, FileImportResponse } from '@/api/client';

interface ColumnMappingModalProps {
  file: File;
  previewData: FilePreviewResponse;
  onImportComplete?: () => void;
  onClose: () => void;
}

const DB_COLUMNS = [
  { value: 'date', label: 'Date' },
  { value: 'quantite', label: 'Quantité' },
  { value: 'nom', label: 'Nom' },
  // NOTE: Solde n'est plus dans le mapping, il sera calculé automatiquement
];

export default function ColumnMappingModal({
  file,
  previewData,
  onImportComplete,
  onClose,
}: ColumnMappingModalProps) {
  const [mapping, setMapping] = useState<ColumnMapping[]>(previewData.column_mapping);
  const [isImporting, setIsImporting] = useState(false);
  const [importResult, setImportResult] = useState<FileImportResponse | null>(null);
  const [importError, setImportError] = useState<string | null>(null);

  const handleMappingChange = (fileColumn: string, dbColumn: string) => {
    setMapping(prev => 
      prev.map(m => 
        m.file_column === fileColumn ? { ...m, db_column: dbColumn } : m
      )
    );
  };

  const handleConfirm = async () => {
    // Vérifier que tous les mappings requis sont présents (date, quantite, nom uniquement)
    const requiredColumns = ['date', 'quantite', 'nom'];
    const mappedColumns = mapping.map(m => m.db_column);
    const missingColumns = requiredColumns.filter(col => !mappedColumns.includes(col));
    
    if (missingColumns.length > 0) {
      alert(`Colonnes requises manquantes: ${missingColumns.join(', ')}`);
      return;
    }
    
    // Lancer l'import
    setIsImporting(true);
    setImportError(null);
    setImportResult(null);
    
    try {
      const result = await fileUploadAPI.import(file, mapping);
      setImportResult(result);
      
      // Appeler onImportComplete pour recharger les transactions
      if (onImportComplete) {
        onImportComplete();
      }
    } catch (error) {
      console.error('Erreur lors de l\'import:', error);
      const errorMessage = error instanceof Error ? error.message : 'Erreur inconnue lors de l\'import';
      setImportError(errorMessage);
    } finally {
      setIsImporting(false);
    }
  };

  // Obtenir toutes les colonnes du fichier
  const fileColumns = previewData.column_mapping.map(m => m.file_column);

  return (
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
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '24px',
          maxWidth: '900px',
          maxHeight: '90vh',
          overflow: 'auto',
          width: '90%',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1a1a1a', margin: 0 }}>
            Mapping des colonnes - {file.name}
          </h2>
          <button
            onClick={onClose}
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

        {/* Informations fichier */}
        <div style={{ marginBottom: '24px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
          <div style={{ fontSize: '13px', color: '#666' }}>
            <div><strong>Encodage:</strong> {previewData.encoding}</div>
            <div><strong>Séparateur:</strong> {previewData.separator}</div>
            <div><strong>Total lignes:</strong> {previewData.total_rows}</div>
            <div><strong>Lignes valides:</strong> {previewData.stats.valid_rows}</div>
            {previewData.stats.date_min && (
              <div><strong>Période:</strong> {previewData.stats.date_min} - {previewData.stats.date_max}</div>
            )}
          </div>
        </div>

        {/* Erreurs de validation */}
        {previewData.validation_errors.length > 0 && (
          <div style={{ marginBottom: '24px', padding: '12px', backgroundColor: '#fff3cd', borderRadius: '4px' }}>
            <div style={{ fontSize: '14px', fontWeight: '600', marginBottom: '8px', color: '#856404' }}>
              ⚠️ Erreurs de validation:
            </div>
            <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', color: '#856404' }}>
              {previewData.validation_errors.map((error, idx) => (
                <li key={idx}>{error}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Mapping des colonnes */}
        <div style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: '#1a1a1a' }}>
            Mapping des colonnes
          </h3>
          <div style={{ display: 'grid', gap: '12px' }}>
            {fileColumns.map((fileCol) => {
              const currentMapping = mapping.find(m => m.file_column === fileCol);
              return (
                <div key={fileCol} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ flex: 1, fontSize: '14px', color: '#666' }}>
                    <strong>{fileCol}</strong> →
                  </div>
                  <select
                    value={currentMapping?.db_column || ''}
                    onChange={(e) => handleMappingChange(fileCol, e.target.value)}
                    style={{
                      flex: 1,
                      padding: '8px 12px',
                      border: '1px solid #ccc',
                      borderRadius: '4px',
                      fontSize: '14px',
                    }}
                  >
                    <option value="">-- Sélectionner --</option>
                    {DB_COLUMNS.map(dbCol => (
                      <option key={dbCol.value} value={dbCol.value}>
                        {dbCol.label}
                      </option>
                    ))}
                  </select>
                </div>
              );
            })}
          </div>
        </div>

        {/* Aperçu des données */}
        <div style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: '#1a1a1a' }}>
            Aperçu des données (10 premières lignes)
          </h3>
          <div style={{ overflowX: 'auto', border: '1px solid #e5e5e5', borderRadius: '4px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ backgroundColor: '#f5f5f5' }}>
                  {DB_COLUMNS.map(col => (
                    <th
                      key={col.value}
                      style={{
                        padding: '10px',
                        textAlign: 'left',
                        borderBottom: '2px solid #e5e5e5',
                        fontWeight: '600',
                        color: '#1a1a1a',
                      }}
                    >
                      {col.label}
                    </th>
                  ))}
                  <th
                    style={{
                      padding: '10px',
                      textAlign: 'left',
                      borderBottom: '2px solid #e5e5e5',
                      fontWeight: '600',
                      color: '#1a1a1a',
                    }}
                  >
                    Solde (calculé)
                  </th>
                </tr>
              </thead>
              <tbody>
                {previewData.preview.map((row, idx) => {
                  // Calculer le solde pour l'aperçu (cumul depuis le début)
                  let solde_cumule = 0.0;
                  for (let i = 0; i <= idx; i++) {
                    const quantite = previewData.preview[i]?.quantite || 0;
                    solde_cumule += quantite;
                  }
                  
                  return (
                    <tr key={idx} style={{ borderBottom: '1px solid #e5e5e5' }}>
                      {DB_COLUMNS.map(col => (
                        <td
                          key={col.value}
                          style={{
                            padding: '10px',
                            color: '#666',
                          }}
                        >
                          {row[col.value] !== undefined && row[col.value] !== null
                            ? String(row[col.value])
                            : '-'}
                        </td>
                      ))}
                      <td
                        style={{
                          padding: '10px',
                          color: '#666',
                          fontStyle: 'italic',
                        }}
                      >
                        {solde_cumule.toFixed(2)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Résultats de l'import */}
        {importResult && (
          <div style={{ 
            marginBottom: '24px', 
            padding: '16px', 
            backgroundColor: '#d4edda', 
            borderRadius: '4px',
            border: '1px solid #c3e6cb'
          }}>
            <div style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px', color: '#155724' }}>
              ✅ Import terminé avec succès
            </div>
            <div style={{ fontSize: '14px', color: '#155724', marginBottom: '8px' }}>
              <div><strong>Transactions importées:</strong> {importResult.imported_count}</div>
              <div><strong>Doublons détectés:</strong> {importResult.duplicates_count}</div>
              <div><strong>Erreurs:</strong> {importResult.errors_count}</div>
              {importResult.period_start && importResult.period_end && (
                <div><strong>Période:</strong> {importResult.period_start} - {importResult.period_end}</div>
              )}
            </div>
            {importResult.duplicates.length > 0 && (
              <div style={{ marginTop: '12px' }}>
                <div style={{ fontSize: '14px', fontWeight: '600', marginBottom: '8px', color: '#856404' }}>
                  ⚠️ Doublons détectés ({importResult.duplicates.length}):
                </div>
                <div style={{ 
                  maxHeight: '150px', 
                  overflowY: 'auto', 
                  fontSize: '12px',
                  backgroundColor: 'white',
                  padding: '8px',
                  borderRadius: '4px',
                  border: '1px solid #ccc'
                }}>
                  {importResult.duplicates.slice(0, 10).map((dup, idx) => (
                    <div key={idx} style={{ marginBottom: '4px', color: '#856404' }}>
                      • {dup.date} | {dup.quantite}€ | {dup.nom}
                    </div>
                  ))}
                  {importResult.duplicates.length > 10 && (
                    <div style={{ color: '#856404', fontStyle: 'italic' }}>
                      ... et {importResult.duplicates.length - 10} autres doublons
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Erreur d'import */}
        {importError && (
          <div style={{ 
            marginBottom: '24px', 
            padding: '16px', 
            backgroundColor: '#f8d7da', 
            borderRadius: '4px',
            border: '1px solid #f5c6cb'
          }}>
            <div style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px', color: '#721c24' }}>
              ❌ Erreur lors de l'import
            </div>
            <div style={{ fontSize: '14px', color: '#721c24' }}>
              {importError}
            </div>
          </div>
        )}

        {/* Loading pendant l'import */}
        {isImporting && (
          <div style={{ 
            marginBottom: '24px', 
            padding: '16px', 
            backgroundColor: '#d1ecf1', 
            borderRadius: '4px',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '16px', marginBottom: '8px' }}>⏳ Import en cours...</div>
            <div style={{ fontSize: '14px', color: '#666' }}>Veuillez patienter</div>
          </div>
        )}

        {/* Boutons */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button
            onClick={onClose}
            disabled={isImporting}
            style={{
              padding: '10px 20px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              backgroundColor: 'white',
              color: '#666',
              fontSize: '14px',
              cursor: isImporting ? 'not-allowed' : 'pointer',
              opacity: isImporting ? 0.5 : 1,
            }}
          >
            {importResult ? 'Fermer' : 'Annuler'}
          </button>
          {!importResult && (
            <button
              onClick={handleConfirm}
              disabled={isImporting}
              style={{
                padding: '10px 20px',
                border: 'none',
                borderRadius: '4px',
                backgroundColor: isImporting ? '#ccc' : '#1e3a5f',
                color: 'white',
                fontSize: '14px',
                fontWeight: '500',
                cursor: isImporting ? 'not-allowed' : 'pointer',
              }}
            >
              {isImporting ? 'Import en cours...' : 'Confirmer et importer'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

