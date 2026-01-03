/**
 * BilanTable component - Tableau du bilan
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import React, { useState, useEffect } from 'react';
import { bilanAPI, BilanMapping, transactionsAPI } from '@/api/client';

interface BilanTableProps {
  refreshKey?: number; // Pour forcer le rechargement
}

export default function BilanTable({ refreshKey }: BilanTableProps) {
  // STEP 10.8.1 - Charger les mappings et les données réelles depuis l'API
  
  const [mappings, setMappings] = useState<BilanMapping[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [years, setYears] = useState<number[]>([]);
  const [amounts, setAmounts] = useState<Record<string, Record<string, number>>>({}); // {year: {category: amount}}
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Charger les mappings et calculer les années au montage et quand refreshKey change
  useEffect(() => {
    loadMappings();
    calculateYears();
  }, [refreshKey]);

  // Charger les données quand les années et mappings sont prêts
  useEffect(() => {
    if (years.length > 0 && mappings.length > 0) {
      loadBilanData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [years.length, mappings.length, refreshKey]);

  const loadMappings = async () => {
    try {
      console.log('🔄 [BilanTable] Chargement des mappings...');
      const response = await bilanAPI.getMappings();
      const loadedMappings = response.mappings || [];
      console.log(`✅ [BilanTable] ${loadedMappings.length} mapping(s) chargé(s)`);
      setMappings(loadedMappings);
      
      // Extraire les catégories uniques depuis les mappings
      // Filtrer pour n'afficher que les catégories qui ont des level_1_values OU qui sont spéciales
      const SPECIAL_CATEGORIES = [
        'Amortissements cumulés',
        'Compte bancaire',
        'Résultat de l\'exercice (bénéfice / perte)',
        'Report à nouveau / report du déficit',
        'Emprunt bancaire (capital restant dû)',
      ];
      
      const categoriesToDisplay = loadedMappings.filter(m => {
        // Afficher si c'est une catégorie spéciale (is_special = true OU dans la liste)
        if (m.is_special || SPECIAL_CATEGORIES.includes(m.category_name)) {
          console.log(`  ✅ [BilanTable] Catégorie spéciale à afficher: ${m.category_name}`);
          return true;
        }
        // Afficher si elle a des level_1_values configurés (non vide)
        const hasLevel1Values = m.level_1_values && Array.isArray(m.level_1_values) && m.level_1_values.length > 0;
        if (hasLevel1Values) {
          console.log(`  ✅ [BilanTable] Catégorie avec level_1_values à afficher: ${m.category_name} (${m.level_1_values.length} valeur(s))`);
          return true;
        }
        // Sinon, ne pas afficher
        console.log(`  ⚠️ [BilanTable] Catégorie sans level_1_values, masquée: ${m.category_name}`);
        return false;
      });
      
      const uniqueCategories = Array.from(new Set(categoriesToDisplay.map(m => m.category_name)));
      console.log(`✅ [BilanTable] ${uniqueCategories.length} catégorie(s) à afficher (filtrées sur ${loadedMappings.length} mapping(s)):`, uniqueCategories);
      
      // Trier les catégories selon Type (ACTIF puis PASSIF), puis Sous-catégorie, puis Catégorie
      const ACTIF_SUB_CATEGORY_ORDER = ['Actif immobilisé', 'Actif circulant'];
      const PASSIF_SUB_CATEGORY_ORDER = ['Capitaux propres', 'Trésorerie passive', 'Dettes financières'];
      
      const sortedCategories = uniqueCategories.sort((a, b) => {
        const mappingA = loadedMappings.find(m => m.category_name === a);
        const mappingB = loadedMappings.find(m => m.category_name === b);
        
        if (!mappingA || !mappingB) {
          return a.localeCompare(b);
        }
        
        // Comparer par Type (ACTIF avant PASSIF)
        if (mappingA.type !== mappingB.type) {
          return mappingA.type === 'ACTIF' ? -1 : 1;
        }
        
        // Même Type : comparer par Sous-catégorie
        const subCatA = mappingA.sub_category || '';
        const subCatB = mappingB.sub_category || '';
        
        if (subCatA !== subCatB) {
          const orderList = mappingA.type === 'ACTIF' ? ACTIF_SUB_CATEGORY_ORDER : PASSIF_SUB_CATEGORY_ORDER;
          const indexA = orderList.indexOf(subCatA);
          const indexB = orderList.indexOf(subCatB);
          
          if (indexA === -1 && indexB === -1) {
            return subCatA.localeCompare(subCatB);
          }
          if (indexA === -1) return 1;
          if (indexB === -1) return -1;
          
          return indexA - indexB;
        }
        
        // Même Type et Sous-catégorie : comparer par Catégorie
        return a.localeCompare(b);
      });
      
      setCategories(sortedCategories);
    } catch (err: any) {
      console.error('❌ [BilanTable] Erreur lors du chargement des mappings:', err);
      setError(err.message || 'Erreur lors du chargement des mappings');
      setLoading(false);
    }
  };

  const calculateYears = async () => {
    try {
      // Récupérer toutes les transactions pour trouver la première date
      const transactions = await transactionsAPI.getAllForExport();
      
      if (transactions.length === 0) {
        const currentYear = new Date().getFullYear();
        setYears([currentYear]);
        return;
      }

      const dates = transactions
        .map(t => new Date(t.date))
        .filter(d => !isNaN(d.getTime()));
      
      if (dates.length === 0) {
        const currentYear = new Date().getFullYear();
        setYears([currentYear]);
        return;
      }

      const minDate = new Date(Math.min(...dates.map(d => d.getTime())));
      const firstYear = minDate.getFullYear();
      const currentYear = new Date().getFullYear();

      const yearsList: number[] = [];
      for (let year = firstYear; year <= currentYear; year++) {
        yearsList.push(year);
      }
      
      setYears(yearsList);
    } catch (err: any) {
      console.error('Erreur lors du calcul des années:', err);
      const currentYear = new Date().getFullYear();
      setYears([currentYear]);
    }
  };

  const loadBilanData = async (retryCount = 0) => {
    if (years.length === 0 || mappings.length === 0) {
      console.log('⚠️ [BilanTable] Années ou mappings manquants, attente...', { years: years.length, mappings: mappings.length });
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      console.log('🔄 [BilanTable] Calcul des montants du bilan à la volée...');
      
      // Récupérer les selectedLevel3Values depuis localStorage (même clé que BilanConfigCard)
      let selectedLevel3Values: string[] = [];
      if (typeof window !== 'undefined') {
        const saved = localStorage.getItem('bilanConfigCard_selectedLevel3Values');
        if (saved) {
          try {
            selectedLevel3Values = JSON.parse(saved);
            console.log('✅ [BilanTable] Level 3 sélectionnés:', selectedLevel3Values);
          } catch (e) {
            console.warn('⚠️ [BilanTable] Erreur lors du chargement de selectedLevel3Values:', e);
          }
        }
      }
      
      // Calculer les montants à la volée (comme CompteResultatTable)
      const amountsByYear = await bilanAPI.calculateAmounts(years, selectedLevel3Values.length > 0 ? selectedLevel3Values : null);
      console.log(`✅ [BilanTable] Montants calculés pour ${Object.keys(amountsByYear).length} année(s)`);
      
      setAmounts(amountsByYear);
      console.log('✅ [BilanTable] Montants organisés:', Object.keys(amountsByYear).length, 'année(s)');
    } catch (err: any) {
      // Vérifier si c'est une erreur réseau (backend non disponible)
      const isNetworkError = err.message?.includes('NETWORK_ERROR') ||
                            err.message?.includes('Impossible de se connecter') || 
                            err.message?.includes('Failed to fetch') ||
                            err.message?.includes('NetworkError');
      
      if (isNetworkError && retryCount < 3) {
        // Retry automatique avec délai exponentiel
        const delay = Math.min(1000 * Math.pow(2, retryCount), 5000);
        console.log(`🔄 [BilanTable] Retry ${retryCount + 1}/3 dans ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
        return loadBilanData(retryCount + 1);
      }
      
      // Si c'est une erreur réseau après les retries, ne pas afficher d'erreur bloquante
      // L'utilisateur verra juste un tableau vide, ce qui est moins intrusif
      if (isNetworkError) {
        // Ne pas logger comme erreur - juste un avertissement silencieux
        console.log('ℹ️ [BilanTable] Backend non disponible. Le tableau restera vide jusqu\'à ce que le backend soit démarré.');
        setAmounts({});
        // Ne pas définir d'erreur pour éviter le message bloquant
        return;
      }
      
      // Pour les autres erreurs, afficher le message
      console.error('❌ [BilanTable] Erreur lors du calcul des montants:', err);
      setError(err.message || 'Erreur lors du calcul des montants du bilan');
    } finally {
      setLoading(false);
    }
  };

  const formatAmount = (amount: number): string => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  // Fonction pour obtenir le montant d'une catégorie pour une année donnée
  const getCategoryAmount = (category: string, year: number): number => {
    const yearStr = year.toString();
    if (amounts[yearStr] && amounts[yearStr][category] !== undefined) {
      return amounts[yearStr][category];
    }
    return 0;
  };

  // Fonction pour obtenir le montant d'affichage (peut être modifié pour certaines catégories)
  const getDisplayAmount = (category: string, amount: number): number => {
    // STEP 10.8.4.1: "Amortissements cumulés" doit être affiché en négatif même si le backend retourne un montant positif
    if (category === 'Amortissements cumulés') {
      return -Math.abs(amount); // Toujours négatif pour l'affichage
    }
    // Step 10.8.4.3: Pour "Résultat de l'exercice", préserver le signe (positif = bénéfice, négatif = perte)
    if (category === 'Résultat de l\'exercice (bénéfice / perte)') {
      return amount; // Retourner tel quel (peut être positif ou négatif)
    }
    return amount;
  };

  // Fonction pour vérifier si une catégorie doit avoir un montant négatif en rouge
  const isNegativeAmountCategory = (categoryName: string, amount?: number): boolean => {
    if (categoryName === 'Amortissements cumulés') {
      return true; // Toujours négatif
    }
    // Step 10.8.4.3: Pour "Résultat de l'exercice", vérifier si le montant est négatif (perte)
    if (categoryName === 'Résultat de l\'exercice (bénéfice / perte)') {
      return amount !== undefined && amount < 0; // Négatif si perte
    }
    return false;
  };

  // STEP 10.8.2 - Calculer les totaux par sous-catégorie
  const calculateSubCategoryTotal = (subCategory: string, year: number): number => {
    // Trouver toutes les catégories qui appartiennent à cette sous-catégorie
    const categoriesInSubCategory = mappings
      .filter(m => m.sub_category === subCategory)
      .map(m => m.category_name)
      .filter(catName => categories.includes(catName));

    let total = 0;

    // Logique de calcul spécifique selon la sous-catégorie
    if (subCategory === 'Actif immobilisé') {
      // Actif immobilisé = Immobilisations - Amortissements cumulés
      // STEP 10.8.4.1: Les amortissements doivent être soustraits (valeur négative)
      const immobilisations = getCategoryAmount('Immobilisations', year);
      const amortissements = getCategoryAmount('Amortissements cumulés', year);
      // Les montants du backend sont positifs, mais pour le calcul on soustrait les amortissements
      total = immobilisations - amortissements;
    } else if (subCategory === 'Actif circulant') {
      // Actif circulant = Compte bancaire + Créances locataires + Charges payées d'avance
      categoriesInSubCategory.forEach(catName => {
        total += getCategoryAmount(catName, year);
      });
    } else if (subCategory === 'Capitaux propres') {
      // Capitaux propres = somme de toutes les catégories
      categoriesInSubCategory.forEach(catName => {
        total += getCategoryAmount(catName, year);
      });
    } else if (subCategory === 'Trésorerie passive') {
      // Tresorerie passive = Cautions
      categoriesInSubCategory.forEach(catName => {
        total += getCategoryAmount(catName, year);
      });
    } else if (subCategory === 'Dettes financières') {
      // Dettes financières = Emprunt bancaire + Autres dettes
      categoriesInSubCategory.forEach(catName => {
        total += getCategoryAmount(catName, year);
      });
    } else {
      // Par défaut, sommer toutes les catégories de la sous-catégorie
      categoriesInSubCategory.forEach(catName => {
        total += getCategoryAmount(catName, year);
      });
    }

    return total;
  };

  // Grouper les catégories par sous-catégorie pour l'affichage
  const getGroupedCategories = () => {
    const grouped: Array<{
      type: string;
      subCategory: string;
      categories: Array<{ name: string; mapping: BilanMapping }>;
    }> = [];

    const ACTIF_SUB_CATEGORY_ORDER = ['Actif immobilisé', 'Actif circulant'];
    const PASSIF_SUB_CATEGORY_ORDER = ['Capitaux propres', 'Trésorerie passive', 'Dettes financières'];

    // Grouper par type puis par sous-catégorie
    const actifGroups: Record<string, Array<{ name: string; mapping: BilanMapping }>> = {};
    const passifGroups: Record<string, Array<{ name: string; mapping: BilanMapping }>> = {};

    categories.forEach(categoryName => {
      const mapping = mappings.find(m => m.category_name === categoryName);
      if (!mapping) return;

      const group = mapping.type === 'ACTIF' ? actifGroups : passifGroups;
      const subCat = mapping.sub_category || 'Autres';

      if (!group[subCat]) {
        group[subCat] = [];
      }
      group[subCat].push({ name: categoryName, mapping });
    });

    // Ajouter les groupes ACTIF dans l'ordre
    ACTIF_SUB_CATEGORY_ORDER.forEach(subCat => {
      if (actifGroups[subCat] && actifGroups[subCat].length > 0) {
        grouped.push({
          type: 'ACTIF',
          subCategory: subCat,
          categories: actifGroups[subCat].sort((a, b) => a.name.localeCompare(b.name))
        });
      }
    });

    // Ajouter les autres sous-catégories ACTIF non listées
    Object.keys(actifGroups).forEach(subCat => {
      if (!ACTIF_SUB_CATEGORY_ORDER.includes(subCat) && actifGroups[subCat].length > 0) {
        grouped.push({
          type: 'ACTIF',
          subCategory: subCat,
          categories: actifGroups[subCat].sort((a, b) => a.name.localeCompare(b.name))
        });
      }
    });

    // Ajouter les groupes PASSIF dans l'ordre
    PASSIF_SUB_CATEGORY_ORDER.forEach(subCat => {
      if (passifGroups[subCat] && passifGroups[subCat].length > 0) {
        grouped.push({
          type: 'PASSIF',
          subCategory: subCat,
          categories: passifGroups[subCat].sort((a, b) => a.name.localeCompare(b.name))
        });
      }
    });

    // Ajouter les autres sous-catégories PASSIF non listées
    Object.keys(passifGroups).forEach(subCat => {
      if (!PASSIF_SUB_CATEGORY_ORDER.includes(subCat) && passifGroups[subCat].length > 0) {
        grouped.push({
          type: 'PASSIF',
          subCategory: subCat,
          categories: passifGroups[subCat].sort((a, b) => a.name.localeCompare(b.name))
        });
      }
    });

    return grouped;
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
        ⏳ Chargement du bilan...
      </div>
    );
  }

  // Ne pas afficher d'erreur si c'est juste que le backend n'est pas disponible
  // Le tableau sera vide, ce qui est moins intrusif
  if (error && !error.includes('Impossible de se connecter')) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ color: '#dc2626', marginBottom: '8px' }}>❌ Erreur</div>
        <div style={{ color: '#6b7280', fontSize: '14px', marginBottom: '16px' }}>{error}</div>
        <button
          onClick={() => loadBilanData()}
          style={{
            padding: '8px 16px',
            backgroundColor: '#3b82f6',
            color: '#ffffff',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          Réessayer
        </button>
      </div>
    );
  }

  if (categories.length === 0) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
        Aucune catégorie configurée dans la card de configuration du bilan.
        <br />
        <small style={{ fontSize: '12px', color: '#9ca3af', marginTop: '8px', display: 'block' }}>
          Configurez des catégories dans la card "Configuration du bilan" ci-dessus.
        </small>
      </div>
    );
  }

  // Si aucune donnée mais des catégories configurées, c'est probablement que le backend n'est pas accessible
  const hasData = Object.keys(amounts).length > 0 && Object.values(amounts).some(yearData => Object.keys(yearData).length > 0);
  if (!hasData && categories.length > 0 && !loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
        <div style={{ marginBottom: '16px' }}>⏳ Aucune donnée disponible</div>
        <small style={{ fontSize: '12px', color: '#9ca3af', display: 'block', marginBottom: '16px' }}>
          Le backend n'est peut-être pas démarré. Vérifiez que le serveur est accessible sur http://localhost:8000
        </small>
        <button
          onClick={() => loadBilanData()}
          style={{
            padding: '8px 16px',
            backgroundColor: '#3b82f6',
            color: '#ffffff',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          Réessayer
        </button>
      </div>
    );
  }

  // STEP 10.8.3 - Calculer les totaux par niveau A (ACTIF et PASSIF)
  const calculateTypeTotal = (type: 'ACTIF' | 'PASSIF', year: number): number => {
    const groupedCategories = getGroupedCategories();
    let total = 0;

    if (type === 'ACTIF') {
      // TOTAL ACTIF = Actif immobilisé + Actif circulant
      const actifGroups = groupedCategories.filter(g => g.type === 'ACTIF');
      actifGroups.forEach(group => {
        total += calculateSubCategoryTotal(group.subCategory, year);
      });
    } else {
      // TOTAL PASSIF = Capitaux propres + Trésorerie passive + Dettes financières
      const passifGroups = groupedCategories.filter(g => g.type === 'PASSIF');
      passifGroups.forEach(group => {
        total += calculateSubCategoryTotal(group.subCategory, year);
      });
    }

    return total;
  };

  // STEP 10.8.2 & 10.8.3 - Afficher les catégories groupées par sous-catégorie avec totaux et niveaux A
  const groupedCategories = getGroupedCategories();
  console.log('📊 [BilanTable] RENDU - Groupes:', groupedCategories.length);
  console.log('📊 [BilanTable] Groupes:', groupedCategories);

  return (
    <div style={{ 
      backgroundColor: 'white', 
      borderRadius: '8px', 
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      padding: '24px',
      overflowX: 'auto'
    }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '600px' }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
            <th style={{ 
              padding: '12px', 
              textAlign: 'left', 
              fontWeight: '600', 
              color: '#374151',
              width: '30%'
            }}>
              Bilan
            </th>
            {years.map(year => (
              <th key={year} style={{ 
                padding: '12px', 
                textAlign: 'right', 
                fontWeight: '600', 
                color: '#374151',
                width: `${70 / years.length}%`
              }}>
                {year}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {(() => {
            const rows: React.ReactNode[] = [];
            let currentType: 'ACTIF' | 'PASSIF' | null = null;

            groupedCategories.forEach((group, groupIndex) => {
              // STEP 10.8.3 - Ajouter la ligne de niveau A (ACTIF ou PASSIF) si changement de type
              if (currentType !== group.type) {
                currentType = group.type as 'ACTIF' | 'PASSIF';
                const typeTotal = years.map(year => calculateTypeTotal(currentType!, year));
                
                rows.push(
                  <tr 
                    key={`type-${currentType}`}
                    style={{ 
                      borderTop: '2px solid #d1d5db',
                      borderBottom: '2px solid #d1d5db',
                      backgroundColor: '#e5e7eb'
                    }}
                  >
                    <td style={{ 
                      padding: '14px 12px',
                      color: '#111827',
                      fontWeight: '700',
                      fontSize: '15px'
                    }}>
                      {currentType}
                    </td>
                    {years.map((year, yearIndex) => {
                      const total = typeTotal[yearIndex];
                      return (
                        <td 
                          key={year} 
                          style={{ 
                            padding: '14px 12px',
                            textAlign: 'right',
                            color: '#111827',
                            fontWeight: '700',
                            fontSize: '15px'
                          }}
                        >
                          {formatAmount(total)}
                        </td>
                      );
                    })}
                  </tr>
                );
              }
              
              // Ligne de sous-catégorie (niveau B) avec total
              const subCategoryTotal = years.map(year => calculateSubCategoryTotal(group.subCategory, year));
              rows.push(
                <tr 
                  key={`subcategory-${group.subCategory}`}
                  style={{ 
                    borderBottom: '1px solid #e5e7eb',
                    backgroundColor: '#f9fafb'
                  }}
                >
                  <td style={{ 
                    padding: '12px',
                    color: '#111827',
                    fontWeight: '600'
                  }}>
                    &nbsp;&nbsp;{group.subCategory}
                  </td>
                  {years.map((year, yearIndex) => {
                    const total = subCategoryTotal[yearIndex];
                    return (
                      <td 
                        key={year} 
                        style={{ 
                          padding: '12px',
                          textAlign: 'right',
                          color: '#111827',
                          fontWeight: '600'
                        }}
                      >
                        {formatAmount(total)}
                      </td>
                    );
                  })}
                </tr>
              );

              // Lignes des catégories (niveau C) de cette sous-catégorie
              group.categories.forEach((categoryItem, catIndex) => {
                // On calculera le montant dans le map des années ci-dessous
                const isLastInGroup = catIndex === group.categories.length - 1;
                const isLastGroup = groupIndex === groupedCategories.length - 1;
                
                rows.push(
                  <tr 
                    key={categoryItem.name}
                    style={{ 
                      borderBottom: (isLastInGroup && isLastGroup) ? 'none' : '1px solid #e5e7eb'
                    }}
                  >
                    <td style={{ 
                      padding: '12px',
                      color: '#111827'
                    }}>
                      &nbsp;&nbsp;&nbsp;&nbsp;{categoryItem.name}
                    </td>
                    {years.map(year => {
                      // STEP 10.8.4.1 & 10.8.4.3: Utiliser getDisplayAmount pour "Amortissements cumulés" et "Résultat de l'exercice"
                      const amount = getCategoryAmount(categoryItem.name, year);
                      const displayAmount = getDisplayAmount(categoryItem.name, amount);
                      const isNegative = isNegativeAmountCategory(categoryItem.name, displayAmount); // Vérifier le signe pour "Résultat de l'exercice"
                      return (
                        <td 
                          key={year} 
                          style={{ 
                            padding: '12px',
                            textAlign: 'right',
                            color: isNegative ? '#dc2626' : '#111827',
                            fontWeight: isNegative ? '600' : 'normal'
                          }}
                        >
                          {formatAmount(displayAmount)}
                        </td>
                      );
                    })}
                  </tr>
                );
              });
            });

            return <>{rows}</>;
          })()}
        </tbody>
      </table>
    </div>
  );
}

