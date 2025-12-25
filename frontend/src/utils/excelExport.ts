/**
 * Excel Export Utilities
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 * 
 * Fonctions utilitaires pour exporter des données vers Excel (.xlsx)
 */

import * as XLSX from 'xlsx';
import { Mapping, Transaction } from '@/api/client';

/**
 * Exporte les mappings vers un fichier Excel (.xlsx)
 * 
 * @param mappings - Liste des mappings à exporter
 * @returns Buffer du fichier Excel généré
 */
export function exportMappingsToExcel(mappings: Mapping[]): XLSX.WorkBook {
  // Créer un nouveau workbook
  const workbook = XLSX.utils.book_new();
  
  // Préparer les données avec en-têtes
  const data: any[][] = [];
  
  // Ajouter les en-têtes en première ligne
  data.push(['Nom', 'Level 1', 'Level 2', 'Level 3']);
  
  // Ajouter les données des mappings
  mappings.forEach((mapping) => {
    data.push([
      mapping.nom || '',
      mapping.level_1 || '',
      mapping.level_2 || '',
      mapping.level_3 || '', // Gérer les valeurs null/vides
    ]);
  });
  
  // Créer une worksheet à partir des données
  const worksheet = XLSX.utils.aoa_to_sheet(data);
  
  // Définir la largeur des colonnes (optionnel, pour meilleure lisibilité)
  worksheet['!cols'] = [
    { wch: 30 }, // Nom
    { wch: 20 }, // Level 1
    { wch: 20 }, // Level 2
    { wch: 20 }, // Level 3
  ];
  
  // Ajouter la worksheet au workbook
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Mappings');
  
  return workbook;
}

/**
 * Génère un nom de fichier par défaut avec la date actuelle
 * Format: mappings_YYYY-MM-DD.xlsx
 * 
 * @returns Nom de fichier avec date
 */
export function generateDefaultFilename(): string {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  
  return `mappings_${year}-${month}-${day}.xlsx`;
}

/**
 * Génère un nom de fichier par défaut pour les transactions avec la date actuelle
 * Format: transactions_YYYY-MM-DD.xlsx
 * 
 * @returns Nom de fichier avec date
 */
export function generateTransactionsFilename(): string {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  
  return `transactions_${year}-${month}-${day}.xlsx`;
}

/**
 * Formate une date au format français DD/MM/YYYY
 * 
 * @param dateString - Date au format ISO string
 * @returns Date formatée DD/MM/YYYY
 */
function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
  } catch {
    return dateString;
  }
}

/**
 * Exporte les transactions vers un fichier Excel (.xlsx)
 * 
 * @param transactions - Liste des transactions à exporter
 * @returns Workbook Excel généré
 */
export function exportTransactionsToExcel(transactions: Transaction[]): XLSX.WorkBook {
  // Créer un nouveau workbook
  const workbook = XLSX.utils.book_new();
  
  // Préparer les données avec en-têtes
  const data: any[][] = [];
  
  // Ajouter les en-têtes en première ligne
  data.push(['Date', 'Nom', 'Quantité', 'Solde', 'Level 1', 'Level 2', 'Level 3']);
  
  // Ajouter les données des transactions
  transactions.forEach((transaction) => {
    data.push([
      formatDate(transaction.date), // Date formatée DD/MM/YYYY
      transaction.nom || '',
      transaction.quantite.toFixed(2), // Format avec 2 décimales
      transaction.solde.toFixed(2), // Format avec 2 décimales
      transaction.level_1 || '', // Gérer les valeurs null/vides
      transaction.level_2 || '',
      transaction.level_3 || '',
    ]);
  });
  
  // Créer une worksheet à partir des données
  const worksheet = XLSX.utils.aoa_to_sheet(data);
  
  // Définir la largeur des colonnes (optionnel, pour meilleure lisibilité)
  worksheet['!cols'] = [
    { wch: 12 }, // Date
    { wch: 30 }, // Nom
    { wch: 12 }, // Quantité
    { wch: 12 }, // Solde
    { wch: 20 }, // Level 1
    { wch: 20 }, // Level 2
    { wch: 20 }, // Level 3
  ];
  
  // Ajouter la worksheet au workbook
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Transactions');
  
  return workbook;
}

/**
 * Exporte les transactions et ouvre le dialogue de sauvegarde
 * Fonction principale à utiliser dans les composants
 * 
 * @param transactions - Liste des transactions à exporter
 * @param filename - Nom du fichier (optionnel, par défaut avec date)
 * @returns Promise qui se résout quand le fichier est sauvegardé
 */
export async function exportAndDownloadTransactions(
  transactions: Transaction[], 
  filename?: string
): Promise<void> {
  const workbook = exportTransactionsToExcel(transactions);
  const defaultFilename = filename || generateTransactionsFilename();
  await saveExcelFileWithDialog(workbook, defaultFilename);
}

/**
 * Télécharge un workbook Excel en tant que fichier (fallback)
 * Utilisé si l'API File System Access n'est pas supportée
 * 
 * @param workbook - Workbook Excel à télécharger
 * @param filename - Nom du fichier (par défaut: mappings_YYYY-MM-DD.xlsx)
 */
function downloadExcelFileFallback(workbook: XLSX.WorkBook, filename?: string): void {
  const defaultFilename = filename || generateDefaultFilename();
  
  // Convertir le workbook en buffer
  const excelBuffer = XLSX.write(workbook, { 
    type: 'array', 
    bookType: 'xlsx' 
  });
  
  // Créer un Blob à partir du buffer
  const blob = new Blob([excelBuffer], { 
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
  });
  
  // Créer un lien de téléchargement
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = defaultFilename;
  
  // Déclencher le téléchargement
  document.body.appendChild(link);
  link.click();
  
  // Nettoyer
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

/**
 * Sauvegarde un workbook Excel avec dialogue de sauvegarde (File System Access API)
 * Fallback sur téléchargement direct si l'API n'est pas supportée
 * 
 * @param workbook - Workbook Excel à sauvegarder
 * @param defaultFilename - Nom de fichier par défaut
 * @returns Promise qui se résout quand le fichier est sauvegardé
 */
export async function saveExcelFileWithDialog(
  workbook: XLSX.WorkBook, 
  defaultFilename?: string
): Promise<void> {
  const filename = defaultFilename || generateDefaultFilename();
  
  // Vérifier si l'API File System Access est supportée
  if ('showSaveFilePicker' in window) {
    try {
      // Convertir le workbook en buffer
      const excelBuffer = XLSX.write(workbook, { 
        type: 'array', 
        bookType: 'xlsx' 
      });
      
      // Créer un Blob
      const blob = new Blob([excelBuffer], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      
      // Ouvrir le dialogue de sauvegarde
      const fileHandle = await (window as any).showSaveFilePicker({
        suggestedName: filename,
        types: [{
          description: 'Fichier Excel',
          accept: {
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
          },
        }],
      });
      
      // Écrire le fichier
      const writable = await fileHandle.createWritable();
      await writable.write(blob);
      await writable.close();
      
      return;
    } catch (error: any) {
      // Si l'utilisateur annule le dialogue, ne rien faire
      if (error.name === 'AbortError') {
        throw new Error('Export annulé par l\'utilisateur');
      }
      // Sinon, fallback sur téléchargement direct
      console.warn('Erreur avec File System Access API, utilisation du fallback:', error);
    }
  }
  
  // Fallback : téléchargement direct
  downloadExcelFileFallback(workbook, filename);
}

/**
 * Exporte les mappings et ouvre le dialogue de sauvegarde
 * Fonction principale à utiliser dans les composants
 * 
 * @param mappings - Liste des mappings à exporter
 * @param filename - Nom du fichier (optionnel, par défaut avec date)
 * @returns Promise qui se résout quand le fichier est sauvegardé
 */
export async function exportAndDownloadMappings(
  mappings: Mapping[], 
  filename?: string
): Promise<void> {
  const workbook = exportMappingsToExcel(mappings);
  const defaultFilename = filename || generateDefaultFilename();
  await saveExcelFileWithDialog(workbook, defaultFilename);
}

