'use client';

import React, { useState, useEffect, useMemo, useCallback, useImperativeHandle, forwardRef } from 'react';
import { mappingsAPI, enrichmentAPI, Mapping, MappingCreate, MappingUpdate, allowedMappingsAPI } from '../api/client';
import { exportAndDownloadMappings, generateDefaultFilename } from '../utils/excelExport';

type SortColumn = 'id' | 'nom' | 'level_1' | 'level_2' | 'level_3';
type SortDirection = 'asc' | 'desc';

interface MappingTableProps {
  onMappingChange?: () => void;
}

export interface MappingTableRef {
  loadMappings: (resetPage?: boolean) => Promise<void>;
}

const MappingTable = forwardRef<MappingTableRef, MappingTableProps>(({ onMappingChange }, ref) => {
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [sortColumn, setSortColumn] = useState<SortColumn>('id');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  
  // États pour les filtres (valeurs affichées dans les inputs)
  const [filterNom, setFilterNom] = useState('');
  const [filterLevel1, setFilterLevel1] = useState('');
  const [filterLevel2, setFilterLevel2] = useState('');
  const [filterLevel3, setFilterLevel3] = useState('');
  
  // États pour les filtres appliqués (après debounce)
  const [appliedFilterNom, setAppliedFilterNom] = useState('');
  const [appliedFilterLevel1, setAppliedFilterLevel1] = useState('');
  const [appliedFilterLevel2, setAppliedFilterLevel2] = useState('');
  const [appliedFilterLevel3, setAppliedFilterLevel3] = useState('');
  
  // Données brutes chargées depuis l'API (sans filtres appliqués)
  const [rawMappings, setRawMappings] = useState<Mapping[]>([]);
  
  // Valeurs uniques pour les dropdowns
  const [uniqueNoms, setUniqueNoms] = useState<string[]>([]);
  const [uniqueLevel1s, setUniqueLevel1s] = useState<string[]>([]);
  const [uniqueLevel2s, setUniqueLevel2s] = useState<string[]>([]);
  const [uniqueLevel3s, setUniqueLevel3s] = useState<string[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [isDeletingMultiple, setIsDeletingMultiple] = useState(false);
  const [isReEnriching, setIsReEnriching] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newMapping, setNewMapping] = useState<MappingCreate>({
    nom: '',
    level_1: '',
    level_2: '',
    level_3: '',
    is_prefix_match: true,
    priority: 0,
  });
  
  // États pour les dropdowns filtrés dans le modal de création
  const [availableLevel1ForCreate, setAvailableLevel1ForCreate] = useState<string[]>([]);
  const [availableLevel2ForCreate, setAvailableLevel2ForCreate] = useState<string[]>([]);
  const [availableLevel3ForCreate, setAvailableLevel3ForCreate] = useState<string[]>([]);
  
  // États pour les dropdowns filtrés dans l'édition inline
  const [editingMappingValues, setEditingMappingValues] = useState<{
    level_1?: string;
    level_2?: string;
    level_3?: string;
  }>({});
  const [availableLevel1ForEdit, setAvailableLevel1ForEdit] = useState<string[]>([]);
  const [availableLevel2ForEdit, setAvailableLevel2ForEdit] = useState<string[]>([]);
  const [availableLevel3ForEdit, setAvailableLevel3ForEdit] = useState<string[]>([]);

  const loadMappings = async (resetPage: boolean = false) => {
    // Si resetPage est true, réinitialiser la page à 1
    if (resetPage) {
      setPage(1);
    }
    
    setLoading(true);
    setError(null);
    try {
      // Utiliser la page actuelle (ou 1 si resetPage)
      const currentPage = resetPage ? 1 : page;
      // Passer les filtres à l'API pour filtrage côté serveur
      const response = await mappingsAPI.list(
        (currentPage - 1) * pageSize,
        pageSize,
        search || undefined,
        sortColumn,
        sortDirection,
        appliedFilterNom || undefined,
        appliedFilterLevel1 || undefined,
        appliedFilterLevel2 || undefined,
        appliedFilterLevel3 || undefined
      );
      
      // L'API fait déjà le filtrage, on utilise directement les résultats
      setRawMappings(response.mappings);
      setTotal(response.total);
    } catch (err: any) {
      setError(err.message || 'Erreur lors du chargement des mappings');
      console.error('Erreur chargement mappings:', err);
    } finally {
      setLoading(false);
    }
  };

  // Réinitialiser la page à 1 quand les filtres changent
  useEffect(() => {
    if (appliedFilterNom || appliedFilterLevel1 || appliedFilterLevel2 || appliedFilterLevel3) {
      setPage(1);
    }
  }, [appliedFilterNom, appliedFilterLevel1, appliedFilterLevel2, appliedFilterLevel3]);

  // Recharger depuis l'API quand page, tri, search ou filtres changent
  useEffect(() => {
    loadMappings();
  }, [page, pageSize, search, sortColumn, sortDirection, appliedFilterNom, appliedFilterLevel1, appliedFilterLevel2, appliedFilterLevel3]);

  // L'API fait déjà le filtrage, on utilise directement les résultats
  const mappings = rawMappings;

  // Réinitialiser la sélection quand les mappings changent
  useEffect(() => {
    setSelectedIds(prev => {
      const loadedIds = new Set(mappings.map(m => m.id));
      const newSet = new Set<number>();
      prev.forEach(id => {
        if (loadedIds.has(id)) {
          newSet.add(id);
        }
      });
      return newSet;
    });
  }, [mappings]);

  // Debounce pour les filtres texte (attendre 500ms après la dernière frappe)
  useEffect(() => {
    const timer = setTimeout(() => {
      setAppliedFilterNom(filterNom);
    }, 500);
    return () => clearTimeout(timer);
  }, [filterNom]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setAppliedFilterLevel1(filterLevel1);
    }, 500);
    return () => clearTimeout(timer);
  }, [filterLevel1]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setAppliedFilterLevel2(filterLevel2);
    }, 500);
    return () => clearTimeout(timer);
  }, [filterLevel2]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setAppliedFilterLevel3(filterLevel3);
    }, 500);
    return () => clearTimeout(timer);
  }, [filterLevel3]);

  // Charger les valeurs uniques pour les filtres
  useEffect(() => {
    const loadUniqueValues = async () => {
      try {
        const [noms, level1s, level2s, level3s] = await Promise.all([
          mappingsAPI.getUniqueValues('nom'),
          mappingsAPI.getUniqueValues('level_1'),
          mappingsAPI.getUniqueValues('level_2'),
          mappingsAPI.getUniqueValues('level_3'),
        ]);
        setUniqueNoms(noms.values);
        setUniqueLevel1s(level1s.values);
        setUniqueLevel2s(level2s.values);
        setUniqueLevel3s(level3s.values);
      } catch (err) {
        console.error('Error loading unique values:', err);
      }
    };
    loadUniqueValues();
  }, []);

  const handleSort = useCallback((column: SortColumn) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  }, [sortColumn, sortDirection]);

  // Handlers pour les filtres (mémorisés pour éviter les re-renders)
  const handleFilterNomChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setFilterNom(e.target.value);
  }, []);

  const handleFilterLevel1Change = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setFilterLevel1(e.target.value);
  }, []);

  const handleFilterLevel2Change = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setFilterLevel2(e.target.value);
  }, []);

  const handleFilterLevel3Change = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setFilterLevel3(e.target.value);
  }, []);

  // Fonction pour réinitialiser tous les filtres
  const handleClearFilters = useCallback(() => {
    // Réinitialiser tous les filtres (valeurs affichées)
    setFilterNom('');
    setFilterLevel1('');
    setFilterLevel2('');
    setFilterLevel3('');
    
    // Réinitialiser tous les filtres appliqués
    setAppliedFilterNom('');
    setAppliedFilterLevel1('');
    setAppliedFilterLevel2('');
    setAppliedFilterLevel3('');
  }, []);

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
      // Réinitialiser les dropdowns
      setAvailableLevel1ForCreate([]);
      setAvailableLevel2ForCreate([]);
      setAvailableLevel3ForCreate([]);
      loadMappings();
      onMappingChange?.();
    } catch (err: any) {
      alert(`Erreur lors de la création: ${err.message}`);
    }
  };
  
  // Charger les valeurs autorisées quand le modal de création s'ouvre
  useEffect(() => {
    if (showCreateModal) {
      const loadAllowedValues = async () => {
        try {
          const level1List = await allowedMappingsAPI.getAllowedLevel1();
          setAvailableLevel1ForCreate(level1List);
          
          const allLevel2List = await allowedMappingsAPI.getAllowedLevel2();
          setAvailableLevel2ForCreate(allLevel2List);
          
          const allLevel3List = await allowedMappingsAPI.getAllowedLevel3();
          setAvailableLevel3ForCreate(allLevel3List);
        } catch (err) {
          console.error('❌ Erreur lors du chargement des valeurs autorisées:', err);
        }
      };
      loadAllowedValues();
    }
  }, [showCreateModal]);
  
  // Handlers pour le filtrage hiérarchique dans le modal de création
  const handleCreateLevel1Change = async (value: string) => {
    if (!value) {
      setNewMapping({ ...newMapping, level_1: '', level_2: '', level_3: '' });
      const allLevel2List = await allowedMappingsAPI.getAllowedLevel2();
      setAvailableLevel2ForCreate(allLevel2List);
      const allLevel3List = await allowedMappingsAPI.getAllowedLevel3();
      setAvailableLevel3ForCreate(allLevel3List);
      return;
    }
    
    try {
      // Scénario 1 : level_1 → level_2 et level_3 sélectionnés automatiquement
      const combination = await allowedMappingsAPI.getUniqueCombinationForLevel1(value);
      if (combination) {
        setNewMapping({
          ...newMapping,
          level_1: value,
          level_2: combination.level_2 || '',
          level_3: combination.level_3 || '',
        });
        // Garder toutes les valeurs disponibles pour permettre le changement
        const allLevel2List = await allowedMappingsAPI.getAllowedLevel2();
        setAvailableLevel2ForCreate(allLevel2List);
        const allLevel3List = await allowedMappingsAPI.getAllowedLevel3();
        setAvailableLevel3ForCreate(allLevel3List);
      } else {
        setNewMapping({ ...newMapping, level_1: value });
      }
    } catch (err) {
      console.error('❌ Erreur lors de la sélection de level_1:', err);
      setNewMapping({ ...newMapping, level_1: value });
    }
  };
  
  const handleCreateLevel2Change = async (value: string) => {
    if (!value) {
      setNewMapping({ ...newMapping, level_2: '', level_3: '' });
      const allLevel3List = await allowedMappingsAPI.getAllowedLevel3();
      setAvailableLevel3ForCreate(allLevel3List);
      return;
    }
    
    try {
      // Scénario 2 : level_2 → level_3 sélectionné automatiquement, level_1 filtré
      const combination = await allowedMappingsAPI.getUniqueCombinationForLevel2(value);
      if (combination && combination.level_3) {
        setNewMapping({
          ...newMapping,
          level_2: value,
          level_3: combination.level_3,
        });
      } else {
        setNewMapping({ ...newMapping, level_2: value, level_3: '' });
      }
      
      // Filtrer level_1 par level_2
      const level1List = await allowedMappingsAPI.getAllowedLevel1ForLevel2(value);
      setAvailableLevel1ForCreate(level1List);
      
      // Garder toutes les valeurs level_3 disponibles
      const allLevel3List = await allowedMappingsAPI.getAllowedLevel3();
      setAvailableLevel3ForCreate(allLevel3List);
    } catch (err) {
      console.error('❌ Erreur lors de la sélection de level_2:', err);
      setNewMapping({ ...newMapping, level_2: value });
    }
  };
  
  const handleCreateLevel3Change = async (value: string) => {
    if (!value) {
      setNewMapping({ ...newMapping, level_3: '' });
      const allLevel2List = await allowedMappingsAPI.getAllowedLevel2();
      setAvailableLevel2ForCreate(allLevel2List);
      const allLevel1List = await allowedMappingsAPI.getAllowedLevel1();
      setAvailableLevel1ForCreate(allLevel1List);
      return;
    }
    
    try {
      // Scénario 3 : level_3 → level_2 filtré, level_1 filtré
      setNewMapping({ ...newMapping, level_3: value });
      
      // Filtrer level_2 par level_3
      const level2List = await allowedMappingsAPI.getAllowedLevel2ForLevel3(value);
      setAvailableLevel2ForCreate(level2List);
      
      // Si level_2 existe déjà, filtrer level_1 par le couple (level_2, level_3)
      if (newMapping.level_2) {
        const level1List = await allowedMappingsAPI.getAllowedLevel1ForLevel2AndLevel3(newMapping.level_2, value);
        setAvailableLevel1ForCreate(level1List);
      } else {
        // Garder toutes les valeurs level_1 disponibles
        const allLevel1List = await allowedMappingsAPI.getAllowedLevel1();
        setAvailableLevel1ForCreate(allLevel1List);
      }
    } catch (err) {
      console.error('❌ Erreur lors de la sélection de level_3:', err);
      setNewMapping({ ...newMapping, level_3: value });
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

  const handleEdit = async (mapping: Mapping) => {
    setEditingId(mapping.id);
    
    // Initialiser les valeurs d'édition
    setEditingMappingValues({
      level_1: mapping.level_1 || undefined,
      level_2: mapping.level_2 || undefined,
      level_3: mapping.level_3 || undefined,
    });
    
    // Charger les valeurs autorisées pour les dropdowns
    try {
      const level1List = await allowedMappingsAPI.getAllowedLevel1();
      setAvailableLevel1ForEdit(level1List);
      
      const allLevel2List = await allowedMappingsAPI.getAllowedLevel2();
      setAvailableLevel2ForEdit(allLevel2List);
      
      const allLevel3List = await allowedMappingsAPI.getAllowedLevel3();
      setAvailableLevel3ForEdit(allLevel3List);
    } catch (err) {
      console.error('❌ Erreur lors du chargement des valeurs autorisées:', err);
    }
  };

  const handleSaveEdit = async (mapping: Mapping, updates: MappingUpdate) => {
    try {
      await mappingsAPI.update(mapping.id, updates);
      setEditingId(null);
      setEditingMappingValues({});
      loadMappings();
      onMappingChange?.();
    } catch (err: any) {
      // Si le mapping n'existe plus (404), rafraîchir la liste
      if (err.message && err.message.includes('non trouvé')) {
        console.warn(`Mapping avec ID ${mapping.id} non trouvé, rafraîchissement de la liste...`);
        loadMappings();
        setEditingId(null);
        setEditingMappingValues({});
        alert(`Le mapping n'existe plus. La liste a été rafraîchie.`);
      } else {
        alert(`Erreur lors de la modification: ${err.message}`);
      }
    }
  };
  
  // Handlers pour le filtrage hiérarchique dans l'édition inline (sans sauvegarde immédiate)
  const handleEditLevel1Change = async (value: string) => {
    if (!value) {
      setEditingMappingValues({ ...editingMappingValues, level_1: undefined, level_2: undefined, level_3: undefined });
      const allLevel2List = await allowedMappingsAPI.getAllowedLevel2();
      setAvailableLevel2ForEdit(allLevel2List);
      const allLevel3List = await allowedMappingsAPI.getAllowedLevel3();
      setAvailableLevel3ForEdit(allLevel3List);
      return;
    }
    
    try {
      // Scénario 1 : level_1 → level_2 et level_3 sélectionnés automatiquement
      const combination = await allowedMappingsAPI.getUniqueCombinationForLevel1(value);
      if (combination) {
        setEditingMappingValues({
          ...editingMappingValues,
          level_1: value,
          level_2: combination.level_2 || undefined,
          level_3: combination.level_3 || undefined,
        });
        // Garder toutes les valeurs disponibles pour permettre le changement
        const allLevel2List = await allowedMappingsAPI.getAllowedLevel2();
        setAvailableLevel2ForEdit(allLevel2List);
        const allLevel3List = await allowedMappingsAPI.getAllowedLevel3();
        setAvailableLevel3ForEdit(allLevel3List);
      } else {
        setEditingMappingValues({ ...editingMappingValues, level_1: value });
      }
    } catch (err) {
      console.error('❌ Erreur lors de la sélection de level_1:', err);
      setEditingMappingValues({ ...editingMappingValues, level_1: value });
    }
  };
  
  const handleEditLevel2Change = async (value: string) => {
    if (!value) {
      setEditingMappingValues({ ...editingMappingValues, level_2: undefined, level_3: undefined });
      const allLevel3List = await allowedMappingsAPI.getAllowedLevel3();
      setAvailableLevel3ForEdit(allLevel3List);
      return;
    }
    
    try {
      // Scénario 2 : level_2 → level_3 sélectionné automatiquement, level_1 filtré
      const combination = await allowedMappingsAPI.getUniqueCombinationForLevel2(value);
      if (combination && combination.level_3) {
        setEditingMappingValues({ ...editingMappingValues, level_2: value, level_3: combination.level_3 });
      } else {
        setEditingMappingValues({ ...editingMappingValues, level_2: value, level_3: undefined });
      }
      
      // Filtrer level_1 par level_2
      const level1List = await allowedMappingsAPI.getAllowedLevel1ForLevel2(value);
      setAvailableLevel1ForEdit(level1List);
      
      // Garder toutes les valeurs level_3 disponibles
      const allLevel3List = await allowedMappingsAPI.getAllowedLevel3();
      setAvailableLevel3ForEdit(allLevel3List);
    } catch (err) {
      console.error('❌ Erreur lors de la sélection de level_2:', err);
      setEditingMappingValues({ ...editingMappingValues, level_2: value });
    }
  };
  
  const handleEditLevel3Change = async (value: string) => {
    if (!value) {
      setEditingMappingValues({ ...editingMappingValues, level_3: undefined });
      const allLevel2List = await allowedMappingsAPI.getAllowedLevel2();
      setAvailableLevel2ForEdit(allLevel2List);
      const allLevel1List = await allowedMappingsAPI.getAllowedLevel1();
      setAvailableLevel1ForEdit(allLevel1List);
      return;
    }
    
    try {
      // Scénario 3 : level_3 → level_2 filtré, level_1 filtré
      setEditingMappingValues({ ...editingMappingValues, level_3: value });
      
      // Filtrer level_2 par level_3
      const level2List = await allowedMappingsAPI.getAllowedLevel2ForLevel3(value);
      setAvailableLevel2ForEdit(level2List);
      
      // Si level_2 existe déjà, filtrer level_1 par le couple (level_2, level_3)
      if (editingMappingValues.level_2) {
        const level1List = await allowedMappingsAPI.getAllowedLevel1ForLevel2AndLevel3(editingMappingValues.level_2, value);
        setAvailableLevel1ForEdit(level1List);
      } else {
        // Garder toutes les valeurs level_1 disponibles
        const allLevel1List = await allowedMappingsAPI.getAllowedLevel1();
        setAvailableLevel1ForEdit(allLevel1List);
      }
    } catch (err) {
      console.error('❌ Erreur lors de la sélection de level_3:', err);
      setEditingMappingValues({ ...editingMappingValues, level_3: value });
    }
  };
  
  // Handler pour sauvegarder les modifications (appelé par le bouton ✓)
  const handleSaveEditClick = async (mapping: Mapping) => {
    const updates: MappingUpdate = {};
    if (editingMappingValues.level_1 !== undefined) {
      updates.level_1 = editingMappingValues.level_1 || undefined;
    }
    if (editingMappingValues.level_2 !== undefined) {
      updates.level_2 = editingMappingValues.level_2 || undefined;
    }
    if (editingMappingValues.level_3 !== undefined) {
      updates.level_3 = editingMappingValues.level_3 || undefined;
    }
    
    if (Object.keys(updates).length > 0) {
      await handleSaveEdit(mapping, updates);
    } else {
      // Aucun changement, juste fermer l'édition
      setEditingId(null);
      setEditingMappingValues({});
    }
  };

  const handleExportMappings = async () => {
    setIsExporting(true);
    try {
      // Récupérer tous les mappings
      const allMappings = await mappingsAPI.getAll();
      
      if (allMappings.length === 0) {
        alert('Aucun mapping à exporter.');
        setIsExporting(false);
        return;
      }
      
      // Générer le nom de fichier avec la date
      const filename = generateDefaultFilename();
      
      // Exporter et ouvrir le dialogue de sauvegarde
      await exportAndDownloadMappings(allMappings, filename);
      
      // Message de succès
      alert(`✅ Export réussi !\n\n${allMappings.length} mapping${allMappings.length > 1 ? 's' : ''} exporté${allMappings.length > 1 ? 's' : ''} vers ${filename}`);
    } catch (err: any) {
      // Ne pas afficher d'erreur si l'utilisateur a annulé
      if (err.message && err.message.includes('annulé')) {
        // L'utilisateur a annulé, ne rien faire
        return;
      }
      alert(`❌ Erreur lors de l'export: ${err.message}`);
      console.error('Erreur export mappings:', err);
    } finally {
      setIsExporting(false);
    }
  };

  const handleReEnrichAll = async () => {
    if (!confirm('Êtes-vous sûr de vouloir re-enrichir toutes les transactions ? Cette opération peut prendre quelques instants.')) {
      return;
    }

    setIsReEnriching(true);
    try {
      const result = await enrichmentAPI.reEnrichAll();
      alert(`✅ ${result.message}\n\n${result.enriched_count} nouvelles transactions enrichies\n${result.already_enriched_count} transactions re-enrichies\nTotal: ${result.total_processed} transactions traitées`);
      onMappingChange?.(); // Rafraîchir les transactions si nécessaire
    } catch (err: any) {
      alert(`Erreur lors du re-enrichissement: ${err.message}`);
    } finally {
      setIsReEnriching(false);
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
          <button
            onClick={handleExportMappings}
            disabled={isExporting}
            style={{
              padding: '8px 16px',
              fontSize: '14px',
              backgroundColor: isExporting ? '#ccc' : '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: isExporting ? 'not-allowed' : 'pointer',
              opacity: isExporting ? 0.6 : 1,
            }}
            title="Exporter tous les mappings vers un fichier Excel (.xlsx)"
          >
            {isExporting ? '⏳ Export...' : '📥 Extraire mapping'}
          </button>
          <button
            onClick={handleReEnrichAll}
            disabled={isReEnriching}
            style={{
              padding: '8px 16px',
              fontSize: '14px',
              backgroundColor: isReEnriching ? '#ccc' : '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: isReEnriching ? 'not-allowed' : 'pointer',
              opacity: isReEnriching ? 0.6 : 1,
            }}
            title="Re-enrichir toutes les transactions avec les mappings disponibles. Utile après avoir importé de nouveaux mappings."
          >
            {isReEnriching ? '⏳ Re-enrichissement...' : '🔄 Re-enrichir toutes les transactions'}
          </button>
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

      {/* Pagination en haut */}
      {totalPages > 1 && (
        <div style={{ 
          marginBottom: '16px', 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px'
        }}>
          <div style={{ fontSize: '14px', color: '#666' }}>
            Page {page} sur {totalPages} ({total} mapping{total !== 1 ? 's' : ''})
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => setPage(1)}
              disabled={page === 1}
              style={{
                padding: '8px 12px',
                backgroundColor: page === 1 ? '#e5e5e5' : '#1e3a5f',
                color: page === 1 ? '#999' : 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '14px',
                cursor: page === 1 ? 'not-allowed' : 'pointer',
              }}
            >
              « Première
            </button>
            <button
              onClick={() => setPage(page - 1)}
              disabled={page === 1}
              style={{
                padding: '8px 12px',
                backgroundColor: page === 1 ? '#e5e5e5' : '#1e3a5f',
                color: page === 1 ? '#999' : 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '14px',
                cursor: page === 1 ? 'not-allowed' : 'pointer',
              }}
            >
              ‹ Précédente
            </button>
            <button
              onClick={() => setPage(page + 1)}
              disabled={page >= totalPages}
              style={{
                padding: '8px 12px',
                backgroundColor: page >= totalPages ? '#e5e5e5' : '#1e3a5f',
                color: page >= totalPages ? '#999' : 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '14px',
                cursor: page >= totalPages ? 'not-allowed' : 'pointer',
              }}
            >
              Suivante ›
            </button>
            <button
              onClick={() => setPage(totalPages)}
              disabled={page >= totalPages}
              style={{
                padding: '8px 12px',
                backgroundColor: page >= totalPages ? '#e5e5e5' : '#1e3a5f',
                color: page >= totalPages ? '#999' : 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '14px',
                cursor: page >= totalPages ? 'not-allowed' : 'pointer',
              }}
            >
              Dernière »
            </button>
          </div>
          <div>
            <label style={{ fontSize: '14px', color: '#666', marginRight: '8px' }}>
              Par page:
            </label>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setPage(1);
              }}
              style={{
                padding: '6px 12px',
                border: '1px solid #ccc',
                borderRadius: '4px',
                fontSize: '14px',
              }}
            >
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
              <option value={200}>200</option>
            </select>
          </div>
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
              <th
                onClick={() => handleSort('id')}
                style={{
                  padding: '12px',
                  textAlign: 'left',
                  fontWeight: '600',
                  color: '#1a1a1a',
                  cursor: 'pointer',
                  userSelect: 'none',
                }}
              >
                ID {sortColumn === 'id' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th
                onClick={() => handleSort('nom')}
                style={{
                  padding: '12px',
                  textAlign: 'left',
                  fontWeight: '600',
                  color: '#1a1a1a',
                  cursor: 'pointer',
                  userSelect: 'none',
                }}
              >
                Nom {sortColumn === 'nom' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th
                onClick={() => handleSort('level_1')}
                style={{
                  padding: '12px',
                  textAlign: 'left',
                  fontWeight: '600',
                  color: '#1a1a1a',
                  cursor: 'pointer',
                  userSelect: 'none',
                }}
              >
                Level 1 {sortColumn === 'level_1' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th
                onClick={() => handleSort('level_2')}
                style={{
                  padding: '12px',
                  textAlign: 'left',
                  fontWeight: '600',
                  color: '#1a1a1a',
                  cursor: 'pointer',
                  userSelect: 'none',
                }}
              >
                Level 2 {sortColumn === 'level_2' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th
                onClick={() => handleSort('level_3')}
                style={{
                  padding: '12px',
                  textAlign: 'left',
                  fontWeight: '600',
                  color: '#1a1a1a',
                  cursor: 'pointer',
                  userSelect: 'none',
                }}
              >
                Level 3 {sortColumn === 'level_3' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th style={{ padding: '12px', textAlign: 'center', fontWeight: '600', color: '#1a1a1a' }}>Préfixe</th>
              <th style={{ padding: '12px', textAlign: 'center', fontWeight: '600', color: '#1a1a1a' }}>Actions</th>
            </tr>
            {/* Ligne de filtres */}
            <tr key="filter-row" style={{ backgroundColor: '#fafafa', borderBottom: '1px solid #e5e5e5' }}>
              <td style={{ padding: '8px', textAlign: 'center' }}></td>
              <td style={{ padding: '8px' }}></td>
              <td style={{ padding: '8px' }}>
                <div style={{ position: 'relative' }}>
                  <input
                    type="text"
                    value={filterNom}
                    onChange={handleFilterNomChange}
                    placeholder="Filtrer..."
                    list={`nom-list-${page}`}
                    style={{
                      width: '100%',
                      padding: '4px 8px',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      fontSize: '12px',
                    }}
                  />
                  <datalist id={`nom-list-${page}`}>
                    {uniqueNoms.map((nom) => (
                      <option key={nom} value={nom} />
                    ))}
                  </datalist>
                </div>
              </td>
              <td style={{ padding: '8px' }}>
                <div style={{ position: 'relative' }}>
                  <input
                    type="text"
                    value={filterLevel1}
                    onChange={handleFilterLevel1Change}
                    placeholder="Filtrer..."
                    list={`level1-list-${page}`}
                    style={{
                      width: '100%',
                      padding: '4px 8px',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      fontSize: '12px',
                    }}
                  />
                  <datalist id={`level1-list-${page}`}>
                    {uniqueLevel1s.map((level1) => (
                      <option key={level1} value={level1} />
                    ))}
                  </datalist>
                </div>
              </td>
              <td style={{ padding: '8px' }}>
                <div style={{ position: 'relative' }}>
                  <input
                    type="text"
                    value={filterLevel2}
                    onChange={handleFilterLevel2Change}
                    placeholder="Filtrer..."
                    list={`level2-list-${page}`}
                    style={{
                      width: '100%',
                      padding: '4px 8px',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      fontSize: '12px',
                    }}
                  />
                  <datalist id={`level2-list-${page}`}>
                    {uniqueLevel2s.map((level2) => (
                      <option key={level2} value={level2} />
                    ))}
                  </datalist>
                </div>
              </td>
              <td style={{ padding: '8px' }}>
                <div style={{ position: 'relative' }}>
                  <input
                    type="text"
                    value={filterLevel3}
                    onChange={handleFilterLevel3Change}
                    placeholder="Filtrer..."
                    list={`level3-list-${page}`}
                    style={{
                      width: '100%',
                      padding: '4px 8px',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      fontSize: '12px',
                    }}
                  />
                  <datalist id={`level3-list-${page}`}>
                    {uniqueLevel3s.map((level3) => (
                      <option key={level3} value={level3} />
                    ))}
                  </datalist>
                </div>
              </td>
              <td style={{ padding: '8px', textAlign: 'center' }}></td>
              <td style={{ padding: '8px', textAlign: 'center' }}>
                <button
                  onClick={handleClearFilters}
                  style={{
                    padding: '6px 12px',
                    backgroundColor: '#f44336',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '12px',
                    fontWeight: '500',
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.backgroundColor = '#d32f2f';
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.backgroundColor = '#f44336';
                  }}
                >
                  Clear filters
                </button>
              </td>
            </tr>
          </thead>
          <tbody>
            {mappings.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
                  Aucun mapping trouvé
                </td>
              </tr>
            ) : (
              mappings.map((mapping) => (
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
                    <select
                      value={editingMappingValues.level_1 || ''}
                      onChange={(e) => handleEditLevel1Change(e.target.value)}
                      style={{ width: '100%', padding: '4px', border: '1px solid #ddd', borderRadius: '2px' }}
                    >
                      <option value="">Unassigned</option>
                      {availableLevel1ForEdit.map((val) => (
                        <option key={val} value={val}>{val}</option>
                      ))}
                    </select>
                  ) : (
                    mapping.level_1
                  )}
                </td>
                <td style={{ padding: '12px' }}>
                  {editingId === mapping.id ? (
                    <select
                      value={editingMappingValues.level_2 || ''}
                      onChange={(e) => handleEditLevel2Change(e.target.value)}
                      style={{ width: '100%', padding: '4px', border: '1px solid #ddd', borderRadius: '2px' }}
                    >
                      <option value="">Unassigned</option>
                      {availableLevel2ForEdit.map((val) => (
                        <option key={val} value={val}>{val}</option>
                      ))}
                    </select>
                  ) : (
                    mapping.level_2
                  )}
                </td>
                <td style={{ padding: '12px' }}>
                  {editingId === mapping.id ? (
                    <select
                      value={editingMappingValues.level_3 || ''}
                      onChange={(e) => handleEditLevel3Change(e.target.value)}
                      style={{ width: '100%', padding: '4px', border: '1px solid #ddd', borderRadius: '2px' }}
                    >
                      <option value="">Unassigned</option>
                      {availableLevel3ForEdit.map((val) => (
                        <option key={val} value={val}>{val}</option>
                      ))}
                    </select>
                  ) : (
                    mapping.level_3 || '-'
                  )}
                </td>
                <td style={{ padding: '12px', textAlign: 'center' }}>
                  {mapping.is_prefix_match ? '✓' : '✗'}
                </td>
                <td style={{ padding: '12px', textAlign: 'center', display: 'flex', gap: '8px', justifyContent: 'center' }}>
                  {editingId === mapping.id ? (
                    <>
                      <button
                        onClick={() => handleSaveEditClick(mapping)}
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
                      <button
                        onClick={() => {
                          setEditingId(null);
                          setEditingMappingValues({});
                        }}
                        style={{
                          padding: '4px 8px',
                          fontSize: '12px',
                          backgroundColor: '#6c757d',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                        }}
                      >
                        ✗
                      </button>
                    </>
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
              ))
            )}
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
                <select
                  value={newMapping.level_1}
                  onChange={(e) => handleCreateLevel1Change(e.target.value)}
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                >
                  <option value="">Unassigned</option>
                  {availableLevel1ForCreate.map((val) => (
                    <option key={val} value={val}>{val}</option>
                  ))}
                </select>
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>Level 2 *</label>
                <select
                  value={newMapping.level_2}
                  onChange={(e) => handleCreateLevel2Change(e.target.value)}
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                >
                  <option value="">Unassigned</option>
                  {availableLevel2ForCreate.map((val) => (
                    <option key={val} value={val}>{val}</option>
                  ))}
                </select>
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>Level 3</label>
                <select
                  value={newMapping.level_3 || ''}
                  onChange={(e) => handleCreateLevel3Change(e.target.value)}
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                >
                  <option value="">Unassigned</option>
                  {availableLevel3ForCreate.map((val) => (
                    <option key={val} value={val}>{val}</option>
                  ))}
                </select>
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
});

MappingTable.displayName = 'MappingTable';

export default MappingTable;

