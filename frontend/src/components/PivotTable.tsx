/**
 * PivotTable component - Affichage du tableau croisé format Excel avec hiérarchie
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect, useMemo } from 'react';
import React from 'react';
import { analyticsAPI, PivotData } from '@/api/client';
import { PivotFieldConfig } from './PivotFieldSelector';

interface PivotTableProps {
  config: PivotFieldConfig;
  onCellClick?: (rowValues: (string | number)[], columnValues: (string | number)[]) => void;
}

interface PivotRow {
  key: string | number | (string | number)[];
  label: string;
  level: number;
  children?: PivotRow[];
  values: Record<string, number>;
  total: number;
  hasChildren: boolean;
}

export default function PivotTable({ config, onCellClick }: PivotTableProps) {
  const [pivotData, setPivotData] = useState<PivotData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; rowKey: string | number | (string | number)[]; rowLevel: number } | null>(null);

  // Appeler l'API quand la config change
  useEffect(() => {
    const loadPivotData = async () => {
      // Ne pas charger si pas de lignes ou colonnes
      if (config.rows.length === 0 && config.columns.length === 0) {
        setPivotData(null);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const data = await analyticsAPI.getPivot(
          config.rows.length > 0 ? config.rows : undefined,
          config.columns.length > 0 ? config.columns : undefined,
          'quantite',
          'sum',
          config.filters
        );
        console.log('Pivot data reçue:', data);
        console.log('Pivot data reçue:', data);
        console.log('Rows:', data.rows);
        console.log('Columns:', data.columns);
        console.log('Data:', data.data);
        console.log('Row totals:', data.row_totals);
        setPivotData(data);
        // Expand tout par défaut
        if (data.rows) {
          const allKeys = data.rows.map(r => {
            if (Array.isArray(r)) {
              return JSON.stringify(r);
            }
            return String(r);
          });
          setExpandedRows(new Set(allKeys));
        }
      } catch (err: any) {
        setError(err.message || 'Erreur lors du chargement des données');
        console.error('Erreur pivot:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadPivotData();
  }, [config]);

  // Convertir les clés en strings pour l'affichage
  const formatKey = (key: string | number | (string | number)[]): string => {
    if (Array.isArray(key)) {
      return key[key.length - 1]?.toString() || 'N/A'; // Afficher seulement le dernier niveau
    }
    if (key === null || key === undefined) {
      return 'N/A';
    }
    return String(key);
  };

  // Convertir une clé en string pour les accès aux données
  // Le backend utilise str(list(key)) qui donne "['val1', 'val2']" (guillemets simples)
  // On doit utiliser le même format pour accéder aux données
  const keyToString = (key: string | number | (string | number)[]): string => {
    if (Array.isArray(key)) {
      // Utiliser le même format que le backend: str(list(key))
      return `[${key.map(k => typeof k === 'string' ? `'${k}'` : String(k)).join(', ')}]`;
    }
    if (key === null || key === undefined) {
      return 'None';
    }
    return String(key);
  };

  // Construire la structure hiérarchique des lignes
  const hierarchicalRows = useMemo(() => {
    if (!pivotData) return [];

    const rows = pivotData.rows || [];
    const data = pivotData.data || {};
    const rowTotals = pivotData.row_totals || {};
    const rowFields = pivotData.row_fields || [];

    // Si un seul champ en lignes, structure simple
    if (rowFields.length === 1) {
      return rows.map(row => {
        const rowKey = row;
        const rowKeyStr = keyToString(rowKey);
        return {
          key: rowKey,
          label: formatKey(rowKey),
          level: 0,
          values: data[rowKeyStr] || {},
          total: rowTotals[rowKeyStr] || 0,
          hasChildren: false,
        };
      });
    }

    // Si plusieurs champs, construire la hiérarchie
    // Le backend retourne des arrays comme ["CHARGES", "Énergie"] pour level_1, level_2
    const hierarchyMap = new Map<string, PivotRow>();

    rows.forEach(row => {
      if (Array.isArray(row) && row.length > 0) {
        const fullKey = JSON.stringify(row);
        const rowKeyStr = keyToString(row);
        const nodeData = data[rowKeyStr] || {};
        const nodeTotal = rowTotals[rowKeyStr] || 0;

        // Construire la hiérarchie niveau par niveau
        for (let level = 0; level < row.length; level++) {
          const path = row.slice(0, level + 1);
          const pathKey = JSON.stringify(path);
          const isLeaf = level === row.length - 1;

          if (!hierarchyMap.has(pathKey)) {
            const node: PivotRow = {
              key: path,
              label: String(row[level]),
              level: level,
              children: [],
              values: isLeaf ? nodeData : {},
              total: isLeaf ? nodeTotal : 0,
              hasChildren: !isLeaf,
            };

            hierarchyMap.set(pathKey, node);

            // Ajouter au parent si existe
            if (level > 0) {
              const parentPath = row.slice(0, level);
              const parentKey = JSON.stringify(parentPath);
              const parent = hierarchyMap.get(parentKey);
              if (parent && parent.children) {
                // Vérifier si l'enfant n'existe pas déjà
                const exists = parent.children.some(c => JSON.stringify(c.key) === pathKey);
                if (!exists) {
                  parent.children.push(node);
                }
              }
            }
          } else if (isLeaf) {
            // Mettre à jour les données de la feuille
            const node = hierarchyMap.get(pathKey);
            if (node) {
              node.values = nodeData;
              node.total = nodeTotal;
            }
          }
        }

        // Accumuler les totaux vers les parents après avoir créé tous les nœuds
        for (let level = row.length - 1; level > 0; level--) {
          const path = row.slice(0, level + 1);
          const pathKey = JSON.stringify(path);
          const node = hierarchyMap.get(pathKey);
          
          if (node && level === row.length - 1) {
            // C'est une feuille, remonter les totaux
            for (let pLevel = level - 1; pLevel >= 0; pLevel--) {
              const parentPath = row.slice(0, pLevel + 1);
              const parentKey = JSON.stringify(parentPath);
              const parent = hierarchyMap.get(parentKey);
              if (parent) {
                parent.total += node.total;
                Object.keys(node.values).forEach(colKey => {
                  parent.values[colKey] = (parent.values[colKey] || 0) + (node.values[colKey] || 0);
                });
              }
            }
          }
        }
      } else {
        // Ligne simple (non-array)
        const rowKeyStr = keyToString(row);
        hierarchyMap.set(String(row), {
          key: row,
          label: formatKey(row),
          level: 0,
          values: data[rowKeyStr] || {},
          total: rowTotals[rowKeyStr] || 0,
          hasChildren: false,
        });
      }
    });

    // Retourner seulement les nœuds racine (level 0)
    return Array.from(hierarchyMap.values()).filter(node => node.level === 0);
  }, [pivotData]);

  // Helper pour trouver un nœud dans la hiérarchie
  const findInHierarchy = (nodes: PivotRow[], path: (string | number)[]): PivotRow | null => {
    for (const node of nodes) {
      const nodePath = Array.isArray(node.key) ? node.key : [node.key];
      if (JSON.stringify(nodePath) === JSON.stringify(path)) {
        return node;
      }
      if (node.children) {
        const found = findInHierarchy(node.children, path);
        if (found) return found;
      }
    }
    return null;
  };

  // Toggle expand/collapse
  const toggleExpand = (key: string | number | (string | number)[]) => {
    const keyStr = keyToString(key);
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(keyStr)) {
      newExpanded.delete(keyStr);
    } else {
      newExpanded.add(keyStr);
    }
    setExpandedRows(newExpanded);
  };

  // Collecter récursivement toutes les clés des enfants d'un nœud
  const collectAllChildKeys = (row: PivotRow): string[] => {
    const keys: string[] = [keyToString(row.key)];
    if (row.children) {
      row.children.forEach(child => {
        keys.push(...collectAllChildKeys(child));
      });
    }
    return keys;
  };

  // Expand élément unique : expand cet élément seulement
  const expandElement = (rowKey: string | number | (string | number)[]) => {
    const keyStr = keyToString(rowKey);
    const newExpanded = new Set(expandedRows);
    newExpanded.add(keyStr);
    setExpandedRows(newExpanded);
    setContextMenu(null);
  };

  // Collapse élément unique : collapse cet élément seulement
  const collapseElement = (rowKey: string | number | (string | number)[]) => {
    const keyStr = keyToString(rowKey);
    const newExpanded = new Set(expandedRows);
    newExpanded.delete(keyStr);
    setExpandedRows(newExpanded);
    setContextMenu(null);
  };

  // Collecter toutes les clés d'un niveau spécifique dans tout le tableau
  const collectAllKeysAtLevel = (targetLevel: number, nodes: PivotRow[]): string[] => {
    const keys: string[] = [];
    nodes.forEach(node => {
      if (node.level === targetLevel) {
        keys.push(keyToString(node.key));
      }
      if (node.children) {
        keys.push(...collectAllKeysAtLevel(targetLevel, node.children));
      }
    });
    return keys;
  };

  // Expand Entire Field : développer tous les éléments du même champ (même level)
  const expandEntireField = (targetLevel: number) => {
    const allKeys = collectAllKeysAtLevel(targetLevel, hierarchicalRows);
    const newExpanded = new Set(expandedRows);
    allKeys.forEach(key => newExpanded.add(key));
    setExpandedRows(newExpanded);
    setContextMenu(null);
  };

  // Collapse Entire Field : réduire tous les éléments du même champ (même level)
  const collapseEntireField = (targetLevel: number) => {
    const allKeys = collectAllKeysAtLevel(targetLevel, hierarchicalRows);
    const newExpanded = new Set(expandedRows);
    allKeys.forEach(key => newExpanded.delete(key));
    setExpandedRows(newExpanded);
    setContextMenu(null);
  };

  // Navigation par niveaux : Collapse to level X (masquer tous les niveaux > X)
  // targetLevel est le niveau Excel (1-indexed), donc level 1 = niveau 0 dans mon code
  const collapseToLevel = (targetExcelLevel: number) => {
    const targetCodeLevel = targetExcelLevel - 1; // Convertir Excel Level (1-indexed) → Code level (0-indexed)
    const newExpanded = new Set<string>();
    // Garder seulement les clés des niveaux < targetCodeLevel (pour voir jusqu'à targetCodeLevel)
    const collectKeysUpToLevel = (nodes: PivotRow[], maxLevel: number): void => {
      nodes.forEach(node => {
        if (node.level < maxLevel && node.hasChildren) {
          newExpanded.add(keyToString(node.key));
        }
        if (node.children) {
          collectKeysUpToLevel(node.children, maxLevel);
        }
      });
    };
    collectKeysUpToLevel(hierarchicalRows, targetCodeLevel);
    setExpandedRows(newExpanded);
    setContextMenu(null);
  };

  // Navigation par niveaux : Expand to level X (afficher tous les niveaux <= X)
  // targetLevel est le niveau Excel (1-indexed), donc level 2 = niveau 1 dans mon code
  const expandToLevel = (targetExcelLevel: number) => {
    const targetCodeLevel = targetExcelLevel - 1; // Convertir Excel Level (1-indexed) → Code level (0-indexed)
    const newExpanded = new Set(expandedRows);
    // Ajouter toutes les clés des niveaux < targetCodeLevel (pour voir jusqu'à targetCodeLevel)
    const collectKeysUpToLevel = (nodes: PivotRow[], maxLevel: number): void => {
      nodes.forEach(node => {
        if (node.level < maxLevel && node.hasChildren) {
          newExpanded.add(keyToString(node.key));
        }
        if (node.children) {
          collectKeysUpToLevel(node.children, maxLevel);
        }
      });
    };
    collectKeysUpToLevel(hierarchicalRows, targetCodeLevel);
    setExpandedRows(newExpanded);
    setContextMenu(null);
  };

  // Gérer le clic droit (menu contextuel)
  const handleContextMenu = (e: React.MouseEvent, rowKey: string | number | (string | number)[], rowLevel: number) => {
    e.preventDefault();
    setContextMenu({
      x: e.clientX,
      y: e.clientY,
      rowKey: rowKey,
      rowLevel: rowLevel,
    });
  };

  // Fermer le menu contextuel
  const closeContextMenu = () => {
    setContextMenu(null);
  };

  // Fermer le menu au clic ailleurs ou Escape
  useEffect(() => {
    const handleClickOutside = () => {
      if (contextMenu) {
        closeContextMenu();
      }
    };

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && contextMenu) {
        closeContextMenu();
      }
    };

    if (contextMenu) {
      document.addEventListener('click', handleClickOutside);
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('click', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [contextMenu]);

  // Rendre une ligne récursivement
  const renderRow = (row: PivotRow, columns: (string | number | (string | number)[])[], columnTotals: Record<string, number>, parentKey: string = '', rowIndexByLevel: Map<number, number> = new Map()): React.ReactNode => {
    const keyStr = keyToString(row.key);
    const uniqueKey = `${parentKey}-${keyStr}`;
    const isExpanded = expandedRows.has(keyStr);
    const indent = row.level * 24;

    // Gérer l'alternance zebra par niveau
    const currentIndex = rowIndexByLevel.get(row.level) || 0;
    rowIndexByLevel.set(row.level, currentIndex + 1);
    const isEven = currentIndex % 2 === 0;

    // Couleurs par niveau - Thème de l'application
    let bgColor: string;
    let textColor: string;
    let borderLeft: string = 'none';
    let fontWeight: string;

    if (row.level === 0) {
      // Niveau 1 : Fond blanc, texte noir bold
      bgColor = '#ffffff';
      textColor = '#000000';
      fontWeight = '700';
      borderLeft = '4px solid #1e3a5f';
    } else if (row.level === 1) {
      // Niveau 2 : Fond bleu foncé (#1e3a5f), texte blanc bold
      bgColor = '#1e3a5f';
      textColor = '#ffffff';
      fontWeight = '700';
      borderLeft = '3px solid #1e3a5f';
    } else {
      // Niveau 3+ : Alternance blanc/gris très clair, texte noir normal
      bgColor = isEven ? '#ffffff' : '#f8f9fa';
      textColor = '#000000';
      fontWeight = '400';
      borderLeft = '2px solid #e5e7eb';
    }

    return (
      <>
        <tr
          key={uniqueKey}
          onContextMenu={(e) => handleContextMenu(e, row.key, row.level)}
          style={{
            backgroundColor: bgColor,
            borderBottom: '1px solid #e2e8f0',
            borderTop: row.level === 0 ? '2px solid #cbd5e1' : '1px solid #e2e8f0',
            cursor: 'context-menu',
          }}
        >
          {/* Cellule de ligne */}
          <td
            style={{
              padding: '10px 12px',
              borderRight: '1px solid #e2e8f0',
              borderLeft: borderLeft,
              fontWeight: fontWeight,
              fontSize: row.level === 0 ? '14px' : row.level === 1 ? '13px' : '12px',
              color: textColor,
              paddingLeft: `${12 + indent}px`,
              position: 'sticky',
              left: 0,
              zIndex: 5,
              backgroundColor: bgColor,
              minWidth: '200px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {row.hasChildren && (
                <button
                  onClick={() => toggleExpand(row.key)}
                  style={{
                    width: '20px',
                    height: '20px',
                    border: '1px solid #d1d5db',
                    borderRadius: '4px',
                    backgroundColor: '#ffffff',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '12px',
                    padding: 0,
                  }}
                >
                  {isExpanded ? '−' : '+'}
                </button>
              )}
              {!row.hasChildren && <span style={{ width: '20px' }} />}
              <span>{row.label}</span>
            </div>
          </td>
          {/* Cellules de données */}
          {columns.map((col, colIdx) => {
            // Le backend convertit les clés en strings avec str(list(key))
            // Format: "['val1', 'val2']" pour arrays, ou juste la valeur pour simples
            const colKeyStr = keyToString(col);
            
            // Accéder aux données avec le bon format de clé
            const value = row.values[colKeyStr] || 0;

            return (
              <td
                key={colIdx}
                onClick={() => onCellClick?.(Array.isArray(row.key) ? row.key : [row.key], Array.isArray(col) ? col : [col])}
                style={{
                  padding: '10px 12px',
                  borderRight: '1px solid #e2e8f0',
                  textAlign: 'right',
                  cursor: onCellClick ? 'pointer' : 'default',
                  backgroundColor: bgColor,
                  transition: 'background-color 0.15s',
                  fontWeight: row.level === 0 ? '700' : row.level === 1 ? '700' : '400',
                  color: textColor,
                }}
                onMouseEnter={(e) => {
                  if (onCellClick) {
                    if (row.level === 0) {
                      e.currentTarget.style.backgroundColor = '#f3f4f6';
                    } else if (row.level === 1) {
                      e.currentTarget.style.backgroundColor = '#2d4a6f';
                    } else {
                      e.currentTarget.style.backgroundColor = '#e5e7eb';
                    }
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = bgColor;
                }}
              >
                {value.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </td>
            );
          })}
          {/* Total de ligne */}
          <td
            onClick={() => onCellClick?.(Array.isArray(row.key) ? row.key : [row.key], ['TOTAL'])}
            style={{
              padding: '10px 12px',
              borderRight: '1px solid #e2e8f0',
              backgroundColor: bgColor,
              fontWeight: row.level === 0 ? '700' : row.level === 1 ? '700' : '400',
              textAlign: 'right',
              cursor: onCellClick ? 'pointer' : 'default',
              transition: 'background-color 0.15s',
              color: textColor,
            }}
            onMouseEnter={(e) => {
              if (onCellClick) {
                if (row.level === 0) {
                  e.currentTarget.style.backgroundColor = '#f3f4f6';
                } else if (row.level === 1) {
                  e.currentTarget.style.backgroundColor = '#2d4a6f';
                } else {
                  e.currentTarget.style.backgroundColor = '#e5e7eb';
                }
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = bgColor;
            }}
          >
            {row.total.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </td>
        </tr>
        {/* Rendre les enfants si expandé */}
        {row.hasChildren && isExpanded && row.children && row.children.map((child, childIdx) => {
          const childKey = keyToString(child.key);
          return (
            <React.Fragment key={`${uniqueKey}-child-${childIdx}-${childKey}`}>
              {renderRow(child, columns, columnTotals, uniqueKey, rowIndexByLevel)}
            </React.Fragment>
          );
        })}
      </>
    );
  };

  if (config.rows.length === 0 && config.columns.length === 0) {
    return (
      <div style={{ padding: '48px', textAlign: 'center', color: '#6b7280' }}>
        <p style={{ fontSize: '14px' }}>Sélectionnez des champs dans le panneau de configuration pour afficher le tableau croisé.</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div style={{ padding: '48px', textAlign: 'center' }}>
        <div style={{ fontSize: '14px', color: '#6b7280' }}>⏳ Chargement des données...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '48px', textAlign: 'center' }}>
        <div style={{ fontSize: '14px', color: '#ef4444' }}>❌ Erreur: {error}</div>
      </div>
    );
  }

  if (!pivotData) {
    return null;
  }

  const columns = pivotData.columns || [];
  const columnTotals = pivotData.column_totals || {};
  const grandTotal = pivotData.grand_total || 0;

  return (
    <div style={{ padding: '16px', overflowX: 'auto', backgroundColor: '#ffffff' }}>
      <table
        style={{
          borderCollapse: 'collapse',
          width: '100%',
          fontSize: '13px',
          backgroundColor: '#ffffff',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        }}
      >
        <thead>
          <tr style={{ backgroundColor: '#1e293b' }}>
            <th
              style={{
                padding: '12px',
                border: '1px solid #334155',
                borderLeft: '4px solid #0284c7',
                fontWeight: '700',
                fontSize: '13px',
                textAlign: 'left',
                position: 'sticky',
                left: 0,
                zIndex: 10,
                backgroundColor: '#1e293b',
                color: '#ffffff',
                minWidth: '200px',
              }}
            >
              {pivotData.row_fields.length > 0 ? pivotData.row_fields.join(' / ') : 'Lignes'}
            </th>
            {columns.map((col, colIdx) => (
              <th
                key={colIdx}
                style={{
                  padding: '12px',
                  border: '1px solid #334155',
                  fontWeight: '700',
                  fontSize: '13px',
                  textAlign: 'right',
                  color: '#ffffff',
                  minWidth: '120px',
                }}
              >
                {formatKey(col)}
              </th>
            ))}
            <th
              style={{
                padding: '12px',
                border: '1px solid #334155',
                fontWeight: '700',
                fontSize: '13px',
                textAlign: 'right',
                minWidth: '120px',
                backgroundColor: '#0f172a',
                color: '#ffffff',
              }}
            >
              Total
            </th>
          </tr>
        </thead>
        <tbody>
          {hierarchicalRows.map((row, idx) => {
            const rowIndexByLevel = new Map<number, number>(); // Reset pour chaque ligne racine
            const rowKey = keyToString(row.key);
            return (
              <React.Fragment key={`root-${idx}-${rowKey}`}>
                {renderRow(row, columns, columnTotals, `root-${idx}`, rowIndexByLevel)}
              </React.Fragment>
            );
          })}
          {/* Ligne de totaux */}
          <tr style={{ backgroundColor: '#f1f5f9', borderTop: '3px solid #cbd5e1' }}>
            <td
              style={{
                padding: '12px',
                border: '1px solid #cbd5e1',
                borderLeft: '4px solid #0284c7',
                fontWeight: '700',
                fontSize: '14px',
                position: 'sticky',
                left: 0,
                zIndex: 5,
                backgroundColor: '#94a3b8',
                color: '#ffffff',
              }}
            >
              Total
            </td>
            {columns.map((col, colIdx) => {
              const colKeyStr = keyToString(col);
              const colTotal = columnTotals[colKeyStr] || 0;
              return (
                <td
                  key={colIdx}
                  onClick={() => onCellClick?.(['TOTAL'], Array.isArray(col) ? col : [col])}
                  style={{
                    padding: '12px',
                    border: '1px solid #cbd5e1',
                    fontWeight: '700',
                    textAlign: 'right',
                    cursor: onCellClick ? 'pointer' : 'default',
                    backgroundColor: '#94a3b8',
                    color: '#ffffff',
                    transition: 'background-color 0.15s',
                  }}
                  onMouseEnter={(e) => {
                    if (onCellClick) {
                      e.currentTarget.style.backgroundColor = '#64748b';
                    }
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = '#94a3b8';
                  }}
                >
                  {colTotal.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </td>
              );
            })}
            <td
              onClick={() => onCellClick?.(['TOTAL'], ['TOTAL'])}
              style={{
                padding: '12px',
                border: '1px solid #cbd5e1',
                fontWeight: '700',
                textAlign: 'right',
                cursor: onCellClick ? 'pointer' : 'default',
                backgroundColor: '#64748b',
                color: '#ffffff',
                transition: 'background-color 0.15s',
              }}
              onMouseEnter={(e) => {
                if (onCellClick) {
                  e.currentTarget.style.backgroundColor = '#475569';
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#64748b';
              }}
            >
              {grandTotal.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </td>
          </tr>
        </tbody>
      </table>
      
      {/* Menu contextuel */}
      {contextMenu && (() => {
        const maxLevel = config.rows.length - 1; // Niveau maximum (0-indexed)
        const excelLevel = contextMenu.rowLevel + 1; // Excel Level (1-indexed)
        // Trouver la ligne cliquée pour vérifier si elle a des enfants
        const clickedRow = findInHierarchy(hierarchicalRows, Array.isArray(contextMenu.rowKey) ? contextMenu.rowKey : [contextMenu.rowKey]);
        const hasChildren = clickedRow?.hasChildren || false;
        
        return (
          <div
            style={{
              position: 'fixed',
              top: contextMenu.y,
              left: contextMenu.x,
              backgroundColor: '#ffffff',
              border: '1px solid #d1d5db',
              borderRadius: '4px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
              zIndex: 1000,
              minWidth: '180px',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Expand / Collapse (élément unique) */}
            {hasChildren && (
              <>
                <button
                  onClick={() => expandElement(contextMenu.rowKey)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    textAlign: 'left',
                    border: 'none',
                    backgroundColor: 'transparent',
                    cursor: 'pointer',
                    fontSize: '14px',
                    color: '#1f2937',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#f3f4f6';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  Expand
                </button>
                <button
                  onClick={() => collapseElement(contextMenu.rowKey)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    textAlign: 'left',
                    border: 'none',
                    backgroundColor: 'transparent',
                    cursor: 'pointer',
                    fontSize: '14px',
                    color: '#1f2937',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#f3f4f6';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  Collapse
                </button>
                <div style={{ height: '1px', backgroundColor: '#e5e7eb', margin: '4px 0' }} />
              </>
            )}
            
            {/* Expand/Collapse Entire Field */}
            <button
              onClick={() => expandEntireField(contextMenu.rowLevel)}
              style={{
                width: '100%',
                padding: '8px 12px',
                textAlign: 'left',
                border: 'none',
                backgroundColor: 'transparent',
                cursor: 'pointer',
                fontSize: '14px',
                color: '#1f2937',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#f3f4f6';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent';
              }}
            >
              Expand Entire Field
            </button>
            <button
              onClick={() => collapseEntireField(contextMenu.rowLevel)}
              style={{
                width: '100%',
                padding: '8px 12px',
                textAlign: 'left',
                border: 'none',
                backgroundColor: 'transparent',
                cursor: 'pointer',
                fontSize: '14px',
                color: '#1f2937',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#f3f4f6';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent';
              }}
            >
              Collapse Entire Field
            </button>
            <div style={{ height: '1px', backgroundColor: '#e5e7eb', margin: '4px 0' }} />
            
            {/* Navigation par niveaux */}
            {/* Collapse to level 1 (Excel) = niveau 0 (code) = voir seulement le niveau racine */}
            {maxLevel >= 0 && (
              <button
                onClick={() => collapseToLevel(1)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  textAlign: 'left',
                  border: 'none',
                  backgroundColor: 'transparent',
                  cursor: 'pointer',
                  fontSize: '14px',
                  color: '#1f2937',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#f3f4f6';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }}
              >
                Collapse to "level 1"
              </button>
            )}
            {/* Expand to level 2 (Excel) = niveau 1 (code) = voir jusqu'au niveau 2 */}
            {maxLevel >= 1 && (
              <button
                onClick={() => expandToLevel(2)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  textAlign: 'left',
                  border: 'none',
                  backgroundColor: 'transparent',
                  cursor: 'pointer',
                  fontSize: '14px',
                  color: '#1f2937',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#f3f4f6';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }}
              >
                Expand to "level 2"
              </button>
            )}
            {/* Expand to level 3 (Excel) = niveau 2 (code) = voir jusqu'au niveau 3 (tout) */}
            {maxLevel >= 2 && (
              <button
                onClick={() => expandToLevel(3)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  textAlign: 'left',
                  border: 'none',
                  backgroundColor: 'transparent',
                  cursor: 'pointer',
                  fontSize: '14px',
                  color: '#1f2937',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#f3f4f6';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }}
              >
                Expand to "level 3"
              </button>
            )}
          </div>
        );
      })()}
    </div>
  );
}
