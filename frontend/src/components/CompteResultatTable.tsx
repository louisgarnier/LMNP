/**
 * CompteResultatTable component - Tableau croisé du compte de résultat
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect } from 'react';
import { compteResultatAPI, CompteResultatMapping, CompteResultatCalculateResponse, transactionsAPI } from '@/api/client';

interface CompteResultatTableProps {
  refreshKey?: number; // Pour forcer le rechargement
}

// Catégories comptables prédéfinies (ordre fixe, groupées par type)
const PRODUITS_CATEGORIES = [
  'Loyers hors charge encaissés',
  'Charges locatives payées par locataires',
  'Autres revenus',
];

const CHARGES_CATEGORIES = [
  'Charges de copropriété hors fonds travaux',
  'Fluides non refacturés',
  'Assurances',
  'Honoraires',
  'Travaux et mobilier',
  'Impôts et taxes',
  'Charges d\'amortissements',
  'Autres charges diverses',
  'Coût du financement (hors remboursement du capital)',
];

// Catégories spéciales (toujours affichées, même sans mapping)
const SPECIAL_CATEGORIES = [
  'Charges d\'amortissements',
  'Coût du financement (hors remboursement du capital)',
];

// Fonction pour récupérer les années à afficher depuis les transactions
const getYearsToDisplay = async (): Promise<number[]> => {
  const currentYear = new Date().getFullYear();
  
  try {
    // Récupérer la première transaction (triée par date croissante)
    const firstTransactionResponse = await transactionsAPI.getAll(
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
    console.error('Erreur lors de la récupération de la première transaction:', error);
    // En cas d'erreur, utiliser 2020 comme valeur par défaut
    const years: number[] = [];
    for (let year = 2020; year <= currentYear; year++) {
      years.push(year);
    }
    return years;
  }
};

export default function CompteResultatTable({ refreshKey }: CompteResultatTableProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [years, setYears] = useState<number[]>([]);
  const [mappings, setMappings] = useState<CompteResultatMapping[]>([]);
  const [data, setData] = useState<CompteResultatCalculateResponse | null>(null);

  // Calculer les années à afficher depuis les transactions
  useEffect(() => {
    const loadYears = async () => {
      const yearsToDisplay = await getYearsToDisplay();
      setYears(yearsToDisplay);
    };
    loadYears();
  }, []);

  // Charger les mappings et les données depuis l'API
  useEffect(() => {
    if (years.length > 0) {
      loadData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey, years.length]);

  const loadData = async () => {
    if (years.length === 0) return;
    
    try {
      setLoading(true);
      setError(null);
      
      // Charger les mappings
      const mappingsResponse = await compteResultatAPI.getMappings();
      setMappings(mappingsResponse.items || []);
      
      // Charger les données calculées
      const calculateResponse = await compteResultatAPI.calculate(years);
      setData(calculateResponse);
    } catch (err: any) {
      console.error('Erreur lors du chargement des données:', err);
      setError(err.message || 'Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  // Déterminer quelles catégories afficher
  // - Catégories spéciales : toujours affichées
  // - Autres catégories : uniquement si elles ont un mapping avec des level_1_values
  // - Catégories personnalisées : affichées si elles ont un mapping (type déterminé depuis le mapping)
  const getCategoriesToDisplay = () => {
    const categoriesToDisplay: {
      type: 'Produits d\'exploitation' | 'Charges d\'exploitation';
      category: string;
      hasMapping: boolean;
    }[] = [];

    // Créer un Map des catégories avec leurs mappings et types
    const categoriesMap = new Map<string, { hasLevel1Values: boolean; type: string | null }>();
    mappings.forEach(mapping => {
      let hasLevel1Values = false;
      if (mapping.level_1_values) {
        try {
          const level1Values = JSON.parse(mapping.level_1_values);
          if (Array.isArray(level1Values) && level1Values.length > 0) {
            hasLevel1Values = true;
          }
        } catch (e) {
          // Ignorer les erreurs de parsing
        }
      }
      categoriesMap.set(mapping.category_name, {
        hasLevel1Values,
        type: mapping.type,
      });
    });

    // Ajouter les catégories Produits d'exploitation prédéfinies qui ont des mappings
    PRODUITS_CATEGORIES.forEach(category => {
      const mappingInfo = categoriesMap.get(category);
      if (mappingInfo?.hasLevel1Values || SPECIAL_CATEGORIES.includes(category)) {
        categoriesToDisplay.push({
          type: 'Produits d\'exploitation',
          category,
          hasMapping: mappingInfo?.hasLevel1Values || false,
        });
      }
    });

    // Ajouter les catégories Charges d'exploitation prédéfinies qui ont des mappings
    CHARGES_CATEGORIES.forEach(category => {
      const mappingInfo = categoriesMap.get(category);
      // Les catégories spéciales sont TOUJOURS affichées, même sans mapping
      if (SPECIAL_CATEGORIES.includes(category)) {
        categoriesToDisplay.push({
          type: 'Charges d\'exploitation',
          category,
          hasMapping: mappingInfo?.hasLevel1Values || false,
        });
      } else if (mappingInfo?.hasLevel1Values) {
        // Les autres catégories nécessitent un mapping avec des level_1_values
        categoriesToDisplay.push({
          type: 'Charges d\'exploitation',
          category,
          hasMapping: true,
        });
      }
    });

    // Ajouter les catégories personnalisées (celles qui ne sont pas dans les listes prédéfinies)
    mappings.forEach(mapping => {
      const isPredefined = PRODUITS_CATEGORIES.includes(mapping.category_name) || 
                          CHARGES_CATEGORIES.includes(mapping.category_name);
      
      if (!isPredefined) {
        // Catégorie personnalisée : déterminer le type depuis le mapping
        const type = mapping.type === "Produits d'exploitation" 
          ? 'Produits d\'exploitation' 
          : 'Charges d\'exploitation'; // Par défaut Charges si type null ou autre
        
        // Afficher si elle a des level_1_values ou si c'est une catégorie spéciale
        const mappingInfo = categoriesMap.get(mapping.category_name);
        if (mappingInfo?.hasLevel1Values || SPECIAL_CATEGORIES.includes(mapping.category_name)) {
          categoriesToDisplay.push({
            type,
            category: mapping.category_name,
            hasMapping: mappingInfo?.hasLevel1Values || false,
          });
        }
      }
    });

    return categoriesToDisplay;
  };

  const categoriesToDisplay = getCategoriesToDisplay();
  const produitsCategories = categoriesToDisplay.filter(c => c.type === 'Produits d\'exploitation');
  const chargesCategories = categoriesToDisplay.filter(c => c.type === 'Charges d\'exploitation');

  // Fonction pour obtenir le montant d'une catégorie pour une année donnée
  const getAmount = (category: string, year: number, type: 'Produits d\'exploitation' | 'Charges d\'exploitation'): number | null => {
    if (!data || !data.results[year]) {
      return null;
    }
    
    const yearData = data.results[year];
    
    // Catégories spéciales
    if (category === "Charges d'amortissements") {
      return yearData.amortissements !== 0 ? Math.abs(yearData.amortissements) : null;
    }
    if (category === "Coût du financement (hors remboursement du capital)") {
      // Utiliser DIRECTEMENT la valeur du backend (cout_financement)
      // Le backend retourne déjà la bonne valeur, on l'affiche telle quelle
      const cout = yearData.cout_financement;
      if (cout === null || cout === undefined || cout === 0) {
        return null;
      }
      // Le backend retourne une valeur positive, on l'affiche telle quelle
      return Math.abs(cout);
    }
    
    // Catégories normales
    if (type === 'Produits d\'exploitation') {
      return yearData.produits[category] ?? null;
    } else {
      // Les charges peuvent être stockées en négatif, prendre la valeur absolue pour l'affichage
      const amount = yearData.charges[category];
      return amount !== undefined && amount !== null ? Math.abs(amount) : null;
    }
  };

  // Fonction pour formater un montant
  const formatAmount = (amount: number | null): string => {
    if (amount === null) return '-';
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  // Calculer les totaux en sommant les valeurs affichées dans le tableau
  const getTotalProduits = (year: number): number | null => {
    if (!data || !data.results[year]) return null;
    let total = 0;
    produitsCategories.forEach(({ category }) => {
      const amount = getAmount(category, year, 'Produits d\'exploitation');
      if (amount !== null) {
        total += amount;
      }
    });
    return total !== 0 ? total : null;
  };

  const getTotalCharges = (year: number): number | null => {
    if (!data || !data.results[year]) return null;
    let total = 0;
    chargesCategories.forEach(({ category }) => {
      const amount = getAmount(category, year, 'Charges d\'exploitation');
      if (amount !== null) {
        // Les charges peuvent être stockées en négatif, prendre la valeur absolue pour le total
        total += Math.abs(amount);
      }
    });
    return total !== 0 ? total : null;
  };

  const getResultatExploitation = (year: number): number | null => {
    const totalProduits = getTotalProduits(year);
    const totalCharges = getTotalCharges(year);
    if (totalProduits === null && totalCharges === null) return null;
    const produits = totalProduits ?? 0;
    const charges = totalCharges ?? 0; // getTotalCharges retourne déjà la valeur absolue
    const resultat = produits - charges; // Produits - Charges (charges en valeur absolue)
    return resultat !== 0 ? resultat : null;
  };

  const getResultatNet = (year: number): number | null => {
    // Le résultat net est égal au résultat d'exploitation
    return getResultatExploitation(year);
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
      </div>
    );
  }

  // Si aucune catégorie à afficher, afficher un message
  if (categoriesToDisplay.length === 0) {
    return (
      <div
        style={{
          backgroundColor: '#ffffff',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          padding: '40px',
          marginBottom: '24px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
          textAlign: 'center',
          color: '#6b7280',
        }}
      >
        <div style={{ marginBottom: '8px', fontSize: '16px', fontWeight: '600' }}>ℹ️ Aucune catégorie configurée</div>
        <div style={{ fontSize: '14px', marginBottom: '16px' }}>
          Configurez les mappings dans le panneau de configuration ci-dessus.<br />
          Le tableau affichera uniquement les catégories avec des mappings configurés.
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        backgroundColor: '#ffffff',
        border: '1px solid #e5e7eb',
        borderRadius: '8px',
        padding: '20px',
        marginBottom: '24px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
      }}
    >
      <h3 style={{ margin: '0 0 20px 0', fontSize: '18px', fontWeight: '600', color: '#111827' }}>
        Compte de résultat
      </h3>
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
            {/* Total des produits d'exploitation (ligne de total, fond gris) - uniquement s'il y a des produits */}
            {produitsCategories.length > 0 && (
              <>
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
                    Total des produits d'exploitation
                  </td>
                  {years.map((year) => (
                    <td
                      key={year}
                      style={{
                        padding: '12px',
                        textAlign: 'right',
                        backgroundColor: '#e5e7eb',
                        border: '1px solid #d1d5db',
                        fontWeight: '700',
                        color: '#111827',
                      }}
                    >
                      {formatAmount(getTotalProduits(year))}
                    </td>
                  ))}
                </tr>
                {/* Produits d'exploitation (catégories indentées) - uniquement celles avec mappings */}
                {produitsCategories.map(({ category }) => (
                  <tr key={category}>
                    <td
                      style={{
                        padding: '12px 12px 12px 32px',
                        backgroundColor: '#ffffff',
                        border: '1px solid #e5e7eb',
                        color: '#111827',
                      }}
                    >
                      {category}
                    </td>
                    {years.map((year) => {
                      const amount = getAmount(category, year, 'Produits d\'exploitation');
                      return (
                        <td
                          key={year}
                          style={{
                            padding: '12px',
                            textAlign: 'right',
                            backgroundColor: '#ffffff',
                            border: '1px solid #e5e7eb',
                            color: '#111827',
                          }}
                        >
                          {formatAmount(amount)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </>
            )}
            {/* Total des charges d'exploitation (ligne de total, fond gris) - uniquement s'il y a des charges */}
            {chargesCategories.length > 0 && (
              <>
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
                    Total des charges d'exploitation
                  </td>
                  {years.map((year) => (
                    <td
                      key={year}
                      style={{
                        padding: '12px',
                        textAlign: 'right',
                        backgroundColor: '#e5e7eb',
                        border: '1px solid #d1d5db',
                        fontWeight: '700',
                        color: '#111827',
                      }}
                    >
                      {formatAmount(getTotalCharges(year))}
                    </td>
                  ))}
                </tr>
                {/* Charges d'exploitation (catégories indentées) - uniquement celles avec mappings ou spéciales */}
                {chargesCategories.map(({ category }) => (
                  <tr key={category}>
                    <td
                      style={{
                        padding: '12px 12px 12px 32px',
                        backgroundColor: '#ffffff',
                        border: '1px solid #e5e7eb',
                        color: '#111827',
                      }}
                    >
                      {category}
                    </td>
                    {years.map((year) => {
                      const amount = getAmount(category, year, 'Charges d\'exploitation');
                      // Afficher un message si catégorie spéciale sans données
                      const isSpecialCategory = category === "Charges d'amortissements" || 
                                                category === "Coût du financement (hors remboursement du capital)";
                      const displayText = isSpecialCategory && amount === null 
                        ? (category === "Charges d'amortissements" 
                            ? "Aucune donnée d'amortissement" 
                            : "Aucun crédit configuré")
                        : formatAmount(amount);
                      
                      return (
                        <td
                          key={year}
                          style={{
                            padding: '12px',
                            textAlign: 'right',
                            backgroundColor: '#ffffff',
                            border: '1px solid #e5e7eb',
                            color: amount === null && isSpecialCategory ? '#9ca3af' : '#111827',
                            fontSize: amount === null && isSpecialCategory ? '11px' : '13px',
                            fontStyle: amount === null && isSpecialCategory ? 'italic' : 'normal',
                          }}
                        >
                          {displayText}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </>
            )}
            {/* Résultat d'exploitation (ligne de total, fond gris) */}
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
                Résultat d'exploitation
              </td>
              {years.map((year) => (
                <td
                  key={year}
                  style={{
                    padding: '12px',
                    textAlign: 'right',
                    backgroundColor: '#e5e7eb',
                    border: '1px solid #d1d5db',
                    fontWeight: '700',
                    color: '#111827',
                  }}
                >
                  {formatAmount(getResultatExploitation(year))}
                </td>
              ))}
            </tr>
            {/* Résultat net de l'exercice (ligne de total, fond gris, texte magenta) */}
            <tr>
              <td
                style={{
                  padding: '12px',
                  backgroundColor: '#e5e7eb',
                  border: '1px solid #d1d5db',
                  fontWeight: '700',
                  color: '#d946ef', // Magenta
                }}
              >
                Résultat net de l'exercice
              </td>
              {years.map((year) => (
                <td
                  key={year}
                  style={{
                    padding: '12px',
                    textAlign: 'right',
                    backgroundColor: '#e5e7eb',
                    border: '1px solid #d1d5db',
                    fontWeight: '700',
                    color: '#d946ef', // Magenta
                  }}
                >
                  {formatAmount(getResultatNet(year))}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
