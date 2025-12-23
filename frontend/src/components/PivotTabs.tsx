/**
 * PivotTabs component - Gestion des sous-onglets pour tableaux croisés (style Chrome)
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { PivotFieldConfig } from './PivotFieldSelector';

export interface PivotTab {
  id: string; // 'new' pour nouvel onglet, ou ID du config sauvegardé
  name: string;
  config: PivotFieldConfig;
  isSaved: boolean; // Si true, c'est un config sauvegardé dans la BDD
  createdAt?: string; // Date de création (pour le tri)
}

interface PivotTabsProps {
  tabs: PivotTab[];
  activeTabId: string;
  onTabChange: (tabId: string) => void;
  onTabCreate: () => void;
  onTabRename: (tabId: string, newName: string) => void;
  onTabDelete: (tabId: string) => void;
  onTabMove: (tabId: string, direction: 'left' | 'right') => void;
}

export default function PivotTabs({
  tabs,
  activeTabId,
  onTabChange,
  onTabCreate,
  onTabRename,
  onTabDelete,
  onTabMove,
}: PivotTabsProps) {
  const [editingTabId, setEditingTabId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState<string>('');
  const [contextMenu, setContextMenu] = useState<{ tabId: string; x: number; y: number } | null>(null);
  const [deleteConfirmTabId, setDeleteConfirmTabId] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus sur l'input quand on commence à éditer
  useEffect(() => {
    if (editingTabId && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editingTabId]);

  // Fermer le menu contextuel au clic ailleurs
  useEffect(() => {
    const handleClickOutside = () => {
      if (contextMenu) {
        setContextMenu(null);
      }
    };

    if (contextMenu) {
      document.addEventListener('click', handleClickOutside);
      return () => {
        document.removeEventListener('click', handleClickOutside);
      };
    }
  }, [contextMenu]);

  const handleDoubleClick = (tabId: string, currentName: string) => {
    setEditingTabId(tabId);
    setEditingName(currentName);
  };

  const handleRenameSubmit = (tabId: string) => {
    if (editingName.trim() && editingName.trim() !== tabs.find(t => t.id === tabId)?.name) {
      onTabRename(tabId, editingName.trim());
    }
    setEditingTabId(null);
    setEditingName('');
  };

  const handleRenameCancel = () => {
    setEditingTabId(null);
    setEditingName('');
  };

  const handleContextMenu = (e: React.MouseEvent, tabId: string) => {
    e.preventDefault();
    e.stopPropagation();
    setContextMenu({
      tabId,
      x: e.clientX,
      y: e.clientY,
    });
  };

  const handleMove = (tabId: string, direction: 'left' | 'right') => {
    onTabMove(tabId, direction);
    setContextMenu(null);
  };

  const handleDelete = (tabId: string) => {
    setDeleteConfirmTabId(tabId);
    setContextMenu(null);
  };

  const confirmDelete = () => {
    if (deleteConfirmTabId) {
      onTabDelete(deleteConfirmTabId);
      setDeleteConfirmTabId(null);
    }
  };

  const cancelDelete = () => {
    setDeleteConfirmTabId(null);
  };

  const activeTabIndex = tabs.findIndex(t => t.id === activeTabId);
  const canMoveLeft = activeTabIndex > 0;
  const canMoveRight = activeTabIndex < tabs.length - 1;

  return (
    <>
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-end',
          backgroundColor: '#f1f5f9',
          borderBottom: '1px solid #cbd5e1',
          padding: '0 8px',
          gap: '2px',
          overflowX: 'auto',
          overflowY: 'hidden',
        }}
      >
        {tabs.map((tab, index) => {
          const isActive = tab.id === activeTabId;
          const isEditing = editingTabId === tab.id;

          return (
            <div
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              onDoubleClick={() => handleDoubleClick(tab.id, tab.name)}
              onContextMenu={(e) => handleContextMenu(e, tab.id)}
              style={{
                position: 'relative',
                padding: '8px 16px',
                backgroundColor: isActive ? '#ffffff' : '#e2e8f0',
                border: '1px solid',
                borderColor: isActive ? '#cbd5e1' : 'transparent',
                borderBottom: isActive ? '1px solid transparent' : '1px solid #cbd5e1',
                borderTopLeftRadius: '8px',
                borderTopRightRadius: '8px',
                cursor: 'pointer',
                fontSize: '13px',
                color: isActive ? '#1e293b' : '#64748b',
                fontWeight: isActive ? '500' : '400',
                minWidth: '120px',
                maxWidth: '200px',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                userSelect: 'none',
                transition: 'all 0.15s',
                marginTop: isActive ? '0' : '2px',
                zIndex: isActive ? 10 : 1,
              }}
              title={tab.name}
            >
              {isEditing ? (
                <input
                  ref={inputRef}
                  type="text"
                  value={editingName}
                  onChange={(e) => setEditingName(e.target.value)}
                  onBlur={() => handleRenameSubmit(tab.id)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleRenameSubmit(tab.id);
                    } else if (e.key === 'Escape') {
                      handleRenameCancel();
                    }
                  }}
                  onClick={(e) => e.stopPropagation()}
                  style={{
                    width: '100%',
                    padding: '2px 4px',
                    fontSize: '13px',
                    border: '1px solid #3b82f6',
                    borderRadius: '4px',
                    outline: 'none',
                  }}
                />
              ) : (
                <span>{tab.name}</span>
              )}
              {isActive && !isEditing && (
                <span
                  style={{
                    position: 'absolute',
                    right: '4px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    fontSize: '10px',
                    color: '#64748b',
                    cursor: 'pointer',
                    padding: '2px',
                  }}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(tab.id);
                  }}
                  title="Fermer"
                >
                  ×
                </span>
              )}
            </div>
          );
        })}

        {/* Bouton "+" pour créer un nouvel onglet */}
        <button
          onClick={onTabCreate}
          style={{
            padding: '8px 12px',
            backgroundColor: '#e2e8f0',
            border: '1px solid transparent',
            borderBottom: '1px solid #cbd5e1',
            borderTopLeftRadius: '8px',
            borderTopRightRadius: '8px',
            cursor: 'pointer',
            fontSize: '16px',
            color: '#64748b',
            marginTop: '2px',
            transition: 'all 0.15s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#cbd5e1';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = '#e2e8f0';
          }}
          title="Nouvel onglet"
        >
          +
        </button>
      </div>

      {/* Menu contextuel */}
      {contextMenu && (
        <div
          style={{
            position: 'fixed',
            top: contextMenu.y,
            left: contextMenu.x,
            backgroundColor: '#ffffff',
            border: '1px solid #d1d5db',
            borderRadius: '4px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            zIndex: 1000,
            minWidth: '150px',
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={() => handleMove(contextMenu.tabId, 'left')}
            disabled={tabs.findIndex(t => t.id === contextMenu.tabId) === 0}
            style={{
              width: '100%',
              padding: '8px 12px',
              textAlign: 'left',
              border: 'none',
              backgroundColor: 'transparent',
              cursor: tabs.findIndex(t => t.id === contextMenu.tabId) === 0 ? 'not-allowed' : 'pointer',
              fontSize: '14px',
              color: tabs.findIndex(t => t.id === contextMenu.tabId) === 0 ? '#9ca3af' : '#1f2937',
            }}
            onMouseEnter={(e) => {
              if (tabs.findIndex(t => t.id === contextMenu.tabId) > 0) {
                e.currentTarget.style.backgroundColor = '#f3f4f6';
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
            }}
          >
            Déplacer à gauche
          </button>
          <button
            onClick={() => handleMove(contextMenu.tabId, 'right')}
            disabled={tabs.findIndex(t => t.id === contextMenu.tabId) === tabs.length - 1}
            style={{
              width: '100%',
              padding: '8px 12px',
              textAlign: 'left',
              border: 'none',
              backgroundColor: 'transparent',
              cursor: tabs.findIndex(t => t.id === contextMenu.tabId) === tabs.length - 1 ? 'not-allowed' : 'pointer',
              fontSize: '14px',
              color: tabs.findIndex(t => t.id === contextMenu.tabId) === tabs.length - 1 ? '#9ca3af' : '#1f2937',
              borderTop: '1px solid #e5e7eb',
            }}
            onMouseEnter={(e) => {
              if (tabs.findIndex(t => t.id === contextMenu.tabId) < tabs.length - 1) {
                e.currentTarget.style.backgroundColor = '#f3f4f6';
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
            }}
          >
            Déplacer à droite
          </button>
          <div style={{ height: '1px', backgroundColor: '#e5e7eb', margin: '4px 0' }} />
          <button
            onClick={() => handleDelete(contextMenu.tabId)}
            style={{
              width: '100%',
              padding: '8px 12px',
              textAlign: 'left',
              border: 'none',
              backgroundColor: 'transparent',
              cursor: 'pointer',
              fontSize: '14px',
              color: '#ef4444',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#fef2f2';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
            }}
          >
            Supprimer
          </button>
        </div>
      )}

      {/* Confirmation de suppression */}
      {deleteConfirmTabId && (
        <div
          style={{
            position: 'fixed',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            backgroundColor: '#ffffff',
            border: '1px solid #d1d5db',
            borderRadius: '8px',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
            zIndex: 2000,
            padding: '24px',
            minWidth: '300px',
          }}
        >
          <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', fontWeight: '600', color: '#1f2937' }}>
            Confirmer la suppression
          </h3>
          <p style={{ margin: '0 0 20px 0', fontSize: '14px', color: '#6b7280' }}>
            Êtes-vous sûr de vouloir supprimer l'onglet "{tabs.find(t => t.id === deleteConfirmTabId)?.name}" ?
            {tabs.find(t => t.id === deleteConfirmTabId)?.isSaved && (
              <span style={{ display: 'block', marginTop: '8px', fontSize: '12px', color: '#ef4444' }}>
                Cette action supprimera également la sauvegarde dans la base de données.
              </span>
            )}
          </p>
          <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
            <button
              onClick={cancelDelete}
              style={{
                padding: '8px 16px',
                fontSize: '14px',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                backgroundColor: '#f9fafb',
                color: '#374151',
                cursor: 'pointer',
              }}
            >
              Annuler
            </button>
            <button
              onClick={confirmDelete}
              style={{
                padding: '8px 16px',
                fontSize: '14px',
                border: 'none',
                borderRadius: '4px',
                backgroundColor: '#ef4444',
                color: '#ffffff',
                cursor: 'pointer',
              }}
            >
              Supprimer
            </button>
          </div>
        </div>
      )}
    </>
  );
}

