/**
 * Simple Dashboard page
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useEffect, useState } from 'react';
import { healthAPI, transactionsAPI } from '@/api/client';
import { useProperty } from '@/contexts/PropertyContext';

export default function DashboardPage() {
  const { activeProperty } = useProperty();
  const [apiStatus, setApiStatus] = useState<string>('checking...');
  const [transactionsCount, setTransactionsCount] = useState<number | null>(null);

  useEffect(() => {
    const checkAPI = async () => {
      try {
        const healthResponse = await healthAPI.check();
        setApiStatus(healthResponse.status);
        if (activeProperty && activeProperty.id && activeProperty.id > 0) {
          const transactionsResponse = await transactionsAPI.getAll(activeProperty.id, 0, 1);
          setTransactionsCount(transactionsResponse.total);
        } else {
          setTransactionsCount(null);
        }
      } catch (error) {
        setApiStatus('error');
      }
    };
    checkAPI();
  }, [activeProperty?.id]);

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '24px', fontWeight: '600', marginBottom: '24px', color: '#111827' }}>
        Vue d'ensemble
      </h1>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '24px' }}>
        <div style={{ backgroundColor: 'white', padding: '16px', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
          <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>API Backend</div>
          <div style={{ fontSize: '18px', fontWeight: '600', color: apiStatus === 'healthy' ? '#10b981' : '#ef4444' }}>
            {apiStatus === 'healthy' ? 'Connecté' : 'Erreur'}
          </div>
        </div>

        <div style={{ backgroundColor: 'white', padding: '16px', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
          <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Transactions</div>
          <div style={{ fontSize: '18px', fontWeight: '600', color: '#111827' }}>
            {transactionsCount !== null ? transactionsCount : '...'}
          </div>
        </div>

        <div style={{ backgroundColor: 'white', padding: '16px', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
          <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Actions</div>
          <div style={{ fontSize: '18px', fontWeight: '600', color: '#111827' }}>Disponibles</div>
        </div>
      </div>

      <div style={{ backgroundColor: 'white', padding: '24px', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
        <h2 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '12px', color: '#111827' }}>
          Bienvenue dans votre gestion comptable LMNP
        </h2>
        <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '16px' }}>
          Gérez efficacement votre comptabilité pour votre location meublée en régime réel.
        </p>
        <div style={{ fontSize: '14px', color: '#6b7280' }}>
          <div>• <strong>Transactions</strong> : Visualiser et gérer toutes vos transactions bancaires</div>
          <div>• <strong>États financiers</strong> : Consulter vos états financiers (Compte de résultat, Bilan, Liasse fiscale, Crédit)</div>
          <div>• <strong>Amortissements</strong> : Suivre vos amortissements par catégorie</div>
          <div>• <strong>Cashflow</strong> : Analyser l'évolution de votre solde bancaire</div>
        </div>
      </div>
    </div>
  );
}
