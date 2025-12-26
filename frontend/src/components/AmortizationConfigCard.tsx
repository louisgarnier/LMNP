/**
 * AmortizationConfigCard component - Card de configuration des amortissements
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

interface AmortizationConfigCardProps {
  onConfigUpdated?: () => void;
}

export default function AmortizationConfigCard({ onConfigUpdated }: AmortizationConfigCardProps) {
  return (
    <div
      style={{
        backgroundColor: '#ffffff',
        borderRadius: '8px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        padding: '24px',
        marginBottom: '24px',
      }}
    >
      <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#111827', marginBottom: '16px' }}>
        Configuration des amortissements
      </h2>
      
      {/* Contenu à venir dans les prochaines étapes */}
      <div style={{ color: '#6b7280', fontSize: '14px', fontStyle: 'italic' }}>
        Configuration à implémenter...
      </div>
    </div>
  );
}

