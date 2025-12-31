/**
 * LoanPaymentFileUpload component - Bouton "Load mensualités" pour sélectionner un fichier Excel de mensualités
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useRef } from 'react';
import { loanPaymentsAPI, LoanPaymentPreviewResponse } from '@/api/client';
import LoanPaymentPreviewModal from './LoanPaymentPreviewModal';

interface LoanPaymentFileUploadProps {
  loanName?: string;
  onFileSelect?: (file: File) => void;
  onImportComplete?: () => void;
}

export default function LoanPaymentFileUpload({ 
  loanName = 'Prêt principal',
  onFileSelect, 
  onImportComplete 
}: LoanPaymentFileUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewData, setPreviewData] = useState<LoanPaymentPreviewResponse | null>(null);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      console.log('📋 [LoanPaymentFileUpload] Fichier sélectionné:', file.name, `(${(file.size / 1024).toFixed(2)} KB)`);
      
      // Vérifier que c'est un fichier Excel
      const filenameLower = file.name.toLowerCase();
      if (!filenameLower.endsWith('.xlsx') && !filenameLower.endsWith('.xls')) {
        console.error('❌ [LoanPaymentFileUpload] Fichier non Excel:', file.name);
        alert('Veuillez sélectionner un fichier Excel (.xlsx ou .xls)');
        return;
      }
      setSelectedFile(file);
      
      if (onFileSelect) {
        onFileSelect(file);
      }
      
      // Appeler preview automatiquement
      console.log('⏳ [LoanPaymentFileUpload] Début du preview...');
      setIsLoadingPreview(true);
      try {
        const preview = await loanPaymentsAPI.preview(file, loanName);
        console.log('✅ [LoanPaymentFileUpload] Preview réussi!', preview);
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
          📄 Load Mensualités
        </button>
        {selectedFile && (
          <button
            onClick={handleRemoveFile}
            style={{
              backgroundColor: '#dc2626',
              color: 'white',
              border: 'none',
              padding: '6px 12px',
              borderRadius: '4px',
              fontSize: '12px',
              cursor: 'pointer',
            }}
          >
            ✕ Retirer
          </button>
        )}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".xlsx,.xls"
        onChange={handleFileChange}
        style={{ display: 'none' }}
      />

      {selectedFile && (
        <div style={{ 
          padding: '12px', 
          backgroundColor: '#f5f5f5', 
          borderRadius: '4px',
          fontSize: '13px',
          color: '#666'
        }}>
          <div><strong>Fichier:</strong> {selectedFile.name}</div>
          <div><strong>Taille:</strong> {(selectedFile.size / 1024).toFixed(2)} KB</div>
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

