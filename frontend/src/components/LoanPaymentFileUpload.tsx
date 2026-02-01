/**
 * LoanPaymentFileUpload component - Bouton "Load Mensualités" pour sélectionner un fichier Excel de mensualités
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useRef } from 'react';
import { loanPaymentsAPI, LoanPaymentPreviewResponse } from '@/api/client';
import LoanPaymentPreviewModal from './LoanPaymentPreviewModal';
import { useProperty } from '@/contexts/PropertyContext';

interface LoanPaymentFileUploadProps {
  loanName?: string; // Nom du crédit pour l'import (par défaut "Prêt principal")
  onFileSelect?: (file: File) => void;
  onImportComplete?: () => void;
}

export default function LoanPaymentFileUpload({ 
  loanName = 'Prêt principal',
  onFileSelect, 
  onImportComplete 
}: LoanPaymentFileUploadProps) {
  const { activeProperty } = useProperty();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewData, setPreviewData] = useState<LoanPaymentPreviewResponse | null>(null);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      console.log('📁 [LoanPaymentFileUpload] Fichier sélectionné:', file.name, `(${(file.size / 1024).toFixed(2)} KB)`);
      
      // Vérifier que c'est un fichier Excel ou CSV
      const filenameLower = file.name.toLowerCase();
      if (!filenameLower.endsWith('.xlsx') && !filenameLower.endsWith('.xls') && !filenameLower.endsWith('.csv')) {
        console.error('❌ [LoanPaymentFileUpload] Fichier non supporté:', file.name);
        alert('Veuillez sélectionner un fichier Excel (.xlsx, .xls) ou CSV (.csv)');
        return;
      }
      setSelectedFile(file);
      
      if (onFileSelect) {
        onFileSelect(file);
      }
      
      // Appeler preview automatiquement
      if (!activeProperty?.id || activeProperty.id <= 0) {
        console.error('[LoanPaymentFileUpload] Property ID invalide');
        alert('Property ID invalide');
        return;
      }
      console.log('⏳ [LoanPaymentFileUpload] Début du preview...');
      setIsLoadingPreview(true);
      try {
        const preview = await loanPaymentsAPI.preview(activeProperty.id, file);
        console.log('✅ [LoanPaymentFileUpload] Preview réussi!', preview);
        console.log('📊 [LoanPaymentFileUpload] Stats:', {
          total_rows: preview.total_rows,
          years_detected: preview.stats.years_detected,
          records_to_create: preview.stats.records_to_create,
          existing_records: preview.stats.existing_records,
        });
        setPreviewData(preview);
        setShowModal(true);
        console.log('✅ [LoanPaymentFileUpload] Modal ouvert');
      } catch (error) {
        console.error('❌ [LoanPaymentFileUpload] Erreur lors du preview:', error);
        const errorMessage = error instanceof Error ? error.message : 'Erreur inconnue';
        alert(`Erreur lors de l'analyse du fichier: ${errorMessage}`);
      } finally {
        setIsLoadingPreview(false);
        console.log('🏁 [LoanPaymentFileUpload] Preview terminé');
      }
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setPreviewData(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div style={{ marginBottom: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
        <button
          onClick={handleButtonClick}
          style={{
            backgroundColor: '#1e3a5f',
            color: 'white',
            border: 'none',
            padding: '10px 20px',
            borderRadius: '4px',
            fontSize: '14px',
            fontWeight: '500',
            cursor: 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.backgroundColor = '#2a4f7a';
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.backgroundColor = '#1e3a5f';
          }}
        >
          📊 Load Mensualités
        </button>
        
        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx,.xls,.csv"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />

        {selectedFile && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
            <span style={{ fontSize: '14px', color: '#666' }}>
              Fichier sélectionné: <strong>{selectedFile.name}</strong>
            </span>
            <button
              onClick={handleRemoveFile}
              style={{
                backgroundColor: 'transparent',
                border: '1px solid #ccc',
                color: '#666',
                padding: '4px 8px',
                borderRadius: '4px',
                fontSize: '12px',
                cursor: 'pointer',
              }}
            >
              ✕ Retirer
            </button>
          </div>
        )}
      </div>

      {selectedFile && (
        <div style={{ 
          padding: '12px', 
          backgroundColor: '#f5f5f5', 
          borderRadius: '4px',
          fontSize: '13px',
          color: '#666'
        }}>
          <div><strong>Taille:</strong> {(selectedFile.size / 1024).toFixed(2)} KB</div>
          <div><strong>Type:</strong> {selectedFile.type || 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}</div>
          <div><strong>Crédit:</strong> {loanName}</div>
          {isLoadingPreview && (
            <div style={{ marginTop: '8px', color: '#1e3a5f' }}>⏳ Analyse du fichier en cours...</div>
          )}
        </div>
      )}

      {showModal && selectedFile && previewData && (
        <LoanPaymentPreviewModal
          file={selectedFile}
          previewData={previewData}
          loanName={loanName}
          onImportComplete={() => {
            setShowModal(false);
            setSelectedFile(null);
            setPreviewData(null);
            if (fileInputRef.current) {
              fileInputRef.current.value = '';
            }
            if (onImportComplete) {
              onImportComplete();
            }
          }}
          onClose={() => {
            setShowModal(false);
            setSelectedFile(null);
            setPreviewData(null);
            if (fileInputRef.current) {
              fileInputRef.current.value = '';
            }
          }}
        />
      )}
    </div>
  );
}
