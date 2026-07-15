/**
 * TransactionsTable component - Tableau des transactions avec tri, pagination et suppression
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect, useMemo, useCallback, Fragment } from 'react';
import { transactionsAPI, Transaction, TransactionUpdate } from '@/api/client';
import { useProperty } from '@/contexts/PropertyContext';
import CategorySelector from '@/components/CategorySelector';

interface TransactionsTableProps {
  onDelete?: () => void;
  unclassifiedOnly?: boolean; // Si true, affiche uniquement les transactions non classées
  onUpdate?: () => void; // Callback appelé après mise à jour d'une transaction (pour rafraîchir Mapping)
}

type SortColumn = 'date' | 'quantite' | 'nom' | 'solde' | 'level_1' | 'level_2' | 'level_3';
type SortDirection = 'asc' | 'desc';

export default function TransactionsTable({ onDelete, unclassifiedOnly = false, onUpdate }: TransactionsTableProps) {
  const { activeProperty } = useProperty();
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
  // Étape 3 (cutover Task C2) : la classification se fait désormais via une unique
  // sélection de catégorie du référentiel (CategorySelector), au lieu des 3 dropdowns
  // en cascade level_1/2/3 sur allowed_mappings.
  const [editingCategoryId, setEditingCategoryId] = useState<number | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [isDeletingMultiple, setIsDeletingMultiple] = useState(false);

  // Étape 4 : saisie manuelle (créer / éclater / écriture croisée)
  const [manualError, setManualError] = useState<string | null>(null);

  const [showAddForm, setShowAddForm] = useState(false);
  const [addDate, setAddDate] = useState('');
  const [addQuantite, setAddQuantite] = useState('');
  const [addNom, setAddNom] = useState('');
  const [addCategoryId, setAddCategoryId] = useState<number | null>(null);
  const [addSubmitting, setAddSubmitting] = useState(false);

  const [showCrossEntryForm, setShowCrossEntryForm] = useState(false);
  const [crossDate, setCrossDate] = useState('');
  const [crossMontant, setCrossMontant] = useState('');
  const [crossDebitNom, setCrossDebitNom] = useState('');
  const [crossDebitCategoryId, setCrossDebitCategoryId] = useState<number | null>(null);
  const [crossCreditNom, setCrossCreditNom] = useState('');
  const [crossCreditCategoryId, setCrossCreditCategoryId] = useState<number | null>(null);
  const [crossSubmitting, setCrossSubmitting] = useState(false);

  const [splittingId, setSplittingId] = useState<number | null>(null);
  const [splitParts, setSplitParts] = useState<{ quantite: string; nom: string; category_id: number | null }[]>([]);
  const [splitSubmitting, setSplitSubmitting] = useState(false);

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
  const [isExporting, setIsExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const loadTransactions = async () => {
    console.log('[TransactionsTable] loadTransactions - activeProperty:', activeProperty);
    console.log('[TransactionsTable] loadTransactions - activeProperty?.id:', activeProperty?.id);
    
    if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
      console.warn('[TransactionsTable] loadTransactions - PROPERTY INVALIDE:', {
        activeProperty,
        id: activeProperty?.id,
        reason: !activeProperty ? 'activeProperty is null/undefined' : 
                !activeProperty.id ? 'activeProperty.id is null/undefined' : 
                'activeProperty.id <= 0'
      });
      setError('Aucune propriété sélectionnée');
      setRawTransactions([]);
      setTotal(0);
      setIsLoading(false);
      return;
    }
    
    console.log('[TransactionsTable] loadTransactions - Appel API avec property_id:', activeProperty.id, 'page:', page);
    setIsLoading(true);
    setError(null);
    try {
      const skip = (page - 1) * pageSize;
      
      // Note: Les filtres quantité et solde utilisent un filtre "contient" (ex: "14" trouve 14, 14.02, 140, etc.)
      // Le backend ne supporte pas encore ce type de filtre pour les nombres, donc on les garde côté client
      // Pour l'instant, on ne passe pas ces filtres à l'API
      
      // Appel API avec tri et filtres côté serveur (texte uniquement) - AJOUTER PROPERTY_ID
      const response = await transactionsAPI.getAll(
        activeProperty.id,
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

  // Recharger depuis l'API quand page, tri, date range, filtres ou propriété changent
  useEffect(() => {
    console.log('[TransactionsTable] useEffect déclenché - activeProperty:', activeProperty);
    console.log('[TransactionsTable] useEffect - activeProperty?.id:', activeProperty?.id);
    console.log('[TransactionsTable] useEffect - Dépendances:', { 
      page, 
      pageSize, 
      sortColumn, 
      sortDirection, 
      activePropertyId: activeProperty?.id 
    });
    
    if (activeProperty && activeProperty.id && activeProperty.id > 0) {
      console.log('[TransactionsTable] useEffect - ✅ Property valide, chargement des transactions');
      loadTransactions();
      // Réinitialiser la page à 1 quand la propriété change
      setPage(1);
    } else {
      console.warn('[TransactionsTable] useEffect - ❌ PROPERTY INVALIDE, vidage des transactions:', {
        activeProperty,
        id: activeProperty?.id,
        type: typeof activeProperty?.id,
        reason: !activeProperty ? 'activeProperty is null/undefined' : 
                !activeProperty.id ? 'activeProperty.id is null/undefined' : 
                activeProperty.id <= 0 ? `activeProperty.id (${activeProperty.id}) <= 0` : 
                'unknown'
      });
      // Pas de propriété sélectionnée, vider les transactions
      setRawTransactions([]);
      setTotal(0);
      setError('Aucune propriété sélectionnée');
      setIsLoading(false);
    }
  }, [page, pageSize, sortColumn, sortDirection, appliedFilterNom, appliedFilterLevel1, appliedFilterLevel2, appliedFilterLevel3, appliedFilterQuantite, appliedFilterSolde, activeProperty?.id]);

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

  // Charger les valeurs uniques pour les filtres
  useEffect(() => {
    if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) return;
    
    const loadUniqueValues = async () => {
      try {
        const [noms, level1s, level2s, level3s] = await Promise.all([
        transactionsAPI.getUniqueValues(activeProperty.id, 'nom'),
        transactionsAPI.getUniqueValues(activeProperty.id, 'level_1'),
        transactionsAPI.getUniqueValues(activeProperty.id, 'level_2'),
        transactionsAPI.getUniqueValues(activeProperty.id, 'level_3'),
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
  }, [activeProperty?.id]);

  const handleSort = useCallback((column: SortColumn) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  }, [sortColumn, sortDirection]);

  // Helper function to download a blob as a file
  const downloadBlob = useCallback((blob: Blob, filename: string) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }, []);

  const handleExport = useCallback(async (format: 'excel' | 'csv') => {
    if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
      setExportError('Aucune propriété sélectionnée');
      return;
    }
    
    setIsExporting(true);
    setExportError(null);
    try {
      // Le filtre de date dans TransactionsTable est une date unique (YYYY-MM-DD)
      // On l'utilise comme start_date et end_date pour filtrer uniquement cette date
      let startDate: string | undefined;
      let endDate: string | undefined;
      if (appliedFilterDate) {
        // Si c'est une date unique, utiliser la même date pour start et end
        startDate = appliedFilterDate;
        endDate = appliedFilterDate;
      }

      const blob = await transactionsAPI.export(
        activeProperty.id,
        format,
        startDate,
        endDate,
        appliedFilterLevel1 || undefined,
        appliedFilterLevel2 || undefined,
        appliedFilterLevel3 || undefined,
        appliedFilterNom || undefined
      );
      const extension = format === 'excel' ? 'xlsx' : 'csv';
      const today = new Date().toISOString().split('T')[0];
      const filename = `transactions_${today}.${extension}`;
      downloadBlob(blob, filename);
    } catch (error) {
      console.error('Erreur lors de l\'export des transactions:', error);
      setExportError(error instanceof Error ? error.message : 'Erreur lors de l\'export');
    } finally {
      setIsExporting(false);
    }
  }, [appliedFilterDate, appliedFilterLevel1, appliedFilterLevel2, appliedFilterLevel3, appliedFilterNom, downloadBlob]);

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
    if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
      alert('Aucune propriété sélectionnée');
      return;
    }
    
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette transaction ?')) {
      return;
    }

    setDeletingId(id);
    try {
      await transactionsAPI.delete(id, activeProperty.id);
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
    if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
      alert('Aucune propriété sélectionnée');
      return;
    }
    
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
      const deletePromises = Array.from(selectedIds).map(id => transactionsAPI.delete(id, activeProperty.id));
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
        if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
          alert('Aucune propriété sélectionnée');
          return;
        }
        
        await transactionsAPI.update(transaction.id, activeProperty.id, updates);
        setEditingId(null);
        setEditingValues({});
        await loadTransactions();
        if (onDelete) {
          onDelete();
        }
        
        // Émettre un événement global pour notifier les autres pages (ex: Amortissements)
        // que la transaction a été modifiée
        window.dispatchEvent(new CustomEvent('transactionUpdated', {
          detail: { transactionId: transaction.id }
        }));
        console.log('📢 [TransactionsTable] Événement transactionUpdated émis');
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

  // Étape 3 (cutover Task C2) : reclassification via le référentiel de catégories
  // (transactionsAPI.setCategory), au lieu des dropdowns en cascade sur allowed_mappings.
  const handleEditClassification = (transaction: Transaction) => {
    setEditingClassificationId(transaction.id);
    setEditingCategoryId(transaction.category_id ?? null);
  };

  const handleSaveClassification = async (transaction: Transaction) => {
    try {
      await transactionsAPI.setCategory(transaction.id, editingCategoryId);
      setEditingClassificationId(null);
      setEditingCategoryId(null);
      await loadTransactions();
      // Appeler le callback pour rafraîchir Mapping
      if (onUpdate) {
        onUpdate();
      }

      // Émettre un événement global pour notifier les autres pages (ex: Amortissements)
      // que la transaction a été modifiée (mapping)
      window.dispatchEvent(new CustomEvent('transactionUpdated', {
        detail: { transactionId: transaction.id }
      }));
      console.log('📢 [TransactionsTable] Événement transactionUpdated émis (mapping modifié)');
    } catch (err: any) {
      console.error('Error updating classification:', err);
      alert(`Erreur lors de la modification: ${err.message || 'Erreur inconnue'}`);
    }
  };

  const handleCancelClassification = () => {
    setEditingClassificationId(null);
    setEditingCategoryId(null);
  };

  // Étape 4 : saisie manuelle — ➕ Ajouter une transaction

  const resetAddForm = () => {
    setAddDate('');
    setAddQuantite('');
    setAddNom('');
    setAddCategoryId(null);
  };

  const handleOpenAddForm = () => {
    setManualError(null);
    resetAddForm();
    setShowAddForm(true);
    setShowCrossEntryForm(false);
    setSplittingId(null);
  };

  const handleCancelAddForm = () => {
    setShowAddForm(false);
    resetAddForm();
  };

  const handleSubmitAdd = async () => {
    if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
      setManualError('Aucune propriété sélectionnée');
      return;
    }
    const quantite = parseFloat(addQuantite);
    if (!addDate || addNom.trim() === '' || addQuantite.trim() === '' || isNaN(quantite)) {
      setManualError('Merci de renseigner la date, le montant et le nom.');
      return;
    }
    setAddSubmitting(true);
    setManualError(null);
    try {
      await transactionsAPI.createManual({
        property_id: activeProperty.id,
        date: addDate,
        quantite,
        nom: addNom,
        category_id: addCategoryId,
      });
      setShowAddForm(false);
      resetAddForm();
      await loadTransactions();
      if (onUpdate) {
        onUpdate();
      }
    } catch (err) {
      console.error('Error creating manual transaction:', err);
      setManualError(err instanceof Error ? err.message : 'Erreur lors de la création de la transaction');
    } finally {
      setAddSubmitting(false);
    }
  };

  // Étape 4 : saisie manuelle — ✂️ Éclater une transaction

  const handleOpenSplit = (transaction: Transaction) => {
    setManualError(null);
    setSplittingId(transaction.id);
    setSplitParts([
      { quantite: '', nom: '', category_id: null },
      { quantite: '', nom: '', category_id: null },
    ]);
    setShowAddForm(false);
    setShowCrossEntryForm(false);
  };

  const handleCancelSplit = () => {
    setSplittingId(null);
    setSplitParts([]);
  };

  const handleAddSplitPart = () => {
    setSplitParts((prev) => [...prev, { quantite: '', nom: '', category_id: null }]);
  };

  const handleRemoveSplitPart = (index: number) => {
    setSplitParts((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSplitPartQuantiteChange = (index: number, value: string) => {
    setSplitParts((prev) => prev.map((part, i) => (i === index ? { ...part, quantite: value } : part)));
  };

  const handleSplitPartNomChange = (index: number, value: string) => {
    setSplitParts((prev) => prev.map((part, i) => (i === index ? { ...part, nom: value } : part)));
  };

  const handleSplitPartCategoryChange = (index: number, categoryId: number | null) => {
    setSplitParts((prev) => prev.map((part, i) => (i === index ? { ...part, category_id: categoryId } : part)));
  };

  const splitSum = useMemo(() => {
    return splitParts.reduce((sum, part) => sum + (parseFloat(part.quantite) || 0), 0);
  }, [splitParts]);

  const handleSubmitSplit = async (transaction: Transaction) => {
    const sumCents = Math.round(splitSum * 100);
    const originalCents = Math.round(transaction.quantite * 100);
    if (sumCents !== originalCents) {
      setManualError("La somme des parts doit être égale au montant d'origine.");
      return;
    }
    if (splitParts.some((p) => p.nom.trim() === '' || p.quantite.trim() === '' || isNaN(parseFloat(p.quantite)))) {
      setManualError('Merci de renseigner le montant et le nom de chaque part.');
      return;
    }
    setSplitSubmitting(true);
    setManualError(null);
    try {
      await transactionsAPI.splitTransaction(
        transaction.id,
        splitParts.map((p) => ({
          quantite: parseFloat(p.quantite),
          nom: p.nom,
          category_id: p.category_id,
        }))
      );
      setSplittingId(null);
      setSplitParts([]);
      await loadTransactions();
      if (onUpdate) {
        onUpdate();
      }
    } catch (err) {
      console.error('Error splitting transaction:', err);
      setManualError(err instanceof Error ? err.message : "Erreur lors de l'éclatement de la transaction");
    } finally {
      setSplitSubmitting(false);
    }
  };

  // Étape 4 : saisie manuelle — ⇄ Écriture croisée

  const resetCrossEntryForm = () => {
    setCrossDate('');
    setCrossMontant('');
    setCrossDebitNom('');
    setCrossDebitCategoryId(null);
    setCrossCreditNom('');
    setCrossCreditCategoryId(null);
  };

  const handleOpenCrossEntryForm = () => {
    setManualError(null);
    resetCrossEntryForm();
    setShowCrossEntryForm(true);
    setShowAddForm(false);
    setSplittingId(null);
  };

  const handleCancelCrossEntryForm = () => {
    setShowCrossEntryForm(false);
    resetCrossEntryForm();
  };

  const handleSubmitCrossEntry = async () => {
    if (!activeProperty || !activeProperty.id || activeProperty.id <= 0) {
      setManualError('Aucune propriété sélectionnée');
      return;
    }
    const montant = parseFloat(crossMontant);
    if (!crossDate || crossDebitNom.trim() === '' || crossCreditNom.trim() === '' || crossMontant.trim() === '' || isNaN(montant)) {
      setManualError('Merci de renseigner la date, le montant et les deux noms.');
      return;
    }
    setCrossSubmitting(true);
    setManualError(null);
    try {
      await transactionsAPI.crossEntry({
        property_id: activeProperty.id,
        date: crossDate,
        montant,
        debit: { nom: crossDebitNom, category_id: crossDebitCategoryId },
        credit: { nom: crossCreditNom, category_id: crossCreditCategoryId },
      });
      setShowCrossEntryForm(false);
      resetCrossEntryForm();
      await loadTransactions();
      if (onUpdate) {
        onUpdate();
      }
    } catch (err) {
      console.error('Error creating cross entry:', err);
      setManualError(err instanceof Error ? err.message : "Erreur lors de la création de l'écriture croisée");
    } finally {
      setCrossSubmitting(false);
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div>
      {/* Boutons d'export */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '16px',
        padding: '0 4px'
      }}>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            onClick={() => handleExport('excel')}
            disabled={isExporting}
            style={{
              padding: '8px 16px',
              fontSize: '14px',
              fontWeight: '500',
              color: '#fff',
              backgroundColor: isExporting ? '#9ca3af' : '#1e3a5f',
              border: 'none',
              borderRadius: '6px',
              cursor: isExporting ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'background-color 0.2s',
            }}
            onMouseEnter={(e) => {
              if (!isExporting) {
                e.currentTarget.style.backgroundColor = '#2d4a6f';
              }
            }}
            onMouseLeave={(e) => {
              if (!isExporting) {
                e.currentTarget.style.backgroundColor = '#1e3a5f';
              }
            }}
          >
            {isExporting ? (
              <>
                <span>⏳</span>
                <span>Export en cours...</span>
              </>
            ) : (
              <>
                <span>📥</span>
                <span>Extraire (Excel)</span>
              </>
            )}
          </button>
          <button
            onClick={() => handleExport('csv')}
            disabled={isExporting}
            style={{
              padding: '8px 16px',
              fontSize: '14px',
              fontWeight: '500',
              color: '#fff',
              backgroundColor: isExporting ? '#9ca3af' : '#1e3a5f',
              border: 'none',
              borderRadius: '6px',
              cursor: isExporting ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'background-color 0.2s',
            }}
            onMouseEnter={(e) => {
              if (!isExporting) {
                e.currentTarget.style.backgroundColor = '#2d4a6f';
              }
            }}
            onMouseLeave={(e) => {
              if (!isExporting) {
                e.currentTarget.style.backgroundColor = '#1e3a5f';
              }
            }}
          >
            {isExporting ? (
              <>
                <span>⏳</span>
                <span>Export en cours...</span>
              </>
            ) : (
              <>
                <span>📥</span>
                <span>Extraire (CSV)</span>
              </>
            )}
          </button>
        </div>
        {exportError && (
          <div style={{
            padding: '8px 12px',
            backgroundColor: '#fee2e2',
            color: '#991b1b',
            borderRadius: '6px',
            fontSize: '14px',
          }}>
            ❌ Erreur: {exportError}
          </div>
        )}
      </div>

      {/* Saisie manuelle : Ajouter / Écriture croisée */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', padding: '0 4px' }}>
        <button
          onClick={handleOpenAddForm}
          style={{
            padding: '8px 16px',
            fontSize: '14px',
            fontWeight: '500',
            color: '#fff',
            backgroundColor: '#1e3a5f',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
          }}
        >
          ➕ Ajouter
        </button>
        <button
          onClick={handleOpenCrossEntryForm}
          style={{
            padding: '8px 16px',
            fontSize: '14px',
            fontWeight: '500',
            color: '#fff',
            backgroundColor: '#1e3a5f',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
          }}
        >
          ⇄ Écriture croisée
        </button>
      </div>

      {manualError && (
        <div
          role="alert"
          style={{
            padding: '12px 16px',
            marginBottom: '16px',
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '8px',
            color: '#dc3545',
            fontSize: '14px',
          }}
        >
          ❌ {manualError}
        </div>
      )}

      {showAddForm && (
        <div style={{
          marginBottom: '16px',
          padding: '16px',
          backgroundColor: 'white',
          border: '1px solid #e5e5e5',
          borderRadius: '8px',
        }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '15px', color: '#1a1a1a' }}>➕ Ajouter une transaction</h3>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
            <input
              type="date"
              aria-label="Date"
              value={addDate}
              onChange={(e) => setAddDate(e.target.value)}
              style={{ padding: '6px 8px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '13px' }}
            />
            <input
              type="number"
              step="0.01"
              aria-label="Montant"
              placeholder="Montant €"
              value={addQuantite}
              onChange={(e) => setAddQuantite(e.target.value)}
              style={{ padding: '6px 8px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '13px', width: '120px' }}
            />
            <input
              type="text"
              aria-label="Nom"
              placeholder="Nom"
              value={addNom}
              onChange={(e) => setAddNom(e.target.value)}
              style={{ padding: '6px 8px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '13px', minWidth: '200px' }}
            />
            <CategorySelector value={addCategoryId} onChange={setAddCategoryId} />
            <button
              onClick={handleSubmitAdd}
              disabled={addSubmitting}
              style={{
                padding: '6px 14px',
                backgroundColor: addSubmitting ? '#ccc' : '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '13px',
                cursor: addSubmitting ? 'not-allowed' : 'pointer',
              }}
            >
              {addSubmitting ? '⏳ Ajout...' : 'Ajouter'}
            </button>
            <button
              onClick={handleCancelAddForm}
              disabled={addSubmitting}
              style={{
                padding: '6px 14px',
                backgroundColor: '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '13px',
                cursor: 'pointer',
              }}
            >
              Annuler
            </button>
          </div>
        </div>
      )}

      {showCrossEntryForm && (
        <div style={{
          marginBottom: '16px',
          padding: '16px',
          backgroundColor: 'white',
          border: '1px solid #e5e5e5',
          borderRadius: '8px',
        }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '15px', color: '#1a1a1a' }}>⇄ Écriture croisée</h3>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap', marginBottom: '12px' }}>
            <input
              type="date"
              aria-label="Date"
              value={crossDate}
              onChange={(e) => setCrossDate(e.target.value)}
              style={{ padding: '6px 8px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '13px' }}
            />
            <input
              type="number"
              step="0.01"
              aria-label="Montant"
              placeholder="Montant €"
              value={crossMontant}
              onChange={(e) => setCrossMontant(e.target.value)}
              style={{ padding: '6px 8px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '13px', width: '120px' }}
            />
          </div>
          <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap', marginBottom: '12px' }}>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '12px', color: '#666', fontWeight: 500 }}>Débit :</span>
              <input
                type="text"
                aria-label="Nom débit"
                placeholder="ex: Frais de notaire"
                value={crossDebitNom}
                onChange={(e) => setCrossDebitNom(e.target.value)}
                style={{ padding: '6px 8px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '13px', minWidth: '200px' }}
              />
              <CategorySelector value={crossDebitCategoryId} onChange={setCrossDebitCategoryId} />
            </div>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '12px', color: '#666', fontWeight: 500 }}>Crédit :</span>
              <input
                type="text"
                aria-label="Nom crédit"
                placeholder="ex: Compte courant d'associé"
                value={crossCreditNom}
                onChange={(e) => setCrossCreditNom(e.target.value)}
                style={{ padding: '6px 8px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '13px', minWidth: '200px' }}
              />
              <CategorySelector value={crossCreditCategoryId} onChange={setCrossCreditCategoryId} />
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={handleSubmitCrossEntry}
              disabled={crossSubmitting}
              style={{
                padding: '6px 14px',
                backgroundColor: crossSubmitting ? '#ccc' : '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '13px',
                cursor: crossSubmitting ? 'not-allowed' : 'pointer',
              }}
            >
              {crossSubmitting ? '⏳ Création...' : 'Valider'}
            </button>
            <button
              onClick={handleCancelCrossEntryForm}
              disabled={crossSubmitting}
              style={{
                padding: '6px 14px',
                backgroundColor: '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '13px',
                cursor: 'pointer',
              }}
            >
              Annuler
            </button>
          </div>
        </div>
      )}

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
                    <Fragment key={transaction.id}>
                    <tr
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
                        <CategorySelector
                          value={editingCategoryId}
                          onChange={setEditingCategoryId}
                        />
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
                        <span style={{ fontSize: '12px', color: '#999', fontStyle: 'italic' }}>
                          (auto)
                        </span>
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
                        <span style={{ fontSize: '12px', color: '#999', fontStyle: 'italic' }}>
                          (auto)
                        </span>
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
                              onClick={() => handleOpenSplit(transaction)}
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
                              ✂️
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
                  {splittingId === transaction.id && (
                    <tr>
                      <td colSpan={9} style={{ padding: '16px', backgroundColor: '#fafafa', borderBottom: '1px solid #e5e5e5' }}>
                        <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#1a1a1a' }}>
                          ✂️ Éclater la transaction ({formatAmount(transaction.quantite)})
                        </h4>
                        {splitParts.map((part, index) => (
                          <div key={index} style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap' }}>
                            <input
                              type="number"
                              step="0.01"
                              aria-label={`Montant part ${index + 1}`}
                              placeholder="Montant €"
                              value={part.quantite}
                              onChange={(e) => handleSplitPartQuantiteChange(index, e.target.value)}
                              style={{ padding: '6px 8px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '13px', width: '110px' }}
                            />
                            <input
                              type="text"
                              aria-label={`Nom part ${index + 1}`}
                              placeholder="Nom"
                              value={part.nom}
                              onChange={(e) => handleSplitPartNomChange(index, e.target.value)}
                              style={{ padding: '6px 8px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '13px', minWidth: '200px' }}
                            />
                            <CategorySelector
                              value={part.category_id}
                              onChange={(categoryId) => handleSplitPartCategoryChange(index, categoryId)}
                            />
                            {splitParts.length > 2 && (
                              <button
                                onClick={() => handleRemoveSplitPart(index)}
                                style={{ padding: '6px 10px', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: '4px', fontSize: '12px', cursor: 'pointer' }}
                              >
                                ✗
                              </button>
                            )}
                          </div>
                        ))}
                        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginTop: '8px', flexWrap: 'wrap' }}>
                          <button
                            onClick={handleAddSplitPart}
                            style={{ padding: '6px 12px', backgroundColor: '#1e3a5f', color: 'white', border: 'none', borderRadius: '4px', fontSize: '12px', cursor: 'pointer' }}
                          >
                            + Ajouter une ligne
                          </button>
                          <span style={{
                            fontSize: '13px',
                            fontWeight: 500,
                            color: Math.round(splitSum * 100) === Math.round(transaction.quantite * 100) ? '#28a745' : '#dc3545',
                          }}>
                            Somme : {formatAmount(splitSum)} / {formatAmount(transaction.quantite)}
                          </span>
                          <button
                            onClick={() => handleSubmitSplit(transaction)}
                            disabled={splitSubmitting || Math.round(splitSum * 100) !== Math.round(transaction.quantite * 100)}
                            style={{
                              padding: '6px 14px',
                              backgroundColor: (splitSubmitting || Math.round(splitSum * 100) !== Math.round(transaction.quantite * 100)) ? '#ccc' : '#28a745',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              fontSize: '13px',
                              cursor: (splitSubmitting || Math.round(splitSum * 100) !== Math.round(transaction.quantite * 100)) ? 'not-allowed' : 'pointer',
                            }}
                          >
                            {splitSubmitting ? '⏳ Validation...' : 'Valider'}
                          </button>
                          <button
                            onClick={handleCancelSplit}
                            disabled={splitSubmitting}
                            style={{ padding: '6px 14px', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: '4px', fontSize: '13px', cursor: 'pointer' }}
                          >
                            Annuler
                          </button>
                        </div>
                      </td>
                    </tr>
                  )}
                  </Fragment>
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

