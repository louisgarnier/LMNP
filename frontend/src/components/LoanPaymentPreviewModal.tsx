/**
 * LoanPaymentPreviewModal component - Popup pour prévisualiser et importer les mensualités de crédit
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState } from 'react';
import { loanPaymentsAPI, LoanPaymentPreviewResponse, LoanPaymentImportResponse } from '@/api/client';

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
  const [isImporting, setIsImporting] = useState(false);
  const [importResult, setImportResult] = useState<LoanPaymentImportResponse | null>(null);
  const [importError, setImportError] = useState<string | null>(null);
  const [confirmOverwrite, setConfirmOverwrite] = useState(false);

  const handleImport = async () => {
    // Si des mensualités existent, demander confirmation
    if (previewData.existing_payments_count > 0 && !confirmOverwrite) {
      if (!confirm(
        `⚠️ ${previewData.existing_payments_count} mensualité(s) existante(s) pour "${loanName}" seront supprimée(s).\n\nVoulez-vous continuer ?`
      )) {
        return;
      }
      setConfirmOverwrite(true);
    }

    console.log('🔄 [LoanPaymentPreviewModal] Début de l\'import...');
    console.log('📁 [LoanPaymentPreviewModal] Fichier:', file.name);
    
    setIsImporting(true);
    setImportError(null);
    setImportResult(null);
    
    try {
      console.log('📤 [LoanPaymentPreviewModal] Appel API import...');
      
      const result = await loanPaymentsAPI.import(file, loanName, confirmOverwrite || previewData.existing_payments_count > 0);
      
      console.log('✅ [LoanPaymentPreviewModal] Import réussi!', result);
      setImportResult(result);
      
      if (onImportComplete) {
        // Attendre un peu avant de fermer pour que l'utilisateur voie le résultat
        setTimeout(() => {
          onImportComplete();
        }, 1500);
      }
    } catch (error) {
      console.error('❌ [LoanPaymentPreviewModal] Erreur lors de l\'import:', error);
      const errorMessage = error instanceof Error ? error.message : 'Erreur inconnue';
      setImportError(errorMessage);
    } finally {
      setIsImporting(false);
      console.log('🏁 [LoanPaymentPreviewModal] Import terminé');
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
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#111827' }}>
            Prévisualisation des mensualités
          </h2>
          <button
            onClick={onClose}
            style={{
              backgroundColor: 'transparent',
              border: 'none',
              fontSize: '24px',
              cursor: 'pointer',
              color: '#6b7280',
            }}
          >
            ×
          </button>
        </div>

        {/* Informations générales */}
        <div style={{ marginBottom: '20px', padding: '12px', backgroundColor: '#f9fafb', borderRadius: '6px' }}>
          <div><strong>Fichier:</strong> {previewData.filename}</div>
          <div><strong>Lignes détectées:</strong> {previewData.total_rows}</div>
          <div><strong>Années détectées:</strong> {previewData.detected_years.join(', ')} ({previewData.detected_years.length} année(s))</div>
          {previewData.existing_payments_count > 0 && (
            <div style={{ color: '#dc2626', marginTop: '8px' }}>
              ⚠️ <strong>{previewData.existing_payments_count} mensualité(s) existante(s)</strong> pour "{loanName}" seront supprimée(s) lors de l'import.
            </div>
          )}
        </div>

        {/* Avertissements */}
        {previewData.warnings.length > 0 && (
          <div style={{ marginBottom: '20px', padding: '12px', backgroundColor: '#fef3c7', borderRadius: '6px' }}>
            <div style={{ fontWeight: '600', marginBottom: '8px', color: '#92400e' }}>⚠️ Avertissements:</div>
            {previewData.warnings.map((warning, index) => (
              <div key={index} style={{ fontSize: '13px', color: '#78350f', marginBottom: '4px' }}>
                {warning}
              </div>
            ))}
          </div>
        )}

        {/* Erreurs de validation */}
        {previewData.validation_errors.length > 0 && (
          <div style={{ marginBottom: '20px', padding: '12px', backgroundColor: '#fee2e2', borderRadius: '6px' }}>
            <div style={{ fontWeight: '600', marginBottom: '8px', color: '#991b1b' }}>❌ Erreurs de validation:</div>
            {previewData.validation_errors.map((error, index) => (
              <div key={index} style={{ fontSize: '13px', color: '#7f1d1d', marginBottom: '4px' }}>
                {error}
              </div>
            ))}
          </div>
        )}

        {/* Aperçu des données */}
        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px', color: '#111827' }}>
            Aperçu des données ({previewData.preview.length} enregistrement(s))
          </h3>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ backgroundColor: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
                  <th style={{ padding: '8px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>Année</th>
                  <th style={{ padding: '8px', textAlign: 'right', fontWeight: '600', color: '#374151' }}>Capital (€)</th>
                  <th style={{ padding: '8px', textAlign: 'right', fontWeight: '600', color: '#374151' }}>Intérêts (€)</th>
                  <th style={{ padding: '8px', textAlign: 'right', fontWeight: '600', color: '#374151' }}>Assurance (€)</th>
                  <th style={{ padding: '8px', textAlign: 'right', fontWeight: '600', color: '#374151' }}>Total (€)</th>
                </tr>
              </thead>
              <tbody>
                {previewData.preview.map((row, index) => {
                  const capital = row.capital ?? 0;
                  const interest = row.interest ?? 0;
                  const insurance = row.insurance ?? 0;
                  const total = row.total ?? 0;
                  
                  return (
                    <tr key={index} style={{ borderBottom: '1px solid #e5e7eb' }}>
                      <td style={{ padding: '8px' }}>{row.year}</td>
                      <td style={{ padding: '8px', textAlign: 'right' }}>
                        {capital.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €
                      </td>
                      <td style={{ padding: '8px', textAlign: 'right' }}>
                        {interest.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €
                      </td>
                      <td style={{ padding: '8px', textAlign: 'right' }}>
                        {insurance.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €
                      </td>
                      <td style={{ padding: '8px', textAlign: 'right', fontWeight: '600' }}>
                        {total.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Résultat de l'import */}
        {importResult && (
          <div style={{ marginBottom: '20px', padding: '12px', backgroundColor: '#d1fae5', borderRadius: '6px' }}>
            <div style={{ fontWeight: '600', marginBottom: '8px', color: '#065f46' }}>✅ Import réussi!</div>
            <div style={{ fontSize: '13px', color: '#047857' }}>
              {importResult.message}
            </div>
            {importResult.warnings.length > 0 && (
              <div style={{ marginTop: '8px' }}>
                {importResult.warnings.map((warning, index) => (
                  <div key={index} style={{ fontSize: '12px', color: '#92400e', marginTop: '4px' }}>
                    ⚠️ {warning}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Erreur d'import */}
        {importError && (
          <div style={{ marginBottom: '20px', padding: '12px', backgroundColor: '#fee2e2', borderRadius: '6px' }}>
            <div style={{ fontWeight: '600', marginBottom: '8px', color: '#991b1b' }}>❌ Erreur lors de l'import:</div>
            <div style={{ fontSize: '13px', color: '#7f1d1d' }}>{importError}</div>
          </div>
        )}

        {/* Boutons */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button
            onClick={onClose}
            disabled={isImporting}
            style={{
              padding: '10px 20px',
              fontSize: '14px',
              fontWeight: '500',
              color: '#374151',
              backgroundColor: '#f3f4f6',
              border: 'none',
              borderRadius: '6px',
              cursor: isImporting ? 'not-allowed' : 'pointer',
            }}
          >
            {importResult ? 'Fermer' : 'Annuler'}
          </button>
          {!importResult && (
            <button
              onClick={handleImport}
              disabled={isImporting || previewData.validation_errors.length > 0}
              style={{
                padding: '10px 20px',
                fontSize: '14px',
                fontWeight: '500',
                color: 'white',
                backgroundColor: isImporting || previewData.validation_errors.length > 0 ? '#9ca3af' : '#3b82f6',
                border: 'none',
                borderRadius: '6px',
                cursor: isImporting || previewData.validation_errors.length > 0 ? 'not-allowed' : 'pointer',
              }}
            >
              {isImporting ? '⏳ Import en cours...' : '✅ Importer'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

