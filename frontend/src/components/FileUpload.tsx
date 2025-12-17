/**
 * FileUpload component - Bouton "Load Trades" pour sélectionner un fichier CSV
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useRef } from 'react';

interface FileUploadProps {
  onFileSelect?: (file: File) => void;
}

export default function FileUpload({ onFileSelect }: FileUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
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
        </div>
      )}
    </div>
  );
}

