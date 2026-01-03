/**
 * États financiers page - Compte de résultat, Bilan, Liasse fiscale, Crédit
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import LoanConfigCard from '@/components/LoanConfigCard';
import LoanPaymentFileUpload from '@/components/LoanPaymentFileUpload';
import LoanPaymentTable from '@/components/LoanPaymentTable';
import CompteResultatConfigCard from '@/components/CompteResultatConfigCard';
import CompteResultatTable from '@/components/CompteResultatTable';
import BilanConfigCard from '@/components/BilanConfigCard';
import BilanTable from '@/components/BilanTable';

export default function EtatsFinanciersPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const tabParam = searchParams?.get('tab');
  
  // État pour la checkbox "J'ai un crédit" (persisté dans localStorage)
  const [hasCredit, setHasCredit] = useState<boolean>(false);
  const [mounted, setMounted] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [activeLoanName, setActiveLoanName] = useState<string>('Prêt principal');
  const [compteResultatRefreshKey, setCompteResultatRefreshKey] = useState(0);
  const [bilanRefreshKey, setBilanRefreshKey] = useState(0);

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

  // Définir les onglets de base
  const baseTabs = [
    { name: 'Compte de résultat', value: 'compte-resultat' },
    { name: 'Bilan', value: 'bilan' },
    { name: 'Liasse fiscale', value: 'liasse-fiscale' },
  ];

  // Ajouter l'onglet Crédit si la checkbox est activée
  const tabs = mounted && hasCredit 
    ? [...baseTabs, { name: 'Crédit', value: 'credit' }]
    : baseTabs;

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f9fafb' }}>
      {/* Sous-onglets */}
      <nav style={{ backgroundColor: 'white', borderBottom: '1px solid #e5e7eb' }}>
        <div style={{ padding: '0 24px' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            {tabs.map((tab) => {
              const isActive = activeTab === tab.value;
              return (
                <Link
                  key={tab.value}
                  href={`/dashboard/etats-financiers?tab=${tab.value}`}
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
          </div>
        </div>
      </nav>

      {/* Checkbox "J'ai un crédit" */}
      <div style={{ padding: '16px 24px', backgroundColor: 'white', borderBottom: '1px solid #e5e7eb' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={hasCredit}
            onChange={(e) => handleCreditCheckboxChange(e.target.checked)}
            disabled={!mounted}
            style={{
              width: '16px',
              height: '16px',
              cursor: 'pointer',
            }}
          />
          <span style={{ fontSize: '14px', color: '#374151' }}>J'ai un crédit</span>
        </label>
      </div>

      {/* Contenu selon l'onglet actif */}
      <div style={{ padding: '24px' }}>
        <div style={{ 
          backgroundColor: 'white', 
          borderRadius: '8px', 
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          padding: '24px',
          minHeight: '400px'
        }}>
          {activeTab === 'compte-resultat' && (
            <div>
              <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#111827', marginBottom: '16px' }}>
                Compte de résultat
              </h2>
              <CompteResultatConfigCard 
                onConfigUpdated={() => {
                  // Recharger le tableau quand la config change
                  setCompteResultatRefreshKey(prev => prev + 1);
                }}
              />
              <div style={{ marginTop: '24px' }}>
                <CompteResultatTable 
                  refreshKey={compteResultatRefreshKey}
                />
              </div>
            </div>
          )}

          {activeTab === 'bilan' && (
            <div>
              <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#111827', marginBottom: '16px' }}>
                Bilan
              </h2>
              <BilanConfigCard 
                onConfigUpdated={() => {
                  // Recharger le tableau quand la config change
                  setBilanRefreshKey(prev => prev + 1);
                }}
              />
              <div style={{ marginTop: '24px' }}>
                <BilanTable 
                  refreshKey={bilanRefreshKey}
                />
              </div>
            </div>
          )}

          {activeTab === 'liasse-fiscale' && (
            <div>
              <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#111827', marginBottom: '16px' }}>
                Liasse fiscale
              </h2>
              <p style={{ color: '#6b7280' }}>
                Cette section sera implémentée dans Step 7.3
              </p>
            </div>
          )}

          {activeTab === 'credit' && mounted && hasCredit && (
            <div>
              <LoanConfigCard 
                onConfigsChange={() => {
                  // Recharger LoanPaymentTable quand les configurations changent
                  setRefreshKey(prev => prev + 1);
                }}
              />
              <div style={{ marginTop: '24px' }}>
                <LoanPaymentFileUpload
                  loanName={activeLoanName}
                  onImportComplete={() => {
                    // Le tableau se rafraîchira automatiquement via refreshKey
                    setRefreshKey(prev => prev + 1);
                  }}
                />
              </div>
              <div style={{ marginTop: '24px' }}>
                <LoanPaymentTable 
                  refreshKey={refreshKey}
                  onActiveLoanNameChange={(loanName) => {
                    setActiveLoanName(loanName);
                  }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
