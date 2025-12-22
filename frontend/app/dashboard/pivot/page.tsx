/**
 * Pivot Table Page - Test page for PivotFieldSelector
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

import { useState } from 'react';
import PivotFieldSelector, { PivotFieldConfig } from '@/components/PivotFieldSelector';
import PivotTable from '@/components/PivotTable';

export default function PivotPage() {
  const [config, setConfig] = useState<PivotFieldConfig>({
    rows: [],
    columns: [],
    data: [],
    filters: {},
  });

  const handleConfigChange = (newConfig: PivotFieldConfig) => {
    setConfig(newConfig);
    console.log('Configuration mise à jour:', newConfig);
  };

  const handleCellClick = (rowValues: (string | number)[], columnValues: (string | number)[]) => {
    console.log('Cellule cliquée:', { rowValues, columnValues });
    // TODO: Afficher les transactions détaillées (Step 4.1.6)
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f9fafb' }}>
      <PivotFieldSelector config={config} onChange={handleConfigChange} />
      
      {/* Tableau croisé */}
      <div style={{ padding: '16px' }}>
        <PivotTable config={config} onCellClick={handleCellClick} />
      </div>
    </div>
  );
}
