/**
 * CompteResultatConfigCard component - Card de configuration du compte de résultat
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { compteResultatAPI, CompteResultatMapping, transactionsAPI, compteResultatMappingViewsAPI, CompteResultatMappingView, amortizationViewsAPI, loanConfigsAPI, LoanConfig, allowedMappingsAPI } from '@/api/client';

interface CompteResultatConfigCardProps {
  onConfigUpdated?: () => void;
}

type TypeValue = 'Produits d\'exploitation' | 'Charges d\'exploitation';

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
  'Charges d\'amortissements',
  'Autres charges diverses',
  'Coût du financement (hors remboursement du capital)',
];

// Catégories spéciales (données calculées, pas de mapping level_1/level_2)
const SPECIAL_CATEGORIES = [
  'Charges d\'amortissements',
  'Coût du financement (hors remboursement du capital)',
];

// Fonction pour déduire le type selon la catégorie
function getTypeForCategory(categoryName: string): 'Produits d\'exploitation' | 'Charges d\'exploitation' {
  if (PRODUITS_CATEGORIES.includes(categoryName)) {
    return 'Produits d\'exploitation';
  }
  return 'Charges d\'exploitation';
}

// Fonction pour vérifier si une catégorie est spéciale
function isSpecialCategory(categoryName: string): boolean {
  return SPECIAL_CATEGORIES.includes(categoryName);
}

export default function CompteResultatConfigCard({ onConfigUpdated }: CompteResultatConfigCardProps) {
  const [mappings, setMappings] = useState<CompteResultatMapping[]>([]);
  const [loading, setLoading] = useState(false);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; mappingId: number } | null>(null);
  // État pour stocker le Type de chaque mapping (pas stocké en backend, uniquement frontend)
  const [mappingTypes, setMappingTypes] = useState<Record<number, TypeValue>>({});
  // États pour gérer les valeurs level_1 (Step 7.5.5)
  const [level1Values, setLevel1Values] = useState<string[]>([]);
  const [editingLevel1Id, setEditingLevel1Id] = useState<number | null>(null);
  // États pour gérer la sélection des level_3 à inclure (Step 9.2)
  const [selectedLevel3Values, setSelectedLevel3Values] = useState<string[]>([]);
  const [availableLevel3Values, setAvailableLevel3Values] = useState<string[]>([]);
  const [loadingLevel3Values, setLoadingLevel3Values] = useState(false);
  const [showLevel3Dropdown, setShowLevel3Dropdown] = useState(false);
  const level3DropdownRef = useRef<HTMLDivElement>(null);
  // États pour gérer les vues (Save/Load/Delete) (Step 7.5.10)
  const [isViewMenuOpen, setIsViewMenuOpen] = useState(false);
  const [showSaveViewPopup, setShowSaveViewPopup] = useState(false);
  const [saveViewName, setSaveViewName] = useState('');
  const [showLoadViewPopup, setShowLoadViewPopup] = useState(false);
  const [availableViews, setAvailableViews] = useState<Array<{ id: number; name: string }>>([]);
  const [loadingViews, setLoadingViews] = useState(false);
  const [loadingView, setLoadingView] = useState(false);
  const [selectedViewId, setSelectedViewId] = useState<number | null>(null);
  const [showDeleteViewPopup, setShowDeleteViewPopup] = useState(false);
  const [availableViewsForDelete, setAvailableViewsForDelete] = useState<Array<{ id: number; name: string }>>([]);
  const [loadingViewsForDelete, setLoadingViewsForDelete] = useState(false);
  const [selectedViewIdForDelete, setSelectedViewIdForDelete] = useState<number | null>(null);
  const viewMenuRef = useRef<HTMLDivElement>(null);
  // États pour gérer les vues d'amortissement (Step 7.5.11)
  const [amortizationViews, setAmortizationViews] = useState<Array<{ id: number; name: string; level_2_value: string }>>([]);
  const [loadingAmortizationViews, setLoadingAmortizationViews] = useState(false);
  // États pour gérer les crédits (Step 7.5.12)
  const [loanConfigs, setLoanConfigs] = useState<LoanConfig[]>([]);
  const [loadingLoanConfigs, setLoadingLoanConfigs] = useState(false);
  const [showLoanDropdown, setShowLoanDropdown] = useState<number | null>(null); // ID du mapping pour lequel le dropdown est ouvert
  const loanDropdownRef = useRef<HTMLDivElement>(null);
  // État pour gérer le repli/dépli de la card (Step 7.6.8)
  const [isCollapsed, setIsCollapsed] = useState<boolean>(() => {
    // Charger l'état depuis localStorage au montage
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('compteResultatConfigCard_collapsed');
      return saved === 'true';
    }
    return false;
  });

  // Sauvegarder l'état dans localStorage quand il change (Step 7.6.8)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('compteResultatConfigCard_collapsed', String(isCollapsed));
    }
  }, [isCollapsed]);

  // Charger les mappings et les valeurs level_1 au montage
  useEffect(() => {
    loadMappings();
    loadLevel1Values();
    loadAvailableLevel3Values();
    loadAmortizationViews();
    loadLoanConfigs();
  }, []);

  // Recharger les level_1 quand la sélection de level_3 change (Step 9.3)
  useEffect(() => {
    loadLevel1Values();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedLevel3Values]);

  // Charger les vues d'amortissement (Step 7.5.11)
  const loadAmortizationViews = async () => {
    try {
      setLoadingAmortizationViews(true);
      // Récupérer toutes les vues d'amortissement (sans filtre level_2)
      // Note: On récupère toutes les vues, puis on les regroupe par level_2_value si nécessaire
      const allViews: Array<{ id: number; name: string; level_2_value: string }> = [];
      
      // Récupérer tous les level_2_values uniques depuis les transactions
      const level2Response = await transactionsAPI.getUniqueValues('level_2');
      const level2Values = level2Response.values || [];
      
      // Pour chaque level_2, récupérer les vues
      for (const level2 of level2Values) {
        try {
          const viewsResponse = await amortizationViewsAPI.getAll(level2);
          viewsResponse.views.forEach(view => {
            allViews.push({
              id: view.id,
              name: view.name,
              level_2_value: view.level_2_value
            });
          });
        } catch (err) {
          console.warn(`⚠️ [CompteResultatConfigCard] Erreur lors du chargement des vues pour ${level2}:`, err);
        }
      }
      
      setAmortizationViews(allViews);
      console.log('✅ [CompteResultatConfigCard] Vues d\'amortissement chargées:', allViews.length);
    } catch (err: any) {
      console.error('❌ [CompteResultatConfigCard] Erreur lors du chargement des vues d\'amortissement:', err);
    } finally {
      setLoadingAmortizationViews(false);
    }
  };

  // Charger les crédits configurés (Step 7.5.12)
  const loadLoanConfigs = async () => {
    try {
      setLoadingLoanConfigs(true);
      const response = await loanConfigsAPI.getAll();
      setLoanConfigs(response.configs || []);
      console.log('✅ [CompteResultatConfigCard] Crédits chargés:', response.configs.length);
    } catch (err: any) {
      console.error('❌ [CompteResultatConfigCard] Erreur lors du chargement des crédits:', err);
      setLoanConfigs([]);
    } finally {
      setLoadingLoanConfigs(false);
    }
  };

  // Gérer le changement de sélection des crédits (Step 7.5.12)
  const handleLoanSelectionChange = async (mappingId: number, loanId: number, checked: boolean) => {
    try {
      const mapping = mappings.find(m => m.id === mappingId);
      if (!mapping) return;

      const currentSelectedIds = mapping.selected_loan_ids || [];
      let newSelectedIds: number[];

      if (checked) {
        // Ajouter le crédit à la sélection
        newSelectedIds = [...currentSelectedIds, loanId];
      } else {
        // Retirer le crédit de la sélection
        newSelectedIds = currentSelectedIds.filter(id => id !== loanId);
      }

      console.log('🔄 [CompteResultatConfigCard] Changement de sélection de crédits:', { mappingId, loanId, checked, newSelectedIds });
      
      await compteResultatAPI.updateMapping(mappingId, {
        selected_loan_ids: newSelectedIds.length > 0 ? newSelectedIds : null,
      });
      
      console.log('✅ [CompteResultatConfigCard] Sélection de crédits mise à jour avec succès');
      
      // Recharger les mappings
      await loadMappings();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [CompteResultatConfigCard] Erreur lors de la mise à jour de la sélection de crédits:', err);
      alert(`❌ Erreur lors de la mise à jour: ${err.message || 'Erreur inconnue'}`);
    }
  };

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

  // Fermer le dropdown de crédits au clic ailleurs (Step 7.5.12)
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (showLoanDropdown !== null) {
        const target = event.target as HTMLElement;
        if (!target.closest('[data-loan-dropdown]')) {
          setShowLoanDropdown(null);
        }
      }
    };

    if (showLoanDropdown !== null) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [showLoanDropdown]);

  // Fermer le dropdown Level 3 au clic ailleurs (Step 9.2)
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (showLevel3Dropdown && level3DropdownRef.current) {
        const target = event.target as HTMLElement;
        if (!level3DropdownRef.current.contains(target)) {
          setShowLevel3Dropdown(false);
        }
      }
    };

    if (showLevel3Dropdown) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [showLevel3Dropdown]);

  // Recharger les crédits quand onConfigUpdated est appelé (Step 7.5.12)
  // Cela permet de mettre à jour la liste des crédits si un crédit est ajouté/supprimé ailleurs
  useEffect(() => {
    if (onConfigUpdated) {
      // Recharger les crédits après un court délai pour laisser le temps aux autres composants de se mettre à jour
      const timeout = setTimeout(() => {
        loadLoanConfigs();
      }, 500);
      return () => clearTimeout(timeout);
    }
  }, [onConfigUpdated]);

  // Fermer le menu View au clic ailleurs (Step 7.5.10)
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (viewMenuRef.current && !viewMenuRef.current.contains(event.target as Node)) {
        setIsViewMenuOpen(false);
      }
    };

    if (isViewMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isViewMenuOpen]);

  const loadMappings = async () => {
    try {
      setLoading(true);
      const response = await compteResultatAPI.getMappings();
      const loadedMappings = response.mappings || [];
      console.log('🔄 [CompteResultatConfigCard] Mappings rechargés:', loadedMappings);
      setMappings(loadedMappings);
      
      // Initialiser les Types pour chaque mapping (déduit selon la catégorie)
      const initialTypes: Record<number, TypeValue> = {};
      loadedMappings.forEach(mapping => {
        initialTypes[mapping.id] = getTypeForCategory(mapping.category_name);
        console.log(`🔍 [CompteResultatConfigCard] Mapping ${mapping.id} - level_1_values:`, mapping.level_1_values);
      });
      setMappingTypes(initialTypes);
    } catch (err: any) {
      console.error('❌ Erreur lors du chargement des mappings:', err);
      alert(`❌ Erreur lors du chargement des mappings: ${err.message || 'Erreur inconnue'}`);
    } finally {
      setLoading(false);
    }
  };

  // Gérer le changement de Type (Step 7.5.3)
  const handleTypeChange = async (mappingId: number, newType: TypeValue) => {
    const mapping = mappings.find(m => m.id === mappingId);
    if (!mapping) return;

    // Vérifier si la catégorie actuelle est valide pour le nouveau Type
    const availableCategories = getAvailableCategoriesForType(newType);
    const currentCategoryValid = availableCategories.includes(mapping.category_name);

    // Mettre à jour le Type dans l'état local
    setMappingTypes(prev => ({
      ...prev,
      [mappingId]: newType
    }));

    // Si la catégorie actuelle n'est plus valide, la réinitialiser à la première catégorie du nouveau Type
    if (!currentCategoryValid) {
      const newCategory = availableCategories[0];
      console.log(`🔄 [CompteResultatConfigCard] Type changé, réinitialisation de la catégorie à:`, newCategory);
      await handleCategoryChange(mappingId, newCategory);
    }
  };

  // Obtenir les catégories disponibles selon le Type (Step 7.5.4)
  const getAvailableCategoriesForType = (type: TypeValue): string[] => {
    if (type === 'Produits d\'exploitation') {
      return PRODUITS_CATEGORIES;
    }
    return CHARGES_CATEGORIES;
  };

  // Charger les valeurs level_1 disponibles depuis les transactions enrichies (Step 7.5.5)
  // Charger les valeurs level_1 filtrées par les level_3 sélectionnés ET qui existent dans les transactions (Step 9.3)
  const loadLevel1Values = async () => {
    try {
      // Si aucun level_3 n'est sélectionné, ne pas charger de valeurs
      if (selectedLevel3Values.length === 0) {
        console.log('⚠️ [CompteResultatConfigCard] Aucun level_3 sélectionné, pas de chargement de level_1');
        setLevel1Values([]);
        return;
      }

      console.log('🔍 [CompteResultatConfigCard] Chargement des valeurs level_1 filtrées par level_3:', selectedLevel3Values);
      
      // 1. Récupérer les level_1 autorisés pour les level_3 sélectionnés
      const allowedLevel1Values = await allowedMappingsAPI.getAllowedLevel1ForLevel3List(selectedLevel3Values);
      console.log('✅ [CompteResultatConfigCard] Level_1 autorisés:', allowedLevel1Values);
      
      // 2. Récupérer les level_1 qui existent réellement dans les transactions enrichies
      const transactionLevel1Response = await transactionsAPI.getUniqueValues('level_1');
      const transactionLevel1Values = transactionLevel1Response.values || [];
      console.log('✅ [CompteResultatConfigCard] Level_1 dans les transactions:', transactionLevel1Values);
      
      // 3. Faire l'intersection : garder uniquement les level_1 qui sont à la fois autorisés ET dans les transactions
      const filteredValues = allowedLevel1Values.filter(level1 => transactionLevel1Values.includes(level1));
      console.log('✅ [CompteResultatConfigCard] Level_1 filtrés (autorisés ET dans transactions):', filteredValues);
      
      setLevel1Values(filteredValues);
      console.log('✅ [CompteResultatConfigCard] Nombre de valeurs level_1 chargées:', filteredValues.length);
    } catch (err: any) {
      console.error('❌ [CompteResultatConfigCard] Erreur lors du chargement des valeurs level_1:', err);
      // Ne pas afficher d'alerte, juste logger l'erreur pour ne pas bloquer l'interface
      setLevel1Values([]);
    }
  };

  // Charger toutes les valeurs level_3 disponibles (Step 9.2)
  const loadAvailableLevel3Values = async () => {
    try {
      setLoadingLevel3Values(true);
      console.log('🔍 [CompteResultatConfigCard] Chargement des valeurs level_3 disponibles...');
      const values = await allowedMappingsAPI.getAllowedLevel3();
      console.log('✅ [CompteResultatConfigCard] Valeurs level_3 reçues:', values);
      setAvailableLevel3Values(values);
      console.log('✅ [CompteResultatConfigCard] Nombre de valeurs level_3 chargées:', values.length);
    } catch (err: any) {
      console.error('❌ [CompteResultatConfigCard] Erreur lors du chargement des valeurs level_3:', err);
      setAvailableLevel3Values([]);
    } finally {
      setLoadingLevel3Values(false);
    }
  };

  // Gérer le changement de catégorie comptable (Step 7.5.4)
  const handleCategoryChange = async (mappingId: number, newCategory: string) => {
    const mapping = mappings.find(m => m.id === mappingId);
    if (!mapping) return;

    try {
      console.log(`🔄 [CompteResultatConfigCard] Mise à jour de la catégorie pour le mapping ${mappingId}:`, newCategory);
      
      // Mettre à jour le mapping via l'API
      await compteResultatAPI.updateMapping(mappingId, {
        category_name: newCategory,
        // Conserver les valeurs existantes
        level_1_values: mapping.level_1_values,
        level_2_values: [],
        level_3_values: null,
      });
      
      console.log('✅ [CompteResultatConfigCard] Catégorie mise à jour avec succès');
      
      // Recharger les mappings pour avoir les données à jour
      await loadMappings();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [CompteResultatConfigCard] Erreur lors de la mise à jour de la catégorie:', err);
      alert(`❌ Erreur lors de la mise à jour: ${err.message || 'Erreur inconnue'}`);
    }
  };

  // Ajouter une valeur level_1 (Step 7.5.5)
  const handleLevel1Add = async (mappingId: number, value: string) => {
    if (!value) return;
    
    const mapping = mappings.find(m => m.id === mappingId);
    if (!mapping) return;
    
    // Vérifier que la valeur n'est pas déjà présente
    const currentValues = mapping.level_1_values && Array.isArray(mapping.level_1_values) ? mapping.level_1_values : [];
    if (currentValues.includes(value)) return;
    
    try {
      const updatedValues = [...currentValues, value];
      console.log('💾 [CompteResultatConfigCard] Ajout de valeur level_1:', value, 'pour mapping:', mappingId, '→', updatedValues);
      
      await compteResultatAPI.updateMapping(mappingId, {
        category_name: mapping.category_name,
        level_1_values: updatedValues,
        level_2_values: [],
        level_3_values: null,
      });
      
      console.log('✅ [CompteResultatConfigCard] Valeur level_1 ajoutée avec succès');
      
      // Recharger les mappings
      await loadMappings();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [CompteResultatConfigCard] Erreur lors de l\'ajout de la valeur level_1:', err);
      alert(`❌ Erreur lors de l'ajout: ${err.message || 'Erreur inconnue'}`);
    }
  };

  // Supprimer une valeur level_1 (Step 7.5.5)
  const handleLevel1Remove = async (mappingId: number, value: string) => {
    console.log('🗑️ [CompteResultatConfigCard] handleLevel1Remove appelé avec:', { mappingId, value });
    const mapping = mappings.find(m => m.id === mappingId);
    if (!mapping) {
      console.error('❌ [CompteResultatConfigCard] Mapping non trouvé:', mappingId);
      alert(`❌ Mapping non trouvé pour l'ID: ${mappingId}`);
      return;
    }
    
    try {
      const currentValues = mapping.level_1_values && Array.isArray(mapping.level_1_values) ? mapping.level_1_values : [];
      console.log('🔍 [CompteResultatConfigCard] Valeurs actuelles level_1:', currentValues);
      console.log('🔍 [CompteResultatConfigCard] Valeur à supprimer:', value);
      const updatedValues = currentValues.filter(v => v !== value);
      console.log('🔍 [CompteResultatConfigCard] Valeurs après filtrage:', updatedValues);
      console.log('🗑️ [CompteResultatConfigCard] Suppression de valeur level_1:', value, 'pour mapping:', mappingId, '→', updatedValues);
      
      await compteResultatAPI.updateMapping(mappingId, {
        category_name: mapping.category_name,
        level_1_values: updatedValues.length > 0 ? updatedValues : null,
        level_2_values: [],
        level_3_values: null,
      });
      
      console.log('✅ [CompteResultatConfigCard] Valeur level_1 supprimée avec succès');
      
      // Recharger les mappings
      await loadMappings();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [CompteResultatConfigCard] Erreur lors de la suppression de la valeur level_1:', err);
      alert(`❌ Erreur lors de la suppression: ${err.message || 'Erreur inconnue'}`);
    }
  };


  // Ajouter une nouvelle catégorie (Step 7.5.7)
  const handleAddCategory = async () => {
    try {
      // Prendre la première catégorie de "Charges d'exploitation" par défaut
      const defaultCategory = CHARGES_CATEGORIES[0]; // "Charges de copropriété hors fonds travaux"
      
      console.log('➕ [CompteResultatConfigCard] Création d\'un nouveau mapping...');
      const newMapping = await compteResultatAPI.createMapping({
        category_name: defaultCategory,
        level_1_values: null,
        level_2_values: [],
        level_3_values: null,
      });
      console.log('✅ [CompteResultatConfigCard] Nouveau mapping créé:', newMapping);
      
      // Recharger les mappings
      await loadMappings();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [CompteResultatConfigCard] Erreur lors de la création du mapping:', err);
      alert(`❌ Erreur lors de la création: ${err.message || 'Erreur inconnue'}`);
    }
  };

  // Gérer le clic droit pour afficher le menu contextuel (Step 7.5.8)
  const handleContextMenu = (e: React.MouseEvent<HTMLTableRowElement>, mappingId: number) => {
    e.preventDefault();
    setContextMenu({ x: e.clientX, y: e.clientY, mappingId });
  };

  // Fermer le menu contextuel
  const handleCloseContextMenu = () => {
    setContextMenu(null);
  };

  // Supprimer un mapping (Step 7.5.8)
  const handleDeleteMapping = async (mappingId: number) => {
    const mapping = mappings.find(m => m.id === mappingId);
    if (!mapping) return;

    // Confirmation
    const confirmed = window.confirm(
      `Êtes-vous sûr de vouloir supprimer le mapping pour "${mapping.category_name}" ?\n\n` +
      `Cette action est irréversible.`
    );

    if (!confirmed) {
      handleCloseContextMenu();
      return;
    }

    try {
      console.log('🗑️ [CompteResultatConfigCard] Suppression du mapping:', mappingId);
      await compteResultatAPI.deleteMapping(mappingId);
      console.log('✅ [CompteResultatConfigCard] Mapping supprimé avec succès');
      
      // Recharger les mappings
      await loadMappings();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [CompteResultatConfigCard] Erreur lors de la suppression:', err);
      alert(`❌ Erreur lors de la suppression: ${err.message || 'Erreur inconnue'}`);
    } finally {
      handleCloseContextMenu();
    }
  };

  // Sauvegarder une vue (Step 7.5.10)
  const saveView = async () => {
    const name = saveViewName.trim();
    if (!name) {
      alert('⚠️ Veuillez entrer un nom pour la vue');
      return;
    }

    try {
      console.log('💾 [CompteResultatConfigCard] Sauvegarde de la vue:', name);

      // Préparer les données de la vue (tous les mappings actuels)
      const viewData = {
        mappings: mappings.map(m => ({
          id: m.id,
          category_name: m.category_name,
          level_1_values: m.level_1_values,
          level_2_values: [],
          level_3_values: null,
        })),
        selected_level_3_values: selectedLevel3Values,
      };

      // Vérifier si une vue avec le même nom existe déjà
      const viewsResponse = await compteResultatMappingViewsAPI.getAll();
      const existingView = viewsResponse.views.find(v => v.name === name);

      if (existingView) {
        // Vue existante - demander confirmation pour écraser
        const confirmed = window.confirm(
          `Une vue avec le nom "${name}" existe déjà.\n\n` +
          `Voulez-vous l'écraser ?`
        );

        if (confirmed) {
          // Mettre à jour la vue existante
          await compteResultatMappingViewsAPI.update(existingView.id, {
            view_data: viewData,
          });

          console.log('✅ [CompteResultatConfigCard] Vue écrasée avec succès');

          // Fermer le popup et réinitialiser
          setShowSaveViewPopup(false);
          setSaveViewName('');
        }
        // Si l'utilisateur annule, on ne fait rien (le popup reste ouvert)
      } else {
        // Aucune vue existante - créer une nouvelle vue
        await compteResultatMappingViewsAPI.create({
          name: name,
          view_data: viewData,
        });

        console.log('✅ [CompteResultatConfigCard] Vue sauvegardée avec succès');

        // Fermer le popup et réinitialiser
        setShowSaveViewPopup(false);
        setSaveViewName('');
      }
    } catch (err: any) {
      console.error('❌ [CompteResultatConfigCard] Erreur lors de la sauvegarde de la vue:', err);

      // Extraire le message d'erreur
      let errorMessage = 'Erreur inconnue';
      if (err?.message) {
        errorMessage = err.message;
      } else if (typeof err === 'string') {
        errorMessage = err;
      }

      alert(`❌ Erreur lors de la sauvegarde: ${errorMessage}`);
    }
  };

  // Ouvrir le popup Save view (Step 7.5.10)
  const handleOpenSaveView = () => {
    setIsViewMenuOpen(false);
    setSaveViewName('');
    setShowSaveViewPopup(true);
  };

  // Ouvrir le popup Load view (Step 7.5.10)
  const handleOpenLoadView = async () => {
    setIsViewMenuOpen(false);
    setSelectedViewId(null);

    try {
      setLoadingViews(true);
      const viewsResponse = await compteResultatMappingViewsAPI.getAll();
      setAvailableViews(viewsResponse.views.map(v => ({ id: v.id, name: v.name })));
      setShowLoadViewPopup(true);
    } catch (err: any) {
      console.error('❌ [CompteResultatConfigCard] Erreur lors du chargement des vues:', err);
      alert(`❌ Erreur lors du chargement des vues: ${err?.message || 'Erreur inconnue'}`);
    } finally {
      setLoadingViews(false);
    }
  };

  // Charger une vue (Step 7.5.10)
  const loadView = async (viewId: number | null) => {
    if (viewId === null) {
      // "(default)" sélectionné - ne rien faire
      setShowLoadViewPopup(false);
      setSelectedViewId(null);
      return;
    }

    // Confirmation avant chargement
    const confirmed = window.confirm(
      'Cette action va remplacer la configuration actuelle. Continuer ?'
    );

    if (!confirmed) {
      return;
    }

    try {
      setLoadingView(true);
      console.log('📥 [CompteResultatConfigCard] Chargement de la vue:', viewId);

      // Récupérer la vue depuis l'API
      const view = await compteResultatMappingViewsAPI.getById(viewId);
      const viewData = view.view_data;

      // Supprimer tous les mappings existants
      for (const mapping of mappings) {
        try {
          await compteResultatAPI.deleteMapping(mapping.id);
        } catch (err) {
          console.warn(`⚠️ [CompteResultatConfigCard] Erreur lors de la suppression du mapping ${mapping.id}:`, err);
        }
      }

      // Créer les mappings depuis view_data.mappings
      for (const mappingData of viewData.mappings) {
        try {
          await compteResultatAPI.createMapping({
            category_name: mappingData.category_name,
            level_1_values: mappingData.level_1_values,
            level_2_values: [],
            level_3_values: null,
          });
        } catch (err) {
          console.error(`❌ [CompteResultatConfigCard] Erreur lors de la création du mapping ${mappingData.category_name}:`, err);
        }
      }

      // Recharger les mappings
      await loadMappings();

      // Charger selected_level_3_values depuis view_data (Step 9.2)
      if (viewData.selected_level_3_values && Array.isArray(viewData.selected_level_3_values)) {
        setSelectedLevel3Values(viewData.selected_level_3_values);
        console.log('✅ [CompteResultatConfigCard] Level 3 sélectionnés chargés:', viewData.selected_level_3_values);
      } else {
        // Compatibilité avec les vues existantes qui n'ont pas selected_level_3_values
        setSelectedLevel3Values([]);
        console.log('⚠️ [CompteResultatConfigCard] Aucune sélection Level 3 dans la vue, réinitialisation');
      }

      console.log('✅ [CompteResultatConfigCard] Vue chargée avec succès');

      // Fermer le popup
      setShowLoadViewPopup(false);
      setSelectedViewId(null);

      // Notifier le parent
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [CompteResultatConfigCard] Erreur lors du chargement de la vue:', err);
      alert(`❌ Erreur lors du chargement: ${err?.message || 'Erreur inconnue'}`);
    } finally {
      setLoadingView(false);
    }
  };

  // Ouvrir le popup Delete view (Step 7.5.10)
  const handleOpenDeleteView = async () => {
    setIsViewMenuOpen(false);
    setSelectedViewIdForDelete(null);

    try {
      setLoadingViewsForDelete(true);
      const viewsResponse = await compteResultatMappingViewsAPI.getAll();
      setAvailableViewsForDelete(viewsResponse.views.map(v => ({ id: v.id, name: v.name })));
      setShowDeleteViewPopup(true);
    } catch (err: any) {
      console.error('❌ [CompteResultatConfigCard] Erreur lors du chargement des vues:', err);
      alert(`❌ Erreur lors du chargement des vues: ${err?.message || 'Erreur inconnue'}`);
    } finally {
      setLoadingViewsForDelete(false);
    }
  };

  // Supprimer une vue (Step 7.5.10)
  const deleteView = async (viewId: number | null) => {
    if (viewId === null) {
      return;
    }

    // Trouver le nom de la vue pour la confirmation
    const viewToDelete = availableViewsForDelete.find(v => v.id === viewId);
    if (!viewToDelete) {
      alert('⚠️ Vue introuvable');
      return;
    }

    // Confirmation avant suppression
    const confirmed = window.confirm(
      `Êtes-vous sûr de vouloir supprimer la vue "${viewToDelete.name}" ?\n\n` +
      `Cette action est irréversible.`
    );

    if (!confirmed) {
      return;
    }

    try {
      console.log('🗑️ [CompteResultatConfigCard] Suppression de la vue:', viewId);

      // Appeler l'API pour supprimer la vue
      await compteResultatMappingViewsAPI.delete(viewId);

      console.log('✅ [CompteResultatConfigCard] Vue supprimée avec succès');

      // Retirer la vue de la liste
      const updatedViews = availableViewsForDelete.filter(v => v.id !== viewId);
      setAvailableViewsForDelete(updatedViews);
      setSelectedViewIdForDelete(null);

      // Si la liste est vide, fermer le popup
      if (updatedViews.length === 0) {
        setShowDeleteViewPopup(false);
      }
    } catch (err: any) {
      console.error('❌ [CompteResultatConfigCard] Erreur lors de la suppression de la vue:', err);
      alert(`❌ Erreur lors de la suppression: ${err?.message || 'Erreur inconnue'}`);
    }
  };

  // Gérer le changement de vue d'amortissement (Step 7.5.11)
  const handleAmortizationViewChange = async (mappingId: number, viewId: number | null) => {
    try {
      console.log('🔄 [CompteResultatConfigCard] Changement de vue d\'amortissement:', { mappingId, viewId });
      await compteResultatAPI.updateMapping(mappingId, {
        amortization_view_id: viewId,
      });
      console.log('✅ [CompteResultatConfigCard] Vue d\'amortissement mise à jour avec succès');
      
      // Recharger les mappings
      await loadMappings();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [CompteResultatConfigCard] Erreur lors de la mise à jour de la vue d\'amortissement:', err);
      alert(`❌ Erreur lors de la mise à jour: ${err.message || 'Erreur inconnue'}`);
    }
  };

  // Réinitialiser tous les mappings (Step 7.5.9)
  const handleResetMappings = async () => {
    const confirmed = window.confirm(
      `Êtes-vous sûr de vouloir réinitialiser tous les mappings ?\n\n` +
      `Cette action va :\n` +
      `- Supprimer tous les mappings existants (${mappings.length} mapping(s))\n` +
      `- Créer les mappings par défaut pour toutes les catégories comptables prédéfinies\n\n` +
      `Cette action est irréversible.`
    );

    if (!confirmed) return;

    try {
      console.log(`🔄 [CompteResultatConfigCard] Réinitialisation de tous les mappings...`);
      
      // 1. Supprimer tous les mappings existants
      for (const mapping of mappings) {
        console.log(`🗑️ [CompteResultatConfigCard] Suppression du mapping ${mapping.id}: ${mapping.category_name}`);
        await compteResultatAPI.deleteMapping(mapping.id);
      }
      
      console.log('✅ [CompteResultatConfigCard] Tous les mappings existants ont été supprimés');
      
      // 2. Créer les mappings par défaut pour toutes les catégories prédéfinies
      const allCategories = [...PRODUITS_CATEGORIES, ...CHARGES_CATEGORIES];
      console.log(`➕ [CompteResultatConfigCard] Création des mappings par défaut pour ${allCategories.length} catégories...`);
      
      for (const category of allCategories) {
        console.log(`➕ [CompteResultatConfigCard] Création du mapping pour: ${category}`);
        await compteResultatAPI.createMapping({
          category_name: category,
          level_1_values: null,
          level_2_values: [],
          level_3_values: null,
        });
      }
      
      console.log(`✅ [CompteResultatConfigCard] ${allCategories.length} mappings par défaut créés`);
      
      // 3. Recharger les mappings
      await loadMappings();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [CompteResultatConfigCard] Erreur lors de la réinitialisation:', err);
      alert(`❌ Erreur lors de la réinitialisation: ${err.message || 'Erreur inconnue'}`);
    }
  };

  // Fonction pour récupérer toutes les valeurs level_1 déjà utilisées dans tous les mappings
  const getAllUsedLevel1Values = (): string[] => {
    const usedValues = new Set<string>();
    mappings.forEach(mapping => {
      if (mapping.level_1_values && Array.isArray(mapping.level_1_values)) {
        mapping.level_1_values.forEach(v => usedValues.add(v));
      }
    });
    return Array.from(usedValues);
  };

  // Fonction pour récupérer toutes les valeurs level_2 déjà utilisées dans tous les mappings

  // Trier les mappings par Type puis par Catégorie comptable
  const sortedMappings = [...mappings].sort((a, b) => {
    // Utiliser le Type stocké dans mappingTypes, ou déduire depuis la catégorie
    const typeA = mappingTypes[a.id] || getTypeForCategory(a.category_name);
    const typeB = mappingTypes[b.id] || getTypeForCategory(b.category_name);
    
    if (typeA !== typeB) {
      // Produits d'exploitation avant Charges d'exploitation
      return typeA === 'Produits d\'exploitation' ? -1 : 1;
    }
    
    // Même type : trier par nom de catégorie
    return a.category_name.localeCompare(b.category_name);
  });

  if (loading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <p>Chargement des mappings...</p>
      </div>
    );
  }

  return (
    <div style={{ 
      backgroundColor: 'white', 
      borderRadius: '8px', 
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      padding: '24px'
    }}>
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#111827', margin: 0 }}>
            Configuration du compte de résultat
          </h3>
          {/* Bouton pin/unpin (Step 7.6.8) */}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '4px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#6b7280',
              fontSize: '16px',
              borderRadius: '4px',
              transition: 'background-color 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#f3f4f6';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
            }}
            title={isCollapsed ? 'Déplier la configuration' : 'Replier la configuration'}
          >
            {isCollapsed ? '📌' : '📍'}
          </button>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {mappings.length > 0 && (
            <button
              onClick={handleResetMappings}
              disabled={loading}
              style={{
                padding: '6px 12px',
                fontSize: '13px',
                fontWeight: '600',
                color: '#dc2626',
                backgroundColor: loading ? '#f3f4f6' : '#ffffff',
                border: '1px solid #dc2626',
                borderRadius: '6px',
                cursor: loading ? 'not-allowed' : 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                opacity: loading ? 0.5 : 1,
              }}
              title="Réinitialiser tous les mappings"
            >
              <span>🔄</span>
              <span>Réinitialiser les mappings</span>
            </button>
          )}
          {/* Bouton engrenage (Step 7.5.10) */}
          <div style={{ position: 'relative' }} ref={viewMenuRef}>
            <button
              onClick={() => setIsViewMenuOpen(!isViewMenuOpen)}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                padding: '4px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#6b7280',
                fontSize: '18px',
                borderRadius: '4px',
                transition: 'background-color 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#f3f4f6';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent';
              }}
              title="Options de vue"
            >
              ⚙️
            </button>
            {/* Menu déroulant */}
            {isViewMenuOpen && (
              <div
                style={{
                  position: 'absolute',
                  top: '100%',
                  right: '0',
                  marginTop: '4px',
                  backgroundColor: '#ffffff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '6px',
                  boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                  minWidth: '150px',
                  zIndex: 1000,
                }}
              >
                <button
                  onClick={handleOpenLoadView}
                  style={{
                    width: '100%',
                    padding: '10px 16px',
                    textAlign: 'left',
                    fontSize: '14px',
                    color: '#374151',
                    backgroundColor: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    borderRadius: '6px',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#f3f4f6';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  Load...
                </button>
                <button
                  onClick={handleOpenSaveView}
                  style={{
                    width: '100%',
                    padding: '10px 16px',
                    textAlign: 'left',
                    fontSize: '14px',
                    color: '#374151',
                    backgroundColor: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    borderRadius: '6px',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#f3f4f6';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  Save
                </button>
                <div style={{ height: '1px', backgroundColor: '#e5e7eb', margin: '4px 0' }} />
                <button
                  onClick={handleOpenDeleteView}
                  style={{
                    width: '100%',
                    padding: '10px 16px',
                    textAlign: 'left',
                    fontSize: '14px',
                    color: '#dc2626',
                    backgroundColor: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    borderRadius: '6px',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#fee2e2';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  Delete...
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Contenu de la card (masqué si repliée) (Step 7.6.8) */}
      {!isCollapsed && (
        <>
          {/* Dropdown Level 3 valeurs à inclure (Step 9.2) */}
          <div style={{ marginBottom: '16px', position: 'relative' }} ref={level3DropdownRef}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500', color: '#374151' }}>
              Level 3 valeurs à inclure dans le compte de résultat
            </label>
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setShowLevel3Dropdown(!showLevel3Dropdown)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  fontSize: '14px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  backgroundColor: '#ffffff',
                  color: '#374151',
                  cursor: 'pointer',
                  textAlign: 'left',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
                disabled={loadingLevel3Values}
              >
                <span>
                  {loadingLevel3Values 
                    ? 'Chargement...' 
                    : selectedLevel3Values.length === 0
                    ? 'Sélectionner des Level 3...'
                    : `${selectedLevel3Values.length} valeur${selectedLevel3Values.length > 1 ? 's' : ''} sélectionnée${selectedLevel3Values.length > 1 ? 's' : ''}`
                  }
                </span>
                <span style={{ fontSize: '10px' }}>{showLevel3Dropdown ? '▲' : '▼'}</span>
              </button>
              {showLevel3Dropdown && (
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
                    maxHeight: '300px',
                    overflowY: 'auto',
                  }}
                  onClick={(e) => e.stopPropagation()}
                >
                  {availableLevel3Values.length === 0 ? (
                    <div style={{ padding: '12px', color: '#9ca3af', fontSize: '14px', textAlign: 'center' }}>
                      Aucune valeur level_3 disponible
                    </div>
                  ) : (
                    availableLevel3Values.map((value) => {
                      const isChecked = selectedLevel3Values.includes(value);
                      return (
                        <label
                          key={value}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            padding: '10px 12px',
                            cursor: 'pointer',
                            borderBottom: '1px solid #f3f4f6',
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
                            checked={isChecked}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedLevel3Values([...selectedLevel3Values, value]);
                              } else {
                                setSelectedLevel3Values(selectedLevel3Values.filter(v => v !== value));
                              }
                            }}
                            style={{
                              marginRight: '8px',
                              cursor: 'pointer',
                            }}
                          />
                          <span style={{ fontSize: '14px', color: '#374151' }}>{value}</span>
                        </label>
                      );
                    })
                  )}
                </div>
              )}
            </div>
          </div>
          {sortedMappings.length === 0 ? (
        <div style={{ padding: '24px', textAlign: 'center', color: '#6b7280' }}>
          <p style={{ marginBottom: '16px' }}>Aucun mapping configuré. Cliquez sur "+ Ajouter une catégorie" pour en créer un.</p>
          <button
            onClick={handleAddCategory}
            disabled={loading}
            style={{
              padding: '8px 16px',
              fontSize: '14px',
              fontWeight: '600',
              color: '#ffffff',
              backgroundColor: loading ? '#9ca3af' : '#3b82f6',
              border: 'none',
              borderRadius: '6px',
              cursor: loading ? 'not-allowed' : 'pointer',
              boxShadow: loading ? 'none' : '0 2px 4px rgba(0, 0, 0, 0.1)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
            }}
            title="Ajouter une nouvelle catégorie comptable"
          >
            <span>+</span>
            <span>Ajouter une catégorie</span>
          </button>
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
                <th style={{ 
                  padding: '12px', 
                  textAlign: 'left', 
                  fontWeight: '600', 
                  color: '#374151',
                  width: '10%'
                }}>
                  Type
                </th>
                <th style={{ 
                  padding: '12px', 
                  textAlign: 'left', 
                  fontWeight: '600', 
                  color: '#374151',
                  width: '18%'
                }}>
                  Catégorie comptable
                </th>
                <th style={{ 
                  padding: '12px', 
                  textAlign: 'left', 
                  fontWeight: '600', 
                  color: '#374151',
                  width: '25%'
                }}>
                  Level 1 (valeurs)
                </th>
                <th style={{ 
                  padding: '12px', 
                  textAlign: 'left', 
                  fontWeight: '600', 
                  color: '#374151',
                  width: '25%'
                }}>
                  Vue
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedMappings.map((mapping) => {
                // Utiliser le Type stocké dans mappingTypes, ou déduire depuis la catégorie
                const type = mappingTypes[mapping.id] || getTypeForCategory(mapping.category_name);
                const isSpecial = isSpecialCategory(mapping.category_name);
                
                return (
                  <tr 
                    key={mapping.id} 
                    style={{ borderBottom: '1px solid #e5e7eb', cursor: 'context-menu' }}
                    onContextMenu={(e) => {
                      // Ne pas afficher le menu contextuel si on clique sur un bouton de suppression
                      const target = e.target as HTMLElement;
                      if (target.tagName === 'BUTTON' || target.closest('button')) {
                        return;
                      }
                      handleContextMenu(e, mapping.id);
                    }}
                  >
                    <td style={{ padding: '12px' }}>
                      <select
                        value={type}
                        onChange={(e) => handleTypeChange(mapping.id, e.target.value as TypeValue)}
                        style={{
                          width: '100%',
                          padding: '6px 8px',
                          fontSize: '13px',
                          border: '1px solid #d1d5db',
                          borderRadius: '4px',
                          backgroundColor: '#ffffff',
                          color: '#374151',
                          cursor: 'pointer',
                        }}
                      >
                        <option value="Produits d'exploitation">Produits d'exploitation</option>
                        <option value="Charges d'exploitation">Charges d'exploitation</option>
                      </select>
                    </td>
                    <td style={{ padding: '12px' }}>
                      <select
                        value={mapping.category_name}
                        onChange={(e) => handleCategoryChange(mapping.id, e.target.value)}
                        style={{
                          width: '100%',
                          padding: '6px 8px',
                          fontSize: '13px',
                          border: '1px solid #d1d5db',
                          borderRadius: '4px',
                          backgroundColor: '#ffffff',
                          color: '#374151',
                          cursor: 'pointer',
                        }}
                      >
                        {getAvailableCategoriesForType(type).map((category) => (
                          <option key={category} value={category}>
                            {category}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td style={{ padding: '12px' }}>
                      {isSpecial ? (
                        <span style={{ fontStyle: 'italic', color: '#9ca3af' }}>Données calculées</span>
                      ) : (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', alignItems: 'center' }}>
                          {/* Tags des valeurs level_1 sélectionnées */}
                          {mapping.level_1_values && Array.isArray(mapping.level_1_values) && mapping.level_1_values.length > 0 ? (
                            mapping.level_1_values.map((value) => (
                              <span
                                key={value}
                                style={{
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  padding: '2px 6px',
                                  backgroundColor: '#3b82f6',
                                  color: '#ffffff',
                                  borderRadius: '4px',
                                  fontSize: '11px',
                                  gap: '4px',
                                }}
                              >
                                {value}
                                <button
                                  onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    console.log('🗑️ [CompteResultatConfigCard] Clic sur suppression level_1:', value, 'pour mapping:', mapping.id);
                                    handleLevel1Remove(mapping.id, value);
                                  }}
                                  style={{
                                    background: 'none',
                                    border: 'none',
                                    color: '#ffffff',
                                    cursor: 'pointer',
                                    padding: '0',
                                    marginLeft: '4px',
                                    fontSize: '12px',
                                    fontWeight: 'bold',
                                    lineHeight: '1',
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                  }}
                                  title="Supprimer"
                                >
                                  ×
                                </button>
                              </span>
                            ))
                          ) : (
                            <span style={{ color: '#9ca3af', fontStyle: 'italic', fontSize: '12px' }}>
                              Aucune valeur
                            </span>
                          )}
                          {/* Dropdown pour ajouter une valeur */}
                          {editingLevel1Id === mapping.id ? (
                            <select
                              onChange={(e) => {
                                if (e.target.value) {
                                  handleLevel1Add(mapping.id, e.target.value);
                                  setEditingLevel1Id(null);
                                }
                              }}
                              onBlur={() => setEditingLevel1Id(null)}
                              autoFocus
                              style={{
                                padding: '2px 6px',
                                fontSize: '12px',
                                border: '1px solid #3b82f6',
                                borderRadius: '4px',
                                backgroundColor: '#ffffff',
                                minWidth: '120px',
                              }}
                            >
                              <option value="">
                                {selectedLevel3Values.length === 0 
                                  ? "Sélectionnez d'abord des Level 3" 
                                  : level1Values.length === 0
                                  ? "Aucune valeur disponible"
                                  : "Sélectionner..."}
                              </option>
                              {level1Values
                                .filter(v => !getAllUsedLevel1Values().includes(v))
                                .map((value) => (
                                  <option key={value} value={value}>
                                    {value}
                                  </option>
                                ))}
                            </select>
                          ) : (
                            (() => {
                              const usedValues = getAllUsedLevel1Values();
                              const availableValues = level1Values.filter(v => !usedValues.includes(v));
                              const isDisabled = level1Values.length === 0 || availableValues.length === 0;
                              
                              return (
                                <button
                                  onClick={() => {
                                    console.log('🔍 [CompteResultatConfigCard] Clic sur "+ Ajouter" pour mapping:', mapping.id);
                                    console.log('🔍 [CompteResultatConfigCard] level1Values:', level1Values);
                                    console.log('🔍 [CompteResultatConfigCard] mapping.level_1_values:', mapping.level_1_values);
                                    console.log('🔍 [CompteResultatConfigCard] Valeurs disponibles:', availableValues);
                                    if (selectedLevel3Values.length === 0) {
                                      alert('⚠️ Sélectionnez d\'abord des Level 3 dans le dropdown "Level 3 valeurs à inclure dans le compte de résultat".');
                                    } else if (availableValues.length > 0) {
                                      setEditingLevel1Id(mapping.id);
                                    } else {
                                      alert('⚠️ Toutes les valeurs level_1 sont déjà assignées à ce mapping, ou aucune valeur level_1 n\'est disponible pour les Level 3 sélectionnés.');
                                    }
                                  }}
                                  disabled={isDisabled}
                                  style={{
                                    padding: '2px 6px',
                                    fontSize: '11px',
                                    border: '1px solid #d1d5db',
                                    borderRadius: '4px',
                                    backgroundColor: isDisabled ? '#f3f4f6' : '#f9fafb',
                                    color: isDisabled ? '#9ca3af' : '#374151',
                                    cursor: isDisabled ? 'not-allowed' : 'pointer',
                                    opacity: isDisabled ? 0.5 : 1,
                                  }}
                                  title={selectedLevel3Values.length === 0
                                    ? "Sélectionnez d'abord des Level 3"
                                    : level1Values.length === 0 
                                    ? "Aucune valeur level_1 disponible pour les Level 3 sélectionnés" 
                                    : availableValues.length === 0
                                    ? "Toutes les valeurs sont déjà assignées"
                                    : "Ajouter une valeur"}
                                >
                                  + Ajouter
                                </button>
                              );
                            })()
                          )}
                        </div>
                      )}
                    </td>
                    {/* Colonne Vue (Step 7.5.11) */}
                    <td style={{ padding: '12px' }}>
                      {mapping.category_name === 'Charges d\'amortissements' ? (
                        // Dropdown pour sélectionner une vue d'amortissement
                        loadingAmortizationViews ? (
                          <span style={{ color: '#9ca3af', fontStyle: 'italic', fontSize: '12px' }}>
                            Chargement...
                          </span>
                        ) : amortizationViews.length === 0 ? (
                          <span style={{ color: '#9ca3af', fontStyle: 'italic', fontSize: '12px' }}>
                            vue à configurer
                          </span>
                        ) : (
                          <select
                            value={mapping.amortization_view_id || ''}
                            onChange={(e) => {
                              const viewId = e.target.value ? parseInt(e.target.value) : null;
                              handleAmortizationViewChange(mapping.id, viewId);
                            }}
                            style={{
                              width: '100%',
                              padding: '6px 8px',
                              fontSize: '13px',
                              border: '1px solid #d1d5db',
                              borderRadius: '4px',
                              backgroundColor: '#ffffff',
                              color: '#374151',
                              cursor: 'pointer',
                            }}
                          >
                            <option value="">Sélectionner une vue...</option>
                            {amortizationViews.map((view) => (
                              <option key={view.id} value={view.id}>
                                {view.name} ({view.level_2_value})
                              </option>
                            ))}
                          </select>
                        )
                      ) : mapping.category_name === 'Coût du financement (hors remboursement du capital)' ? (
                        // Dropdown avec checkboxes pour sélectionner les crédits (Step 7.5.12)
                        <div style={{ position: 'relative' }} data-loan-dropdown>
                          {loadingLoanConfigs ? (
                            <span style={{ color: '#9ca3af', fontStyle: 'italic', fontSize: '12px' }}>
                              Chargement...
                            </span>
                          ) : loanConfigs.length === 0 ? (
                            <span style={{ color: '#9ca3af', fontStyle: 'italic', fontSize: '12px' }}>
                              vue à configurer
                            </span>
                          ) : (
                            <>
                              <button
                                onClick={() => setShowLoanDropdown(showLoanDropdown === mapping.id ? null : mapping.id)}
                                style={{
                                  width: '100%',
                                  padding: '6px 8px',
                                  fontSize: '13px',
                                  border: '1px solid #d1d5db',
                                  borderRadius: '4px',
                                  backgroundColor: '#ffffff',
                                  color: '#374151',
                                  cursor: 'pointer',
                                  textAlign: 'left',
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  alignItems: 'center',
                                }}
                              >
                                <span>
                                  {(() => {
                                    const selectedIds = mapping.selected_loan_ids || [];
                                    if (selectedIds.length === 0) {
                                      return 'Sélectionner des crédits...';
                                    } else if (selectedIds.length === 1) {
                                      const loan = loanConfigs.find(l => l.id === selectedIds[0]);
                                      return loan ? loan.name : `${selectedIds.length} crédit sélectionné`;
                                    } else {
                                      return `${selectedIds.length} crédits sélectionnés`;
                                    }
                                  })()}
                                </span>
                                <span style={{ fontSize: '10px' }}>{showLoanDropdown === mapping.id ? '▲' : '▼'}</span>
                              </button>
                              {showLoanDropdown === mapping.id && (
                                <div
                                  style={{
                                    position: 'absolute',
                                    top: '100%',
                                    left: 0,
                                    right: 0,
                                    marginTop: '4px',
                                    backgroundColor: '#ffffff',
                                    border: '1px solid #d1d5db',
                                    borderRadius: '4px',
                                    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                                    zIndex: 1000,
                                    maxHeight: '200px',
                                    overflowY: 'auto',
                                  }}
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  {loanConfigs.map((loan) => {
                                    const selectedIds = mapping.selected_loan_ids || [];
                                    const isChecked = selectedIds.includes(loan.id);
                                    return (
                                      <label
                                        key={loan.id}
                                        style={{
                                          display: 'flex',
                                          alignItems: 'center',
                                          padding: '8px 12px',
                                          cursor: 'pointer',
                                          borderBottom: '1px solid #f3f4f6',
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
                                          checked={isChecked}
                                          onChange={(e) => {
                                            handleLoanSelectionChange(mapping.id, loan.id, e.target.checked);
                                          }}
                                          style={{
                                            marginRight: '8px',
                                            cursor: 'pointer',
                                          }}
                                        />
                                        <span style={{ fontSize: '13px', color: '#374151' }}>{loan.name}</span>
                                      </label>
                                    );
                                  })}
                                </div>
                              )}
                            </>
                          )}
                        </div>
                      ) : (
                        // Pour toutes les autres catégories
                        <span style={{ color: '#9ca3af', fontStyle: 'italic', fontSize: '12px' }}>
                          Aucune valeur
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
              {/* Ligne pour ajouter une nouvelle catégorie (Step 7.5.7) */}
              <tr style={{ backgroundColor: '#f9fafb', borderTop: '2px solid #e5e7eb' }}>
                <td colSpan={4} style={{ padding: '12px', textAlign: 'center' }}>
                  <button
                    onClick={handleAddCategory}
                    disabled={loading}
                    style={{
                      padding: '8px 16px',
                      fontSize: '14px',
                      fontWeight: '600',
                      color: '#ffffff',
                      backgroundColor: loading ? '#9ca3af' : '#3b82f6',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: loading ? 'not-allowed' : 'pointer',
                      boxShadow: loading ? 'none' : '0 2px 4px rgba(0, 0, 0, 0.1)',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                    }}
                    title="Ajouter une nouvelle catégorie comptable"
                  >
                    <span>+</span>
                    <span>Ajouter une catégorie</span>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      )}

      {/* Menu contextuel (Step 7.5.8) */}
      {contextMenu && (
        <div
          style={{
            position: 'fixed',
            left: `${contextMenu.x}px`,
            top: `${contextMenu.y}px`,
            backgroundColor: '#ffffff',
            border: '1px solid #e5e7eb',
            borderRadius: '6px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
            zIndex: 1000,
            minWidth: '150px',
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={() => handleDeleteMapping(contextMenu.mappingId)}
            style={{
              width: '100%',
              padding: '10px 16px',
              textAlign: 'left',
              fontSize: '14px',
              color: '#dc2626',
              backgroundColor: 'transparent',
              border: 'none',
              cursor: 'pointer',
              borderRadius: '6px',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#fef2f2';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
            }}
          >
            🗑️ Supprimer
          </button>
        </div>
      )}
        </>
      )}

      {/* Popup Save view (Step 7.5.10) */}
      {showSaveViewPopup && (
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
          onClick={() => {
            setShowSaveViewPopup(false);
            setSaveViewName('');
          }}
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
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1a1a1a', margin: 0 }}>
                Sauvegarder la vue
              </h2>
              <button
                onClick={() => {
                  setShowSaveViewPopup(false);
                  setSaveViewName('');
                }}
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

            <div style={{ marginBottom: '20px' }}>
              <label
                htmlFor="save-view-name"
                style={{
                  display: 'block',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#374151',
                  marginBottom: '8px',
                }}
              >
                Nom de la vue
              </label>
              <input
                id="save-view-name"
                type="text"
                value={saveViewName}
                onChange={(e) => setSaveViewName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && saveViewName.trim()) {
                    saveView();
                  } else if (e.key === 'Escape') {
                    setShowSaveViewPopup(false);
                    setSaveViewName('');
                  }
                }}
                placeholder="Ex: Configuration 2024..."
                autoFocus
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  fontSize: '14px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  outline: 'none',
                }}
              />
              <p style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px', marginBottom: 0 }}>
                Format libre. Si une vue avec ce nom existe déjà, vous pourrez choisir de l'écraser.
              </p>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button
                onClick={() => {
                  setShowSaveViewPopup(false);
                  setSaveViewName('');
                }}
                style={{
                  padding: '10px 20px',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#374151',
                  backgroundColor: '#f3f4f6',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                }}
              >
                Annuler
              </button>
              <button
                onClick={saveView}
                disabled={!saveViewName.trim()}
                style={{
                  padding: '10px 20px',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#ffffff',
                  backgroundColor: saveViewName.trim() ? '#3b82f6' : '#9ca3af',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: saveViewName.trim() ? 'pointer' : 'not-allowed',
                }}
              >
                Sauvegarder
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Popup Load view (Step 7.5.10) */}
      {showLoadViewPopup && (
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
          onClick={() => {
            if (!loadingView) {
              setShowLoadViewPopup(false);
              setSelectedViewId(null);
            }
          }}
        >
          <div
            style={{
              backgroundColor: 'white',
              borderRadius: '8px',
              padding: '24px',
              maxWidth: '500px',
              width: '90%',
              maxHeight: '80vh',
              display: 'flex',
              flexDirection: 'column',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1a1a1a', margin: 0 }}>
                Charger une vue
              </h2>
              <button
                onClick={() => {
                  if (!loadingView) {
                    setShowLoadViewPopup(false);
                    setSelectedViewId(null);
                  }
                }}
                disabled={loadingView}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '24px',
                  cursor: loadingView ? 'not-allowed' : 'pointer',
                  color: '#666',
                  padding: '0',
                  width: '32px',
                  height: '32px',
                  opacity: loadingView ? 0.5 : 1,
                }}
              >
                ×
              </button>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', marginBottom: '20px' }}>
              {loadingViews ? (
                <div style={{ textAlign: 'center', padding: '20px', color: '#6b7280' }}>
                  Chargement des vues...
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {/* Option "(default)" */}
                  <div
                    onClick={() => !loadingView && setSelectedViewId(null)}
                    style={{
                      padding: '12px 16px',
                      borderRadius: '6px',
                      cursor: loadingView ? 'not-allowed' : 'pointer',
                      backgroundColor: selectedViewId === null ? '#e0f2fe' : 'transparent',
                      border: selectedViewId === null ? '2px solid #3b82f6' : '2px solid transparent',
                      opacity: loadingView ? 0.5 : 1,
                    }}
                    onMouseEnter={(e) => {
                      if (!loadingView && selectedViewId !== null) {
                        e.currentTarget.style.backgroundColor = '#f3f4f6';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (selectedViewId !== null) {
                        e.currentTarget.style.backgroundColor = 'transparent';
                      }
                    }}
                  >
                    <div style={{ fontWeight: '500', color: '#111827' }}>(default)</div>
                    <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '2px' }}>
                      Ne rien charger
                    </div>
                  </div>
                  {/* Liste des vues disponibles */}
                  {availableViews.map((view) => (
                    <div
                      key={view.id}
                      onClick={() => !loadingView && setSelectedViewId(view.id)}
                      style={{
                        padding: '12px 16px',
                        borderRadius: '6px',
                        cursor: loadingView ? 'not-allowed' : 'pointer',
                        backgroundColor: selectedViewId === view.id ? '#e0f2fe' : 'transparent',
                        border: selectedViewId === view.id ? '2px solid #3b82f6' : '2px solid transparent',
                        opacity: loadingView ? 0.5 : 1,
                      }}
                      onMouseEnter={(e) => {
                        if (!loadingView && selectedViewId !== view.id) {
                          e.currentTarget.style.backgroundColor = '#f3f4f6';
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (selectedViewId !== view.id) {
                          e.currentTarget.style.backgroundColor = 'transparent';
                        }
                      }}
                    >
                      <div style={{ fontWeight: '500', color: '#111827' }}>{view.name}</div>
                    </div>
                  ))}
                  {availableViews.length === 0 && (
                    <div style={{ textAlign: 'center', padding: '20px', color: '#6b7280', fontStyle: 'italic' }}>
                      Aucune vue sauvegardée
                    </div>
                  )}
                </div>
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button
                onClick={() => {
                  if (!loadingView) {
                    setShowLoadViewPopup(false);
                    setSelectedViewId(null);
                  }
                }}
                disabled={loadingView}
                style={{
                  padding: '10px 20px',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#374151',
                  backgroundColor: '#f3f4f6',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: loadingView ? 'not-allowed' : 'pointer',
                  opacity: loadingView ? 0.5 : 1,
                }}
              >
                Annuler
              </button>
              <button
                onClick={() => loadView(selectedViewId)}
                disabled={loadingView || selectedViewId === null}
                style={{
                  padding: '10px 20px',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#ffffff',
                  backgroundColor: (!loadingView && selectedViewId !== null) ? '#3b82f6' : '#9ca3af',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: (loadingView || selectedViewId === null) ? 'not-allowed' : 'pointer',
                }}
              >
                {loadingView ? 'Chargement...' : 'Charger'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Popup Delete view (Step 7.5.10) */}
      {showDeleteViewPopup && (
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
          onClick={() => {
            setShowDeleteViewPopup(false);
            setSelectedViewIdForDelete(null);
          }}
        >
          <div
            style={{
              backgroundColor: 'white',
              borderRadius: '8px',
              padding: '24px',
              maxWidth: '500px',
              width: '90%',
              maxHeight: '80vh',
              display: 'flex',
              flexDirection: 'column',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1a1a1a', margin: 0 }}>
                Supprimer une vue
              </h2>
              <button
                onClick={() => {
                  setShowDeleteViewPopup(false);
                  setSelectedViewIdForDelete(null);
                }}
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

            <div style={{ flex: 1, overflowY: 'auto', marginBottom: '20px' }}>
              {loadingViewsForDelete ? (
                <div style={{ textAlign: 'center', padding: '20px', color: '#6b7280' }}>
                  Chargement des vues...
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {availableViewsForDelete.map((view) => (
                    <div
                      key={view.id}
                      onClick={() => setSelectedViewIdForDelete(view.id)}
                      style={{
                        padding: '12px 16px',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        backgroundColor: selectedViewIdForDelete === view.id ? '#fee2e2' : 'transparent',
                        border: selectedViewIdForDelete === view.id ? '2px solid #dc2626' : '2px solid transparent',
                      }}
                      onMouseEnter={(e) => {
                        if (selectedViewIdForDelete !== view.id) {
                          e.currentTarget.style.backgroundColor = '#f3f4f6';
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (selectedViewIdForDelete !== view.id) {
                          e.currentTarget.style.backgroundColor = 'transparent';
                        }
                      }}
                    >
                      <div style={{ fontWeight: '500', color: '#111827' }}>{view.name}</div>
                    </div>
                  ))}
                  {availableViewsForDelete.length === 0 && (
                    <div style={{ textAlign: 'center', padding: '20px', color: '#6b7280', fontStyle: 'italic' }}>
                      Aucune vue sauvegardée
                    </div>
                  )}
                </div>
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button
                onClick={() => {
                  setShowDeleteViewPopup(false);
                  setSelectedViewIdForDelete(null);
                }}
                style={{
                  padding: '10px 20px',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#374151',
                  backgroundColor: '#f3f4f6',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                }}
              >
                Annuler
              </button>
              <button
                onClick={() => deleteView(selectedViewIdForDelete)}
                disabled={selectedViewIdForDelete === null}
                style={{
                  padding: '10px 20px',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#ffffff',
                  backgroundColor: selectedViewIdForDelete !== null ? '#dc2626' : '#9ca3af',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: selectedViewIdForDelete !== null ? 'pointer' : 'not-allowed',
                }}
              >
                Supprimer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

