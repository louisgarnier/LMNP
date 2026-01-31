/**
 * BilanConfigCard - Card de configuration du bilan
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 * 
 * Card de configuration pour mapper les level_1 aux catégories comptables du bilan
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { transactionsAPI, bilanAPI, BilanMapping } from '@/api/client';
import { useProperty } from '@/contexts/PropertyContext';

interface BilanConfigCardProps {
  onConfigUpdated?: () => void;
  onLevel3Change?: (level3Values: string[]) => void;
  isActive?: boolean; // Ne charger les données que si l'onglet est actif
}

const STORAGE_KEY_COLLAPSED = 'bilan_config_collapsed';

// Sous-catégories prédéfinies par Type
const SUB_CATEGORIES_BY_TYPE: Record<string, string[]> = {
  'ACTIF': [
    'Actif immobilisé',
    'Actif circulant',
  ],
  'PASSIF': [
    'Capitaux propres',
    'Trésorerie passive',
    'Dettes financières',
  ],
};

// Catégories spéciales
const SPECIAL_CATEGORIES = [
  'Amortissements cumulés',
  'Compte bancaire',
  'Résultat de l\'exercice',
  'Report à nouveau / report du déficit',
  'Emprunt bancaire (capital restant dû)',
];

// Catégories spéciales qui nécessitent une vue de compte de résultat
const SPECIAL_CATEGORIES_WITH_VIEW = [
  'Résultat de l\'exercice',
];

export default function BilanConfigCard({
  onConfigUpdated,
  onLevel3Change,
  isActive = true,
}: BilanConfigCardProps) {
  const { activeProperty } = useProperty();
  
  const [selectedLevel3Values, setSelectedLevel3Values] = useState<string[]>([]);
  const [level3Values, setLevel3Values] = useState<string[]>([]);
  const [loadingValues, setLoadingValues] = useState<boolean>(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState<boolean>(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  // États pour les mappings
  const [mappings, setMappings] = useState<BilanMapping[]>([]);
  const [loadingMappings, setLoadingMappings] = useState<boolean>(false);
  
  // États pour la colonne "Level 1 (valeurs)"
  const [level1Values, setLevel1Values] = useState<string[]>([]);
  const [loadingLevel1Values, setLoadingLevel1Values] = useState<boolean>(false);
  const [openLevel1DropdownId, setOpenLevel1DropdownId] = useState<number | string | null>(null);
  const [level1DropdownPosition, setLevel1DropdownPosition] = useState<'bottom' | 'top'>('bottom');
  
  // État pour le repli/dépli de la card
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);
  
  // État pour la création d'une nouvelle catégorie
  const [isCreatingCategory, setIsCreatingCategory] = useState<boolean>(false);
  
  // États pour l'édition de la catégorie comptable (champ texte libre)
  const [editingCategoryNameId, setEditingCategoryNameId] = useState<number | null>(null);
  const [editingCategoryNameValue, setEditingCategoryNameValue] = useState<string>('');
  
  // États pour le menu contextuel (clic droit)
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; mappingId: number } | null>(null);
  const [isDeletingMapping, setIsDeletingMapping] = useState<number | null>(null);
  
  // État pour la réinitialisation
  const [isResetting, setIsResetting] = useState<boolean>(false);

  // Charger les valeurs Level 3 disponibles
  const loadLevel3Values = async () => {
    if (!isActive) return; // Ne pas charger si l'onglet n'est pas actif
    if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
      console.error('[BilanConfigCard] Property ID invalide pour loadLevel3Values');
      return;
    }
    
    try {
      setLoadingValues(true);
      const response = await transactionsAPI.getUniqueValues(activeProperty.id, 'level_3');
      const values = response.values || [];
      setLevel3Values(values);
    } catch (err: any) {
      console.error('Erreur lors du chargement des valeurs level_3:', err);
    } finally {
      setLoadingValues(false);
    }
  };

  // Charger la configuration (selected_level_3_values)
  const loadConfig = async () => {
    if (!isActive) return; // Ne pas charger si l'onglet n'est pas actif
    
    try {
      const config = await bilanAPI.getConfig();
      if (config.level_3_values) {
        try {
          const values = JSON.parse(config.level_3_values);
          if (Array.isArray(values)) {
            setSelectedLevel3Values(values);
            if (onLevel3Change) {
              onLevel3Change(values);
            }
          }
        } catch (e) {
          console.error('Erreur lors du parsing des level_3_values:', e);
        }
      }
    } catch (err: any) {
      console.error('Erreur lors du chargement de la configuration:', err);
    }
  };

  // Charger les mappings
  const loadMappings = async () => {
    if (!isActive) return; // Ne pas charger si l'onglet n'est pas actif
    
    try {
      setLoadingMappings(true);
      const response = await bilanAPI.getMappings();
      const loadedMappings = response.items || [];
      setMappings(loadedMappings);
    } catch (err: any) {
      console.error('Erreur lors du chargement des mappings:', err);
    } finally {
      setLoadingMappings(false);
    }
  };

  // Charger les valeurs Level 1 filtrées par Level 3
  const loadLevel1Values = async () => {
    if (!isActive) return; // Ne pas charger si l'onglet n'est pas actif
    if (selectedLevel3Values.length === 0) {
      setLevel1Values([]);
      return;
    }

    if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
      console.error('[BilanConfigCard] Property ID invalide pour loadLevel1Values');
      return;
    }
    try {
      setLoadingLevel1Values(true);
      // Ne charger que si on a vraiment besoin (éviter les appels inutiles)
      const response = await transactionsAPI.getUniqueValues(activeProperty.id, 'level_1', undefined, undefined, undefined, selectedLevel3Values);
      setLevel1Values(response.values || []);
    } catch (err: any) {
      console.error('Erreur lors du chargement des valeurs level_1:', err);
      setLevel1Values([]);
    } finally {
      setLoadingLevel1Values(false);
    }
  };

  // Charger les valeurs au montage (seulement si l'onglet est actif)
  useEffect(() => {
    // Toujours restaurer l'état collapsed depuis localStorage
    const savedCollapsed = localStorage.getItem(STORAGE_KEY_COLLAPSED);
    if (savedCollapsed !== null) {
      setIsCollapsed(savedCollapsed === 'true');
    }
    
    // Charger les données seulement si l'onglet est actif
    if (isActive) {
      loadLevel3Values();
      loadConfig();
      loadMappings();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Charger les level_1 quand les level_3 sélectionnés changent (seulement si l'onglet est actif)
  useEffect(() => {
    if (!isActive) return;
    
    // Utiliser un debounce pour éviter les appels trop fréquents
    const timeoutId = setTimeout(() => {
      if (isActive) {
        loadLevel1Values();
      }
    }, 500); // Attendre 500ms avant de charger
    
    return () => {
      clearTimeout(timeoutId);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedLevel3Values, isActive]);

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
      await bilanAPI.updateConfig({
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
        // Déterminer le type et la sous-catégorie par défaut
        const defaultType = 'ACTIF';
        const defaultSubCategory = 'Actif immobilisé';
        
        const newMapping = await bilanAPI.createMapping({
          category_name: categoryName,
          type: defaultType,
          sub_category: defaultSubCategory,
          level_1_values: JSON.stringify([level1Value]),
          is_special: false,
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
      await bilanAPI.updateMapping(mappingId, {
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

  // Gérer la création d'une nouvelle catégorie
  const handleCreateNewCategory = async () => {
    if (selectedLevel3Values.length === 0 || isCreatingCategory) {
      return;
    }

    try {
      setIsCreatingCategory(true);
      
      // Créer toujours un nouveau mapping avec "nouvelle categorie" par défaut
      const newMapping = await bilanAPI.createMapping({
        category_name: 'nouvelle categorie',
        type: 'ACTIF', // Type par défaut
        sub_category: 'Actif immobilisé', // Sous-catégorie par défaut
        level_1_values: null,
        is_special: false,
      });
      
      // Recharger les mappings
      await loadMappings();
      
      // Notifier le parent si nécessaire
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('Erreur lors de la création de la catégorie:', err);
      alert(`Erreur lors de la création: ${err.message || 'Erreur inconnue'}`);
    } finally {
      setIsCreatingCategory(false);
    }
  };

  // Gérer le début de l'édition de la catégorie comptable
  const handleCategoryNameEditStart = (mapping: BilanMapping) => {
    setEditingCategoryNameId(mapping.id);
    setEditingCategoryNameValue(mapping.category_name);
  };

  // Sauvegarder la catégorie comptable édité
  const handleCategoryNameEditSave = async (mappingId: number) => {
    const trimmedValue = editingCategoryNameValue.trim();
    if (!trimmedValue) {
      // Si vide, garder "nouvelle categorie"
      setEditingCategoryNameId(null);
      setEditingCategoryNameValue('');
      return;
    }
    
    try {
      await bilanAPI.updateMapping(mappingId, {
        category_name: trimmedValue,
      });
      
      // Recharger les mappings pour avoir la valeur à jour
      await loadMappings();
      
      setEditingCategoryNameId(null);
      setEditingCategoryNameValue('');
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('Erreur lors de la sauvegarde de la catégorie:', err);
      alert(`Erreur lors de la sauvegarde: ${err.message || 'Erreur inconnue'}`);
    }
  };

  // Annuler l'édition de la catégorie comptable
  const handleCategoryNameEditCancel = () => {
    setEditingCategoryNameId(null);
    setEditingCategoryNameValue('');
  };

  // Gérer les touches dans le champ d'édition de la catégorie
  const handleCategoryNameEditKeyDown = (e: React.KeyboardEvent, mappingId: number) => {
    if (e.key === 'Enter') {
      handleCategoryNameEditSave(mappingId);
    } else if (e.key === 'Escape') {
      handleCategoryNameEditCancel();
    }
  };

  // Gérer le changement de Type
  const handleTypeChange = async (mappingId: number, newType: string) => {
    try {
      const mapping = mappings.find(m => m.id === mappingId);
      if (!mapping) return;
      
      // Si le type change, réinitialiser la sous-catégorie à la première de la liste
      const newSubCategory = SUB_CATEGORIES_BY_TYPE[newType]?.[0] || mapping.sub_category;
      
      await bilanAPI.updateMapping(mappingId, {
        type: newType,
        sub_category: newSubCategory,
      });
      
      // Recharger les mappings pour avoir la valeur à jour
      await loadMappings();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('Erreur lors de la mise à jour du Type:', err);
      alert(`Erreur lors de la sauvegarde: ${err.message || 'Erreur inconnue'}`);
    }
  };

  // Gérer le changement de Sous-catégorie
  const handleSubCategoryChange = async (mappingId: number, newSubCategory: string) => {
    try {
      await bilanAPI.updateMapping(mappingId, {
        sub_category: newSubCategory,
      });
      
      // Recharger les mappings pour avoir la valeur à jour
      await loadMappings();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('Erreur lors de la mise à jour de la Sous-catégorie:', err);
      alert(`Erreur lors de la sauvegarde: ${err.message || 'Erreur inconnue'}`);
    }
  };

  // Gérer le changement de catégorie spéciale (is_special)
  const handleSpecialCategoryToggle = async (mappingId: number, isSpecial: boolean, specialSource?: string) => {
    try {
      await bilanAPI.updateMapping(mappingId, {
        is_special: isSpecial,
        special_source: isSpecial ? specialSource || null : null,
        level_1_values: isSpecial ? null : undefined, // Réinitialiser level_1_values si spécial
      });
      
      // Recharger les mappings pour avoir la valeur à jour
      await loadMappings();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('Erreur lors de la mise à jour de la catégorie spéciale:', err);
      alert(`Erreur lors de la sauvegarde: ${err.message || 'Erreur inconnue'}`);
    }
  };

  // Gérer le menu contextuel (clic droit)
  const handleContextMenu = (e: React.MouseEvent, mappingId: number) => {
    e.preventDefault();
    setContextMenu({
      x: e.clientX,
      y: e.clientY,
      mappingId: mappingId,
    });
  };

  // Fermer le menu contextuel
  const closeContextMenu = () => {
    setContextMenu(null);
  };

  // Fonction pour supprimer un mapping
  const handleDeleteMapping = async (mappingId: number) => {
    const mapping = mappings.find(m => m.id === mappingId);
    if (!mapping) return;

    if (!window.confirm(`Êtes-vous sûr de vouloir supprimer la catégorie "${mapping.category_name}" ?`)) {
      return;
    }

    try {
      setIsDeletingMapping(mappingId);
      closeContextMenu();

      await bilanAPI.deleteMapping(mappingId);

      console.log('[BilanConfigCard] Mapping supprimé:', mappingId);
      
      // Recharger les mappings depuis le serveur
      await loadMappings();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('Erreur lors de la suppression:', err);
      alert(`Erreur lors de la suppression: ${err.message || 'Erreur inconnue'}`);
    } finally {
      setIsDeletingMapping(null);
    }
  };

  // Fermer le menu contextuel quand on clique ailleurs
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

  // Fonction pour réinitialiser tous les mappings
  const handleResetMappings = async () => {
    if (mappings.length === 0) {
      alert('Aucun mapping à réinitialiser.');
      return;
    }

    const confirmed = window.confirm(
      `⚠️ Êtes-vous sûr de vouloir réinitialiser les mappings ?\n\nCette action supprimera ${mappings.length} mapping(s) et créera des mappings par défaut.`
    );

    if (!confirmed) {
      return;
    }

    try {
      setIsResetting(true);
      console.log(`[BilanConfigCard] Réinitialisation de ${mappings.length} mapping(s)...`);
      
      // Supprimer tous les mappings un par un
      const deletePromises = mappings.map(mapping => bilanAPI.deleteMapping(mapping.id));
      await Promise.all(deletePromises);
      
      console.log(`[BilanConfigCard] ✓ ${mappings.length} mapping(s) supprimé(s)`);
      
      // Créer les mappings par défaut
      console.log(`[BilanConfigCard] Création des mappings par défaut...`);
      
      const defaultMappings = [
        // ACTIF - Actif immobilisé
        {
          category_name: 'Immobilisations',
          type: 'ACTIF',
          sub_category: 'Actif immobilisé',
          level_1_values: null,
          is_special: false,
        },
        {
          category_name: 'Amortissements cumulés',
          type: 'ACTIF',
          sub_category: 'Actif immobilisé',
          level_1_values: null,
          is_special: true,
          special_source: 'amortizations',
        },
        // ACTIF - Actif circulant
        {
          category_name: 'Compte bancaire',
          type: 'ACTIF',
          sub_category: 'Actif circulant',
          level_1_values: null,
          is_special: true,
          special_source: 'transactions',
        },
        // PASSIF - Capitaux propres
        {
          category_name: 'Résultat de l\'exercice',
          type: 'PASSIF',
          sub_category: 'Capitaux propres',
          level_1_values: null,
          is_special: true,
          special_source: 'compte_resultat',
          compte_resultat_view_id: null,
        },
        {
          category_name: 'Report à nouveau / report du déficit',
          type: 'PASSIF',
          sub_category: 'Capitaux propres',
          level_1_values: null,
          is_special: true,
          special_source: 'compte_resultat_cumul',
        },
        {
          category_name: 'Souscription de parts sociales',
          type: 'PASSIF',
          sub_category: 'Capitaux propres',
          level_1_values: null,
          is_special: false,
        },
        {
          category_name: 'Compte courant d\'associé',
          type: 'PASSIF',
          sub_category: 'Capitaux propres',
          level_1_values: null,
          is_special: false,
        },
        // PASSIF - Dettes financières
        {
          category_name: 'Emprunt bancaire (capital restant dû)',
          type: 'PASSIF',
          sub_category: 'Dettes financières',
          level_1_values: null,
          is_special: true,
          special_source: 'loan_payments',
        },
        // PASSIF - Trésorerie passive
        {
          category_name: 'Cautions reçues',
          type: 'PASSIF',
          sub_category: 'Trésorerie passive',
          level_1_values: null,
          is_special: false,
        },
      ];
      
      const createPromises = defaultMappings.map(mapping => bilanAPI.createMapping(mapping));
      await Promise.all(createPromises);
      
      console.log(`[BilanConfigCard] ✓ ${defaultMappings.length} mapping(s) par défaut créé(s)`);
      
      // Recharger les mappings
      await loadMappings();
      
      alert(`✅ Réinitialisation réussie : ${mappings.length} mapping(s) supprimé(s) et ${defaultMappings.length} mapping(s) par défaut créé(s).`);
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('Erreur lors de la réinitialisation:', err);
      alert(`Erreur lors de la réinitialisation: ${err.message || 'Erreur inconnue'}`);
    } finally {
      setIsResetting(false);
    }
  };

  // Trier les mappings par Type puis Sous-catégorie puis Catégorie
  const sortedMappings = [...mappings].sort((a, b) => {
    // D'abord par Type (ACTIF avant PASSIF)
    if (a.type !== b.type) {
      if (a.type === 'ACTIF') return -1;
      if (b.type === 'ACTIF') return 1;
      return 0;
    }
    
    // Ensuite par Sous-catégorie
    if (a.sub_category !== b.sub_category) {
      return a.sub_category.localeCompare(b.sub_category);
    }
    
    // Enfin par Catégorie
    return a.category_name.localeCompare(b.category_name);
  });

  // Obtenir les sous-catégories disponibles pour un type donné
  const getSubCategoriesForType = (type: string): string[] => {
    return SUB_CATEGORIES_BY_TYPE[type] || [];
  };

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
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            flex: 1,
            cursor: 'pointer',
          }}
          onClick={toggleCollapse}
        >
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '600', color: '#111827' }}>
            Configuration du bilan
          </h3>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              toggleCollapse();
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '32px',
              height: '32px',
              padding: '0',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              backgroundColor: '#ffffff',
              cursor: 'pointer',
              fontSize: '16px',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#f9fafb';
              e.currentTarget.style.borderColor = '#9ca3af';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = '#ffffff';
              e.currentTarget.style.borderColor = '#d1d5db';
            }}
            title={isCollapsed ? 'Déplier la card' : 'Replier la card'}
          >
            {isCollapsed ? '📍' : '📌'}
          </button>
        </div>
        {!isCollapsed && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {mappings.length > 0 && (
              <button
                type="button"
                onClick={handleResetMappings}
                disabled={isResetting}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 16px',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: isResetting ? '#9ca3af' : '#374151',
                  backgroundColor: isResetting ? '#f3f4f6' : '#f9fafb',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  cursor: isResetting ? 'not-allowed' : 'pointer',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  if (!isResetting) {
                    e.currentTarget.style.backgroundColor = '#f3f4f6';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isResetting) {
                    e.currentTarget.style.backgroundColor = '#f9fafb';
                  }
                }}
              >
                {isResetting ? (
                  <>
                    <span>⏳</span>
                    <span>Réinitialisation...</span>
                  </>
                ) : (
                  <>
                    <span>🔄</span>
                    <span>Réinitialiser les mappings</span>
                  </>
                )}
              </button>
            )}
          </div>
        )}
      </div>
      
      {/* Contenu de la card (masqué si collapsed) */}
      {!isCollapsed && (
        <>
          {/* Champ Level 3 - Dropdown avec checkboxes */}
          <div style={{ marginBottom: '24px' }}>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '8px' }}>
              Level 3 (Valeur à considérer dans le bilan)
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
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151', width: '12%' }}>
                      Type
                    </th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151', width: '18%' }}>
                      Sous-catégorie
                    </th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151', width: '20%' }}>
                      Catégorie comptable
                    </th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151', width: '35%' }}>
                      Level 1 (valeurs)
                    </th>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151', width: '15%' }}>
                      Vue
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {loadingMappings ? (
                    <tr>
                      <td colSpan={5} style={{ padding: '20px', textAlign: 'center', color: '#6b7280' }}>
                        Chargement des mappings...
                      </td>
                    </tr>
                  ) : sortedMappings.length === 0 ? (
                    <tr>
                      <td colSpan={5} style={{ padding: '20px', textAlign: 'center', color: '#6b7280' }}>
                        Aucun mapping configuré. Cliquez sur "+ Ajouter une catégorie" pour commencer.
                      </td>
                    </tr>
                  ) : (
                    sortedMappings.map((mapping) => {
                      const isSpecial = mapping.is_special;
                      const needsView = isSpecial && SPECIAL_CATEGORIES_WITH_VIEW.includes(mapping.category_name);
                      
                      return (
                        <tr
                          key={mapping.id}
                          onContextMenu={!isSpecial ? (e) => handleContextMenu(e, mapping.id) : undefined}
                          style={{
                            borderBottom: '1px solid #e5e7eb',
                            cursor: !isSpecial ? 'context-menu' : 'default',
                          }}
                        >
                          {/* Colonne Type */}
                          <td style={{ padding: '12px', color: '#111827', width: '12%' }}>
                            <select
                              value={mapping.type}
                              onChange={(e) => handleTypeChange(mapping.id, e.target.value)}
                              style={{
                                padding: '4px 8px',
                                fontSize: '14px',
                                border: '1px solid #d1d5db',
                                borderRadius: '4px',
                                backgroundColor: '#ffffff',
                                color: '#111827',
                                cursor: 'pointer',
                                width: '100%',
                              }}
                            >
                              <option value="ACTIF">ACTIF</option>
                              <option value="PASSIF">PASSIF</option>
                            </select>
                          </td>
                          
                          {/* Colonne Sous-catégorie */}
                          <td style={{ padding: '12px', color: '#111827', width: '18%' }}>
                            <select
                              value={mapping.sub_category}
                              onChange={(e) => handleSubCategoryChange(mapping.id, e.target.value)}
                              style={{
                                padding: '4px 8px',
                                fontSize: '14px',
                                border: '1px solid #d1d5db',
                                borderRadius: '4px',
                                backgroundColor: '#ffffff',
                                color: '#111827',
                                cursor: 'pointer',
                                width: '100%',
                              }}
                            >
                              {getSubCategoriesForType(mapping.type).map(subCat => (
                                <option key={subCat} value={subCat}>{subCat}</option>
                              ))}
                            </select>
                          </td>
                          
                          {/* Colonne Catégorie comptable */}
                          <td style={{ padding: '12px', color: '#111827', width: '20%' }}>
                            {editingCategoryNameId === mapping.id ? (
                              <input
                                type="text"
                                value={editingCategoryNameValue}
                                onChange={(e) => setEditingCategoryNameValue(e.target.value)}
                                onBlur={() => handleCategoryNameEditSave(mapping.id)}
                                onKeyDown={(e) => handleCategoryNameEditKeyDown(e, mapping.id)}
                                autoFocus
                                style={{
                                  padding: '4px 8px',
                                  fontSize: '14px',
                                  border: '1px solid #3b82f6',
                                  borderRadius: '4px',
                                  outline: 'none',
                                  width: '100%',
                                }}
                              />
                            ) : (
                              <span
                                onClick={() => handleCategoryNameEditStart(mapping)}
                                style={{
                                  cursor: 'pointer',
                                  color: '#111827',
                                  textDecoration: 'underline',
                                  textDecorationStyle: 'dotted',
                                }}
                                title="Cliquer pour éditer"
                              >
                                {mapping.category_name}
                              </span>
                            )}
                          </td>
                          
                          {/* Colonne Level 1 (valeurs) */}
                          <td style={{ padding: '12px', color: '#111827', width: '35%' }}>
                            {isSpecial ? (
                              <span style={{ color: '#6b7280', fontStyle: 'italic' }}>
                                Données calculées
                              </span>
                            ) : (
                              <div style={{ position: 'relative' }} data-level1-dropdown>
                                {/* Tags des valeurs sélectionnées */}
                                {(() => {
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
                                            onClick={() => handleLevel1Remove(mapping.category_name, mapping.id, value)}
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
                                    const buttonRect = e.currentTarget.getBoundingClientRect();
                                    const viewportHeight = window.innerHeight;
                                    const shouldShowTop = buttonRect.bottom > viewportHeight / 2;
                                    setLevel1DropdownPosition(shouldShowTop ? 'top' : 'bottom');
                                    setOpenLevel1DropdownId(openLevel1DropdownId === mapping.id ? null : mapping.id);
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
                                {openLevel1DropdownId === mapping.id && (
                                  <div
                                    style={{
                                      position: 'absolute',
                                      ...(level1DropdownPosition === 'top' 
                                        ? { bottom: '100%', marginBottom: '4px', marginTop: 0 }
                                        : { top: '100%', marginTop: '4px', marginBottom: 0 }
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
                                      
                                      return availableValues.map((value) => {
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
                                        const isSelected = currentValues.includes(value);
                                        
                                        return (
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
                                              checked={isSelected}
                                              onChange={() => handleLevel1Toggle(mapping.category_name, value, mapping.id)}
                                              style={{
                                                width: '16px',
                                                height: '16px',
                                                cursor: 'pointer',
                                              }}
                                            />
                                            <span>{value}</span>
                                          </label>
                                        );
                                      });
                                    })()}
                                  </div>
                                )}
                              </div>
                            )}
                          </td>
                          
                          {/* Colonne Vue */}
                          <td style={{ padding: '12px', color: '#111827', width: '15%' }}>
                            {isSpecial ? (
                              needsView ? (
                                <span style={{ color: '#6b7280', fontStyle: 'italic' }}>
                                  Vue compte de résultat
                                </span>
                              ) : (
                                <span style={{ color: '#6b7280', fontStyle: 'italic' }}>
                                  Données calculées
                                </span>
                              )
                            ) : (
                              <span style={{ color: '#9ca3af' }}>—</span>
                            )}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
              
              {/* Bouton "+ Ajouter une catégorie" */}
              <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'flex-start' }}>
                <button
                  type="button"
                  onClick={handleCreateNewCategory}
                  disabled={isCreatingCategory || selectedLevel3Values.length === 0}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '8px 16px',
                    fontSize: '14px',
                    fontWeight: '500',
                    color: (isCreatingCategory || selectedLevel3Values.length === 0) ? '#9ca3af' : '#3b82f6',
                    backgroundColor: (isCreatingCategory || selectedLevel3Values.length === 0) ? '#f3f4f6' : '#eff6ff',
                    border: '1px solid',
                    borderColor: (isCreatingCategory || selectedLevel3Values.length === 0) ? '#d1d5db' : '#3b82f6',
                    borderRadius: '6px',
                    cursor: (isCreatingCategory || selectedLevel3Values.length === 0) ? 'not-allowed' : 'pointer',
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={(e) => {
                    if (!isCreatingCategory && selectedLevel3Values.length > 0) {
                      e.currentTarget.style.backgroundColor = '#dbeafe';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isCreatingCategory && selectedLevel3Values.length > 0) {
                      e.currentTarget.style.backgroundColor = '#eff6ff';
                    }
                  }}
                >
                  {isCreatingCategory ? (
                    <>
                      <span>⏳</span>
                      <span>Création...</span>
                    </>
                  ) : (
                    <>
                      <span>+</span>
                      <span>Ajouter une catégorie</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Menu contextuel */}
          {contextMenu && (
            <div
              style={{
                position: 'fixed',
                left: contextMenu.x,
                top: contextMenu.y,
                backgroundColor: '#ffffff',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                zIndex: 10000,
                minWidth: '150px',
              }}
            >
              <button
                type="button"
                onClick={() => {
                  if (contextMenu) {
                    handleDeleteMapping(contextMenu.mappingId);
                  }
                }}
                disabled={isDeletingMapping === contextMenu.mappingId}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  fontSize: '14px',
                  textAlign: 'left',
                  color: isDeletingMapping === contextMenu.mappingId ? '#9ca3af' : '#dc2626',
                  backgroundColor: 'transparent',
                  border: 'none',
                  cursor: isDeletingMapping === contextMenu.mappingId ? 'not-allowed' : 'pointer',
                  borderBottom: '1px solid #f3f4f6',
                }}
                onMouseEnter={(e) => {
                  if (isDeletingMapping !== contextMenu.mappingId) {
                    e.currentTarget.style.backgroundColor = '#fef2f2';
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }}
              >
                {isDeletingMapping === contextMenu.mappingId ? '⏳ Suppression...' : '🗑️ Supprimer'}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
