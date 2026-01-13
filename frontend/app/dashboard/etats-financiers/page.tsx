/**
 * États financiers page - Compte de résultat, Bilan, Liasse fiscale, Crédit
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import LoanConfigCard from '@/components/LoanConfigCard';
import LoanConfigSingleCard from '@/components/LoanConfigSingleCard';
import LoanPaymentFileUpload from '@/components/LoanPaymentFileUpload';
import LoanPaymentTable from '@/components/LoanPaymentTable';
import { loanConfigsAPI, LoanConfig, LoanConfigCreate, loanPaymentsAPI } from '@/api/client';

interface CreditTabContentProps {
  activeTab: string;
  hasCredit: boolean;
}

function CreditTabContent({ activeTab, hasCredit }: CreditTabContentProps) {
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [loanConfigs, setLoanConfigs] = useState<LoanConfig[]>([]);
  const [isLoadingConfigs, setIsLoadingConfigs] = useState(true);
  const [activeLoanName, setActiveLoanName] = useState<string | null>(null);
  const [hoveredLoanId, setHoveredLoanId] = useState<number | null>(null);

  // Charger les configurations de crédit au montage
  useEffect(() => {
    loadLoanConfigs();
  }, []);

  const loadLoanConfigs = async () => {
    try {
      setIsLoadingConfigs(true);
      const response = await loanConfigsAPI.getAll();
      const sortedConfigs = response.items.sort((a, b) => {
        // Trier par created_at si disponible, sinon par id
        const aDate = (a as any).created_at ? new Date((a as any).created_at).getTime() : a.id;
        const bDate = (b as any).created_at ? new Date((b as any).created_at).getTime() : b.id;
        return aDate - bDate;
      });
      setLoanConfigs(sortedConfigs);
      
      // Si des configurations existent et qu'aucun crédit n'est actif, utiliser le nom de la première
      if (sortedConfigs.length > 0 && !activeLoanName) {
        setActiveLoanName(sortedConfigs[0].name);
      } else if (sortedConfigs.length === 0) {
        setActiveLoanName(null);
      } else if (activeLoanName) {
        // Vérifier que le crédit actif existe toujours
        const activeConfig = sortedConfigs.find(c => c.name === activeLoanName);
        if (!activeConfig && sortedConfigs.length > 0) {
          // Le crédit actif n'existe plus, sélectionner le premier
          setActiveLoanName(sortedConfigs[0].name);
        }
      }
    } catch (error) {
      console.error('❌ [CreditTabContent] Erreur lors du chargement des configurations:', error);
      setLoanConfigs([]);
      setActiveLoanName(null);
    } finally {
      setIsLoadingConfigs(false);
    }
  };

  const handleImportComplete = () => {
    // Incrémenter le trigger pour forcer le rafraîchissement du tableau
    setRefreshTrigger(prev => prev + 1);
    // Recharger les configurations au cas où un nouveau crédit aurait été créé
    loadLoanConfigs();
  };

  const handleAddCredit = async () => {
    try {
      // Générer un nom unique pour le nouveau crédit
      const baseName = 'Nouveau crédit';
      let creditName = baseName;
      let counter = 1;
      
      // Vérifier si le nom existe déjà et incrémenter si nécessaire
      while (loanConfigs.some(config => config.name === creditName)) {
        creditName = `${baseName} ${counter}`;
        counter++;
      }

      // Créer un nouveau crédit avec valeurs par défaut
      const newConfig = await loanConfigsAPI.create({
        name: creditName,
        credit_amount: 0,
        interest_rate: 0,
        duration_years: 0,
        initial_deferral_months: 0,
        loan_start_date: null,
        loan_end_date: null
      });

      // Recharger la liste des crédits
      await loadLoanConfigs();

      // Bascule automatiquement vers le nouvel onglet créé
      setActiveLoanName(newConfig.name);
    } catch (error: any) {
      console.error('❌ [CreditTabContent] Erreur lors de la création du crédit:', error);
      alert(error.message || 'Erreur lors de la création du crédit');
    }
  };

  const handleDeleteCredit = async (configId: number, configName: string) => {
    // Vérifier s'il y a des mensualités associées
    let hasPayments = false;
    let paymentCount = 0;
    try {
      const paymentsResponse = await loanPaymentsAPI.getAll({ loan_name: configName, limit: 1 });
      hasPayments = paymentsResponse.items.length > 0;
      if (hasPayments) {
        const allPayments = await loanPaymentsAPI.getAll({ loan_name: configName, limit: 1000 });
        paymentCount = allPayments.items.length;
      }
    } catch (err) {
      console.error('Erreur lors de la vérification des mensualités:', err);
    }

    // Message de confirmation avec information sur les mensualités
    const confirmMessage = hasPayments
      ? `Êtes-vous sûr de vouloir supprimer le crédit "${configName}" ?\n\nToutes les mensualités associées (${paymentCount}) seront également supprimées.`
      : `Êtes-vous sûr de vouloir supprimer le crédit "${configName}" ?`;

    if (!window.confirm(confirmMessage)) {
      return;
    }

    try {
      // Supprimer toutes les mensualités associées
      if (hasPayments) {
        try {
          const allPayments = await loanPaymentsAPI.getAll({ loan_name: configName, limit: 1000 });
          const deletePromises = allPayments.items.map(payment => loanPaymentsAPI.delete(payment.id));
          await Promise.allSettled(deletePromises);
          console.log(`✅ ${allPayments.items.length} mensualité(s) supprimée(s) pour le crédit "${configName}"`);
        } catch (err) {
          console.error('Erreur lors de la suppression des mensualités:', err);
          // Continuer quand même avec la suppression de la config
        }
      }

      // Supprimer la configuration
      await loanConfigsAPI.delete(configId);
      
      // Recharger la liste des crédits
      const response = await loanConfigsAPI.getAll();
      const sortedConfigs = response.items.sort((a, b) => {
        const aDate = (a as any).created_at ? new Date((a as any).created_at).getTime() : a.id;
        const bDate = (b as any).created_at ? new Date((b as any).created_at).getTime() : b.id;
        return aDate - bDate;
      });
      setLoanConfigs(sortedConfigs);

      // Gérer la sélection du crédit actif après suppression
      if (sortedConfigs.length === 0) {
        // C'était le dernier crédit, plus de crédit actif
        setActiveLoanName(null);
      } else {
        // Sélectionner le premier crédit disponible
        setActiveLoanName(sortedConfigs[0].name);
      }
    } catch (error: any) {
      console.error('❌ [CreditTabContent] Erreur lors de la suppression:', error);
      alert(error.message || 'Erreur lors de la suppression');
    }
  };

  // Utiliser useCallback pour éviter les re-renders infinis
  const handleConfigsChange = useCallback((configs: LoanConfig[]) => {
    setLoanConfigs(prevConfigs => {
      // Vérifier si les configs ont vraiment changé (comparer les IDs)
      const prevIds = prevConfigs.map(c => c.id).sort().join(',');
      const newIds = configs.map(c => c.id).sort().join(',');
      if (prevIds === newIds) {
        return prevConfigs; // Pas de changement, retourner l'ancien state
      }
      return configs;
    });
    
    // Si le crédit actif n'existe plus, sélectionner le premier
    setActiveLoanName(prevActive => {
      if (prevActive && !configs.find(c => c.name === prevActive)) {
        if (configs.length > 0) {
          return configs[0].name;
        } else {
          return null;
        }
      } else if (!prevActive && configs.length > 0) {
        return configs[0].name;
      }
      return prevActive; // Pas de changement
    });
  }, []);

  // Afficher les sous-onglets uniquement si l'onglet Crédit est actif ET hasCredit est coché
  const showSubTabs = activeTab === 'credit' && hasCredit;

  return (
    <div>
      {/* Barre de sous-onglets crédit */}
      {showSubTabs && (
        <nav style={{ 
          backgroundColor: '#f9fafb', 
          borderBottom: '1px solid #e5e7eb', 
          marginBottom: '24px',
          padding: '0 24px'
        }}>
          <div style={{ 
            display: 'flex', 
            gap: '6px',
            alignItems: 'center',
            minHeight: '44px',
            justifyContent: 'space-between'
          }}>
            <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
              {isLoadingConfigs ? (
                <div style={{ 
                  padding: '8px 12px', 
                  fontSize: '13px', 
                  color: '#6b7280',
                  fontStyle: 'italic'
                }}>
                  Chargement des crédits...
                </div>
              ) : loanConfigs.length > 0 ? (
                <>
                  {loanConfigs.map((config) => {
                    const isActive = activeLoanName === config.name;
                    const showDelete = hoveredLoanId === config.id;
                    return (
                      <div
                        key={config.id}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          padding: '8px 12px',
                          fontSize: '13px',
                          fontWeight: '500',
                          color: isActive ? '#1e3a5f' : '#6b7280',
                          borderBottom: isActive ? '2px solid #1e3a5f' : '2px solid transparent',
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                          borderRadius: '4px 4px 0 0',
                          backgroundColor: isActive ? 'white' : 'transparent',
                          position: 'relative',
                        }}
                        onClick={() => setActiveLoanName(config.name)}
                        onMouseEnter={() => setHoveredLoanId(config.id)}
                        onMouseLeave={() => setHoveredLoanId(null)}
                      >
                        <span>{config.name}</span>
                        {showDelete && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation(); // Empêcher le changement d'onglet
                              handleDeleteCredit(config.id, config.name);
                            }}
                            style={{
                              padding: '2px 6px',
                              fontSize: '16px',
                              fontWeight: '600',
                              color: '#6b7280',
                              backgroundColor: 'transparent',
                              border: 'none',
                              cursor: 'pointer',
                              borderRadius: '4px',
                              transition: 'all 0.2s',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              width: '20px',
                              height: '20px',
                              lineHeight: '1',
                            }}
                            onMouseOver={(e) => {
                              e.currentTarget.style.color = '#dc2626';
                              e.currentTarget.style.backgroundColor = '#fee2e2';
                            }}
                            onMouseOut={(e) => {
                              e.currentTarget.style.color = '#6b7280';
                              e.currentTarget.style.backgroundColor = 'transparent';
                            }}
                            title="Supprimer ce crédit"
                          >
                            ×
                          </button>
                        )}
                      </div>
                    );
                  })}
                </>
              ) : (
                <div style={{ 
                  padding: '8px 12px', 
                  fontSize: '13px', 
                  color: '#6b7280'
                }}>
                  Aucun crédit configuré
                </div>
              )}
            </div>

            {/* Bouton "+ Ajouter un crédit" */}
            {!isLoadingConfigs && (
              <button
                onClick={handleAddCredit}
                style={{
                  padding: '8px 16px',
                  fontSize: '13px',
                  fontWeight: '500',
                  backgroundColor: '#1e3a5f',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = '#2d4a6f';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = '#1e3a5f';
                }}
              >
                <span>+</span>
                <span>Ajouter un crédit</span>
              </button>
            )}
          </div>
        </nav>
      )}

      {/* Contenu principal */}
      {isLoadingConfigs ? (
        <div style={{ padding: '24px', textAlign: 'center', color: '#6b7280' }}>
          Chargement des configurations de crédit...
        </div>
      ) : loanConfigs.length > 0 && activeLoanName ? (
        <>
          {/* Card de configuration pour le crédit actif */}
          {(() => {
            const activeConfig = loanConfigs.find(c => c.name === activeLoanName);
            return activeConfig ? (
              <LoanConfigSingleCard 
                loanConfig={activeConfig}
                onConfigUpdated={() => {
                  loadLoanConfigs();
                  handleImportComplete();
                }}
              />
            ) : null;
          })()}
          
          <div style={{ marginTop: '24px' }}>
            <LoanPaymentTable 
              loanConfigs={loanConfigs}
              refreshTrigger={refreshTrigger}
              onActiveLoanChange={setActiveLoanName}
              initialActiveLoanName={activeLoanName}
              onUpdate={() => setRefreshTrigger(prev => prev + 1)}
              hideSubTabs={true}
            />
          </div>
        </>
      ) : (
        <div style={{ 
          padding: '48px 24px', 
          textAlign: 'center', 
          color: '#6b7280',
          backgroundColor: 'white',
          borderRadius: '8px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          <div style={{
            fontSize: '16px',
            fontWeight: '500',
            color: '#374151',
            marginBottom: '8px'
          }}>
            Aucun crédit configuré
          </div>
          <div style={{
            fontSize: '14px',
            color: '#6b7280',
            marginBottom: '24px'
          }}>
            Cliquez sur "+ Ajouter un crédit" ci-dessus pour créer votre premier crédit.
          </div>
        </div>
      )}
    </div>
  );
}

export default function EtatsFinanciersPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const tabParam = searchParams?.get('tab');
  
  // État pour la checkbox "J'ai un crédit" (persisté dans localStorage)
  const [hasCredit, setHasCredit] = useState<boolean>(false);
  const [mounted, setMounted] = useState(false);

  // Déterminer l'onglet actif (par défaut: compte-resultat)
  const activeTab = tabParam || 'compte-resultat';

  // Charger l'état de la checkbox depuis localStorage au montage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('etats_financiers_has_credit');
      setHasCredit(saved === 'true');
      setMounted(true);
    }
  }, []);

  // Sauvegarder l'état de la checkbox dans localStorage
  const handleCreditCheckboxChange = (checked: boolean) => {
    if (checked) {
      // Activer la checkbox : onglet Crédit apparaît immédiatement
      setHasCredit(true);
      localStorage.setItem('etats_financiers_has_credit', 'true');
    } else {
      // Désactiver la checkbox : demander confirmation
      const confirmMessage = 'Les données de crédit (si il y en a) vont être écrasées. Continuer ?';
      if (window.confirm(confirmMessage)) {
        setHasCredit(false);
        localStorage.setItem('etats_financiers_has_credit', 'false');
        
        // Si on était sur l'onglet Crédit, rediriger vers Compte de résultat
        if (activeTab === 'credit') {
          router.push('/dashboard/etats-financiers?tab=compte-resultat');
        }
      }
    }
  };

  // Définir les onglets de base (toujours affichés)
  const baseTabs = [
    { name: 'Compte de résultat', tab: 'compte-resultat' },
    { name: 'Bilan', tab: 'bilan' },
    { name: 'Liasse fiscale', tab: 'liasse-fiscale' },
  ];

  // Onglet Crédit (conditionnel)
  const creditTab = { name: 'Crédit', tab: 'credit' };

  // Attendre le montage pour éviter les problèmes d'hydratation
  if (!mounted) {
    return (
      <div style={{ padding: '24px' }}>
        <div style={{ fontSize: '14px', color: '#6b7280' }}>Chargement...</div>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      {/* Sous-onglets horizontaux */}
      <nav style={{ backgroundColor: 'white', borderBottom: '1px solid #e5e7eb', marginBottom: '24px' }}>
        <div style={{ padding: '0 24px' }}>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', gap: '8px' }}>
              {/* Onglets de base */}
              {baseTabs.map((tab) => {
                const isActive = activeTab === tab.tab;
                return (
                  <Link
                    key={tab.tab}
                    href={`/dashboard/etats-financiers?tab=${tab.tab}`}
                    style={{
                      padding: '12px 16px',
                      fontSize: '14px',
                      fontWeight: '500',
                      color: isActive ? '#1e3a5f' : '#6b7280',
                      borderBottom: isActive ? '2px solid #1e3a5f' : '2px solid transparent',
                      textDecoration: 'none',
                      transition: 'all 0.2s',
                    }}
                  >
                    {tab.name}
                  </Link>
                );
              })}
              
              {/* Onglet Crédit (conditionnel) */}
              {hasCredit && (
                <Link
                  key={creditTab.tab}
                  href={`/dashboard/etats-financiers?tab=${creditTab.tab}`}
                  style={{
                    padding: '12px 16px',
                    fontSize: '14px',
                    fontWeight: '500',
                    color: activeTab === creditTab.tab ? '#1e3a5f' : '#6b7280',
                    borderBottom: activeTab === creditTab.tab ? '2px solid #1e3a5f' : '2px solid transparent',
                    textDecoration: 'none',
                    transition: 'all 0.2s',
                  }}
                >
                  {creditTab.name}
                </Link>
              )}
            </div>

            {/* "J'ai un crédit" dans la barre de navigation */}
            <label
              style={{
                padding: '12px 16px',
                fontSize: '14px',
                fontWeight: '500',
                color: hasCredit ? '#1e3a5f' : '#6b7280',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'all 0.2s',
                borderRadius: '4px',
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.backgroundColor = '#f3f4f6';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent';
              }}
              title={hasCredit ? "Cliquer pour désactiver" : "Cliquer pour activer"}
            >
              <input
                type="checkbox"
                checked={hasCredit}
                onChange={(e) => handleCreditCheckboxChange(e.target.checked)}
                style={{
                  width: '16px',
                  height: '16px',
                  cursor: 'pointer',
                }}
              />
              <span>J'ai un crédit</span>
            </label>
          </div>
        </div>
      </nav>

      {/* Contenu selon l'onglet actif */}
      <div style={{ 
        backgroundColor: 'white', 
        borderRadius: '8px', 
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        padding: '24px',
        minHeight: '400px'
      }}>
        {activeTab === 'compte-resultat' && (
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1a1a1a', marginBottom: '16px' }}>
              Compte de résultat
            </h2>
            <p style={{ color: '#6b7280' }}>
              Cette section sera implémentée dans les prochaines phases.
            </p>
          </div>
        )}

        {activeTab === 'bilan' && (
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1a1a1a', marginBottom: '16px' }}>
              Bilan
            </h2>
            <p style={{ color: '#6b7280' }}>
              Cette section sera implémentée dans les prochaines phases.
            </p>
          </div>
        )}

        {activeTab === 'liasse-fiscale' && (
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1a1a1a', marginBottom: '16px' }}>
              Liasse fiscale
            </h2>
            <p style={{ color: '#6b7280' }}>
              Cette section sera implémentée dans les prochaines phases.
            </p>
          </div>
        )}

        {activeTab === 'credit' && hasCredit && (
          <CreditTabContent activeTab={activeTab} hasCredit={hasCredit} />
        )}
      </div>
    </div>
  );
}
