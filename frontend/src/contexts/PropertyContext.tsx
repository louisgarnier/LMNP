/**
 * PropertyContext - Context for managing the active property
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Property, propertiesAPI } from '@/api/client';

const STORAGE_KEY = 'active_property_id';

interface PropertyContextType {
  activeProperty: Property | null;
  properties: Property[];
  loading: boolean;
  error: string | null;
  isRestoring: boolean; // Expose isRestoring so components can wait for restoration
  setActiveProperty: (property: Property | null) => void;
  refreshProperties: () => Promise<void>;
  createProperty: (name: string, address?: string) => Promise<Property>;
  updateProperty: (id: number, name?: string, address?: string) => Promise<Property>;
  deleteProperty: (id: number) => Promise<void>;
}

const PropertyContext = createContext<PropertyContextType | undefined>(undefined);

export function PropertyProvider({ children }: { children: ReactNode }) {
  const [activeProperty, setActivePropertyState] = useState<Property | null>(null);
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isRestoring, setIsRestoring] = useState<boolean>(false);
  const [hasCheckedLocalStorage, setHasCheckedLocalStorage] = useState<boolean>(false);

  // Load properties on mount
  const refreshProperties = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('[PropertyContext] Chargement des propriétés...');
      
      // Timeout de 10 secondes pour éviter que l'app reste bloquée
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Timeout: Le serveur ne répond pas. Vérifiez que le backend est démarré sur http://localhost:8000')), 10000);
      });
      
      const apiPromise = propertiesAPI.getAll(0, 1000);
      const response = await Promise.race([apiPromise, timeoutPromise]) as Awaited<ReturnType<typeof propertiesAPI.getAll>>;
      
      console.log('[PropertyContext] Propriétés chargées:', response.items.length);
      setProperties(response.items);

      // Restore active property from localStorage if available
      const savedPropertyId = localStorage.getItem(STORAGE_KEY);
      console.log('[PropertyContext] Vérification localStorage au chargement:', savedPropertyId);
      if (savedPropertyId) {
        const propertyId = parseInt(savedPropertyId, 10);
        const property = response.items.find(p => p.id === propertyId);
        if (property) {
          console.log('[PropertyContext] Propriété active trouvée dans localStorage, restauration...');
          // Set flag to indicate we're restoring
          setIsRestoring(true);
          // Set activeProperty - this will trigger a re-render
          // The useEffect below will set loading to false once activeProperty is updated
          setActivePropertyState(property);
          return; // Exit early - useEffect will handle setting loading to false
        } else {
          // Property not found, clear localStorage
          console.log('[PropertyContext] Propriété sauvegardée non trouvée, nettoyage localStorage');
          localStorage.removeItem(STORAGE_KEY);
        }
      } else {
        console.log('[PropertyContext] Aucune propriété sauvegardée dans localStorage');
      }
      
      // If we reach here, no property was restored, set loading to false
      setLoading(false);
      console.log('[PropertyContext] Chargement terminé, loading=false, aucune propriété active');
    } catch (err) {
      console.error('[PropertyContext] Erreur lors du chargement des propriétés:', err);
      const errorMessage = err instanceof Error ? err.message : 'Erreur lors du chargement des propriétés';
      setError(errorMessage);
      console.error('[PropertyContext] Message d\'erreur:', errorMessage);
      setLoading(false);
      console.log('[PropertyContext] Chargement terminé avec erreur, loading=false');
    } finally {
      // Mark that we've checked localStorage, so the save useEffect can now run
      setHasCheckedLocalStorage(true);
    }
  };

  useEffect(() => {
    refreshProperties();
  }, []);

  // When restoring from localStorage, wait for activeProperty to be updated before setting loading to false
  // This ensures activeProperty is available when components check it
  useEffect(() => {
    if (isRestoring && activeProperty) {
      console.log('[PropertyContext] Propriété restaurée avec succès, loading=false');
      setLoading(false);
      setIsRestoring(false);
    }
  }, [isRestoring, activeProperty]);

  // Save active property to localStorage when it changes
  // IMPORTANT: Don't remove from localStorage on initial mount (activeProperty = null)
  // Wait until we've checked localStorage first (hasCheckedLocalStorage = true)
  useEffect(() => {
    // Don't do anything until we've checked localStorage on initial load
    if (!hasCheckedLocalStorage) {
      return;
    }
    
    if (activeProperty) {
      console.log('[PropertyContext] Sauvegarde de la propriété active dans localStorage:', activeProperty.id, activeProperty.name);
      localStorage.setItem(STORAGE_KEY, activeProperty.id.toString());
      // Vérifier que la sauvegarde a fonctionné
      const saved = localStorage.getItem(STORAGE_KEY);
      console.log('[PropertyContext] Vérification localStorage après sauvegarde:', saved);
    } else {
      console.log('[PropertyContext] Suppression de la propriété active du localStorage');
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [activeProperty, hasCheckedLocalStorage]);

  const setActiveProperty = (property: Property | null) => {
    setActivePropertyState(property);
  };

  const createProperty = async (name: string, address?: string): Promise<Property> => {
    try {
      const newProperty = await propertiesAPI.create({ name, address });
      await refreshProperties();
      return newProperty;
    } catch (err) {
      console.error('Error creating property:', err);
      throw err;
    }
  };

  const updateProperty = async (id: number, name?: string, address?: string): Promise<Property> => {
    try {
      const updatedProperty = await propertiesAPI.update(id, { name, address });
      await refreshProperties();
      
      // Update active property if it's the one being updated
      if (activeProperty?.id === id) {
        setActivePropertyState(updatedProperty);
      }
      
      return updatedProperty;
    } catch (err) {
      console.error('Error updating property:', err);
      throw err;
    }
  };

  const deleteProperty = async (id: number): Promise<void> => {
    try {
      await propertiesAPI.delete(id);
      
      // Clear active property if it's the one being deleted
      if (activeProperty?.id === id) {
        setActivePropertyState(null);
        localStorage.removeItem(STORAGE_KEY);
      }
      
      // Refresh properties list
      await refreshProperties();
    } catch (err) {
      console.error('Error deleting property:', err);
      throw err;
    }
  };

  return (
    <PropertyContext.Provider
      value={{
        activeProperty,
        properties,
        loading,
        error,
        isRestoring,
        setActiveProperty,
        refreshProperties,
        createProperty,
        updateProperty,
        deleteProperty,
      }}
    >
      {children}
    </PropertyContext.Provider>
  );
}

export function useProperty() {
  const context = useContext(PropertyContext);
  if (context === undefined) {
    throw new Error('useProperty must be used within a PropertyProvider');
  }
  return context;
}
