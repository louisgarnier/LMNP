/**
 * UnclassifiedTransactionsTable component - Tableau des transactions non classées
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

'use client';

// Réutiliser TransactionsTable avec le paramètre unclassifiedOnly=true
import TransactionsTable from './TransactionsTable';

interface UnclassifiedTransactionsTableProps {
  onDelete?: () => void;
  onUpdate?: () => void; // Callback appelé après mise à jour d'une transaction (pour rafraîchir Mapping)
}

/**
 * Composant qui affiche uniquement les transactions non classées.
 * Réutilise TransactionsTable avec unclassifiedOnly=true.
 */
export default function UnclassifiedTransactionsTable({ onDelete, onUpdate }: UnclassifiedTransactionsTableProps) {
  // Créer une version modifiée de TransactionsTable qui passe toujours unclassifiedOnly=true
  // Pour l'instant, on va créer un wrapper simple qui utilise TransactionsTable
  // mais on pourrait aussi modifier TransactionsTable pour accepter un prop unclassifiedOnly
  
  return (
    <div>
      <div style={{ marginBottom: '16px', padding: '12px', backgroundColor: '#fff3cd', borderRadius: '4px', border: '1px solid #ffc107' }}>
        <p style={{ margin: 0, fontSize: '14px', color: '#856404' }}>
          📋 <strong>Transactions non classées</strong> - Ces transactions n'ont pas encore de classification (level_1/2/3 = NULL).
          Vous pouvez les éditer directement depuis ce tableau.
        </p>
      </div>
      <TransactionsTable onDelete={onDelete} unclassifiedOnly={true} onUpdate={onUpdate} />
    </div>
  );
}

