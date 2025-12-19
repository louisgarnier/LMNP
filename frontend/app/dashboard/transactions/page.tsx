/**
 * Transactions page
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useSearchParams } from 'next/navigation';
import FileUpload from '@/components/FileUpload';
import ImportLog from '@/components/ImportLog';
import TransactionsTable from '@/components/TransactionsTable';

export default function TransactionsPage() {
  const searchParams = useSearchParams();
  const filter = searchParams?.get('filter');
  const tab = searchParams?.get('tab');

  const handleFileSelect = (file: File) => {
    console.log('📁 [TransactionsPage] Fichier sélectionné:', file.name);
    // Le preview est maintenant géré automatiquement dans FileUpload
  };

  const handleImportComplete = () => {
    console.log('✅ [TransactionsPage] Import terminé');
    // Le tableau se rechargera automatiquement via son propre useEffect
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
          <TransactionsTable onDelete={handleImportComplete} />
        )}

        {filter === 'unclassified' && (
          <div>
            <p style={{ fontSize: '14px', color: '#666' }}>
              Les transactions non classées seront affichées ici (à implémenter après enrichissement).
            </p>
          </div>
        )}

        {filter === 'to_validate' && (
          <div>
            <p style={{ fontSize: '14px', color: '#666' }}>
              Les transactions à valider seront affichées ici (à implémenter après enrichissement).
            </p>
          </div>
        )}

        {tab === 'load_trades' && (
          <div>
            <FileUpload onFileSelect={handleFileSelect} onImportComplete={handleImportComplete} />
            
            <div style={{ 
              marginTop: '24px', 
              padding: '16px', 
              backgroundColor: '#f9f9f9', 
              borderRadius: '4px',
              fontSize: '14px',
              color: '#666'
            }}>
              <p style={{ margin: 0 }}>
                Sélectionnez un fichier CSV pour charger vos transactions. 
                Le fichier sera analysé et vous pourrez confirmer le mapping des colonnes.
              </p>
            </div>
          </div>
        )}

        {tab === 'log' && (
          <ImportLog />
        )}
      </div>
    </div>
  );
}

