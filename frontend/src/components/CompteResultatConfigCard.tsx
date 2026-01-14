/**
 * CompteResultatConfigCard - Card de configuration du compte de résultat
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 * 
 * Intègre Step 8.4.5 (Filtre Level 3) et Step 8.5 (Tableau de mapping)
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { transactionsAPI, compteResultatAPI, CompteResultatMapping } from '@/api/client';

interface CompteResultatConfigCardProps {
  onConfigUpdated?: () => void;
  onLevel3Change?: (level3Values: string[]) => void;
  onLevel3ValuesLoaded?: (count: number) => void;
}

const STORAGE_KEY_COLLAPSED = 'compte_resultat_config_collapsed';

export default function CompteResultatConfigCard({
  onConfigUpdated,
  onLevel3Change,
  onLevel3ValuesLoaded,
}: CompteResultatConfigCardProps) {
  
  const [selectedLevel3Values, setSelectedLevel3Values] = useState<string[]>([]);
  const [level3Values, setLevel3Values] = useState<string[]>([]);
  const [loadingValues, setLoadingValues] = useState<boolean>(false);
  const [level3ValuesLoaded, setLevel3ValuesLoaded] = useState<boolean>(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState<boolean>(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  // États pour les mappings
  const [mappings, setMappings] = useState<CompteResultatMapping[]>([]);
  const [loadingMappings, setLoadingMappings] = useState<boolean>(false);
  
  // États pour la colonne "Level 1 (valeurs)"
  const [level1Values, setLevel1Values] = useState<string[]>([]);
  const [loadingLevel1Values, setLoadingLevel1Values] = useState<boolean>(false);
  const [openLevel1DropdownId, setOpenLevel1DropdownId] = useState<number | string | null>(null);
  const [level1DropdownPosition, setLevel1DropdownPosition] = useState<'bottom' | 'top'>('bottom');
  
  // État pour le repli/dépli de la card
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);

  // Catégories prédéfinies
  const PRODUITS_CATEGORIES = [
    'Loyers hors charge encaissés',
    'Charges locatives payées par locataires',
    'Autres revenus',
  ];

  const CHARGES_CATEGORIES = [
    'Charges de copropriété hors fonds travaux',
    'Fluides non refacturés',
    'Assurances',
    'Honoraires',
    'Travaux et mobilier',
    'Impôts et taxes',
    'Autres charges diverses',
  ];

  const SPECIAL_CATEGORIES = [
    "Charges d'amortissements",
    'Coût du financement (hors remboursement du capital)',
  ];

  // Toutes les catégories prédéfinies (pour affichage complet)
  const ALL_CATEGORIES = [
    ...PRODUITS_CATEGORIES,
    ...CHARGES_CATEGORIES,
    ...SPECIAL_CATEGORIES,
  ];

  // Déterminer le Type selon la catégorie
  const getTypeForCategory = (categoryName: string): 'Produits d\'exploitation' | 'Charges d\'exploitation' => {
    if (PRODUITS_CATEGORIES.includes(categoryName)) {
      return 'Produits d\'exploitation';
    }
    return 'Charges d\'exploitation';
  };

  // Créer une map des mappings par catégorie pour accès rapide
  const mappingsByCategory = new Map<string, CompteResultatMapping>();
  mappings.forEach(mapping => {
    mappingsByCategory.set(mapping.category_name, mapping);
  });

  // Créer la liste complète des catégories avec leurs mappings (si existants)
  interface CategoryRow {
    categoryName: string;
    type: 'Produits d\'exploitation' | 'Charges d\'exploitation';
    mapping: CompteResultatMapping | null;
  }

  const allCategoriesWithMappings: CategoryRow[] = ALL_CATEGORIES.map(categoryName => ({
    categoryName,
    type: getTypeForCategory(categoryName),
    mapping: mappingsByCategory.get(categoryName) || null,
  }));

  // Trier par Type puis par Catégorie
  const sortedCategories = [...allCategoriesWithMappings].sort((a, b) => {
    if (a.type !== b.type) {
      return a.type.localeCompare(b.type);
    }
    return a.categoryName.localeCompare(b.categoryName);
  });

  // Charger les valeurs Level 3 depuis l'API
  const loadLevel3Values = async () => {
    try {
      setLoadingValues(true);
      const response = await transactionsAPI.getUniqueValues('level_3');
      const values = response.values || [];
      setLevel3Values(values);
      setLevel3ValuesLoaded(true);

      // Notifier le parent du nombre de valeurs disponibles
      if (onLevel3ValuesLoaded) {
        onLevel3ValuesLoaded(values.length);
      }
      
      // Charger la configuration depuis l'API
      try {
        const config = await compteResultatAPI.getConfig();
        if (config.level_3_values) {
          try {
            const savedValues: string[] = JSON.parse(config.level_3_values);
            const validValues = savedValues.filter(v => values.includes(v));
            if (validValues.length > 0) {
              setSelectedLevel3Values(validValues);
              if (onLevel3Change) {
                onLevel3Change(validValues);
              }
            }
          } catch (e) {
            // Si ce n'est pas du JSON valide, ignorer
            console.warn('Configuration level_3_values invalide:', config.level_3_values);
          }
        }
      } catch (err) {
        console.error('Erreur lors du chargement de la configuration:', err);
      }
      
      // Restaurer l'état collapsed depuis localStorage
      const savedCollapsed = localStorage.getItem(STORAGE_KEY_COLLAPSED);
      if (savedCollapsed !== null) {
        setIsCollapsed(savedCollapsed === 'true');
      }
    } catch (err: any) {
      console.error('Erreur lors du chargement des valeurs level_3:', err);
      setLevel3ValuesLoaded(true);
      if (onLevel3ValuesLoaded) {
        onLevel3ValuesLoaded(0);
      }
    } finally {
      setLoadingValues(false);
    }
  };

  // Charger les mappings
  const loadMappings = async () => {
    try {
      setLoadingMappings(true);
      const response = await compteResultatAPI.getMappings();
      setMappings(response.items || []);
    } catch (err: any) {
      console.error('Erreur lors du chargement des mappings:', err);
    } finally {
      setLoadingMappings(false);
    }
  };

  // Charger les valeurs Level 1 filtrées par Level 3
  const loadLevel1Values = async () => {
    if (selectedLevel3Values.length === 0) {
      setLevel1Values([]);
      return;
    }

    try {
      setLoadingLevel1Values(true);
      const response = await transactionsAPI.getUniqueValues('level_1', undefined, undefined, undefined, selectedLevel3Values);
      setLevel1Values(response.values || []);
    } catch (err: any) {
      console.error('Erreur lors du chargement des valeurs level_1:', err);
      setLevel1Values([]);
    } finally {
      setLoadingLevel1Values(false);
    }
  };

  // Charger les valeurs au montage
  useEffect(() => {
    loadLevel3Values();
    loadMappings();
  }, []);

  // Charger les level_1 quand les level_3 sélectionnés changent
  useEffect(() => {
    loadLevel1Values();
  }, [selectedLevel3Values]);

  // Gérer le changement de checkbox Level 3
  const handleLevel3CheckboxChange = async (value: string, checked: boolean) => {
    let newValues: string[];
    if (checked) {
      newValues = [...selectedLevel3Values, value];
    } else {
      newValues = selectedLevel3Values.filter(v => v !== value);
    }
    
    setSelectedLevel3Values(newValues);
    
    // Sauvegarder via API
    try {
      await compteResultatAPI.updateConfig({
        level_3_values: JSON.stringify(newValues),
      });
      
      if (onLevel3Change) {
        onLevel3Change(newValues);
      }
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('Erreur lors de la sauvegarde de la configuration:', err);
      // Revenir à l'état précédent en cas d'erreur
      setSelectedLevel3Values(selectedLevel3Values);
    }
  };

  // Fermer le dropdown si on clique en dehors
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Gérer le repli/dépli
  const toggleCollapse = () => {
    const newCollapsed = !isCollapsed;
    setIsCollapsed(newCollapsed);
    localStorage.setItem(STORAGE_KEY_COLLAPSED, String(newCollapsed));
  };

  // Gérer l'ajout/suppression d'une valeur Level 1
  const handleLevel1Toggle = async (categoryName: string, level1Value: string, mappingId?: number) => {
    // Si pas de mappingId, créer le mapping d'abord
    if (!mappingId) {
      try {
        const newMapping = await compteResultatAPI.createMapping({
          category_name: categoryName,
          level_1_values: JSON.stringify([level1Value]),
        });
        // Recharger les mappings pour avoir le nouveau mapping
        await loadMappings();
        if (onConfigUpdated) {
          onConfigUpdated();
        }
        return;
      } catch (err: any) {
        console.error('Erreur lors de la création du mapping:', err);
        alert(`Erreur lors de la création: ${err.message || 'Erreur inconnue'}`);
        return;
      }
    }
    
    const mapping = mappings.find(m => m.id === mappingId);
    if (!mapping) return;
    
    let currentValues: string[] = [];
    if (mapping.level_1_values) {
      try {
        currentValues = JSON.parse(mapping.level_1_values);
        if (!Array.isArray(currentValues)) {
          currentValues = [];
        }
      } catch (e) {
        currentValues = [];
      }
    }
    
    const isSelected = currentValues.includes(level1Value);
    
    let newValues: string[];
    if (isSelected) {
      // Supprimer la valeur
      newValues = currentValues.filter(v => v !== level1Value);
    } else {
      // Ajouter la valeur
      newValues = [...currentValues, level1Value];
    }

    try {
      await compteResultatAPI.updateMapping(mappingId, {
        level_1_values: JSON.stringify(newValues),
      });
      
      // Recharger les mappings pour avoir la valeur à jour
      await loadMappings();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('Erreur lors de la mise à jour des valeurs level_1:', err);
      alert(`Erreur lors de la sauvegarde: ${err.message || 'Erreur inconnue'}`);
    }
  };

  // Gérer la suppression d'une valeur Level 1 (via le tag)
  const handleLevel1Remove = async (categoryName: string, mappingId: number, level1Value: string) => {
    await handleLevel1Toggle(categoryName, level1Value, mappingId);
  };

  // Fermer le dropdown Level 1 si on clique en dehors
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      // Fermer tous les dropdowns Level 1 si on clique en dehors
      const target = event.target as Node;
      const isClickInsideDropdown = (target as Element).closest('[data-level1-dropdown]');
      if (!isClickInsideDropdown) {
        setOpenLevel1DropdownId(null);
      }
    };

    if (openLevel1DropdownId !== null) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [openLevel1DropdownId]);

  return (
    <div
      style={{
        backgroundColor: '#ffffff',
        border: '1px solid #e5e7eb',
        borderRadius: '8px',
        padding: '20px',
        marginBottom: '24px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
      }}
    >
      {/* En-tête de la card */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: isCollapsed ? 0 : '20px',
          cursor: 'pointer',
        }}
        onClick={toggleCollapse}
      >
        <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '600', color: '#111827' }}>
          Configuration du compte de résultat
        </h3>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            toggleCollapse();
          }}
          style={{
            background: 'none',
            border: 'none',
            fontSize: '20px',
            cursor: 'pointer',
            color: '#6b7280',
            padding: '4px 8px',
          }}
        >
          {isCollapsed ? '▶' : '▼'}
        </button>
      </div>
      
      {/* Contenu de la card (masqué si collapsed) */}
      {!isCollapsed && (
        <>
          {/* Champ Level 3 - Dropdown avec checkboxes */}
          <div style={{ marginBottom: '24px' }}>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '8px' }}>
              Level 3 (Valeur à considérer dans le compte de résultat)
            </label>
            {loadingValues ? (
              <div style={{ color: '#6b7280', fontSize: '14px' }}>Chargement...</div>
            ) : level3Values.length === 0 ? (
              <div style={{ color: '#6b7280', fontSize: '14px' }}>Aucune valeur disponible</div>
            ) : (
              <div ref={dropdownRef} style={{ position: 'relative', maxWidth: '400px' }}>
                {/* Bouton du dropdown */}
                <button
                  type="button"
                  onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    fontSize: '14px',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    backgroundColor: '#ffffff',
                    color: '#111827',
                    cursor: 'pointer',
                    textAlign: 'left',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {selectedLevel3Values.length > 0
                      ? `${selectedLevel3Values.length} valeur(s) sélectionnée(s)`
                      : '-- Sélectionner des valeurs --'}
                  </span>
                  <span style={{ marginLeft: '8px', fontSize: '12px', color: '#6b7280' }}>
                    {isDropdownOpen ? '▲' : '▼'}
                  </span>
                </button>

                {/* Menu déroulant avec checkboxes */}
                {isDropdownOpen && (
                  <div
                    style={{
                      position: 'absolute',
                      top: '100%',
                      left: 0,
                      right: 0,
                      marginTop: '4px',
                      backgroundColor: '#ffffff',
                      border: '1px solid #d1d5db',
                      borderRadius: '6px',
                      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                      zIndex: 1000,
                      maxHeight: '200px',
                      overflowY: 'auto',
                    }}
                  >
                    {level3Values.map((value) => (
                      <label
                        key={value}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px',
                          cursor: 'pointer',
                          fontSize: '14px',
                          color: '#111827',
                          padding: '8px 12px',
                          borderBottom: '1px solid #f3f4f6',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = '#f9fafb';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = '#ffffff';
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={selectedLevel3Values.includes(value)}
                          onChange={(e) => handleLevel3CheckboxChange(value, e.target.checked)}
                          style={{
                            width: '16px',
                            height: '16px',
                            cursor: 'pointer',
                          }}
                        />
                        <span>{value}</span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Tableau de mapping - Masqué si aucune valeur level_3 sélectionnée */}
          {selectedLevel3Values.length > 0 && (
            <div style={{ overflowX: 'auto' }}>
              <table
                style={{
                  width: '100%',
                  borderCollapse: 'collapse',
                  fontSize: '14px',
                }}
              >
                <thead>
                  <tr style={{ backgroundColor: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151', width: '20%' }}>
                      Type
                    </th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151', width: '30%' }}>
                      Catégorie comptable
                    </th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151', width: '50%' }}>
                      Level 1 (valeurs)
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {loadingMappings ? (
                    <tr>
                      <td colSpan={3} style={{ padding: '20px', textAlign: 'center', color: '#6b7280' }}>
                        Chargement des mappings...
                      </td>
                    </tr>
                  ) : (
                    sortedCategories.map((categoryRow) => {
                      const { categoryName, type, mapping } = categoryRow;
                      const isSpecialCategory = SPECIAL_CATEGORIES.includes(categoryName);
                      const key = mapping ? `mapping-${mapping.id}` : `category-${categoryName}`;
                      
                      return (
                        <tr
                          key={key}
                          style={{
                            borderBottom: '1px solid #e5e7eb',
                          }}
                        >
                          <td style={{ padding: '12px', color: '#111827', width: '20%' }}>
                            {type}
                          </td>
                          <td style={{ padding: '12px', color: '#111827', width: '30%' }}>
                            {categoryName}
                          </td>
                          <td style={{ padding: '12px', color: '#111827', width: '50%' }}>
                            {isSpecialCategory ? (
                              <span style={{ color: '#6b7280', fontStyle: 'italic' }}>
                                Données calculées
                              </span>
                            ) : (
                              <div style={{ position: 'relative' }}>
                                {/* Tags des valeurs sélectionnées */}
                                {mapping && (() => {
                                  let currentValues: string[] = [];
                                  if (mapping.level_1_values) {
                                    try {
                                      currentValues = JSON.parse(mapping.level_1_values);
                                      if (!Array.isArray(currentValues)) {
                                        currentValues = [];
                                      }
                                    } catch (e) {
                                      currentValues = [];
                                    }
                                  }
                                  return currentValues.length > 0 ? (
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '6px' }}>
                                      {currentValues.map((value) => (
                                        <span
                                          key={value}
                                          style={{
                                            display: 'inline-flex',
                                            alignItems: 'center',
                                            gap: '4px',
                                            padding: '4px 8px',
                                            backgroundColor: '#3b82f6',
                                            color: '#ffffff',
                                            borderRadius: '4px',
                                            fontSize: '12px',
                                            fontWeight: '500',
                                          }}
                                        >
                                          {value}
                                          <button
                                            type="button"
                                            onClick={() => handleLevel1Remove(categoryName, mapping.id, value)}
                                            style={{
                                              background: 'none',
                                              border: 'none',
                                              color: '#ffffff',
                                              cursor: 'pointer',
                                              padding: '0',
                                              marginLeft: '4px',
                                              fontSize: '14px',
                                              lineHeight: '1',
                                              fontWeight: 'bold',
                                            }}
                                            title="Supprimer"
                                          >
                                            ×
                                          </button>
                                        </span>
                                      ))}
                                    </div>
                                  ) : null;
                                })()}
                                
                                {/* Bouton "+" pour ouvrir le dropdown */}
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    // Détecter si on est dans les rangées du bas pour positionner le dropdown vers le haut
                                    const buttonRect = e.currentTarget.getBoundingClientRect();
                                    const viewportHeight = window.innerHeight;
                                    
                                    // Si le bouton est dans la moitié inférieure de la viewport, afficher le dropdown vers le haut
                                    const shouldShowTop = buttonRect.bottom > viewportHeight / 2;
                                    
                                    // Utiliser categoryName comme identifiant si pas de mapping
                                    const dropdownId = mapping ? mapping.id : categoryName;
                                    setLevel1DropdownPosition(shouldShowTop ? 'top' : 'bottom');
                                    setOpenLevel1DropdownId(openLevel1DropdownId === dropdownId ? null : dropdownId);
                                  }}
                                  style={{
                                    padding: '4px 8px',
                                    fontSize: '12px',
                                    color: '#3b82f6',
                                    backgroundColor: '#eff6ff',
                                    border: '1px solid #3b82f6',
                                    borderRadius: '4px',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '4px',
                                  }}
                                >
                                  <span>+</span>
                                  <span>Ajouter</span>
                                </button>
                                
                                {/* Dropdown */}
                                {(() => {
                                  const dropdownId = mapping ? mapping.id : categoryName;
                                  return openLevel1DropdownId === dropdownId && (
                                  <div
                                    data-level1-dropdown
                                    style={{
                                      position: 'absolute',
                                      ...(level1DropdownPosition === 'top' 
                                        ? { bottom: '100%', marginBottom: '4px' }
                                        : { top: '100%', marginTop: '4px' }
                                      ),
                                      left: 0,
                                      backgroundColor: '#ffffff',
                                      border: '1px solid #d1d5db',
                                      borderRadius: '6px',
                                      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                                      zIndex: 1000,
                                      maxHeight: '200px',
                                      overflowY: 'auto',
                                      minWidth: '200px',
                                    }}
                                  >
                                    {loadingLevel1Values ? (
                                      <div style={{ padding: '12px', color: '#6b7280', fontSize: '14px' }}>
                                        Chargement...
                                      </div>
                                    ) : level1Values.length === 0 ? (
                                      <div style={{ padding: '12px', color: '#6b7280', fontSize: '14px' }}>
                                        Aucune valeur disponible
                                      </div>
                                    ) : (() => {
                                      // Collecter toutes les valeurs Level 1 déjà sélectionnées pour TOUTES les catégories
                                      const allSelectedValues = new Set<string>();
                                      mappings.forEach(m => {
                                        if (m.level_1_values) {
                                          try {
                                            const values = JSON.parse(m.level_1_values);
                                            if (Array.isArray(values)) {
                                              values.forEach(v => allSelectedValues.add(v));
                                            }
                                          } catch (e) {
                                            // Ignorer les erreurs de parsing
                                          }
                                        }
                                      });
                                      
                                      // Filtrer les valeurs déjà sélectionnées (pour n'importe quelle catégorie)
                                      const availableValues = level1Values.filter(value => !allSelectedValues.has(value));
                                      
                                      if (availableValues.length === 0) {
                                        return (
                                          <div style={{ padding: '12px', color: '#6b7280', fontSize: '14px' }}>
                                            Toutes les valeurs sont déjà sélectionnées
                                          </div>
                                        );
                                      }
                                      
                                      return availableValues.map((value) => (
                                        <label
                                          key={value}
                                          style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '8px',
                                            padding: '8px 12px',
                                            cursor: 'pointer',
                                            backgroundColor: 'transparent',
                                          }}
                                          onMouseEnter={(e) => {
                                            e.currentTarget.style.backgroundColor = '#f9fafb';
                                          }}
                                          onMouseLeave={(e) => {
                                            e.currentTarget.style.backgroundColor = 'transparent';
                                          }}
                                        >
                                          <input
                                            type="checkbox"
                                            checked={(() => {
                                              if (!mapping) return false;
                                              let currentValues: string[] = [];
                                              if (mapping.level_1_values) {
                                                try {
                                                  currentValues = JSON.parse(mapping.level_1_values);
                                                  if (!Array.isArray(currentValues)) {
                                                    currentValues = [];
                                                  }
                                                } catch (e) {
                                                  currentValues = [];
                                                }
                                              }
                                              return currentValues.includes(value);
                                            })()}
                                            onChange={() => handleLevel1Toggle(categoryName, value, mapping?.id)}
                                            style={{
                                              width: '16px',
                                              height: '16px',
                                              cursor: 'pointer',
                                            }}
                                          />
                                          <span>{value}</span>
                                        </label>
                                      ));
                                    })()}
                                  </div>
                                  );
                                })()}
                              </div>
                            )}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          )}

          {/* Message si aucune valeur level_3 sélectionnée */}
          {selectedLevel3Values.length === 0 && (
            <div style={{ padding: '20px', textAlign: 'center', color: '#6b7280', fontSize: '14px' }}>
              Veuillez sélectionner au moins une valeur Level 3 pour afficher le tableau de mapping
            </div>
          )}
        </>
      )}
    </div>
  );
}
