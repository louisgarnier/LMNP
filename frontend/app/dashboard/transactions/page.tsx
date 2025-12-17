/**
 * Transactions page
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useSearchParams } from 'next/navigation';
import FileUpload from '@/components/FileUpload';

export default function TransactionsPage() {
  const searchParams = useSearchParams();
  const filter = searchParams?.get('filter');
  const tab = searchParams?.get('tab');

  const handleFileSelect = (file: File) => {
    console.log('Fichier sélectionné:', file.name);
    // TODO: Appeler API preview dans Step 2.1.5
  };

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: '600', color: '#1a1a1a', marginBottom: '8px' }}>
          Transactions
        </h1>
        <p style={{ fontSize: '14px', color: '#666' }}>
          Gestion et visualisation de toutes vos transactions
        </p>
      </div>

      {/* Contenu selon l'onglet actif */}
      <div style={{ 
        backgroundColor: 'white', 
        borderRadius: '8px', 
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        padding: '24px',
        minHeight: '400px'
      }}>
        {(!filter && !tab) && (
          <div>
            <p style={{ fontSize: '14px', color: '#666' }}>
              Toutes les transactions seront affichées ici (à implémenter après Step 2.1.7).
            </p>
          </div>
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
            <FileUpload onFileSelect={handleFileSelect} />
            
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
      </div>
    </div>
  );
}

