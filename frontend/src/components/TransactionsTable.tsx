/**
 * TransactionsTable component - Tableau des transactions avec tri, pagination et suppression
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { transactionsAPI, Transaction, TransactionUpdate, enrichmentAPI, mappingsAPI, allowedMappingsAPI } from '@/api/client';
import { exportAndDownloadTransactions, generateTransactionsFilename } from '@/utils/excelExport';

interface TransactionsTableProps {
  onDelete?: () => void;
  unclassifiedOnly?: boolean; // Si true, affiche uniquement les transactions non classées
  onUpdate?: () => void; // Callback appelé après mise à jour d'une transaction (pour rafraîchir Mapping)
}

type SortColumn = 'date' | 'quantite' | 'nom' | 'solde' | 'level_1' | 'level_2' | 'level_3';
type SortDirection = 'asc' | 'desc';

export default function TransactionsTable({ onDelete, unclassifiedOnly = false, onUpdate }: TransactionsTableProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [sortColumn, setSortColumn] = useState<SortColumn>('date');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingValues, setEditingValues] = useState<{ date?: string; nom?: string; quantite?: number }>({});
  const [editingClassificationId, setEditingClassificationId] = useState<number | null>(null);
  const [editingClassificationValues, setEditingClassificationValues] = useState<{ level_1?: string; level_2?: string; level_3?: string }>({});
  const [availableLevel1, setAvailableLevel1] = useState<string[]>([]);
  const [availableLevel2, setAvailableLevel2] = useState<string[]>([]);
  const [availableLevel3, setAvailableLevel3] = useState<string[]>([]);
  
  // Debug: Log quand les valeurs changent
  useEffect(() => {
    console.log('🔄 [TransactionsTable] availableLevel2 changed:', availableLevel2.length, availableLevel2);
  }, [availableLevel2]);
  
  useEffect(() => {
    console.log('🔄 [TransactionsTable] availableLevel3 changed:', availableLevel3.length, availableLevel3);
  }, [availableLevel3]);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [isDeletingMultiple, setIsDeletingMultiple] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  
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
      
      // Note: Les filtres quantité et solde utilisent un filtre "contient" (ex: "14" trouve 14, 14.02, 140, etc.)
      // Le backend ne supporte pas encore ce type de filtre pour les nombres, donc on les garde côté client
      // Pour l'instant, on ne passe pas ces filtres à l'API
      
      // Appel API avec tri et filtres côté serveur (texte uniquement)
      const response = await transactionsAPI.getAll(
        skip,
        pageSize,
        undefined, // startDate (supprimé)
        undefined, // endDate (supprimé)
        sortColumn, // Passer le tri à l'API
        sortDirection,
        unclassifiedOnly, // Passer le filtre non classées
        appliedFilterNom || undefined, // Filtre nom
        appliedFilterLevel1 || undefined, // Filtre level_1
        appliedFilterLevel2 || undefined, // Filtre level_2
        appliedFilterLevel3 || undefined, // Filtre level_3
        undefined, // Filtre quantité min (non utilisé pour filtre "contient")
        undefined, // Filtre quantité max (non utilisé pour filtre "contient")
        undefined, // Filtre solde min (non utilisé pour filtre "contient")
        undefined // Filtre solde max (non utilisé pour filtre "contient")
      );
      
      // L'API fait déjà le filtrage, on utilise directement les résultats
      setRawTransactions(response.transactions);
      setTotal(response.total);
    } catch (err) {
      console.error('Error loading transactions:', err);
      setError(err instanceof Error ? err.message : 'Erreur lors du chargement');
    } finally {
      setIsLoading(false);
    }
  };

  // Réinitialiser la page à 1 quand les filtres changent
  useEffect(() => {
    if (appliedFilterDate || appliedFilterNom || appliedFilterLevel1 || appliedFilterLevel2 || appliedFilterLevel3 || appliedFilterQuantite || appliedFilterSolde) {
      setPage(1);
    }
  }, [appliedFilterDate, appliedFilterNom, appliedFilterLevel1, appliedFilterLevel2, appliedFilterLevel3, appliedFilterQuantite, appliedFilterSolde]);

  // Recharger depuis l'API quand page, tri, date range ou filtres changent
  useEffect(() => {
    loadTransactions();
  }, [page, pageSize, sortColumn, sortDirection, appliedFilterNom, appliedFilterLevel1, appliedFilterLevel2, appliedFilterLevel3, appliedFilterQuantite, appliedFilterSolde]);

  // L'API fait déjà le filtrage pour les filtres texte (nom, level_1/2/3)
  // On doit encore filtrer localement pour date, quantité et solde (non supportés côté serveur)
  const transactions = useMemo(() => {
    let filtered = [...rawTransactions];
    
    // Filtrer par date (filtre exact)
    if (appliedFilterDate) {
      const filterDateObj = new Date(appliedFilterDate);
      filtered = filtered.filter(t => {
        const tDate = new Date(t.date);
        return tDate.toDateString() === filterDateObj.toDateString();
      });
    }
    
    // Filtrer par quantité avec filtre "contient" (si on tape "14", trouve 14, 14.02, 140, 14000, etc.)
    if (appliedFilterQuantite && appliedFilterQuantite.trim() !== '') {
      const filterValue = appliedFilterQuantite.trim();
      if (filterValue !== '' && !isNaN(Number(filterValue))) {
        filtered = filtered.filter(t => {
          const quantiteStr = t.quantite.toString();
          return quantiteStr.includes(filterValue);
        });
      }
    }
    // Filtrer par solde avec filtre "contient" (si on tape "14", trouve 14, 14.02, 140, 14000, etc.)
    if (appliedFilterSolde && appliedFilterSolde.trim() !== '') {
      const filterValue = appliedFilterSolde.trim();
      if (filterValue !== '' && !isNaN(Number(filterValue))) {
        filtered = filtered.filter(t => {
          const soldeStr = t.solde.toString();
          return soldeStr.includes(filterValue);
        });
      }
    }
    
    return filtered;
  }, [rawTransactions, appliedFilterDate, appliedFilterQuantite, appliedFilterSolde]);

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
          transactionsAPI.getUniqueValues('nom'),
          transactionsAPI.getUniqueValues('level_1'),
          transactionsAPI.getUniqueValues('level_2'),
          transactionsAPI.getUniqueValues('level_3'),
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

  const handleExportTransactions = async () => {
    setIsExporting(true);
    try {
      // Récupérer toutes les transactions (sans filtres)
      const allTransactions = await transactionsAPI.getAllForExport();
      
      if (allTransactions.length === 0) {
        alert('Aucune transaction à exporter.');
        setIsExporting(false);
        return;
      }
      
      // Générer le nom de fichier avec la date
      const filename = generateTransactionsFilename();
      
      // Exporter et ouvrir le dialogue de sauvegarde
      await exportAndDownloadTransactions(allTransactions, filename);
      
      // Message de succès
      alert(`✅ Export réussi !\n\n${allTransactions.length} transaction${allTransactions.length > 1 ? 's' : ''} exportée${allTransactions.length > 1 ? 's' : ''} vers ${filename}`);
    } catch (err: any) {
      // Ne pas afficher d'erreur si l'utilisateur a annulé
      if (err.message && err.message.includes('annulé')) {
        // L'utilisateur a annulé, ne rien faire
        return;
      }
      alert(`❌ Erreur lors de l'export: ${err.message}`);
      console.error('Erreur export transactions:', err);
    } finally {
      setIsExporting(false);
    }
  };

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
    
    // Step 8.4: Charger les valeurs autorisées depuis allowed_mappings avec filtrage bidirectionnel
    try {
      // Charger toutes les valeurs level_1 autorisées
      const level1List = await allowedMappingsAPI.getAllowedLevel1();
      setAvailableLevel1(level1List);
      
      // Charger toutes les valeurs level_2 disponibles (pour le Scénario 2)
      const allLevel2List = await allowedMappingsAPI.getAllowedLevel2();
      console.log('✅ [TransactionsTable] Toutes les valeurs level_2 chargées:', allLevel2List.length, allLevel2List);
      setAvailableLevel2(allLevel2List);
      
      // Charger toutes les valeurs level_3 disponibles (pour le Scénario 3)
      const allLevel3List = await allowedMappingsAPI.getAllowedLevel3();
      console.log('✅ [TransactionsTable] Toutes les valeurs level_3 chargées:', allLevel3List.length, allLevel3List);
      setAvailableLevel3(allLevel3List);
      
      // Déterminer quelle valeur est disponible pour charger les autres
      if (currentLevel1) {
        // Scénario 1 : level_1 existe → charger level_2 filtrés pour ce level_1 (mais garder toutes les valeurs pour le dropdown)
        console.log('🔍 [TransactionsTable] Chargement level_2 pour level_1:', currentLevel1);
        const level2List = await allowedMappingsAPI.getAllowedLevel2(currentLevel1);
        console.log('✅ [TransactionsTable] Level_2 disponibles pour', currentLevel1, ':', level2List.length, 'valeurs');
        // Ne pas écraser allLevel2List, garder toutes les valeurs pour permettre le Scénario 2
        // setAvailableLevel2(level2List);
        
        // Ne pas écraser allLevel3List, garder toutes les valeurs pour permettre le Scénario 3
        // setAvailableLevel3 reste avec allLevel3List (déjà chargé plus haut)
      } else if (currentLevel2) {
        // Scénario 2 : level_2 existe (sans level_1) → charger level_1, garder toutes les valeurs level_3
        const level1List = await allowedMappingsAPI.getAllowedLevel1ForLevel2(currentLevel2);
        setAvailableLevel1(level1List);
        // setAvailableLevel3 reste avec allLevel3List (déjà chargé plus haut)
      } else if (currentLevel3) {
        // Scénario 3 : level_3 existe (sans level_1 ni level_2) → charger level_2 puis level_1
        const level2List = await allowedMappingsAPI.getAllowedLevel2ForLevel3(currentLevel3);
        setAvailableLevel2(level2List);
        
        if (level2List.length > 0) {
          const level1List = await allowedMappingsAPI.getAllowedLevel1ForLevel2AndLevel3(level2List[0], currentLevel3);
          setAvailableLevel1(level1List);
        } else {
          setAvailableLevel1([]);
        }
        // Garder toutes les valeurs level_3 disponibles (déjà chargé plus haut)
        // setAvailableLevel3 reste avec allLevel3List
      } else {
        // Aucune valeur → garder toutes les valeurs level_2 et level_3 chargées (pour permettre les Scénarios 2 et 3)
        // setAvailableLevel2 reste avec allLevel2List (déjà chargé plus haut)
        // setAvailableLevel3 reste avec allLevel3List (déjà chargé plus haut)
        console.log('🔍 [TransactionsTable] Aucune valeur sélectionnée, level_1 disponibles:', level1List.length, 'level_2 disponibles:', allLevel2List.length, 'level_3 disponibles:', allLevel3List.length);
      }
    } catch (err) {
      console.error('Error loading allowed mappings:', err);
      setAvailableLevel1([]);
      setAvailableLevel2([]);
      setAvailableLevel3([]);
    }
  };

  const handleLevel1Change = async (value: string) => {
    // Scénario 1 : Sélection de level_1 → level_2 et level_3 sélectionnés automatiquement
    if (!value) {
      // Level_1 vidé → réinitialiser tout
      setEditingClassificationValues({ 
        ...editingClassificationValues, 
        level_1: undefined,
        level_2: undefined,
        level_3: undefined
      });
      setAvailableLevel2([]);
      setAvailableLevel3([]);
      return;
    }

    try {
      // 1. Récupérer la combinaison unique (level_2, level_3) pour ce level_1
      const combination = await allowedMappingsAPI.getUniqueCombinationForLevel1(value);
      
      if (!combination || !combination.level_2) {
        console.error('❌ Pas de combinaison unique trouvée pour level_1:', value);
        setEditingClassificationValues({ 
          ...editingClassificationValues, 
          level_1: value,
          level_2: undefined,
          level_3: undefined
        });
        setAvailableLevel2([]);
        setAvailableLevel3([]);
        return;
      }

      // 2. Sélectionner automatiquement level_2 et level_3
      const newLevel2 = combination.level_2;
      const newLevel3 = combination.level_3 || undefined;

      setEditingClassificationValues({ 
        ...editingClassificationValues, 
        level_1: value,
        level_2: newLevel2,
        level_3: newLevel3
      });

      // 3. Charger les listes disponibles pour les dropdowns (au cas où l'utilisateur voudrait changer)
      const level2List = await allowedMappingsAPI.getAllowedLevel2(value);
      setAvailableLevel2(level2List);

      if (newLevel2) {
        const level3List = await allowedMappingsAPI.getAllowedLevel3(value, newLevel2);
        setAvailableLevel3(level3List);
      } else {
        setAvailableLevel3([]);
      }

      console.log('✅ Scénario 1 - level_1 sélectionné:', value, '→ level_2:', newLevel2, 'level_3:', newLevel3);
    } catch (err) {
      console.error('❌ Erreur lors de la sélection automatique:', err);
      setEditingClassificationValues({ 
        ...editingClassificationValues, 
        level_1: value,
        level_2: undefined,
        level_3: undefined
      });
      setAvailableLevel2([]);
      setAvailableLevel3([]);
    }
  };

  const handleLevel2Change = async (value: string) => {
    // Scénario 2 : Sélection de level_2 → level_3 sélectionné automatiquement, level_1 à sélectionner
    if (!value) {
      // Level_2 vidé → réinitialiser level_3, garder level_1
      setEditingClassificationValues({ 
        ...editingClassificationValues, 
        level_2: undefined,
        level_3: undefined
      });
      setAvailableLevel3([]);
      // Recharger toutes les valeurs level_1
      const allLevel1List = await allowedMappingsAPI.getAllowedLevel1();
      setAvailableLevel1(allLevel1List);
      return;
    }

    try {
      // Vérifier si level_3 est déjà sélectionné (Scénario 3)
      const existingLevel3 = editingClassificationValues.level_3;
      
      if (existingLevel3) {
        // Scénario 3 : level_3 est déjà sélectionné → vérifier que level_2 est valide pour ce level_3
        const validLevel2List = await allowedMappingsAPI.getAllowedLevel2ForLevel3(existingLevel3);
        if (!validLevel2List.includes(value)) {
          // Le level_2 sélectionné n'est pas valide pour le level_3 → réinitialiser level_3
          console.warn('⚠️ [TransactionsTable] Level_2', value, 'n\'est pas valide pour level_3', existingLevel3);
          setEditingClassificationValues({ 
            ...editingClassificationValues, 
            level_2: value,
            level_3: undefined
          });
          // Recharger toutes les valeurs level_3
          const allLevel3List = await allowedMappingsAPI.getAllowedLevel3();
          setAvailableLevel3(allLevel3List);
        } else {
          // Le level_2 est valide → garder level_3
          setEditingClassificationValues({ 
            ...editingClassificationValues, 
            level_2: value
          });
        }
      } else {
        // Scénario 2 : level_3 n'est pas sélectionné → sélectionner automatiquement level_3
        // 1. Récupérer la combinaison unique (level_1, level_3) pour ce level_2
        const combination = await allowedMappingsAPI.getUniqueCombinationForLevel2(value);
        console.log('🔍 [TransactionsTable] Combinaison unique pour level_2', value, ':', combination);
        
        if (!combination || !combination.level_3) {
          console.error('❌ Pas de combinaison unique trouvée pour level_2:', value);
          setEditingClassificationValues({ 
            ...editingClassificationValues, 
            level_2: value,
            level_3: undefined
          });
          setAvailableLevel3([]);
          return;
        }

        // 2. Sélectionner automatiquement level_3
        const newLevel3 = combination.level_3;
        console.log('✅ [TransactionsTable] Sélection automatique de level_3:', newLevel3);

        setEditingClassificationValues({ 
          ...editingClassificationValues, 
          level_2: value,
          level_3: newLevel3
        });
      }

      // 3. Filtrer le dropdown level_1 : afficher uniquement les level_1 qui correspondent à ce level_2
      // Si level_3 existe déjà, filtrer aussi par level_3
      const currentLevel3 = editingClassificationValues.level_3;
      let level1List: string[] = [];
      if (currentLevel3) {
        // Si level_3 existe, filtrer level_1 par le couple (level_2, level_3)
        level1List = await allowedMappingsAPI.getAllowedLevel1ForLevel2AndLevel3(value, currentLevel3);
        console.log('✅ [TransactionsTable] Level_1 filtrés pour level_2/level_3', value, '/', currentLevel3, ':', level1List.length, 'valeurs', level1List);
      } else {
        // Si level_3 n'existe pas, filtrer level_1 uniquement par level_2
        level1List = await allowedMappingsAPI.getAllowedLevel1ForLevel2(value);
        console.log('✅ [TransactionsTable] Level_1 filtrés pour level_2', value, ':', level1List.length, 'valeurs', level1List);
      }
      setAvailableLevel1(level1List);

      // 4. Charger les level_3 disponibles pour les dropdowns (au cas où l'utilisateur voudrait changer)
      if (currentLevel3) {
        // Si level_3 existe déjà, garder toutes les valeurs level_3 disponibles
        const allLevel3List = await allowedMappingsAPI.getAllowedLevel3();
        setAvailableLevel3(allLevel3List);
      } else {
        // Si level_3 n'existe pas, charger les level_3 pour le couple (level_1, level_2) si possible
        if (editingClassificationValues.level_1) {
          const level3List = await allowedMappingsAPI.getAllowedLevel3(editingClassificationValues.level_1, value);
          setAvailableLevel3(level3List);
        } else {
          // Garder toutes les valeurs level_3 disponibles
          const allLevel3List = await allowedMappingsAPI.getAllowedLevel3();
          setAvailableLevel3(allLevel3List);
        }
      }

      const finalLevel3 = editingClassificationValues.level_3;
      console.log('✅ Scénario 2 - level_2 sélectionné:', value, '→ level_3:', finalLevel3, 'level_1 disponibles:', level1List.length);
    } catch (err) {
      console.error('❌ Erreur lors de la sélection automatique de level_3:', err);
      setEditingClassificationValues({ 
        ...editingClassificationValues, 
        level_2: value,
        level_3: undefined
      });
      setAvailableLevel3([]);
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
      // Appeler le callback pour rafraîchir Mapping
      if (onUpdate) {
        onUpdate();
      }
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
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div>
      {/* Statistiques et actions de sélection */}
      <div style={{ 
        marginBottom: '16px', 
        display: 'flex', 
        justifyContent: 'flex-end', 
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
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
      {totalPages >= 1 && (
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
            <button
              onClick={handleExportTransactions}
              disabled={isExporting}
              style={{
                padding: '8px 12px',
                backgroundColor: isExporting ? '#ccc' : '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '14px',
                cursor: isExporting ? 'not-allowed' : 'pointer',
                opacity: isExporting ? 0.6 : 1,
                marginLeft: '8px',
              }}
              title="Exporter toutes les transactions vers un fichier Excel (.xlsx)"
            >
              {isExporting ? '⏳ Export...' : '📥 Extraire transactions'}
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
                        <select
                          value={editingClassificationValues.level_1 || ''}
                          onChange={(e) => handleLevel1Change(e.target.value)}
                          disabled={false}
                          style={{ 
                            width: '100%', 
                            padding: '4px', 
                            border: '1px solid #ddd', 
                            borderRadius: '2px',
                            backgroundColor: 'white'
                          }}
                        >
                          <option value="">Unassigned</option>
                          {availableLevel1.length > 0 ? (
                            availableLevel1.map((val) => (
                              <option key={val} value={val}>{val}</option>
                            ))
                          ) : (
                            <option disabled>Aucune valeur disponible</option>
                          )}
                        </select>
                      ) : (
                        <span 
                          onClick={() => handleEditClassification(transaction)}
                          style={{ cursor: 'pointer', textDecoration: 'underline' }}
                        >
                          {transaction.level_1 || 'unassigned'}
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '12px', color: transaction.level_2 ? '#666' : '#999', fontStyle: transaction.level_2 ? 'normal' : 'italic' }}>
                      {editingClassificationId === transaction.id ? (
                        <select
                          value={editingClassificationValues.level_2 || ''}
                          onChange={(e) => handleLevel2Change(e.target.value)}
                          disabled={false}
                          style={{ 
                            width: '100%', 
                            padding: '4px', 
                            border: '1px solid #ddd', 
                            borderRadius: '2px',
                            backgroundColor: 'white'
                          }}
                        >
                          <option value="">Unassigned</option>
                          {(() => {
                            console.log('🔍 [TransactionsTable] Render - availableLevel2:', availableLevel2.length, availableLevel2);
                            return null;
                          })()}
                          {availableLevel2.length > 0 ? (
                            availableLevel2.map((val) => (
                              <option key={val} value={val}>{val}</option>
                            ))
                          ) : (
                            <option disabled>Aucune valeur disponible ({availableLevel2.length})</option>
                          )}
                        </select>
                      ) : (
                        <span 
                          onClick={() => handleEditClassification(transaction)}
                          style={{ cursor: 'pointer', textDecoration: 'underline' }}
                        >
                          {transaction.level_2 || 'unassigned'}
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '12px', color: transaction.level_3 ? '#666' : '#999', fontStyle: transaction.level_3 ? 'normal' : 'italic' }}>
                      {editingClassificationId === transaction.id ? (
                        <select
                          value={editingClassificationValues.level_3 || ''}
                          onChange={async (e) => {
                            const value = e.target.value || undefined;
                            // Scénario 3 : Sélection de level_3 → level_2 et level_1 à sélectionner
                            if (!value) {
                              // Level_3 vidé → réinitialiser level_2 et level_1, recharger toutes les valeurs
                              setEditingClassificationValues({ 
                                ...editingClassificationValues, 
                                level_2: undefined,
                                level_3: undefined
                              });
                              // Recharger toutes les valeurs level_2 et level_1
                              const allLevel2List = await allowedMappingsAPI.getAllowedLevel2();
                              setAvailableLevel2(allLevel2List);
                              const allLevel1List = await allowedMappingsAPI.getAllowedLevel1();
                              setAvailableLevel1(allLevel1List);
                              return;
                            }

                            try {
                              // 1. Filtrer le dropdown level_2 : afficher uniquement les level_2 qui correspondent à ce level_3
                              const level2List = await allowedMappingsAPI.getAllowedLevel2ForLevel3(value);
                              console.log('✅ [TransactionsTable] Level_2 filtrés pour level_3', value, ':', level2List.length, 'valeurs', level2List);
                              setAvailableLevel2(level2List);

                              // 2. Si level_2 existe déjà, vérifier qu'il est toujours valide pour ce level_3
                              if (editingClassificationValues.level_2) {
                                if (!level2List.includes(editingClassificationValues.level_2)) {
                                  // Le level_2 actuel n'est pas valide pour ce level_3 → le réinitialiser
                                  setEditingClassificationValues({ 
                                    ...editingClassificationValues, 
                                    level_2: undefined,
                                    level_3: value
                                  });
                                  // Charger toutes les valeurs level_1 disponibles
                                  const allLevel1List = await allowedMappingsAPI.getAllowedLevel1();
                                  setAvailableLevel1(allLevel1List);
                                } else {
                                  // Le level_2 actuel est valide → filtrer level_1 par le couple (level_2, level_3)
                                  const level1List = await allowedMappingsAPI.getAllowedLevel1ForLevel2AndLevel3(
                                    editingClassificationValues.level_2,
                                    value
                                  );
                                  console.log('✅ [TransactionsTable] Level_1 filtrés pour level_2/level_3', editingClassificationValues.level_2, '/', value, ':', level1List.length, 'valeurs', level1List);
                                  setAvailableLevel1(level1List);
                                  setEditingClassificationValues({ 
                                    ...editingClassificationValues, 
                                    level_3: value
                                  });
                                }
                              } else {
                                // Si level_2 n'existe pas, garder toutes les valeurs level_1 disponibles
                                // (l'utilisateur devra sélectionner level_2 d'abord)
                                const allLevel1List = await allowedMappingsAPI.getAllowedLevel1();
                                setAvailableLevel1(allLevel1List);
                                setEditingClassificationValues({ 
                                  ...editingClassificationValues, 
                                  level_3: value
                                });
                              }

                              // 3. Garder toutes les valeurs level_3 disponibles pour les dropdowns
                              const allLevel3List = await allowedMappingsAPI.getAllowedLevel3();
                              setAvailableLevel3(allLevel3List);

                              console.log('✅ Scénario 3 - level_3 sélectionné:', value, '→ level_2 filtrés:', level2List.length);
                            } catch (err) {
                              console.error('❌ Erreur lors de la sélection de level_3:', err);
                              setEditingClassificationValues({ 
                                ...editingClassificationValues, 
                                level_3: value
                              });
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
                          <option value="">Unassigned</option>
                          {(() => {
                            console.log('🔍 [TransactionsTable] Render - availableLevel3:', availableLevel3.length, availableLevel3);
                            return null;
                          })()}
                          {availableLevel3.length > 0 ? (
                            availableLevel3.map((val) => (
                              <option key={val} value={val}>{val}</option>
                            ))
                          ) : (
                            <option disabled>Aucune valeur disponible ({availableLevel3.length})</option>
                          )}
                        </select>
                      ) : (
                        <span 
                          onClick={() => handleEditClassification(transaction)}
                          style={{ cursor: 'pointer', textDecoration: 'underline' }}
                        >
                          {transaction.level_3 || 'unassigned'}
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
          {totalPages >= 1 && (
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
                <button
                  onClick={handleExportTransactions}
                  disabled={isExporting}
                  style={{
                    padding: '8px 12px',
                    backgroundColor: isExporting ? '#ccc' : '#007bff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    fontSize: '14px',
                    cursor: isExporting ? 'not-allowed' : 'pointer',
                    opacity: isExporting ? 0.6 : 1,
                    marginLeft: '8px',
                  }}
                  title="Exporter toutes les transactions vers un fichier Excel (.xlsx)"
                >
                  {isExporting ? '⏳ Export...' : '📥 Extraire transactions'}
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

