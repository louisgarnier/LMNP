import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import TransactionsTable from '@/components/TransactionsTable';

// 120 transactions, 50 par page => 3 pages
const makeTx = (id: number) => ({
  id,
  date: '2025-06-28',
  quantite: 450,
  nom: `tx-${id}`,
  solde: 450,
  created_at: '',
  updated_at: '',
  category_id: 1,
  level_1: 'Produits',
  parent_transaction_id: null,
  is_split_parent: false,
  source: 'csv',
});

jest.mock('@/contexts/PropertyContext', () => ({ useProperty: () => ({ activeProperty: { id: 15 } }) }));
jest.mock('@/api/client', () => ({
  transactionsAPI: {
    getAll: jest.fn().mockImplementation((_propertyId: number, skip: number, pageSize: number) =>
      Promise.resolve({
        transactions: Array.from({ length: pageSize }, (_, i) => ({
          id: skip + i + 1,
          date: '2025-06-28',
          quantite: 450,
          nom: `tx-${skip + i + 1}`,
          solde: 450,
          created_at: '',
          updated_at: '',
          category_id: 1,
          level_1: 'Produits',
          parent_transaction_id: null,
          is_split_parent: false,
          source: 'csv',
        })),
        total: 120,
        page: skip / pageSize + 1,
        page_size: pageSize,
      })
    ),
    getUniqueValues: jest.fn().mockResolvedValue({ column: 'nom', values: [] }),
  },
  categoriesAPI: {
    list: jest.fn().mockResolvedValue([
      { id: 1, label: 'Encaissement locataire et CAF', group_label: 'Produits', nature: 'produits' },
    ]),
  },
}));

// Laisse tous les effets et leurs re-rendus se stabiliser avant d'observer l'état final.
const settle = () => act(async () => { await new Promise((r) => setTimeout(r, 50)); });

test('un clic sur « Suivante » charge la page 2 et y reste', async () => {
  const { transactionsAPI } = require('@/api/client');
  render(<TransactionsTable />);

  await waitFor(() => expect(transactionsAPI.getAll).toHaveBeenCalled());
  expect(transactionsAPI.getAll.mock.calls[0][1]).toBe(0); // page 1 => skip 0

  fireEvent.click(screen.getAllByText('Suivante ›')[0]);
  await settle();

  const skips = transactionsAPI.getAll.mock.calls.map((c: unknown[]) => c[1]);
  // La page 2 doit avoir été demandée...
  expect(skips).toContain(50);
  // ...et surtout, on doit y RESTER : le dernier chargement est celui de la page 2,
  // pas un retour silencieux à la page 1.
  expect(skips[skips.length - 1]).toBe(50);
});

test('la pagination affiche la page 2 après un clic sur « Suivante »', async () => {
  const { transactionsAPI } = require('@/api/client');
  transactionsAPI.getAll.mockClear();
  render(<TransactionsTable />);

  await waitFor(() => expect(transactionsAPI.getAll).toHaveBeenCalled());

  fireEvent.click(screen.getAllByText('Suivante ›')[0]);
  await settle();

  const label = screen.getAllByText((_, el) => /Page 2 sur 3/.test(el?.textContent ?? ''));
  expect(label.length).toBeGreaterThan(0);
});
