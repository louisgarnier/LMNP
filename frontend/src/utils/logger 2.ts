/**
 * Configuration centralisée du logging pour le frontend.
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

type LogLevel = 'info' | 'warn' | 'error' | 'debug';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  category: string;
  message: string;
  data?: any;
}

class FrontendLogger {
  private logs: LogEntry[] = [];
  private maxLogs = 1000; // Limite de logs en mémoire
  private logToConsole = true;
  private logToFile = true; // Activé par défaut pour envoyer au backend

  private formatMessage(level: LogLevel, category: string, message: string, data?: any): LogEntry {
    return {
      timestamp: new Date().toISOString(),
      level,
      category,
      message,
      data,
    };
  }

  private log(level: LogLevel, category: string, message: string, data?: any): void {
    const entry = this.formatMessage(level, category, message, data);
    
    // Ajouter au tableau de logs
    this.logs.push(entry);
    if (this.logs.length > this.maxLogs) {
      this.logs.shift(); // Supprimer le plus ancien
    }

    // Logger dans la console
    if (this.logToConsole) {
      const prefix = `[${entry.timestamp}] [${category.toUpperCase()}]`;
      const logMethod = level === 'error' ? console.error : 
                       level === 'warn' ? console.warn : 
                       level === 'debug' ? console.debug : 
                       console.log;
      
      if (data) {
        logMethod(`${prefix} ${message}`, data);
      } else {
        logMethod(`${prefix} ${message}`);
      }
    }

    // Essayer de logger dans un fichier (si possible via API)
    if (this.logToFile && typeof window !== 'undefined') {
      this.sendLogToBackend(entry);
    }
  }

  private async sendLogToBackend(entry: LogEntry): Promise<void> {
    try {
      // Envoyer les logs au backend pour stockage
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/logs/frontend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(entry),
      });
      
      if (!response.ok) {
        console.warn(`[FrontendLogger] Échec de l'envoi du log au backend: ${response.status}`);
      }
    } catch (error) {
      // Logger l'erreur seulement si ce n'est pas une erreur réseau (pour éviter les boucles)
      if (error instanceof TypeError && error.message !== 'Failed to fetch') {
        console.warn(`[FrontendLogger] Erreur lors de l'envoi du log au backend:`, error);
      }
      // Les logs sont déjà dans la console et en mémoire
    }
  }

  info(category: string, message: string, data?: any): void {
    this.log('info', category, message, data);
  }

  warn(category: string, message: string, data?: any): void {
    this.log('warn', category, message, data);
  }

  error(category: string, message: string, data?: any): void {
    this.log('error', category, message, data);
  }

  debug(category: string, message: string, data?: any): void {
    this.log('debug', category, message, data);
  }

  // Récupérer les logs récents
  getLogs(level?: LogLevel, category?: string): LogEntry[] {
    let filtered = this.logs;
    
    if (level) {
      filtered = filtered.filter(log => log.level === level);
    }
    
    if (category) {
      filtered = filtered.filter(log => log.category === category);
    }
    
    return filtered;
  }

  // Exporter les logs au format JSON
  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }

  // Télécharger les logs
  downloadLogs(): void {
    const logsJson = this.exportLogs();
    const blob = new Blob([logsJson], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `frontend_logs_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // Activer/désactiver le logging
  setLogToConsole(enabled: boolean): void {
    this.logToConsole = enabled;
  }

  setLogToFile(enabled: boolean): void {
    this.logToFile = enabled;
    // Activer automatiquement au démarrage si en développement
    if (enabled && typeof window !== 'undefined') {
      this.info('Logger', 'Envoi des logs au backend activé');
    }
  }
}

// Instance singleton
export const frontendLogger = new FrontendLogger();

// Initialiser le logger au chargement du module
if (typeof window !== 'undefined') {
  (window as any).frontendLogger = frontendLogger;
  
  // Activer l'envoi au backend automatiquement
  frontendLogger.setLogToFile(true);
  
  // Logger le démarrage (après un petit délai pour éviter les erreurs de chargement)
  setTimeout(() => {
    frontendLogger.info('Logger', 'Frontend logger initialisé', {
      timestamp: new Date().toISOString()
    });
  }, 100);
}
