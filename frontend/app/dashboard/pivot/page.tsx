/**
 * Pivot Table Page - Page principale avec gestion des sous-onglets
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import PivotFieldSelector, { PivotFieldConfig } from '@/components/PivotFieldSelector';
import PivotTable from '@/components/PivotTable';
import PivotTabs, { PivotTab } from '@/components/PivotTabs';
import PivotDetailsTable from '@/components/PivotDetailsTable';
import { pivotConfigsAPI, PivotConfigResponse } from '@/api/client';
import { useProperty } from '@/contexts/PropertyContext';

export default function PivotPage() {
  const { activeProperty } = useProperty();
  const [tabs, setTabs] = useState<PivotTab[]>([]);
  const [activeTabId, setActiveTabId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [selectedRowValues, setSelectedRowValues] = useState<(string | number)[]>([]);
  const [selectedColumnValues, setSelectedColumnValues] = useState<(string | number)[]>([]);

  console.log('[PivotPage] propertyId:', activeProperty?.id);

  // Charger les tableaux sauvegardés au montage et quand la propriété change
  useEffect(() => {
    const loadSavedConfigs = async () => {
      if (!activeProperty?.id) {
        console.log('[PivotPage] Pas de propriété active, skip le chargement');
        setIsLoading(false);
        return;
      }

      console.log('[PivotPage] Chargement des configs pour propertyId:', activeProperty.id);
      setIsLoading(true);
      try {
        const response = await pivotConfigsAPI.getAll(activeProperty.id, 0, 100);
        console.log('[PivotPage] Loaded', response.items.length, 'configs pour propertyId:', activeProperty.id);
        
        const savedTabs: PivotTab[] = response.items.map((item) => ({
          id: `saved-${item.id}`,
          name: item.name,
          config: {
            rows: item.config.rows as any,
            columns: item.config.columns as any,
            data: item.config.data as any,
            filters: item.config.filters || {},
          },
          isSaved: true,
          createdAt: item.created_at, // Stocker pour le tri
        }));

        // Trier les onglets sauvegardés par ordre de création (created_at croissant = ancien → récent)
        const sortedSavedTabs = savedTabs.sort((a, b) => {
          const aDate = new Date(a.createdAt || '').getTime();
          const bDate = new Date(b.createdAt || '').getTime();
          return aDate - bDate; // Plus ancien en premier
        });

        // Vérifier qu'il n'y a pas de doublons
        const seenIds = new Set<string>();
        const uniqueSavedTabs = sortedSavedTabs.filter((tab) => {
          if (seenIds.has(tab.id)) {
            return false;
          }
          seenIds.add(tab.id);
          return true;
        });

        // Si aucun TCD sauvegardé, créer "New TCD" initial
        // Sinon, afficher seulement les TCD sauvegardés (pas de "New TCD" initial)
        if (uniqueSavedTabs.length === 0) {
          const initialNewTab: PivotTab = {
            id: 'new',
            name: 'New TCD',
            config: { rows: [], columns: [], data: [], filters: {} },
            isSaved: false,
          };
          setTabs([initialNewTab]);
          setActiveTabId('new');
        } else {
          setTabs(uniqueSavedTabs);
          setActiveTabId(uniqueSavedTabs[0].id);
        }
      } catch (error) {
        console.error('[PivotPage] Erreur lors du chargement des configs sauvegardés:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadSavedConfigs();
  }, [activeProperty?.id]);

  const activeTab = tabs.find(t => t.id === activeTabId) || tabs[0];

  const handleConfigChange = useCallback(async (newConfig: PivotFieldConfig) => {
    if (!activeProperty?.id) {
      console.error('[PivotPage] Pas de propertyId pour sauvegarder');
      return;
    }

    setTabs((prev) =>
      prev.map((tab) =>
        tab.id === activeTabId ? { ...tab, config: newConfig } : tab
      )
    );

    // Sauvegarder automatiquement si l'onglet est déjà sauvegardé
    const activeTab = tabs.find(t => t.id === activeTabId);
    if (activeTab?.isSaved) {
      const configId = parseInt(activeTabId.replace('saved-', ''));
      try {
        console.log('[PivotPage] Auto-save config', configId, 'pour propertyId:', activeProperty.id);
        await pivotConfigsAPI.update(activeProperty.id, configId, {
          config: {
            rows: newConfig.rows,
            columns: newConfig.columns,
            data: newConfig.data,
            filters: newConfig.filters,
          },
        });
      } catch (error) {
        console.error('[PivotPage] Erreur lors de la sauvegarde automatique:', error);
      }
    }
  }, [activeTabId, tabs, activeProperty?.id]);

  const handleTabChange = (tabId: string) => {
    setActiveTabId(tabId);
  };

  const handleTabCreate = () => {
    // Vérifier qu'il n'y a pas déjà un onglet "New TCD" non sauvegardé
    const existingNewTab = tabs.find(t => !t.isSaved && t.name === 'New TCD');
    if (existingNewTab) {
      // Activer l'onglet existant au lieu d'en créer un nouveau
      setActiveTabId(existingNewTab.id);
      return;
    }

    // Créer un nouvel onglet "New TCD" temporaire
    const newTab: PivotTab = {
      id: `new-${Date.now()}`,
      name: 'New TCD',
      config: {
        rows: [],
        columns: [],
        data: [],
        filters: {},
      },
      isSaved: false,
    };
    // Ajouter à la fin (après les TCD sauvegardés et le bouton "+")
    setTabs((prev) => [...prev, newTab]);
    setActiveTabId(newTab.id);
  };

  const handleTabRename = async (tabId: string, newName: string) => {
    if (!activeProperty?.id) {
      console.error('[PivotPage] Pas de propertyId pour renommer');
      return;
    }

    const tab = tabs.find(t => t.id === tabId);
    if (!tab) return;

    setTabs((prev) =>
      prev.map((t) => (t.id === tabId ? { ...t, name: newName } : t))
    );

    // Sauvegarder automatiquement si c'est un onglet sauvegardé
    if (tab.isSaved) {
      const configId = parseInt(tabId.replace('saved-', ''));
      try {
        console.log('[PivotPage] Renommer config', configId, 'pour propertyId:', activeProperty.id);
        await pivotConfigsAPI.update(activeProperty.id, configId, { name: newName });
      } catch (error) {
        console.error('[PivotPage] Erreur lors de la sauvegarde du nom:', error);
      }
    } else {
      // Si c'est un nouvel onglet, créer la sauvegarde
      try {
        console.log('[PivotPage] Créer config pour propertyId:', activeProperty.id);
        const response = await pivotConfigsAPI.create(activeProperty.id, {
          name: newName,
          config: {
            rows: tab.config.rows,
            columns: tab.config.columns,
            data: tab.config.data,
            filters: tab.config.filters,
          },
        });
        // Mettre à jour l'onglet avec l'ID sauvegardé
        const newSavedId = `saved-${response.id}`;
        setTabs((prev) => {
          // Retirer l'onglet temporaire et ajouter le sauvegardé à la bonne position (par ordre de création)
          const updatedTabs = prev
            .filter(t => t.id !== tabId) // Retirer l'ancien onglet
            .filter(t => t.isSaved); // Garder seulement les sauvegardés
          
          // Créer le nouvel onglet sauvegardé
          const savedTab: PivotTab = {
            id: newSavedId,
            name: newName,
            config: tab.config,
            isSaved: true,
            createdAt: response.created_at,
          };
          
          // Ajouter le nouvel onglet et trier par date de création
          updatedTabs.push(savedTab);
          updatedTabs.sort((a, b) => {
            const aDate = new Date(a.createdAt || '').getTime();
            const bDate = new Date(b.createdAt || '').getTime();
            return aDate - bDate; // Plus ancien en premier
          });
          
          return updatedTabs;
        });
        setActiveTabId(newSavedId);
      } catch (error) {
        console.error('[PivotPage] Erreur lors de la création de la sauvegarde:', error);
      }
    }
  };

  const handleTabDelete = async (tabId: string) => {
    if (!activeProperty?.id) {
      console.error('[PivotPage] Pas de propertyId pour supprimer');
      return;
    }

    const tab = tabs.find(t => t.id === tabId);
    if (!tab) return;

    // Supprimer de la BDD si sauvegardé
    if (tab.isSaved) {
      const configId = parseInt(tabId.replace('saved-', ''));
      try {
        console.log('[PivotPage] Supprimer config', configId, 'pour propertyId:', activeProperty.id);
        await pivotConfigsAPI.delete(activeProperty.id, configId);
      } catch (error) {
        console.error('[PivotPage] Erreur lors de la suppression:', error);
      }
    }

    // Retirer l'onglet de la liste
    const newTabs = tabs.filter(t => t.id !== tabId);
    setTabs(newTabs);

    // Si l'onglet supprimé était actif, activer le premier disponible
    if (tabId === activeTabId) {
      if (newTabs.length > 0) {
        setActiveTabId(newTabs[0].id);
      } else {
        // Si plus aucun onglet, créer "New TCD" initial
        const initialNewTab: PivotTab = {
          id: 'new',
          name: 'New TCD',
          config: { rows: [], columns: [], data: [], filters: {} },
          isSaved: false,
        };
        setTabs([initialNewTab]);
        setActiveTabId('new');
      }
    }
  };

  const handleTabMove = (tabId: string, direction: 'left' | 'right') => {
    const currentIndex = tabs.findIndex(t => t.id === tabId);
    if (currentIndex === -1) return;

    const newIndex = direction === 'left' ? currentIndex - 1 : currentIndex + 1;
    if (newIndex < 0 || newIndex >= tabs.length) return;

    const newTabs = [...tabs];
    [newTabs[currentIndex], newTabs[newIndex]] = [newTabs[newIndex], newTabs[currentIndex]];
    setTabs(newTabs);
  };

  const handleCellClick = (rowValues: (string | number)[], columnValues: (string | number)[]) => {
    console.log('[PivotPage] Cellule cliquée:', { rowValues, columnValues });
    setSelectedRowValues(rowValues);
    setSelectedColumnValues(columnValues);
  };

  const handleCloseDetails = () => {
    setSelectedRowValues([]);
    setSelectedColumnValues([]);
  };

  if (!activeProperty?.id) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#f9fafb', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ fontSize: '14px', color: '#6b7280' }}>Veuillez sélectionner une propriété</div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#f9fafb', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ fontSize: '14px', color: '#6b7280' }}>Chargement...</div>
      </div>
    );
  }

  // Séparer les onglets : sauvegardés, puis temporaires (New TCD)
  const savedTabs = tabs.filter(t => t.isSaved);
  const tempTabs = tabs.filter(t => !t.isSaved);
  // Ordre : sauvegardés (déjà triés par création), puis temporaires
  const orderedTabs = [...savedTabs, ...tempTabs];

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f9fafb', display: 'flex', flexDirection: 'column' }}>
      {/* Sous-onglets */}
      <PivotTabs
        tabs={orderedTabs}
        activeTabId={activeTabId}
        onTabChange={handleTabChange}
        onTabCreate={handleTabCreate}
        onTabRename={handleTabRename}
        onTabDelete={handleTabDelete}
        onTabMove={handleTabMove}
      />

      {/* Contenu principal */}
      {activeTab && (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <PivotFieldSelector config={activeTab.config} onChange={handleConfigChange} />
          
          {/* Tableau croisé */}
          <div style={{ flex: 1, padding: '16px', overflow: 'auto' }}>
            <PivotTable config={activeTab.config} onCellClick={handleCellClick} />
            
            {/* Transactions détaillées */}
            {(selectedRowValues.length > 0 || selectedColumnValues.length > 0) && (
              <PivotDetailsTable
                config={activeTab.config}
                rowValues={selectedRowValues}
                columnValues={selectedColumnValues}
                onClose={handleCloseDetails}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
