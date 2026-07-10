/**
 * Card de prévisions Bilan
 * 
 * Affiche les catégories Compte bancaire et Compte courant d'associé
 * avec leurs valeurs réelles et prévues.
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect } from 'react';
import { useProperty } from '@/contexts/PropertyContext';
import { prorataAPI, ProRataSettings } from '@/api/client';
import { computeCompteBancairePrevu, extractCategory } from '@/utils/bilanProjection';

interface Props {
  year: number;
  onConfigChange?: () => void;
  refreshKey?: number;
}

interface BilanCategoryData {
  category_name: string;
  real_current_year: number;
  real_previous_year: number;
}

export default function BilanForecastCard({ year, onConfigChange, refreshKey }: Props) {
  const { activeProperty } = useProperty();
  const [settings, setSettings] = useState<ProRataSettings | null>(null);
  const [compteBancaire, setCompteBancaire] = useState<BilanCategoryData | null>(null);
  const [compteCourant, setCompteCourant] = useState<BilanCategoryData | null>(null);
  const [totalCRPrevisionnel, setTotalCRPrevisionnel] = useState<number>(0);
  const [totalCreditAnnuel, setTotalCreditAnnuel] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isPinned, setIsPinned] = useState(false);

  useEffect(() => {
    if (!activeProperty?.id) return;

    const loadData = async () => {
      setIsLoading(true);
      try {
        // Récupérer les settings
        const settingsData = await prorataAPI.getSettings(activeProperty.id);
        setSettings(settingsData);

        // Récupérer les données du Bilan via l'API
        const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        
        // Année en cours
        const responseN = await fetch(
          `${API_BASE_URL}/api/bilan/calculate?property_id=${activeProperty.id}&years=${year}`,
          { headers: { 'Content-Type': 'application/json' } }
        );
        
        // Année précédente
        const responseN1 = await fetch(
          `${API_BASE_URL}/api/bilan/calculate?property_id=${activeProperty.id}&years=${year - 1}`,
          { headers: { 'Content-Type': 'application/json' } }
        );

        if (responseN.ok && responseN1.ok) {
          const dataN = await responseN.json();
          const dataN1 = await responseN1.json();

          // Extraire les données du bilan pour l'année en cours et l'année précédente
          const bilanN = dataN.results?.[String(year)];
          const bilanN1 = dataN1.results?.[String(year - 1)];

          setCompteBancaire({
            category_name: 'Compte bancaire',
            real_current_year: extractCategory(bilanN, 'actif', 'Compte bancaire'),
            real_previous_year: extractCategory(bilanN1, 'actif', 'Compte bancaire'),
          });

          setCompteCourant({
            category_name: "Compte courant d'associé",
            real_current_year: extractCategory(bilanN, 'passif', "Compte courant d'associé"),
            real_previous_year: extractCategory(bilanN1, 'passif', "Compte courant d'associé"),
          });
        }

        // Récupérer le total CR prévisionnel depuis les configs forecast
        const configsResponse = await prorataAPI.getConfigs(activeProperty.id, year, 'compte_resultat');
        const totalPrevisionnel = configsResponse.reduce((sum: number, config: any) => {
          return sum + (config.base_annual_amount || 0);
        }, 0);
        setTotalCRPrevisionnel(totalPrevisionnel);

        // Récupérer le total crédit annuel depuis l'API loan-payments
        const creditResponse = await fetch(
          `${API_BASE_URL}/api/loan-payments?property_id=${activeProperty.id}`,
          { headers: { 'Content-Type': 'application/json' } }
        );
        if (creditResponse.ok) {
          const creditData = await creditResponse.json();
          const items = creditData.items || [];
          // Filtrer par année en vérifiant la colonne date
          const itemsForYear = items.filter((item: any) => {
            const itemDate = new Date(item.date);
            return itemDate.getFullYear() === year;
          });
          const totalCredit = itemsForYear.reduce((sum: number, item: any) => {
            return sum + (item.capital || 0) + (item.interest || 0) + (item.insurance || 0);
          }, 0);
          setTotalCreditAnnuel(totalCredit);
        }
        
      } catch (err) {
        console.error('[BilanForecastCard] Error loading data:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [activeProperty?.id, year, refreshKey]);

  const formatEuro = (amount: number) => {
    return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(amount);
  };

  if (isLoading) {
    return (
      <div style={{ 
        padding: '20px', 
        backgroundColor: 'white', 
        borderRadius: '8px', 
        border: '1px solid #e5e7eb',
        marginTop: '24px',
        color: '#666' 
      }}>
        ⏳ Chargement des prévisions Bilan...
      </div>
    );
  }

  // Ne pas afficher si prorata_enabled n'est pas activé
  if (!settings?.prorata_enabled) {
    return null;
  }

  return (
    <div style={{ 
      backgroundColor: 'white', 
      borderRadius: '8px', 
      border: '1px solid #e5e7eb',
      marginTop: '24px',
      padding: '20px'
    }}>
      {/* En-tête de la card */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: isPinned ? '16px' : 0,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            flex: 1,
            cursor: 'pointer',
          }}
          onClick={() => setIsPinned(!isPinned)}
        >
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '600', color: '#1e3a5f' }}>
            ⚙️ Prévisions annuelles - Bilan
          </h3>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setIsPinned(!isPinned);
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '32px',
              height: '32px',
              padding: '0',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              backgroundColor: '#ffffff',
              cursor: 'pointer',
              fontSize: '16px',
            }}
            title={isPinned ? 'Replier la card' : 'Déplier la card'}
          >
            {isPinned ? '📌' : '📍'}
          </button>
        </div>
      </div>

      {/* Contenu (visible seulement si épinglé) */}
      {isPinned && (
        <>
          {/* Message indiquant que les prévisions sont héritées du CR */}
          <div style={{ 
            padding: '12px 16px', 
            backgroundColor: '#f0f9ff', 
            borderRadius: '6px',
            marginBottom: '16px',
            color: '#0369a1',
            fontSize: '14px',
          }}>
            ✅ Prévision année en cours activée (Cf Compte de résultat)
          </div>

          {/* Tableau des catégories */}
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <thead>
              <tr style={{ backgroundColor: '#f9fafb' }}>
                <th style={{ padding: '10px', textAlign: 'left', borderBottom: '2px solid #e5e7eb' }}>
                  Catégorie
                </th>
                <th style={{ padding: '10px', textAlign: 'right', borderBottom: '2px solid #e5e7eb', width: '150px' }}>
                  Réel {year - 1}
                </th>
                <th style={{ padding: '10px', textAlign: 'right', borderBottom: '2px solid #e5e7eb', width: '150px' }}>
                  Réel {year}
                </th>
                <th style={{ padding: '10px', textAlign: 'right', borderBottom: '2px solid #e5e7eb', width: '150px', backgroundColor: '#f0f9ff' }}>
                  Prévu {year} (€)
                </th>
                <th style={{ padding: '10px', textAlign: 'right', borderBottom: '2px solid #e5e7eb', width: '120px' }}>
                  Variation
                </th>
              </tr>
            </thead>
            <tbody>
              {/* Compte bancaire */}
              {compteBancaire && (
                <tr>
                  <td style={{ padding: '10px', borderBottom: '1px solid #e5e7eb', fontWeight: '500' }}>
                    🏦 {compteBancaire.category_name}
                  </td>
                  <td style={{ padding: '10px', textAlign: 'right', borderBottom: '1px solid #e5e7eb', color: '#6b7280' }}>
                    {formatEuro(compteBancaire.real_previous_year)}
                  </td>
                  <td style={{ 
                    padding: '10px', 
                    textAlign: 'right', 
                    borderBottom: '1px solid #e5e7eb',
                    fontWeight: '600',
                    color: compteBancaire.real_current_year >= 0 ? '#059669' : '#dc2626',
                  }}>
                    {formatEuro(compteBancaire.real_current_year)}
                  </td>
                  {(() => {
                    // Compte bancaire prévu = Réel N-1 + Total CR Prévisionnel - Crédit annuel + Variation CCA
                    const variationCCA = compteCourant ? (compteCourant.real_current_year - compteCourant.real_previous_year) : 0;
                    const compteBancairePrevu = computeCompteBancairePrevu({
                      reelN1: compteBancaire.real_previous_year,
                      totalCrPrevisionnel: totalCRPrevisionnel,
                      creditAnnuel: totalCreditAnnuel,
                      variationCca: variationCCA,
                    });
                    return (
                      <td style={{ 
                        padding: '10px', 
                        textAlign: 'right', 
                        borderBottom: '1px solid #e5e7eb', 
                        backgroundColor: '#e0f2fe',
                        fontWeight: '600',
                        color: compteBancairePrevu >= 0 ? '#059669' : '#dc2626',
                      }}>
                        {formatEuro(compteBancairePrevu)}
                      </td>
                    );
                  })()}
                  <td style={{ 
                    padding: '10px', 
                    textAlign: 'right', 
                    borderBottom: '1px solid #e5e7eb',
                    color: (compteBancaire.real_current_year - compteBancaire.real_previous_year) >= 0 ? '#059669' : '#dc2626',
                  }}>
                    {formatEuro(compteBancaire.real_current_year - compteBancaire.real_previous_year)}
                  </td>
                </tr>
              )}

              {/* Compte courant d'associé */}
              {compteCourant && (
                <tr>
                  <td style={{ padding: '10px', borderBottom: '1px solid #e5e7eb', fontWeight: '500' }}>
                    💰 {compteCourant.category_name}
                  </td>
                  <td style={{ padding: '10px', textAlign: 'right', borderBottom: '1px solid #e5e7eb', color: '#6b7280' }}>
                    {formatEuro(compteCourant.real_previous_year)}
                  </td>
                  <td style={{ 
                    padding: '10px', 
                    textAlign: 'right', 
                    borderBottom: '1px solid #e5e7eb',
                    fontWeight: '600',
                    color: compteCourant.real_current_year >= 0 ? '#059669' : '#dc2626',
                  }}>
                    {formatEuro(compteCourant.real_current_year)}
                  </td>
                  <td style={{ padding: '10px', textAlign: 'right', borderBottom: '1px solid #e5e7eb', backgroundColor: '#f0f9ff', color: '#94a3b8' }}>
                    —
                  </td>
                  <td style={{ 
                    padding: '10px', 
                    textAlign: 'right', 
                    borderBottom: '1px solid #e5e7eb',
                    color: (compteCourant.real_current_year - compteCourant.real_previous_year) >= 0 ? '#059669' : '#dc2626',
                  }}>
                    {formatEuro(compteCourant.real_current_year - compteCourant.real_previous_year)}
                  </td>
                </tr>
              )}

              {/* Total CR Prévisionnel */}
              <tr style={{ backgroundColor: '#f1f5f9' }}>
                <td style={{ 
                  padding: '10px', 
                  borderTop: '2px solid #e5e7eb',
                  fontWeight: '600',
                  color: '#1e3a5f',
                }}>
                  📊 Total CR Prévisionnel {year}
                </td>
                <td style={{ padding: '10px', borderTop: '2px solid #e5e7eb', textAlign: 'right', color: '#94a3b8' }}>
                  —
                </td>
                <td style={{ padding: '10px', borderTop: '2px solid #e5e7eb', textAlign: 'right', color: '#94a3b8' }}>
                  —
                </td>
                <td style={{ 
                  padding: '10px', 
                  textAlign: 'right', 
                  borderTop: '2px solid #e5e7eb',
                  fontWeight: '600',
                  backgroundColor: '#e0f2fe',
                  color: totalCRPrevisionnel >= 0 ? '#059669' : '#dc2626',
                }}>
                  {formatEuro(totalCRPrevisionnel)}
                </td>
                <td style={{ padding: '10px', borderTop: '2px solid #e5e7eb', textAlign: 'right', color: '#94a3b8' }}>
                  —
                </td>
              </tr>

              {/* Crédit annuel */}
              <tr style={{ backgroundColor: '#f1f5f9' }}>
                <td style={{ 
                  padding: '10px', 
                  borderTop: '1px solid #e5e7eb',
                  fontWeight: '600',
                  color: '#1e3a5f',
                }}>
                  💳 Crédit annuel {year}
                </td>
                <td style={{ padding: '10px', borderTop: '1px solid #e5e7eb', textAlign: 'right', color: '#94a3b8' }}>
                  —
                </td>
                <td style={{ padding: '10px', borderTop: '1px solid #e5e7eb', textAlign: 'right', color: '#94a3b8' }}>
                  —
                </td>
                <td style={{ 
                  padding: '10px', 
                  textAlign: 'right', 
                  borderTop: '1px solid #e5e7eb',
                  fontWeight: '600',
                  backgroundColor: '#e0f2fe',
                  color: '#dc2626',
                }}>
                  -{formatEuro(totalCreditAnnuel)}
                </td>
                <td style={{ padding: '10px', borderTop: '1px solid #e5e7eb', textAlign: 'right', color: '#94a3b8' }}>
                  —
                </td>
              </tr>
            </tbody>
          </table>

          <div style={{ marginTop: '16px', fontSize: '12px', color: '#6b7280' }}>
            💡 Ces valeurs sont calculées automatiquement à partir des transactions réelles.
          </div>
        </>
      )}
    </div>
  );
}
