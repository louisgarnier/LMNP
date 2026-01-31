'use client';

import React, { useState, useEffect } from 'react';
import { mappingsAPI, AllowedMapping, AllowedMappingListResponse } from '../api/client';
import { useProperty } from '@/contexts/PropertyContext';

export default function AllowedMappingsTable() {
  const { activeProperty } = useProperty();
  const [mappings, setMappings] = useState<AllowedMapping[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [isResetting, setIsResetting] = useState(false);
  
  // États pour la modal de création
  const [newLevel1, setNewLevel1] = useState('');
  const [newLevel2, setNewLevel2] = useState('');
  const [newLevel3, setNewLevel3] = useState('');
  const [customLevel1, setCustomLevel1] = useState(false);
  const [customLevel2, setCustomLevel2] = useState(false);
  const [createAvailableLevel1, setCreateAvailableLevel1] = useState<string[]>([]);
  const [createAvailableLevel2, setCreateAvailableLevel2] = useState<string[]>([]);
  const [createAvailableLevel3, setCreateAvailableLevel3] = useState<string[]>([]);
  const [similarLevel1Warning, setSimilarLevel1Warning] = useState<string[]>([]);
  const [similarLevel2Warning, setSimilarLevel2Warning] = useState<string[]>([]);
  
  // États pour les valeurs autorisées (pour les dropdowns)
  const [allowedLevel1List, setAllowedLevel1List] = useState<string[]>([]);
  const [allowedLevel2List, setAllowedLevel2List] = useState<string[]>([]);
  
  // Valeurs level_3 autorisées (fixes)
  const ALLOWED_LEVEL_3_VALUES = ['Passif', 'Produits', 'Emprunt', 'Charges Déductibles', 'Actif'];

  const loadMappings = async () => {
    console.log('[AllowedMappingsTable] loadMappings appelé - activeProperty:', activeProperty);
    
    if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
      console.warn('[AllowedMappingsTable] loadMappings - PROPERTY INVALIDE:', {
        activeProperty,
        id: activeProperty?.id,
        reason: !activeProperty ? 'activeProperty is null/undefined' : 
                !activeProperty.id ? 'activeProperty.id is null/undefined' : 
                'activeProperty.id <= 0'
      });
      setError('Aucune propriété sélectionnée');
      setMappings([]);
      setTotal(0);
      setLoading(false);
      return;
    }
    
    setLoading(true);
    setError(null);
    try {
      console.log('[AllowedMappingsTable] loadMappings - Appel API avec propertyId:', activeProperty.id, 'page:', page, 'pageSize:', pageSize);
      const response = await mappingsAPI.getAllowedMappings(activeProperty.id, (page - 1) * pageSize, pageSize);
      console.log('[AllowedMappingsTable] loadMappings - Réponse API:', {
        total: response.total,
        count: response.mappings.length,
        propertyId: activeProperty.id
      });
      setMappings(response.mappings);
      setTotal(response.total);
    } catch (err: any) {
      console.error('[AllowedMappingsTable] loadMappings - Erreur:', err);
      setError(err.message || 'Erreur lors du chargement des mappings autorisés');
      setMappings([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMappings();
  }, [page, pageSize, activeProperty?.id]);

  // Fonction pour détecter les valeurs similaires
  const findSimilarValues = (value: string, existingValues: string[]): string[] => {
    if (!value || value.trim() === '') return [];
    
    const normalizedValue = value.toLowerCase().trim();
    const similar: string[] = [];
    
    for (const existing of existingValues) {
      const normalizedExisting = existing.toLowerCase().trim();
      
      // Détecter si les valeurs sont similaires (même racine, pluriel/singulier, etc.)
      if (normalizedValue === normalizedExisting) {
        similar.push(existing);
      } else if (
        normalizedValue.includes(normalizedExisting) || 
        normalizedExisting.includes(normalizedValue)
      ) {
        // Vérifier si l'une contient l'autre (ex: "caution" vs "cautions")
        const shorter = normalizedValue.length < normalizedExisting.length ? normalizedValue : normalizedExisting;
        const longer = normalizedValue.length >= normalizedExisting.length ? normalizedValue : normalizedExisting;
        
        // Si la différence est juste un 's' à la fin (pluriel), considérer comme similaire
        if (longer === shorter + 's' || shorter === longer.slice(0, -1)) {
          similar.push(existing);
        } else if (longer.includes(shorter) && shorter.length >= 4) {
          // Si la valeur plus courte est contenue dans la plus longue et fait au moins 4 caractères
          similar.push(existing);
        }
      }
    }
    
    return similar;
  };

  // Charger les valeurs autorisées au montage
  useEffect(() => {
    const loadAllowedValues = async () => {
      if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
        return;
      }
      try {
        const level1Response = await mappingsAPI.getAllowedLevel1(activeProperty.id);
        const level1List = level1Response.level_1 || [];
        setAllowedLevel1List(level1List);
        setCreateAvailableLevel1(level1List);
        
        // Charger aussi tous les level_2 pour la détection de similarité
        const level2Response = await mappingsAPI.getAllowedLevel2(activeProperty.id);
        const level2List = level2Response.level_2 || [];
        setAllowedLevel2List(level2List);
      } catch (err) {
        console.error('Error loading allowed values:', err);
      }
    };
    loadAllowedValues();
  }, [activeProperty?.id]);

  // Handlers pour la modal de création
  const handleCreateLevel1Change = async (value: string) => {
    if (value === '__CUSTOM__') {
      setCustomLevel1(true);
      setNewLevel1('');
      setSimilarLevel1Warning([]);
      // Quand on crée un nouveau level_1, charger TOUS les level_2 disponibles
      if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
        return;
      }
      try {
        const level2Response = await mappingsAPI.getAllowedLevel2(activeProperty.id);
        const level2List = level2Response.level_2 || [];
        setCreateAvailableLevel2(level2List);
      } catch (err) {
        console.error('Error loading allowed level_2:', err);
      }
    } else {
      setCustomLevel1(false);
      setNewLevel1(value);
      setNewLevel2('');
      setNewLevel3('');
      setCreateAvailableLevel2([]);
      setCreateAvailableLevel3([]);
      setSimilarLevel1Warning([]);
      
      if (value) {
        try {
          if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
            return;
          }
          const level2Response = await mappingsAPI.getAllowedLevel2(activeProperty.id, value);
          const level2List = level2Response.level_2 || [];
          setCreateAvailableLevel2(level2List);
        } catch (err) {
          console.error('Error loading allowed level_2:', err);
        }
      }
    }
  };

  const handleCreateLevel1InputChange = async (value: string) => {
    setNewLevel1(value);
    
    // Détecter les valeurs similaires
    if (value && value.trim() !== '') {
      const similar = findSimilarValues(value, allowedLevel1List);
      setSimilarLevel1Warning(similar);
    } else {
      setSimilarLevel1Warning([]);
    }
    
    // Quand on tape un nouveau level_1, s'assurer que tous les level_2 sont disponibles
    if (value && value.trim() !== '' && createAvailableLevel2.length === 0) {
      if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
        return;
      }
      try {
        const level2Response = await mappingsAPI.getAllowedLevel2(activeProperty.id);
        const level2List = level2Response.level_2 || [];
        setCreateAvailableLevel2(level2List);
      } catch (err) {
        console.error('Error loading allowed level_2:', err);
      }
    }
  };

  const handleCreateLevel2Change = async (value: string) => {
    if (value === '__CUSTOM__') {
      setCustomLevel2(true);
      setNewLevel2('');
      setNewLevel3('');
      setCreateAvailableLevel3([]);
      setSimilarLevel2Warning([]);
    } else {
      setCustomLevel2(false);
      setNewLevel2(value);
      setNewLevel3('');
      setCreateAvailableLevel3([]);
      setSimilarLevel2Warning([]);
      
      // Si level_2 existe (même avec un nouveau level_1), charger les level_3 déjà mappés
      if (value) {
        if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
          console.error('[AllowedMappingsTable] Property ID invalide pour getAllowedLevel3ForLevel2');
          return;
        }
        try {
          // Charger les level_3 pour ce level_2 (peu importe le level_1)
          const level3Response = await mappingsAPI.getAllowedLevel3ForLevel2(activeProperty.id, value);
          const level3List = level3Response.level_3 || [];
          setCreateAvailableLevel3(level3List);
        } catch (err) {
          console.error('Error loading allowed level_3:', err);
        }
      }
    }
  };

  const handleCreateLevel2InputChange = (value: string) => {
    setNewLevel2(value);
    
    // Détecter les valeurs similaires
    if (value && value.trim() !== '') {
      const similar = findSimilarValues(value, allowedLevel2List);
      setSimilarLevel2Warning(similar);
    } else {
      setSimilarLevel2Warning([]);
    }
    
    // Si c'est une nouvelle valeur, vider level_3 (on ne peut pas savoir quel level_3 lui associer)
    setNewLevel3('');
    setCreateAvailableLevel3([]);
  };

  const handleCreateLevel3Change = (value: string) => {
    setNewLevel3(value || '');
  };

  const handleCreate = async () => {
    if (!newLevel1 || !newLevel2) {
      alert('Veuillez remplir au moins level_1 et level_2');
      return;
    }

    // Valider level_3
    if (newLevel3 && !ALLOWED_LEVEL_3_VALUES.includes(newLevel3)) {
      alert(`level_3 doit être l'une des valeurs suivantes : ${ALLOWED_LEVEL_3_VALUES.join(', ')}`);
      return;
    }

    try {
      if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
        alert('Aucune propriété sélectionnée');
        return;
      }
      await mappingsAPI.createAllowedMapping(activeProperty.id, newLevel1.trim(), newLevel2.trim(), newLevel3?.trim() || undefined);
      setShowCreateModal(false);
      setNewLevel1('');
      setNewLevel2('');
      setNewLevel3('');
      setCustomLevel1(false);
      setCustomLevel2(false);
      setCreateAvailableLevel2([]);
      setCreateAvailableLevel3([]);
      setSimilarLevel1Warning([]);
      setSimilarLevel2Warning([]);
      loadMappings();
    } catch (err: any) {
      alert(`Erreur lors de la création: ${err.message}`);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce mapping autorisé ?')) {
      return;
    }

    setDeletingId(id);
    try {
      if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
        console.error('[AllowedMappingsTable] Property ID invalide pour deleteAllowedMapping');
        return;
      }
      await mappingsAPI.deleteAllowedMapping(activeProperty.id, id);
      loadMappings();
    } catch (err: any) {
      alert(`Erreur lors de la suppression: ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  const handleReset = async () => {
    if (!confirm('⚠️ Êtes-vous sûr de vouloir réinitialiser les mappings autorisés ?\n\nCette action supprimera toutes les combinaisons ajoutées manuellement et gardera uniquement les 50 combinaisons initiales (hard codées).')) {
      return;
    }

    setIsResetting(true);
    try {
      if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
        console.error('[AllowedMappingsTable] Property ID invalide pour resetAllowedMappings');
        return;
      }
      const result = await mappingsAPI.resetAllowedMappings(activeProperty.id);
      alert(`Reset effectué avec succès :\n- ${result.deleted_allowed} mapping(s) autorisé(s) supprimé(s)\n- ${result.deleted_mappings} mapping(s) invalide(s) supprimé(s)\n- ${result.unassigned_transactions} transaction(s) non assignée(s)`);
      loadMappings();
    } catch (err: any) {
      alert(`Erreur lors du reset: ${err.message}`);
    } finally {
      setIsResetting(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
        ⏳ Chargement des mappings autorisés...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#dc3545' }}>
        ❌ Erreur : {error}
      </div>
    );
  }

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: '600', color: '#1a1a1a', margin: 0 }}>
          Mappings autorisés
        </h2>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={handleReset}
            disabled={isResetting}
            style={{
              padding: '8px 16px',
              fontSize: '14px',
              backgroundColor: isResetting ? '#ccc' : '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: isResetting ? 'not-allowed' : 'pointer',
            }}
          >
            {isResetting ? '⏳ Reset...' : '🔄 Reset mappings autorisés par défaut'}
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            style={{
              padding: '8px 16px',
              fontSize: '14px',
              backgroundColor: '#1e3a5f',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            + Ajouter
          </button>
        </div>
      </div>

      <div style={{ marginBottom: '16px', color: '#666', fontSize: '14px' }}>
        Total : {total} mapping{total !== 1 ? 's' : ''} autorisé{total !== 1 ? 's' : ''}
      </div>

      <table style={{ width: '100%', borderCollapse: 'collapse', backgroundColor: 'white' }}>
        <thead>
          <tr style={{ backgroundColor: '#f3f4f6', borderBottom: '2px solid #e5e5e5' }}>
            <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#1a1a1a' }}>ID</th>
            <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#1a1a1a' }}>Level 1</th>
            <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#1a1a1a' }}>Level 2</th>
            <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#1a1a1a' }}>Level 3</th>
            <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#1a1a1a' }}>Type</th>
            <th style={{ padding: '12px', textAlign: 'center', fontWeight: '600', color: '#1a1a1a' }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {mappings.map((mapping) => (
            <tr
              key={mapping.id}
              style={{
                backgroundColor: mapping.is_hardcoded ? '#f9f9f9' : 'white',
                borderBottom: '1px solid #e5e5e5',
              }}
            >
              <td style={{ padding: '12px', color: '#666' }}>{mapping.id}</td>
              <td style={{ padding: '12px', color: '#666' }}>{mapping.level_1}</td>
              <td style={{ padding: '12px', color: '#666' }}>{mapping.level_2}</td>
              <td style={{ padding: '12px', color: '#666' }}>{mapping.level_3 || '-'}</td>
              <td style={{ padding: '12px', color: '#666' }}>
                {mapping.is_hardcoded ? (
                  <span style={{ color: '#6b7280', fontStyle: 'italic' }}>Hard codé</span>
                ) : (
                  <span style={{ color: '#1e3a5f' }}>Ajouté manuellement</span>
                )}
              </td>
              <td style={{ padding: '12px', textAlign: 'center' }}>
                <button
                  onClick={() => handleDelete(mapping.id)}
                  disabled={mapping.is_hardcoded || deletingId === mapping.id}
                  style={{
                    padding: '4px 8px',
                    fontSize: '12px',
                    backgroundColor: mapping.is_hardcoded ? '#ccc' : '#dc3545',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: mapping.is_hardcoded || deletingId === mapping.id ? 'not-allowed' : 'pointer',
                    opacity: mapping.is_hardcoded || deletingId === mapping.id ? 0.6 : 1,
                  }}
                >
                  {deletingId === mapping.id ? '⏳' : '🗑️'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '12px', marginTop: '24px' }}>
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            style={{
              padding: '8px 16px',
              fontSize: '14px',
              backgroundColor: page === 1 ? '#ccc' : '#1e3a5f',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: page === 1 ? 'not-allowed' : 'pointer',
            }}
          >
            ← Précédent
          </button>
          <span style={{ color: '#666', fontSize: '14px' }}>
            Page {page} sur {totalPages}
          </span>
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            style={{
              padding: '8px 16px',
              fontSize: '14px',
              backgroundColor: page === totalPages ? '#ccc' : '#1e3a5f',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: page === totalPages ? 'not-allowed' : 'pointer',
            }}
          >
            Suivant →
          </button>
        </div>
      )}

      {/* Modal de création */}
      {showCreateModal && (
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
          onClick={() => setShowCreateModal(false)}
        >
          <div
            style={{
              backgroundColor: 'white',
              padding: '24px',
              borderRadius: '8px',
              width: '90%',
              maxWidth: '500px',
              maxHeight: '90vh',
              overflow: 'auto',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '20px', color: '#1a1a1a' }}>
              Ajouter un mapping autorisé
            </h3>
            
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>Level 1 *</label>
              {customLevel1 ? (
                <div>
                  <input
                    type="text"
                    value={newLevel1}
                    onChange={(e) => handleCreateLevel1InputChange(e.target.value)}
                    placeholder="Entrer une nouvelle valeur level_1"
                    style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                  />
                  <button
                    onClick={() => {
                      setCustomLevel1(false);
                      setNewLevel1('');
                      setSimilarLevel1Warning([]);
                    }}
                    style={{
                      marginTop: '4px',
                      padding: '4px 8px',
                      fontSize: '12px',
                      backgroundColor: '#6b7280',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                    }}
                  >
                    ← Retour à la liste
                  </button>
                  {similarLevel1Warning.length > 0 && (
                    <div style={{ marginTop: '8px', padding: '8px', backgroundColor: '#fef3c7', border: '1px solid #fbbf24', borderRadius: '4px', fontSize: '12px', color: '#92400e' }}>
                      ⚠️ Valeurs similaires existantes : {similarLevel1Warning.join(', ')}
                    </div>
                  )}
                </div>
              ) : (
                <select
                  value={newLevel1}
                  onChange={(e) => handleCreateLevel1Change(e.target.value)}
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                >
                  <option value="">-- Sélectionner --</option>
                  {createAvailableLevel1.map((val) => (
                    <option key={val} value={val}>{val}</option>
                  ))}
                  <option value="__CUSTOM__">➕ Nouveau...</option>
                </select>
              )}
            </div>
            
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>Level 2 *</label>
              {customLevel2 ? (
                <div>
                  <input
                    type="text"
                    value={newLevel2}
                    onChange={(e) => handleCreateLevel2InputChange(e.target.value)}
                    placeholder="Entrer une nouvelle valeur level_2"
                    style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                  />
                  <button
                    onClick={() => {
                      setCustomLevel2(false);
                      setNewLevel2('');
                      setNewLevel3('');
                      setCreateAvailableLevel3([]);
                      setSimilarLevel2Warning([]);
                    }}
                    style={{
                      marginTop: '4px',
                      padding: '4px 8px',
                      fontSize: '12px',
                      backgroundColor: '#6b7280',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                    }}
                  >
                    ← Retour à la liste
                  </button>
                  {similarLevel2Warning.length > 0 && (
                    <div style={{ marginTop: '8px', padding: '8px', backgroundColor: '#fef3c7', border: '1px solid #fbbf24', borderRadius: '4px', fontSize: '12px', color: '#92400e' }}>
                      ⚠️ Valeurs similaires existantes : {similarLevel2Warning.join(', ')}
                    </div>
                  )}
                </div>
              ) : (
                <select
                  value={newLevel2}
                  onChange={(e) => handleCreateLevel2Change(e.target.value)}
                  disabled={false}
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                >
                  <option value="">-- Sélectionner --</option>
                  {createAvailableLevel2.map((val) => (
                    <option key={val} value={val}>{val}</option>
                  ))}
                  <option value="__CUSTOM__">➕ Nouveau...</option>
                </select>
              )}
            </div>
            
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>Level 3</label>
              <select
                value={newLevel3}
                onChange={(e) => handleCreateLevel3Change(e.target.value)}
                disabled={!newLevel2 && !customLevel2}
                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
              >
                <option value="">-- Sélectionner (optionnel) --</option>
                {/* Afficher les level_3 déjà mappés pour ce level_2 si level_2 existe, sinon toutes les valeurs autorisées */}
                {(createAvailableLevel3.length > 0 ? createAvailableLevel3 : ALLOWED_LEVEL_3_VALUES).map((val) => (
                  <option key={val} value={val}>{val}</option>
                ))}
              </select>
              <div style={{ marginTop: '4px', fontSize: '12px', color: '#666' }}>
                {createAvailableLevel3.length > 0 
                  ? `Valeurs déjà mappées pour ce level_2 : ${createAvailableLevel3.join(', ')}`
                  : `Valeurs autorisées : ${ALLOWED_LEVEL_3_VALUES.join(', ')}`
                }
              </div>
            </div>
            
            <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
              <button
                onClick={handleCreate}
                style={{
                  flex: 1,
                  padding: '10px 20px',
                  fontSize: '14px',
                  backgroundColor: '#1e3a5f',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                }}
              >
                Créer
              </button>
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setNewLevel1('');
                  setNewLevel2('');
                  setNewLevel3('');
                  setCustomLevel1(false);
                  setCustomLevel2(false);
                  setCreateAvailableLevel2([]);
                  setCreateAvailableLevel3([]);
                  setSimilarLevel1Warning([]);
                  setSimilarLevel2Warning([]);
                }}
                style={{
                  flex: 1,
                  padding: '10px 20px',
                  fontSize: '14px',
                  backgroundColor: '#6b7280',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                }}
              >
                Annuler
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

