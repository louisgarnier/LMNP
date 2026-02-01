/**
 * LoanPaymentPreviewModal component - Modal de prévisualisation pour l'import de mensualités
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState } from 'react';
import { loanPaymentsAPI, LoanPaymentPreviewResponse, LoanPaymentImportResponse } from '@/api/client';
import { useProperty } from '@/contexts/PropertyContext';

interface LoanPaymentPreviewModalProps {
  file: File;
  previewData: LoanPaymentPreviewResponse;
  loanName: string;
  onImportComplete?: () => void;
  onClose: () => void;
}

export default function LoanPaymentPreviewModal({
  file,
  previewData,
  loanName,
  onImportComplete,
  onClose,
}: LoanPaymentPreviewModalProps) {
  const { activeProperty } = useProperty();
  const [isImporting, setIsImporting] = useState(false);
  const [importResult, setImportResult] = useState<LoanPaymentImportResponse | null>(null);
  const [importError, setImportError] = useState<string | null>(null);

  const handleConfirm = async () => {
    console.log('🔄 [LoanPaymentPreviewModal] Début de l\'import...');
    console.log('📁 [LoanPaymentPreviewModal] Fichier:', file.name);
    console.log('💰 [LoanPaymentPreviewModal] Crédit:', loanName);
    
    setIsImporting(true);
    setImportError(null);
    setImportResult(null);
    
    if (!activeProperty?.id || activeProperty.id <= 0) {
      console.error('[LoanPaymentPreviewModal] Property ID invalide');
      setImportError('Property ID invalide');
      return;
    }
    try {
      console.log('📤 [LoanPaymentPreviewModal] Appel API import...');
      const result = await loanPaymentsAPI.import(activeProperty.id, file, loanName);
      
      console.log('✅ [LoanPaymentPreviewModal] Import réussi!', result);
      setImportResult(result);
      
      if (onImportComplete) {
        onImportComplete();
      }
    } catch (error) {
      console.error('❌ [LoanPaymentPreviewModal] Erreur lors de l\'import:', error);
      const errorMessage = error instanceof Error ? error.message : 'Erreur inconnue';
      setImportError(errorMessage);
    } finally {
      console.log('🏁 [LoanPaymentPreviewModal] Import terminé');
      setIsImporting(false);
    }
  };

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
        zIndex: 9999,
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '24px',
          maxWidth: '1000px',
          maxHeight: '90vh',
          overflow: 'auto',
          width: '90%',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1a1a1a', margin: 0 }}>
            Prévisualisation - {file.name}
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
            <div><strong>Total lignes:</strong> {previewData.total_rows}</div>
            <div><strong>Colonnes détectées:</strong> {previewData.detected_columns.length}</div>
            <div><strong>Colonnes années valides:</strong> {previewData.year_columns.length}</div>
            {previewData.invalid_columns.length > 0 && (
              <div style={{ color: '#dc2626', marginTop: '4px' }}>
                <strong>⚠️ Colonnes invalides:</strong> {previewData.invalid_columns.join(', ')}
              </div>
            )}
            <div><strong>Années détectées:</strong> {previewData.stats.years_detected}</div>
            <div><strong>Enregistrements à créer:</strong> {previewData.stats.records_to_create}</div>
            <div><strong>Crédit:</strong> {loanName}</div>
          </div>
        </div>

        {/* Avertissement si données existantes */}
        {previewData.warning && (
          <div style={{ 
            marginBottom: '24px', 
            padding: '12px', 
            backgroundColor: '#fff3cd', 
            borderRadius: '4px',
            border: '1px solid #ffc107'
          }}>
            <div style={{ fontSize: '14px', fontWeight: '600', marginBottom: '4px', color: '#856404' }}>
              ⚠️ Avertissement
            </div>
            <div style={{ fontSize: '13px', color: '#856404' }}>
              {previewData.warning}
            </div>
          </div>
        )}

        {/* Données extraites */}
        <div style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: '#1a1a1a' }}>
            Données extraites ({previewData.extracted_data.length} années)
          </h3>
          <div style={{ overflowX: 'auto', border: '1px solid #e5e5e5', borderRadius: '4px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ backgroundColor: '#f5f5f5' }}>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '2px solid #e5e5e5', fontWeight: '600', color: '#1a1a1a' }}>
                    Année
                  </th>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '2px solid #e5e5e5', fontWeight: '600', color: '#1a1a1a' }}>
                    Date
                  </th>
                  <th style={{ padding: '10px', textAlign: 'right', borderBottom: '2px solid #e5e5e5', fontWeight: '600', color: '#1a1a1a' }}>
                    Capital (€)
                  </th>
                  <th style={{ padding: '10px', textAlign: 'right', borderBottom: '2px solid #e5e5e5', fontWeight: '600', color: '#1a1a1a' }}>
                    Intérêts (€)
                  </th>
                  <th style={{ padding: '10px', textAlign: 'right', borderBottom: '2px solid #e5e5e5', fontWeight: '600', color: '#1a1a1a' }}>
                    Assurance (€)
                  </th>
                  <th style={{ padding: '10px', textAlign: 'right', borderBottom: '2px solid #e5e5e5', fontWeight: '600', color: '#1a1a1a' }}>
                    Total (€)
                  </th>
                </tr>
              </thead>
              <tbody>
                {previewData.extracted_data.map((item, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #e5e5e5' }}>
                    <td style={{ padding: '10px', color: '#666' }}>{item.year}</td>
                    <td style={{ padding: '10px', color: '#666' }}>{item.date}</td>
                    <td style={{ padding: '10px', textAlign: 'right', color: '#666' }}>
                      {item.capital.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €
                    </td>
                    <td style={{ padding: '10px', textAlign: 'right', color: '#666' }}>
                      {item.interest.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €
                    </td>
                    <td style={{ padding: '10px', textAlign: 'right', color: '#666' }}>
                      {item.insurance.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €
                    </td>
                    <td style={{ padding: '10px', textAlign: 'right', color: '#666', fontWeight: '500' }}>
                      {item.total.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Aperçu du fichier Excel (premières lignes) */}
        {previewData.preview && previewData.preview.length > 0 && (
          <div style={{ marginBottom: '24px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: '#1a1a1a' }}>
              Aperçu du fichier Excel (10 premières lignes)
            </h3>
            <div style={{ overflowX: 'auto', border: '1px solid #e5e5e5', borderRadius: '4px' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f5f5f5' }}>
                    {previewData.detected_columns.map((col) => (
                      <th
                        key={col}
                        style={{
                          padding: '10px',
                          textAlign: 'left',
                          borderBottom: '2px solid #e5e5e5',
                          fontWeight: '600',
                          color: previewData.year_columns.includes(col) ? '#1e3a5f' : 
                                 previewData.invalid_columns.includes(col) ? '#dc2626' : '#1a1a1a',
                        }}
                      >
                        {col}
                        {previewData.year_columns.includes(col) && ' ✓'}
                        {previewData.invalid_columns.includes(col) && ' ⚠️'}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {previewData.preview.slice(0, 10).map((row, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #e5e5e5' }}>
                      {previewData.detected_columns.map((col) => (
                        <td
                          key={col}
                          style={{
                            padding: '10px',
                            color: '#666',
                          }}
                        >
                          {row[col] !== undefined && row[col] !== null
                            ? String(row[col])
                            : '-'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

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
            <div style={{ fontSize: '14px', color: '#155724' }}>
              <div><strong>Message:</strong> {importResult.message}</div>
              <div><strong>Enregistrements supprimés:</strong> {importResult.deleted_count}</div>
              <div><strong>Enregistrements créés:</strong> {importResult.created_count}</div>
              <div><strong>Total années:</strong> {importResult.total_years}</div>
              <div><strong>Crédit:</strong> {importResult.loan_name}</div>
              {importResult.errors && importResult.errors.length > 0 && (
                <div style={{ marginTop: '8px', color: '#721c24' }}>
                  <strong>Erreurs:</strong>
                  <ul style={{ marginTop: '4px', paddingLeft: '20px' }}>
                    {importResult.errors.map((error, idx) => (
                      <li key={idx}>{error}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
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

        {/* Boutons d'action */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button
            onClick={onClose}
            disabled={isImporting}
            style={{
              padding: '10px 20px',
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: isImporting ? 'not-allowed' : 'pointer',
              opacity: isImporting ? 0.6 : 1,
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
                backgroundColor: '#1e3a5f',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '14px',
                fontWeight: '500',
                cursor: isImporting ? 'not-allowed' : 'pointer',
                opacity: isImporting ? 0.6 : 1,
              }}
            >
              {isImporting ? '⏳ Import en cours...' : '✅ Confirmer l\'import'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
