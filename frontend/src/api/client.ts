/**
 * API Client for Frontend
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 * Always check with the user before modifying this file.
 * 
 * Handles all communication with the backend API
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  try {
    console.log(`📤 [API] Appel ${options?.method || 'GET'} ${url}`);
    
    // Ne pas ajouter Content-Type si c'est FormData (le navigateur le fera automatiquement)
    const isFormData = options?.body instanceof FormData;
    const headers: HeadersInit = isFormData
      ? { ...options?.headers }
      : {
          'Content-Type': 'application/json',
          ...options?.headers,
        };
    
    const response = await fetch(url, {
      ...options,
      headers,
    });

    console.log(`📥 [API] Réponse ${response.status} pour ${endpoint}`);

    if (!response.ok) {
      let error;
      try {
        error = await response.json();
      } catch {
        error = { detail: `HTTP error! status: ${response.status}` };
      }
      
      // Gérer les erreurs de validation FastAPI (422)
      let errorMessage = `HTTP error! status: ${response.status}`;
      if (error.detail) {
        if (Array.isArray(error.detail)) {
          // Erreurs de validation FastAPI (liste d'erreurs)
          errorMessage = error.detail.map((e: any) => {
            if (typeof e === 'string') return e;
            return `${e.loc?.join('.') || 'field'}: ${e.msg || e}`;
          }).join(', ');
        } else if (typeof error.detail === 'string') {
          errorMessage = error.detail;
        } else {
          errorMessage = JSON.stringify(error.detail);
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      // Logger différemment selon le type d'erreur
      // 400/404/422 = erreurs métier/validation (normales) → warn
      // 500+ = erreurs techniques (vraies erreurs) → error
      if (response.status >= 500) {
        console.error(`❌ [API] Erreur serveur ${response.status} (${endpoint}): ${errorMessage}`);
      } else {
        // Erreurs métier normales (400, 404, 422) - pas besoin de logger comme erreur
        // Le message sera affiché à l'utilisateur via l'alerte
        console.log(`ℹ️ [API] Réponse ${response.status} (${endpoint}): ${errorMessage}`);
      }
      throw new Error(errorMessage);
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    return await response.json();
  } catch (error) {
    // Gérer les erreurs réseau (Failed to fetch)
    if (error instanceof TypeError && error.message === 'Failed to fetch') {
      // Ne pas logger comme erreur - c'est juste que le backend n'est pas disponible
      // Le composant gérera cela silencieusement
      throw new Error(`NETWORK_ERROR: Impossible de se connecter au serveur. Vérifiez que le backend est démarré sur ${API_BASE_URL}`);
    }
    
    // Pour les autres erreurs, logger normalement
    console.error(`❌ [API] Erreur lors de l'appel (${endpoint}):`, error);
    throw error;
  }
}

// Types
export interface Transaction {
  id: number;
  date: string;
  quantite: number;
  nom: string;
  solde: number;
  source_file?: string;
  created_at: string;
  updated_at: string;
  level_1?: string;
  level_2?: string;
  level_3?: string;
}

export interface TransactionCreate {
  date: string;
  quantite: number;
  nom: string;
  solde: number;
  source_file?: string;
}

export interface TransactionUpdate {
  date?: string;
  quantite?: number;
  nom?: string;
  solde?: number;
  source_file?: string;
}

export interface TransactionListResponse {
  transactions: Transaction[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * Health check API
 */
export const healthAPI = {
  check: async (): Promise<{ status: string }> => {
    return fetchAPI<{ status: string }>('/health');
  },
};

/**
 * Transactions API
 */
export const transactionsAPI = {
  /**
   * Récupérer toutes les transactions (sans pagination, sans filtres)
   * Utilisé pour l'export Excel
   */
  getAllForExport: async (): Promise<Transaction[]> => {
    return fetchAPI<Transaction[]>('/api/transactions/all');
  },

  getAll: async (
    skip: number = 0,
    limit: number = 100,
    startDate?: string,
    endDate?: string,
    sortBy?: string,
    sortDirection?: 'asc' | 'desc',
    unclassifiedOnly?: boolean,
    filterNom?: string,
    filterLevel1?: string,
    filterLevel2?: string,
    filterLevel3?: string,
    filterQuantiteMin?: number,
    filterQuantiteMax?: number,
    filterSoldeMin?: number,
    filterSoldeMax?: number
  ): Promise<TransactionListResponse> => {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (sortBy) params.append('sort_by', sortBy);
    if (sortDirection) params.append('sort_direction', sortDirection);
    if (unclassifiedOnly) params.append('unclassified_only', 'true');
    if (filterNom) params.append('filter_nom', filterNom);
    if (filterLevel1) params.append('filter_level_1', filterLevel1);
    if (filterLevel2) params.append('filter_level_2', filterLevel2);
    if (filterLevel3) params.append('filter_level_3', filterLevel3);
    if (filterQuantiteMin !== undefined) params.append('filter_quantite_min', filterQuantiteMin.toString());
    if (filterQuantiteMax !== undefined) params.append('filter_quantite_max', filterQuantiteMax.toString());
    if (filterSoldeMin !== undefined) params.append('filter_solde_min', filterSoldeMin.toString());
    if (filterSoldeMax !== undefined) params.append('filter_solde_max', filterSoldeMax.toString());
    return fetchAPI<TransactionListResponse>(`/api/transactions?${params}`);
  },

  getById: async (id: number): Promise<Transaction> => {
    return fetchAPI<Transaction>(`/api/transactions/${id}`);
  },

  create: async (data: TransactionCreate): Promise<Transaction> => {
    return fetchAPI<Transaction>('/api/transactions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update: async (id: number, data: TransactionUpdate): Promise<Transaction> => {
    console.log('📤 [API] Appel PUT /api/transactions/' + id, data);
    try {
      const result = await fetchAPI<Transaction>(`/api/transactions/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      });
      console.log('✅ [API] Transaction mise à jour:', result);
      return result;
    } catch (error) {
      console.error('❌ [API] Erreur lors de la mise à jour:', error);
      throw error;
    }
  },

  delete: async (id: number): Promise<void> => {
    return fetchAPI<void>(`/api/transactions/${id}`, {
      method: 'DELETE',
    });
  },

  /**
   * Récupérer les valeurs uniques d'une colonne pour les filtres
   */
  getUniqueValues: async (
    column: string,
    startDate?: string,
    endDate?: string,
    filterLevel2?: string
  ): Promise<{ column: string; values: string[] }> => {
    const params = new URLSearchParams({
      column,
    });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (filterLevel2) params.append('filter_level_2', filterLevel2);
    
    return fetchAPI<{ column: string; values: string[] }>(`/api/transactions/unique-values?${params}`);
  },
};

/**
 * Re-enrichment response
 */
export interface ReEnrichResponse {
  enriched_count: number;
  already_enriched_count: number;
  total_processed: number;
  message: string;
}

/**
 * Enrichment API
 */
export const enrichmentAPI = {
  /**
   * Mettre à jour les classifications d'une transaction
   */
  updateClassifications: async (
    transactionId: number,
    level_1?: string | null,
    level_2?: string | null,
    level_3?: string | null
  ): Promise<Transaction> => {
    const params = new URLSearchParams();
    if (level_1 !== undefined && level_1 !== null) params.append('level_1', level_1);
    if (level_2 !== undefined && level_2 !== null) params.append('level_2', level_2);
    if (level_3 !== undefined && level_3 !== null) params.append('level_3', level_3);
    
    return fetchAPI<Transaction>(`/api/enrichment/transactions/${transactionId}?${params.toString()}`, {
      method: 'PUT',
    });
  },

  /**
   * Re-enrichir toutes les transactions avec les mappings disponibles
   */
  reEnrichAll: async (): Promise<ReEnrichResponse> => {
    return fetchAPI<ReEnrichResponse>('/api/enrichment/re-enrich', {
      method: 'POST',
    });
  },
};

// File upload types
export interface ColumnMapping {
  file_column: string;
  db_column: string;
}

export interface FilePreviewResponse {
  filename: string;
  encoding: string;
  separator: string;
  total_rows: number;
  column_mapping: ColumnMapping[];
  preview: Array<Record<string, any>>;
  validation_errors: string[];
  stats: {
    total_rows: number;
    valid_rows: number;
    date_min?: string;
    date_max?: string;
  };
}

export interface TransactionError {
  line_number: number;
  date?: string;
  quantite?: number;
  nom?: string;
  error_message: string;
}

export interface FileImportResponse {
  filename: string;
  imported_count: number;
  duplicates_count: number;
  errors_count: number;
  duplicates: Array<{
    date: string;
    quantite: number;
    nom: string;
    existing_id: number;
  }>;
  errors: TransactionError[];
  period_start?: string;
  period_end?: string;
  message: string;
}

/**
 * File upload API
 */
// Mapping types
export interface Mapping {
  id: number;
  nom: string;
  level_1: string;
  level_2: string;
  level_3?: string;
  is_prefix_match: boolean;
  priority: number;
  created_at: string;
  updated_at: string;
}

export interface MappingCreate {
  nom: string;
  level_1: string;
  level_2: string;
  level_3?: string;
  is_prefix_match?: boolean;
  priority?: number;
}

export interface MappingUpdate {
  nom?: string;
  level_1?: string;
  level_2?: string;
  level_3?: string;
  is_prefix_match?: boolean;
  priority?: number;
}

export interface MappingListResponse {
  mappings: Mapping[];
  total: number;
}

// Mapping import types
export interface MappingPreviewResponse {
  filename: string;
  total_rows: number;
  column_mapping: ColumnMapping[];
  preview: Array<Record<string, any>>;
  validation_errors: string[];
  stats: {
    total_rows: number;
    detected_columns: number;
    required_columns_detected: number;
  };
}

export interface MappingError {
  line_number: number;
  nom?: string;
  level_1?: string;
  level_2?: string;
  level_3?: string;
  error_message: string;
}

export interface DuplicateMapping {
  nom: string;
  existing_id: number;
}

export interface MappingImportResponse {
  filename: string;
  imported_count: number;
  duplicates_count: number;
  errors_count: number;
  duplicates: DuplicateMapping[];
  errors: MappingError[];
  message: string;
}

export interface MappingImportHistory {
  id: number;
  filename: string;
  imported_at: string;
  imported_count: number;
  duplicates_count: number;
  errors_count: number;
}

// Mapping API
// Allowed mappings API (Step 8.1)
export interface AllowedLevel1Response {
  values: string[];
}

export interface AllowedLevel2Response {
  values: string[];
}

export interface AllowedLevel3Response {
  values: string[];
}

// AllowedMapping interfaces (Step 8.7)
export interface AllowedMapping {
  id: number;
  level_1: string;
  level_2: string;
  level_3: string | null;
  created_at: string;
  updated_at: string;
}

export interface AllowedMappingCreate {
  level_1: string;
  level_2: string;
  level_3?: string | null;
}

export interface AllowedMappingListResponse {
  mappings: AllowedMapping[];
  total: number;
}

export const allowedMappingsAPI = {
  /**
   * Récupère toutes les valeurs level_1 autorisées
   */
  async getAllowedLevel1(): Promise<string[]> {
    const response = await fetchAPI<AllowedLevel1Response>('/api/mappings/allowed-level1');
    return response.values;
  },

  /**
   * Récupère les valeurs level_2 autorisées.
   * Si level_1 est fourni, retourne uniquement les level_2 pour ce level_1.
   * Sinon, retourne toutes les valeurs level_2 disponibles.
   */
  async getAllowedLevel2(level_1?: string): Promise<string[]> {
    const url = level_1 
      ? `/api/mappings/allowed-level2?level_1=${encodeURIComponent(level_1)}`
      : `/api/mappings/allowed-level2`;
    const response = await fetchAPI<AllowedLevel2Response>(url);
    return response.values;
  },

  /**
   * Récupère les valeurs level_3 autorisées.
   * Si level_1 et level_2 sont fournis, retourne uniquement les level_3 pour ce couple.
   * Sinon, retourne toutes les valeurs level_3 disponibles.
   */
  async getAllowedLevel3(level_1?: string, level_2?: string): Promise<string[]> {
    const url = (level_1 && level_2)
      ? `/api/mappings/allowed-level3?level_1=${encodeURIComponent(level_1)}&level_2=${encodeURIComponent(level_2)}`
      : `/api/mappings/allowed-level3`;
    const response = await fetchAPI<AllowedLevel3Response>(url);
    return response.values;
  },

  /**
   * Récupère les valeurs level_2 autorisées pour un level_3 donné (filtrage ascendant)
   */
  async getAllowedLevel2ForLevel3(level_3: string): Promise<string[]> {
    const response = await fetchAPI<AllowedLevel2Response>(`/api/mappings/allowed-level2-for-level3?level_3=${encodeURIComponent(level_3)}`);
    return response.values;
  },

  /**
   * Récupère les valeurs level_1 autorisées pour un level_2 donné (filtrage ascendant)
   */
  async getAllowedLevel1ForLevel2(level_2: string): Promise<string[]> {
    const response = await fetchAPI<AllowedLevel1Response>(`/api/mappings/allowed-level1-for-level2?level_2=${encodeURIComponent(level_2)}`);
    return response.values;
  },

  /**
   * Récupère les valeurs level_1 autorisées pour un couple (level_2, level_3) donné (filtrage ascendant)
   */
  async getAllowedLevel1ForLevel2AndLevel3(level_2: string, level_3: string): Promise<string[]> {
    const response = await fetchAPI<AllowedLevel1Response>(`/api/mappings/allowed-level1-for-level2-and-level3?level_2=${encodeURIComponent(level_2)}&level_3=${encodeURIComponent(level_3)}`);
    return response.values;
  },

  /**
   * Récupère la combinaison unique (level_2, level_3) pour un level_1 donné
   */
  async getUniqueCombinationForLevel1(level_1: string): Promise<{ level_2: string | null; level_3: string | null }> {
    return fetchAPI<{ level_2: string | null; level_3: string | null }>(`/api/mappings/unique-combination-for-level1?level_1=${encodeURIComponent(level_1)}`);
  },

  /**
   * Récupère la combinaison unique (level_1, level_3) pour un level_2 donné
   */
  async getUniqueCombinationForLevel2(level_2: string): Promise<{ level_1: string | null; level_3: string | null }> {
    return fetchAPI<{ level_1: string | null; level_3: string | null }>(`/api/mappings/unique-combination-for-level2?level_2=${encodeURIComponent(level_2)}`);
  },

  /**
   * Récupère toutes les valeurs level_1 autorisées associées à au moins un des level_3 de la liste (Step 9.3)
   */
  async getAllowedLevel1ForLevel3List(level_3_list: string[]): Promise<string[]> {
    if (level_3_list.length === 0) {
      return [];
    }
    const level_3_list_str = level_3_list.join(',');
    const response = await fetchAPI<AllowedLevel1Response>(`/api/mappings/allowed-level1-for-level3-list?level_3_list=${encodeURIComponent(level_3_list_str)}`);
    return response.values;
  },
  
  /**
   * Récupère tous les mappings autorisés (Step 8.7)
   */
  async getAllowedMappings(skip: number = 0, limit: number = 100, filters?: {
    level_1?: string;
    level_2?: string;
    level_3?: string;
  }): Promise<{ mappings: AllowedMapping[]; total: number }> {
    const params = new URLSearchParams();
    params.append('skip', skip.toString());
    params.append('limit', limit.toString());
    if (filters?.level_1) params.append('level_1', filters.level_1);
    if (filters?.level_2) params.append('level_2', filters.level_2);
    if (filters?.level_3) params.append('level_3', filters.level_3);
    return fetchAPI<{ mappings: AllowedMapping[]; total: number }>(`/api/mappings/allowed?${params.toString()}`);
  },
  
  /**
   * Crée un nouveau mapping autorisé (Step 8.7)
   */
  async createAllowedMapping(mapping: AllowedMappingCreate): Promise<AllowedMapping> {
    return fetchAPI<AllowedMapping>('/api/mappings/allowed', {
      method: 'POST',
      body: JSON.stringify(mapping),
    });
  },
  
  /**
   * Supprime un mapping autorisé (Step 8.7)
   */
  async deleteAllowedMapping(mappingId: number): Promise<void> {
    return fetchAPI<void>(`/api/mappings/allowed/${mappingId}`, {
      method: 'DELETE',
    });
  },
  
  /**
   * Réinitialise les mappings autorisés depuis le fichier Excel par défaut (Step 8.7)
   */
  async resetAllowedMappings(): Promise<{
    deleted_count: number;
    inserted_count: number;
    error_count: number;
    total_count: number;
    invalid_mappings_deleted: number;
    transactions_reset: number;
    message: string;
  }> {
    return fetchAPI<{
      deleted_count: number;
      inserted_count: number;
      error_count: number;
      total_count: number;
      invalid_mappings_deleted: number;
      transactions_reset: number;
      message: string;
    }>('/api/mappings/allowed/reset', {
      method: 'POST',
    });
  },
};

export const mappingsAPI = {
  /**
   * Récupérer tous les mappings (sans pagination)
   * Utilisé pour l'export Excel
   */
  async getAll(): Promise<Mapping[]> {
    return fetchAPI<Mapping[]>('/api/mappings/all');
  },

  /**
   * Récupérer la liste des mappings
   */
  async list(
    skip: number = 0,
    limit: number = 100,
    search?: string,
    sortBy?: string,
    sortDirection?: 'asc' | 'desc',
    filterNom?: string,
    filterLevel1?: string,
    filterLevel2?: string,
    filterLevel3?: string
  ): Promise<MappingListResponse> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });
    if (search) {
      params.append('search', search);
    }
    if (sortBy) params.append('sort_by', sortBy);
    if (sortDirection) params.append('sort_direction', sortDirection);
    if (filterNom) params.append('filter_nom', filterNom);
    if (filterLevel1) params.append('filter_level_1', filterLevel1);
    if (filterLevel2) params.append('filter_level_2', filterLevel2);
    if (filterLevel3) params.append('filter_level_3', filterLevel3);
    return fetchAPI<MappingListResponse>(`/api/mappings?${params.toString()}`);
  },

  /**
   * Récupérer un mapping par ID
   */
  async get(id: number): Promise<Mapping> {
    return fetchAPI<Mapping>(`/api/mappings/${id}`);
  },

  /**
   * Créer un nouveau mapping
   */
  async create(mapping: MappingCreate): Promise<Mapping> {
    return fetchAPI<Mapping>('/api/mappings', {
      method: 'POST',
      body: JSON.stringify(mapping),
    });
  },

  /**
   * Modifier un mapping
   */
  async update(id: number, mapping: MappingUpdate): Promise<Mapping> {
    return fetchAPI<Mapping>(`/api/mappings/${id}`, {
      method: 'PUT',
      body: JSON.stringify(mapping),
    });
  },

  /**
   * Supprimer un mapping
   */
  async delete(id: number): Promise<void> {
    return fetchAPI<void>(`/api/mappings/${id}`, {
      method: 'DELETE',
    });
  },

  /**
   * Récupérer les combinaisons possibles pour les dropdowns intelligents
   */
  async getCombinations(level_1?: string, level_2?: string, all_level_2?: boolean, all_level_3?: boolean): Promise<{
    level_1?: string[];
    level_2?: string[];
    level_3?: string[];
  }> {
    const params = new URLSearchParams();
    if (level_1) params.append('level_1', level_1);
    if (level_2) params.append('level_2', level_2);
    if (all_level_2) params.append('all_level_2', 'true');
    if (all_level_3) params.append('all_level_3', 'true');
    return fetchAPI<{ level_1?: string[]; level_2?: string[]; level_3?: string[] }>(
      `/api/mappings/combinations?${params.toString()}`
    );
  },

  /**
   * Prévisualiser un fichier Excel de mappings
   */
  preview: async (file: File): Promise<MappingPreviewResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const url = `${API_BASE_URL}/api/mappings/preview`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  },

  /**
   * Importer un fichier Excel de mappings
   */
  import: async (file: File, mapping: ColumnMapping[]): Promise<MappingImportResponse> => {
    console.log('📤 [API] Appel POST /api/mappings/import');
    console.log('📤 [API] Fichier:', file.name);
    console.log('📤 [API] Mapping:', mapping);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mapping', JSON.stringify(mapping));
    
    const url = `${API_BASE_URL}/api/mappings/import`;
    console.log('📤 [API] URL:', url);
    
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    console.log('📥 [API] Réponse status:', response.status, response.statusText);

    if (!response.ok) {
      let errorMessage = `HTTP error! status: ${response.status}`;
      try {
        const error = await response.json();
        console.error('❌ [API] Erreur API:', error);
        errorMessage = error.detail || error.message || error.error || JSON.stringify(error) || errorMessage;
      } catch (e) {
        // Si la réponse n'est pas du JSON, essayer de lire le texte
        try {
          const text = await response.text();
          errorMessage = text || errorMessage;
        } catch (textError) {
          console.error('❌ [API] Impossible de lire la réponse d\'erreur:', textError);
        }
      }
      throw new Error(errorMessage);
    }

    const result = await response.json();
    console.log('✅ [API] Import réussi:', result);
    return result;
  },

  /**
   * Récupérer l'historique des imports de mappings
   */
  getImportsHistory: async (): Promise<MappingImportHistory[]> => {
    return fetchAPI<MappingImportHistory[]>('/api/mappings/imports');
  },

  /**
   * Supprimer un import de mapping de l'historique
   */
  deleteImport: async (importId: number): Promise<void> => {
    return fetchAPI<void>(`/api/mappings/imports/${importId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Récupérer le nombre total de mappings
   */
  getCount: async (): Promise<{ count: number }> => {
    return fetchAPI<{ count: number }>('/api/mappings/count');
  },

  /**
   * Récupérer les valeurs uniques d'une colonne pour les filtres
   */
  getUniqueValues: async (column: string): Promise<{ column: string; values: string[] }> => {
    const params = new URLSearchParams({
      column,
    });
    
    return fetchAPI<{ column: string; values: string[] }>(`/api/mappings/unique-values?${params}`);
  },

  /**
   * Supprimer tous les imports de mappings de l'historique
   */
  deleteAllImports: async (): Promise<void> => {
    return fetchAPI<void>('/api/mappings/imports', {
      method: 'DELETE',
    });
  },
};

export const fileUploadAPI = {
  preview: async (file: File): Promise<FilePreviewResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const url = `${API_BASE_URL}/api/transactions/preview`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  },

  getImportsHistory: async (): Promise<Array<{
    id: number;
    filename: string;
    imported_at: string;
    imported_count: number;
    duplicates_count: number;
    errors_count: number;
    period_start?: string;
    period_end?: string;
  }>> => {
    return fetchAPI<Array<{
      id: number;
      filename: string;
      imported_at: string;
      imported_count: number;
      duplicates_count: number;
      errors_count: number;
      period_start?: string;
      period_end?: string;
    }>>('/api/transactions/imports');
  },

  deleteAllImports: async (): Promise<void> => {
    return fetchAPI<void>('/api/transactions/imports', {
      method: 'DELETE',
    });
  },

  import: async (file: File, mapping: ColumnMapping[]): Promise<FileImportResponse> => {
    console.log('📤 [API] Appel POST /api/transactions/import');
    console.log('📤 [API] Fichier:', file.name);
    console.log('📤 [API] Mapping:', mapping);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mapping', JSON.stringify(mapping));
    
    const url = `${API_BASE_URL}/api/transactions/import`;
    console.log('📤 [API] URL:', url);
    
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    console.log('📥 [API] Réponse status:', response.status, response.statusText);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      console.error('❌ [API] Erreur API:', error);
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    console.log('✅ [API] Import réussi:', result);
    return result;
  },
};

// Analytics API Types
export interface PivotData {
  rows: (string | number | (string | number)[])[];
  columns: (string | number | (string | number)[])[];
  data: Record<string, Record<string, number>>;
  row_totals: Record<string, number>;
  column_totals: Record<string, number>;
  grand_total: number;
  row_fields: string[];
  column_fields: string[];
}

export interface PivotDetailsParams {
  rows?: string;
  columns?: string;
  row_values?: string; // JSON array string
  column_values?: string; // JSON array string
  filters?: string; // JSON object string
  sort_by?: string; // Colonne de tri (date, quantite, nom, solde, level_1, level_2, level_3)
  sort_direction?: string; // Direction du tri (asc, desc)
}

export const analyticsAPI = {
  /**
   * Récupère les données du tableau croisé dynamique
   */
  getPivot: async (
    rows?: string[],
    columns?: string[],
    dataField: string = 'quantite',
    dataOperation: string = 'sum',
    filters?: Record<string, any>
  ): Promise<PivotData> => {
    const params = new URLSearchParams();
    
    if (rows && rows.length > 0) {
      params.append('rows', rows.join(','));
    }
    if (columns && columns.length > 0) {
      params.append('columns', columns.join(','));
    }
    params.append('data_field', dataField);
    params.append('data_operation', dataOperation);
    
    if (filters && Object.keys(filters).length > 0) {
      params.append('filters', JSON.stringify(filters));
    }
    
    return fetchAPI<PivotData>(`/api/analytics/pivot?${params.toString()}`);
  },

  /**
   * Récupère les transactions détaillées d'une cellule du tableau croisé
   */
  getPivotDetails: async (
    params: PivotDetailsParams,
    skip: number = 0,
    limit: number = 100
  ): Promise<TransactionListResponse> => {
    const queryParams = new URLSearchParams();
    
    if (params.rows) {
      queryParams.append('rows', params.rows);
    }
    if (params.columns) {
      queryParams.append('columns', params.columns);
    }
    if (params.row_values) {
      queryParams.append('row_values', params.row_values);
    }
    if (params.column_values) {
      queryParams.append('column_values', params.column_values);
    }
    if (params.filters) {
      queryParams.append('filters', params.filters);
    }
    if (params.sort_by) {
      queryParams.append('sort_by', params.sort_by);
    }
    if (params.sort_direction) {
      queryParams.append('sort_direction', params.sort_direction);
    }
    queryParams.append('skip', skip.toString());
    queryParams.append('limit', limit.toString());
    
    return fetchAPI<TransactionListResponse>(`/api/analytics/pivot/details?${queryParams.toString()}`);
  },
};

// ============================================================================
// Pivot Configs API
// ============================================================================

export interface PivotConfigResponse {
  id: number;
  name: string;
  config: {
    rows: string[];
    columns: string[];
    data: string[];
    filters: Record<string, any>;
  };
  created_at: string;
  updated_at: string;
}

export interface PivotConfigListResponse {
  items: PivotConfigResponse[];
  total: number;
}

export interface PivotConfigCreate {
  name: string;
  config: {
    rows: string[];
    columns: string[];
    data: string[];
    filters: Record<string, any>;
  };
}

export interface PivotConfigUpdate {
  name?: string;
  config?: {
    rows: string[];
    columns: string[];
    data: string[];
    filters: Record<string, any>;
  };
}

export const pivotConfigsAPI = {
  /**
   * Liste tous les tableaux croisés sauvegardés
   */
  getAll: async (skip: number = 0, limit: number = 100): Promise<PivotConfigListResponse> => {
    return fetchAPI<PivotConfigListResponse>(`/api/pivot-configs?skip=${skip}&limit=${limit}`);
  },

  /**
   * Récupère un tableau croisé par ID
   */
  getById: async (id: number): Promise<PivotConfigResponse> => {
    return fetchAPI<PivotConfigResponse>(`/api/pivot-configs/${id}`);
  },

  /**
   * Crée un nouveau tableau croisé
   */
  create: async (data: PivotConfigCreate): Promise<PivotConfigResponse> => {
    return fetchAPI<PivotConfigResponse>('/api/pivot-configs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },

  /**
   * Met à jour un tableau croisé
   */
  update: async (id: number, data: PivotConfigUpdate): Promise<PivotConfigResponse> => {
    return fetchAPI<PivotConfigResponse>(`/api/pivot-configs/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },

  /**
   * Supprime un tableau croisé
   */
  delete: async (id: number): Promise<void> => {
    return fetchAPI<void>(`/api/pivot-configs/${id}`, {
      method: 'DELETE',
    });
  },
};


// Amortization API

export interface AmortizationConfig {
  level_2_value: string;
  level_3_mapping: {
    part_terrain: string[];
    structure_go: string[];
    mobilier: string[];
    igt: string[];
    agencements: string[];
    facade_toiture: string[];
    travaux: string[];
  };
  duration_part_terrain: number;
  duration_structure_go: number;
  duration_mobilier: number;
  duration_igt: number;
  duration_agencements: number;
  duration_facade_toiture: number;
  duration_travaux: number;
}

export interface AmortizationConfigResponse extends AmortizationConfig {
  id: number;
  created_at: string;
  updated_at: string;
}

export interface AmortizationResultsResponse {
  results: Record<number, Record<string, number>>;
  totals_by_year: Record<number, number>;
  totals_by_category: Record<string, number>;
  grand_total: number;
}

export interface AmortizationAggregatedResponse {
  categories: string[];
  years: number[];
  data: number[][];
  row_totals: number[];
  column_totals: number[];
  grand_total: number;
}

export interface AmortizationRecalculateResponse {
  message: string;
  transactions_processed: number;
}

export interface AmortizationType {
  id: number;
  name: string;
  level_2_value: string;
  level_1_values: string[];
  start_date: string | null;
  duration: number;
  annual_amount: number | null;
  created_at: string;
  updated_at: string;
}

export interface AmortizationTypeListResponse {
  types: AmortizationType[];
  total: number;
}

export interface AmortizationTypeCreate {
  name: string;
  level_2_value: string;
  level_1_values: string[];
  start_date?: string | null;
  duration: number;
  annual_amount?: number | null;
}

export interface AmortizationTypeUpdate {
  name?: string;
  level_2_value?: string;
  level_1_values?: string[];
  start_date?: string | null;
  duration?: number;
  annual_amount?: number | null;
}

export const amortizationAPI = {
  /**
   * Récupère la configuration des amortissements
   */
  getConfig: async (): Promise<AmortizationConfigResponse> => {
    return fetchAPI<AmortizationConfigResponse>('/api/amortization/config');
  },

  /**
   * Met à jour la configuration des amortissements
   */
  updateConfig: async (config: AmortizationConfig): Promise<AmortizationConfigResponse> => {
    return fetchAPI<AmortizationConfigResponse>('/api/amortization/config', {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  },

  /**
   * Récupère les résultats d'amortissements agrégés
   */
  getResults: async (): Promise<AmortizationResultsResponse> => {
    return fetchAPI<AmortizationResultsResponse>('/api/amortization/results');
  },

  /**
   * Récupère les résultats d'amortissements sous forme de tableau croisé
   */
  getResultsAggregated: async (): Promise<AmortizationAggregatedResponse> => {
    return fetchAPI<AmortizationAggregatedResponse>('/api/amortization/results/aggregated');
  },

  /**
   * Récupère les transactions détaillées pour un drill-down
   */
  getResultsDetails: async (
    year?: number,
    category?: string,
    skip: number = 0,
    limit: number = 100
  ): Promise<TransactionListResponse> => {
    const params = new URLSearchParams();
    if (year !== undefined) params.append('year', year.toString());
    if (category) params.append('category', category);
    params.append('skip', skip.toString());
    params.append('limit', limit.toString());
    
    return fetchAPI<TransactionListResponse>(`/api/amortization/results/details?${params.toString()}`);
  },

  /**
   * Force le recalcul complet de tous les amortissements
   */
  recalculate: async (): Promise<AmortizationRecalculateResponse> => {
    return fetchAPI<AmortizationRecalculateResponse>('/api/amortization/recalculate', {
      method: 'POST',
    });
  },

  /**
   * Supprime tous les résultats d'amortissement
   */
  deleteAllResults: async (): Promise<{ message: string; deleted_count: number }> => {
    return fetchAPI<{ message: string; deleted_count: number }>('/api/amortization/results', {
      method: 'DELETE',
    });
  },
};

/**
 * Amortization Types API
 */
export const amortizationTypesAPI = {
  /**
   * Récupère tous les types d'amortissement
   */
  getAll: async (): Promise<AmortizationTypeListResponse> => {
    return fetchAPI<AmortizationTypeListResponse>('/api/amortization/types');
  },

  /**
   * Récupère un type d'amortissement par ID
   */
  getById: async (id: number): Promise<AmortizationType> => {
    return fetchAPI<AmortizationType>(`/api/amortization/types/${id}`);
  },

  /**
   * Crée un nouveau type d'amortissement
   */
  create: async (type: AmortizationTypeCreate): Promise<AmortizationType> => {
    return fetchAPI<AmortizationType>('/api/amortization/types', {
      method: 'POST',
      body: JSON.stringify(type),
    });
  },

  /**
   * Met à jour un type d'amortissement
   */
  update: async (id: number, type: AmortizationTypeUpdate): Promise<AmortizationType> => {
    return fetchAPI<AmortizationType>(`/api/amortization/types/${id}`, {
      method: 'PUT',
      body: JSON.stringify(type),
    });
  },

  /**
   * Supprime un type d'amortissement
   */
  delete: async (id: number): Promise<void> => {
    return fetchAPI<void>(`/api/amortization/types/${id}`, {
      method: 'DELETE',
    });
  },

  /**
   * Calcule le montant d'immobilisation pour un type
   */
  getAmount: async (id: number): Promise<{ type_id: number; type_name: string; amount: number }> => {
    return fetchAPI<{ type_id: number; type_name: string; amount: number }>(`/api/amortization/types/${id}/amount`);
  },

  /**
   * Calcule le montant cumulé pour un type
   */
  getCumulated: async (id: number): Promise<{ type_id: number; type_name: string; cumulated_amount: number }> => {
    return fetchAPI<{ type_id: number; type_name: string; cumulated_amount: number }>(`/api/amortization/types/${id}/cumulated`);
  },

  /**
   * Compte le nombre de transactions pour un type
   */
  getTransactionCount: async (id: number): Promise<{ type_id: number; type_name: string; transaction_count: number }> => {
    return fetchAPI<{ type_id: number; type_name: string; transaction_count: number }>(`/api/amortization/types/${id}/transaction-count`);
  },
};

// Amortization Views API

export interface AmortizationView {
  id: number;
  name: string;
  level_2_value: string;
  view_data: {
    level_2_value: string;
    amortization_types: Array<{
      name: string;
      level_1_values: string[];
      start_date: string | null;
      duration: number;
      annual_amount: number | null;
    }>;
  };
  created_at: string;
  updated_at: string;
}

export interface AmortizationViewListResponse {
  views: AmortizationView[];
  total: number;
}

export interface AmortizationViewCreate {
  name: string;
  level_2_value: string;
  view_data: {
    level_2_value: string;
    amortization_types: Array<{
      name: string;
      level_1_values: string[];
      start_date: string | null;
      duration: number;
      annual_amount: number | null;
    }>;
  };
}

export interface AmortizationViewUpdate {
  name?: string;
  view_data?: {
    level_2_value: string;
    amortization_types: Array<{
      name: string;
      level_1_values: string[];
      start_date: string | null;
      duration: number;
      annual_amount: number | null;
    }>;
  };
}

export const amortizationViewsAPI = {
  /**
   * Récupère toutes les vues d'amortissement (optionnellement filtrées par Level 2)
   */
  getAll: async (level2Value?: string): Promise<AmortizationViewListResponse> => {
    const url = level2Value 
      ? `/api/amortization/views?level_2_value=${encodeURIComponent(level2Value)}`
      : '/api/amortization/views';
    return fetchAPI<AmortizationViewListResponse>(url);
  },

  /**
   * Récupère une vue d'amortissement par ID
   */
  getById: async (id: number): Promise<AmortizationView> => {
    return fetchAPI<AmortizationView>(`/api/amortization/views/${id}`);
  },

  /**
   * Crée une nouvelle vue d'amortissement
   */
  create: async (data: AmortizationViewCreate): Promise<AmortizationView> => {
    return fetchAPI<AmortizationView>('/api/amortization/views', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },

  /**
   * Met à jour une vue d'amortissement (renommage ou données)
   */
  update: async (id: number, data: AmortizationViewUpdate): Promise<AmortizationView> => {
    return fetchAPI<AmortizationView>(`/api/amortization/views/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },

  /**
   * Supprime une vue d'amortissement
   */
  delete: async (id: number): Promise<void> => {
    return fetchAPI<void>(`/api/amortization/views/${id}`, {
      method: 'DELETE',
    });
  },
};

// Loan Config API Types
export interface LoanConfig {
  id: number;
  name: string;
  credit_amount: number;
  interest_rate: number;
  duration_years: number;
  initial_deferral_months: number;
  created_at: string;
  updated_at: string;
}

export interface LoanConfigCreate {
  name: string;
  credit_amount: number;
  interest_rate: number;
  duration_years: number;
  initial_deferral_months: number;
}

export interface LoanConfigUpdate {
  name?: string;
  credit_amount?: number;
  interest_rate?: number;
  duration_years?: number;
  initial_deferral_months?: number;
}

export interface LoanConfigListResponse {
  configs: LoanConfig[];
  total: number;
}

export const loanConfigsAPI = {
  getAll: async (): Promise<LoanConfigListResponse> => {
    return fetchAPI<LoanConfigListResponse>('/api/loan-configs');
  },
  getById: async (id: number): Promise<LoanConfig> => {
    return fetchAPI<LoanConfig>(`/api/loan-configs/${id}`);
  },
  create: async (data: LoanConfigCreate): Promise<LoanConfig> => {
    return fetchAPI<LoanConfig>('/api/loan-configs', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  update: async (id: number, data: LoanConfigUpdate): Promise<LoanConfig> => {
    return fetchAPI<LoanConfig>(`/api/loan-configs/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
  delete: async (id: number): Promise<void> => {
    return fetchAPI<void>(`/api/loan-configs/${id}`, {
      method: 'DELETE',
    });
  },
};

// Loan Payment API Types
export interface LoanPayment {
  id: number;
  date: string;
  capital: number;
  interest: number;
  insurance: number;
  total: number;
  loan_name: string;
  created_at: string;
  updated_at: string;
}

export interface LoanPaymentCreate {
  date: string;
  capital: number;
  interest: number;
  insurance: number;
  total: number;
  loan_name?: string;
}

export interface LoanPaymentUpdate {
  date?: string;
  capital?: number;
  interest?: number;
  insurance?: number;
  total?: number;
  loan_name?: string;
}

export interface LoanPaymentListResponse {
  payments: LoanPayment[];
  total: number;
}

export interface LoanPaymentPreviewResponse {
  filename: string;
  total_rows: number;
  detected_years: number[];
  preview: Array<{
    year: number;
    date: string;
    capital: number;
    interest: number;
    insurance: number;
    total: number;
  }>;
  validation_errors: string[];
  warnings: string[];
  stats: Record<string, any>;
  existing_payments_count: number;
}

export interface LoanPaymentImportResponse {
  message: string;
  imported_count: number;
  errors: string[];
  warnings: string[];
}

export const loanPaymentsAPI = {
  getAll: async (params?: {
    skip?: number;
    limit?: number;
    loan_name?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<LoanPaymentListResponse> => {
    const queryParams = new URLSearchParams();
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());
    if (params?.loan_name) queryParams.append('loan_name', params.loan_name);
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    
    const query = queryParams.toString();
    return fetchAPI<LoanPaymentListResponse>(`/api/loan-payments${query ? `?${query}` : ''}`);
  },
  getById: async (id: number): Promise<LoanPayment> => {
    return fetchAPI<LoanPayment>(`/api/loan-payments/${id}`);
  },
  create: async (data: LoanPaymentCreate): Promise<LoanPayment> => {
    return fetchAPI<LoanPayment>('/api/loan-payments', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  update: async (id: number, data: LoanPaymentUpdate): Promise<LoanPayment> => {
    return fetchAPI<LoanPayment>(`/api/loan-payments/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
  delete: async (id: number): Promise<void> => {
    return fetchAPI<void>(`/api/loan-payments/${id}`, {
      method: 'DELETE',
    });
  },
  preview: async (file: File, loan_name: string = 'Prêt principal'): Promise<LoanPaymentPreviewResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    return fetchAPI<LoanPaymentPreviewResponse>(`/api/loan-payments/preview?loan_name=${encodeURIComponent(loan_name)}`, {
      method: 'POST',
      body: formData,
    });
  },
  import: async (file: File, loan_name: string = 'Prêt principal', confirm_replace: boolean = false): Promise<LoanPaymentImportResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    // Le backend attend confirm_replace comme query param
    const queryParams = new URLSearchParams();
    queryParams.append('loan_name', loan_name);
    if (confirm_replace) {
      queryParams.append('confirm_replace', 'true');
    }
    
    return fetchAPI<LoanPaymentImportResponse>(`/api/loan-payments/import?${queryParams.toString()}`, {
      method: 'POST',
      body: formData,
    });
  },
};

// Compte de résultat API
export interface CompteResultatMapping {
  id: number;
  category_name: string;
  level_1_values: string[] | null;
  level_2_values: string[];
  level_3_values: string[] | null;
  amortization_view_id: number | null;
  selected_loan_ids: number[] | null;
  created_at: string;
  updated_at: string;
}

export interface CompteResultatMappingListResponse {
  mappings: CompteResultatMapping[];
  total: number;
}

export interface CompteResultatMappingCreate {
  category_name: string;
  level_1_values?: string[] | null;
  level_2_values: string[];
  level_3_values?: string[] | null;
  amortization_view_id?: number | null;
  selected_loan_ids?: number[] | null;
}

export interface CompteResultatMappingUpdate {
  category_name?: string;
  level_1_values?: string[] | null;
  level_2_values?: string[] | null;
  level_3_values?: string[] | null;
  amortization_view_id?: number | null;
  selected_loan_ids?: number[] | null;
}

export const compteResultatAPI = {
  getMappings: async (): Promise<CompteResultatMappingListResponse> => {
    return fetchAPI<CompteResultatMappingListResponse>('/api/compte-resultat/mappings');
  },
  getMapping: async (id: number): Promise<CompteResultatMapping> => {
    return fetchAPI<CompteResultatMapping>(`/api/compte-resultat/mappings/${id}`);
  },
  createMapping: async (data: CompteResultatMappingCreate): Promise<CompteResultatMapping> => {
    return fetchAPI<CompteResultatMapping>('/api/compte-resultat/mappings', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  updateMapping: async (id: number, data: CompteResultatMappingUpdate): Promise<CompteResultatMapping> => {
    return fetchAPI<CompteResultatMapping>(`/api/compte-resultat/mappings/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
  deleteMapping: async (id: number): Promise<void> => {
    return fetchAPI<void>(`/api/compte-resultat/mappings/${id}`, {
      method: 'DELETE',
    });
  },
  calculateAmounts: async (years: number[]): Promise<Record<string, Record<string, number>>> => {
    const yearsParam = years.join(',');
    return fetchAPI<Record<string, Record<string, number>>>(`/api/compte-resultat/calculate?years=${yearsParam}`);
  },
};

// Compte de résultat mapping views API
export interface CompteResultatMappingView {
  id: number;
  name: string;
  view_data: {
    mappings: CompteResultatMapping[];
  };
  created_at: string;
  updated_at: string;
}

export interface CompteResultatMappingViewListResponse {
  views: CompteResultatMappingView[];
  total: number;
}

export interface CompteResultatMappingViewCreate {
  name: string;
  view_data: {
    mappings: CompteResultatMapping[];
  };
}

export interface CompteResultatMappingViewUpdate {
  name?: string;
  view_data?: {
    mappings: CompteResultatMapping[];
  };
}

export const compteResultatMappingViewsAPI = {
  getAll: async (): Promise<CompteResultatMappingViewListResponse> => {
    return fetchAPI<CompteResultatMappingViewListResponse>('/api/compte-resultat/mapping-views');
  },
  getById: async (id: number): Promise<CompteResultatMappingView> => {
    return fetchAPI<CompteResultatMappingView>(`/api/compte-resultat/mapping-views/${id}`);
  },
  create: async (data: CompteResultatMappingViewCreate): Promise<CompteResultatMappingView> => {
    return fetchAPI<CompteResultatMappingView>('/api/compte-resultat/mapping-views', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  update: async (id: number, data: CompteResultatMappingViewUpdate): Promise<CompteResultatMappingView> => {
    return fetchAPI<CompteResultatMappingView>(`/api/compte-resultat/mapping-views/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
  delete: async (id: number): Promise<void> => {
    return fetchAPI<void>(`/api/compte-resultat/mapping-views/${id}`, {
      method: 'DELETE',
    });
  },
};

// Bilan API Types
export interface BilanMapping {
  id: number;
  category_name: string;
  level_1_values: string[] | null;
  type: string; // "ACTIF" ou "PASSIF"
  sub_category: string;
  is_special: boolean;
  special_source: string | null;
  amortization_view_id: number | null;
  compte_resultat_view_id: number | null; // Step 10.8.4.3
  created_at: string;
  updated_at: string;
}

export interface BilanMappingListResponse {
  mappings: BilanMapping[];
  total: number;
}

export interface BilanMappingCreate {
  category_name: string;
  level_1_values?: string[] | null;
  type: string;
  sub_category: string;
  is_special?: boolean;
  special_source?: string | null;
  amortization_view_id?: number | null;
  compte_resultat_view_id?: number | null; // Step 10.8.4.3
}

export interface BilanMappingUpdate {
  category_name?: string;
  level_1_values?: string[] | null;
  type?: string;
  sub_category?: string;
  is_special?: boolean;
  special_source?: string | null;
  amortization_view_id?: number | null;
  compte_resultat_view_id?: number | null; // Step 10.8.4.3
}

export interface BilanData {
  id: number;
  annee: number;
  category_name: string;
  amount: number;
  created_at: string;
  updated_at: string;
}

export interface BilanDataListResponse {
  data: BilanData[];
  total: number;
}

export interface BilanCategoryItem {
  category_name: string;
  amount: number;
}

export interface BilanSubCategoryItem {
  sub_category: string;
  total: number;
  categories: BilanCategoryItem[];
}

export interface BilanTypeItem {
  type: string;
  total: number;
  sub_categories: BilanSubCategoryItem[];
}

export interface BilanResponse {
  year: number;
  types: BilanTypeItem[];
  equilibre: {
    actif: number;
    passif: number;
    difference: number;
    percentage: number;
  };
}

export interface BilanGenerateRequest {
  year: number;
  selected_level_3_values?: string[] | null;
}

export const bilanAPI = {
  getMappings: async (): Promise<BilanMappingListResponse> => {
    return fetchAPI<BilanMappingListResponse>('/api/bilan/mappings');
  },
  getMapping: async (id: number): Promise<BilanMapping> => {
    return fetchAPI<BilanMapping>(`/api/bilan/mappings/${id}`);
  },
  createMapping: async (data: BilanMappingCreate): Promise<BilanMapping> => {
    return fetchAPI<BilanMapping>('/api/bilan/mappings', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  updateMapping: async (id: number, data: BilanMappingUpdate): Promise<BilanMapping> => {
    return fetchAPI<BilanMapping>(`/api/bilan/mappings/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
  deleteMapping: async (id: number): Promise<void> => {
    return fetchAPI<void>(`/api/bilan/mappings/${id}`, {
      method: 'DELETE',
    });
  },
  generate: async (year: number, selected_level_3_values?: string[] | null): Promise<BilanResponse> => {
    return fetchAPI<BilanResponse>('/api/bilan/generate', {
      method: 'POST',
      body: JSON.stringify({
        year,
        selected_level_3_values: selected_level_3_values || null,
      }),
    });
  },
  getBilan: async (params?: {
    year?: number;
    start_year?: number;
    end_year?: number;
  }): Promise<BilanDataListResponse> => {
    const queryParams = new URLSearchParams();
    if (params?.year !== undefined) queryParams.append('year', params.year.toString());
    if (params?.start_year !== undefined) queryParams.append('start_year', params.start_year.toString());
    if (params?.end_year !== undefined) queryParams.append('end_year', params.end_year.toString());
    
    const query = queryParams.toString();
    return fetchAPI<BilanDataListResponse>(`/api/bilan${query ? `?${query}` : ''}`);
  },
  calculateAmounts: async (
    years: number[],
    selectedLevel3Values?: string[] | null
  ): Promise<Record<string, Record<string, number>>> => {
    const yearsParam = years.join(',');
    const queryParams = new URLSearchParams();
    queryParams.append('years', yearsParam);
    if (selectedLevel3Values && selectedLevel3Values.length > 0) {
      queryParams.append('selected_level_3_values', selectedLevel3Values.join(','));
    }
    return fetchAPI<Record<string, Record<string, number>>>(`/api/bilan/calculate?${queryParams.toString()}`);
  },
};

// Bilan Mapping Views API
export interface BilanMappingView {
  id: number;
  name: string;
  view_data: {
    mappings: BilanMapping[];
    selected_level_3_values?: string[];
  };
  created_at: string;
  updated_at: string;
}

export interface BilanMappingViewListResponse {
  views: BilanMappingView[];
  total: number;
}

export interface BilanMappingViewCreate {
  name: string;
  view_data: {
    mappings: BilanMapping[];
    selected_level_3_values?: string[];
  };
}

export interface BilanMappingViewUpdate {
  name?: string;
  view_data?: {
    mappings: BilanMapping[];
    selected_level_3_values?: string[];
  };
}

export const bilanMappingViewsAPI = {
  getAll: async (): Promise<BilanMappingViewListResponse> => {
    return fetchAPI<BilanMappingViewListResponse>('/api/bilan/mapping-views');
  },
  getById: async (id: number): Promise<BilanMappingView> => {
    return fetchAPI<BilanMappingView>(`/api/bilan/mapping-views/${id}`);
  },
  create: async (data: BilanMappingViewCreate): Promise<BilanMappingView> => {
    return fetchAPI<BilanMappingView>('/api/bilan/mapping-views', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  update: async (id: number, data: BilanMappingViewUpdate): Promise<BilanMappingView> => {
    return fetchAPI<BilanMappingView>(`/api/bilan/mapping-views/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
  delete: async (id: number): Promise<void> => {
    return fetchAPI<void>(`/api/bilan/mapping-views/${id}`, {
      method: 'DELETE',
    });
  },
};


