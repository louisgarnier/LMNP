/**
 * AmortizationConfigCard - Card de configuration des amortissements
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 * 
 * Steps implémentés:
 * - Step 6.6.2: Structure de base de la card
 * - Step 6.6.3: Champ Level 2 avec localStorage
 * - Step 6.6.4: Tableau (structure vide)
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { transactionsAPI, amortizationTypesAPI, AmortizationType } from '@/api/client';

interface AmortizationConfigCardProps {
  onConfigUpdated?: () => void;
  onLevel2Change?: (level2Value: string) => void;
  onLevel2ValuesLoaded?: (count: number) => void;
}

const STORAGE_KEY_LEVEL2 = 'amortization_config_level2';

export default function AmortizationConfigCard({
  onConfigUpdated,
  onLevel2Change,
  onLevel2ValuesLoaded,
}: AmortizationConfigCardProps) {
  const [selectedLevel2Value, setSelectedLevel2Value] = useState<string>('');
  const [level2Values, setLevel2Values] = useState<string[]>([]);
  const [loadingValues, setLoadingValues] = useState<boolean>(false);
  const [level2ValuesLoaded, setLevel2ValuesLoaded] = useState<boolean>(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState<boolean>(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  // États pour les types d'amortissement
  const [amortizationTypes, setAmortizationTypes] = useState<AmortizationType[]>([]);
  const [loadingTypes, setLoadingTypes] = useState<boolean>(false);
  const [editingNameId, setEditingNameId] = useState<number | null>(null);
  const [editingNameValue, setEditingNameValue] = useState<string>('');
  const [isResetting, setIsResetting] = useState<boolean>(false); // Flag pour éviter la duplication lors de la réinitialisation
  
  // États pour l'édition de la date de début
  const [editingStartDateId, setEditingStartDateId] = useState<number | null>(null);
  const [editingStartDateValue, setEditingStartDateValue] = useState<string>('');
  
  // États pour la colonne "Level 1 (valeurs)"
  const [level1Values, setLevel1Values] = useState<string[]>([]);
  const [loadingLevel1Values, setLoadingLevel1Values] = useState<boolean>(false);
  const [openLevel1DropdownId, setOpenLevel1DropdownId] = useState<number | null>(null);
  const [level1DropdownPosition, setLevel1DropdownPosition] = useState<'bottom' | 'top'>('bottom');
  
  // États pour la colonne "Nombre de transactions"
  const [transactionCounts, setTransactionCounts] = useState<Record<number, number>>({});
  const [loadingTransactionCounts, setLoadingTransactionCounts] = useState<Record<number, boolean>>({});

  // Charger les valeurs Level 2 depuis l'API
  const loadLevel2Values = async () => {
    try {
      setLoadingValues(true);
      const response = await transactionsAPI.getUniqueValues('level_2');
      const values = response.values || [];
      setLevel2Values(values);
      setLevel2ValuesLoaded(true);
      
      // Notifier le parent du nombre de valeurs disponibles
      if (onLevel2ValuesLoaded) {
        onLevel2ValuesLoaded(values.length);
      }
      
      // Restaurer la valeur depuis localStorage si disponible
      const savedLevel2 = localStorage.getItem(STORAGE_KEY_LEVEL2);
      if (savedLevel2) {
        try {
          // Essayer de parser comme JSON (ancien format array)
          const savedValues: string[] = JSON.parse(savedLevel2);
          const validValue = savedValues.find(v => values.includes(v));
          if (validValue) {
            setSelectedLevel2Value(validValue);
      if (onLevel2Change) {
              onLevel2Change(validValue);
            }
          }
          } catch (e) {
          // Si ce n'est pas du JSON, utiliser comme string simple
          if (values.includes(savedLevel2)) {
            setSelectedLevel2Value(savedLevel2);
            if (onLevel2Change) {
              onLevel2Change(savedLevel2);
            }
          }
        }
      }
    } catch (err: any) {
      console.error('Erreur lors du chargement des valeurs level_2:', err);
      setLevel2ValuesLoaded(true);
      if (onLevel2ValuesLoaded) {
        onLevel2ValuesLoaded(0);
      }
    } finally {
      setLoadingValues(false);
    }
  };

  // Charger les valeurs au montage
  useEffect(() => {
    loadLevel2Values();
  }, []);

  // Les 7 types initiaux (template par défaut)
  const INITIAL_TYPES = [
    "Part terrain",
    "Immobilisation structure/GO",
    "Immobilisation mobilier",
    "Immobilisation IGT",
    "Immobilisation agencements",
    "Immobilisation Facade/Toiture",
    "Immobilisation travaux",
  ];

  // Créer les 7 types initiaux si aucun type n'existe
  const createInitialTypes = async (level2Value: string) => {
    try {
      console.log(`[AmortizationConfigCard] Création des 7 types initiaux pour Level 2: ${level2Value}`);
      
      // Créer les 7 types en parallèle
      const createPromises = INITIAL_TYPES.map(typeName =>
        amortizationTypesAPI.create({
          name: typeName,
          level_2_value: level2Value,
          level_1_values: [],
          start_date: null,
          duration: 0.0,
          annual_amount: null,
        })
      );

      await Promise.all(createPromises);
      console.log(`[AmortizationConfigCard] ✓ 7 types initiaux créés avec succès`);
    } catch (err: any) {
      console.error('Erreur lors de la création des types initiaux:', err);
      throw err;
    }
  };

  // Charger les types d'amortissement
  const loadAmortizationTypes = async (skipAutoCreate: boolean = false, level2ValueOverride?: string) => {
    // Utiliser la valeur override si fournie, sinon utiliser selectedLevel2Value
    const level2ValueToUse = level2ValueOverride || selectedLevel2Value;
    
    if (!level2ValueToUse) {
      setAmortizationTypes([]);
      return;
    }

    try {
      setLoadingTypes(true);
      // Charger les types pour le Level 2 sélectionné (une seule valeur)
      const response = await amortizationTypesAPI.getAll(level2ValueToUse);
      
      if (response && response.items) {
        // Si aucun type n'existe ET que le Level 2 est "Immobilisations" ET qu'on n'est pas en train de réinitialiser, créer les 7 types initiaux automatiquement
        if (response.items.length === 0 && level2ValueToUse === "Immobilisations" && !skipAutoCreate && !isResetting) {
          console.log(`[AmortizationConfigCard] Aucun type trouvé pour Level 2 "Immobilisations", création des 7 types initiaux...`);
          await createInitialTypes(level2ValueToUse);
          
          // Recharger les types après création
          const newResponse = await amortizationTypesAPI.getAll(level2ValueToUse);
          if (newResponse && newResponse.items) {
            const sortedTypes = [...newResponse.items].sort((a, b) => a.name.localeCompare(b.name));
            setAmortizationTypes(sortedTypes);
          } else {
            setAmortizationTypes([]);
          }
        } else {
          // Trier par nom pour un affichage cohérent
          const sortedTypes = [...response.items].sort((a, b) => a.name.localeCompare(b.name));
          setAmortizationTypes(sortedTypes);
        }
      } else {
        setAmortizationTypes([]);
      }
    } catch (err: any) {
      console.error('Erreur lors du chargement des types d\'amortissement:', err);
      setAmortizationTypes([]);
    } finally {
      setLoadingTypes(false);
    }
  };

  // Charger les valeurs Level 1 filtrées par Level 2
  const loadLevel1Values = async () => {
    if (!selectedLevel2Value) {
      setLevel1Values([]);
      return;
    }

    try {
      setLoadingLevel1Values(true);
      const response = await transactionsAPI.getUniqueValues('level_1', undefined, undefined, selectedLevel2Value);
      setLevel1Values(response.values || []);
    } catch (err: any) {
      console.error('Erreur lors du chargement des valeurs level_1:', err);
      setLevel1Values([]);
    } finally {
      setLoadingLevel1Values(false);
    }
  };

  // Charger le nombre de transactions pour tous les types
  const loadTransactionCounts = async () => {
    if (!selectedLevel2Value || amortizationTypes.length === 0) {
      setTransactionCounts({});
      return;
    }

    try {
      // Marquer tous les types comme en cours de chargement
      const loadingState: Record<number, boolean> = {};
      amortizationTypes.forEach(type => {
        loadingState[type.id] = true;
      });
      setLoadingTransactionCounts(loadingState);

      // Charger les compteurs pour tous les types en parallèle
      const countPromises = amortizationTypes.map(async (type) => {
        try {
          const response = await amortizationTypesAPI.getTransactionCount(type.id);
          return { typeId: type.id, count: response.transaction_count };
        } catch (err: any) {
          // Ignorer silencieusement les erreurs 404 (type non trouvé - peut arriver après une réinitialisation)
          // Ne pas logger pour éviter le spam dans la console
          if (err.status === 404 || err.message?.includes('404') || err.message?.includes('non trouvé')) {
            return { typeId: type.id, count: 0 };
          }
          // Logger seulement les autres erreurs
          console.error(`Erreur lors du chargement du nombre de transactions pour le type ${type.id}:`, err);
          return { typeId: type.id, count: 0 };
        }
      });

      const results = await Promise.all(countPromises);
      
      // Mettre à jour les compteurs
      const newCounts: Record<number, number> = {};
      results.forEach(({ typeId, count }) => {
        newCounts[typeId] = count;
      });
      setTransactionCounts(newCounts);
    } catch (err: any) {
      console.error('Erreur lors du chargement des nombres de transactions:', err);
    } finally {
      // Marquer tous les types comme terminés
      setLoadingTransactionCounts({});
    }
  };

  // Charger les types quand selectedLevel2Value change
  useEffect(() => {
    loadAmortizationTypes();
    loadLevel1Values(); // Recharger les valeurs Level 1 quand le Level 2 change
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedLevel2Value]);

  // Recharger les compteurs quand les types ou les valeurs Level 1 changent
  useEffect(() => {
    // Attendre un peu pour s'assurer que les types sont bien chargés et persistés en base
    if (amortizationTypes.length > 0 && selectedLevel2Value && !loadingTypes) {
      // Petit délai pour s'assurer que les types sont bien en base après création
      const timeoutId = setTimeout(() => {
        loadTransactionCounts();
      }, 100);
      
      return () => clearTimeout(timeoutId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [amortizationTypes, selectedLevel2Value, loadingTypes]);

  // Fermer le dropdown Level 2 si on clique en dehors
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };

    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isDropdownOpen]);

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

  // Gérer le changement d'une checkbox Level 2 (comportement radio - une seule sélection)
  const handleLevel2CheckboxChange = async (value: string, checked: boolean) => {
    if (checked) {
      // Si on change de Level 2 (pas le premier chargement), vérifier s'il y a des types à perdre
      const previousValue = selectedLevel2Value;
      const isChangingLevel2 = previousValue !== '' && previousValue !== value;
      
      // Si on change de Level 2 ET qu'il existe des types pour le Level 2 actuel, demander confirmation
      if (isChangingLevel2 && amortizationTypes.length > 0) {
        const confirmed = window.confirm(
          `Vous allez perdre les modifications sur "${previousValue}". Toutes les données d'amortissement vont être supprimées. Cette action est irréversible. Continuer ?`
        );
        
        if (!confirmed) {
          // Annuler le changement : ne pas mettre à jour selectedLevel2Value
          return;
        }
      }
      
      // Comportement radio : cocher une checkbox décoche automatiquement les autres
      setSelectedLevel2Value(value);
      
      // Sauvegarder dans localStorage (string simple, pas array)
      localStorage.setItem(STORAGE_KEY_LEVEL2, value);
      
      // Notifier le parent
      if (onLevel2Change) {
        onLevel2Change(value);
      }
      
      // Si on change de Level 2, déclencher la réinitialisation (sans popup car déjà fait si nécessaire)
      if (isChangingLevel2) {
        console.log(`[AmortizationConfigCard] Changement de Level 2: "${previousValue}" -> "${value}", déclenchement de la réinitialisation...`);
        await resetAllTypesForLevel2(value, false); // Pas de popup car déjà fait si nécessaire
      } else {
        // Sinon, juste recharger les types
        await loadAmortizationTypes();
      }
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } else {
      // Empêcher la désélection si c'est la valeur actuellement sélectionnée
      // (comportement radio : on ne peut pas décocher la seule valeur sélectionnée)
      if (selectedLevel2Value === value) {
        // Ne rien faire - on ne peut pas décocher la seule valeur sélectionnée
        return;
      }
    }
  };

  // Gérer le début de l'édition du nom
  const handleNameEditStart = (type: AmortizationType) => {
    setEditingNameId(type.id);
    setEditingNameValue(type.name);
  };

  // Sauvegarder le nom édité
  const handleNameEditSave = async (typeId: number) => {
    if (!editingNameValue.trim()) {
      // Ne pas sauvegarder si vide
      setEditingNameId(null);
      setEditingNameValue('');
        return;
      }
      
    try {
      await amortizationTypesAPI.update(typeId, {
        name: editingNameValue.trim(),
      });
      
      // Recharger les types pour avoir la valeur à jour
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

  // Annuler l'édition du nom
  const handleNameEditCancel = () => {
    setEditingNameId(null);
    setEditingNameValue('');
  };

  // Gérer les touches dans le champ d'édition
  const handleNameEditKeyDown = (e: React.KeyboardEvent, typeId: number) => {
    if (e.key === 'Enter') {
      handleNameEditSave(typeId);
    } else if (e.key === 'Escape') {
      handleNameEditCancel();
    }
  };

  // Gérer l'ajout/suppression d'une valeur Level 1
  const handleLevel1Toggle = async (typeId: number, level1Value: string) => {
    const type = amortizationTypes.find(t => t.id === typeId);
    if (!type) return;

    const currentValues = type.level_1_values || [];
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
      await amortizationTypesAPI.update(typeId, {
        level_1_values: newValues,
      });
      
      // Recharger les types pour avoir la valeur à jour
      await loadAmortizationTypes();
      
      // Recharger les compteurs de transactions après modification des Level 1
      await loadTransactionCounts();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('Erreur lors de la mise à jour des valeurs level_1:', err);
      alert(`Erreur lors de la sauvegarde: ${err.message || 'Erreur inconnue'}`);
    }
  };

  // Gérer la suppression d'une valeur Level 1 (via le tag)
  const handleLevel1Remove = async (typeId: number, level1Value: string) => {
    await handleLevel1Toggle(typeId, level1Value);
  };

  // Gérer le début de l'édition de la date de début
  const handleStartDateEditStart = (type: AmortizationType) => {
    setEditingStartDateId(type.id);
    // Convertir la date en format YYYY-MM-DD pour l'input date
    if (type.start_date) {
      const date = new Date(type.start_date);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      setEditingStartDateValue(`${year}-${month}-${day}`);
    } else {
      setEditingStartDateValue('');
    }
  };

  // Sauvegarder la date de début
  const handleStartDateEditSave = async (typeId: number) => {
    try {
      // Convertir la chaîne en date ou null
      let startDate: string | null = null;
      if (editingStartDateValue.trim()) {
        // Valider le format de date
        const date = new Date(editingStartDateValue);
        if (isNaN(date.getTime())) {
          alert('Date invalide. Format attendu : YYYY-MM-DD');
          return;
        }
        startDate = editingStartDateValue.trim();
      }

      await amortizationTypesAPI.update(typeId, {
        start_date: startDate || null,
      });
      
      // Recharger les types pour avoir la valeur à jour
      await loadAmortizationTypes();
      
      setEditingStartDateId(null);
      setEditingStartDateValue('');
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('Erreur lors de la sauvegarde de la date de début:', err);
      alert(`Erreur lors de la sauvegarde: ${err.message || 'Erreur inconnue'}`);
    }
  };

  // Supprimer la date de début
  const handleStartDateRemove = async (typeId: number) => {
    try {
      await amortizationTypesAPI.update(typeId, {
        start_date: null,
      });
      
      // Recharger les types pour avoir la valeur à jour
      await loadAmortizationTypes();
      
      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('Erreur lors de la suppression de la date de début:', err);
      alert(`Erreur lors de la suppression: ${err.message || 'Erreur inconnue'}`);
    }
  };

  // Annuler l'édition de la date de début
  const handleStartDateEditCancel = () => {
    setEditingStartDateId(null);
    setEditingStartDateValue('');
  };

  // Gérer les touches dans le champ d'édition de la date
  const handleStartDateEditKeyDown = (e: React.KeyboardEvent, typeId: number) => {
    if (e.key === 'Enter') {
      handleStartDateEditSave(typeId);
    } else if (e.key === 'Escape') {
      handleStartDateEditCancel();
    }
  };

  // Fonction interne de réinitialisation (utilisée par le bouton et le changement de Level 2)
  const resetAllTypesForLevel2 = async (level2Value: string, showConfirmation: boolean = true) => {
    if (!level2Value) {
      return;
    }

    // Si confirmation demandée, vérifier qu'il existe des types
    if (showConfirmation) {
      // Vérifier qu'il existe des types pour le Level 2 sélectionné
      if (amortizationTypes.length === 0) {
        alert('Aucun type d\'amortissement à réinitialiser pour ce Level 2.');
        return;
      }

      // Popup d'avertissement
      const confirmed = window.confirm(
        'Attention, toutes les données d\'amortissement vont être supprimées. Cette action est irréversible. Êtes-vous sûr ?'
      );

      if (!confirmed) {
        return;
      }
    }

    try {
      setIsResetting(true); // Activer le flag pour éviter la duplication
      console.log(`[AmortizationConfigCard] Réinitialisation des types d'amortissement pour Level 2: ${level2Value}...`);
      
      // 1. Supprimer TOUS les types de TOUS les Level 2 (toute la table)
      await amortizationTypesAPI.deleteAll();
      console.log('[AmortizationConfigCard] ✓ Tous les types supprimés');

      // 2. Recréer les 7 types par défaut UNIQUEMENT si le Level 2 est "Immobilisations"
      if (level2Value === "Immobilisations") {
        const INITIAL_TYPES = [
          "Part terrain",
          "Immobilisation structure/GO",
          "Immobilisation mobilier",
          "Immobilisation IGT",
          "Immobilisation agencements",
          "Immobilisation Facade/Toiture",
          "Immobilisation travaux",
        ];

        const createPromises = INITIAL_TYPES.map(name =>
          amortizationTypesAPI.create({
            name: name,
            level_2_value: level2Value,
            level_1_values: [],
            start_date: null,
            duration: 0.0,
            annual_amount: null,
          })
        );

        await Promise.all(createPromises);
        console.log('[AmortizationConfigCard] ✓ 7 types par défaut recréés avec valeurs vides pour Immobilisations');
      } else {
        console.log(`[AmortizationConfigCard] Level 2 "${level2Value}" n'est pas "Immobilisations", aucun type par défaut créé`);
      }

      // 3. Recharger le tableau (skipAutoCreate = true pour éviter la duplication, et passer level2Value pour s'assurer qu'on charge les bons types)
      await loadAmortizationTypes(true, level2Value);

      if (onConfigUpdated) {
        onConfigUpdated();
      }
    } catch (err: any) {
      console.error('Erreur lors de la réinitialisation:', err);
      alert(`Erreur lors de la réinitialisation: ${err.message || 'Erreur inconnue'}`);
    } finally {
      setIsResetting(false); // Désactiver le flag
    }
  };

  // Réinitialiser aux valeurs par défaut (bouton)
  const handleResetToDefault = async () => {
    if (!selectedLevel2Value) {
      return;
    }
    await resetAllTypesForLevel2(selectedLevel2Value, true);
  };

  return (
    <div
      style={{
        backgroundColor: '#ffffff',
        borderRadius: '8px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        padding: '24px',
        marginBottom: '24px',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#111827', margin: 0 }}>
          Configuration des amortissements
        </h2>
        <button
          type="button"
          onClick={handleResetToDefault}
          disabled={!selectedLevel2Value || amortizationTypes.length === 0}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 16px',
            fontSize: '14px',
            fontWeight: '500',
            color: !selectedLevel2Value || amortizationTypes.length === 0 ? '#9ca3af' : '#374151',
            backgroundColor: !selectedLevel2Value || amortizationTypes.length === 0 ? '#f3f4f6' : '#f9fafb',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            cursor: !selectedLevel2Value || amortizationTypes.length === 0 ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => {
            if (selectedLevel2Value && amortizationTypes.length > 0) {
              e.currentTarget.style.backgroundColor = '#f3f4f6';
            }
          }}
          onMouseLeave={(e) => {
            if (selectedLevel2Value && amortizationTypes.length > 0) {
              e.currentTarget.style.backgroundColor = '#f9fafb';
            }
          }}
        >
          <span>↻</span>
          <span>Réinitialiser</span>
        </button>
      </div>
      
      {/* Champ Level 2 - Dropdown avec checkboxes */}
      <div style={{ marginBottom: '24px' }}>
        <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '8px' }}>
          Level 2 (Valeur à considérer comme amortissement)
        </label>
        {loadingValues ? (
          <div style={{ color: '#6b7280', fontSize: '14px' }}>Chargement...</div>
        ) : level2Values.length === 0 ? (
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
                {selectedLevel2Value || '-- Sélectionner une valeur --'}
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
                {level2Values.map((value) => (
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
                      checked={selectedLevel2Value === value}
                      onChange={(e) => handleLevel2CheckboxChange(value, e.target.checked)}
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

      {/* Tableau (structure vide) - Step 6.6.4 */}
      {selectedLevel2Value && (
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
                <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>
                  Type d'immobilisation
                </th>
                <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>
                Level 1 (valeurs)
              </th>
                <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>
                Nombre de transactions
              </th>
                <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>
                Date de début
              </th>
                <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>
                  Montant
              </th>
                <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>
                  Durée
              </th>
                <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>
                  Annuité
              </th>
                <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>
                  Cumulé
              </th>
                <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', color: '#374151' }}>
                VNC
              </th>
            </tr>
          </thead>
          <tbody>
            {loadingTypes ? (
              <tr>
                  <td colSpan={9} style={{ padding: '24px', textAlign: 'center', color: '#6b7280' }}>
                    Chargement des types...
                </td>
              </tr>
            ) : amortizationTypes.length === 0 ? (
              <tr>
                  <td colSpan={9} style={{ padding: '24px', textAlign: 'center', color: '#6b7280' }}>
                    Aucun type d'amortissement trouvé pour le Level 2 sélectionné
                  </td>
              </tr>
            ) : (
              amortizationTypes.map((type) => (
                <tr 
                  key={type.id} 
                    style={{
                      borderBottom: '1px solid #e5e7eb',
                    }}
                >
                    {/* Colonne "Type d'immobilisation" - Éditable */}
                    <td style={{ padding: '12px' }}>
                    {editingNameId === type.id ? (
                      <input
                        type="text"
                        value={editingNameValue}
                        onChange={(e) => setEditingNameValue(e.target.value)}
                        onBlur={() => handleNameEditSave(type.id)}
                          onKeyDown={(e) => handleNameEditKeyDown(e, type.id)}
                        autoFocus
                        style={{
                          width: '100%',
                            padding: '4px 8px',
                            fontSize: '14px',
                          border: '1px solid #3b82f6',
                          borderRadius: '4px',
                            outline: 'none',
                        }}
                      />
                    ) : (
                        <span
                        onClick={() => handleNameEditStart(type)}
                        style={{
                          cursor: 'pointer',
                            padding: '4px 8px',
                          borderRadius: '4px',
                            display: 'inline-block',
                            minWidth: '100px',
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
                        </span>
                      )}
                  </td>
                    {/* Colonne "Level 1 (valeurs)" - Multi-select */}
                    <td style={{ padding: '12px' }}>
                      <div style={{ position: 'relative' }}>
                        {/* Tags des valeurs sélectionnées */}
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '6px' }}>
                          {(type.level_1_values || []).map((value) => (
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
                                onClick={() => handleLevel1Remove(type.id, value)}
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
                        
                        {/* Bouton "+" pour ouvrir le dropdown */}
                        <button
                          type="button"
                          onClick={(e) => {
                            // Détecter si on est dans les rangées du bas pour positionner le dropdown vers le haut
                            const buttonRect = e.currentTarget.getBoundingClientRect();
                            const cardRect = e.currentTarget.closest('[style*="backgroundColor"]')?.getBoundingClientRect();
                            const viewportHeight = window.innerHeight;
                            
                            // Si le bouton est dans la moitié inférieure de la viewport, afficher le dropdown vers le haut
                            const shouldShowTop = buttonRect.bottom > viewportHeight / 2;
                            
                            setLevel1DropdownPosition(shouldShowTop ? 'top' : 'bottom');
                            setOpenLevel1DropdownId(openLevel1DropdownId === type.id ? null : type.id);
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
                        {openLevel1DropdownId === type.id && (
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
                              // Collecter toutes les valeurs Level 1 déjà sélectionnées pour TOUS les types (pas seulement ce type)
                              const allSelectedValues = new Set<string>();
                              amortizationTypes.forEach(t => {
                                if (t.level_1_values && t.level_1_values.length > 0) {
                                  t.level_1_values.forEach(v => allSelectedValues.add(v));
                                }
                              });
                              
                              // Filtrer les valeurs déjà sélectionnées (pour n'importe quel type)
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
                                    checked={false}
                                    onChange={() => handleLevel1Toggle(type.id, value)}
                                    style={{
                                      width: '16px',
                                      height: '16px',
                                      cursor: 'pointer',
                                    }}
                                  />
                                  <span style={{ fontSize: '14px', color: '#374151' }}>{value}</span>
                                </label>
                              ));
                            })()}
                          </div>
                        )}
                      </div>
                    </td>
                    {/* Colonne "Nombre de transactions" */}
                    <td style={{ padding: '12px' }}>
                      {loadingTransactionCounts[type.id] ? (
                        <span style={{ color: '#6b7280', fontSize: '14px' }}>⏳...</span>
                      ) : (
                        <span style={{ color: '#374151', fontSize: '14px', fontWeight: '500' }}>
                          {transactionCounts[type.id] ?? '-'}
                        </span>
                      )}
                    </td>
                    {/* Colonne "Date de début" */}
                    <td style={{ padding: '12px' }}>
                      {editingStartDateId === type.id ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <input
                            type="date"
                            value={editingStartDateValue}
                            onChange={(e) => setEditingStartDateValue(e.target.value)}
                            onBlur={() => handleStartDateEditSave(type.id)}
                            onKeyDown={(e) => handleStartDateEditKeyDown(e, type.id)}
                            autoFocus
                            style={{
                              padding: '4px 8px',
                              fontSize: '14px',
                              border: '1px solid #3b82f6',
                              borderRadius: '4px',
                              outline: 'none',
                              width: '140px',
                            }}
                          />
                          <button
                            type="button"
                            onClick={handleStartDateEditCancel}
                            style={{
                              padding: '4px 8px',
                              fontSize: '12px',
                              color: '#6b7280',
                              backgroundColor: 'transparent',
                              border: '1px solid #d1d5db',
                              borderRadius: '4px',
                              cursor: 'pointer',
                            }}
                            title="Annuler"
                          >
                            ✕
                          </button>
                        </div>
                      ) : (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          {type.start_date ? (
                            <>
                              <span
                                onClick={() => handleStartDateEditStart(type)}
                                style={{
                                  cursor: 'pointer',
                                  padding: '4px 8px',
                                  borderRadius: '4px',
                                  display: 'inline-block',
                                  fontSize: '14px',
                                  color: '#374151',
                                }}
                                onMouseEnter={(e) => {
                                  e.currentTarget.style.backgroundColor = '#f3f4f6';
                                }}
                                onMouseLeave={(e) => {
                                  e.currentTarget.style.backgroundColor = 'transparent';
                                }}
                                title="Cliquer pour éditer"
                              >
                                {new Date(type.start_date).toLocaleDateString('fr-FR', {
                                  day: '2-digit',
                                  month: '2-digit',
                                  year: 'numeric'
                                })}
                              </span>
                              <button
                                type="button"
                                onClick={() => handleStartDateRemove(type.id)}
                                style={{
                                  padding: '2px 6px',
                                  fontSize: '12px',
                                  color: '#dc2626',
                                  backgroundColor: 'transparent',
                                  border: 'none',
                                  cursor: 'pointer',
                                  borderRadius: '4px',
                                }}
                                onMouseEnter={(e) => {
                                  e.currentTarget.style.backgroundColor = '#fee2e2';
                                }}
                                onMouseLeave={(e) => {
                                  e.currentTarget.style.backgroundColor = 'transparent';
                                }}
                                title="Supprimer la date"
                              >
                                ×
                              </button>
                            </>
                          ) : (
                            <span
                              onClick={() => handleStartDateEditStart(type)}
                              style={{
                                cursor: 'pointer',
                                padding: '4px 8px',
                                borderRadius: '4px',
                                display: 'inline-block',
                                fontSize: '14px',
                                color: '#9ca3af',
                                fontStyle: 'italic',
                              }}
                              onMouseEnter={(e) => {
                                e.currentTarget.style.backgroundColor = '#f3f4f6';
                                e.currentTarget.style.color = '#374151';
                              }}
                              onMouseLeave={(e) => {
                                e.currentTarget.style.backgroundColor = 'transparent';
                                e.currentTarget.style.color = '#9ca3af';
                              }}
                              title="Cliquer pour ajouter une date"
                            >
                              Ajouter une date
                            </span>
                          )}
                        </div>
                      )}
                    </td>
                    {/* Autres colonnes vides pour l'instant */}
                    <td style={{ padding: '12px', color: '#9ca3af' }}>-</td>
                    <td style={{ padding: '12px', color: '#9ca3af' }}>-</td>
                    <td style={{ padding: '12px', color: '#9ca3af' }}>-</td>
                    <td style={{ padding: '12px', color: '#9ca3af' }}>-</td>
                    <td style={{ padding: '12px', color: '#9ca3af' }}>-</td>
                    <td style={{ padding: '12px', color: '#9ca3af' }}>-</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        </div>
      )}
    </div>
  );
}

