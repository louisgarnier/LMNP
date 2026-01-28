/**
 * Home page - Property selection
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 * Always check with the user before modifying this file.
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useProperty } from '@/contexts/PropertyContext';

export default function HomePage() {
  const router = useRouter();
  const { activeProperty, properties, loading, error, setActiveProperty, createProperty, deleteProperty } = useProperty();
  const [isCreating, setIsCreating] = useState(false);
  const [newPropertyName, setNewPropertyName] = useState('');
  const [newPropertyAddress, setNewPropertyAddress] = useState('');
  const [creating, setCreating] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; propertyId: number; propertyName: string } | null>(null);

  // Redirect to dashboard if property is already selected
  // Wait for loading to complete before checking activeProperty
  useEffect(() => {
    if (!loading && activeProperty) {
      router.push('/dashboard');
    }
  }, [activeProperty, loading, router]);

  const handleSelectProperty = (propertyId: number) => {
    const property = properties.find(p => p.id === propertyId);
    if (property) {
      setActiveProperty(property);
      router.push('/dashboard');
    }
  };

  const handleCreateProperty = async () => {
    if (!newPropertyName.trim()) {
      alert('Le nom de la propriété est requis');
      return;
    }

    try {
      setCreating(true);
      const newProperty = await createProperty(newPropertyName.trim(), newPropertyAddress.trim() || undefined);
      setActiveProperty(newProperty);
      setNewPropertyName('');
      setNewPropertyAddress('');
      setIsCreating(false);
    router.push('/dashboard');
    } catch (err: any) {
      console.error('Error creating property:', err);
      alert(err.message || 'Erreur lors de la création de la propriété');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteProperty = async (propertyId: number, propertyName: string) => {
    const confirmMessage = `⚠️ ATTENTION : Suppression définitive\n\n` +
      `Êtes-vous sûr de vouloir supprimer la propriété "${propertyName}" ?\n\n` +
      `Cette action supprimera DÉFINITIVEMENT :\n` +
      `- Toutes les transactions\n` +
      `- Tous les mappings\n` +
      `- Tous les crédits et mensualités\n` +
      `- Tous les amortissements\n` +
      `- Tous les comptes de résultat\n` +
      `- Tous les bilans\n` +
      `- Toutes les configurations\n\n` +
      `Cette action est IRRÉVERSIBLE.`;

    if (!window.confirm(confirmMessage)) {
      return;
    }

    try {
      setDeletingId(propertyId);
      setContextMenu(null); // Fermer le menu contextuel
      await deleteProperty(propertyId);
      
      // Si la propriété supprimée était la propriété active, la désélectionner
      if (activeProperty?.id === propertyId) {
        setActiveProperty(null);
      }
    } catch (err: any) {
      console.error('Error deleting property:', err);
      alert(err.message || 'Erreur lors de la suppression de la propriété');
    } finally {
      setDeletingId(null);
    }
  };

  const handleContextMenu = (e: React.MouseEvent, propertyId: number, propertyName: string) => {
    e.preventDefault();
    e.stopPropagation();
    setContextMenu({
      x: e.clientX,
      y: e.clientY,
      propertyId,
      propertyName,
    });
  };

  const closeContextMenu = () => {
    setContextMenu(null);
  };

  // Fermer le menu contextuel si on clique ailleurs
  useEffect(() => {
    const handleClickOutside = () => {
      if (contextMenu) {
        closeContextMenu();
      }
    };

    if (contextMenu) {
      document.addEventListener('click', handleClickOutside);
      return () => {
        document.removeEventListener('click', handleClickOutside);
      };
    }
  }, [contextMenu]);

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f9fafb' }}>
        <div style={{ textAlign: 'center' }}>
          <p style={{ color: '#6b7280' }}>Chargement des propriétés...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f9fafb' }}>
        <div style={{ textAlign: 'center', color: '#dc2626', maxWidth: '600px', padding: '20px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '16px' }}>Erreur de chargement</h2>
          <p style={{ marginBottom: '16px' }}>{error}</p>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: '12px 24px',
              backgroundColor: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '16px',
              cursor: 'pointer',
              fontWeight: '500',
            }}
          >
            Recharger la page
          </button>
          <p style={{ marginTop: '16px', fontSize: '14px', color: '#6b7280' }}>
            Vérifiez que le serveur backend est démarré sur http://localhost:8000
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f9fafb', padding: '40px 20px' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <h1 style={{ fontSize: '32px', fontWeight: 'bold', color: '#1f2937', marginBottom: '8px' }}>
            LMNP - Gestion Comptable
          </h1>
          <p style={{ fontSize: '16px', color: '#6b7280' }}>
            Sélectionnez une propriété pour commencer
          </p>
        </div>

        {!isCreating ? (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px', marginBottom: '40px' }}>
              {properties.map((property) => (
                <div
                  key={property.id}
                  style={{
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    padding: '24px',
                    transition: 'all 0.2s',
                    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
                    position: 'relative',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = '#3b82f6';
                    e.currentTarget.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = '#e5e7eb';
                    e.currentTarget.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.1)';
                  }}
                  onContextMenu={(e) => handleContextMenu(e, property.id, property.name)}
                >
                  <div
                    onClick={() => handleSelectProperty(property.id)}
                    style={{ cursor: 'pointer' }}
                  >
                    <h3 style={{ fontSize: '20px', fontWeight: '600', color: '#1f2937', marginBottom: '8px' }}>
                      {property.name}
                    </h3>
                    {property.address && (
                      <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '12px' }}>
                        {property.address}
                      </p>
                    )}
                    <p style={{ fontSize: '12px', color: '#9ca3af' }}>
                      Créé le {new Date(property.created_at).toLocaleDateString('fr-FR')}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {/* Menu contextuel */}
            {contextMenu && (
              <div
                style={{
                  position: 'fixed',
                  top: contextMenu.y,
                  left: contextMenu.x,
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                  zIndex: 1000,
                  minWidth: '200px',
                  padding: '4px 0',
                }}
                onClick={(e) => e.stopPropagation()}
              >
                <button
                  onClick={() => handleDeleteProperty(contextMenu.propertyId, contextMenu.propertyName)}
                  disabled={deletingId === contextMenu.propertyId}
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    textAlign: 'left',
                    border: 'none',
                    backgroundColor: 'transparent',
                    color: deletingId === contextMenu.propertyId ? '#9ca3af' : '#dc2626',
                    cursor: deletingId === contextMenu.propertyId ? 'not-allowed' : 'pointer',
                    fontSize: '14px',
                    fontWeight: '500',
                    transition: 'background-color 0.2s',
                  }}
                  onMouseEnter={(e) => {
                    if (deletingId !== contextMenu.propertyId) {
                      e.currentTarget.style.backgroundColor = '#fef2f2';
                    }
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  {deletingId === contextMenu.propertyId ? 'Suppression...' : '🗑️ Supprimer'}
                </button>
              </div>
            )}

            <div style={{ textAlign: 'center' }}>
              <button
                onClick={() => setIsCreating(true)}
                style={{
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '12px 24px',
                  fontSize: '16px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#2563eb';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#3b82f6';
                }}
              >
                + Créer une nouvelle propriété
              </button>
            </div>
          </>
        ) : (
          <div style={{ maxWidth: '500px', margin: '0 auto', backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '32px' }}>
            <h2 style={{ fontSize: '24px', fontWeight: '600', color: '#1f2937', marginBottom: '24px' }}>
              Créer une nouvelle propriété
            </h2>
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#374151', marginBottom: '8px' }}>
                Nom de la propriété *
              </label>
              <input
                type="text"
                value={newPropertyName}
                onChange={(e) => setNewPropertyName(e.target.value)}
                placeholder="Ex: Appartement 1"
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px',
                }}
                autoFocus
              />
            </div>
            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#374151', marginBottom: '8px' }}>
                Adresse (optionnel)
              </label>
              <input
                type="text"
                value={newPropertyAddress}
                onChange={(e) => setNewPropertyAddress(e.target.value)}
                placeholder="Ex: 123 Rue de Test, 75001 Paris"
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px',
                }}
              />
            </div>
            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={handleCreateProperty}
                disabled={creating || !newPropertyName.trim()}
                style={{
                  flex: 1,
                  backgroundColor: creating || !newPropertyName.trim() ? '#9ca3af' : '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '10px 20px',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: creating || !newPropertyName.trim() ? 'not-allowed' : 'pointer',
                }}
              >
                {creating ? 'Création...' : 'Créer'}
              </button>
              <button
                onClick={() => {
                  setIsCreating(false);
                  setNewPropertyName('');
                  setNewPropertyAddress('');
                }}
                disabled={creating}
                style={{
                  flex: 1,
                  backgroundColor: 'white',
                  color: '#374151',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  padding: '10px 20px',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: creating ? 'not-allowed' : 'pointer',
                }}
              >
                Annuler
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}


