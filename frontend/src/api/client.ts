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
      
      // Ne pas logger les erreurs 404 (souvent attendues, comme pour vérifier si une ressource existe)
      if (response.status !== 404) {
      console.error(`❌ [API] Erreur ${response.status} (${endpoint}):`, error);
      }
      
      // Créer une erreur avec le statut pour faciliter la détection
      const apiError: any = new Error(errorMessage);
      apiError.status = response.status;
      throw apiError;
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
    
    // Ne pas logger les erreurs 404 dans le catch général non plus
    // Vérifier si c'est une erreur avec status 404 ou message contenant "non trouvé"
    const is404Error = (error as any)?.status === 404 || 
                       (error instanceof Error && (
                         error.message?.includes('404') || 
                         error.message?.includes('non trouvé') ||
                         error.message?.includes('Type d\'amortissement non trouvé')
                       ));
    
    if (!is404Error) {
    console.error(`❌ [API] Erreur lors de l'appel (${endpoint}):`, error);
    }
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
    endDate?: string,
    filterLevel2?: string,
    filterLevel3?: string[]
  ): Promise<{ column: string; values: string[] }> => {
    const params = new URLSearchParams({
      column,
    });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (filterLevel2) params.append('filter_level_2', filterLevel2);
    if (filterLevel3 && filterLevel3.length > 0) {
      params.append('filter_level_3', filterLevel3.join(','));
    }
    
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

// Allowed Mappings types (Step 5.8)
export interface AllowedMapping {
  id: number;
  level_1: string;
  level_2: string;
  level_3?: string;
  is_hardcoded: boolean;
  created_at: string;
  updated_at: string;
}

export interface AllowedMappingListResponse {
  mappings: AllowedMapping[];
  total: number;
}

export interface AllowedMappingResetResponse {
  message: string;
  deleted_allowed: number;
  deleted_mappings: number;
  unassigned_transactions: number;
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
   * Récupérer toutes les valeurs level_1 autorisées (depuis allowed_mappings)
   */
  async getAllowedLevel1(): Promise<{ level_1: string[] }> {
    return fetchAPI<{ level_1: string[] }>('/api/mappings/allowed-level1');
  },

  /**
   * Récupérer les valeurs level_2 autorisées (depuis allowed_mappings)
   * Si level_1 est fourni, retourne les level_2 pour ce level_1
   * Si level_1 n'est pas fourni, retourne tous les level_2 autorisés (pour scénario 2)
   */
  async getAllowedLevel2(level_1?: string): Promise<{ level_2: string[] }> {
    const params = new URLSearchParams();
    if (level_1) {
      params.append('level_1', level_1);
    }
    return fetchAPI<{ level_2: string[] }>(`/api/mappings/allowed-level2?${params.toString()}`);
  },

  /**
   * Récupérer les valeurs level_3 autorisées pour un couple (level_1, level_2) (depuis allowed_mappings)
   */
  async getAllowedLevel3(level_1: string, level_2: string): Promise<{ level_3: string[] }> {
    const params = new URLSearchParams({
      level_1,
      level_2,
    });
    return fetchAPI<{ level_3: string[] }>(`/api/mappings/allowed-level3?${params.toString()}`);
  },

  /**
   * Récupérer les valeurs level_3 autorisées pour un level_2 donné (depuis allowed_mappings)
   * Utilisé pour le scénario 2 : quand level_2 est sélectionné en premier
   */
  async getAllowedLevel3ForLevel2(level_2: string): Promise<{ level_3: string[] }> {
    const params = new URLSearchParams({
      level_2,
    });
    return fetchAPI<{ level_3: string[] }>(`/api/mappings/allowed-level3-for-level2?${params.toString()}`);
  },

  /**
   * Récupérer les valeurs level_2 autorisées pour un level_3 donné (filtrage bidirectionnel)
   * Utilisé quand level_3 est sélectionné en premier
   */
  async getAllowedLevel2ForLevel3(level_3: string): Promise<{ level_2: string[] }> {
    const params = new URLSearchParams({
      level_3,
    });
    return fetchAPI<{ level_2: string[] }>(`/api/mappings/allowed-level2-for-level3?${params.toString()}`);
  },

  /**
   * Récupérer les valeurs level_1 autorisées pour un level_2 donné (filtrage bidirectionnel)
   * Utilisé quand level_2 est sélectionné en premier
   */
  async getAllowedLevel1ForLevel2(level_2: string): Promise<{ level_1: string[] }> {
    const params = new URLSearchParams({
      level_2,
    });
    return fetchAPI<{ level_1: string[] }>(`/api/mappings/allowed-level1-for-level2?${params.toString()}`);
  },

  /**
   * Récupérer les valeurs level_1 autorisées pour un couple (level_2, level_3) (filtrage bidirectionnel)
   * Utilisé quand level_3 puis level_2 sont sélectionnés
   */
  async getAllowedLevel1ForLevel2AndLevel3(level_2: string, level_3: string): Promise<{ level_1: string[] }> {
    const params = new URLSearchParams({
      level_2,
      level_3,
    });
    return fetchAPI<{ level_1: string[] }>(`/api/mappings/allowed-level1-for-level2-and-level3?${params.toString()}`);
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

  // ============================================================================
  // Allowed Mappings API (Step 5.8)
  // ============================================================================

  /**
   * Récupérer tous les mappings autorisés avec pagination
   */
  getAllowedMappings: async (skip: number = 0, limit: number = 100): Promise<AllowedMappingListResponse> => {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });
    return fetchAPI<AllowedMappingListResponse>(`/api/mappings/allowed?${params.toString()}`);
  },

  /**
   * Créer un nouveau mapping autorisé
   */
  createAllowedMapping: async (
    level_1: string,
    level_2: string,
    level_3?: string
  ): Promise<AllowedMapping> => {
    const params = new URLSearchParams({
      level_1,
      level_2,
    });
    if (level_3) {
      params.append('level_3', level_3);
    }
    return fetchAPI<AllowedMapping>(`/api/mappings/allowed?${params.toString()}`, {
      method: 'POST',
    });
  },

  /**
   * Supprimer un mapping autorisé (uniquement si is_hardcoded = False)
   */
  deleteAllowedMapping: async (mappingId: number): Promise<void> => {
    return fetchAPI<void>(`/api/mappings/allowed/${mappingId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Reset les mappings autorisés : supprime uniquement les combinaisons ajoutées manuellement
   */
  resetAllowedMappings: async (): Promise<AllowedMappingResetResponse> => {
    return fetchAPI<AllowedMappingResetResponse>('/api/mappings/allowed/reset', {
      method: 'POST',
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

// ============================================================================
// Amortization API
// ============================================================================

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
  totals_by_category: Record<string, number>;
  totals_by_year: Record<number, number>;
  grand_total: number;
}

export interface AmortizationResultDetail {
  transaction_id: number;
  transaction_date: string;
  transaction_nom: string;
  transaction_quantite: number;
  year: number;
  category: string;
  amount: number;
}

export interface AmortizationDetailsResponse {
  items: AmortizationResultDetail[];
  total: number;
  page: number;
  page_size: number;
}

export interface AmortizationRecalculateResponse {
  message: string;
  results_created: number;
}

export const amortizationAPI = {
  /**
   * Récupère les résultats d'amortissement agrégés par année et catégorie
   */
  getResults: async (): Promise<AmortizationResultsResponse> => {
    return fetchAPI<AmortizationResultsResponse>('/api/amortization/results');
  },

  /**
   * Récupère les résultats d'amortissement sous forme de tableau croisé
   */
  getResultsAggregated: async (): Promise<AmortizationAggregatedResponse> => {
    return fetchAPI<AmortizationAggregatedResponse>('/api/amortization/results/aggregated');
  },

  /**
   * Récupère les détails des transactions pour un drill-down
   */
  getResultsDetails: async (params?: { year?: number; category?: string; page?: number; page_size?: number }): Promise<AmortizationDetailsResponse> => {
    const queryParams = new URLSearchParams();
    if (params?.year !== undefined) queryParams.append('year', params.year.toString());
    if (params?.category) queryParams.append('category', params.category);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.page_size) queryParams.append('page_size', params.page_size.toString());
    
    const queryString = queryParams.toString();
    return fetchAPI<AmortizationDetailsResponse>(`/api/amortization/results/details${queryString ? `?${queryString}` : ''}`);
  },

  /**
   * Force le recalcul complet de tous les amortissements
   */
  recalculate: async (): Promise<AmortizationRecalculateResponse> => {
    return fetchAPI<AmortizationRecalculateResponse>('/api/amortization/recalculate', {
      method: 'POST',
    });
  },
};

// ============================================================================
// Amortization Types API
// ============================================================================

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

export interface AmortizationTypeListResponse {
  items: AmortizationType[];
  total: number;
}

export interface AmortizationTypeAmountResponse {
  type_id: number;
  type_name: string;
  amount: number;
}

export interface AmortizationTypeCumulatedResponse {
  type_id: number;
  type_name: string;
  cumulated_amount: number;
}

export interface AmortizationTypeTransactionCountResponse {
  type_id: number;
  type_name: string;
  transaction_count: number;
}

export const amortizationTypesAPI = {
  /**
   * Liste tous les types d'amortissement
   */
  getAll: async (level_2_value?: string): Promise<AmortizationTypeListResponse> => {
    const params = level_2_value ? `?level_2_value=${encodeURIComponent(level_2_value)}` : '';
    return fetchAPI<AmortizationTypeListResponse>(`/api/amortization/types${params}`);
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
  create: async (data: AmortizationTypeCreate): Promise<AmortizationType> => {
    return fetchAPI<AmortizationType>('/api/amortization/types', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },

  /**
   * Met à jour un type d'amortissement
   */
  update: async (id: number, data: AmortizationTypeUpdate): Promise<AmortizationType> => {
    return fetchAPI<AmortizationType>(`/api/amortization/types/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
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
   * Supprime TOUS les types d'amortissement (toute la table)
   */
  deleteAll: async (): Promise<{ deleted_count: number }> => {
    return fetchAPI<{ deleted_count: number }>('/api/amortization/types/all', {
      method: 'DELETE',
    });
  },

  /**
   * Calcule le montant total d'immobilisation pour un type
   */
  getAmount: async (id: number): Promise<AmortizationTypeAmountResponse> => {
    return fetchAPI<AmortizationTypeAmountResponse>(`/api/amortization/types/${id}/amount`);
  },

  /**
   * Calcule le montant cumulé d'amortissement pour un type
   */
  getCumulated: async (id: number): Promise<AmortizationTypeCumulatedResponse> => {
    return fetchAPI<AmortizationTypeCumulatedResponse>(`/api/amortization/types/${id}/cumulated`);
  },

  /**
   * Compte le nombre de transactions correspondant à un type
   */
  getTransactionCount: async (id: number): Promise<AmortizationTypeTransactionCountResponse> => {
    return fetchAPI<AmortizationTypeTransactionCountResponse>(`/api/amortization/types/${id}/transaction-count`);
  },
};

// Loan Config interfaces and API
export interface LoanConfig {
  id: number;
  name: string;
  credit_amount: number;
  interest_rate: number;
  duration_years: number;
  initial_deferral_months: number;
  loan_start_date?: string | null;
  loan_end_date?: string | null;
  monthly_insurance: number;
  simulation_months?: string | null;  // JSON string array (ex: "[1, 50, 100, 150, 200]")
  created_at: string;
  updated_at: string;
}

export interface LoanConfigCreate {
  name: string;
  credit_amount: number;
  interest_rate: number;
  duration_years: number;
  initial_deferral_months: number;
  loan_start_date?: string | null;
  loan_end_date?: string | null;
  monthly_insurance?: number;
  simulation_months?: string | null;  // JSON string array
}

export interface LoanConfigUpdate {
  name?: string;
  credit_amount?: number;
  interest_rate?: number;
  duration_years?: number;
  initial_deferral_months?: number;
  loan_start_date?: string | null;
  loan_end_date?: string | null;
  monthly_insurance?: number;
  simulation_months?: string | null;  // JSON string array
}

export interface LoanConfigListResponse {
  items: LoanConfig[];
  total: number;
}

export const loanConfigsAPI = {
  /**
   * Récupère la liste des configurations de crédit
   */
  getAll: async (): Promise<LoanConfigListResponse> => {
    return fetchAPI<LoanConfigListResponse>('/api/loan-configs');
  },

  /**
   * Récupère une configuration par son ID
   */
  getById: async (id: number): Promise<LoanConfig> => {
    return fetchAPI<LoanConfig>(`/api/loan-configs/${id}`);
  },

  /**
   * Crée une nouvelle configuration
   */
  create: async (config: LoanConfigCreate): Promise<LoanConfig> => {
    return fetchAPI<LoanConfig>('/api/loan-configs', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  },

  /**
   * Met à jour une configuration
   */
  update: async (id: number, config: LoanConfigUpdate): Promise<LoanConfig> => {
    return fetchAPI<LoanConfig>(`/api/loan-configs/${id}`, {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  },

  /**
   * Supprime une configuration
   */
  delete: async (id: number): Promise<void> => {
    return fetchAPI<void>(`/api/loan-configs/${id}`, {
      method: 'DELETE',
    });
  },
};

// Loan Payment interfaces and API
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
  loan_name: string;
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
  items: LoanPayment[];
  total: number;
  page: number;
  page_size: number;
}

export interface LoanPaymentPreviewResponse {
  filename: string;
  total_rows: number;
  detected_columns: string[];
  year_columns: string[];
  invalid_columns: string[];
  extracted_data: Array<{
    year: number;
    date: string;
    capital: number;
    interest: number;
    insurance: number;
    total: number;
  }>;
  preview: Array<Record<string, any>>;
  warning?: string;
  stats: {
    years_detected: number;
    records_to_create: number;
    existing_records: number;
  };
}

export interface LoanPaymentImportResponse {
  message: string;
  deleted_count: number;
  created_count: number;
  total_years: number;
  loan_name: string;
  errors?: string[];
}

export const loanPaymentsAPI = {
  /**
   * Récupère la liste des mensualités
   */
  getAll: async (params?: {
    skip?: number;
    limit?: number;
    start_date?: string;
    end_date?: string;
    loan_name?: string;
    sort_by?: string;
    sort_direction?: string;
  }): Promise<LoanPaymentListResponse> => {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, String(value));
        }
      });
    }
    const query = queryParams.toString();
    return fetchAPI<LoanPaymentListResponse>(`/api/loan-payments${query ? `?${query}` : ''}`);
  },

  /**
   * Récupère une mensualité par son ID
   */
  getById: async (id: number): Promise<LoanPayment> => {
    return fetchAPI<LoanPayment>(`/api/loan-payments/${id}`);
  },

  /**
   * Crée une nouvelle mensualité
   */
  create: async (payment: LoanPaymentCreate): Promise<LoanPayment> => {
    return fetchAPI<LoanPayment>('/api/loan-payments', {
      method: 'POST',
      body: JSON.stringify(payment),
    });
  },

  /**
   * Met à jour une mensualité
   */
  update: async (id: number, payment: LoanPaymentUpdate): Promise<LoanPayment> => {
    return fetchAPI<LoanPayment>(`/api/loan-payments/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payment),
    });
  },

  /**
   * Supprime une mensualité
   */
  delete: async (id: number): Promise<void> => {
    return fetchAPI<void>(`/api/loan-payments/${id}`, {
      method: 'DELETE',
    });
  },

  /**
   * Preview d'un fichier Excel de mensualités
   */
  preview: async (file: File): Promise<LoanPaymentPreviewResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    // Ne pas utiliser fetchAPI car il ajoute 'Content-Type: application/json'
    // Pour FormData, le navigateur doit définir automatiquement le Content-Type avec le boundary
    const url = `${API_BASE_URL}/api/loan-payments/preview`;
    console.log(`📤 [API] Appel POST ${url}`);
    console.log(`📤 [API] Fichier: ${file.name} (${(file.size / 1024).toFixed(2)} KB)`);
    
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      // Ne pas définir Content-Type - le navigateur le fait automatiquement pour FormData
    });

    console.log(`📥 [API] Réponse ${response.status} pour /api/loan-payments/preview`);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      console.error(`❌ [API] Erreur ${response.status} (/api/loan-payments/preview):`, error);
      // Formater l'erreur comme fetchAPI le fait
      let errorMessage = `HTTP error! status: ${response.status}`;
      if (error.detail) {
        if (Array.isArray(error.detail)) {
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
      throw new Error(errorMessage);
    }

    const result = await response.json();
    console.log('✅ [API] Preview réussi:', result);
    return result;
  },

  /**
   * Importe un fichier Excel de mensualités
   */
  import: async (file: File, loanName: string = 'Prêt principal'): Promise<LoanPaymentImportResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    // Ne pas utiliser fetchAPI car il ajoute 'Content-Type: application/json'
    // Pour FormData, le navigateur doit définir automatiquement le Content-Type avec le boundary
    const url = `${API_BASE_URL}/api/loan-payments/import?loan_name=${encodeURIComponent(loanName)}`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      // Ne pas définir Content-Type - le navigateur le fait automatiquement pour FormData
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      // Formater l'erreur comme fetchAPI le fait
      let errorMessage = `HTTP error! status: ${response.status}`;
      if (error.detail) {
        if (Array.isArray(error.detail)) {
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
      throw new Error(errorMessage);
    }

    return await response.json();
  },
};

// ========== Compte de Résultat API ==========

export interface CompteResultatMapping {
  id: number;
  category_name: string;
  type: string | null;
  level_1_values: string | null;
  created_at: string;
  updated_at: string;
}

export interface CompteResultatMappingCreate {
  category_name: string;
  type?: string | null;
  level_1_values?: string | null;
}

export interface CompteResultatMappingUpdate {
  category_name?: string;
  type?: string | null;
  level_1_values?: string | null;
}

export interface CompteResultatMappingListResponse {
  items: CompteResultatMapping[];
  total: number;
}

export interface CompteResultatConfig {
  id: number;
  level_3_values: string;
  created_at: string;
  updated_at: string;
}

export interface CompteResultatConfigUpdate {
  level_3_values?: string | null;
}

export interface CompteResultatCalculateResponse {
  years: number[];
  results: {
    [year: number]: {
      produits: { [category: string]: number };
      charges: { [category: string]: number };
      amortissements: number;
      cout_financement: number;
      total_produits: number;
      total_charges: number;
      resultat_exploitation: number;
      resultat_net: number;
    };
  };
}

export const compteResultatAPI = {
  /**
   * Récupère tous les mappings
   */
  getMappings: async (): Promise<CompteResultatMappingListResponse> => {
    return fetchAPI<CompteResultatMappingListResponse>('/api/compte-resultat/mappings');
  },

  /**
   * Crée un nouveau mapping
   */
  createMapping: async (mapping: CompteResultatMappingCreate): Promise<CompteResultatMapping> => {
    return fetchAPI<CompteResultatMapping>('/api/compte-resultat/mappings', {
      method: 'POST',
      body: JSON.stringify(mapping),
    });
  },

  /**
   * Met à jour un mapping
   */
  updateMapping: async (id: number, mapping: CompteResultatMappingUpdate): Promise<CompteResultatMapping> => {
    return fetchAPI<CompteResultatMapping>(`/api/compte-resultat/mappings/${id}`, {
      method: 'PUT',
      body: JSON.stringify(mapping),
    });
  },

  /**
   * Supprime un mapping
   */
  deleteMapping: async (id: number): Promise<void> => {
    return fetchAPI<void>(`/api/compte-resultat/mappings/${id}`, {
      method: 'DELETE',
    });
  },

  /**
   * Récupère la configuration (level_3_values)
   */
  getConfig: async (): Promise<CompteResultatConfig> => {
    return fetchAPI<CompteResultatConfig>('/api/compte-resultat/config');
  },

  /**
   * Met à jour la configuration (level_3_values)
   */
  updateConfig: async (config: CompteResultatConfigUpdate): Promise<CompteResultatConfig> => {
    return fetchAPI<CompteResultatConfig>('/api/compte-resultat/config', {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  },

  /**
   * Calcule les montants du compte de résultat pour plusieurs années
   */
  calculate: async (years: number[]): Promise<CompteResultatCalculateResponse> => {
    const yearsParam = years.join(',');
    return fetchAPI<CompteResultatCalculateResponse>(`/api/compte-resultat/calculate?years=${yearsParam}`);
  },
};
