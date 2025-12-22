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
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
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
      
      console.error(`❌ [API] Erreur ${response.status} (${endpoint}):`, error);
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
      console.error(`❌ [API] Erreur réseau - Impossible de se connecter au serveur (${url})`);
      console.error(`❌ [API] Vérifiez que le serveur backend est démarré sur ${API_BASE_URL}`);
      throw new Error(`Impossible de se connecter au serveur. Vérifiez que le backend est démarré sur ${API_BASE_URL}`);
    }
    
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
    endDate?: string
  ): Promise<{ column: string; values: string[] }> => {
    const params = new URLSearchParams({
      column,
    });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    return fetchAPI<{ column: string; values: string[] }>(`/api/transactions/unique-values?${params}`);
  },
};

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
export const mappingsAPI = {
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
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      console.error('❌ [API] Erreur API:', error);
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
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


