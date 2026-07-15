import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import TransactionsTable from '@/components/TransactionsTable';

jest.mock('@/contexts/PropertyContext', () => ({ useProperty: () => ({ activeProperty: { id: 25 } }) }));
jest.mock('@/api/client', () => ({
  transactionsAPI: {
    getAll: jest.fn().mockResolvedValue({
      transactions: [
        {
          id: 3,
          date: '2025-06-28',
          quantite: 450,
          nom: 'loyer',
          solde: 450,
          created_at: '',
          updated_at: '',
          category_id: 1,
          level_1: 'Produits',
          parent_transaction_id: 1,
          is_split_parent: false,
          source: 'manual',
        },
      ],
      total: 1,
      page: 1,
      page_size: 50,
    }),
    getUniqueValues: jest.fn().mockResolvedValue({ column: 'nom', values: [] }),
    createManual: jest.fn().mockResolvedValue({ id: 2, category_id: null }),
    splitTransaction: jest.fn().mockResolvedValue({ parent_id: 1, child_ids: [3, 4] }),
    undoSplit: jest.fn().mockResolvedValue({ restored_id: 1 }),
    crossEntry: jest.fn().mockResolvedValue({ debit_id: 5, credit_id: 6 }),
  },
  categoriesAPI: {
    list: jest.fn().mockResolvedValue([
      { id: 1, label: 'Encaissement locataire et CAF', group_label: 'Produits', nature: 'produits' },
      { id: 2, label: 'Énergie', group_label: 'Charges Déductibles', nature: 'charges_deductibles' },
    ]),
  },
}));

test("affiche l'action « Défaire l'éclatement » sur une ligne enfant et appelle undoSplit avec l'id de la parente", async () => {
  const { transactionsAPI } = require('@/api/client');
  render(<TransactionsTable />);

  await waitFor(() => expect(screen.getByText('loyer')).toBeInTheDocument());

  const undoButton = screen.getByTitle("Défaire l'éclatement");
  expect(undoButton).toBeInTheDocument();

  fireEvent.click(undoButton);

  await waitFor(() => expect(transactionsAPI.undoSplit).toHaveBeenCalledWith(1));
  // Le refetch de la liste doit être déclenché après l'annulation.
  await waitFor(() => expect(transactionsAPI.getAll).toHaveBeenCalledTimes(2));
});
