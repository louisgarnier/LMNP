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
      // Vérifier que c'est un fichier CSV
      if (!file.name.endsWith('.csv')) {
        alert('Veuillez sélectionner un fichier CSV');
        return;
      }
      setSelectedFile(file);
      
      if (onFileSelect) {
        onFileSelect(file);
      }
      
      // Appeler preview automatiquement
      setIsLoadingPreview(true);
      try {
        const preview = await fileUploadAPI.preview(file);
        setPreviewData(preview);
        setShowModal(true);
      } catch (error) {
        console.error('Erreur lors du preview:', error);
        alert(`Erreur lors de l'analyse du fichier: ${error instanceof Error ? error.message : 'Erreur inconnue'}`);
      } finally {
        setIsLoadingPreview(false);
      }
    }
  };
  
  const [isImporting, setIsImporting] = useState(false);

  const handleConfirmImport = async (mapping: any[]) => {
    if (!selectedFile) return;
    
    setIsImporting(true);
    try {
      const result = await fileUploadAPI.import(selectedFile, mapping);
      setShowModal(false);
      setSelectedFile(null);
      setPreviewData(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      if (onImportComplete) {
        onImportComplete();
      }
      alert(`Import terminé: ${result.imported_count} transactions importées, ${result.duplicates_count} doublons détectés`);
    } catch (error) {
      console.error('Erreur lors de l\'import:', error);
      alert(`Erreur lors de l'import: ${error instanceof Error ? error.message : 'Erreur inconnue'}`);
    } finally {
      setIsImporting(false);
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

      {showModal && selectedFile && previewData && !isImporting && (
        <ColumnMappingModal
          file={selectedFile}
          previewData={previewData}
          onConfirm={handleConfirmImport}
          onClose={() => {
            if (!isImporting) {
              setShowModal(false);
              setSelectedFile(null);
              setPreviewData(null);
              if (fileInputRef.current) {
                fileInputRef.current.value = '';
              }
            }
          }}
        />
      )}

      {isImporting && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1001,
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '24px',
            borderRadius: '8px',
            textAlign: 'center',
          }}>
            <div style={{ fontSize: '16px', marginBottom: '12px' }}>⏳ Import en cours...</div>
            <div style={{ fontSize: '14px', color: '#666' }}>Veuillez patienter</div>
          </div>
        </div>
      )}
    </div>
  );
}

