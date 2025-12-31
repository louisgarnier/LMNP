/**
 * CompteResultatTable component - Tableau du compte de résultat
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import React, { useState, useEffect } from 'react';
import { compteResultatAPI, CompteResultatMapping, transactionsAPI, Transaction } from '@/api/client';

interface CompteResultatTableProps {
  refreshKey?: number; // Pour forcer le rechargement
}

export default function CompteResultatTable({ refreshKey }: CompteResultatTableProps) {
  const [mappings, setMappings] = useState<CompteResultatMapping[]>([]);
  const [years, setYears] = useState<number[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [amounts, setAmounts] = useState<Record<string, Record<string, number>>>({}); // {year: {category: amount}}
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Charger les mappings et calculer les années au montage et quand refreshKey change
  useEffect(() => {
    loadMappings();
    calculateYears();
  }, [refreshKey]);

  // Charger les montants quand les années et mappings sont prêts
  useEffect(() => {
    if (years.length > 0 && mappings.length > 0) {
      loadAmounts();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [years.length, mappings.length, refreshKey]);

  // Structure pour grouper les catégories par type
  interface CategoryGroup {
    type: 'Produits d\'exploitation' | 'Charges d\'exploitation';
    categories: string[];
  }

  const [categoryGroups, setCategoryGroups] = useState<CategoryGroup[]>([]);

  const loadMappings = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await compteResultatAPI.getMappings();
      const loadedMappings = response.mappings || [];
      setMappings(loadedMappings);
      
      // Extraire les catégories uniques et les grouper par type
      const uniqueCategories = Array.from(new Set(loadedMappings.map(m => m.category_name)));
      
      // Grouper par type
      const produitsCategories = uniqueCategories
        .filter(cat => getTypeForCategory(cat) === 'Produits d\'exploitation')
        .sort((a, b) => a.localeCompare(b));
      
      const chargesCategories = uniqueCategories
        .filter(cat => getTypeForCategory(cat) === 'Charges d\'exploitation')
        .sort((a, b) => a.localeCompare(b));
      
      const groups: CategoryGroup[] = [];
      if (produitsCategories.length > 0) {
        groups.push({ type: 'Produits d\'exploitation', categories: produitsCategories });
      }
      if (chargesCategories.length > 0) {
        groups.push({ type: 'Charges d\'exploitation', categories: chargesCategories });
      }
      
      setCategoryGroups(groups);
      
      // Garder aussi la liste plate pour compatibilité
      const sortedCategories = [...produitsCategories, ...chargesCategories];
      setCategories(sortedCategories);
    } catch (err: any) {
      console.error('Erreur lors du chargement des mappings:', err);
      setError(err.message || 'Erreur lors du chargement des mappings');
    } finally {
      setLoading(false);
    }
  };

  const calculateYears = async () => {
    try {
      // Récupérer toutes les transactions pour trouver la première date
      const transactions = await transactionsAPI.getAllForExport();
      
      if (transactions.length === 0) {
        // Si aucune transaction, utiliser l'année en cours uniquement
        const currentYear = new Date().getFullYear();
        setYears([currentYear]);
        return;
      }

      // Trouver la date minimale
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

      // Générer la liste des années de la première transaction jusqu'à l'année en cours
      const yearsList: number[] = [];
      for (let year = firstYear; year <= currentYear; year++) {
        yearsList.push(year);
      }
      
      setYears(yearsList);
    } catch (err: any) {
      console.error('Erreur lors du calcul des années:', err);
      // En cas d'erreur, utiliser l'année en cours uniquement
      const currentYear = new Date().getFullYear();
      setYears([currentYear]);
    }
  };

  const loadAmounts = async () => {
    if (years.length === 0) {
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await compteResultatAPI.calculateAmounts(years);
      setAmounts(response);
    } catch (err: any) {
      console.error('Erreur lors du chargement des montants:', err);
      setError(err.message || 'Erreur lors du chargement des montants');
    } finally {
      setLoading(false);
    }
  };

  // Fonction pour déduire le type selon la catégorie (identique à CompteResultatConfigCard)
  const PRODUITS_CATEGORIES = [
    'Loyers hors charge encaissés',
    'Charges locatives payées par locataires',
    'Autres revenus',
  ];

  function getTypeForCategory(categoryName: string): 'Produits d\'exploitation' | 'Charges d\'exploitation' {
    if (PRODUITS_CATEGORIES.includes(categoryName)) {
      return 'Produits d\'exploitation';
    }
    return 'Charges d\'exploitation';
  }

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

  // Fonction pour vérifier si une catégorie spéciale est configurée
  const isSpecialCategoryConfigured = (category: string): boolean => {
    const mapping = mappings.find(m => m.category_name === category);
    if (!mapping) return false;
    
    if (category === "Charges d'amortissements") {
      return mapping.amortization_view_id !== null && mapping.amortization_view_id !== undefined;
    }
    
    if (category === "Coût du financement (hors remboursement du capital)") {
      return mapping.selected_loan_ids !== null && 
             mapping.selected_loan_ids !== undefined && 
             Array.isArray(mapping.selected_loan_ids) && 
             mapping.selected_loan_ids.length > 0;
    }
    
    return true; // Catégories normales sont toujours "configurées"
  };

  // Fonction pour calculer les totaux par type pour chaque année
  const calculateTypeTotals = (group: CategoryGroup): number[] => {
    return years.map(year => {
      // Sommer les montants de toutes les catégories de ce type pour cette année
      return group.categories.reduce((sum, category) => {
        return sum + getCategoryAmount(category, year);
      }, 0);
    });
  };

  // Fonction pour calculer le résultat de l'exercice (Produits - Charges) pour chaque année
  const calculateResultatExercice = (): number[] => {
    return years.map(year => {
      // Trouver les groupes de produits et charges
      const produitsGroup = categoryGroups.find(g => g.type === 'Produits d\'exploitation');
      const chargesGroup = categoryGroups.find(g => g.type === 'Charges d\'exploitation');
      
      // Calculer le total des produits
      const totalProduits = produitsGroup 
        ? produitsGroup.categories.reduce((sum, category) => sum + getCategoryAmount(category, year), 0)
        : 0;
      
      // Calculer le total des charges
      const totalCharges = chargesGroup
        ? chargesGroup.categories.reduce((sum, category) => sum + getCategoryAmount(category, year), 0)
        : 0;
      
      // Résultat = Produits - Charges
      return totalProduits - totalCharges;
    });
  };

  // Fonction pour calculer le résultat cumulé (somme depuis la première année jusqu'à l'année en cours)
  const calculateResultatCumule = (): number[] => {
    const resultats = calculateResultatExercice();
    let cumul = 0;
    return resultats.map(resultat => {
      cumul += resultat;
      return cumul;
    });
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
        ⏳ Chargement du compte de résultat...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ color: '#dc2626', marginBottom: '8px' }}>❌ Erreur</div>
        <div style={{ color: '#6b7280', fontSize: '14px' }}>{error}</div>
        <button
          onClick={() => {
            loadMappings();
            calculateYears();
            if (years.length > 0) {
              loadAmounts();
            }
          }}
          style={{
            marginTop: '16px',
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

  if (mappings.length === 0 || categories.length === 0) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
        <div style={{ marginBottom: '8px', fontSize: '16px', fontWeight: '600' }}>ℹ️ Aucun mapping configuré</div>
        <div style={{ fontSize: '14px', marginBottom: '16px' }}>
          Configurez les mappings dans le panneau de configuration ci-dessus,<br />
          puis les montants seront calculés et affichés ici.
        </div>
      </div>
    );
  }

  if (years.length === 0) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
        ⏳ Calcul des années...
      </div>
    );
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table
        style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '13px',
        }}
      >
        <thead>
          <tr>
            <th
              style={{
                padding: '12px',
                textAlign: 'left',
                backgroundColor: '#f3f4f6',
                border: '1px solid #e5e7eb',
                fontWeight: '600',
                color: '#111827',
              }}
            >
              Compte de résultat
            </th>
            {years.map((year) => (
              <th
                key={year}
                style={{
                  padding: '12px',
                  textAlign: 'right',
                  backgroundColor: '#f3f4f6',
                  border: '1px solid #e5e7eb',
                  fontWeight: '600',
                  color: '#111827',
                }}
              >
                {year}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {categoryGroups.map((group) => {
            // Calculer les totaux pour ce type en sommant les montants des catégories
            const typeTotals = calculateTypeTotals(group);
            
            return (
              <React.Fragment key={group.type}>
                {/* Ligne de type avec totaux */}
                <tr>
                  <td
                    style={{
                      padding: '12px',
                      backgroundColor: '#e5e7eb',
                      border: '1px solid #d1d5db',
                      fontWeight: '700',
                      color: '#111827',
                    }}
                  >
                    {group.type}
                  </td>
                  {years.map((year, yearIndex) => {
                    const total = typeTotals[yearIndex];
                    const isNegative = total < 0;
                    return (
                      <td
                        key={year}
                        style={{
                          padding: '12px',
                          textAlign: 'right',
                          backgroundColor: '#e5e7eb',
                          border: '1px solid #d1d5db',
                          fontWeight: '700',
                          color: isNegative ? '#dc2626' : '#111827',
                        }}
                      >
                        {formatAmount(total)}
                      </td>
                    );
                  })}
                </tr>
                {/* Lignes de catégories sous ce type */}
                {group.categories.map((category) => {
                  const isSpecial = category === "Charges d'amortissements" || 
                                   category === "Coût du financement (hors remboursement du capital)";
                  const isConfigured = isSpecialCategoryConfigured(category);
                  
                  return (
                    <tr key={category}>
                      <td
                        style={{
                          padding: '12px 12px 12px 32px', // Indentation pour les catégories
                          backgroundColor: '#ffffff',
                          border: '1px solid #e5e7eb',
                          fontWeight: '500',
                          color: '#111827',
                        }}
                      >
                        {category}
                      </td>
                      {years.map((year) => {
                        // Récupérer le montant de cette catégorie pour cette année
                        const amount = getCategoryAmount(category, year);
                        const isNegative = amount < 0;
                        
                        // Afficher un message si catégorie spéciale non configurée
                        if (isSpecial && !isConfigured) {
                          return (
                            <td
                              key={year}
                              style={{
                                padding: '12px',
                                textAlign: 'right',
                                backgroundColor: '#ffffff',
                                border: '1px solid #e5e7eb',
                                color: '#9ca3af',
                                fontStyle: 'italic',
                                fontSize: '12px',
                              }}
                            >
                              {category === "Charges d'amortissements" ? "Vue non configurée" : "Crédits non configurés"}
                            </td>
                          );
                        }
                        
                        return (
                          <td
                            key={year}
                            style={{
                              padding: '12px',
                              textAlign: 'right',
                              backgroundColor: '#ffffff',
                              border: '1px solid #e5e7eb',
                              color: isNegative ? '#dc2626' : '#111827',
                            }}
                          >
                            {formatAmount(amount)}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </React.Fragment>
            );
          })}
          {/* Ligne Résultat de l'exercice */}
          <tr>
            <td
              style={{
                padding: '12px',
                backgroundColor: '#e5e7eb',
                border: '1px solid #d1d5db',
                fontWeight: '700',
                color: '#111827',
              }}
            >
              Résultat de l'exercice
            </td>
            {years.map((year, yearIndex) => {
              const resultatTotals = calculateResultatExercice();
              const resultat = resultatTotals[yearIndex];
              const isNegative = resultat < 0;
              return (
                <td
                  key={year}
                  style={{
                    padding: '12px',
                    textAlign: 'right',
                    backgroundColor: '#e5e7eb',
                    border: '1px solid #d1d5db',
                    fontWeight: '700',
                    color: isNegative ? '#dc2626' : '#111827',
                  }}
                >
                  {formatAmount(resultat)}
                </td>
              );
            })}
          </tr>
          {/* Ligne Résultat de l'exercice cumulé */}
          <tr>
            <td
              style={{
                padding: '12px',
                backgroundColor: '#d1d5db',
                border: '1px solid #9ca3af',
                fontWeight: '700',
                color: '#111827',
              }}
            >
              Résultat de l'exercice cumulé
            </td>
            {years.map((year, yearIndex) => {
              const resultatCumules = calculateResultatCumule();
              const cumul = resultatCumules[yearIndex];
              const isNegative = cumul < 0;
              return (
                <td
                  key={year}
                  style={{
                    padding: '12px',
                    textAlign: 'right',
                    backgroundColor: '#d1d5db',
                    border: '1px solid #9ca3af',
                    fontWeight: '700',
                    color: isNegative ? '#dc2626' : '#111827',
                  }}
                >
                  {formatAmount(cumul)}
                </td>
              );
            })}
          </tr>
        </tbody>
      </table>
    </div>
  );
}

