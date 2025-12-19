/**
 * FileUpload component - Bouton "Load Trades" pour sélectionner un fichier CSV
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useRef } from 'react';
import { fileUploadAPI, FilePreviewResponse } from '@/api/client';
import ColumnMappingModal from './ColumnMappingModal';

interface FileUploadProps {
  onFileSelect?: (file: File) => void;
  onImportComplete?: () => void;
}

export default function FileUpload({ onFileSelect, onImportComplete }: FileUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewData, setPreviewData] = useState<FilePreviewResponse | null>(null);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      console.log('📁 [FileUpload] Fichier sélectionné:', file.name, `(${(file.size / 1024).toFixed(2)} KB)`);
      
      // Vérifier que c'est un fichier CSV
      if (!file.name.endsWith('.csv')) {
        console.error('❌ [FileUpload] Fichier non CSV:', file.name);
        alert('Veuillez sélectionner un fichier CSV');
        return;
      }
      setSelectedFile(file);
      
      if (onFileSelect) {
        onFileSelect(file);
      }
      
      // Appeler preview automatiquement
      console.log('⏳ [FileUpload] Début du preview...');
      setIsLoadingPreview(true);
      try {
        const preview = await fileUploadAPI.preview(file);
        console.log('✅ [FileUpload] Preview réussi!', preview);
        console.log('📊 [FileUpload] Stats:', {
          total_rows: preview.total_rows,
          valid_rows: preview.stats.valid_rows,
          encoding: preview.encoding,
          separator: preview.separator,
        });
        setPreviewData(preview);
        setShowModal(true);
        console.log('✅ [FileUpload] Modal ouvert');
      } catch (error) {
        console.error('❌ [FileUpload] Erreur lors du preview:', error);
        const errorMessage = error instanceof Error ? error.message : 'Erreur inconnue';
        alert(`Erreur lors de l'analyse du fichier: ${errorMessage}`);
      } finally {
        setIsLoadingPreview(false);
        console.log('🏁 [FileUpload] Preview terminé');
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
          📁 Load Trades
        </button>
        
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
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
          <div><strong>Type:</strong> {selectedFile.type || 'text/csv'}</div>
          {isLoadingPreview && (
            <div style={{ marginTop: '8px', color: '#1e3a5f' }}>⏳ Analyse du fichier en cours...</div>
          )}
        </div>
      )}

      {showModal && selectedFile && previewData && (
        <ColumnMappingModal
          file={selectedFile}
          previewData={previewData}
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

