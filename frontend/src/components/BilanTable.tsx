/**
 * BilanTable component - Tableau du bilan avec structure hiérarchique
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 * 
 * Repris à zéro pour corriger les problèmes de performance
 */

'use client';

import React, { useState, useEffect } from 'react';
import { bilanAPI, BilanMapping, BilanResponse, transactionsAPI, BilanConfig } from '@/api/client';
import { useProperty } from '@/contexts/PropertyContext';

interface BilanTableProps {
  refreshKey?: number; // Pour forcer le rechargement
}

// Fonction pour récupérer les années à afficher depuis les transactions
const getYearsToDisplay = async (propertyId: number): Promise<number[]> => {
  const currentYear = new Date().getFullYear();
  
  try {
    // Récupérer la première transaction (triée par date croissante) pour cette propriété
    const firstTransactionResponse = await transactionsAPI.getAll(
      propertyId, // propertyId
      0, // skip
      1, // limit
      undefined, // startDate
      undefined, // endDate
      'date', // sortBy
      'asc' // sortDirection
    );
    
    let startYear = 2020; // Valeur par défaut
    
    if (firstTransactionResponse.transactions && firstTransactionResponse.transactions.length > 0) {
      const firstTransaction = firstTransactionResponse.transactions[0];
      if (firstTransaction.date) {
        const firstDate = new Date(firstTransaction.date);
        startYear = firstDate.getFullYear();
      }
    }
    
    const years: number[] = [];
    for (let year = startYear; year <= currentYear; year++) {
      years.push(year);
    }
    return years;
  } catch (error) {
    console.error('[BilanTable] Erreur lors de la récupération de la première transaction:', error);
    // En cas d'erreur, utiliser 2020 comme valeur par défaut
    const years: number[] = [];
    for (let year = 2020; year <= currentYear; year++) {
      years.push(year);
    }
    return years;
  }
};

// Fonction pour formater un montant en €
const formatAmount = (amount: number | null | undefined): string => {
  if (amount === null || amount === undefined) {
    return '-';
  }
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
};

// Catégories qui doivent être affichées en négatif (même si le backend retourne positif)
const NEGATIVE_CATEGORIES = [
  'Amortissements cumulés',
];

export default function BilanTable({ refreshKey }: BilanTableProps) {
  const { activeProperty } = useProperty();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [years, setYears] = useState<number[]>([]);
  const [mappings, setMappings] = useState<BilanMapping[]>([]);
  const [config, setConfig] = useState<BilanConfig | null>(null);
  const [bilanData, setBilanData] = useState<Record<number, BilanResponse>>({});

  console.log('[BilanTable] propertyId:', activeProperty?.id);

  // Calculer les années à afficher depuis les transactions
  useEffect(() => {
    const loadYears = async () => {
      if (!activeProperty?.id) return;
      console.log('[BilanTable] Chargement des années pour propertyId:', activeProperty.id);
      const yearsToDisplay = await getYearsToDisplay(activeProperty.id);
      setYears(yearsToDisplay);
    };
    loadYears();
  }, [activeProperty?.id]);

  // Charger les mappings et les données depuis l'API
  useEffect(() => {
    if (years.length > 0 && activeProperty?.id) {
      loadData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey, years.length, activeProperty?.id]);

  // Écouter les événements de modification de crédits pour rafraîchir automatiquement
  useEffect(() => {
    if (!activeProperty?.id) return;
    
    const handleLoanConfigUpdated = async () => {
      console.log('🔄 [BilanTable] Événement loanConfigUpdated reçu, rafraîchissement du bilan...');
      // Si les années ne sont pas encore chargées, les charger d'abord
      if (years.length === 0) {
        const yearsToDisplay = await getYearsToDisplay(activeProperty.id);
        setYears(yearsToDisplay);
        // Attendre un peu pour que le state soit mis à jour
        setTimeout(() => {
          loadData();
        }, 100);
      } else {
        loadData();
      }
    };

    const handleLoanPaymentUpdated = async () => {
      console.log('🔄 [BilanTable] Événement loanPaymentUpdated reçu, rafraîchissement du bilan...');
      // Si les années ne sont pas encore chargées, les charger d'abord
      if (years.length === 0) {
        const yearsToDisplay = await getYearsToDisplay(activeProperty.id);
        setYears(yearsToDisplay);
        // Attendre un peu pour que le state soit mis à jour
        setTimeout(() => {
          loadData();
        }, 100);
      } else {
        loadData();
      }
    };

    window.addEventListener('loanConfigUpdated', handleLoanConfigUpdated);
    window.addEventListener('loanPaymentUpdated', handleLoanPaymentUpdated);

    return () => {
      window.removeEventListener('loanConfigUpdated', handleLoanConfigUpdated);
      window.removeEventListener('loanPaymentUpdated', handleLoanPaymentUpdated);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [years.length, activeProperty?.id]);

  const loadData = async () => {
    if (years.length === 0 || !activeProperty?.id) return;
    
    try {
      setLoading(true);
      setError(null);
      
      console.log('[BilanTable] API call: getMappings, propertyId:', activeProperty.id);
      // Charger les mappings
      const mappingsResponse = await bilanAPI.getMappings(activeProperty.id);
      setMappings(mappingsResponse.items || []);
      
      console.log('[BilanTable] API call: getConfig, propertyId:', activeProperty.id);
      // Charger la configuration (pour obtenir les level_3_values sélectionnés)
      const configResponse = await bilanAPI.getConfig(activeProperty.id);
      setConfig(configResponse);
      
      console.log('[BilanTable] API call: calculateMultiple, propertyId:', activeProperty.id);
      // Charger les données du bilan pour toutes les années en une fois (comme compte de résultat)
      const calculateResponse = await bilanAPI.calculateMultiple(activeProperty.id, years);
      
      // Debug: Vérifier les données reçues
      console.log('📊 [BilanTable] Données reçues:', {
        propertyId: activeProperty.id,
        years: calculateResponse.years,
        resultsKeys: Object.keys(calculateResponse.results)
      });
      
      // Vérifier spécifiquement Amortissements cumulés pour 2021
      if (calculateResponse.results[2021]) {
        const bilan2021 = calculateResponse.results[2021];
        for (const typeItem of bilan2021.types) {
          for (const subCategoryItem of typeItem.sub_categories) {
            for (const categoryItem of subCategoryItem.categories) {
              if (categoryItem.category_name === 'Amortissements cumulés') {
                console.log('✅ [BilanTable] Amortissements cumulés trouvés dans les données:', {
                  categoryName: categoryItem.category_name,
                  amount: categoryItem.amount,
                  subCategory: subCategoryItem.sub_category,
                  type: typeItem.type
                });
              }
            }
          }
        }
      }
      
      // Construire le map des données
      setBilanData(calculateResponse.results);
    } catch (err: any) {
      console.error('[BilanTable] Erreur lors du chargement des données:', err);
      setError(err.message || 'Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  // Obtenir le montant pour une catégorie et une année donnée
  const getCategoryAmount = (categoryName: string, year: number): number | null => {
    const bilan = bilanData[year];
    if (!bilan) return null;
    
    // Parcourir la structure hiérarchique pour trouver la catégorie
    for (const typeItem of bilan.types) {
      for (const subCategoryItem of typeItem.sub_categories) {
        for (const categoryItem of subCategoryItem.categories) {
          if (categoryItem.category_name === categoryName) {
            // Debug pour Amortissements cumulés
            if (categoryName === 'Amortissements cumulés') {
              console.log(`🔍 [BilanTable] getCategoryAmount - Amortissements cumulés trouvé:`, {
                categoryName,
                amount: categoryItem.amount,
                year,
                subCategory: subCategoryItem.sub_category
              });
            }
            return categoryItem.amount;
          }
        }
      }
    }
    
    // Debug si pas trouvé
    if (categoryName === 'Amortissements cumulés') {
      console.warn(`⚠️ [BilanTable] getCategoryAmount - Amortissements cumulés NON trouvé pour année ${year}`);
      console.log('Catégories disponibles:', 
        bilan.types.flatMap(t => 
          t.sub_categories.flatMap(sc => 
            sc.categories.map(c => c.category_name)
          )
        )
      );
    }
    
    return null;
  };

  // Déterminer si une catégorie doit être affichée en négatif
  const shouldDisplayNegative = (categoryName: string): boolean => {
    return NEGATIVE_CATEGORIES.includes(categoryName);
  };

  // Obtenir le style pour un montant (rouge si négatif ou si catégorie spéciale)
  const getAmountStyle = (amount: number | null, categoryName: string): React.CSSProperties => {
    if (amount === null || amount === undefined) {
      return { color: '#6b7280' };
    }
    
    const displayAmount = shouldDisplayNegative(categoryName) ? -amount : amount;
    
    if (displayAmount < 0) {
      return { color: '#dc2626', fontWeight: '500' };
    } else if (displayAmount > 0) {
      return { color: '#059669', fontWeight: '500' };
    } else {
      return { color: '#6b7280' };
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
        ⏳ Chargement du bilan...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#dc2626' }}>
        ❌ Erreur: {error}
      </div>
    );
  }

  if (!config || mappings.length === 0) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
        Aucun mapping configuré. Configurez le bilan dans la card de configuration.
      </div>
    );
  }

  if (Object.keys(bilanData).length === 0) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
        Aucune donnée disponible pour les années sélectionnées.
      </div>
    );
  }

  // Construire la structure hiérarchique pour l'affichage
  const buildDisplayStructure = () => {
    const structure: Array<{
      level: 'A' | 'B' | 'C';
      type?: string;
      subCategory?: string;
      categoryName?: string;
      amounts: Record<number, number | null>;
      isTotal?: boolean;
      isBalance?: boolean;
    }> = [];

    // Parcourir les données par année pour construire la structure
    const firstYear = years[0];
    const firstYearData = bilanData[firstYear];
    
    if (!firstYearData) return structure;

    // Parcourir la structure hiérarchique
    for (const typeItem of firstYearData.types) {
      // Niveau A: Type (ACTIF/PASSIF)
      structure.push({
        level: 'A',
        type: typeItem.type,
        amounts: {},
        isTotal: true,
      });

      // Calculer le total pour le type
      for (const year of years) {
        const yearData = bilanData[year];
        if (!yearData) continue;
        
        const typeData = yearData.types.find(t => t.type === typeItem.type);
        if (typeData) {
          structure[structure.length - 1].amounts[year] = typeData.total;
        }
      }

      // Parcourir les sous-catégories
      for (const subCategoryItem of typeItem.sub_categories) {
        // Niveau B: Sous-catégorie
        structure.push({
          level: 'B',
          type: typeItem.type,
          subCategory: subCategoryItem.sub_category,
          amounts: {},
          isTotal: true,
        });

        // Calculer le total pour la sous-catégorie
        for (const year of years) {
          const yearData = bilanData[year];
          if (!yearData) continue;
          
          const typeData = yearData.types.find(t => t.type === typeItem.type);
          if (!typeData) continue;
          
          const subCategoryData = typeData.sub_categories.find(
            sc => sc.sub_category === subCategoryItem.sub_category
          );
          if (subCategoryData) {
            structure[structure.length - 1].amounts[year] = subCategoryData.total;
          }
        }

        // Parcourir les catégories
        for (const categoryItem of subCategoryItem.categories) {
          // Niveau C: Catégorie
          structure.push({
            level: 'C',
            type: typeItem.type,
            subCategory: subCategoryItem.sub_category,
            categoryName: categoryItem.category_name,
            amounts: {},
            isTotal: false,
          });

          // Récupérer les montants pour chaque année
          // OPTIMISATION: Utiliser directement categoryItem.amount pour la première année
          // puis getCategoryAmount pour les autres années
          for (const year of years) {
            let amount: number | null = null;
            
            // Pour la première année, utiliser directement la valeur de l'API
            if (year === firstYear) {
              amount = categoryItem.amount;
            } else {
              // Pour les autres années, utiliser getCategoryAmount
              amount = getCategoryAmount(categoryItem.category_name, year);
            }
            
            structure[structure.length - 1].amounts[year] = amount;
            
            // Debug pour Amortissements cumulés
            if (categoryItem.category_name === 'Amortissements cumulés') {
              console.log(`🔍 [BilanTable] Amortissements cumulés - Année ${year}:`, {
                categoryName: categoryItem.category_name,
                amountFromAPI: categoryItem.amount,
                amountUsed: amount,
                subCategory: subCategoryItem.sub_category,
                isFirstYear: year === firstYear
              });
            }
          }
        }
      }
    }

    // Ajouter la ligne d'équilibre après le dernier élément (PASSIF)
    const balanceRow: {
      level: 'A' | 'B' | 'C';
      type?: string;
      subCategory?: string;
      categoryName?: string;
      amounts: Record<number, number | null>;
      isTotal?: boolean;
      isBalance?: boolean;
    } = {
      level: 'A',
      amounts: {},
      isTotal: false,
      isBalance: true,
    };

    // Calculer la différence et le pourcentage pour chaque année
    for (const year of years) {
      const yearData = bilanData[year];
      if (!yearData) {
        balanceRow.amounts[year] = null;
        continue;
      }

      const actifTotal = yearData.actif_total || 0;
      const passifTotal = yearData.passif_total || 0;
      const difference = actifTotal - passifTotal;
      
      // Stocker la différence (on l'utilisera pour l'affichage)
      balanceRow.amounts[year] = difference;
    }

    structure.push(balanceRow);

    return structure;
  };

  const displayStructure = buildDisplayStructure();

  // Fonction pour calculer le pourcentage de différence
  const calculateDifferencePercent = (year: number): number | null => {
    const yearData = bilanData[year];
    if (!yearData) return null;

    const actifTotal = yearData.actif_total || 0;
    const passifTotal = yearData.passif_total || 0;
    const difference = actifTotal - passifTotal;

    if (actifTotal === 0) return null; // N/A si ACTIF = 0
    return (difference / actifTotal) * 100;
  };

  // Fonction pour formater le texte d'équilibre
  const formatBalanceText = (year: number): string => {
    const yearData = bilanData[year];
    if (!yearData) return '-';

    const actifTotal = yearData.actif_total || 0;
    const passifTotal = yearData.passif_total || 0;
    const difference = actifTotal - passifTotal;
    const tolerance = 0.01; // Tolérance pour les arrondis (0.01%)

    if (actifTotal === 0) return 'N/A';

    if (Math.abs(difference) < (actifTotal * tolerance / 100)) {
      return 'Équilibre respecté ✓';
    }

    const percent = calculateDifferencePercent(year);
    if (percent === null) return 'N/A';
    
    return `% Différence : ${percent.toFixed(2)}%`;
  };

  // Fonction pour obtenir le style de la ligne d'équilibre
  const getBalanceRowStyle = (year: number): { backgroundColor: string; color: string } => {
    const yearData = bilanData[year];
    if (!yearData) {
      return { backgroundColor: '#f9fafb', color: '#6b7280' };
    }

    const actifTotal = yearData.actif_total || 0;
    const passifTotal = yearData.passif_total || 0;
    const difference = actifTotal - passifTotal;
    const tolerance = 0.01; // Tolérance pour les arrondis (0.01%)

    if (actifTotal === 0) {
      return { backgroundColor: '#f9fafb', color: '#6b7280' };
    }

    if (Math.abs(difference) < (actifTotal * tolerance / 100)) {
      // Équilibré : vert
      return { backgroundColor: '#d1fae5', color: '#065f46' };
    } else {
      // Déséquilibré : rouge
      return { backgroundColor: '#fee2e2', color: '#991b1b' };
    }
  };


  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
        <thead>
          <tr style={{ backgroundColor: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
            <th style={{ 
              padding: '12px', 
              textAlign: 'left', 
              fontWeight: '600', 
              color: '#374151',
              position: 'sticky',
              left: 0,
              backgroundColor: '#f9fafb',
              zIndex: 10,
              minWidth: '250px'
            }}>
              Catégorie
            </th>
            {years.map(year => (
              <th key={year} style={{ 
                padding: '12px', 
                textAlign: 'right', 
                fontWeight: '600', 
                color: '#374151',
                minWidth: '120px'
              }}>
                {year}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {displayStructure.map((row, index) => {
            // Gestion spéciale pour la ligne d'équilibre
            if (row.isBalance) {
              return (
                <tr 
                  key={index}
                  style={{ 
                    borderTop: '3px solid #d1d5db',
                    borderBottom: '2px solid #d1d5db'
                  }}
                >
                  <td style={{ 
                    padding: '12px', 
                    fontWeight: '700',
                    position: 'sticky',
                    left: 0,
                    zIndex: 5
                  }}>
                    ÉQUILIBRE
                  </td>
                  {years.map(year => {
                    const balanceStyle = getBalanceRowStyle(year);
                    return (
                      <td key={year} style={{ 
                        padding: '12px', 
                        textAlign: 'right',
                        fontWeight: '700',
                        ...balanceStyle
                      }}>
                        {formatBalanceText(year)}
                      </td>
                    );
                  })}
                </tr>
              );
            }

            const indent = row.level === 'A' ? 0 : row.level === 'B' ? 20 : 40;
            const isBold = row.isTotal || row.level === 'A';
            const bgColor = row.level === 'A' ? '#f3f4f6' : row.level === 'B' ? '#f9fafb' : 'white';
            const textColor = row.level === 'A' ? '#1f2937' : '#374151';

            return (
              <tr 
                key={index}
                style={{ 
                  backgroundColor: bgColor,
                  borderBottom: row.level === 'A' ? '2px solid #d1d5db' : '1px solid #e5e7eb'
                }}
              >
                <td style={{ 
                  padding: '12px', 
                  paddingLeft: `${12 + indent}px`,
                  fontWeight: isBold ? '600' : '400',
                  color: textColor,
                  position: 'sticky',
                  left: 0,
                  backgroundColor: bgColor,
                  zIndex: row.level === 'A' ? 5 : 1
                }}>
                  {row.level === 'A' && row.type}
                  {row.level === 'B' && row.subCategory}
                  {row.level === 'C' && row.categoryName}
                </td>
                {years.map(year => {
                  const amount = row.amounts[year];
                  const displayAmount = row.categoryName && shouldDisplayNegative(row.categoryName) 
                    ? (amount !== null && amount !== undefined ? -amount : null)
                    : amount;
                  const style = row.categoryName 
                    ? getAmountStyle(amount, row.categoryName)
                    : { color: textColor, fontWeight: isBold ? '600' : '400' };

                  return (
                    <td key={year} style={{ 
                      padding: '12px', 
                      textAlign: 'right',
                      ...style
                    }}>
                      {formatAmount(displayAmount)}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
      
      {/* Message d'alerte si déséquilibré */}
      {(() => {
        let hasImbalance = false;
        for (const year of years) {
          const yearData = bilanData[year];
          if (!yearData) continue;

          const actifTotal = yearData.actif_total || 0;
          const passifTotal = yearData.passif_total || 0;
          const difference = actifTotal - passifTotal;
          const tolerance = 0.01; // Tolérance pour les arrondis (0.01%)

          if (actifTotal > 0 && Math.abs(difference) >= (actifTotal * tolerance / 100)) {
            hasImbalance = true;
            break;
          }
        }

        if (hasImbalance) {
          return (
            <div style={{
              marginTop: '16px',
              padding: '12px 16px',
              backgroundColor: '#fef3c7',
              border: '1px solid #fbbf24',
              borderRadius: '6px',
              color: '#92400e',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <span>⚠️</span>
              <span>Attention : Le bilan n'est pas équilibré. Vérifiez les calculs.</span>
            </div>
          );
        }
        return null;
      })()}
    </div>
  );
}
