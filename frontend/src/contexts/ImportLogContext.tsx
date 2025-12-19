/**
 * ImportLogContext - Context for storing import logs step by step
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { createContext, useContext, useState, ReactNode } from 'react';

export interface ImportLogEntry {
  id: string; // filename + timestamp
  filename: string;
  status: 'pending' | 'in_progress' | 'completed' | 'error';
  startTime: Date;
  endTime?: Date;
  logs: Array<{
    timestamp: Date;
    step: string;
    message: string;
    level: 'info' | 'success' | 'warning' | 'error';
  }>;
  result?: {
    imported_count: number;
    duplicates_count: number;
    errors_count: number;
    period_start?: string;
    period_end?: string;
    duplicates?: Array<{
      date: string;
      quantite: number;
      nom: string;
      existing_id: number;
    }>;
  };
  error?: string;
}

interface ImportLogContextType {
  logs: ImportLogEntry[];
  addLog: (filename: string) => string; // Returns log ID
  updateLog: (id: string, updates: Partial<ImportLogEntry>) => void;
  addLogEntry: (id: string, step: string, message: string, level?: 'info' | 'success' | 'warning' | 'error') => void;
  clearLogs: () => void;
}

const ImportLogContext = createContext<ImportLogContextType | undefined>(undefined);

export function ImportLogProvider({ children }: { children: ReactNode }) {
  const [logs, setLogs] = useState<ImportLogEntry[]>([]);

  const addLog = (filename: string): string => {
    const id = `${filename}_${Date.now()}`;
    const newLog: ImportLogEntry = {
      id,
      filename,
      status: 'pending',
      startTime: new Date(),
      logs: [],
    };
    setLogs(prev => [newLog, ...prev]);
    return id;
  };

  const updateLog = (id: string, updates: Partial<ImportLogEntry>) => {
    setLogs(prev =>
      prev.map(log =>
        log.id === id
          ? { ...log, ...updates }
          : log
      )
    );
  };

  const addLogEntry = (
    id: string,
    step: string,
    message: string,
    level: 'info' | 'success' | 'warning' | 'error' = 'info'
  ) => {
    setLogs(prev =>
      prev.map(log =>
        log.id === id
          ? {
              ...log,
              logs: [
                ...log.logs,
                {
                  timestamp: new Date(),
                  step,
                  message,
                  level,
                },
              ],
            }
          : log
      )
    );
  };

  const clearLogs = () => {
    setLogs([]);
  };

  return (
    <ImportLogContext.Provider
      value={{
        logs,
        addLog,
        updateLog,
        addLogEntry,
        clearLogs,
      }}
    >
      {children}
    </ImportLogContext.Provider>
  );
}

export function useImportLog() {
  const context = useContext(ImportLogContext);
  if (context === undefined) {
    throw new Error('useImportLog must be used within an ImportLogProvider');
  }
  return context;
}

