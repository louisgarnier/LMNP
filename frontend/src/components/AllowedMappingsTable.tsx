'use client';

import React, { useState, useEffect } from 'react';
import { allowedMappingsAPI, AllowedMapping, AllowedMappingCreate } from '../api/client';

export default function AllowedMappingsTable() {
  const [mappings, setMappings] = useState<AllowedMapping[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [total, setTotal] = useState(0);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [resetting, setResetting] = useState(false);
  
  // États pour le nouveau mapping
  const [newMapping, setNewMapping] = useState<AllowedMappingCreate>({
    level_1: '',
    level_2: '',
    level_3: null,
  });
  
  // États pour les dropdowns filtrés
  const [availableLevel1, setAvailableLevel1] = useState<string[]>([]);
  const [availableLevel2, setAvailableLevel2] = useState<string[]>([]);
  const [availableLevel3, setAvailableLevel3] = useState<string[]>([]);
  
  // États pour le mode "création nouvelle valeur" (Option C: dropdowns + bouton +)
  const [creatingNewLevel1, setCreatingNewLevel1] = useState(false);
  const [creatingNewLevel2, setCreatingNewLevel2] = useState(false);
  const [creatingNewLevel3, setCreatingNewLevel3] = useState(false);
  
  // Filtres
  const [filterLevel1, setFilterLevel1] = useState('');
  const [filterLevel2, setFilterLevel2] = useState('');
  const [filterLevel3, setFilterLevel3] = useState('');

  const loadMappings = async () => {
    setLoading(true);
    setError(null);
    try {
      const skip = (page - 1) * pageSize;
      const filters: { level_1?: string; level_2?: string; level_3?: string } = {};
      if (filterLevel1) filters.level_1 = filterLevel1;
      if (filterLevel2) filters.level_2 = filterLevel2;
      if (filterLevel3) filters.level_3 = filterLevel3;
      
      const response = await allowedMappingsAPI.getAllowedMappings(skip, pageSize, filters);
      setMappings(response.mappings);
      setTotal(response.total);
    } catch (err: any) {
      setError(err.message || 'Erreur lors du chargement des mappings autorisés');
      console.error('Erreur chargement mappings autorisés:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMappings();
  }, [page, pageSize, filterLevel1, filterLevel2, filterLevel3]);

  // Charger les valeurs autorisées quand le modal s'ouvre
  useEffect(() => {
    if (showCreateModal) {
      const loadAllowedValues = async () => {
        try {
          const level1List = await allowedMappingsAPI.getAllowedLevel1();
          setAvailableLevel1(level1List);
          
          const allLevel2List = await allowedMappingsAPI.getAllowedLevel2();
          setAvailableLevel2(allLevel2List);
          
          const allLevel3List = await allowedMappingsAPI.getAllowedLevel3();
          setAvailableLevel3(allLevel3List);
        } catch (err) {
          console.error('❌ Erreur lors du chargement des valeurs autorisées:', err);
        }
      };
      loadAllowedValues();
      // Réinitialiser les états de création
      setCreatingNewLevel1(false);
      setCreatingNewLevel2(false);
      setCreatingNewLevel3(false);
      setNewMapping({
        level_1: '',
        level_2: '',
        level_3: null,
      });
    }
  }, [showCreateModal]);

  // Handlers pour le filtrage hiérarchique dans le modal de création
  const handleCreateLevel1Change = async (value: string) => {
    if (!value) {
      setNewMapping({ ...newMapping, level_1: '', level_2: '', level_3: null });
      const allLevel2List = await allowedMappingsAPI.getAllowedLevel2();
      setAvailableLevel2(allLevel2List);
      const allLevel3List = await allowedMappingsAPI.getAllowedLevel3();
      setAvailableLevel3(allLevel3List);
      return;
    }
    
    try {
      // Scénario 1 : level_1 → level_2 et level_3 sélectionnés automatiquement
      const combination = await allowedMappingsAPI.getUniqueCombinationForLevel1(value);
      if (combination) {
        setNewMapping({
          ...newMapping,
          level_1: value,
          level_2: combination.level_2 || '',
          level_3: combination.level_3 || null,
        });
        // Garder toutes les valeurs disponibles pour permettre le changement
        const allLevel2List = await allowedMappingsAPI.getAllowedLevel2();
        setAvailableLevel2(allLevel2List);
        const allLevel3List = await allowedMappingsAPI.getAllowedLevel3();
        setAvailableLevel3(allLevel3List);
      } else {
        setNewMapping({ ...newMapping, level_1: value });
      }
    } catch (err) {
      console.error('❌ Erreur lors de la sélection de level_1:', err);
      setNewMapping({ ...newMapping, level_1: value });
    }
  };
  
  const handleCreateLevel2Change = async (value: string) => {
    if (!value) {
      setNewMapping({ ...newMapping, level_2: '', level_3: null });
      const allLevel3List = await allowedMappingsAPI.getAllowedLevel3();
      setAvailableLevel3(allLevel3List);
      return;
    }
    
    try {
      // Scénario 2 : level_2 → level_3 sélectionné automatiquement, level_1 filtré
      const combination = await allowedMappingsAPI.getUniqueCombinationForLevel2(value);
      if (combination && combination.level_3) {
        setNewMapping({
          ...newMapping,
          level_2: value,
          level_3: combination.level_3,
        });
      } else {
        setNewMapping({ ...newMapping, level_2: value, level_3: null });
      }
      
      // Filtrer level_1 par level_2
      const level1List = await allowedMappingsAPI.getAllowedLevel1ForLevel2(value);
      setAvailableLevel1(level1List);
      
      // Garder toutes les valeurs level_3 disponibles
      const allLevel3List = await allowedMappingsAPI.getAllowedLevel3();
      setAvailableLevel3(allLevel3List);
    } catch (err) {
      console.error('❌ Erreur lors de la sélection de level_2:', err);
      setNewMapping({ ...newMapping, level_2: value });
    }
  };
  
  const handleCreateLevel3Change = async (value: string) => {
    if (!value) {
      setNewMapping({ ...newMapping, level_3: null });
      const allLevel2List = await allowedMappingsAPI.getAllowedLevel2();
      setAvailableLevel2(allLevel2List);
      const allLevel1List = await allowedMappingsAPI.getAllowedLevel1();
      setAvailableLevel1(allLevel1List);
      return;
    }
    
    try {
      // Scénario 3 : level_3 → level_2 filtré, level_1 filtré
      setNewMapping({ ...newMapping, level_3: value });
      
      // Filtrer level_2 par level_3
      const level2List = await allowedMappingsAPI.getAllowedLevel2ForLevel3(value);
      setAvailableLevel2(level2List);
      
      // Si level_2 existe déjà, filtrer level_1 par le couple (level_2, level_3)
      if (newMapping.level_2) {
        const level1List = await allowedMappingsAPI.getAllowedLevel1ForLevel2AndLevel3(newMapping.level_2, value);
        setAvailableLevel1(level1List);
      } else {
        // Garder toutes les valeurs level_1 disponibles
        const allLevel1List = await allowedMappingsAPI.getAllowedLevel1();
        setAvailableLevel1(allLevel1List);
      }
    } catch (err) {
      console.error('❌ Erreur lors de la sélection de level_3:', err);
      setNewMapping({ ...newMapping, level_3: value });
    }
  };

  const handleCreate = async () => {
    if (!newMapping.level_1 || !newMapping.level_2) {
      alert('Veuillez remplir au moins level_1 et level_2');
      return;
    }

    try {
      await allowedMappingsAPI.createAllowedMapping(newMapping);
      setShowCreateModal(false);
      setNewMapping({
        level_1: '',
        level_2: '',
        level_3: null,
      });
      // Réinitialiser les états de création
      setCreatingNewLevel1(false);
      setCreatingNewLevel2(false);
      setCreatingNewLevel3(false);
      // Réinitialiser les dropdowns
      setAvailableLevel1([]);
      setAvailableLevel2([]);
      setAvailableLevel3([]);
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
      await allowedMappingsAPI.deleteAllowedMapping(id);
      loadMappings();
    } catch (err: any) {
      alert(`Erreur lors de la suppression: ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  const handleReset = async () => {
    if (!confirm(
      '⚠️ Êtes-vous sûr de vouloir réinitialiser les mappings autorisés ?\n\n' +
      'Cette action va :\n' +
      '- Supprimer TOUS les mappings autorisés actuels\n' +
      '- Recharger les mappings depuis le fichier mappings_default.xlsx\n\n' +
      'Cette action est irréversible.'
    )) {
      return;
    }

    setResetting(true);
    try {
      const result = await allowedMappingsAPI.resetAllowedMappings();
      alert(
        `✅ Reset réussi !\n\n` +
        `- ${result.deleted_count} mapping(s) autorisé(s) supprimé(s)\n` +
        `- ${result.inserted_count} mapping(s) chargé(s) depuis Excel\n` +
        `- ${result.error_count} erreur(s)\n` +
        `- ${result.invalid_mappings_deleted} mapping(s) invalide(s) supprimé(s)\n` +
        `- ${result.transactions_reset} transaction(s) réinitialisée(s)\n` +
        `- Total en BDD: ${result.total_count}`
      );
      loadMappings();
    } catch (err: any) {
      alert(`❌ Erreur lors du reset: ${err.message}`);
    } finally {
      setResetting(false);
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  if (loading && mappings.length === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <div>Chargement des mappings autorisés...</div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Header avec recherche et boutons */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span style={{ fontSize: '14px', color: '#666' }}>
            {total} mapping{total !== 1 ? 's' : ''} autorisé{total !== 1 ? 's' : ''}
          </span>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            onClick={handleReset}
            disabled={resetting}
            style={{
              padding: '8px 16px',
              fontSize: '14px',
              backgroundColor: resetting ? '#ccc' : '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: resetting ? 'not-allowed' : 'pointer',
              opacity: resetting ? 0.6 : 1,
            }}
          >
            {resetting ? '⏳ Reset en cours...' : '🔄 Reset mappings autorisés par défaut'}
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
            + Ajouter un mapping autorisé
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: '12px', backgroundColor: '#fee', color: '#c33', borderRadius: '4px' }}>
          {error}
        </div>
      )}

      {/* Tableau */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', backgroundColor: 'white' }}>
          <thead>
            <tr style={{ backgroundColor: '#f5f5f5', borderBottom: '2px solid #ddd' }}>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#1a1a1a' }}>ID</th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#1a1a1a' }}>Level 1</th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#1a1a1a' }}>Level 2</th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#1a1a1a' }}>Level 3</th>
              <th style={{ padding: '12px', textAlign: 'center', fontWeight: '600', color: '#1a1a1a' }}>Actions</th>
            </tr>
            {/* Ligne de filtres */}
            <tr key="filter-row" style={{ backgroundColor: '#fafafa', borderBottom: '1px solid #e5e5e5' }}>
              <td style={{ padding: '8px' }}></td>
              <td style={{ padding: '8px' }}>
                <input
                  type="text"
                  value={filterLevel1}
                  onChange={(e) => {
                    setFilterLevel1(e.target.value);
                    setPage(1);
                  }}
                  placeholder="Filtrer..."
                  style={{
                    width: '100%',
                    padding: '4px 8px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '12px',
                  }}
                />
              </td>
              <td style={{ padding: '8px' }}>
                <input
                  type="text"
                  value={filterLevel2}
                  onChange={(e) => {
                    setFilterLevel2(e.target.value);
                    setPage(1);
                  }}
                  placeholder="Filtrer..."
                  style={{
                    width: '100%',
                    padding: '4px 8px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '12px',
                  }}
                />
              </td>
              <td style={{ padding: '8px' }}>
                <input
                  type="text"
                  value={filterLevel3}
                  onChange={(e) => {
                    setFilterLevel3(e.target.value);
                    setPage(1);
                  }}
                  placeholder="Filtrer..."
                  style={{
                    width: '100%',
                    padding: '4px 8px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '12px',
                  }}
                />
              </td>
              <td style={{ padding: '8px', textAlign: 'center' }}>
                {(filterLevel1 || filterLevel2 || filterLevel3) && (
                  <button
                    onClick={() => {
                      setFilterLevel1('');
                      setFilterLevel2('');
                      setFilterLevel3('');
                      setPage(1);
                    }}
                    style={{
                      padding: '6px 12px',
                      backgroundColor: '#f44336',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '12px',
                      fontWeight: '500',
                    }}
                  >
                    Clear filters
                  </button>
                )}
              </td>
            </tr>
          </thead>
          <tbody>
            {mappings.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
                  Aucun mapping autorisé trouvé
                </td>
              </tr>
            ) : (
              mappings.map((mapping) => (
                <tr 
                  key={mapping.id} 
                  style={{ 
                    borderBottom: '1px solid #eee',
                    backgroundColor: 'white',
                  }}
                >
                  <td style={{ padding: '12px' }}>{mapping.id}</td>
                  <td style={{ padding: '12px' }}>{mapping.level_1}</td>
                  <td style={{ padding: '12px' }}>{mapping.level_2}</td>
                  <td style={{ padding: '12px' }}>{mapping.level_3 || '-'}</td>
                  <td style={{ padding: '12px', textAlign: 'center' }}>
                    <button
                      onClick={() => handleDelete(mapping.id)}
                      disabled={deletingId === mapping.id}
                      style={{
                        padding: '4px 8px',
                        fontSize: '12px',
                        backgroundColor: '#dc3545',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: deletingId === mapping.id ? 'not-allowed' : 'pointer',
                        opacity: deletingId === mapping.id ? 0.6 : 1,
                      }}
                    >
                      {deletingId === mapping.id ? '⏳' : '🗑️'}
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span style={{ fontSize: '14px', color: '#666' }}>Lignes par page:</span>
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(1);
            }}
            style={{
              padding: '6px 12px',
              fontSize: '14px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
            <option value={200}>200</option>
          </select>
        </div>
        {totalPages > 1 && (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              style={{
                padding: '6px 12px',
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
            <span style={{ fontSize: '14px' }}>
              Page {page} sur {totalPages}
            </span>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              style={{
                padding: '6px 12px',
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
      </div>

      {/* Modal création */}
      {showCreateModal && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
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
              maxWidth: '500px',
              width: '90%',
              maxHeight: '90vh',
              overflow: 'auto',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{ marginTop: 0, marginBottom: '20px' }}>Ajouter un mapping autorisé</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>Level 1 *</label>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  {creatingNewLevel1 ? (
                    <input
                      type="text"
                      value={newMapping.level_1}
                      onChange={(e) => setNewMapping({ ...newMapping, level_1: e.target.value })}
                      placeholder="Nouvelle valeur Level 1"
                      style={{ flex: 1, padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                      autoFocus
                    />
                  ) : (
                    <select
                      value={newMapping.level_1}
                      onChange={(e) => handleCreateLevel1Change(e.target.value)}
                      style={{ flex: 1, padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                    >
                      <option value="">Sélectionner...</option>
                      {availableLevel1.map((val) => (
                        <option key={val} value={val}>{val}</option>
                      ))}
                    </select>
                  )}
                  <button
                    type="button"
                    onClick={() => {
                      if (creatingNewLevel1) {
                        setCreatingNewLevel1(false);
                        setNewMapping({ ...newMapping, level_1: '' });
                      } else {
                        setCreatingNewLevel1(true);
                        setNewMapping({ ...newMapping, level_1: '' });
                      }
                    }}
                    style={{
                      padding: '8px 12px',
                      fontSize: '14px',
                      backgroundColor: creatingNewLevel1 ? '#6c757d' : '#28a745',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {creatingNewLevel1 ? '✕' : '+'}
                  </button>
                </div>
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>Level 2 *</label>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  {creatingNewLevel2 ? (
                    <input
                      type="text"
                      value={newMapping.level_2}
                      onChange={(e) => setNewMapping({ ...newMapping, level_2: e.target.value })}
                      placeholder="Nouvelle valeur Level 2"
                      style={{ flex: 1, padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                      autoFocus
                    />
                  ) : (
                    <select
                      value={newMapping.level_2}
                      onChange={(e) => handleCreateLevel2Change(e.target.value)}
                      style={{ flex: 1, padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                    >
                      <option value="">Sélectionner...</option>
                      {availableLevel2.map((val) => (
                        <option key={val} value={val}>{val}</option>
                      ))}
                    </select>
                  )}
                  <button
                    type="button"
                    onClick={() => {
                      if (creatingNewLevel2) {
                        setCreatingNewLevel2(false);
                        setNewMapping({ ...newMapping, level_2: '' });
                      } else {
                        setCreatingNewLevel2(true);
                        setNewMapping({ ...newMapping, level_2: '' });
                      }
                    }}
                    style={{
                      padding: '8px 12px',
                      fontSize: '14px',
                      backgroundColor: creatingNewLevel2 ? '#6c757d' : '#28a745',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {creatingNewLevel2 ? '✕' : '+'}
                  </button>
                </div>
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>Level 3</label>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  {creatingNewLevel3 ? (
                    <input
                      type="text"
                      value={newMapping.level_3 || ''}
                      onChange={(e) => setNewMapping({ ...newMapping, level_3: e.target.value || null })}
                      placeholder="Nouvelle valeur Level 3 (optionnel)"
                      style={{ flex: 1, padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                      autoFocus
                    />
                  ) : (
                    <select
                      value={newMapping.level_3 || ''}
                      onChange={(e) => handleCreateLevel3Change(e.target.value || null)}
                      style={{ flex: 1, padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                    >
                      <option value="">Aucun (optionnel)</option>
                      {availableLevel3.map((val) => (
                        <option key={val} value={val}>{val}</option>
                      ))}
                    </select>
                  )}
                  <button
                    type="button"
                    onClick={() => {
                      if (creatingNewLevel3) {
                        setCreatingNewLevel3(false);
                        setNewMapping({ ...newMapping, level_3: null });
                      } else {
                        setCreatingNewLevel3(true);
                        setNewMapping({ ...newMapping, level_3: '' });
                      }
                    }}
                    style={{
                      padding: '8px 12px',
                      fontSize: '14px',
                      backgroundColor: creatingNewLevel3 ? '#6c757d' : '#28a745',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {creatingNewLevel3 ? '✕' : '+'}
                  </button>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '12px', marginTop: '8px' }}>
                <button
                  onClick={handleCreate}
                  style={{
                    padding: '10px 20px',
                    fontSize: '14px',
                    backgroundColor: '#1e3a5f',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    flex: 1,
                  }}
                >
                  Créer
                </button>
                <button
                  onClick={() => setShowCreateModal(false)}
                  style={{
                    padding: '10px 20px',
                    fontSize: '14px',
                    backgroundColor: '#6c757d',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    flex: 1,
                  }}
                >
                  Annuler
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

