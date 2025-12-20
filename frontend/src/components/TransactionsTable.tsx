/**
 * TransactionsTable component - Tableau des transactions avec tri, pagination et suppression
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { transactionsAPI, Transaction, TransactionUpdate, enrichmentAPI, mappingsAPI } from '@/api/client';

interface TransactionsTableProps {
  onDelete?: () => void;
}

type SortColumn = 'date' | 'quantite' | 'nom' | 'solde' | 'level_1' | 'level_2' | 'level_3';
type SortDirection = 'asc' | 'desc';

export default function TransactionsTable({ onDelete }: TransactionsTableProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [sortColumn, setSortColumn] = useState<SortColumn>('date');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [searchTerm, setSearchTerm] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingValues, setEditingValues] = useState<{ date?: string; nom?: string; quantite?: number }>({});
  const [editingClassificationId, setEditingClassificationId] = useState<number | null>(null);
  const [editingClassificationValues, setEditingClassificationValues] = useState<{ level_1?: string; level_2?: string; level_3?: string }>({});
  const [availableLevel1, setAvailableLevel1] = useState<string[]>([]);
  const [availableLevel2, setAvailableLevel2] = useState<string[]>([]);
  const [availableLevel3, setAvailableLevel3] = useState<string[]>([]);
  const [customLevel1, setCustomLevel1] = useState(false);
  const [customLevel2, setCustomLevel2] = useState(false);
  const [customLevel3, setCustomLevel3] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [isDeletingMultiple, setIsDeletingMultiple] = useState(false);
  
  // États pour les filtres (valeurs affichées dans les inputs)
  const [filterDate, setFilterDate] = useState('');
  const [filterQuantite, setFilterQuantite] = useState('');
  const [filterNom, setFilterNom] = useState('');
  const [filterSolde, setFilterSolde] = useState('');
  const [filterLevel1, setFilterLevel1] = useState('');
  const [filterLevel2, setFilterLevel2] = useState('');
  const [filterLevel3, setFilterLevel3] = useState('');
  
  // États pour les filtres appliqués (après debounce)
  const [appliedFilterDate, setAppliedFilterDate] = useState('');
  const [appliedFilterQuantite, setAppliedFilterQuantite] = useState('');
  const [appliedFilterNom, setAppliedFilterNom] = useState('');
  const [appliedFilterSolde, setAppliedFilterSolde] = useState('');
  const [appliedFilterLevel1, setAppliedFilterLevel1] = useState('');
  const [appliedFilterLevel2, setAppliedFilterLevel2] = useState('');
  const [appliedFilterLevel3, setAppliedFilterLevel3] = useState('');
  
  // Données brutes chargées depuis l'API (sans filtres appliqués)
  const [rawTransactions, setRawTransactions] = useState<Transaction[]>([]);
  
  // Valeurs uniques pour les dropdowns
  const [uniqueNoms, setUniqueNoms] = useState<string[]>([]);
  const [uniqueLevel1s, setUniqueLevel1s] = useState<string[]>([]);
  const [uniqueLevel2s, setUniqueLevel2s] = useState<string[]>([]);
  const [uniqueLevel3s, setUniqueLevel3s] = useState<string[]>([]);

  const loadTransactions = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const skip = (page - 1) * pageSize;
      // Appel API avec tri côté serveur
      const response = await transactionsAPI.getAll(
        skip,
        pageSize,
        startDate || undefined,
        endDate || undefined,
        sortColumn, // Passer le tri à l'API
        sortDirection
      );
      
      // Filtrer par terme de recherche si présent (côté client car pas encore implémenté côté serveur)
      let filtered = response.transactions;
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        filtered = filtered.filter(t => 
          t.nom.toLowerCase().includes(searchLower)
        );
      }

      // Stocker les données brutes (sans filtres de colonnes) pour filtrage local
      setRawTransactions(filtered);
      setTotal(response.total);
      
      // Les filtres seront appliqués par useMemo (pas besoin de setTransactions)
      
      // Réinitialiser la sélection si les transactions chargées ne contiennent plus les IDs sélectionnés
      // (sera fait après le calcul des transactions filtrées par useMemo)
    } catch (err) {
      console.error('Error loading transactions:', err);
      setError(err instanceof Error ? err.message : 'Erreur lors du chargement');
    } finally {
      setIsLoading(false);
    }
  };

  // Recharger depuis l'API seulement quand page, tri, ou date range change
  useEffect(() => {
    loadTransactions();
  }, [page, pageSize, sortColumn, sortDirection, startDate, endDate]);

  // Calculer les transactions filtrées avec useMemo (évite les re-renders inutiles et préserve le focus)
  const transactions = useMemo(() => {
    if (rawTransactions.length === 0) {
      return [];
    }
    
    let filtered = [...rawTransactions];

    // Filtrer par terme de recherche si présent
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter(t => 
        t.nom.toLowerCase().includes(searchLower)
      );
    }

    // Appliquer les filtres de colonnes
    if (appliedFilterDate) {
      const filterDateObj = new Date(appliedFilterDate);
      filtered = filtered.filter(t => {
        const tDate = new Date(t.date);
        return tDate.toDateString() === filterDateObj.toDateString();
      });
    }
    if (appliedFilterNom) {
      const filterLower = appliedFilterNom.toLowerCase();
      filtered = filtered.filter(t => 
        t.nom?.toLowerCase().includes(filterLower)
      );
    }
    if (appliedFilterLevel1) {
      const filterLower = appliedFilterLevel1.toLowerCase();
      filtered = filtered.filter(t => 
        t.level_1?.toLowerCase().includes(filterLower)
      );
    }
    if (appliedFilterLevel2) {
      const filterLower = appliedFilterLevel2.toLowerCase();
      filtered = filtered.filter(t => 
        t.level_2?.toLowerCase().includes(filterLower)
      );
    }
    if (appliedFilterLevel3) {
      const filterLower = appliedFilterLevel3.toLowerCase();
      filtered = filtered.filter(t => 
        t.level_3?.toLowerCase().includes(filterLower)
      );
    }
    // Filtrer par quantité avec filtre "contient" (si on tape "14", trouve 14, 14.02, 140, 14000, etc.)
    if (appliedFilterQuantite && appliedFilterQuantite.trim() !== '') {
      const filterValue = appliedFilterQuantite.trim();
      // Vérifier si c'est un nombre valide (même partiel)
      if (filterValue !== '' && !isNaN(Number(filterValue))) {
        // Convertir en string pour vérifier si la valeur tapée est contenue dans le nombre
        filtered = filtered.filter(t => {
          const quantiteStr = t.quantite.toString();
          return quantiteStr.includes(filterValue);
        });
      }
    }
    // Filtrer par solde avec filtre "contient" (si on tape "14", trouve 14, 14.02, 140, 14000, etc.)
    if (appliedFilterSolde && appliedFilterSolde.trim() !== '') {
      const filterValue = appliedFilterSolde.trim();
      // Vérifier si c'est un nombre valide (même partiel)
      if (filterValue !== '' && !isNaN(Number(filterValue))) {
        // Convertir en string pour vérifier si la valeur tapée est contenue dans le nombre
        filtered = filtered.filter(t => {
          const soldeStr = t.solde.toString();
          return soldeStr.includes(filterValue);
        });
      }
    }

    return filtered;
  }, [rawTransactions, searchTerm, appliedFilterDate, appliedFilterNom, appliedFilterLevel1, appliedFilterLevel2, appliedFilterLevel3, appliedFilterQuantite, appliedFilterSolde]);

  // Réinitialiser la sélection quand les transactions changent
  useEffect(() => {
    setSelectedIds(prev => {
      const loadedIds = new Set(transactions.map(t => t.id));
      const newSet = new Set<number>();
      prev.forEach(id => {
        if (loadedIds.has(id)) {
          newSet.add(id);
        }
      });
      return newSet;
    });
  }, [transactions]);

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

  // Pas de debounce pour date (changement immédiat)
  useEffect(() => {
    setAppliedFilterDate(filterDate);
  }, [filterDate]);

  // Pour quantite et solde, on n'applique le filtre que manuellement (pas de debounce automatique)
  // Le filtre sera appliqué via onBlur ou onKeyDown (Enter)
  // Cela évite de filtrer pendant la saisie et de tout cacher si aucune transaction ne correspond

  // Charger les valeurs uniques pour les filtres
  useEffect(() => {
    const loadUniqueValues = async () => {
      try {
        const [noms, level1s, level2s, level3s] = await Promise.all([
          transactionsAPI.getUniqueValues('nom', startDate || undefined, endDate || undefined),
          transactionsAPI.getUniqueValues('level_1', startDate || undefined, endDate || undefined),
          transactionsAPI.getUniqueValues('level_2', startDate || undefined, endDate || undefined),
          transactionsAPI.getUniqueValues('level_3', startDate || undefined, endDate || undefined),
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
  }, [startDate, endDate]);

  // Recharger quand le terme de recherche change (avec debounce)
  useEffect(() => {
    const timer = setTimeout(() => {
      loadTransactions();
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  const handleSort = useCallback((column: SortColumn) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  }, [sortColumn, sortDirection]);

  // Handlers pour les filtres (mémorisés pour éviter les re-renders)
  const handleFilterDateChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setFilterDate(e.target.value);
  }, []);

  const handleFilterQuantiteChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setFilterQuantite(e.target.value);
  }, []);

  const handleFilterNomChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setFilterNom(e.target.value);
  }, []);

  const handleFilterSoldeChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setFilterSolde(e.target.value);
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

  // Handlers pour appliquer le filtre quantité/solde UNIQUEMENT via Enter (pas de onBlur)
  const handleFilterQuantiteKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      // Appliquer le filtre seulement si la valeur est valide
      const value = e.currentTarget.value.trim();
      if (value === '') {
        // Si vide, réinitialiser le filtre
        setFilterQuantite('');
        setAppliedFilterQuantite('');
      } else {
        const num = parseFloat(value);
        if (!isNaN(num) && isFinite(num)) {
          setAppliedFilterQuantite(value);
        }
      }
      e.currentTarget.blur(); // Retirer le focus après validation
    } else if (e.key === 'Escape') {
      setFilterQuantite('');
      setAppliedFilterQuantite('');
      e.currentTarget.blur();
    }
  }, []);

  const handleFilterSoldeKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      // Appliquer le filtre seulement si la valeur est valide
      const value = e.currentTarget.value.trim();
      if (value === '') {
        // Si vide, réinitialiser le filtre
        setFilterSolde('');
        setAppliedFilterSolde('');
      } else {
        const num = parseFloat(value);
        if (!isNaN(num) && isFinite(num)) {
          setAppliedFilterSolde(value);
        }
      }
      e.currentTarget.blur(); // Retirer le focus après validation
    } else if (e.key === 'Escape') {
      setFilterSolde('');
      setAppliedFilterSolde('');
      e.currentTarget.blur();
    }
  }, []);

  // Fonction pour réinitialiser tous les filtres
  const handleClearFilters = useCallback(() => {
    // Réinitialiser tous les filtres (valeurs affichées)
    setFilterDate('');
    setFilterQuantite('');
    setFilterNom('');
    setFilterSolde('');
    setFilterLevel1('');
    setFilterLevel2('');
    setFilterLevel3('');
    
    // Réinitialiser tous les filtres appliqués
    setAppliedFilterDate('');
    setAppliedFilterQuantite('');
    setAppliedFilterNom('');
    setAppliedFilterSolde('');
    setAppliedFilterLevel1('');
    setAppliedFilterLevel2('');
    setAppliedFilterLevel3('');
  }, []);


  const handleDelete = async (id: number) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette transaction ?')) {
      return;
    }

    setDeletingId(id);
    try {
      await transactionsAPI.delete(id);
      setSelectedIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
      await loadTransactions();
      if (onDelete) {
        onDelete();
      }
    } catch (err) {
      console.error('Error deleting transaction:', err);
      alert('Erreur lors de la suppression de la transaction');
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
    if (selectedIds.size === transactions.length) {
      // Tout désélectionner
      setSelectedIds(new Set());
    } else {
      // Tout sélectionner
      setSelectedIds(new Set(transactions.map(t => t.id)));
    }
  };

  const handleDeleteMultiple = async () => {
    if (selectedIds.size === 0) {
      return;
    }

    const count = selectedIds.size;
    if (!confirm(`Êtes-vous sûr de vouloir supprimer ${count} transaction${count > 1 ? 's' : ''} ?`)) {
      return;
    }

    setIsDeletingMultiple(true);
    try {
      // Supprimer toutes les transactions sélectionnées
      const deletePromises = Array.from(selectedIds).map(id => transactionsAPI.delete(id));
      await Promise.all(deletePromises);
      
      setSelectedIds(new Set());
      await loadTransactions();
      if (onDelete) {
        onDelete();
      }
    } catch (err) {
      console.error('Error deleting transactions:', err);
      alert(`Erreur lors de la suppression de ${count} transaction${count > 1 ? 's' : ''}`);
    } finally {
      setIsDeletingMultiple(false);
    }
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
  };

  const formatAmount = (amount: number): string => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const handleEdit = (transaction: Transaction) => {
    setEditingId(transaction.id);
    // Convertir la date au format YYYY-MM-DD pour l'input
    const dateObj = new Date(transaction.date);
    const year = dateObj.getFullYear();
    const month = String(dateObj.getMonth() + 1).padStart(2, '0');
    const day = String(dateObj.getDate()).padStart(2, '0');
    setEditingValues({
      date: `${year}-${month}-${day}`,
      nom: transaction.nom,
      quantite: transaction.quantite,
    });
  };

  const handleSaveEdit = async (transaction: Transaction) => {
    try {
      const updates: TransactionUpdate = {};
      
      // Vérifier si les valeurs ont changé
      const dateObj = new Date(transaction.date);
      const year = dateObj.getFullYear();
      const month = String(dateObj.getMonth() + 1).padStart(2, '0');
      const day = String(dateObj.getDate()).padStart(2, '0');
      const currentDateStr = `${year}-${month}-${day}`;
      
      if (editingValues.date && editingValues.date !== currentDateStr) {
        updates.date = editingValues.date;
      }
      if (editingValues.nom !== undefined && editingValues.nom !== transaction.nom) {
        updates.nom = editingValues.nom;
      }
      if (editingValues.quantite !== undefined && editingValues.quantite !== transaction.quantite) {
        updates.quantite = editingValues.quantite;
      }

      // Si des modifications ont été faites, sauvegarder
      if (Object.keys(updates).length > 0) {
        await transactionsAPI.update(transaction.id, updates);
        setEditingId(null);
        setEditingValues({});
        await loadTransactions();
        if (onDelete) {
          onDelete();
        }
      } else {
        // Aucune modification, juste annuler l'édition
        setEditingId(null);
        setEditingValues({});
      }
    } catch (err: any) {
      console.error('Error updating transaction:', err);
      alert(`Erreur lors de la modification: ${err.message || 'Erreur inconnue'}`);
    }
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditingValues({});
  };

  const handleEditClassification = async (transaction: Transaction) => {
    setEditingClassificationId(transaction.id);
    const currentLevel1 = transaction.level_1 || undefined;
    const currentLevel2 = transaction.level_2 || undefined;
    const currentLevel3 = transaction.level_3 || undefined;
    
    setEditingClassificationValues({
      level_1: currentLevel1,
      level_2: currentLevel2,
      level_3: currentLevel3,
    });
    
    // Vérifier si les valeurs actuelles sont "custom" (pas dans les mappings)
    setCustomLevel1(false);
    setCustomLevel2(false);
    setCustomLevel3(false);
    
    // Charger les combinaisons disponibles
    try {
      const combinations = await mappingsAPI.getCombinations();
      console.log('🔍 [Combinations] Réponse API:', combinations);
      const level1List = combinations.level_1 || [];
      console.log('🔍 [Combinations] Level 1 list:', level1List);
      // Si la valeur actuelle n'est pas dans la liste, c'est une valeur custom
      if (currentLevel1 && !level1List.includes(currentLevel1)) {
        setCustomLevel1(true);
        level1List.push(currentLevel1); // Ajouter quand même pour l'affichage
      }
      setAvailableLevel1(level1List);
      console.log('🔍 [Combinations] Level 1 final:', level1List);
      
      // Charger TOUS les level_2 et level_3 disponibles dès le début (pour les transactions "à remplir")
      const allLevel2Combinations = await mappingsAPI.getCombinations(undefined, undefined, true, false);
      const allLevel2List = allLevel2Combinations.level_2 || [];
      console.log('🔍 [Combinations] All level_2 loaded (initial):', allLevel2List);
      setAvailableLevel2(allLevel2List);
      
      const allLevel3Combinations = await mappingsAPI.getCombinations(undefined, undefined, false, true);
      const allLevel3List = allLevel3Combinations.level_3 || [];
      console.log('🔍 [Combinations] All level_3 loaded (initial):', allLevel3List);
      setAvailableLevel3(allLevel3List);
      
      // Si level_1 existe, charger les level_2 possibles (mais garder tous les level_3)
      if (currentLevel1) {
        const level2Combinations = await mappingsAPI.getCombinations(currentLevel1);
        const level2List = level2Combinations.level_2 || [];
        // Si la valeur actuelle n'est pas dans la liste, c'est une valeur custom
        if (currentLevel2 && !level2List.includes(currentLevel2)) {
          setCustomLevel2(true);
          level2List.push(currentLevel2); // Ajouter quand même pour l'affichage
        }
        setAvailableLevel2(level2List);
        
        // Si level_2 existe aussi, charger les level_3 possibles
        if (currentLevel2) {
          const level3Combinations = await mappingsAPI.getCombinations(currentLevel1, currentLevel2);
          const level3List = level3Combinations.level_3 || [];
          // Si la valeur actuelle n'est pas dans la liste, c'est une valeur custom
          if (currentLevel3 && !level3List.includes(currentLevel3)) {
            setCustomLevel3(true);
            level3List.push(currentLevel3); // Ajouter quand même pour l'affichage
          }
          setAvailableLevel3(level3List);
        } else {
          // Si level_2 n'existe pas mais level_1 existe, charger TOUS les level_3 disponibles
          const allLevel3Combinations = await mappingsAPI.getCombinations(undefined, undefined, false, true);
          const allLevel3List = allLevel3Combinations.level_3 || [];
          setAvailableLevel3(allLevel3List);
        }
      } else {
        // Si level_1 n'existe pas, charger TOUS les level_2 et level_3 disponibles
        const allLevel2Combinations = await mappingsAPI.getCombinations(undefined, undefined, true, false);
        const allLevel2List = allLevel2Combinations.level_2 || [];
        console.log('🔍 [Combinations] All level_2 loaded:', allLevel2List);
        setAvailableLevel2(allLevel2List);
        
        const allLevel3Combinations = await mappingsAPI.getCombinations(undefined, undefined, false, true);
        const allLevel3List = allLevel3Combinations.level_3 || [];
        console.log('🔍 [Combinations] All level_3 loaded:', allLevel3List);
        setAvailableLevel3(allLevel3List);
      }
    } catch (err) {
      console.error('Error loading combinations:', err);
    }
  };

  const handleLevel1Change = async (value: string) => {
    if (value === '__CUSTOM__') {
      setCustomLevel1(true);
      setEditingClassificationValues({ ...editingClassificationValues, level_1: '', level_2: undefined, level_3: undefined });
      // Charger TOUS les level_2 et level_3 disponibles dès qu'on passe en mode custom
      try {
        const allLevel2Combinations = await mappingsAPI.getCombinations(undefined, undefined, true, false);
        const allLevel2List = allLevel2Combinations.level_2 || [];
        console.log('🔍 [Combinations] All level_2 loaded (custom level_1):', allLevel2List);
        setAvailableLevel2(allLevel2List);
        
        const allLevel3Combinations = await mappingsAPI.getCombinations(undefined, undefined, false, true);
        const allLevel3List = allLevel3Combinations.level_3 || [];
        console.log('🔍 [Combinations] All level_3 loaded (custom level_1):', allLevel3List);
        setAvailableLevel3(allLevel3List);
      } catch (err) {
        console.error('Error loading combinations:', err);
      }
      return;
    }
    
    setCustomLevel1(false);
    const currentLevel2 = editingClassificationValues.level_2;
    const currentLevel3 = editingClassificationValues.level_3;
    // Ne pas supprimer level_3, seulement level_2 si on change level_1
    setEditingClassificationValues({ ...editingClassificationValues, level_1: value, level_2: undefined });
    setAvailableLevel2([]);
    
    // Charger les level_2 possibles pour ce level_1
    if (value) {
      try {
        const combinations = await mappingsAPI.getCombinations(value);
        const level2List = combinations.level_2 || [];
        // Ajouter la valeur actuelle si elle n'est pas déjà dans la liste
        if (currentLevel2 && !level2List.includes(currentLevel2)) {
          level2List.push(currentLevel2);
        }
        setAvailableLevel2(level2List);
        
        // Si level_2 n'est pas encore sélectionné, garder TOUS les level_3 disponibles
        // Sinon, filtrer level_3 selon level_1 + level_2
        if (!currentLevel2) {
          const allLevel3Combinations = await mappingsAPI.getCombinations(undefined, undefined, false, true);
          const allLevel3List = allLevel3Combinations.level_3 || [];
          setAvailableLevel3(allLevel3List);
        } else {
          // Filtrer level_3 selon level_1 + level_2
          const level3Combinations = await mappingsAPI.getCombinations(value, currentLevel2);
          const level3List = level3Combinations.level_3 || [];
          // Ajouter la valeur actuelle si elle n'est pas déjà dans la liste
          if (currentLevel3 && !level3List.includes(currentLevel3)) {
            level3List.push(currentLevel3);
          }
          setAvailableLevel3(level3List);
        }
      } catch (err) {
        console.error('Error loading level_2 combinations:', err);
      }
    }
  };

  const handleLevel2Change = async (value: string) => {
    if (value === '__CUSTOM__') {
      setCustomLevel2(true);
      setEditingClassificationValues({ ...editingClassificationValues, level_2: '', level_3: undefined });
      // Charger TOUS les level_3 disponibles dès qu'on passe en mode custom
      try {
        const combinations = await mappingsAPI.getCombinations(undefined, undefined, false, true);
        const level3List = combinations.level_3 || [];
        console.log('🔍 [Combinations] All level_3 loaded (custom level_2):', level3List);
        setAvailableLevel3(level3List);
      } catch (err) {
        console.error('Error loading level_3 combinations:', err);
      }
      return;
    }
    
    setCustomLevel2(false);
    const level_1 = editingClassificationValues.level_1;
    const currentLevel3 = editingClassificationValues.level_3;
    if (!level_1) return;
    
    // Ne pas supprimer level_3, seulement mettre à jour level_2
    setEditingClassificationValues({ ...editingClassificationValues, level_2: value });
    
    // Charger les level_3 possibles pour cette combinaison level_1 + level_2
    if (value) {
      try {
        const combinations = await mappingsAPI.getCombinations(level_1, value);
        const level3List = combinations.level_3 || [];
        // Ajouter la valeur actuelle si elle n'est pas déjà dans la liste
        if (currentLevel3 && !level3List.includes(currentLevel3)) {
          level3List.push(currentLevel3);
        }
        // Si la liste est vide, charger TOUS les level_3 disponibles
        if (level3List.length === 0) {
          const allLevel3Combinations = await mappingsAPI.getCombinations(undefined, undefined, false, true);
          const allLevel3List = allLevel3Combinations.level_3 || [];
          setAvailableLevel3(allLevel3List);
        } else {
          setAvailableLevel3(level3List);
        }
      } catch (err) {
        console.error('Error loading level_3 combinations:', err);
      }
    }
  };

  const handleSaveClassification = async (transaction: Transaction) => {
    try {
      await enrichmentAPI.updateClassifications(
        transaction.id,
        editingClassificationValues.level_1 || null,
        editingClassificationValues.level_2 || null,
        editingClassificationValues.level_3 || null
      );
      setEditingClassificationId(null);
      setEditingClassificationValues({});
      setAvailableLevel1([]);
      setAvailableLevel2([]);
      setAvailableLevel3([]);
      await loadTransactions();
    } catch (err: any) {
      console.error('Error updating classification:', err);
      alert(`Erreur lors de la modification: ${err.message || 'Erreur inconnue'}`);
    }
  };

  const handleCancelClassification = () => {
    setEditingClassificationId(null);
    setEditingClassificationValues({});
    setAvailableLevel1([]);
    setAvailableLevel2([]);
    setAvailableLevel3([]);
    setCustomLevel1(false);
    setCustomLevel2(false);
    setCustomLevel3(false);
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div>
      {/* Filtres et recherche */}
      <div style={{ 
        marginBottom: '24px', 
        padding: '16px', 
        backgroundColor: '#f5f5f5', 
        borderRadius: '8px',
        display: 'flex',
        flexWrap: 'wrap',
        gap: '12px',
        alignItems: 'flex-end'
      }}>
        <div style={{ flex: 1, minWidth: '200px' }}>
          <label style={{ display: 'block', fontSize: '12px', color: '#666', marginBottom: '4px' }}>
            Recherche par nom
          </label>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Rechercher une transaction..."
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              fontSize: '14px',
            }}
          />
        </div>
        <div style={{ minWidth: '150px' }}>
          <label style={{ display: 'block', fontSize: '12px', color: '#666', marginBottom: '4px' }}>
            Date début
          </label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              fontSize: '14px',
            }}
          />
        </div>
        <div style={{ minWidth: '150px' }}>
          <label style={{ display: 'block', fontSize: '12px', color: '#666', marginBottom: '4px' }}>
            Date fin
          </label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              fontSize: '14px',
            }}
          />
        </div>
        <div>
          <button
            onClick={() => {
              setSearchTerm('');
              setStartDate('');
              setEndDate('');
              setPage(1);
            }}
            style={{
              padding: '8px 16px',
              backgroundColor: '#6b7280',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '14px',
              cursor: 'pointer',
            }}
          >
            Réinitialiser
          </button>
        </div>
      </div>

      {/* Statistiques et actions de sélection */}
      <div style={{ 
        marginBottom: '16px', 
        display: 'flex', 
        justifyContent: 'flex-end', 
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        {(searchTerm || startDate || endDate) && (
          <div style={{ fontSize: '14px', color: '#666' }}>
            {searchTerm && `Filtrées par "${searchTerm}"`}
            {(startDate || endDate) && ` (période: ${startDate || 'début'} - ${endDate || 'fin'})`}
          </div>
        )}
        {selectedIds.size > 0 && (
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <span style={{ fontSize: '14px', color: '#1e3a5f', fontWeight: '500' }}>
              {selectedIds.size} transaction{selectedIds.size > 1 ? 's' : ''} sélectionnée{selectedIds.size > 1 ? 's' : ''}
            </span>
            <button
              onClick={handleDeleteMultiple}
              disabled={isDeletingMultiple}
              style={{
                padding: '8px 16px',
                backgroundColor: isDeletingMultiple ? '#ccc' : '#dc3545',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '14px',
                cursor: isDeletingMultiple ? 'not-allowed' : 'pointer',
                opacity: isDeletingMultiple ? 0.6 : 1,
              }}
            >
              {isDeletingMultiple ? '⏳ Suppression...' : `🗑️ Supprimer ${selectedIds.size}`}
            </button>
          </div>
        )}
      </div>

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
            Page {page} sur {totalPages} ({total} transaction{total !== 1 ? 's' : ''})
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
      {isLoading ? (
        <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
          ⏳ Chargement des transactions...
        </div>
      ) : error ? (
        <div style={{ padding: '40px', textAlign: 'center', color: '#dc3545' }}>
          ❌ {error}
        </div>
      ) : (
        <>
          <div style={{ 
            backgroundColor: 'white', 
            borderRadius: '8px', 
            border: '1px solid #e5e5e5',
            overflow: 'auto'
          }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
              <thead>
                <tr style={{ backgroundColor: '#f5f5f5', borderBottom: '2px solid #e5e5e5' }}>
                  <th style={{ 
                    padding: '12px', 
                    textAlign: 'center', 
                    fontWeight: '600', 
                    color: '#1a1a1a',
                    width: '50px'
                  }}>
                    <input
                      type="checkbox"
                      checked={transactions.length > 0 && selectedIds.size === transactions.length}
                      onChange={handleSelectAll}
                      style={{
                        width: '18px',
                        height: '18px',
                        cursor: 'pointer',
                      }}
                    />
                  </th>
                  <th
                    onClick={() => handleSort('date')}
                    style={{
                      padding: '12px',
                      textAlign: 'left',
                      fontWeight: '600',
                      color: '#1a1a1a',
                      cursor: 'pointer',
                      userSelect: 'none',
                    }}
                  >
                    Date {sortColumn === 'date' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    onClick={() => handleSort('quantite')}
                    style={{
                      padding: '12px',
                      textAlign: 'right',
                      fontWeight: '600',
                      color: '#1a1a1a',
                      cursor: 'pointer',
                      userSelect: 'none',
                    }}
                  >
                    Quantité {sortColumn === 'quantite' && (sortDirection === 'asc' ? '↑' : '↓')}
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
                    onClick={() => handleSort('solde')}
                    style={{
                      padding: '12px',
                      textAlign: 'right',
                      fontWeight: '600',
                      color: '#1a1a1a',
                      cursor: 'pointer',
                      userSelect: 'none',
                    }}
                  >
                    Solde {sortColumn === 'solde' && (sortDirection === 'asc' ? '↑' : '↓')}
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
                  <th style={{ padding: '12px', textAlign: 'center', fontWeight: '600', color: '#1a1a1a' }}>
                    Actions
                  </th>
                </tr>
                {/* Ligne de filtres */}
                <tr key="filter-row" style={{ backgroundColor: '#fafafa', borderBottom: '1px solid #e5e5e5' }}>
                  <td style={{ padding: '8px', textAlign: 'center' }}></td>
                  <td style={{ padding: '8px' }}>
                    <input
                      type="date"
                      value={filterDate}
                      onChange={handleFilterDateChange}
                      placeholder="Filtrer..."
                      style={{
                        width: '100%',
                        padding: '4px 8px',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '12px',
                      }}
                    />
                  </td>
                  <td style={{ padding: '8px' }}>
                    <input
                      type="number"
                      value={filterQuantite}
                      onChange={handleFilterQuantiteChange}
                      onKeyDown={handleFilterQuantiteKeyDown}
                      placeholder="Filtrer (Entrée pour valider)..."
                      style={{
                        width: '100%',
                        padding: '4px 8px',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '12px',
                      }}
                    />
                  </td>
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
                    <input
                      type="number"
                      value={filterSolde}
                      onChange={handleFilterSoldeChange}
                      onKeyDown={handleFilterSoldeKeyDown}
                      placeholder="Filtrer (Entrée pour valider)..."
                      style={{
                        width: '100%',
                        padding: '4px 8px',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '12px',
                      }}
                    />
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
                {transactions.length === 0 ? (
                  <tr>
                    <td colSpan={9} style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
                      Aucune transaction trouvée
                    </td>
                  </tr>
                ) : (
                  transactions.map((transaction) => (
                    <tr
                    key={transaction.id}
                    style={{
                      borderBottom: '1px solid #e5e5e5',
                      transition: 'background-color 0.2s',
                      backgroundColor: selectedIds.has(transaction.id) ? '#e3f2fd' : 'white',
                    }}
                    onMouseEnter={(e) => {
                      if (!selectedIds.has(transaction.id)) {
                        e.currentTarget.style.backgroundColor = '#f9f9f9';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!selectedIds.has(transaction.id)) {
                        e.currentTarget.style.backgroundColor = 'white';
                      } else {
                        e.currentTarget.style.backgroundColor = '#e3f2fd';
                      }
                    }}
                  >
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      <input
                        type="checkbox"
                        checked={selectedIds.has(transaction.id)}
                        onChange={() => handleToggleSelect(transaction.id)}
                        style={{
                          width: '18px',
                          height: '18px',
                          cursor: 'pointer',
                        }}
                      />
                    </td>
                    <td style={{ padding: '12px', color: '#1a1a1a' }}>
                      {editingId === transaction.id ? (
                        <input
                          type="date"
                          value={editingValues.date || ''}
                          onChange={(e) => setEditingValues({ ...editingValues, date: e.target.value })}
                          style={{ width: '100%', padding: '4px', border: '1px solid #ddd', borderRadius: '2px' }}
                        />
                      ) : (
                        formatDate(transaction.date)
                      )}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'right', color: transaction.quantite >= 0 ? '#10b981' : '#ef4444' }}>
                      {editingId === transaction.id ? (
                        <input
                          type="number"
                          step="0.01"
                          value={editingValues.quantite !== undefined ? editingValues.quantite : ''}
                          onChange={(e) => setEditingValues({ ...editingValues, quantite: parseFloat(e.target.value) || 0 })}
                          style={{ width: '100%', padding: '4px', border: '1px solid #ddd', borderRadius: '2px', textAlign: 'right' }}
                        />
                      ) : (
                        formatAmount(transaction.quantite)
                      )}
                    </td>
                    <td style={{ padding: '12px', maxWidth: '400px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {editingId === transaction.id ? (
                        <input
                          type="text"
                          value={editingValues.nom !== undefined ? editingValues.nom : ''}
                          onChange={(e) => setEditingValues({ ...editingValues, nom: e.target.value })}
                          style={{ width: '100%', padding: '4px', border: '1px solid #ddd', borderRadius: '2px' }}
                        />
                      ) : (
                        <span style={{ 
                          color: transaction.nom.startsWith('nom_a_justifier_') ? '#dc3545' : '#666',
                          fontWeight: transaction.nom.startsWith('nom_a_justifier_') ? '500' : 'normal',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px'
                        }}>
                          {transaction.nom.startsWith('nom_a_justifier_') && (
                            <span style={{ fontSize: '14px' }}>⚠️</span>
                          )}
                          {transaction.nom}
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'right', color: '#1a1a1a', fontWeight: '500' }}>
                      {formatAmount(transaction.solde)}
                    </td>
                    <td style={{ padding: '12px', color: transaction.level_1 ? '#666' : '#999', fontStyle: transaction.level_1 ? 'normal' : 'italic' }}>
                      {editingClassificationId === transaction.id ? (
                        customLevel1 ? (
                          <input
                            type="text"
                            value={editingClassificationValues.level_1 || ''}
                            onChange={async (e) => {
                              const newValue = e.target.value;
                              setEditingClassificationValues({ ...editingClassificationValues, level_1: newValue, level_2: undefined, level_3: undefined });
                              setAvailableLevel2([]);
                              setAvailableLevel3([]);
                              
                              // Si une valeur est saisie, charger TOUS les level_2 disponibles (car c'est une nouvelle valeur)
                              if (newValue) {
                                try {
                                  const combinations = await mappingsAPI.getCombinations(undefined, undefined, true, false);
                                  const level2List = combinations.level_2 || [];
                                  setAvailableLevel2(level2List);
                                } catch (err) {
                                  console.error('Error loading level_2 combinations:', err);
                                }
                              }
                            }}
                            placeholder="Saisir une valeur..."
                            style={{ width: '100%', padding: '4px', border: '1px solid #ddd', borderRadius: '2px' }}
                          />
                        ) : (
                          <select
                            value={editingClassificationValues.level_1 || ''}
                            onChange={(e) => handleLevel1Change(e.target.value)}
                            style={{ width: '100%', padding: '4px', border: '1px solid #ddd', borderRadius: '2px' }}
                          >
                            <option value="">-- Sélectionner --</option>
                            {availableLevel1.length > 0 ? (
                              availableLevel1.map((val) => (
                                <option key={val} value={val}>{val}</option>
                              ))
                            ) : (
                              <option disabled>Aucune valeur disponible</option>
                            )}
                            <option value="__CUSTOM__">➕ Nouveau...</option>
                          </select>
                        )
                      ) : (
                        <span 
                          onClick={() => handleEditClassification(transaction)}
                          style={{ cursor: 'pointer', textDecoration: 'underline' }}
                        >
                          {transaction.level_1 || 'à remplir'}
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '12px', color: transaction.level_2 ? '#666' : '#999', fontStyle: transaction.level_2 ? 'normal' : 'italic' }}>
                      {editingClassificationId === transaction.id ? (
                        customLevel2 ? (
                          <input
                            type="text"
                            value={editingClassificationValues.level_2 || ''}
                            onChange={async (e) => {
                              const newValue = e.target.value;
                              setEditingClassificationValues({ ...editingClassificationValues, level_2: newValue, level_3: undefined });
                              setAvailableLevel3([]);
                              
                              // Si une valeur est saisie, charger TOUS les level_3 disponibles (car c'est une nouvelle valeur)
                              if (newValue) {
                                try {
                                  const combinations = await mappingsAPI.getCombinations(undefined, undefined, false, true);
                                  const level3List = combinations.level_3 || [];
                                  setAvailableLevel3(level3List);
                                } catch (err) {
                                  console.error('Error loading level_3 combinations:', err);
                                }
                              }
                            }}
                            placeholder="Saisir une valeur..."
                            style={{ 
                              width: '100%', 
                              padding: '4px', 
                              border: '1px solid #ddd', 
                              borderRadius: '2px',
                              backgroundColor: 'white'
                            }}
                          />
                        ) : (
                          <select
                            value={editingClassificationValues.level_2 || ''}
                            onChange={(e) => handleLevel2Change(e.target.value)}
                            disabled={!editingClassificationValues.level_1}
                            style={{ 
                              width: '100%', 
                              padding: '4px', 
                              border: '1px solid #ddd', 
                              borderRadius: '2px',
                              backgroundColor: editingClassificationValues.level_1 ? 'white' : '#f5f5f5'
                            }}
                          >
                            <option value="">-- Sélectionner --</option>
                            {availableLevel2.length > 0 ? (
                              availableLevel2.map((val) => (
                                <option key={val} value={val}>{val}</option>
                              ))
                            ) : (
                              <option disabled>Aucune valeur disponible</option>
                            )}
                            <option value="__CUSTOM__">➕ Nouveau...</option>
                          </select>
                        )
                      ) : (
                        <span 
                          onClick={() => handleEditClassification(transaction)}
                          style={{ cursor: 'pointer', textDecoration: 'underline' }}
                        >
                          {transaction.level_2 || 'à remplir'}
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '12px', color: transaction.level_3 ? '#666' : '#999', fontStyle: transaction.level_3 ? 'normal' : 'italic' }}>
                      {editingClassificationId === transaction.id ? (
                        customLevel3 ? (
                          <input
                            type="text"
                            value={editingClassificationValues.level_3 || ''}
                            onChange={(e) => setEditingClassificationValues({ ...editingClassificationValues, level_3: e.target.value })}
                            placeholder="Saisir une valeur (optionnel)..."
                            style={{ 
                              width: '100%', 
                              padding: '4px', 
                              border: '1px solid #ddd', 
                              borderRadius: '2px',
                              backgroundColor: 'white'
                            }}
                          />
                        ) : (
                          <select
                            value={editingClassificationValues.level_3 || ''}
                            onChange={(e) => {
                              if (e.target.value === '__CUSTOM__') {
                                setCustomLevel3(true);
                                setEditingClassificationValues({ ...editingClassificationValues, level_3: '' });
                              } else {
                                setCustomLevel3(false);
                                setEditingClassificationValues({ ...editingClassificationValues, level_3: e.target.value });
                              }
                            }}
                            disabled={false}
                            style={{ 
                              width: '100%', 
                              padding: '4px', 
                              border: '1px solid #ddd', 
                              borderRadius: '2px',
                              backgroundColor: 'white'
                            }}
                          >
                            <option value="">-- Sélectionner (optionnel) --</option>
                            {availableLevel3.length > 0 ? (
                              availableLevel3.map((val) => (
                                <option key={val} value={val}>{val}</option>
                              ))
                            ) : (
                              <option disabled>Aucune valeur disponible</option>
                            )}
                            <option value="__CUSTOM__">➕ Nouveau...</option>
                          </select>
                        )
                      ) : (
                        <span 
                          onClick={() => handleEditClassification(transaction)}
                          style={{ cursor: 'pointer', textDecoration: 'underline' }}
                        >
                          {transaction.level_3 || 'à remplir'}
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                        {editingId === transaction.id ? (
                          <>
                            <button
                              onClick={() => handleSaveEdit(transaction)}
                              style={{
                                padding: '6px 12px',
                                backgroundColor: '#28a745',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                fontSize: '12px',
                                cursor: 'pointer',
                              }}
                            >
                              ✓
                            </button>
                            <button
                              onClick={handleCancelEdit}
                              style={{
                                padding: '6px 12px',
                                backgroundColor: '#6c757d',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                fontSize: '12px',
                                cursor: 'pointer',
                              }}
                            >
                              ✗
                            </button>
                          </>
                        ) : editingClassificationId === transaction.id ? (
                          <>
                            <button
                              onClick={() => handleSaveClassification(transaction)}
                              style={{
                                padding: '6px 12px',
                                backgroundColor: '#28a745',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                fontSize: '12px',
                                cursor: 'pointer',
                              }}
                            >
                              ✓
                            </button>
                            <button
                              onClick={handleCancelClassification}
                              style={{
                                padding: '6px 12px',
                                backgroundColor: '#6c757d',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                fontSize: '12px',
                                cursor: 'pointer',
                              }}
                            >
                              ✗
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              onClick={() => handleEdit(transaction)}
                              style={{
                                padding: '6px 12px',
                                backgroundColor: '#1e3a5f',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                fontSize: '12px',
                                cursor: 'pointer',
                              }}
                            >
                              ✏️
                            </button>
                            <button
                              onClick={() => handleDelete(transaction.id)}
                              disabled={deletingId === transaction.id}
                              style={{
                                padding: '6px 12px',
                                backgroundColor: deletingId === transaction.id ? '#ccc' : '#dc3545',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                fontSize: '12px',
                                cursor: deletingId === transaction.id ? 'not-allowed' : 'pointer',
                                opacity: deletingId === transaction.id ? 0.6 : 1,
                              }}
                            >
                              {deletingId === transaction.id ? '⏳' : '🗑️'}
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div style={{ 
              marginTop: '24px', 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '12px'
            }}>
              <div style={{ fontSize: '14px', color: '#666' }}>
                Page {page} sur {totalPages} ({total} transaction{total !== 1 ? 's' : ''})
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
        </>
      )}

    </div>
  );
}

