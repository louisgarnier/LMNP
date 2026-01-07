/**
 * AmortizationConfigCard component - Card de configuration des amortissements
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { transactionsAPI, amortizationTypesAPI, amortizationAPI, amortizationViewsAPI, AmortizationType } from '@/api/client';

interface AmortizationConfigCardProps {
  onConfigUpdated?: () => void;
  onLevel2Change?: (level2Value: string) => void;
  onViewLoaded?: (viewId: number | null) => void; // Callback pour notifier quand une vue est chargée
}

export default function AmortizationConfigCard({ onConfigUpdated, onLevel2Change, onViewLoaded }: AmortizationConfigCardProps) {
  // Récupérer la valeur sauvegardée depuis localStorage, ou chaîne vide par défaut
  const getSavedLevel2Value = (): string => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('amortization_level2_value');
      return saved || '';
    }
    return '';
  };

  // Récupérer l'ID de la vue sauvegardée depuis localStorage
  const getSavedLoadedViewId = (): number | null => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('amortization_loaded_view_id');
      if (saved) {
        const viewId = parseInt(saved, 10);
        return isNaN(viewId) ? null : viewId;
      }
    }
    return null;
  };

  const [level2Value, setLevel2Value] = useState<string>(getSavedLevel2Value());
  const [level2Values, setLevel2Values] = useState<string[]>([]);
  const [loadingValues, setLoadingValues] = useState(false);
  const [amortizationTypes, setAmortizationTypes] = useState<AmortizationType[]>([]);
  const [loadingTypes, setLoadingTypes] = useState(false);
  const [editingNameId, setEditingNameId] = useState<number | null>(null);
  const [editingNameValue, setEditingNameValue] = useState<string>('');
  const [level1Values, setLevel1Values] = useState<string[]>([]);
  const [editingLevel1Id, setEditingLevel1Id] = useState<number | null>(null);
  const [editingDateId, setEditingDateId] = useState<number | null>(null);
  const [editingDateValue, setEditingDateValue] = useState<string>('');
  const [amounts, setAmounts] = useState<Record<number, number>>({});
  const [loadingAmounts, setLoadingAmounts] = useState<Record<number, boolean>>({});
  // Ne pas définir cumulatedAmounts ici, il sera défini plus bas avec restauration depuis localStorage
  const [loadingCumulatedAmounts, setLoadingCumulatedAmounts] = useState<Record<number, boolean>>({});
  const [transactionCounts, setTransactionCounts] = useState<Record<number, number>>({});
  const [loadingTransactionCounts, setLoadingTransactionCounts] = useState<Record<number, boolean>>({});
  const [editingDurationId, setEditingDurationId] = useState<number | null>(null);
  const [editingDurationValue, setEditingDurationValue] = useState<string>('');
  const [editingAnnualAmountId, setEditingAnnualAmountId] = useState<number | null>(null);
  const [editingAnnualAmountValue, setEditingAnnualAmountValue] = useState<string>('');
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; typeId: number } | null>(null);
  const [isAutoRecalculating, setIsAutoRecalculating] = useState(false);
  const [level2ValuesLoaded, setLevel2ValuesLoaded] = useState(false);
  const hasRestoredLevel2 = useRef(false); // Pour ne charger qu'une fois au montage
  const [isViewMenuOpen, setIsViewMenuOpen] = useState(false);
  const viewMenuRef = useRef<HTMLDivElement>(null);
  const [showSaveViewPopup, setShowSaveViewPopup] = useState(false);
  const [saveViewName, setSaveViewName] = useState('');
  const [savingView, setSavingView] = useState(false);
  const [showLoadViewPopup, setShowLoadViewPopup] = useState(false);
  const [availableViews, setAvailableViews] = useState<Array<{ id: number; name: string }>>([]);
  const [loadingViews, setLoadingViews] = useState(false);
  const [selectedViewId, setSelectedViewId] = useState<number | null>(null);
  const [loadingView, setLoadingView] = useState(false);
  const justLoadedViewRef = useRef(false); // Flag pour indiquer qu'on vient de charger une vue
  const [showDeleteViewPopup, setShowDeleteViewPopup] = useState(false);
  const [availableViewsForDelete, setAvailableViewsForDelete] = useState<Array<{ id: number; name: string }>>([]);
  const [loadingViewsForDelete, setLoadingViewsForDelete] = useState(false);
  const [selectedViewIdForDelete, setSelectedViewIdForDelete] = useState<number | null>(null);
  const [deletingView, setDeletingView] = useState(false);
  // État pour stocker l'ID de la vue actuellement chargée (pour utiliser ses résultats sauvegardés)
  // Initialiser depuis localStorage pour persister entre les changements d'onglet
  const [loadedViewId, setLoadedViewId] = useState<number | null>(getSavedLoadedViewId());
  
  // Fonction pour restaurer les montants cumulés depuis localStorage
  const restoreCumulatedAmountsFromStorage = (viewId: number | null): Record<number, number> => {
    if (typeof window !== 'undefined' && viewId !== null && viewId > 0) {
      const key = `amortization_cumulated_amounts_view_${viewId}`;
      const saved = localStorage.getItem(key);
      if (saved) {
        try {
          return JSON.parse(saved);
        } catch (e) {
          console.warn('⚠️ [AmortizationConfigCard] Erreur lors de la restauration depuis localStorage:', e);
        }
      }
    }
    return {};
  };
  
  // Initialiser les montants cumulés depuis localStorage si une vue est chargée
  const [cumulatedAmounts, setCumulatedAmounts] = useState<Record<number, number>>(() => {
    const savedViewId = getSavedLoadedViewId();
    if (savedViewId) {
      return restoreCumulatedAmountsFromStorage(savedViewId);
    }
    return {};
  });
  const [mounted, setMounted] = useState(false);

  // Marquer le composant comme monté après l'hydratation
  useEffect(() => {
    setMounted(true);
    
    // IMPORTANT: Restaurer loadedViewId et cumulatedAmounts depuis localStorage au montage
    // Cela garantit que les valeurs sont restaurées même si le composant est remonté
    const savedViewId = getSavedLoadedViewId();
    if (savedViewId !== null && savedViewId > 0) {
      console.log(`📥 [AmortizationConfigCard] Restauration au montage - vue ${savedViewId} depuis localStorage`);
      setLoadedViewId(savedViewId);
      
      // Restaurer les montants cumulés depuis localStorage
      const restoredAmounts = restoreCumulatedAmountsFromStorage(savedViewId);
      if (Object.keys(restoredAmounts).length > 0) {
        console.log(`📥 [AmortizationConfigCard] Montants cumulés restaurés au montage pour vue ${savedViewId}:`, restoredAmounts);
        setCumulatedAmounts(restoredAmounts);
      } else {
        console.log(`⚠️ [AmortizationConfigCard] Aucun montant cumulé trouvé dans localStorage pour vue ${savedViewId}`);
      }
    } else {
      console.log(`📥 [AmortizationConfigCard] Aucune vue chargée trouvée dans localStorage au montage`);
    }
  }, []);

  // Charger les valeurs uniques de level_2 au montage
  useEffect(() => {
    loadLevel2Values();
  }, []);

  // Charger les types d'amortissement si un Level 2 est restauré depuis localStorage
  // (après que loadLevel2Values soit terminé, seulement au montage initial)
  useEffect(() => {
    if (level2Value && level2ValuesLoaded && !hasRestoredLevel2.current) {
      hasRestoredLevel2.current = true; // Marquer comme restauré
      // Charger les types d'amortissement pour le Level 2 restauré
      loadAmortizationTypes();
      // Notifier le parent du Level 2 restauré
      if (onLevel2Change) {
        onLevel2Change(level2Value);
      }
    }
  }, [level2Value, level2ValuesLoaded]); // Quand level2Value change ou quand les valeurs sont chargées

  // Recharger les valeurs level_1 quand level2Value change
  useEffect(() => {
    if (level2Value) {
      loadLevel1Values();
    } else {
      setLevel1Values([]);
    }
  }, [level2Value]);

  // NOTE: Les chargements automatiques sont désactivés pour éviter de charger les types
  // quand on change le Level 2. Les types seront chargés uniquement quand l'utilisateur
  // ajoutera des Level 1 ou fera d'autres actions explicites.
  
  // Recharger les montants quand les types changent (mais PAS quand level2Value change)
  useEffect(() => {
    console.log('🔍 [AmortizationConfigCard] DEBUG useEffect déclenché', {
      loadingView,
      justLoadedViewRef: justLoadedViewRef.current,
      typesCount: amortizationTypes.length,
      level2Value,
      loadedViewId,
      cumulatedAmountsKeys: Object.keys(cumulatedAmounts),
      loadingCumulatedAmountsKeys: Object.keys(loadingCumulatedAmounts)
    });
    
    // Ne pas se déclencher si on est en train de charger une vue
    // Le chargement de vue gère lui-même le rechargement des montants
    if (loadingView) {
      console.log('⏭️ [AmortizationConfigCard] useEffect ignoré car loadingView=true');
      return;
    }
    
    // Ne pas se déclencher si on vient juste de charger une vue
    // Le chargement de vue gère lui-même le rechargement des montants
    if (justLoadedViewRef.current) {
      console.log('⏭️ [AmortizationConfigCard] useEffect ignoré car on vient de charger une vue');
      return;
    }
    
    // Ne pas se déclencher si les montants cumulés sont déjà en cours de chargement
    // Cela évite de recharger inutilement après le chargement d'une vue
    const isLoadingAny = Object.values(loadingCumulatedAmounts).some(loading => loading);
    if (isLoadingAny) {
      console.log('⏭️ [AmortizationConfigCard] useEffect ignoré car montants cumulés déjà en cours de chargement');
      return;
    }
    
    // Utiliser loadedViewId du state (qui est initialisé depuis localStorage au montage)
    // plutôt que de lire localStorage à chaque fois, pour éviter les problèmes de timing
    const currentViewId = loadedViewId;
    
    console.log('🔍 [AmortizationConfigCard] DEBUG useEffect - currentViewId depuis state:', currentViewId, 'loadedViewId:', loadedViewId);
    
    // IMPORTANT: Si on a une vue chargée, ne JAMAIS recharger les montants cumulés depuis le useEffect
    // Les montants cumulés doivent être chargés uniquement lors du chargement de la vue
    // Cela évite d'écraser les valeurs sauvegardées
    if (currentViewId !== null && currentViewId > 0) {
      console.log('⏭️ [AmortizationConfigCard] useEffect ignoré car vue chargée (ID:', currentViewId, ') - les montants cumulés sont gérés par loadView');
      // Vérifier si les montants cumulés sont déjà dans le state
      const hasCumulatedAmounts = Object.keys(cumulatedAmounts).length > 0;
      if (hasCumulatedAmounts) {
        console.log('🔍 [AmortizationConfigCard] DEBUG useEffect - montants cumulés déjà dans le state:', Object.keys(cumulatedAmounts));
      } else {
        // Si pas dans le state, vérifier localStorage et restaurer si nécessaire
        const key = `amortization_cumulated_amounts_view_${currentViewId}`;
        const saved = typeof window !== 'undefined' ? localStorage.getItem(key) : null;
        if (saved) {
          try {
            const restoredAmounts = JSON.parse(saved);
            console.log(`📥 [AmortizationConfigCard] Restauration des montants cumulés depuis localStorage pour vue ${currentViewId}:`, restoredAmounts);
            setCumulatedAmounts(restoredAmounts);
          } catch (e) {
            console.warn('⚠️ [AmortizationConfigCard] Erreur lors de la restauration depuis localStorage:', e);
          }
        } else {
          console.log('🔍 [AmortizationConfigCard] DEBUG useEffect - montants cumulés pas dans localStorage, key:', key);
        }
      }
      return;
    }
    
    // Si on a des montants cumulés déjà chargés (même sans vue), ne pas recharger inutilement
    const hasCumulatedAmounts = Object.keys(cumulatedAmounts).length > 0;
    if (hasCumulatedAmounts) {
      console.log('⏭️ [AmortizationConfigCard] useEffect ignoré car montants cumulés déjà chargés:', Object.keys(cumulatedAmounts));
      return;
    }
    
    console.log('🔄 [AmortizationConfigCard] useEffect loadAmounts déclenché - APPEL DES FONCTIONS', { 
      typesCount: amortizationTypes.length, 
      level2Value,
      loadedViewId,
      currentViewId, // Valeur depuis localStorage
      hasCumulatedAmounts,
      shouldLoad: amortizationTypes.length > 0 && level2Value 
    });
    if (amortizationTypes.length > 0 && level2Value) {
      console.log('🔍 [AmortizationConfigCard] DEBUG useEffect - AVANT loadCumulatedAmounts, cumulatedAmounts actuel:', cumulatedAmounts);
      loadAmounts();
      // Utiliser currentViewId depuis localStorage pour éviter les problèmes de closure
      loadCumulatedAmounts(undefined, currentViewId);
      console.log('🔍 [AmortizationConfigCard] DEBUG useEffect - APRÈS loadCumulatedAmounts appelé');
      loadTransactionCounts();
    } else {
      console.log('⚠️ [AmortizationConfigCard] loadAmounts non déclenché:', { 
        typesCount: amortizationTypes.length, 
        level2Value 
      });
    }
  }, [amortizationTypes, loadedViewId, loadingView, loadingCumulatedAmounts]); // Ne PAS ajouter cumulatedAmounts pour éviter les boucles

  // Fermer le menu View au clic ailleurs
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

  const loadLevel2Values = async () => {
    try {
      setLoadingValues(true);
      const response = await transactionsAPI.getUniqueValues('level_2');
      setLevel2Values(response.values || []);
      setLevel2ValuesLoaded(true); // Marquer comme chargé
      
      // Ne pas sélectionner automatiquement de valeur par défaut
      // L'utilisateur doit sélectionner manuellement un Level 2
    } catch (err: any) {
      console.error('Erreur lors du chargement des valeurs level_2:', err);
      setLevel2ValuesLoaded(true); // Marquer comme chargé même en cas d'erreur
    } finally {
      setLoadingValues(false);
    }
  };

  const loadLevel1Values = async () => {
    try {
      console.log('🔍 [AmortizationConfigCard] Chargement des valeurs level_1...', level2Value ? `(filtré par level_2=${level2Value})` : '');
      const response = await transactionsAPI.getUniqueValues('level_1', undefined, undefined, level2Value || undefined);
      console.log('✅ [AmortizationConfigCard] Valeurs level_1 reçues:', response.values);
      setLevel1Values(response.values || []);
    } catch (err: any) {
      console.error('❌ [AmortizationConfigCard] Erreur lors du chargement des valeurs level_1:', err);
      alert(`❌ Erreur lors du chargement des valeurs level_1: ${err.message || 'Erreur inconnue'}`);
    }
  };

  // Supprimer tous les level_1_values pour TOUS les autres Level 2 (tous sauf celui sélectionné)
  const resetLevel1ValuesForAllOtherLevel2 = async (selectedLevel2: string) => {
    if (!selectedLevel2) return;
    
    try {
      console.log(`🔄 [AmortizationConfigCard] Réinitialisation des level_1_values pour TOUS les autres Level 2 que "${selectedLevel2}"`);
      const response = await amortizationTypesAPI.getAll();
      
      // Filtrer les types qui ont un Level 2 DIFFÉRENT de celui sélectionné et qui ont des level_1_values non vides
      const typesToReset = response.types.filter(
        t => t.level_2_value && 
        t.level_2_value !== selectedLevel2 &&
        t.level_1_values && 
        Array.isArray(t.level_1_values) && 
        t.level_1_values.length > 0
      );

      if (typesToReset.length === 0) {
        console.log('✅ [AmortizationConfigCard] Aucun type à réinitialiser pour les autres Level 2');
        return;
      }

      console.log(`📋 [AmortizationConfigCard] ${typesToReset.length} type(s) à réinitialiser pour les autres Level 2`);

      // Mettre à jour tous les types en parallèle pour SUPPRIMER les level_1_values EN BASE
      const updatePromises = typesToReset.map(async (type) => {
        try {
          console.log(`🔄 [AmortizationConfigCard] Suppression des Level 1 pour type ${type.id} (${type.name}, Level 2: ${type.level_2_value})`);
          await amortizationTypesAPI.update(type.id, {
            level_1_values: [],
          });
        } catch (err: any) {
          console.error(`❌ [AmortizationConfigCard] Erreur lors de la suppression du type ${type.id}:`, err);
          // On continue même si une mise à jour échoue
        }
      });

      await Promise.all(updatePromises);
      console.log('✅ [AmortizationConfigCard] Suppression terminée pour tous les autres Level 2');

    } catch (err: any) {
      console.error('❌ [AmortizationConfigCard] Erreur lors de la suppression des Level 1 pour les autres Level 2:', err);
      // Erreur silencieuse, on continue quand même
    }
  };

  const handleLevel2Change = async (value: string) => {
    // Ne pas permettre de désélectionner (value vide) si un Level 2 est déjà sélectionné
    if (!value && level2Value) {
      return; // Ignorer la désélection
    }
    
    // Si aucun Level 2 n'était sélectionné avant (première sélection)
    const isFirstSelection = !level2Value;
    
    // Si on change de Level 2 (il y avait déjà un Level 2 sélectionné)
    const isChanging = level2Value && value && level2Value !== value;
    
    // Si c'est un changement, demander confirmation
    if (isChanging) {
      const confirmed = window.confirm(
        'Clear previous amortisations?\n\n' +
        'Cette action va :\n' +
        '- Supprimer tous les types d\'amortissement pour TOUS les Level 2\n' +
        '- Créer les 7 types par défaut pour le nouveau Level 2 sélectionné\n\n' +
        'Cette action est irréversible.'
      );
      
      // Si l'utilisateur refuse, annuler le changement (rester sur l'ancien Level 2)
      if (!confirmed) {
        return; // Ne pas changer le Level 2
      }
      
      // Si confirmé, supprimer TOUS les types d'amortissement pour TOUS les Level 2
      try {
        console.log('🗑️ [AmortizationConfigCard] Suppression de tous les types d\'amortissement pour tous les Level 2');
        
        // 1. D'abord supprimer tous les résultats d'amortissement (pour éviter les erreurs de contrainte)
        console.log('🗑️ [AmortizationConfigCard] Suppression de tous les résultats d\'amortissement...');
        const deleteResultsResponse = await amortizationAPI.deleteAllResults();
        console.log(`✅ [AmortizationConfigCard] ${deleteResultsResponse.deleted_count} résultat(s) d'amortissement supprimé(s)`);
        
        // 2. Ensuite supprimer tous les types d'amortissement
        const response = await amortizationTypesAPI.getAll();
        console.log(`🗑️ [AmortizationConfigCard] ${response.types.length} type(s) à supprimer`);
        
        // Supprimer tous les types
        const deletePromises = response.types.map(async (type) => {
          try {
            await amortizationTypesAPI.delete(type.id);
            console.log(`✅ [AmortizationConfigCard] Type ${type.id} (${type.name}) supprimé`);
          } catch (err: any) {
            console.error(`❌ [AmortizationConfigCard] Erreur lors de la suppression du type ${type.id} (${type.name}):`, err);
            throw err; // Propager l'erreur pour arrêter le processus
          }
        });
        await Promise.all(deletePromises);
        console.log('✅ [AmortizationConfigCard] Tous les types d\'amortissement supprimés');
      } catch (err: any) {
        console.error('❌ [AmortizationConfigCard] Erreur lors de la suppression de tous les types:', err);
        alert(`❌ Erreur lors de la suppression: ${err.message || 'Erreur inconnue'}`);
        return; // Annuler le changement en cas d'erreur
      }
    }
    
    // 1. Changer le Level 2 sélectionné et sauvegarder dans localStorage
    setLevel2Value(value);
    // Sauvegarder dans localStorage pour restaurer au prochain chargement
    if (typeof window !== 'undefined') {
      if (value) {
        localStorage.setItem('amortization_level2_value', value);
      } else {
        localStorage.removeItem('amortization_level2_value');
      }
    }
    
    // 2. Vider les cards
    setAmortizationTypes([]);
    setAmounts({});
    console.log('🚨 [AmortizationConfigCard] DEBUG - setCumulatedAmounts({}) appelé - VIDAGE DES MONTANTS CUMULÉS');
    console.trace('🚨 [AmortizationConfigCard] Stack trace du vidage');
    setCumulatedAmounts({});
    setTransactionCounts({});
    
    // 3. Si un Level 2 est sélectionné, créer les 7 types par défaut
    if (value) {
      // Si on vient de changer de Level 2 et de supprimer tous les types, créer FORCÉMENT les 7 types
      // Sinon, vérifier si des types existent déjà
      if (isChanging) {
        // Après suppression de tous les types, créer FORCÉMENT les 7 types par défaut
        console.log(`➕ [AmortizationConfigCard] Création FORCÉE des 7 types par défaut pour Level 2 "${value}" (après changement)`);
        await createInitialTypes([], value); // Passer value explicitement
        // Recharger directement les types depuis l'API
        const newResponse = await amortizationTypesAPI.getAll();
        const filteredTypes = newResponse.types.filter(t => t.level_2_value === value);
        setAmortizationTypes(filteredTypes);
      } else {
        // Première sélection : vérifier si des types existent déjà
        const response = await amortizationTypesAPI.getAll();
        const existingTypes = response.types.filter(t => t.level_2_value === value);
        
        // Si aucun type n'existe, créer les 7 types par défaut
        if (existingTypes.length === 0) {
          console.log(`➕ [AmortizationConfigCard] Création des 7 types par défaut pour Level 2 "${value}" (première sélection)`);
          await createInitialTypes([], value); // Passer value explicitement
          // Recharger directement les types depuis l'API
          const newResponse = await amortizationTypesAPI.getAll();
          const filteredTypes = newResponse.types.filter(t => t.level_2_value === value);
          setAmortizationTypes(filteredTypes);
        } else {
          // Si des types existent déjà, les charger
          setAmortizationTypes(existingTypes);
        }
      }
    }
    
    // 4. Notifier le parent du changement de Level 2
    if (onLevel2Change) {
      onLevel2Change(value);
    }
    
    // 5. Notifier le parent pour rafraîchir AmortizationTable
    if (onConfigUpdated) {
      onConfigUpdated();
    }
  };

  // Réinitialiser les types d'immobilisation aux 7 valeurs par défaut pour le Level 2 sélectionné
  const resetTypesForLevel2 = async () => {
    if (!level2Value) {
      alert('⚠️ Veuillez d\'abord sélectionner une valeur pour Level 2');
      return;
    }

    const confirmed = window.confirm(
      `Êtes-vous sûr de vouloir réinitialiser les types d'immobilisation pour "${level2Value}" ?\n\n` +
      `Cette action va :\n` +
      `- Supprimer tous les types existants pour ce Level 2\n` +
      `- Créer les 7 types initiaux par défaut\n\n` +
      `Cette action est irréversible.`
    );

    if (!confirmed) return;

    try {
      console.log(`🔄 [AmortizationConfigCard] Réinitialisation complète pour Level 2 "${level2Value}"`);
      
      // 1. D'abord supprimer tous les résultats d'amortissement (pour éviter les erreurs de contrainte)
      console.log('🗑️ [AmortizationConfigCard] Suppression de tous les résultats d\'amortissement...');
      const deleteResultsResponse = await amortizationAPI.deleteAllResults();
      console.log(`✅ [AmortizationConfigCard] ${deleteResultsResponse.deleted_count} résultat(s) d'amortissement supprimé(s)`);
      
      // 2. Récupérer tous les types existants pour ce Level 2
      const response = await amortizationTypesAPI.getAll();
      const typesToDelete = response.types.filter(t => t.level_2_value === level2Value);
      
      // 3. Supprimer tous les types existants pour ce Level 2
      if (typesToDelete.length > 0) {
        console.log(`🗑️ [AmortizationConfigCard] Suppression de ${typesToDelete.length} type(s) existant(s)`);
        const deletePromises = typesToDelete.map(async (type) => {
          try {
            await amortizationTypesAPI.delete(type.id);
            console.log(`✅ [AmortizationConfigCard] Type ${type.id} (${type.name}) supprimé`);
          } catch (err: any) {
            console.error(`❌ [AmortizationConfigCard] Erreur lors de la suppression du type ${type.id} (${type.name}):`, err);
            throw err; // Propager l'erreur pour arrêter le processus
          }
        });
        await Promise.all(deletePromises);
      }
      
      // 4. Réinitialiser tous les montants AVANT de créer les nouveaux types
      setAmounts({});
      console.log('🚨 [AmortizationConfigCard] DEBUG - setCumulatedAmounts({}) appelé - VIDAGE DES MONTANTS CUMULÉS');
    console.trace('🚨 [AmortizationConfigCard] Stack trace du vidage');
    setCumulatedAmounts({});
      setTransactionCounts({});
      
      // 5. Créer les 7 types initiaux (vides, comme au premier chargement)
      console.log(`➕ [AmortizationConfigCard] Création des 7 types initiaux vides pour Level 2 "${level2Value}"`);
      await createInitialTypes([], level2Value); // Passer level2Value explicitement
      
      // 6. Attendre un peu pour que la base de données se synchronise
      await new Promise(resolve => setTimeout(resolve, 200));
      
      // 7. Recharger les types (maintenant vides)
      await loadAmortizationTypes();
      
      // 8. Réinitialiser l'ID de la vue chargée (on n'utilise plus une vue sauvegardée)
      setLoadedViewId(null);
      // Supprimer de localStorage aussi
      if (typeof window !== 'undefined') {
        localStorage.removeItem('amortization_loaded_view_id');
      }
      if (onViewLoaded) {
        onViewLoaded(null);
      }
      
      // 9. Notifier le parent pour réinitialiser la table (après tout)
      if (onConfigUpdated) {
        onConfigUpdated();
      }
      
      console.log(`✅ [AmortizationConfigCard] Réinitialisation complète terminée - tout est à 0`);
    } catch (err: any) {
      console.error('❌ [AmortizationConfigCard] Erreur lors de la réinitialisation des types:', err);
      alert(`❌ Erreur lors de la réinitialisation: ${err.message || 'Erreur inconnue'}`);
    }
  };

  const loadAmortizationTypes = async () => {
    try {
      setLoadingTypes(true);
      const response = await amortizationTypesAPI.getAll();
      
      // Filtrer les types par le Level 2 sélectionné
      const filteredTypes = level2Value 
        ? response.types.filter(t => t.level_2_value === level2Value)
        : [];
      
      // Si aucun type n'existe pour ce Level 2, créer les 7 types initiaux
      // IMPORTANT : Ne créer que si on n'est pas en train de charger après une suppression
      if (filteredTypes.length === 0 && level2Value) {
        await createInitialTypes(response.types, level2Value);
        // Recharger après création et filtrer à nouveau
        const newResponse = await amortizationTypesAPI.getAll();
        const newFilteredTypes = newResponse.types.filter(t => t.level_2_value === level2Value);
        setAmortizationTypes(newFilteredTypes);
      } else {
        setAmortizationTypes(filteredTypes);
      }
    } catch (err: any) {
      console.error('Erreur lors du chargement des types d\'amortissement:', err);
    } finally {
      setLoadingTypes(false);
    }
  };

  const createInitialTypes = async (existingTypes: AmortizationType[] = [], targetLevel2?: string) => {
    // Utiliser targetLevel2 si fourni, sinon utiliser level2Value depuis l'état
    const targetLevel2Value = targetLevel2 !== undefined ? targetLevel2 : level2Value;
    
    if (!targetLevel2Value) {
      console.warn('⚠️ [AmortizationConfigCard] Impossible de créer les types : aucun Level 2 spécifié');
      return;
    }
    
    const initialTypes = [
      'Part terrain',
      'Immobilisation structure/GO',
      'Immobilisation mobilier',
      'Immobilisation IGT',
      'Immobilisation agencements',
      'Immobilisation Facade/Toiture',
      'Immobilisation travaux',
    ];

    for (const name of initialTypes) {
      // Vérifier si un type avec ce nom et ce level_2_value existe déjà
      const alreadyExists = existingTypes.some(
        t => t.name === name && t.level_2_value === targetLevel2Value
      );
      
      if (alreadyExists) {
        console.log(`ℹ️ [AmortizationConfigCard] Type "${name}" existe déjà pour Level 2 "${targetLevel2Value}", ignoré`);
        continue;
      }

      try {
        await amortizationTypesAPI.create({
          name,
          level_2_value: targetLevel2Value,
          level_1_values: [],
          start_date: null,
          duration: 0,
          annual_amount: null,
        });
        console.log(`✅ [AmortizationConfigCard] Type "${name}" créé pour Level 2 "${targetLevel2Value}"`);
      } catch (err: any) {
        console.error(`❌ [AmortizationConfigCard] Erreur lors de la création du type ${name}:`, err);
      }
    }
  };

  const handleNameEditStart = (type: AmortizationType) => {
    setEditingNameId(type.id);
    setEditingNameValue(type.name);
  };

  const handleNameEditSave = async (typeId: number) => {
    try {
      await amortizationTypesAPI.update(typeId, {
        name: editingNameValue,
      });
      // Recharger les types
      await loadAmortizationTypes();
      setEditingNameId(null);
      setEditingNameValue('');
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('Erreur lors de la sauvegarde du nom:', err);
      alert(`❌ Erreur lors de la sauvegarde: ${err.message || 'Erreur inconnue'}`);
    }
  };

  const handleNameEditCancel = () => {
    setEditingNameId(null);
    setEditingNameValue('');
  };

  const handleLevel1Add = async (typeId: number, value: string) => {
    if (!value) return;
    
    const type = amortizationTypes.find(t => t.id === typeId);
    if (!type) return;
    
    // Vérifier que la valeur n'est pas déjà présente
    const currentValues = type.level_1_values && Array.isArray(type.level_1_values) ? type.level_1_values : [];
    if (currentValues.includes(value)) return;
    
    try {
      const updatedValues = [...currentValues, value];
      console.log('💾 [AmortizationConfigCard] Ajout de valeur level_1:', value, 'pour type:', typeId, '→', updatedValues);
      await amortizationTypesAPI.update(typeId, {
        level_1_values: updatedValues,
      });
      
      // Recalculer complètement le type (montant, annuité, cumulé)
      await recalculateTypeComplete(typeId);
    } catch (err: any) {
      console.error('❌ [AmortizationConfigCard] Erreur lors de l\'ajout de la valeur level_1:', err);
      alert(`❌ Erreur lors de l'ajout: ${err.message || 'Erreur inconnue'}`);
    }
  };

  const handleLevel1Remove = async (typeId: number, value: string) => {
    const type = amortizationTypes.find(t => t.id === typeId);
    if (!type) return;
    
    try {
      const currentValues = type.level_1_values && Array.isArray(type.level_1_values) ? type.level_1_values : [];
      const updatedValues = currentValues.filter(v => v !== value);
      console.log('🗑️ [AmortizationConfigCard] Suppression de valeur level_1:', value, 'pour type:', typeId, '→', updatedValues);
      await amortizationTypesAPI.update(typeId, {
        level_1_values: updatedValues,
      });
      
      // Recalculer complètement le type (montant, annuité, cumulé)
      await recalculateTypeComplete(typeId);
    } catch (err: any) {
      console.error('❌ [AmortizationConfigCard] Erreur lors de la suppression de la valeur level_1:', err);
      alert(`❌ Erreur lors de la suppression: ${err.message || 'Erreur inconnue'}`);
    }
  };

  const handleDateEditStart = (type: AmortizationType) => {
    setEditingDateId(type.id);
    // Convertir la date en format YYYY-MM-DD pour l'input date
    if (type.start_date) {
      const date = new Date(type.start_date);
      setEditingDateValue(date.toISOString().split('T')[0]);
    } else {
      setEditingDateValue('');
    }
  };

  const handleDateEditSave = async (typeId: number) => {
    try {
      const dateValue = editingDateValue ? editingDateValue : null;
      console.log('💾 [AmortizationConfigCard] Sauvegarde de date de début:', dateValue, 'pour type:', typeId);
      await amortizationTypesAPI.update(typeId, {
        start_date: dateValue,
      });
      setEditingDateId(null);
      setEditingDateValue('');
      
      // Recalculer complètement le type (montant, annuité, cumulé)
      await recalculateTypeComplete(typeId);
    } catch (err: any) {
      console.error('❌ [AmortizationConfigCard] Erreur lors de la sauvegarde de la date:', err);
      alert(`❌ Erreur lors de la sauvegarde: ${err.message || 'Erreur inconnue'}`);
    }
  };

  const handleDateEditCancel = () => {
    setEditingDateId(null);
    setEditingDateValue('');
  };

  const handleDurationEditStart = (type: AmortizationType) => {
    setEditingDurationId(type.id);
    setEditingDurationValue(type.duration.toString());
  };

  const handleDurationEditSave = async (typeId: number) => {
    try {
      const durationValue = parseFloat(editingDurationValue);
      if (isNaN(durationValue) || durationValue < 0) {
        alert('⚠️ La durée doit être un nombre positif');
        setEditingDurationId(null);
        setEditingDurationValue('');
        return;
      }
      
      console.log('💾 [AmortizationConfigCard] Sauvegarde de durée:', durationValue, 'pour type:', typeId);
      
      await amortizationTypesAPI.update(typeId, {
        duration: durationValue,
      });
      setEditingDurationId(null);
      setEditingDurationValue('');
      
      // Recalculer complètement le type (montant, annuité, cumulé)
      // Forcer le recalcul de l'annuité car la durée a changé
      await recalculateTypeComplete(typeId, true);
    } catch (err: any) {
      console.error('❌ [AmortizationConfigCard] Erreur lors de la sauvegarde de la durée:', err);
      alert(`❌ Erreur lors de la sauvegarde: ${err.message || 'Erreur inconnue'}`);
    }
  };

  const handleDurationEditCancel = () => {
    setEditingDurationId(null);
    setEditingDurationValue('');
  };

  const handleAnnualAmountEditStart = (type: AmortizationType) => {
    setEditingAnnualAmountId(type.id);
    // Afficher la valeur actuelle ou calculer si nécessaire
    const amount = amounts[type.id] || 0;
    const duration = type.duration || 0;
    let displayValue = '';
    
    if (type.annual_amount !== null && type.annual_amount !== undefined) {
      displayValue = type.annual_amount.toString();
    } else if (amount > 0 && duration > 0) {
      displayValue = (amount / duration).toString();
    } else {
      displayValue = '0';
    }
    
    setEditingAnnualAmountValue(displayValue);
  };

  const handleAnnualAmountEditSave = async (typeId: number) => {
    try {
      const annualAmountValue = parseFloat(editingAnnualAmountValue);
      if (isNaN(annualAmountValue) || annualAmountValue < 0) {
        alert('⚠️ L\'annuité doit être un nombre positif');
        setEditingAnnualAmountId(null);
        setEditingAnnualAmountValue('');
        return;
      }
      
      console.log('💾 [AmortizationConfigCard] Sauvegarde d\'annuité:', annualAmountValue, 'pour type:', typeId);
      
      await amortizationTypesAPI.update(typeId, {
        annual_amount: annualAmountValue,
      });
      await loadAmortizationTypes();
      setEditingAnnualAmountId(null);
      setEditingAnnualAmountValue('');
      
      // Déclencher le recalcul automatique des amortissements
      await triggerAutoRecalculate();
    } catch (err: any) {
      console.error('❌ [AmortizationConfigCard] Erreur lors de la sauvegarde de l\'annuité:', err);
      alert(`❌ Erreur lors de la sauvegarde: ${err.message || 'Erreur inconnue'}`);
    }
  };

  const handleAnnualAmountEditCancel = () => {
    setEditingAnnualAmountId(null);
    setEditingAnnualAmountValue('');
  };

  // Créer un nouveau type d'amortissement
  const handleAddType = async () => {
    if (!level2Value) {
      alert('⚠️ Veuillez d\'abord sélectionner une valeur pour Level 2');
      return;
    }

    try {
      console.log('➕ [AmortizationConfigCard] Création d\'un nouveau type d\'amortissement...');
      const newType = await amortizationTypesAPI.create({
        name: 'Nouveau type',
        level_2_value: level2Value,
        level_1_values: [],
        start_date: null,
        duration: 0,
        annual_amount: null,
      });
      console.log('✅ [AmortizationConfigCard] Nouveau type créé:', newType);
      
      // Recharger les types
      await loadAmortizationTypes();
      
      // Recharger les montants
      await loadAmounts();
      await loadCumulatedAmounts();
      await loadTransactionCounts();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [AmortizationConfigCard] Erreur lors de la création du type:', err);
      alert(`❌ Erreur lors de la création: ${err.message || 'Erreur inconnue'}`);
    }
  };

  // Gérer le clic droit pour afficher le menu contextuel
  const handleContextMenu = (e: React.MouseEvent<HTMLTableRowElement>, typeId: number) => {
    e.preventDefault();
    setContextMenu({ x: e.clientX, y: e.clientY, typeId });
  };

  // Fermer le menu contextuel
  const handleCloseContextMenu = () => {
    setContextMenu(null);
  };

  // Supprimer un type d'amortissement
  const handleDeleteType = async (typeId: number) => {
    const type = amortizationTypes.find(t => t.id === typeId);
    if (!type) return;

    // Confirmation
    const confirmed = window.confirm(
      `Êtes-vous sûr de vouloir supprimer le type "${type.name}" ?\n\n` +
      `Cette action est irréversible. Si ce type est utilisé dans des amortissements, la suppression échouera.`
    );

    if (!confirmed) {
      handleCloseContextMenu();
      return;
    }

    try {
      console.log('🗑️ [AmortizationConfigCard] Suppression du type d\'amortissement:', typeId);
      await amortizationTypesAPI.delete(typeId);
      console.log('✅ [AmortizationConfigCard] Type supprimé avec succès');
      
      // Recharger les types et filtrer par level2Value (comme loadAmortizationTypes)
      const newTypesResponse = await amortizationTypesAPI.getAll();
      const filteredTypes = level2Value 
        ? newTypesResponse.types.filter(t => t.level_2_value === level2Value)
        : [];
      
      // Mettre à jour l'état avec les types filtrés (PAS de création automatique après suppression)
      setAmortizationTypes(filteredTypes);
      
      // Recharger les montants avec les types filtrés uniquement
      if (filteredTypes.length > 0) {
        await loadAmounts(filteredTypes);
        await loadCumulatedAmounts(filteredTypes);
        await loadTransactionCounts(filteredTypes);
      } else {
        // Si plus aucun type, réinitialiser les montants
        setAmounts({});
        console.log('🚨 [AmortizationConfigCard] DEBUG - setCumulatedAmounts({}) appelé - VIDAGE DES MONTANTS CUMULÉS');
    console.trace('🚨 [AmortizationConfigCard] Stack trace du vidage');
    setCumulatedAmounts({});
        setTransactionCounts({});
      }
      
      handleCloseContextMenu();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [AmortizationConfigCard] Erreur lors de la suppression du type:', err);
      
      // Extraire le message d'erreur
      let errorMessage = 'Erreur inconnue';
      if (err?.message) {
        errorMessage = err.message;
      } else if (typeof err === 'string') {
        errorMessage = err;
      }
      
      // Afficher le message d'erreur approprié
      if (errorMessage.includes('utilisé') || errorMessage.includes('référencé') || errorMessage.includes('résultat')) {
        alert(`❌ ${errorMessage}`);
      } else {
        alert(`❌ Erreur lors de la suppression: ${errorMessage}`);
      }
      handleCloseContextMenu();
    }
  };

  // Fermer le menu contextuel quand on clique ailleurs
  useEffect(() => {
    const handleClickOutside = () => {
      if (contextMenu) {
        handleCloseContextMenu();
      }
    };

    if (contextMenu) {
      document.addEventListener('click', handleClickOutside);
      return () => {
        document.removeEventListener('click', handleClickOutside);
      };
    }
  }, [contextMenu]);

  // Sauvegarder la vue actuelle
  const saveCurrentView = async (name: string) => {
    if (!name || name.trim() === '') {
      alert('⚠️ Le nom de la vue ne peut pas être vide');
      return;
    }

    if (!level2Value) {
      alert('⚠️ Veuillez sélectionner un Level 2 avant de sauvegarder une vue');
      return;
    }

    // Collecter tous les types d'amortissement actuels avec leurs configs
    // (défini avant le try pour être accessible dans le catch)
    const viewData = {
      level_2_value: level2Value,
      amortization_types: amortizationTypes.map(type => ({
        name: type.name,
        level_1_values: type.level_1_values || [],
        start_date: type.start_date || null,
        duration: type.duration,
        annual_amount: type.annual_amount || null,
      })),
    };

    try {
      setSavingView(true);
      console.log('💾 [AmortizationConfigCard] Sauvegarde de la vue:', name);

      // Vérifier d'abord si une vue avec ce nom existe déjà
      const viewsResponse = await amortizationViewsAPI.getAll(level2Value);
      const existingView = viewsResponse.views.find(v => v.name === name.trim());

      if (existingView) {
        // Une vue avec ce nom existe déjà - proposer de l'écraser
        const confirmed = window.confirm(
          `Une vue avec le nom "${name}" existe déjà pour ce Level 2.\n\n` +
          `Voulez-vous écraser la sauvegarde existante ?`
        );
        
        if (confirmed) {
              // Mettre à jour la vue existante
              await amortizationViewsAPI.update(existingView.id, {
                view_data: viewData,
              });
              
              console.log('✅ [AmortizationConfigCard] Vue écrasée avec succès');
              
              // Fermer le popup et réinitialiser
              setShowSaveViewPopup(false);
              setSaveViewName('');
        }
        // Si l'utilisateur annule, on ne fait rien (le popup reste ouvert)
      } else {
        // Aucune vue existante - créer une nouvelle vue
        await amortizationViewsAPI.create({
          name: name.trim(),
          level_2_value: level2Value,
          view_data: viewData,
        });

        console.log('✅ [AmortizationConfigCard] Vue sauvegardée avec succès');
        
        // Fermer le popup et réinitialiser
        setShowSaveViewPopup(false);
        setSaveViewName('');
      }
    } catch (err: any) {
      console.error('❌ [AmortizationConfigCard] Erreur lors de la sauvegarde de la vue:', err);
      
      // Extraire le message d'erreur
      let errorMessage = 'Erreur inconnue';
      if (err?.message) {
        errorMessage = err.message;
      } else if (typeof err === 'string') {
        errorMessage = err;
      }
      
      alert(`❌ Erreur lors de la sauvegarde: ${errorMessage}`);
    } finally {
      setSavingView(false);
    }
  };

  // Ouvrir le popup Save view
  const handleOpenSaveView = () => {
    setIsViewMenuOpen(false);
    setSaveViewName('');
    setShowSaveViewPopup(true);
  };

  // Ouvrir le popup Load view
  const handleOpenLoadView = async () => {
    setIsViewMenuOpen(false);
    setSelectedViewId(null);
    
    if (!level2Value) {
      alert('⚠️ Veuillez sélectionner un Level 2 avant de charger une vue');
      return;
    }

    try {
      setLoadingViews(true);
      const viewsResponse = await amortizationViewsAPI.getAll(level2Value);
      setAvailableViews(viewsResponse.views.map(v => ({ id: v.id, name: v.name })));
      setShowLoadViewPopup(true);
    } catch (err: any) {
      console.error('❌ [AmortizationConfigCard] Erreur lors du chargement des vues:', err);
      alert(`❌ Erreur lors du chargement des vues: ${err?.message || 'Erreur inconnue'}`);
    } finally {
      setLoadingViews(false);
    }
  };

  // Charger une vue
  const loadView = async (viewId: number | null) => {
    if (viewId === null) {
      // "(default)" sélectionné - réinitialiser la vue chargée
      setLoadedViewId(null);
      // Supprimer de localStorage aussi
      if (typeof window !== 'undefined') {
        localStorage.removeItem('amortization_loaded_view_id');
      }
      if (onViewLoaded) {
        onViewLoaded(null);
      }
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
      // IMPORTANT: Réinitialiser le flag au début du chargement pour éviter les problèmes
      justLoadedViewRef.current = false;
      setLoadingView(true);
      console.log('📥 [AmortizationConfigCard] Chargement de la vue:', viewId);

      // Récupérer la vue depuis l'API
      const view = await amortizationViewsAPI.getById(viewId);
      
      // Récupérer level_2_value et view_data
      const targetLevel2 = view.level_2_value;
      const viewData = view.view_data;

      // Changer le Level 2 sélectionné si nécessaire
      if (targetLevel2 !== level2Value) {
        console.log(`🔄 [AmortizationConfigCard] Changement de Level 2: ${level2Value} → ${targetLevel2}`);
        if (onLevel2Change) {
          onLevel2Change(targetLevel2);
        }
        setLevel2Value(targetLevel2);
        if (typeof window !== 'undefined') {
          localStorage.setItem('amortization_level2_value', targetLevel2);
        }
        // Attendre un peu pour que le Level 2 soit mis à jour dans la page
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      // Supprimer tous les types existants pour ce Level 2
      const currentTypes = amortizationTypes.filter(t => t.level_2_value === targetLevel2);
      for (const type of currentTypes) {
        try {
          await amortizationTypesAPI.delete(type.id);
        } catch (err) {
          console.warn(`⚠️ [AmortizationConfigCard] Erreur lors de la suppression du type ${type.id}:`, err);
        }
      }

      // NE PLUS supprimer les résultats d'amortissement - ils sont isolés par vue
      // Les résultats de cette vue sont déjà sauvegardés et seront utilisés directement

      // Créer les types depuis view_data.amortization_types
      const newTypes: AmortizationType[] = [];
      for (const typeData of viewData.amortization_types) {
        try {
          const createdType = await amortizationTypesAPI.create({
            name: typeData.name,
            level_2_value: targetLevel2,
            level_1_values: typeData.level_1_values || [],
            start_date: typeData.start_date || null,
            duration: typeData.duration,
            annual_amount: typeData.annual_amount || null,
          });
          newTypes.push(createdType);
        } catch (err) {
          console.error(`❌ [AmortizationConfigCard] Erreur lors de la création du type ${typeData.name}:`, err);
        }
      }

      // Recharger les types depuis l'API pour avoir les IDs corrects
      const reloadedTypesResponse = await amortizationTypesAPI.getAll();
      const reloadedTypes = reloadedTypesResponse.types.filter(t => t.level_2_value === targetLevel2);
      
      // IMPORTANT: Définir loadedViewId AVANT de mettre à jour amortizationTypes
      // pour que le useEffect utilise la bonne valeur quand il se déclenche
      setLoadedViewId(viewId);
      // Sauvegarder dans localStorage aussi
      if (typeof window !== 'undefined') {
        if (viewId !== null) {
          localStorage.setItem('amortization_loaded_view_id', viewId.toString());
        } else {
          localStorage.removeItem('amortization_loaded_view_id');
        }
      }
      
      // Maintenant mettre à jour les types (cela déclenchera le useEffect avec la bonne loadedViewId)
      setAmortizationTypes(reloadedTypes);

      // IMPORTANT: Mettre à jour la vue avec les types recréés pour recalculer les résultats
      // Cela garantit que les résultats d'amortissement sont à jour avec les types actuels
      if (reloadedTypes.length > 0) {
        console.log(`🔄 [AmortizationConfigCard] Mise à jour de la vue ${viewId} pour recalculer les résultats...`);
        try {
          // Construire view_data depuis les types recréés
          const viewData = {
            amortization_types: reloadedTypes.map(type => {
              // Convertir start_date en string si c'est un objet Date, sinon utiliser tel quel
              let startDateStr: string | null = null;
              if (type.start_date) {
                if (type.start_date instanceof Date) {
                  startDateStr = type.start_date.toISOString().split('T')[0];
                } else if (typeof type.start_date === 'string') {
                  startDateStr = type.start_date.split('T')[0]; // Enlever l'heure si présente
                }
              }
              
              return {
                name: type.name,
                level_1_values: type.level_1_values || [],
                start_date: startDateStr,
                duration: type.duration,
                annual_amount: type.annual_amount
              };
            })
          };
          
          // Mettre à jour la vue (cela déclenchera automatiquement le recalcul des résultats)
          await amortizationViewsAPI.update(viewId, {
            view_data: viewData
          });
          
          console.log(`✅ [AmortizationConfigCard] Vue ${viewId} mise à jour - résultats recalculés`);
          
          // Attendre un peu pour que les résultats soient bien calculés en base
          await new Promise(resolve => setTimeout(resolve, 500));
        } catch (viewError: any) {
          console.warn(`⚠️ [AmortizationConfigCard] Erreur lors de la mise à jour de la vue ${viewId}:`, viewError);
          // Ne pas faire échouer le chargement de la vue si la mise à jour échoue
          // Les résultats existants seront utilisés
        }
      }

      // Recharger les montants avec la vue chargée
      // IMPORTANT: Passer viewId directement car setLoadedViewId est asynchrone
      // IMPORTANT: Attendre un peu pour que React ait mis à jour le state avant de charger
      await new Promise(resolve => setTimeout(resolve, 100));
      
      if (reloadedTypes.length > 0) {
        console.log(`🔄 [AmortizationConfigCard] Chargement des montants pour ${reloadedTypes.length} types avec vue ${viewId}`);
        await loadAmounts(reloadedTypes);
        console.log(`🔄 [AmortizationConfigCard] Chargement des montants cumulés pour vue ${viewId}`);
        // IMPORTANT: Marquer qu'on vient de charger une vue AVANT de charger les montants cumulés
        // pour empêcher le useEffect de se déclencher et d'écraser les valeurs
        justLoadedViewRef.current = true;
        
        // IMPORTANT: Attendre un peu plus pour que les types soient bien dans le state
        await new Promise(resolve => setTimeout(resolve, 200));
        // Appeler loadCumulatedAmounts avec les types et le viewId
        await loadCumulatedAmounts(reloadedTypes, viewId);
        console.log(`✅ [AmortizationConfigCard] Montants cumulés chargés pour vue ${viewId}`);
        
        // IMPORTANT: Attendre que les montants cumulés soient bien dans le state
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Vérifier que les montants cumulés ont bien été chargés
        // Lire depuis le state pour vérifier
        console.log('🔍 [AmortizationConfigCard] Vérification des montants cumulés chargés...');
        
        // Garder le flag actif pendant plus longtemps pour éviter que le useEffect ne se déclenche
        // après que setLoadingView(false) soit appelé
        setTimeout(() => {
          justLoadedViewRef.current = false;
          console.log('🔄 [AmortizationConfigCard] Flag justLoadedViewRef réinitialisé');
        }, 2000);
        await loadTransactionCounts(reloadedTypes);
      } else {
        setAmounts({});
        console.log('🚨 [AmortizationConfigCard] DEBUG - setCumulatedAmounts({}) appelé - VIDAGE DES MONTANTS CUMULÉS');
    console.trace('🚨 [AmortizationConfigCard] Stack trace du vidage');
    setCumulatedAmounts({});
        setTransactionCounts({});
      }

      // Notifier le parent de la vue chargée
      if (onViewLoaded) {
        onViewLoaded(viewId);
      }
      console.log(`✅ [AmortizationConfigCard] Vue ${viewId} chargée - utilisation des résultats sauvegardés`);

      console.log('✅ [AmortizationConfigCard] Vue chargée avec succès');
      
      // IMPORTANT: Mettre loadingView à false APRÈS avoir tout mis à jour
      // Le flag justLoadedViewRef est déjà défini plus haut pour empêcher le useEffect de se déclencher
      setLoadingView(false);
      
      // Fermer le popup
      setShowLoadViewPopup(false);
      setSelectedViewId(null);

      // Notifier le parent
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [AmortizationConfigCard] Erreur lors du chargement de la vue:', err);
      alert(`❌ Erreur lors du chargement: ${err?.message || 'Erreur inconnue'}`);
      // En cas d'erreur, mettre loadingView à false aussi
      setLoadingView(false);
    }
  };

  // Ouvrir le popup Delete view
  const handleOpenDeleteView = async () => {
    setIsViewMenuOpen(false);
    setSelectedViewIdForDelete(null);
    
    if (!level2Value) {
      alert('⚠️ Veuillez sélectionner un Level 2 avant de supprimer une vue');
      return;
    }

    try {
      setLoadingViewsForDelete(true);
      const viewsResponse = await amortizationViewsAPI.getAll(level2Value);
      setAvailableViewsForDelete(viewsResponse.views.map(v => ({ id: v.id, name: v.name })));
      setShowDeleteViewPopup(true);
    } catch (err: any) {
      console.error('❌ [AmortizationConfigCard] Erreur lors du chargement des vues:', err);
      alert(`❌ Erreur lors du chargement des vues: ${err?.message || 'Erreur inconnue'}`);
    } finally {
      setLoadingViewsForDelete(false);
    }
  };

  // Supprimer une vue
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
      setDeletingView(true);
      console.log('🗑️ [AmortizationConfigCard] Suppression de la vue:', viewId);

      // Appeler l'API pour supprimer la vue
      await amortizationViewsAPI.delete(viewId);

      console.log('✅ [AmortizationConfigCard] Vue supprimée avec succès');
      
      // Retirer la vue de la liste
      const updatedViews = availableViewsForDelete.filter(v => v.id !== viewId);
      setAvailableViewsForDelete(updatedViews);
      setSelectedViewIdForDelete(null);

      // Si la liste est vide, fermer le popup
      if (updatedViews.length === 0) {
        setShowDeleteViewPopup(false);
      }
    } catch (err: any) {
      console.error('❌ [AmortizationConfigCard] Erreur lors de la suppression de la vue:', err);
      alert(`❌ Erreur lors de la suppression: ${err?.message || 'Erreur inconnue'}`);
    } finally {
      setDeletingView(false);
    }
  };

  // Fonction utilitaire pour déclencher le recalcul automatique des amortissements
  const triggerAutoRecalculate = async () => {
    try {
      setIsAutoRecalculating(true);
      console.log('🔄 [AmortizationConfigCard] Déclenchement du recalcul automatique des amortissements...');
      
      // Si une vue est chargée, mettre à jour la vue pour recalculer ses résultats
      if (loadedViewId !== null && loadedViewId > 0) {
        console.log(`📊 [AmortizationConfigCard] Vue chargée (ID: ${loadedViewId}) - mise à jour de la vue pour recalculer ses résultats...`);
        
        try {
          // Récupérer la vue actuelle
          const currentView = await amortizationViewsAPI.getById(loadedViewId);
          
          // Construire view_data depuis les types actuels
          const currentTypes = amortizationTypes.filter(t => t.level_2_value === level2Value);
          const viewData = {
            amortization_types: currentTypes.map(type => {
              // Convertir start_date en string si c'est un objet Date, sinon utiliser tel quel
              let startDateStr: string | null = null;
              if (type.start_date) {
                if (type.start_date instanceof Date) {
                  startDateStr = type.start_date.toISOString().split('T')[0];
                } else if (typeof type.start_date === 'string') {
                  startDateStr = type.start_date.split('T')[0]; // Enlever l'heure si présente
                }
              }
              
              return {
                name: type.name,
                level_1_values: type.level_1_values || [],
                start_date: startDateStr,
                duration: type.duration,
                annual_amount: type.annual_amount
              };
            })
          };
          
          // Mettre à jour la vue (cela déclenchera automatiquement le recalcul des résultats)
          await amortizationViewsAPI.update(loadedViewId, {
            view_data: viewData
          });
          
          console.log(`✅ [AmortizationConfigCard] Vue ${loadedViewId} mise à jour - résultats recalculés`);
        } catch (viewError: any) {
          // Si la vue n'existe plus, réinitialiser loadedViewId et recalculer globalement
          const errorMessage = viewError?.message || String(viewError || '');
          console.log(`🔍 [AmortizationConfigCard] Erreur lors de la mise à jour de la vue:`, {
            message: errorMessage,
            status: viewError?.status,
            error: viewError
          });
          
          const isViewNotFound = 
            errorMessage.includes('non trouvée') || 
            errorMessage.includes('not found') ||
            errorMessage.includes('404') ||
            errorMessage.includes('Vue d\'amortissement') ||
            viewError?.status === 404;
          
          if (isViewNotFound) {
            console.warn(`⚠️ [AmortizationConfigCard] Vue ${loadedViewId} n'existe plus - réinitialisation et recalcul global`);
            setLoadedViewId(null);
            // Supprimer de localStorage aussi
            if (typeof window !== 'undefined') {
              localStorage.removeItem('amortization_loaded_view_id');
            }
            if (onViewLoaded) {
              onViewLoaded(null);
            }
            // Recalculer globalement
            const response = await amortizationAPI.recalculate();
            console.log('✅ [AmortizationConfigCard] Recalcul global terminé:', response.message);
            
            // Recharger les montants cumulés après le recalcul
            await loadCumulatedAmounts();
            
            // Notifier le parent pour rafraîchir le tableau d'amortissements
            if (onConfigUpdated) {
              onConfigUpdated();
            }
            return; // Sortir de la fonction après le recalcul global
          } else {
            // Autre erreur, la propager
            console.error(`❌ [AmortizationConfigCard] Erreur inattendue lors de la mise à jour de la vue:`, viewError);
            throw viewError;
          }
        }
      } else {
        // Aucune vue chargée - recalculer les résultats globaux
        console.log('📊 [AmortizationConfigCard] Aucune vue chargée - recalcul des résultats globaux...');
        const response = await amortizationAPI.recalculate();
        console.log('✅ [AmortizationConfigCard] Recalcul automatique terminé:', response.message);
      }
      
      // Recharger les montants cumulés après le recalcul
      await loadCumulatedAmounts();
      
      // Notifier le parent pour rafraîchir le tableau d'amortissements
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('❌ [AmortizationConfigCard] Erreur lors du recalcul automatique:', err);
      // Ne pas afficher d'alerte pour le recalcul automatique (silencieux)
      // L'utilisateur peut toujours utiliser le bouton manuel si nécessaire
    } finally {
      setIsAutoRecalculating(false);
    }
  };

  // Calculer l'annuité automatiquement pour un type
  const calculateAnnualAmount = (type: AmortizationType): number | null => {
    const amount = amounts[type.id] || 0;
    const duration = type.duration || 0;
    
    console.log(`🔍 [AmortizationConfigCard] Calcul annuité pour type ${type.id} (${type.name}):`, {
      amount,
      duration,
      annual_amount: type.annual_amount,
      hasManualAmount: type.annual_amount !== null && type.annual_amount !== undefined && type.annual_amount !== 0
    });
    
    // PRIORITÉ 1: Si montant = 0, annuité = 0 (TOUJOURS, même si annuité manuelle était définie)
    const absAmount = Math.abs(amount);
    if (absAmount === 0) {
      console.log(`💰 [AmortizationConfigCard] Montant = 0, annuité = 0 pour type ${type.id} (ignore annuité manuelle: ${type.annual_amount})`);
      return 0;
    }
    
    // PRIORITÉ 2: Si une annuité est déjà définie manuellement (et différente de 0), la retourner
    // annual_amount = 0 signifie "pas encore défini", on calcule automatiquement
    if (type.annual_amount !== null && type.annual_amount !== undefined && type.annual_amount > 0) {
      console.log(`✅ [AmortizationConfigCard] Annuité manuelle pour type ${type.id}:`, type.annual_amount);
      return type.annual_amount;
    }
    
    // PRIORITÉ 3: Calculer automatiquement : Montant / Durée
    if (absAmount > 0 && duration > 0) {
      const calculated = absAmount / duration;
      console.log(`💰 [AmortizationConfigCard] Annuité calculée pour type ${type.id}:`, calculated, `(abs(${amount}) / ${duration})`);
      return calculated;
    }
    
    console.log(`⚠️ [AmortizationConfigCard] Impossible de calculer annuité pour type ${type.id}: amount=${amount}, duration=${duration}`);
    return 0; // Retourner 0 au lieu de null pour cohérence
  };

  const loadAmounts = async (typesToLoad?: AmortizationType[]) => {
    const types = typesToLoad || amortizationTypes;
    console.log('🔍 [AmortizationConfigCard] loadAmounts appelé', { level2Value, typesCount: types.length });
    if (!level2Value || types.length === 0) {
      console.log('⚠️ [AmortizationConfigCard] loadAmounts annulé: level2Value ou types manquants');
      return;
    }
    
    const newAmounts: Record<number, number> = {};
    const newLoadingAmounts: Record<number, boolean> = {};
    
    // Marquer tous les types comme en cours de chargement
    types.forEach(type => {
      newLoadingAmounts[type.id] = true;
    });
    setLoadingAmounts(newLoadingAmounts);
    
    console.log('📊 [AmortizationConfigCard] Calcul des montants pour', types.length, 'types');
    
    // Charger les montants pour tous les types en parallèle
    const promises = types.map(async (type) => {
      try {
        console.log(`📤 [AmortizationConfigCard] Appel API pour type ${type.id} (${type.name})`);
        const response = await amortizationTypesAPI.getAmount(type.id);
        console.log(`✅ [AmortizationConfigCard] Montant reçu pour type ${type.id}:`, response.amount);
        newAmounts[type.id] = response.amount;
      } catch (err: any) {
        console.error(`❌ [AmortizationConfigCard] Erreur lors du calcul du montant pour type ${type.id}:`, err);
        newAmounts[type.id] = 0;
      } finally {
        newLoadingAmounts[type.id] = false;
      }
    });
    
    await Promise.all(promises);
    console.log('💾 [AmortizationConfigCard] Montants calculés:', newAmounts);
    setAmounts(newAmounts);
    setLoadingAmounts(newLoadingAmounts);
  };

  const loadCumulatedAmounts = async (typesToLoad?: AmortizationType[], viewIdOverride?: number | null) => {
    const types = typesToLoad || amortizationTypes;
    if (!level2Value || types.length === 0) {
      console.log('⚠️ [AmortizationConfigCard] loadCumulatedAmounts ignoré:', { level2Value, typesCount: types.length });
      return;
    }
    
    // Utiliser viewIdOverride si fourni, sinon lire depuis localStorage pour éviter les problèmes de closure
    let viewIdToUse: number | null | undefined;
    if (viewIdOverride !== undefined) {
      viewIdToUse = viewIdOverride;
    } else {
      // Lire depuis localStorage pour éviter les problèmes de closure avec React batching
      if (typeof window !== 'undefined') {
        const saved = localStorage.getItem('amortization_loaded_view_id');
        if (saved) {
          const viewId = parseInt(saved, 10);
          viewIdToUse = isNaN(viewId) ? null : viewId;
        } else {
          viewIdToUse = null;
        }
      } else {
        viewIdToUse = loadedViewId;
      }
    }
    
    console.log('📊 [AmortizationConfigCard] loadCumulatedAmounts appelé', { 
      typesCount: types.length, 
      viewIdOverride, 
      loadedViewId, 
      viewIdToUse 
    });
    
    const newCumulatedAmounts: Record<number, number> = {};
    const newLoadingCumulatedAmounts: Record<number, boolean> = {};
    
    // Marquer tous les types comme en cours de chargement
    types.forEach(type => {
      newLoadingCumulatedAmounts[type.id] = true;
    });
    setLoadingCumulatedAmounts(newLoadingCumulatedAmounts);
    
    console.log('📊 [AmortizationConfigCard] Calcul des montants cumulés pour', types.length, 'types');
    
    // Charger les montants cumulés pour tous les types en parallèle
    const promises = types.map(async (type) => {
      try {
        console.log(`📤 [AmortizationConfigCard] Appel API cumulated pour type ${type.id} (${type.name}), vue: ${viewIdToUse || 'none'}`);
        const response = await amortizationTypesAPI.getCumulated(type.id, viewIdToUse || undefined);
        console.log(`✅ [AmortizationConfigCard] Montant cumulé reçu pour type ${type.id}:`, response.cumulated_amount);
        newCumulatedAmounts[type.id] = response.cumulated_amount;
      } catch (err: any) {
        console.error(`❌ [AmortizationConfigCard] Erreur lors du calcul du montant cumulé pour type ${type.id}:`, err);
        newCumulatedAmounts[type.id] = 0;
      } finally {
        newLoadingCumulatedAmounts[type.id] = false;
      }
    });
    
    await Promise.all(promises);
    console.log('💾 [AmortizationConfigCard] Montants cumulés calculés:', newCumulatedAmounts);
    console.log('💾 [AmortizationConfigCard] Mise à jour du state avec les montants cumulés');
    console.log('🔍 [AmortizationConfigCard] DEBUG loadCumulatedAmounts - viewIdToUse:', viewIdToUse, 'types count:', types.length);
    
    // IMPORTANT: Sauvegarder dans localStorage AVANT de mettre à jour le state
    // pour que les valeurs persistent même si le composant est remonté
    if (typeof window !== 'undefined' && viewIdToUse !== null && viewIdToUse !== undefined) {
      const key = `amortization_cumulated_amounts_view_${viewIdToUse}`;
      localStorage.setItem(key, JSON.stringify(newCumulatedAmounts));
      console.log('💾 [AmortizationConfigCard] Montants cumulés sauvegardés dans localStorage pour vue', viewIdToUse, 'key:', key);
    }
    
    // IMPORTANT: Mettre à jour le state de manière synchrone pour éviter les problèmes de timing
    // Utiliser une fonction de mise à jour pour éviter d'écraser les valeurs existantes
    setCumulatedAmounts(prev => {
      console.log('🔍 [AmortizationConfigCard] DEBUG setCumulatedAmounts - prev:', prev, 'new:', newCumulatedAmounts);
      const updated = { ...prev, ...newCumulatedAmounts };
      console.log('💾 [AmortizationConfigCard] State mis à jour (merge):', updated);
      return updated;
    });
    setLoadingCumulatedAmounts(newLoadingCumulatedAmounts);
    console.log('✅ [AmortizationConfigCard] State mis à jour avec les montants cumulés - FIN loadCumulatedAmounts');
  };

  const loadTransactionCounts = async (typesToLoad?: AmortizationType[]) => {
    const types = typesToLoad || amortizationTypes;
    if (!level2Value || types.length === 0) return;
    
    // Fusionner avec les compteurs existants au lieu de les remplacer
    const newTransactionCounts: Record<number, number> = { ...transactionCounts };
    const newLoadingTransactionCounts: Record<number, boolean> = { ...loadingTransactionCounts };
    
    // Marquer tous les types à charger comme en cours de chargement
    types.forEach(type => {
      newLoadingTransactionCounts[type.id] = true;
    });
    setLoadingTransactionCounts(newLoadingTransactionCounts);
    
    console.log('📊 [AmortizationConfigCard] Calcul des nombres de transactions pour', types.length, 'types');
    
    // Charger les nombres de transactions pour tous les types en parallèle
    const promises = types.map(async (type) => {
      try {
        console.log(`📤 [AmortizationConfigCard] Appel API transaction-count pour type ${type.id} (${type.name})`);
        const response = await amortizationTypesAPI.getTransactionCount(type.id);
        console.log(`✅ [AmortizationConfigCard] Nombre de transactions reçu pour type ${type.id}:`, response.transaction_count);
        newTransactionCounts[type.id] = response.transaction_count;
      } catch (err: any) {
        console.error(`❌ [AmortizationConfigCard] Erreur lors du calcul du nombre de transactions pour type ${type.id}:`, err);
        newTransactionCounts[type.id] = 0;
      } finally {
        newLoadingTransactionCounts[type.id] = false;
      }
    });
    
    await Promise.all(promises);
    console.log('💾 [AmortizationConfigCard] Nombres de transactions calculés:', newTransactionCounts);
    setTransactionCounts(newTransactionCounts);
    setLoadingTransactionCounts(newLoadingTransactionCounts);
  };

  // Fonction pour recalculer complètement un type d'amortissement
  // Appelée après modification de Level 1, Durée, ou Date
  // forceRecalculateAnnualAmount: si true, force le recalcul de l'annuité même si elle est manuelle
  const recalculateTypeComplete = async (typeId: number, forceRecalculateAnnualAmount: boolean = false) => {
    try {
      console.log(`🔄 [AmortizationConfigCard] Recalcul complet pour type ${typeId}`);
      
      // 1. Recharger le type depuis le backend pour avoir les dernières valeurs
      await loadAmortizationTypes();
      
      // Attendre un peu pour que le state soit mis à jour
      await new Promise(resolve => setTimeout(resolve, 50));
      
      // Recharger à nouveau pour être sûr d'avoir les dernières valeurs
      const refreshedTypesResponse = await amortizationTypesAPI.getAll();
      const type = refreshedTypesResponse.types.find(t => t.id === typeId);
      if (!type) {
        console.warn(`⚠️ [AmortizationConfigCard] Type ${typeId} non trouvé après rechargement`);
        return;
      }
      
      // 2. Charger le montant d'immobilisation directement depuis l'API
      let amount = 0;
      try {
        const amountResponse = await amortizationTypesAPI.getAmount(typeId);
        amount = amountResponse.amount;
        console.log(`💰 [AmortizationConfigCard] Montant d'immobilisation chargé pour type ${typeId}:`, amount);
      } catch (err: any) {
        console.error(`❌ [AmortizationConfigCard] Erreur lors du chargement du montant pour type ${typeId}:`, err);
        amount = 0;
      }
      
      // Mettre à jour le state des montants
      setAmounts(prev => ({ ...prev, [typeId]: amount }));
      
      // 3. Recalculer l'annuité de manière cohérente
      const duration = type.duration || 0;
      let annualAmount: number | null = null;
      
      // Logique cohérente : si montant = 0, alors annuité = 0 (pas de montant = pas d'annuité)
      if (amount === 0) {
        annualAmount = 0;
        console.log(`💰 [AmortizationConfigCard] Montant = 0 → annuité = 0 pour type ${typeId}`);
      } else if (amount > 0 && duration > 0) {
        // Si on force le recalcul OU si l'annuité n'est pas définie manuellement, calculer automatiquement
        if (forceRecalculateAnnualAmount || !type.annual_amount || type.annual_amount === 0) {
          annualAmount = amount / duration;
          console.log(`💰 [AmortizationConfigCard] Annuité recalculée automatiquement pour type ${typeId}:`, annualAmount, `(${amount} / ${duration})`);
        } else {
          // Conserver l'annuité manuelle si elle est définie et qu'on ne force pas le recalcul
          annualAmount = type.annual_amount;
          console.log(`💰 [AmortizationConfigCard] Annuité manuelle conservée pour type ${typeId}:`, annualAmount);
        }
      } else {
        // Montant > 0 mais durée = 0 : annuité = 0 (logique)
        annualAmount = 0;
        console.log(`💰 [AmortizationConfigCard] Montant > 0 mais durée = 0 → annuité = 0 pour type ${typeId}`);
      }
      
      // 4. Mettre à jour le type avec la nouvelle annuité dans la base de données
      const currentAnnualAmount = type.annual_amount ?? 0;
      const newAnnualAmount = annualAmount ?? 0;
      
      // Toujours mettre à jour si la valeur a changé (même si c'est pour mettre à 0)
      if (Math.abs(currentAnnualAmount - newAnnualAmount) > 0.01) {
        console.log(`💾 [AmortizationConfigCard] Mise à jour de l'annuité dans la BD pour type ${typeId}:`, currentAnnualAmount, '→', newAnnualAmount);
        await amortizationTypesAPI.update(typeId, {
          annual_amount: newAnnualAmount,
        });
        // Recharger les types pour avoir la valeur à jour
        await loadAmortizationTypes();
      } else {
        console.log(`ℹ️ [AmortizationConfigCard] Annuité déjà correcte pour type ${typeId}:`, currentAnnualAmount);
      }
      
      // 5. Recharger tous les montants pour garantir la cohérence (pas seulement celui du type modifié)
      await loadAmounts();
      
      // 6. Recharger les montants cumulés pour ce type
      await loadCumulatedAmounts([type]);
      
      // 6.1. Recharger les nombres de transactions pour TOUS les types (pas seulement celui modifié)
      // pour éviter de perdre les compteurs des autres types
      await loadTransactionCounts();
      
      // 7. Déclencher le recalcul des amortissements
      await triggerAutoRecalculate();
      
      console.log(`✅ [AmortizationConfigCard] Recalcul complet terminé pour type ${typeId}`);
    } catch (err: any) {
      console.error(`❌ [AmortizationConfigCard] Erreur lors du recalcul complet pour type ${typeId}:`, err);
      // Ne pas afficher d'alerte, juste logger l'erreur
    }
  };

  return (
    <div
      style={{
        backgroundColor: '#ffffff',
        borderRadius: '8px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        padding: '24px',
        marginBottom: '24px',
        position: 'relative', // Pour positionner le menu
      }}
    >
      <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#111827', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'space-between' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          Configuration des amortissements
          {isAutoRecalculating && (
            <span style={{ fontSize: '14px', color: '#3b82f6', fontStyle: 'italic' }}>
              ⏳ Recalcul en cours...
            </span>
          )}
        </span>
        {/* Icône engrenage */}
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
      </h2>
      
      {/* Champ Level 2 */}
      <div style={{ marginBottom: '24px' }}>
        <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '8px' }}>
          Level 2 (Valeur à considérer comme amortissement)
        </label>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
          <select
            value={level2Value}
            onChange={(e) => handleLevel2Change(e.target.value)}
            disabled={loadingValues}
            style={{
              flex: '1',
              maxWidth: '400px',
              padding: '8px 12px',
              fontSize: '14px',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              backgroundColor: loadingValues ? '#f3f4f6' : '#ffffff',
              color: '#111827',
              cursor: loadingValues ? 'not-allowed' : 'pointer',
            }}
          >
            {loadingValues ? (
              <option>Chargement...</option>
            ) : level2Values.length === 0 ? (
              <option value="">Aucune valeur disponible</option>
            ) : (
              <>
                {/* Afficher "-- Sélectionner une valeur --" uniquement si aucun Level 2 n'est sélectionné */}
                {!level2Value && (
                  <option value="">-- Sélectionner une valeur --</option>
                )}
                {level2Values.map((value) => (
                  <option key={value} value={value}>
                    {value || '(vide)'}
                  </option>
                ))}
              </>
            )}
          </select>
          {mounted && level2Value && (
            <button
              onClick={resetTypesForLevel2}
              disabled={loadingTypes}
              style={{
                padding: '8px 16px',
                fontSize: '14px',
                fontWeight: '600',
                color: '#ffffff',
                backgroundColor: loadingTypes ? '#9ca3af' : '#10b981',
                border: 'none',
                borderRadius: '6px',
                cursor: loadingTypes ? 'not-allowed' : 'pointer',
                boxShadow: loadingTypes ? 'none' : '0 2px 4px rgba(0, 0, 0, 0.1)',
                whiteSpace: 'nowrap',
              }}
              title="Réinitialise les types d'immobilisation aux 7 valeurs par défaut pour ce Level 2"
            >
              {loadingTypes ? '⏳...' : '🔄 Réinitialiser les types'}
            </button>
          )}
        </div>
      </div>

      {/* Tableau des types d'amortissement */}
      {/* Ne rien afficher si aucune valeur Level 2 n'est disponible */}
      {level2Values.length > 0 && (
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
                <th style={{ padding: '6px 8px', textAlign: 'left', fontWeight: '600', color: '#374151', borderRight: '1px solid #e5e7eb', fontSize: '13px' }}>
                  Type d'immobilisation
                </th>
              <th style={{ padding: '6px 8px', textAlign: 'left', fontWeight: '600', color: '#374151', borderRight: '1px solid #e5e7eb', fontSize: '13px' }}>
                Level 1 (valeurs)
              </th>
              <th style={{ padding: '6px 8px', textAlign: 'right', fontWeight: '600', color: '#374151', borderRight: '1px solid #e5e7eb', fontSize: '13px' }}>
                Nombre de transactions
              </th>
              <th style={{ padding: '6px 8px', textAlign: 'left', fontWeight: '600', color: '#374151', borderRight: '1px solid #e5e7eb', fontSize: '13px' }}>
                Date de début
              </th>
              <th style={{ padding: '6px 8px', textAlign: 'right', fontWeight: '600', color: '#374151', borderRight: '1px solid #e5e7eb', fontSize: '13px' }}>
                Montant d'immobilisation
              </th>
              <th style={{ padding: '6px 8px', textAlign: 'right', fontWeight: '600', color: '#374151', borderRight: '1px solid #e5e7eb', fontSize: '13px' }}>
                Durée d'amortissement
              </th>
              <th style={{ padding: '6px 8px', textAlign: 'right', fontWeight: '600', color: '#374151', borderRight: '1px solid #e5e7eb', fontSize: '13px' }}>
                Annuité d'amortissement
              </th>
              <th style={{ padding: '6px 8px', textAlign: 'right', fontWeight: '600', color: '#374151', borderRight: '1px solid #e5e7eb', fontSize: '13px' }}>
                Montant cumulé
              </th>
              <th style={{ padding: '6px 8px', textAlign: 'right', fontWeight: '600', color: '#374151', fontSize: '13px' }}>
                VNC
              </th>
            </tr>
          </thead>
          <tbody>
            {loadingTypes ? (
              <tr>
                <td colSpan={9} style={{ padding: '24px', textAlign: 'center', color: '#6b7280', fontSize: '14px' }}>
                  ⏳ Chargement des types d'amortissement...
                </td>
              </tr>
            ) : amortizationTypes.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ padding: '24px', textAlign: 'center', color: '#6b7280', fontSize: '14px', fontStyle: 'italic' }}>
                  Aucun type d'amortissement configuré
                </td>
              </tr>
            ) : (
              amortizationTypes.map((type) => (
                <tr 
                  key={type.id} 
                  style={{ borderBottom: '1px solid #e5e7eb', cursor: 'context-menu' }}
                  onContextMenu={(e) => handleContextMenu(e, type.id)}
                >
                  {/* Colonne Type d'immobilisation */}
                  <td style={{ padding: '6px 8px', borderRight: '1px solid #e5e7eb' }}>
                    {editingNameId === type.id ? (
                      <input
                        type="text"
                        value={editingNameValue}
                        onChange={(e) => setEditingNameValue(e.target.value)}
                        onBlur={() => handleNameEditSave(type.id)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            handleNameEditSave(type.id);
                          } else if (e.key === 'Escape') {
                            handleNameEditCancel();
                          }
                        }}
                        autoFocus
                        style={{
                          width: '100%',
                          padding: '4px 6px',
                          fontSize: '13px',
                          border: '1px solid #3b82f6',
                          borderRadius: '4px',
                          backgroundColor: '#ffffff',
                        }}
                      />
                    ) : (
                      <div
                        onClick={() => handleNameEditStart(type)}
                        style={{
                          padding: '4px 6px',
                          cursor: 'pointer',
                          borderRadius: '4px',
                          transition: 'background-color 0.2s',
                          fontSize: '13px',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = '#f3f4f6';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'transparent';
                        }}
                        title="Cliquer pour éditer"
                      >
                        {type.name}
                      </div>
                    )}
                  </td>
                  {/* Colonne Level 1 (valeurs) */}
                  <td style={{ padding: '6px 8px', borderRight: '1px solid #e5e7eb', fontSize: '13px' }}>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', alignItems: 'center' }}>
                      {/* Tags des valeurs sélectionnées */}
                      {type.level_1_values && Array.isArray(type.level_1_values) && type.level_1_values.length > 0 ? (
                        type.level_1_values.map((value) => (
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
                              onClick={() => handleLevel1Remove(type.id, value)}
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
                      {editingLevel1Id === type.id ? (
                        <select
                          onChange={(e) => {
                            if (e.target.value) {
                              handleLevel1Add(type.id, e.target.value);
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
                          <option value="">Sélectionner...</option>
                          {level1Values
                            .filter(v => !(type.level_1_values && Array.isArray(type.level_1_values) && type.level_1_values.includes(v)))
                            .map((value) => (
                              <option key={value} value={value}>
                                {value}
                              </option>
                            ))}
                        </select>
                      ) : (
                        <button
                          onClick={() => {
                            console.log('🔍 [AmortizationConfigCard] Clic sur "+ Ajouter" pour type:', type.id);
                            console.log('🔍 [AmortizationConfigCard] level1Values:', level1Values);
                            console.log('🔍 [AmortizationConfigCard] type.level_1_values:', type.level_1_values);
                            const currentValues = type.level_1_values && Array.isArray(type.level_1_values) ? type.level_1_values : [];
                            const availableValues = level1Values.filter(v => !currentValues.includes(v));
                            console.log('🔍 [AmortizationConfigCard] Valeurs disponibles:', availableValues);
                            if (availableValues.length > 0) {
                              setEditingLevel1Id(type.id);
                            } else {
                              alert('⚠️ Toutes les valeurs level_1 sont déjà assignées à ce type, ou aucune valeur level_1 n\'est disponible dans les transactions.');
                            }
                          }}
                          disabled={level1Values.length === 0 || level1Values.filter(v => !(type.level_1_values && Array.isArray(type.level_1_values) && type.level_1_values.includes(v))).length === 0}
                          style={{
                            padding: '2px 6px',
                            fontSize: '11px',
                            border: '1px solid #d1d5db',
                            borderRadius: '4px',
                            backgroundColor: '#f9fafb',
                            color: '#374151',
                            cursor: (level1Values.length > 0 && level1Values.filter(v => !(type.level_1_values && Array.isArray(type.level_1_values) && type.level_1_values.includes(v))).length > 0) ? 'pointer' : 'not-allowed',
                            opacity: (level1Values.length > 0 && level1Values.filter(v => !(type.level_1_values && Array.isArray(type.level_1_values) && type.level_1_values.includes(v))).length > 0) ? 1 : 0.5,
                          }}
                          title={level1Values.length === 0 
                            ? "Aucune valeur level_1 disponible dans les transactions" 
                            : level1Values.filter(v => !(type.level_1_values && Array.isArray(type.level_1_values) && type.level_1_values.includes(v))).length === 0
                            ? "Toutes les valeurs sont déjà assignées"
                            : "Ajouter une valeur"}
                        >
                          + Ajouter
                        </button>
                      )}
                    </div>
                  </td>
                  {/* Colonne Nombre de transactions */}
                  <td style={{ padding: '6px 8px', textAlign: 'right', borderRight: '1px solid #e5e7eb' }}>
                    {loadingTransactionCounts[type.id] ? (
                      <span style={{ color: '#9ca3af', fontSize: '12px' }}>⏳...</span>
                    ) : (
                      <span style={{ fontSize: '13px', fontWeight: '500', color: '#374151' }}>
                        {transactionCounts[type.id] ?? 0}
                      </span>
                    )}
                  </td>
                  {/* Colonne Date de début */}
                  <td style={{ padding: '6px 8px', borderRight: '1px solid #e5e7eb', fontSize: '13px' }}>
                    {editingDateId === type.id ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <input
                          type="date"
                          value={editingDateValue}
                          onChange={(e) => setEditingDateValue(e.target.value)}
                          onBlur={() => handleDateEditSave(type.id)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              handleDateEditSave(type.id);
                            } else if (e.key === 'Escape') {
                              handleDateEditCancel();
                            }
                          }}
                          autoFocus
                          style={{
                            flex: '1',
                            padding: '4px 6px',
                            fontSize: '12px',
                            border: '1px solid #3b82f6',
                            borderRadius: '4px',
                            backgroundColor: '#ffffff',
                          }}
                        />
                        <button
                          onClick={() => {
                            setEditingDateValue('');
                            handleDateEditSave(type.id);
                          }}
                          style={{
                            padding: '2px 6px',
                            fontSize: '11px',
                            border: '1px solid #dc2626',
                            borderRadius: '4px',
                            backgroundColor: '#fee2e2',
                            color: '#dc2626',
                            cursor: 'pointer',
                          }}
                          title="Supprimer la date"
                        >
                          ×
                        </button>
                      </div>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <div
                          onClick={() => handleDateEditStart(type)}
                          style={{
                            flex: '1',
                            padding: '4px 6px',
                            cursor: 'pointer',
                            borderRadius: '4px',
                            transition: 'background-color 0.2s',
                            fontSize: '13px',
                            color: type.start_date ? '#111827' : '#9ca3af',
                            fontStyle: type.start_date ? 'normal' : 'italic',
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.backgroundColor = '#f3f4f6';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.backgroundColor = 'transparent';
                          }}
                          title="Cliquer pour éditer"
                        >
                          {type.start_date 
                            ? new Date(type.start_date).toLocaleDateString('fr-FR', { year: 'numeric', month: '2-digit', day: '2-digit' })
                            : 'Aucune date'}
                        </div>
                        {type.start_date && (
                          <button
                            onClick={async (e) => {
                              e.stopPropagation();
                              try {
                                console.log('🗑️ [AmortizationConfigCard] Suppression de date pour type:', type.id);
                                const updateData: { start_date: null } = { start_date: null };
                                console.log('📤 [AmortizationConfigCard] Données envoyées:', JSON.stringify(updateData));
                                await amortizationTypesAPI.update(type.id, updateData);
                                console.log('✅ [AmortizationConfigCard] Date supprimée avec succès');
                                await loadAmortizationTypes();
                                
                                // Recharger les montants d'immobilisation (la date peut affecter le calcul)
                                await loadAmounts();
                                await loadTransactionCounts();
                                
                                // Déclencher le recalcul automatique des amortissements
                                await triggerAutoRecalculate();
                              } catch (err: any) {
                                console.error('❌ [AmortizationConfigCard] Erreur lors de la suppression de la date:', err);
                                alert(`❌ Erreur lors de la suppression: ${err.message || 'Erreur inconnue'}`);
                              }
                            }}
                            style={{
                              padding: '2px 6px',
                              fontSize: '11px',
                              border: '1px solid #dc2626',
                              borderRadius: '4px',
                              backgroundColor: '#fee2e2',
                              color: '#dc2626',
                              cursor: 'pointer',
                            }}
                            title="Supprimer la date"
                          >
                            ×
                          </button>
                        )}
                      </div>
                    )}
                  </td>
                  {/* Colonne Montant d'immobilisation */}
                  <td style={{ padding: '6px 8px', borderRight: '1px solid #e5e7eb', textAlign: 'right', fontSize: '13px', fontWeight: '500' }}>
                    {loadingAmounts[type.id] ? (
                      <span style={{ color: '#9ca3af', fontStyle: 'italic' }}>⏳ Calcul...</span>
                    ) : (
                      <span style={{ color: '#111827' }}>
                        {amounts[type.id] !== undefined 
                          ? new Intl.NumberFormat('fr-FR', { 
                              style: 'currency', 
                              currency: 'EUR',
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2
                            }).format(Math.abs(amounts[type.id]))
                          : '0,00 €'}
                      </span>
                    )}
                  </td>
                  {/* Colonne Durée d'amortissement */}
                  <td style={{ padding: '6px 8px', borderRight: '1px solid #e5e7eb', textAlign: 'right', fontSize: '13px' }}>
                    {editingDurationId === type.id ? (
                      <input
                        type="number"
                        value={editingDurationValue}
                        onChange={(e) => setEditingDurationValue(e.target.value)}
                        onBlur={() => handleDurationEditSave(type.id)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            handleDurationEditSave(type.id);
                          } else if (e.key === 'Escape') {
                            handleDurationEditCancel();
                          }
                        }}
                        autoFocus
                        min="0"
                        step="0.1"
                        style={{
                          width: '100%',
                          padding: '4px 6px',
                          fontSize: '12px',
                          border: '1px solid #3b82f6',
                          borderRadius: '4px',
                          backgroundColor: '#ffffff',
                          textAlign: 'right',
                        }}
                      />
                    ) : (
                      <div
                        onClick={() => handleDurationEditStart(type)}
                        style={{
                          padding: '4px 6px',
                          cursor: 'pointer',
                          borderRadius: '4px',
                          transition: 'background-color 0.2s',
                          fontSize: '13px',
                          color: type.duration > 0 ? '#111827' : '#9ca3af',
                          fontStyle: type.duration > 0 ? 'normal' : 'italic',
                          textAlign: 'right',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = '#f3f4f6';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'transparent';
                        }}
                        title="Cliquer pour éditer"
                      >
                        {type.duration > 0 ? `${type.duration} ans` : '0 ans'}
                      </div>
                    )}
                  </td>
                  {/* Colonne Annuité d'amortissement */}
                  <td style={{ padding: '6px 8px', borderRight: '1px solid #e5e7eb', textAlign: 'right', fontSize: '13px', fontWeight: '500' }}>
                    {editingAnnualAmountId === type.id ? (
                      <input
                        type="number"
                        value={editingAnnualAmountValue}
                        onChange={(e) => setEditingAnnualAmountValue(e.target.value)}
                        onBlur={() => handleAnnualAmountEditSave(type.id)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            handleAnnualAmountEditSave(type.id);
                          } else if (e.key === 'Escape') {
                            handleAnnualAmountEditCancel();
                          }
                        }}
                        autoFocus
                        min="0"
                        step="0.01"
                        style={{
                          width: '100%',
                          padding: '4px 6px',
                          fontSize: '12px',
                          border: '1px solid #3b82f6',
                          borderRadius: '4px',
                          backgroundColor: '#ffffff',
                          textAlign: 'right',
                        }}
                      />
                    ) : (
                      <div
                        onClick={() => handleAnnualAmountEditStart(type)}
                        style={{
                          padding: '4px 6px',
                          cursor: 'pointer',
                          borderRadius: '4px',
                          transition: 'background-color 0.2s',
                          fontSize: '13px',
                          color: '#111827',
                          textAlign: 'right',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = '#f3f4f6';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'transparent';
                        }}
                        title="Cliquer pour éditer"
                      >
                        {(() => {
                          const calculatedAmount = calculateAnnualAmount(type);
                          console.log(`📊 [AmortizationConfigCard] Affichage annuité pour type ${type.id}:`, {
                            calculatedAmount,
                            amount: amounts[type.id],
                            duration: type.duration,
                            annual_amount: type.annual_amount
                          });
                          // Afficher la valeur calculée (peut être 0)
                          if (calculatedAmount !== null) {
                            return new Intl.NumberFormat('fr-FR', {
                              style: 'currency',
                              currency: 'EUR',
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2
                            }).format(calculatedAmount);
                          }
                          return '0,00 €';
                        })()}
                      </div>
                    )}
                  </td>
                  {/* Colonne Montant cumulé */}
                  <td style={{ padding: '6px 8px', borderRight: '1px solid #e5e7eb', textAlign: 'right', fontSize: '13px', fontWeight: '500' }}>
                    {loadingCumulatedAmounts[type.id] ? (
                      <span style={{ color: '#9ca3af', fontStyle: 'italic' }}>⏳ Calcul...</span>
                    ) : (
                      <span style={{ color: '#111827' }}>
                        {cumulatedAmounts[type.id] !== undefined 
                          ? new Intl.NumberFormat('fr-FR', { 
                              style: 'currency', 
                              currency: 'EUR',
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2
                            }).format(Math.abs(cumulatedAmounts[type.id]))
                          : '0,00 €'}
                      </span>
                    )}
                  </td>
                  {/* Colonne VNC */}
                  <td style={{ padding: '6px 8px', borderRight: '1px solid #e5e7eb', textAlign: 'right', fontSize: '13px', fontWeight: '500' }}>
                    {(() => {
                      const montant = amounts[type.id] || 0;
                      const cumule = cumulatedAmounts[type.id] || 0;
                      const vnc = Math.abs(montant) - Math.abs(cumule);
                      return (
                        <span style={{ color: vnc >= 0 ? '#111827' : '#dc2626' }}>
                          {new Intl.NumberFormat('fr-FR', { 
                            style: 'currency', 
                            currency: 'EUR',
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2
                          }).format(vnc)}
                        </span>
                      );
                    })()}
                  </td>
                </tr>
              ))
            )}
            {/* Ligne pour ajouter un nouveau type */}
            <tr style={{ backgroundColor: '#f9fafb', borderTop: '2px solid #e5e7eb' }}>
              <td colSpan={8} style={{ padding: '12px', textAlign: 'center' }}>
                <button
                  onClick={handleAddType}
                  disabled={!level2Value || loadingTypes}
                  style={{
                    padding: '8px 16px',
                    fontSize: '14px',
                    fontWeight: '600',
                    color: '#ffffff',
                    backgroundColor: (!level2Value || loadingTypes) ? '#9ca3af' : '#3b82f6',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: (!level2Value || loadingTypes) ? 'not-allowed' : 'pointer',
                    boxShadow: (!level2Value || loadingTypes) ? 'none' : '0 2px 4px rgba(0, 0, 0, 0.1)',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                  }}
                  title={!level2Value ? 'Sélectionnez d\'abord une valeur pour Level 2' : 'Ajouter un nouveau type d\'amortissement'}
                >
                  <span>+</span>
                  <span>Ajouter un type</span>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      )}

      {/* Menu contextuel */}
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
            onClick={() => handleDeleteType(contextMenu.typeId)}
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

      {/* Popup Save view */}
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
            if (!savingView) {
              setShowSaveViewPopup(false);
              setSaveViewName('');
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
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1a1a1a', margin: 0 }}>
                Sauvegarder la vue
              </h2>
              <button
                onClick={() => {
                  if (!savingView) {
                    setShowSaveViewPopup(false);
                    setSaveViewName('');
                  }
                }}
                disabled={savingView}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '24px',
                  cursor: savingView ? 'not-allowed' : 'pointer',
                  color: '#666',
                  padding: '0',
                  width: '32px',
                  height: '32px',
                  opacity: savingView ? 0.5 : 1,
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
                  if (e.key === 'Enter' && !savingView && saveViewName.trim()) {
                    saveCurrentView(saveViewName);
                  } else if (e.key === 'Escape' && !savingView) {
                    setShowSaveViewPopup(false);
                    setSaveViewName('');
                  }
                }}
                disabled={savingView}
                placeholder="Ex: Configuration 2024, Waitlists..."
                autoFocus
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  fontSize: '14px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  outline: 'none',
                  opacity: savingView ? 0.6 : 1,
                }}
              />
              <p style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px', marginBottom: 0 }}>
                Format libre. Si une vue avec ce nom existe déjà, vous pourrez choisir de l'écraser.
              </p>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button
                onClick={() => {
                  if (!savingView) {
                    setShowSaveViewPopup(false);
                    setSaveViewName('');
                  }
                }}
                disabled={savingView}
                style={{
                  padding: '10px 20px',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#374151',
                  backgroundColor: '#f3f4f6',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: savingView ? 'not-allowed' : 'pointer',
                  opacity: savingView ? 0.5 : 1,
                }}
              >
                Annuler
              </button>
              <button
                onClick={() => saveCurrentView(saveViewName)}
                disabled={savingView || !saveViewName.trim()}
                style={{
                  padding: '10px 20px',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#ffffff',
                  backgroundColor: (!savingView && saveViewName.trim()) ? '#3b82f6' : '#9ca3af',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: (savingView || !saveViewName.trim()) ? 'not-allowed' : 'pointer',
                }}
              >
                {savingView ? 'Sauvegarde...' : 'Sauvegarder'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Popup Load view */}
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
                      if (!loadingView && selectedViewId !== null) {
                        e.currentTarget.style.backgroundColor = 'transparent';
                      }
                    }}
                  >
                    <div style={{ fontSize: '14px', fontWeight: '500', color: '#374151' }}>
                      (default)
                    </div>
                    <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '2px' }}>
                      Vue actuelle (non sauvegardée)
                    </div>
                  </div>

                  {/* Liste des vues sauvegardées */}
                  {availableViews.length === 0 ? (
                    <div style={{ padding: '20px', textAlign: 'center', color: '#6b7280', fontSize: '14px' }}>
                      Aucune vue sauvegardée pour ce Level 2
                    </div>
                  ) : (
                    availableViews.map((view) => (
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
                          if (!loadingView && selectedViewId !== view.id) {
                            e.currentTarget.style.backgroundColor = 'transparent';
                          }
                        }}
                      >
                        <div style={{ fontSize: '14px', fontWeight: '500', color: '#374151' }}>
                          {view.name}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', borderTop: '1px solid #e5e7eb', paddingTop: '16px' }}>
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
                Cancel
              </button>
              <button
                onClick={() => loadView(selectedViewId)}
                disabled={loadingView || (selectedViewId === null && availableViews.length > 0)}
                style={{
                  padding: '10px 20px',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#ffffff',
                  backgroundColor: (loadingView || (selectedViewId === null && availableViews.length > 0)) ? '#9ca3af' : '#3b82f6',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: (loadingView || (selectedViewId === null && availableViews.length > 0)) ? 'not-allowed' : 'pointer',
                }}
              >
                {loadingView ? 'Chargement...' : 'OK'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Popup Delete view */}
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
            if (!deletingView) {
              setShowDeleteViewPopup(false);
              setSelectedViewIdForDelete(null);
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
                Supprimer une vue
              </h2>
              <button
                onClick={() => {
                  if (!deletingView) {
                    setShowDeleteViewPopup(false);
                    setSelectedViewIdForDelete(null);
                  }
                }}
                disabled={deletingView}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '24px',
                  cursor: deletingView ? 'not-allowed' : 'pointer',
                  color: '#666',
                  padding: '0',
                  width: '32px',
                  height: '32px',
                  opacity: deletingView ? 0.5 : 1,
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
                  {availableViewsForDelete.length === 0 ? (
                    <div style={{ padding: '20px', textAlign: 'center', color: '#6b7280', fontSize: '14px' }}>
                      Aucune vue sauvegardée pour ce Level 2
                    </div>
                  ) : (
                    availableViewsForDelete.map((view) => (
                      <div
                        key={view.id}
                        onClick={() => !deletingView && setSelectedViewIdForDelete(view.id)}
                        style={{
                          padding: '12px 16px',
                          borderRadius: '6px',
                          cursor: deletingView ? 'not-allowed' : 'pointer',
                          backgroundColor: selectedViewIdForDelete === view.id ? '#fee2e2' : 'transparent',
                          border: selectedViewIdForDelete === view.id ? '2px solid #dc2626' : '2px solid transparent',
                          opacity: deletingView ? 0.5 : 1,
                        }}
                        onMouseEnter={(e) => {
                          if (!deletingView && selectedViewIdForDelete !== view.id) {
                            e.currentTarget.style.backgroundColor = '#f3f4f6';
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (!deletingView && selectedViewIdForDelete !== view.id) {
                            e.currentTarget.style.backgroundColor = 'transparent';
                          }
                        }}
                      >
                        <div style={{ fontSize: '14px', fontWeight: '500', color: '#374151' }}>
                          {view.name}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', borderTop: '1px solid #e5e7eb', paddingTop: '16px' }}>
              <button
                onClick={() => {
                  if (!deletingView) {
                    setShowDeleteViewPopup(false);
                    setSelectedViewIdForDelete(null);
                  }
                }}
                disabled={deletingView}
                style={{
                  padding: '10px 20px',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#374151',
                  backgroundColor: '#f3f4f6',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: deletingView ? 'not-allowed' : 'pointer',
                  opacity: deletingView ? 0.5 : 1,
                }}
              >
                Annuler
              </button>
              <button
                onClick={() => deleteView(selectedViewIdForDelete)}
                disabled={deletingView || selectedViewIdForDelete === null}
                style={{
                  padding: '10px 20px',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#ffffff',
                  backgroundColor: (deletingView || selectedViewIdForDelete === null) ? '#9ca3af' : '#dc2626',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: (deletingView || selectedViewIdForDelete === null) ? 'not-allowed' : 'pointer',
                }}
              >
                {deletingView ? 'Suppression...' : 'Supprimer'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

