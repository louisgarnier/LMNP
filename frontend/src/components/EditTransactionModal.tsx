/**
 * EditTransactionModal component - Popup pour éditer une transaction
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState } from 'react';
import { transactionsAPI, Transaction } from '@/api/client';

interface EditTransactionModalProps {
  transaction: Transaction;
  onClose: () => void;
  onSave: () => void;
}

export default function EditTransactionModal({
  transaction,
  onClose,
  onSave,
}: EditTransactionModalProps) {
  // Initialiser la date au format YYYY-MM-DD pour l'input date
  const getInitialDate = () => {
    const dateStr = transaction.date;
    if (dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
      return dateStr;
    }
    // Si c'est au format ISO avec time, extraire juste la date
    return dateStr.split('T')[0];
  };
  
  const [date, setDate] = useState(getInitialDate());
  const [quantite, setQuantite] = useState(transaction.quantite.toString());
  const [nom, setNom] = useState(transaction.nom);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    // Validation
    if (!date) {
      setError('La date est requise');
      return;
    }
    
    const quantiteNum = parseFloat(quantite);
    if (isNaN(quantiteNum)) {
      setError('La quantité doit être un nombre valide');
      return;
    }
    
    if (!nom.trim()) {
      setError('Le nom est requis');
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      console.log('🔄 [EditTransactionModal] Mise à jour transaction:', {
        id: transaction.id,
        date,
        quantite: quantiteNum,
        nom: nom.trim(),
      });
      
      const result = await transactionsAPI.update(transaction.id, {
        date,
        quantite: quantiteNum,
        nom: nom.trim(),
      });
      
      console.log('✅ [EditTransactionModal] Transaction mise à jour:', result);
      
      onSave();
      onClose();
    } catch (err) {
      console.error('❌ [EditTransactionModal] Erreur lors de la mise à jour:', err);
      
      // Gérer différents types d'erreurs
      let errorMessage = 'Erreur lors de la mise à jour';
      if (err instanceof Error) {
        errorMessage = err.message;
      } else if (typeof err === 'object' && err !== null) {
        // Si c'est un objet, essayer d'extraire le message
        const errObj = err as any;
        if (errObj.message) {
          errorMessage = errObj.message;
        } else if (errObj.detail) {
          errorMessage = errObj.detail;
        } else {
          errorMessage = JSON.stringify(err);
        }
      }
      
      setError(errorMessage);
    } finally {
      setIsSaving(false);
    }
  };

  // Convertir date YYYY-MM-DD en format pour input date
  const formatDateForInput = (dateString: string): string => {
    // Si c'est déjà au format YYYY-MM-DD, retourner tel quel
    if (dateString.match(/^\d{4}-\d{2}-\d{2}$/)) {
      return dateString;
    }
    // Sinon, extraire la partie date
    return dateString.split('T')[0];
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
          maxWidth: '500px',
          width: '90%',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1a1a1a', margin: 0 }}>
            Éditer la transaction
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

        {/* Formulaire */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#1a1a1a', marginBottom: '8px' }}>
              Date *
            </label>
            <input
              type="date"
              value={formatDateForInput(date)}
              onChange={(e) => setDate(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 12px',
                border: '1px solid #ccc',
                borderRadius: '4px',
                fontSize: '14px',
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#1a1a1a', marginBottom: '8px' }}>
              Quantité *
            </label>
            <input
              type="number"
              step="0.01"
              value={quantite}
              onChange={(e) => setQuantite(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 12px',
                border: '1px solid #ccc',
                borderRadius: '4px',
                fontSize: '14px',
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#1a1a1a', marginBottom: '8px' }}>
              Nom *
            </label>
            <input
              type="text"
              value={nom}
              onChange={(e) => setNom(e.target.value)}
              maxLength={500}
              style={{
                width: '100%',
                padding: '10px 12px',
                border: '1px solid #ccc',
                borderRadius: '4px',
                fontSize: '14px',
              }}
            />
          </div>

          {/* Erreur */}
          {error && (
            <div style={{ 
              padding: '12px', 
              backgroundColor: '#fee2e2', 
              borderRadius: '4px',
              color: '#dc2626',
              fontSize: '14px'
            }}>
              ❌ {error}
            </div>
          )}

          {/* Info solde */}
          <div style={{ 
            padding: '12px', 
            backgroundColor: '#f0f9ff', 
            borderRadius: '4px',
            fontSize: '13px',
            color: '#666'
          }}>
            ℹ️ Le solde sera automatiquement recalculé après la sauvegarde, ainsi que celui de toutes les transactions suivantes.
          </div>
        </div>

        {/* Boutons */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '24px' }}>
          <button
            onClick={onClose}
            disabled={isSaving}
            style={{
              padding: '10px 20px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              backgroundColor: 'white',
              color: '#666',
              fontSize: '14px',
              cursor: isSaving ? 'not-allowed' : 'pointer',
              opacity: isSaving ? 0.5 : 1,
            }}
          >
            Annuler
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            style={{
              padding: '10px 20px',
              border: 'none',
              borderRadius: '4px',
              backgroundColor: isSaving ? '#ccc' : '#1e3a5f',
              color: 'white',
              fontSize: '14px',
              fontWeight: '500',
              cursor: isSaving ? 'not-allowed' : 'pointer',
            }}
          >
            {isSaving ? '⏳ Sauvegarde...' : '💾 Sauvegarder'}
          </button>
        </div>
      </div>
    </div>
  );
}

