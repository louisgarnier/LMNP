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
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error (${endpoint}):`, error);
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
    endDate?: string
  ): Promise<TransactionListResponse> => {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
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
    return fetchAPI<Transaction>(`/api/transactions/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  delete: async (id: number): Promise<void> => {
    return fetchAPI<void>(`/api/transactions/${id}`, {
      method: 'DELETE',
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
  period_start?: string;
  period_end?: string;
  message: string;
}

/**
 * File upload API
 */
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

  import: async (file: File, mapping: ColumnMapping[]): Promise<FileImportResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mapping', JSON.stringify(mapping));
    
    const url = `${API_BASE_URL}/api/transactions/import`;
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
};


