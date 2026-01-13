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
        </div>
      </nav>

      {/* Checkbox "J'ai un crédit" */}
      <div style={{ 
        padding: '16px 24px', 
        backgroundColor: 'white', 
        borderBottom: '1px solid #e5e7eb',
        marginBottom: '24px'
      }}>
        <label style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '8px',
          cursor: 'pointer',
          fontSize: '14px',
          color: '#374151'
        }}>
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
          <div>
            <LoanConfigCard />
          </div>
        )}
      </div>
    </div>
  );
}
