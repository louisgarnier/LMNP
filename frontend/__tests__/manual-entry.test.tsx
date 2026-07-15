import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import TransactionsTable from '@/components/TransactionsTable';

jest.mock('@/contexts/PropertyContext', () => ({ useProperty: () => ({ activeProperty: { id: 25 } }) }));
jest.mock('@/api/client', () => ({
  transactionsAPI: {
    getAll: jest.fn().mockResolvedValue({
      transactions: [
        { id: 1, date: '2025-06-28', quantite: 100, nom: 'Loyer', solde: 1000, created_at: '', updated_at: '', category_id: 1, level_1: 'Produits' },
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

test('ouvre le formulaire Ajouter, le remplit et appelle createManual avec le bon payload', async () => {
  const { transactionsAPI } = require('@/api/client');
  render(<TransactionsTable />);

  await waitFor(() => expect(screen.getByText('Loyer')).toBeInTheDocument());

  fireEvent.click(screen.getByText('➕ Ajouter'));

  fireEvent.change(screen.getByLabelText('Date'), { target: { value: '2025-07-01' } });
  fireEvent.change(screen.getByLabelText('Montant'), { target: { value: '150.50' } });
  fireEvent.change(screen.getByLabelText('Nom'), { target: { value: 'Achat fournitures' } });

  const categorySelects = await screen.findAllByRole('combobox');
  fireEvent.change(categorySelects[0], { target: { value: '2' } });

  fireEvent.click(screen.getByText('Ajouter'));

  await waitFor(() =>
    expect(transactionsAPI.createManual).toHaveBeenCalledWith({
      property_id: 25,
      date: '2025-07-01',
      quantite: 150.5,
      nom: 'Achat fournitures',
      category_id: 2,
    })
  );
});

test('le bouton Valider de l\'éclatement est désactivé tant que la somme des parts ne correspond pas au montant', async () => {
  render(<TransactionsTable />);

  await waitFor(() => expect(screen.getByText('Loyer')).toBeInTheDocument());

  fireEvent.click(screen.getByText('✂️'));

  const montantInputs = screen.getAllByPlaceholderText('Montant €');
  // Les deux premiers champs "Montant €" appartiennent au formulaire d'éclatement (part 1 et part 2)
  const [part1, part2] = montantInputs.slice(-2);

  fireEvent.change(part1, { target: { value: '40' } });
  fireEvent.change(part2, { target: { value: '30' } });

  const validerButtons = screen.getAllByText('Valider');
  const splitValiderButton = validerButtons[validerButtons.length - 1];
  expect(splitValiderButton).toBeDisabled();

  fireEvent.change(part2, { target: { value: '60' } });
  expect(splitValiderButton).not.toBeDisabled();
});
