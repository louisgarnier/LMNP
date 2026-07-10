/**
 * Formules partagées pour les prévisions du Bilan.
 *
 * Source de vérité unique pour :
 * - Le calcul du compte bancaire prévu (utilisé par BilanForecastCard et BilanTable)
 * - L'extraction d'une catégorie du Bilan (ACTIF/PASSIF) depuis la réponse API
 *
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

import { BilanResponse } from '@/api/client';

/**
 * Calcule le compte bancaire prévu pour l'année en cours.
 *
 * Formule : Réel N-1 + Total CR prévisionnel - Crédit annuel + Variation CCA
 */
export function computeCompteBancairePrevu(params: {
  reelN1: number;
  totalCrPrevisionnel: number;
  creditAnnuel: number;
  variationCca: number;
}): number {
  const { reelN1, totalCrPrevisionnel, creditAnnuel, variationCca } = params;
  const result = reelN1 + totalCrPrevisionnel - creditAnnuel + variationCca;
  return Math.round(result * 100) / 100;
}

/**
 * Extrait le montant d'une catégorie du Bilan (ACTIF ou PASSIF) pour une année donnée.
 * Retourne 0 si la catégorie n'est pas trouvée.
 */
export function extractCategory(
  bilanData: BilanResponse | null | undefined,
  type: 'actif' | 'passif',
  categoryName: string
): number {
  if (!bilanData?.types) return 0;

  const targetType = type === 'actif' ? 'ACTIF' : 'PASSIF';
  const typeItem = bilanData.types.find(t => t.type === targetType);
  if (!typeItem) return 0;

  for (const subCat of typeItem.sub_categories || []) {
    for (const cat of subCat.categories || []) {
      if (cat.category_name === categoryName) {
        return cat.amount || 0;
      }
    }
  }
  return 0;
}
