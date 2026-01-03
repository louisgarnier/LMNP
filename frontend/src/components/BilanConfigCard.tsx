/**
 * BilanConfigCard component - Card de configuration du bilan
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { bilanAPI, BilanMapping, transactionsAPI, bilanMappingViewsAPI, BilanMappingView, amortizationViewsAPI, allowedMappingsAPI } from '@/api/client';

interface BilanConfigCardProps {
  onConfigUpdated?: () => void;
}

type TypeValue = 'ACTIF' | 'PASSIF';

// Sous-catégories par Type
const ACTIF_SUB_CATEGORIES = [
  'Actif immobilisé',
  'Actif circulant',
];

const PASSIF_SUB_CATEGORIES = [
  'Capitaux propres',
  'Trésorerie passive',
  'Dettes financières',
];

// Catégories comptables par sous-catégorie
const CATEGORIES_BY_SUB_CATEGORY: Record<string, string[]> = {
  'Actif immobilisé': [
    'Immobilisations',
    'Amortissements cumulés',
  ],
  'Actif circulant': [
    'Compte bancaire',
    'Créances locataires',
    'Charges payées d\'avance',
  ],
  'Capitaux propres': [
    'Capitaux propres',
    'Apports initiaux',
    'Souscription de parts sociales',
    'Résultat de l\'exercice (bénéfice / perte)',
    'Report à nouveau / report du déficit',
    'Compte courant d\'associé',
  ],
  'Trésorerie passive': [
    'Cautions reçues',
  ],
  'Dettes financières': [
    'Emprunt bancaire (capital restant dû)',
    'Autres dettes',
  ],
};

// Catégories spéciales (données calculées, pas de mapping level_1)
const SPECIAL_CATEGORIES = [
  'Amortissements cumulés',
  'Compte bancaire',
  'Résultat de l\'exercice (bénéfice / perte)',
  'Report à nouveau / report du déficit',
];

// Source pour chaque catégorie spéciale
const SPECIAL_SOURCE_BY_CATEGORY: Record<string, string> = {
  'Amortissements cumulés': 'amortizations',
  'Compte bancaire': 'transactions',
  'Résultat de l\'exercice (bénéfice / perte)': 'compte_resultat',
  'Report à nouveau / report du déficit': 'compte_resultat_cumul',
  'Emprunt bancaire (capital restant dû)': 'loan_payments',
};

// Fonction pour obtenir la sous-catégorie d'une catégorie comptable
function getSubCategoryForCategory(categoryName: string): string | null {
  for (const [subCategory, categories] of Object.entries(CATEGORIES_BY_SUB_CATEGORY)) {
    if (categories.includes(categoryName)) {
      return subCategory;
    }
  }
  return null;
}

// Fonction pour obtenir le type d'une sous-catégorie
function getTypeForSubCategory(subCategory: string): TypeValue {
  if (ACTIF_SUB_CATEGORIES.includes(subCategory)) {
    return 'ACTIF';
  }
  return 'PASSIF';
}

// Fonction pour obtenir le type d'une catégorie comptable
function getTypeForCategory(categoryName: string): TypeValue {
  const subCategory = getSubCategoryForCategory(categoryName);
  if (!subCategory) return 'ACTIF'; // Par défaut
  return getTypeForSubCategory(subCategory);
}

// Fonction pour vérifier si une catégorie est spéciale
function isSpecialCategory(categoryName: string): boolean {
  return SPECIAL_CATEGORIES.includes(categoryName) || categoryName === 'Emprunt bancaire (capital restant dû)';
}

export default function BilanConfigCard({ onConfigUpdated }: BilanConfigCardProps) {
  const [mappings, setMappings] = useState<BilanMapping[]>([]);
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
  // Flag pour éviter de sauvegarder lors du chargement initial depuis localStorage
  const [isInitialLoad, setIsInitialLoad] = useState<boolean>(true);
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
  // État pour gérer le repli/dépli de la card (Step 7.6.8)
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);

  // Charger selectedLevel3Values depuis localStorage après le montage (évite erreur d'hydratation)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('bilanConfigCard_selectedLevel3Values');
      console.log('🔍 [BilanConfigCard] Chargement depuis localStorage:', saved);
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          if (Array.isArray(parsed)) {
            console.log('✅ [BilanConfigCard] Valeurs chargées depuis localStorage:', parsed);
            // Charger les valeurs
            setSelectedLevel3Values(parsed);
            // Réinitialiser le flag après un court délai pour permettre le rendu et éviter la sauvegarde immédiate
            setTimeout(() => {
              console.log('✅ [BilanConfigCard] Fin du chargement initial, activation de la sauvegarde');
              setIsInitialLoad(false);
            }, 200);
          } else {
            console.log('⚠️ [BilanConfigCard] Valeurs invalides dans localStorage (pas un tableau)');
            setIsInitialLoad(false);
          }
        } catch (e) {
          console.warn('⚠️ [BilanConfigCard] Erreur lors du chargement de selectedLevel3Values depuis localStorage:', e);
          setIsInitialLoad(false);
        }
      } else {
        console.log('⚠️ [BilanConfigCard] Aucune valeur trouvée dans localStorage');
        setIsInitialLoad(false);
      }
      
      // Charger isCollapsed depuis localStorage
      const savedCollapsed = localStorage.getItem('bilanConfigCard_collapsed');
      if (savedCollapsed === 'true') {
        setIsCollapsed(true);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Exécuter une seule fois au montage

  // Sauvegarder l'état dans localStorage quand il change (Step 7.6.8)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('bilanConfigCard_collapsed', String(isCollapsed));
    }
  }, [isCollapsed]);

  // Sauvegarder selectedLevel3Values dans localStorage quand il change
  useEffect(() => {
    if (typeof window !== 'undefined') {
      // Ne pas sauvegarder lors du chargement initial
      if (isInitialLoad) {
        console.log('⏭️ [BilanConfigCard] Ignorer la sauvegarde (chargement initial), valeurs:', selectedLevel3Values);
        return;
      }
      console.log('💾 [BilanConfigCard] Sauvegarde dans localStorage:', selectedLevel3Values);
      localStorage.setItem('bilanConfigCard_selectedLevel3Values', JSON.stringify(selectedLevel3Values));
    }
  }, [selectedLevel3Values, isInitialLoad]);

  // Charger les mappings et les valeurs level_1 au montage
  useEffect(() => {
    loadMappings();
    loadLevel1Values();
    loadAvailableLevel3Values();
    loadAmortizationViews();
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
          console.warn(`⚠️ [BilanConfigCard] Erreur lors du chargement des vues pour ${level2}:`, err);
        }
      }
      
      setAmortizationViews(allViews);
      console.log('✅ [BilanConfigCard] Vues d\'amortissement chargées:', allViews.length);
    } catch (err: any) {
      console.error('❌ [BilanConfigCard] Erreur lors du chargement des vues d\'amortissement:', err);
    } finally {
      setLoadingAmortizationViews(false);
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
      const response = await bilanAPI.getMappings();
      const loadedMappings = response.mappings || [];
      console.log('🔄 [BilanConfigCard] Mappings rechargés:', loadedMappings);
      setMappings(loadedMappings);
      
      // Initialiser les Types pour chaque mapping (déduit selon la catégorie)
      const initialTypes: Record<number, TypeValue> = {};
      loadedMappings.forEach(mapping => {
        initialTypes[mapping.id] = getTypeForCategory(mapping.category_name);
        console.log(`🔍 [BilanConfigCard] Mapping ${mapping.id} - level_1_values:`, mapping.level_1_values);
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
    const availableCategories = getAvailableSubCategoriesForType(newType);
    const currentCategoryValid = availableCategories.includes(mapping.category_name);

    // Mettre à jour le Type dans l'état local
    setMappingTypes(prev => ({
      ...prev,
      [mappingId]: newType
    }));

    // Si la catégorie actuelle n'est plus valide, la réinitialiser à la première catégorie du nouveau Type
    if (!currentCategoryValid) {
      const newCategory = availableCategories[0];
      console.log(`🔄 [BilanConfigCard] Type changé, réinitialisation de la catégorie à:`, newCategory);
      await handleCategoryChange(mappingId, newCategory);
    }
  };

  // Obtenir les sous-catégories disponibles selon le Type
  const getAvailableSubCategoriesForType = (type: TypeValue): string[] => {
    if (type === 'ACTIF') {
      return ACTIF_SUB_CATEGORIES;
    }
    return PASSIF_SUB_CATEGORIES;
  };

  // Obtenir les catégories comptables disponibles selon la sous-catégorie
  const getAvailableCategoriesForSubCategory = (subCategory: string): string[] => {
    return CATEGORIES_BY_SUB_CATEGORY[subCategory] || [];
  };

  // Charger les valeurs level_1 disponibles depuis les transactions enrichies (Step 7.5.5)
  // Charger les valeurs level_1 filtrées par les level_3 sélectionnés ET qui existent dans les transactions (Step 9.3)
  const loadLevel1Values = async () => {
    try {
      // Si aucun level_3 n'est sélectionné, ne pas charger de valeurs
      if (selectedLevel3Values.length === 0) {
        console.log('⚠️ [BilanConfigCard] Aucun level_3 sélectionné, pas de chargement de level_1');
        setLevel1Values([]);
        return;
      }

      console.log('🔍 [BilanConfigCard] Chargement des valeurs level_1 filtrées par level_3:', selectedLevel3Values);
      
      // Récupérer directement les level_1 uniques depuis les transactions qui ont les level_3 sélectionnés
      // Pour chaque level_3 sélectionné, récupérer les transactions et extraire les level_1 uniques
      const allLevel1Values = new Set<string>();
      
      for (const level3 of selectedLevel3Values) {
        try {
          // Récupérer toutes les transactions avec ce level_3 (pagination si nécessaire)
          let skip = 0;
          const limit = 1000; // Limite maximale de l'API
          let hasMore = true;
          
          while (hasMore) {
            const transactionsResponse = await transactionsAPI.getAll(
              skip,
              limit,
              undefined, // startDate
              undefined, // endDate
              undefined, // sortBy
              undefined, // sortDirection
              undefined, // unclassifiedOnly
              undefined, // filterNom
              undefined, // filterLevel1
              undefined, // filterLevel2
              level3 // filterLevel3
            );
            
            // Extraire les level_1 uniques de ces transactions (déjà filtrées par filter_level_3)
            transactionsResponse.transactions
              .map((t: { level_1?: string }) => t.level_1)
              .filter((level1): level1 is string => level1 !== null && level1 !== undefined && level1 !== '')
              .forEach((level1: string) => allLevel1Values.add(level1));
            
            // Vérifier s'il y a plus de transactions à récupérer
            hasMore = transactionsResponse.transactions.length === limit;
            skip += limit;
          }
        } catch (err) {
          console.warn(`⚠️ [BilanConfigCard] Erreur lors de la récupération des transactions pour level_3=${level3}:`, err);
        }
      }
      
      const filteredValues = Array.from(allLevel1Values).sort();
      console.log('✅ [BilanConfigCard] Level_1 filtrés (depuis transactions avec level_3 sélectionnés):', filteredValues);
      
      setLevel1Values(filteredValues);
      console.log('✅ [BilanConfigCard] Nombre de valeurs level_1 chargées:', filteredValues.length);
    } catch (err: any) {
      console.error('❌ [BilanConfigCard] Erreur lors du chargement des valeurs level_1:', err);
      // Ne pas afficher d'alerte, juste logger l'erreur pour ne pas bloquer l'interface
      setLevel1Values([]);
    }
  };

  // Plus besoin de régénérer - le calcul se fait maintenant à la volée dans BilanTable
  // Cette fonction est conservée pour compatibilité mais ne fait plus rien
  const regenerateBilanData = async () => {
    console.log('✅ [BilanConfigCard] Les données seront calculées à la volée dans BilanTable (comme CompteResultatTable)');
    // Plus besoin de générer - BilanTable utilise maintenant calculateAmounts() à la volée
  };

  // Charger toutes les valeurs level_3 disponibles (Step 9.2)
  const loadAvailableLevel3Values = async () => {
    try {
      setLoadingLevel3Values(true);
      console.log('🔍 [BilanConfigCard] Chargement des valeurs level_3 disponibles...');
      const values = await allowedMappingsAPI.getAllowedLevel3();
      console.log('✅ [BilanConfigCard] Valeurs level_3 reçues:', values);
      setAvailableLevel3Values(values);
      console.log('✅ [BilanConfigCard] Nombre de valeurs level_3 chargées:', values.length);
    } catch (err: any) {
      console.error('❌ [BilanConfigCard] Erreur lors du chargement des valeurs level_3:', err);
      setAvailableLevel3Values([]);
    } finally {
      setLoadingLevel3Values(false);
    }
  };

  // Gérer le changement de sous-catégorie
  const handleSubCategoryChange = async (mappingId: number, newSubCategory: string) => {
    const mapping = mappings.find(m => m.id === mappingId);
    if (!mapping) return;

    try {
      console.log(`🔄 [BilanConfigCard] Mise à jour de la sous-catégorie pour le mapping ${mappingId}:`, newSubCategory);
      
      // Obtenir la première catégorie de la nouvelle sous-catégorie
      const availableCategories = getAvailableCategoriesForSubCategory(newSubCategory);
      const newCategory = availableCategories[0] || mapping.category_name;
      const newType = getTypeForSubCategory(newSubCategory);
      const isSpecial = isSpecialCategory(newCategory);
      const specialSource = SPECIAL_SOURCE_BY_CATEGORY[newCategory] || null;
      
      // Mettre à jour le mapping via l'API
      await bilanAPI.updateMapping(mappingId, {
        category_name: newCategory,
        type: newType,
        sub_category: newSubCategory,
        is_special: isSpecial,
        special_source: specialSource,
        // Conserver les valeurs existantes si la catégorie n'est pas spéciale
        level_1_values: isSpecial ? null : mapping.level_1_values,
      });
      
      console.log('✅ [BilanConfigCard] Sous-catégorie mise à jour avec succès');
      
      // Mettre à jour le Type dans l'état local
      setMappingTypes(prev => ({
        ...prev,
        [mappingId]: newType
      }));
      
      // Recharger les mappings pour avoir les données à jour
      await loadMappings();
      
      // Générer les données du bilan pour toutes les années après modification
      await regenerateBilanData();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [BilanConfigCard] Erreur lors de la mise à jour de la sous-catégorie:', err);
      alert(`❌ Erreur lors de la mise à jour: ${err.message || 'Erreur inconnue'}`);
    }
  };

  // Gérer le changement de catégorie comptable
  const handleCategoryChange = async (mappingId: number, newCategory: string) => {
    const mapping = mappings.find(m => m.id === mappingId);
    if (!mapping) return;

    try {
      console.log(`🔄 [BilanConfigCard] Mise à jour de la catégorie pour le mapping ${mappingId}:`, newCategory);
      
      const subCategory = getSubCategoryForCategory(newCategory);
      if (!subCategory) {
        alert('❌ Sous-catégorie introuvable pour cette catégorie');
        return;
      }
      
      const type = getTypeForSubCategory(subCategory);
      const isSpecial = isSpecialCategory(newCategory);
      const specialSource = SPECIAL_SOURCE_BY_CATEGORY[newCategory] || null;
      
      // Mettre à jour le mapping via l'API
      await bilanAPI.updateMapping(mappingId, {
        category_name: newCategory,
        type: type,
        sub_category: subCategory,
        is_special: isSpecial,
        special_source: specialSource,
        // Conserver les valeurs existantes si la catégorie n'est pas spéciale
        level_1_values: isSpecial ? null : mapping.level_1_values,
      });
      
      console.log('✅ [BilanConfigCard] Catégorie mise à jour avec succès');
      
      // Mettre à jour le Type dans l'état local
      setMappingTypes(prev => ({
        ...prev,
        [mappingId]: type
      }));
      
      // Recharger les mappings pour avoir les données à jour
      await loadMappings();
      
      // Générer les données du bilan pour toutes les années après modification
      await regenerateBilanData();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [BilanConfigCard] Erreur lors de la mise à jour de la catégorie:', err);
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
      console.log('💾 [BilanConfigCard] Ajout de valeur level_1:', value, 'pour mapping:', mappingId, '→', updatedValues);
      
      await bilanAPI.updateMapping(mappingId, {
        category_name: mapping.category_name,
        level_1_values: updatedValues,
      });
      
      console.log('✅ [BilanConfigCard] Valeur level_1 ajoutée avec succès');
      
      // Recharger les mappings
      await loadMappings();
      
      // Générer les données du bilan pour toutes les années après modification
      await regenerateBilanData();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [BilanConfigCard] Erreur lors de l\'ajout de la valeur level_1:', err);
      alert(`❌ Erreur lors de l'ajout: ${err.message || 'Erreur inconnue'}`);
    }
  };

  // Supprimer une valeur level_1 (Step 7.5.5)
  const handleLevel1Remove = async (mappingId: number, value: string) => {
    console.log('🗑️ [BilanConfigCard] handleLevel1Remove appelé avec:', { mappingId, value });
    const mapping = mappings.find(m => m.id === mappingId);
    if (!mapping) {
      console.error('❌ [BilanConfigCard] Mapping non trouvé:', mappingId);
      alert(`❌ Mapping non trouvé pour l'ID: ${mappingId}`);
      return;
    }
    
    try {
      const currentValues = mapping.level_1_values && Array.isArray(mapping.level_1_values) ? mapping.level_1_values : [];
      console.log('🔍 [BilanConfigCard] Valeurs actuelles level_1:', currentValues);
      console.log('🔍 [BilanConfigCard] Valeur à supprimer:', value);
      const updatedValues = currentValues.filter(v => v !== value);
      console.log('🔍 [BilanConfigCard] Valeurs après filtrage:', updatedValues);
      console.log('🗑️ [BilanConfigCard] Suppression de valeur level_1:', value, 'pour mapping:', mappingId, '→', updatedValues);
      
      await bilanAPI.updateMapping(mappingId, {
        category_name: mapping.category_name,
        level_1_values: updatedValues.length > 0 ? updatedValues : null,
      });
      
      console.log('✅ [BilanConfigCard] Valeur level_1 supprimée avec succès');
      
      // Recharger les mappings
      await loadMappings();
      
      // Générer les données du bilan pour toutes les années après modification
      await regenerateBilanData();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [BilanConfigCard] Erreur lors de la suppression de la valeur level_1:', err);
      alert(`❌ Erreur lors de la suppression: ${err.message || 'Erreur inconnue'}`);
    }
  };


  // Ajouter une nouvelle catégorie (Step 7.5.7)
  const handleAddCategory = async () => {
    try {
      // Prendre la première catégorie de "ACTIF" par défaut
      const defaultSubCategory = ACTIF_SUB_CATEGORIES[0]; // "Actif immobilisé"
      const defaultCategory = CATEGORIES_BY_SUB_CATEGORY[defaultSubCategory][0]; // "Immobilisations"
      
      console.log('➕ [BilanConfigCard] Création d\'un nouveau mapping...');
      const newMapping = await bilanAPI.createMapping({
        category_name: defaultCategory,
        type: 'ACTIF',
        sub_category: defaultSubCategory,
        is_special: false,
        level_1_values: null,
      });
      console.log('✅ [BilanConfigCard] Nouveau mapping créé:', newMapping);
      
      // Recharger les mappings
      await loadMappings();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [BilanConfigCard] Erreur lors de la création du mapping:', err);
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
      console.log('🗑️ [BilanConfigCard] Suppression du mapping:', mappingId);
      await bilanAPI.deleteMapping(mappingId);
      console.log('✅ [BilanConfigCard] Mapping supprimé avec succès');
      
      // Recharger les mappings
      await loadMappings();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [BilanConfigCard] Erreur lors de la suppression:', err);
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
      console.log('💾 [BilanConfigCard] Sauvegarde de la vue:', name);

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
      const viewsResponse = await bilanMappingViewsAPI.getAll();
      const existingView = viewsResponse.views.find(v => v.name === name);

      if (existingView) {
        // Vue existante - demander confirmation pour écraser
        const confirmed = window.confirm(
          `Une vue avec le nom "${name}" existe déjà.\n\n` +
          `Voulez-vous l'écraser ?`
        );

        if (confirmed) {
          // Mettre à jour la vue existante
          await bilanMappingViewsAPI.update(existingView.id, {
            view_data: viewData,
          });

          console.log('✅ [BilanConfigCard] Vue écrasée avec succès');

          // Fermer le popup et réinitialiser
          setShowSaveViewPopup(false);
          setSaveViewName('');
        }
        // Si l'utilisateur annule, on ne fait rien (le popup reste ouvert)
      } else {
        // Aucune vue existante - créer une nouvelle vue
        await bilanMappingViewsAPI.create({
          name: name,
          view_data: viewData,
        });

        console.log('✅ [BilanConfigCard] Vue sauvegardée avec succès');

        // Fermer le popup et réinitialiser
        setShowSaveViewPopup(false);
        setSaveViewName('');
      }
    } catch (err: any) {
      console.error('❌ [BilanConfigCard] Erreur lors de la sauvegarde de la vue:', err);

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
      const viewsResponse = await bilanMappingViewsAPI.getAll();
      setAvailableViews(viewsResponse.views.map(v => ({ id: v.id, name: v.name })));
      setShowLoadViewPopup(true);
    } catch (err: any) {
      console.error('❌ [BilanConfigCard] Erreur lors du chargement des vues:', err);
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
      console.log('📥 [BilanConfigCard] Chargement de la vue:', viewId);

      // Récupérer la vue depuis l'API
      const view = await bilanMappingViewsAPI.getById(viewId);
      const viewData = view.view_data;

      // Supprimer tous les mappings existants
      for (const mapping of mappings) {
        try {
          await bilanAPI.deleteMapping(mapping.id);
        } catch (err) {
          console.warn(`⚠️ [BilanConfigCard] Erreur lors de la suppression du mapping ${mapping.id}:`, err);
        }
      }

      // Créer les mappings depuis view_data.mappings
      for (const mappingData of viewData.mappings) {
        try {
          await bilanAPI.createMapping({
            category_name: mappingData.category_name,
            level_1_values: mappingData.level_1_values,
            type: mappingData.type,
            sub_category: mappingData.sub_category,
            is_special: mappingData.is_special,
            special_source: mappingData.special_source,
            amortization_view_id: mappingData.amortization_view_id,
          });
        } catch (err) {
          console.error(`❌ [BilanConfigCard] Erreur lors de la création du mapping ${mappingData.category_name}:`, err);
        }
      }

      // Recharger les mappings
      await loadMappings();

      // Charger selected_level_3_values depuis view_data (Step 9.2)
      if (viewData.selected_level_3_values && Array.isArray(viewData.selected_level_3_values)) {
        setSelectedLevel3Values(viewData.selected_level_3_values);
        console.log('✅ [BilanConfigCard] Level 3 sélectionnés chargés:', viewData.selected_level_3_values);
      } else {
        // Compatibilité avec les vues existantes qui n'ont pas selected_level_3_values
        setSelectedLevel3Values([]);
        console.log('⚠️ [BilanConfigCard] Aucune sélection Level 3 dans la vue, réinitialisation');
      }

      console.log('✅ [BilanConfigCard] Vue chargée avec succès');

      // Fermer le popup
      setShowLoadViewPopup(false);
      setSelectedViewId(null);

      // Notifier le parent
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [BilanConfigCard] Erreur lors du chargement de la vue:', err);
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
      const viewsResponse = await bilanMappingViewsAPI.getAll();
      setAvailableViewsForDelete(viewsResponse.views.map(v => ({ id: v.id, name: v.name })));
      setShowDeleteViewPopup(true);
    } catch (err: any) {
      console.error('❌ [BilanConfigCard] Erreur lors du chargement des vues:', err);
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
      console.log('🗑️ [BilanConfigCard] Suppression de la vue:', viewId);

      // Appeler l'API pour supprimer la vue
      await bilanMappingViewsAPI.delete(viewId);

      console.log('✅ [BilanConfigCard] Vue supprimée avec succès');

      // Retirer la vue de la liste
      const updatedViews = availableViewsForDelete.filter(v => v.id !== viewId);
      setAvailableViewsForDelete(updatedViews);
      setSelectedViewIdForDelete(null);

      // Si la liste est vide, fermer le popup
      if (updatedViews.length === 0) {
        setShowDeleteViewPopup(false);
      }
    } catch (err: any) {
      console.error('❌ [BilanConfigCard] Erreur lors de la suppression de la vue:', err);
      alert(`❌ Erreur lors de la suppression: ${err?.message || 'Erreur inconnue'}`);
    }
  };

  // Gérer le changement de vue d'amortissement (Step 7.5.11)
  const handleAmortizationViewChange = async (mappingId: number, viewId: number | null) => {
    try {
      console.log('🔄 [BilanConfigCard] Changement de vue d\'amortissement:', { mappingId, viewId });
      await bilanAPI.updateMapping(mappingId, {
        amortization_view_id: viewId,
      });
      console.log('✅ [BilanConfigCard] Vue d\'amortissement mise à jour avec succès');
      
      // Recharger les mappings
      await loadMappings();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [BilanConfigCard] Erreur lors de la mise à jour de la vue d\'amortissement:', err);
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
      console.log(`🔄 [BilanConfigCard] Réinitialisation de tous les mappings...`);
      
      // 1. Supprimer tous les mappings existants
      for (const mapping of mappings) {
        console.log(`🗑️ [BilanConfigCard] Suppression du mapping ${mapping.id}: ${mapping.category_name}`);
        await bilanAPI.deleteMapping(mapping.id);
      }
      
      console.log('✅ [BilanConfigCard] Tous les mappings existants ont été supprimés');
      
      // 2. Créer les mappings par défaut pour toutes les catégories prédéfinies
      const allCategories: string[] = [];
      Object.entries(CATEGORIES_BY_SUB_CATEGORY).forEach(([subCategory, categories]) => {
        categories.forEach(category => {
          allCategories.push(category);
        });
      });
      console.log(`➕ [BilanConfigCard] Création des mappings par défaut pour ${allCategories.length} catégories...`);
      
      for (const category of allCategories) {
        const subCategory = getSubCategoryForCategory(category);
        if (!subCategory) continue;
        const type = getTypeForSubCategory(subCategory);
        const isSpecial = isSpecialCategory(category);
        const specialSource = SPECIAL_SOURCE_BY_CATEGORY[category] || null;
        
        console.log(`➕ [BilanConfigCard] Création du mapping pour: ${category} (${type}, ${subCategory})`);
        await bilanAPI.createMapping({
          category_name: category,
          type: type,
          sub_category: subCategory,
          is_special: isSpecial,
          special_source: specialSource,
          level_1_values: null,
        });
      }
      
      console.log(`✅ [BilanConfigCard] ${allCategories.length} mappings par défaut créés`);
      
      // 3. Recharger les mappings
      await loadMappings();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [BilanConfigCard] Erreur lors de la réinitialisation:', err);
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
      // ACTIF avant PASSIF
      return typeA === 'ACTIF' ? -1 : 1;
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
            Configuration du bilan
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
              Level 3 valeurs à inclure dans le bilan
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
                  width: '15%'
                }}>
                  Sous-catégorie
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
                        <option value="ACTIF">ACTIF</option>
                        <option value="PASSIF">PASSIF</option>
                      </select>
                    </td>
                    <td style={{ padding: '12px' }}>
                      <select
                        value={mapping.sub_category || ''}
                        onChange={(e) => handleSubCategoryChange(mapping.id, e.target.value)}
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
                        {getAvailableSubCategoriesForType(type).map((subCategory) => (
                          <option key={subCategory} value={subCategory}>
                            {subCategory}
                          </option>
                        ))}
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
                        {getAvailableCategoriesForSubCategory(mapping.sub_category || '').map((category) => (
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
                                    console.log('🗑️ [BilanConfigCard] Clic sur suppression level_1:', value, 'pour mapping:', mapping.id);
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
                                    console.log('🔍 [BilanConfigCard] Clic sur "+ Ajouter" pour mapping:', mapping.id);
                                    console.log('🔍 [BilanConfigCard] level1Values:', level1Values);
                                    console.log('🔍 [BilanConfigCard] mapping.level_1_values:', mapping.level_1_values);
                                    console.log('🔍 [BilanConfigCard] Valeurs disponibles:', availableValues);
                                    if (selectedLevel3Values.length === 0) {
                                      alert('⚠️ Sélectionnez d\'abord des Level 3 dans le dropdown "Level 3 valeurs à inclure dans le bilan".');
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
                      ) : mapping.category_name === 'Emprunt bancaire (capital restant dû)' ? (
                        // Pour "Emprunt bancaire", afficher "Données calculées" (utilise tous les crédits automatiquement)
                        <span style={{ color: '#9ca3af', fontStyle: 'italic', fontSize: '12px' }}>
                          Données calculées
                        </span>
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

