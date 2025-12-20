'use client';

import React, { useState, useEffect } from 'react';
import { mappingsAPI, Mapping, MappingCreate, MappingUpdate } from '../api/client';

interface MappingTableProps {
  onMappingChange?: () => void;
}

export default function MappingTable({ onMappingChange }: MappingTableProps) {
  const [mappings, setMappings] = useState<Mapping[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [isDeletingMultiple, setIsDeletingMultiple] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newMapping, setNewMapping] = useState<MappingCreate>({
    nom: '',
    level_1: '',
    level_2: '',
    level_3: '',
    is_prefix_match: true,
    priority: 0,
  });

  const loadMappings = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await mappingsAPI.list((page - 1) * pageSize, pageSize, search || undefined);
      setMappings(response.mappings);
      setTotal(response.total);
      
      // Réinitialiser la sélection si les mappings chargés ne contiennent plus les IDs sélectionnés
      setSelectedIds(prev => {
        const loadedIds = new Set(response.mappings.map(m => m.id));
        const newSet = new Set<number>();
        prev.forEach(id => {
          if (loadedIds.has(id)) {
            newSet.add(id);
          }
        });
        return newSet;
      });
    } catch (err: any) {
      setError(err.message || 'Erreur lors du chargement des mappings');
      console.error('Erreur chargement mappings:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMappings();
  }, [page, pageSize, search]);

  const handleCreate = async () => {
    if (!newMapping.nom || !newMapping.level_1 || !newMapping.level_2) {
      alert('Veuillez remplir au moins le nom, level_1 et level_2');
      return;
    }

    try {
      await mappingsAPI.create(newMapping);
      setShowCreateModal(false);
      setNewMapping({
        nom: '',
        level_1: '',
        level_2: '',
        level_3: '',
        is_prefix_match: true,
        priority: 0,
      });
      loadMappings();
      onMappingChange?.();
    } catch (err: any) {
      alert(`Erreur lors de la création: ${err.message}`);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce mapping ?')) {
      return;
    }

    setDeletingId(id);
    try {
      await mappingsAPI.delete(id);
      loadMappings();
      onMappingChange?.();
    } catch (err: any) {
      alert(`Erreur lors de la suppression: ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  const handleToggleSelect = (id: number) => {
    setSelectedIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    if (selectedIds.size === mappings.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(mappings.map(m => m.id)));
    }
  };

  const handleDeleteMultiple = async () => {
    if (selectedIds.size === 0) return;
    
    if (!confirm(`Êtes-vous sûr de vouloir supprimer ${selectedIds.size} mapping${selectedIds.size > 1 ? 's' : ''} ?`)) {
      return;
    }

    setIsDeletingMultiple(true);
    try {
      const idsToDelete = Array.from(selectedIds);
      for (const id of idsToDelete) {
        await mappingsAPI.delete(id);
      }
      setSelectedIds(new Set());
      loadMappings();
      onMappingChange?.();
    } catch (err: any) {
      alert(`Erreur lors de la suppression: ${err.message}`);
    } finally {
      setIsDeletingMultiple(false);
    }
  };

  const handleEdit = (mapping: Mapping) => {
    setEditingId(mapping.id);
  };

  const handleSaveEdit = async (mapping: Mapping, updates: MappingUpdate) => {
    try {
      await mappingsAPI.update(mapping.id, updates);
      setEditingId(null);
      loadMappings();
      onMappingChange?.();
    } catch (err: any) {
      // Si le mapping n'existe plus (404), rafraîchir la liste
      if (err.message && err.message.includes('non trouvé')) {
        console.warn(`Mapping avec ID ${mapping.id} non trouvé, rafraîchissement de la liste...`);
        loadMappings();
        setEditingId(null);
        alert(`Le mapping n'existe plus. La liste a été rafraîchie.`);
      } else {
        alert(`Erreur lors de la modification: ${err.message}`);
      }
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  if (loading && mappings.length === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <div>Chargement des mappings...</div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Header avec recherche et bouton créer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, display: 'flex', gap: '8px', alignItems: 'center' }}>
          <input
            type="text"
            placeholder="Rechercher un mapping..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            style={{
              padding: '8px 12px',
              fontSize: '14px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              flex: 1,
              maxWidth: '400px',
            }}
          />
          <span style={{ fontSize: '14px', color: '#666' }}>
            {total} mapping{total !== 1 ? 's' : ''}
          </span>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          {selectedIds.size > 0 && (
            <>
              <span style={{ fontSize: '14px', color: '#1e3a5f', fontWeight: '500' }}>
                {selectedIds.size} mapping{selectedIds.size > 1 ? 's' : ''} sélectionné{selectedIds.size > 1 ? 's' : ''}
              </span>
              <button
                onClick={handleDeleteMultiple}
                disabled={isDeletingMultiple}
                style={{
                  padding: '8px 16px',
                  fontSize: '14px',
                  backgroundColor: isDeletingMultiple ? '#ccc' : '#dc3545',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: isDeletingMultiple ? 'not-allowed' : 'pointer',
                  opacity: isDeletingMultiple ? 0.6 : 1,
                }}
              >
                {isDeletingMultiple ? '⏳ Suppression...' : `🗑️ Supprimer ${selectedIds.size}`}
              </button>
            </>
          )}
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
            + Créer un mapping
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: '12px', backgroundColor: '#fee', color: '#c33', borderRadius: '4px' }}>
          ❌ {error}
        </div>
      )}

      {/* Tableau */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', backgroundColor: 'white' }}>
          <thead>
            <tr style={{ backgroundColor: '#f5f5f5', borderBottom: '2px solid #ddd' }}>
              <th style={{ padding: '12px', textAlign: 'center', fontWeight: '600', width: '50px' }}>
                <input
                  type="checkbox"
                  checked={mappings.length > 0 && selectedIds.size === mappings.length}
                  onChange={handleSelectAll}
                  style={{
                    width: '18px',
                    height: '18px',
                    cursor: 'pointer',
                  }}
                />
              </th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>ID</th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Nom</th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Level 1</th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Level 2</th>
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Level 3</th>
              <th style={{ padding: '12px', textAlign: 'center', fontWeight: '600' }}>Préfixe</th>
              <th style={{ padding: '12px', textAlign: 'center', fontWeight: '600' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {mappings.map((mapping) => (
              <tr 
                key={mapping.id} 
                style={{ 
                  borderBottom: '1px solid #eee',
                  backgroundColor: selectedIds.has(mapping.id) ? '#e3f2fd' : 'white',
                }}
              >
                <td style={{ padding: '12px', textAlign: 'center' }}>
                  <input
                    type="checkbox"
                    checked={selectedIds.has(mapping.id)}
                    onChange={() => handleToggleSelect(mapping.id)}
                    style={{
                      width: '18px',
                      height: '18px',
                      cursor: 'pointer',
                    }}
                  />
                </td>
                <td style={{ padding: '12px' }}>{mapping.id}</td>
                <td style={{ padding: '12px', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {editingId === mapping.id ? (
                    <input
                      type="text"
                      defaultValue={mapping.nom}
                      onBlur={(e) => {
                        if (e.target.value !== mapping.nom) {
                          handleSaveEdit(mapping, { nom: e.target.value });
                        }
                      }}
                      style={{ width: '100%', padding: '4px', border: '1px solid #ddd', borderRadius: '2px' }}
                    />
                  ) : (
                    mapping.nom
                  )}
                </td>
                <td style={{ padding: '12px' }}>
                  {editingId === mapping.id ? (
                    <input
                      type="text"
                      defaultValue={mapping.level_1}
                      onBlur={(e) => {
                        if (e.target.value !== mapping.level_1) {
                          handleSaveEdit(mapping, { level_1: e.target.value });
                        }
                      }}
                      style={{ width: '100%', padding: '4px', border: '1px solid #ddd', borderRadius: '2px' }}
                    />
                  ) : (
                    mapping.level_1
                  )}
                </td>
                <td style={{ padding: '12px' }}>
                  {editingId === mapping.id ? (
                    <input
                      type="text"
                      defaultValue={mapping.level_2}
                      onBlur={(e) => {
                        if (e.target.value !== mapping.level_2) {
                          handleSaveEdit(mapping, { level_2: e.target.value });
                        }
                      }}
                      style={{ width: '100%', padding: '4px', border: '1px solid #ddd', borderRadius: '2px' }}
                    />
                  ) : (
                    mapping.level_2
                  )}
                </td>
                <td style={{ padding: '12px' }}>
                  {editingId === mapping.id ? (
                    <input
                      type="text"
                      defaultValue={mapping.level_3 || ''}
                      onBlur={(e) => {
                        if (e.target.value !== (mapping.level_3 || '')) {
                          handleSaveEdit(mapping, { level_3: e.target.value || undefined });
                        }
                      }}
                      style={{ width: '100%', padding: '4px', border: '1px solid #ddd', borderRadius: '2px' }}
                    />
                  ) : (
                    mapping.level_3 || '-'
                  )}
                </td>
                <td style={{ padding: '12px', textAlign: 'center' }}>
                  {mapping.is_prefix_match ? '✓' : '✗'}
                </td>
                <td style={{ padding: '12px', textAlign: 'center', display: 'flex', gap: '8px', justifyContent: 'center' }}>
                  {editingId === mapping.id ? (
                    <button
                      onClick={() => setEditingId(null)}
                      style={{
                        padding: '4px 8px',
                        fontSize: '12px',
                        backgroundColor: '#28a745',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                      }}
                    >
                      ✓
                    </button>
                  ) : (
                    <>
                      <button
                        onClick={() => handleEdit(mapping)}
                        style={{
                          padding: '4px 8px',
                          fontSize: '12px',
                          backgroundColor: '#007bff',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                        }}
                      >
                        ✏️
                      </button>
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
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label style={{ fontSize: '14px', color: '#666' }}>
            Par page:
          </label>
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(1); // Reset to first page when changing page size
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
              maxWidth: '500px',
              width: '90%',
              maxHeight: '90vh',
              overflow: 'auto',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{ marginTop: 0, marginBottom: '20px' }}>Créer un nouveau mapping</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>Nom *</label>
                <input
                  type="text"
                  value={newMapping.nom}
                  onChange={(e) => setNewMapping({ ...newMapping, nom: e.target.value })}
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>Level 1 *</label>
                <input
                  type="text"
                  value={newMapping.level_1}
                  onChange={(e) => setNewMapping({ ...newMapping, level_1: e.target.value })}
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>Level 2 *</label>
                <input
                  type="text"
                  value={newMapping.level_2}
                  onChange={(e) => setNewMapping({ ...newMapping, level_2: e.target.value })}
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>Level 3</label>
                <input
                  type="text"
                  value={newMapping.level_3 || ''}
                  onChange={(e) => setNewMapping({ ...newMapping, level_3: e.target.value })}
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                />
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

