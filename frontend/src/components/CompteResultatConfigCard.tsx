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
import { useProperty } from '@/contexts/PropertyContext';

interface CompteResultatConfigCardProps {
  onConfigUpdated?: () => void;
  onLevel3Change?: (level3Values: string[]) => void;
  onLevel3ValuesLoaded?: (count: number) => void;
  onOverrideEnabledChange?: (enabled: boolean) => void;
}

const STORAGE_KEY_COLLAPSED = 'compte_resultat_config_collapsed';
const STORAGE_KEY_OVERRIDE_ENABLED = 'compte_resultat_override_enabled';

export default function CompteResultatConfigCard({
  onConfigUpdated,
  onLevel3Change,
  onLevel3ValuesLoaded,
  onOverrideEnabledChange,
}: CompteResultatConfigCardProps) {
  const { activeProperty: activePropertyOrNull } = useProperty();
  // Narrowed non-null property: chaque appelant garde ses propres garde-fous runtime
  // (activeProperty?.id, activeProperty.id <= 0, etc.) — cette assertion ne fait
  // que satisfaire TypeScript sans changer le comportement à l'exécution.
  const activeProperty = activePropertyOrNull as NonNullable<typeof activePropertyOrNull>;

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
  
  // État pour la checkbox "Override Resultat"
  const [isOverrideEnabled, setIsOverrideEnabled] = useState<boolean>(false);
  
  // Note: Le Type est maintenant stocké en backend dans le champ `type` du mapping

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
    isCustom: boolean; // true si la catégorie n'est pas dans les catégories prédéfinies
  }

  // Catégories prédéfinies avec leurs mappings
  const predefinedCategoriesWithMappings: CategoryRow[] = ALL_CATEGORIES.map(categoryName => ({
    categoryName,
    type: getTypeForCategory(categoryName),
    mapping: mappingsByCategory.get(categoryName) || null,
    isCustom: false,
  }));

  // Catégories personnalisées (mappings qui ne sont pas dans les catégories prédéfinies)
  const customCategories: CategoryRow[] = mappings
    .filter(mapping => !ALL_CATEGORIES.includes(mapping.category_name))
    .map(mapping => {
      // Récupérer le Type depuis le backend, ou utiliser "Charges d'exploitation" par défaut
      const type = (mapping.type as 'Produits d\'exploitation' | 'Charges d\'exploitation') || 'Charges d\'exploitation';
      return {
        categoryName: mapping.category_name,
        type,
        mapping,
        isCustom: true,
      };
    });

  // Combiner les deux listes
  const allCategoriesWithMappings: CategoryRow[] = [
    ...predefinedCategoriesWithMappings,
    ...customCategories,
  ];

  // Trier par Type puis par Catégorie
  const sortedCategories = [...allCategoriesWithMappings].sort((a, b) => {
    if (a.type !== b.type) {
      return a.type.localeCompare(b.type);
    }
    return a.categoryName.localeCompare(b.categoryName);
  });

  // Charger les valeurs Level 3 depuis l'API
  const loadLevel3Values = async () => {
    if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
      console.error('[CompteResultatConfigCard] Property ID invalide pour loadLevel3Values');
      return;
    }
    try {
      setLoadingValues(true);
      const response = await transactionsAPI.getUniqueValues(activeProperty.id, 'level_3');
      const values = response.values || [];
      setLevel3Values(values);
      setLevel3ValuesLoaded(true);

      // Notifier le parent du nombre de valeurs disponibles
      if (onLevel3ValuesLoaded) {
        onLevel3ValuesLoaded(values.length);
      }
      
      // Charger la configuration depuis l'API
      try {
        console.log('[CompteResultatConfigCard] loadLevel3Values - chargement config pour propertyId:', activeProperty.id);
        const config = await compteResultatAPI.getConfig(activeProperty.id);
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
            console.warn('[CompteResultatConfigCard] Configuration level_3_values invalide:', config.level_3_values);
          }
        }
      } catch (err) {
        console.error('[CompteResultatConfigCard] Erreur lors du chargement de la configuration:', err);
      }
      
      // Restaurer l'état collapsed depuis localStorage
      const savedCollapsed = localStorage.getItem(STORAGE_KEY_COLLAPSED);
      if (savedCollapsed !== null) {
        setIsCollapsed(savedCollapsed === 'true');
      }
      
      // Restaurer l'état override enabled depuis localStorage
      const savedOverrideEnabled = localStorage.getItem(STORAGE_KEY_OVERRIDE_ENABLED);
      if (savedOverrideEnabled !== null) {
        const overrideEnabled = savedOverrideEnabled === 'true';
        setIsOverrideEnabled(overrideEnabled);
        // Notifier le parent si nécessaire
        if (onOverrideEnabledChange) {
          onOverrideEnabledChange(overrideEnabled);
        }
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
    if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
      console.error('[CompteResultatConfigCard] Property ID invalide pour loadMappings');
      return;
    }
    try {
      setLoadingMappings(true);
      console.log('[CompteResultatConfigCard] loadMappings - propertyId:', activeProperty.id);
      const response = await compteResultatAPI.getMappings(activeProperty.id);
      const loadedMappings = response.items || [];
      setMappings(loadedMappings);
    } catch (err: any) {
      console.error('[CompteResultatConfigCard] Erreur lors du chargement des mappings:', err);
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

    if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
      console.error('[CompteResultatConfigCard] Property ID invalide pour loadLevel1Values');
      return;
    }
    try {
      setLoadingLevel1Values(true);
      const response = await transactionsAPI.getUniqueValues(activeProperty.id, 'level_1', undefined, undefined, undefined, selectedLevel3Values);
      setLevel1Values(response.values || []);
    } catch (err: any) {
      console.error('Erreur lors du chargement des valeurs level_1:', err);
      setLevel1Values([]);
    } finally {
      setLoadingLevel1Values(false);
    }
  };

  // Charger les valeurs quand la propriété active change
  useEffect(() => {
    if (activeProperty?.id && activeProperty.id > 0) {
      console.log('[CompteResultatConfigCard] Chargement des données pour propertyId:', activeProperty.id);
      loadLevel3Values();
      loadMappings();
    }
  }, [activeProperty?.id]);

  // Charger les level_1 quand les level_3 sélectionnés changent
  useEffect(() => {
    loadLevel1Values();
  }, [selectedLevel3Values, activeProperty?.id]);

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
    if (!activeProperty?.id || activeProperty.id <= 0) {
      console.error('[CompteResultatConfigCard] Property ID invalide pour updateConfig');
      return;
    }
    try {
      console.log('[CompteResultatConfigCard] handleLevel3CheckboxChange - propertyId:', activeProperty.id);
      await compteResultatAPI.updateConfig(activeProperty.id, {
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
    if (!activeProperty?.id || activeProperty.id <= 0) {
      console.error('[CompteResultatConfigCard] Property ID invalide pour handleLevel1Toggle');
      return;
    }
    
    // Si pas de mappingId, créer le mapping d'abord
    if (!mappingId) {
      try {
        console.log('[CompteResultatConfigCard] createMapping - propertyId:', activeProperty.id);
        const newMapping = await compteResultatAPI.createMapping(activeProperty.id, {
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
        console.error('[CompteResultatConfigCard] Erreur lors de la création du mapping:', err);
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
      console.log('[CompteResultatConfigCard] updateMapping level_1 - propertyId:', activeProperty.id, 'mappingId:', mappingId);
      await compteResultatAPI.updateMapping(activeProperty.id, mappingId, {
        level_1_values: JSON.stringify(newValues),
      });
      
      // Recharger les mappings pour avoir la valeur à jour
      await loadMappings();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('[CompteResultatConfigCard] Erreur lors de la mise à jour des valeurs level_1:', err);
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

  // Gérer la création d'une nouvelle catégorie
  const handleCreateNewCategory = async () => {
    if (selectedLevel3Values.length === 0 || isCreatingCategory) {
      return;
    }
    if (!activeProperty?.id || activeProperty.id <= 0) {
      console.error('[CompteResultatConfigCard] Property ID invalide pour handleCreateNewCategory');
      return;
    }

    try {
      setIsCreatingCategory(true);
      
      console.log('[CompteResultatConfigCard] createMapping nouvelle catégorie - propertyId:', activeProperty.id);
      // Créer toujours un nouveau mapping avec "nouvelle categorie" par défaut
      const newMapping = await compteResultatAPI.createMapping(activeProperty.id, {
        category_name: 'nouvelle categorie',
        type: 'Charges d\'exploitation', // Type par défaut
        level_1_values: null,
      });
      
      // Le Type est stocké en backend, pas besoin d'initialiser en frontend
      
      // Recharger les mappings
      await loadMappings();
      
      // Notifier le parent si nécessaire
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('[CompteResultatConfigCard] Erreur lors de la création de la catégorie:', err);
      alert(`Erreur lors de la création: ${err.message || 'Erreur inconnue'}`);
    } finally {
      setIsCreatingCategory(false);
    }
  };

  // Gérer le début de l'édition de la catégorie comptable
  const handleCategoryNameEditStart = (mapping: CompteResultatMapping) => {
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
    if (!activeProperty?.id || activeProperty.id <= 0) {
      console.error('[CompteResultatConfigCard] Property ID invalide pour handleCategoryNameEditSave');
      return;
    }
    
    try {
      console.log('[CompteResultatConfigCard] updateMapping category_name - propertyId:', activeProperty.id);
      await compteResultatAPI.updateMapping(activeProperty.id, mappingId, {
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
      console.error('[CompteResultatConfigCard] Erreur lors de la sauvegarde de la catégorie:', err);
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

  // Gérer le changement de Type (stocké en backend)
  const handleTypeChange = async (mappingId: number, newType: 'Produits d\'exploitation' | 'Charges d\'exploitation') => {
    if (!activeProperty?.id || activeProperty.id <= 0) {
      console.error('[CompteResultatConfigCard] Property ID invalide pour handleTypeChange');
      return;
    }
    try {
      console.log('[CompteResultatConfigCard] updateMapping type - propertyId:', activeProperty.id);
      await compteResultatAPI.updateMapping(activeProperty.id, mappingId, {
        type: newType,
      });
      
      // Recharger les mappings pour avoir la valeur à jour
      await loadMappings();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('[CompteResultatConfigCard] Erreur lors de la mise à jour du Type:', err);
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
    if (!activeProperty?.id || activeProperty.id <= 0) {
      console.error('[CompteResultatConfigCard] Property ID invalide pour handleDeleteMapping');
      return;
    }
    
    const mapping = mappings.find(m => m.id === mappingId);
    if (!mapping) return;

    if (!window.confirm(`Êtes-vous sûr de vouloir supprimer la catégorie "${mapping.category_name}" ?`)) {
      return;
    }

    try {
      setIsDeletingMapping(mappingId);
      closeContextMenu();

      console.log('[CompteResultatConfigCard] deleteMapping - propertyId:', activeProperty.id, 'mappingId:', mappingId);
      await compteResultatAPI.deleteMapping(activeProperty.id, mappingId);

      console.log('[CompteResultatConfigCard] Mapping supprimé:', mappingId);
      
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
    if (!activeProperty?.id || activeProperty.id <= 0) {
      console.error('[CompteResultatConfigCard] Property ID invalide pour handleResetMappings');
      return;
    }
    
    if (mappings.length === 0) {
      alert('Aucun mapping à réinitialiser.');
      return;
    }

    const confirmed = window.confirm(
      `⚠️ Êtes-vous sûr de vouloir réinitialiser les mappings ?\n\nCette action supprimera ${mappings.length} mapping(s). Cette action est irréversible.`
    );

    if (!confirmed) {
      return;
    }

    try {
      setIsResetting(true);
      console.log(`[CompteResultatConfigCard] Réinitialisation de ${mappings.length} mapping(s) pour propertyId:`, activeProperty.id);
      
      // Supprimer tous les mappings un par un
      const deletePromises = mappings.map(mapping => compteResultatAPI.deleteMapping(activeProperty.id, mapping.id));
      await Promise.all(deletePromises);
      
      console.log(`[CompteResultatConfigCard] ✓ ${mappings.length} mapping(s) supprimé(s)`);
      
      // Recharger les mappings (la liste sera vide maintenant)
      await loadMappings();
      
      alert(`✅ Réinitialisation réussie : ${mappings.length} mapping(s) supprimé(s).`);
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('[CompteResultatConfigCard] Erreur lors de la réinitialisation:', err);
      alert(`Erreur lors de la réinitialisation: ${err.message || 'Erreur inconnue'}`);
    } finally {
      setIsResetting(false);
    }
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
            Configuration du compte de résultat
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
            {/* Checkbox "Override Resultat" */}
            <label
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '14px',
                fontWeight: '500',
                color: isOverrideEnabled ? '#1e3a5f' : '#6b7280',
                cursor: 'pointer',
                padding: '8px 12px',
                borderRadius: '6px',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#f3f4f6';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent';
              }}
              title={isOverrideEnabled ? "Cliquer pour désactiver" : "Cliquer pour activer"}
            >
              <input
                type="checkbox"
                checked={isOverrideEnabled}
                onChange={async (e) => {
                  const newValue = e.target.checked;
                  
                  // Si on désélectionne, supprimer tous les overrides en BDD
                  if (!newValue && isOverrideEnabled) {
                    const confirmMessage = 'Êtes-vous sûr de vouloir désactiver l\'override ?\n\nTous les overrides enregistrés seront supprimés.';
                    if (!window.confirm(confirmMessage)) {
                      return; // Annuler si l'utilisateur ne confirme pas
                    }
                    
                    try {
                      // Récupérer tous les overrides et les supprimer
                      const allOverrides = await compteResultatAPI.getOverrides(activeProperty.id);
                      const deletePromises = allOverrides.map(override =>
                        compteResultatAPI.deleteOverride(activeProperty.id, override.year)
                      );
                      await Promise.all(deletePromises);
                      console.log(`✅ ${allOverrides.length} override(s) supprimé(s)`);
                    } catch (err: any) {
                      console.error('Erreur lors de la suppression des overrides:', err);
                      alert('Erreur lors de la suppression des overrides. Veuillez réessayer.');
                      return; // Ne pas changer l'état si erreur
                    }
                  }
                  
                  setIsOverrideEnabled(newValue);
                  localStorage.setItem(STORAGE_KEY_OVERRIDE_ENABLED, newValue ? 'true' : 'false');
                  if (onOverrideEnabledChange) {
                    onOverrideEnabledChange(newValue);
                  }
                }}
                style={{
                  width: '16px',
                  height: '16px',
                  cursor: 'pointer',
                }}
              />
              <span>Override Resultat</span>
            </label>
            
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
                      const { categoryName, type, mapping, isCustom } = categoryRow;
                      const isSpecialCategory = SPECIAL_CATEGORIES.includes(categoryName);
                      const key = mapping ? `mapping-${mapping.id}` : `category-${categoryName}`;
                      
                      // Pour les catégories personnalisées, récupérer le Type depuis le backend
                      const currentType = mapping && isCustom 
                        ? ((mapping.type as 'Produits d\'exploitation' | 'Charges d\'exploitation') || 'Charges d\'exploitation')
                        : type;
                      
                      return (
                        <tr
                          key={key}
                          onContextMenu={mapping && !isSpecialCategory ? (e) => handleContextMenu(e, mapping.id) : undefined}
                          style={{
                            borderBottom: '1px solid #e5e7eb',
                            cursor: mapping && !isSpecialCategory ? 'context-menu' : 'default',
                          }}
                        >
                          <td style={{ padding: '12px', color: '#111827', width: '20%' }}>
                            {isCustom && mapping ? (
                              <select
                                value={currentType}
                                onChange={(e) => handleTypeChange(mapping.id, e.target.value as 'Produits d\'exploitation' | 'Charges d\'exploitation')}
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
                                <option value="Produits d'exploitation">Produits d'exploitation</option>
                                <option value="Charges d'exploitation">Charges d'exploitation</option>
                              </select>
                            ) : (
                              type
                            )}
                          </td>
                          <td style={{ padding: '12px', color: '#111827', width: '30%' }}>
                            {isCustom && mapping && editingCategoryNameId === mapping.id ? (
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
                            ) : isCustom && mapping ? (
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
                                {categoryName}
                              </span>
                            ) : (
                              categoryName
                            )}
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
                  {/* Ligne pour le bouton "+" Ajouter une catégorie */}
                  <tr>
                    <td colSpan={3} style={{ padding: '12px', textAlign: 'center', borderTop: '2px solid #e5e7eb' }}>
                      <button
                        onClick={handleCreateNewCategory}
                        disabled={selectedLevel3Values.length === 0 || isCreatingCategory}
                        style={{
                          padding: '8px 16px',
                          backgroundColor: selectedLevel3Values.length > 0 && !isCreatingCategory ? '#3b82f6' : '#9ca3af',
                          color: 'white',
                          border: 'none',
                          borderRadius: '6px',
                          cursor: selectedLevel3Values.length > 0 && !isCreatingCategory ? 'pointer' : 'not-allowed',
                          fontSize: '14px',
                          fontWeight: '500',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          transition: 'background-color 0.2s',
                        }}
                        onMouseEnter={(e) => {
                          if (selectedLevel3Values.length > 0 && !isCreatingCategory) {
                            e.currentTarget.style.backgroundColor = '#2563eb';
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (selectedLevel3Values.length > 0 && !isCreatingCategory) {
                            e.currentTarget.style.backgroundColor = '#3b82f6';
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
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {/* Menu contextuel (clic droit) */}
          {contextMenu && (
            <div
              style={{
                position: 'fixed',
                top: `${contextMenu.y}px`,
                left: `${contextMenu.x}px`,
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
                zIndex: 1000,
                minWidth: '150px',
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <button
                onClick={() => handleDeleteMapping(contextMenu.mappingId)}
                disabled={isDeletingMapping === contextMenu.mappingId}
                style={{
                  width: '100%',
                  padding: '10px 16px',
                  textAlign: 'left',
                  backgroundColor: 'transparent',
                  border: 'none',
                  cursor: isDeletingMapping === contextMenu.mappingId ? 'not-allowed' : 'pointer',
                  color: isDeletingMapping === contextMenu.mappingId ? '#9ca3af' : '#dc2626',
                  fontSize: '14px',
                  fontWeight: '500',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  transition: 'background-color 0.2s',
                }}
                onMouseEnter={(e) => {
                  if (isDeletingMapping !== contextMenu.mappingId) {
                    e.currentTarget.style.backgroundColor = '#fef2f2';
                  }
                }}
                onMouseLeave={(e) => {
                  if (isDeletingMapping !== contextMenu.mappingId) {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }
                }}
              >
                {isDeletingMapping === contextMenu.mappingId ? (
                  <>
                    <span>⏳</span>
                    <span>Suppression...</span>
                  </>
                ) : (
                  <>
                    <span>🗑️</span>
                    <span>Supprimer</span>
                  </>
                )}
              </button>
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
