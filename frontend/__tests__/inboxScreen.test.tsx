import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import InboxScreen from '@/components/InboxScreen';

jest.mock('@/contexts/PropertyContext', () => ({ useProperty: () => ({ activeProperty: { id: 25 } }) }));
jest.mock('@/api/client', () => ({
  inboxAPI: {
    list: jest.fn().mockResolvedValue([{
      transaction_id: 1, nom: 'VIR AIRBNB PAYMENTS LUXEMBOU G-ZE', date: '2025-06-28',
      montant: 540, suggestion: { category_id: 1 },
      proposed_rule: { pattern: 'VIR AIRBNB PAYMENTS LUXEMBOU', match_type: 'prefix' } }]),
    validate: jest.fn().mockResolvedValue({}),
    validateAll: jest.fn().mockResolvedValue({ rules_created: 1, transactions_validated: 1 }),
  },
  categoriesAPI: { list: jest.fn().mockResolvedValue([{ id: 1, label: 'Encaissement locataire et CAF', group_label: 'Produits', nature: 'produits' }]) },
}));

test('liste un item et valide', async () => {
  const { inboxAPI } = require('@/api/client');
  render(<InboxScreen />);
  await waitFor(() => expect(screen.getByText(/VIR AIRBNB/)).toBeInTheDocument());
  expect(screen.getByText('Encaissement locataire et CAF')).toBeInTheDocument();
  fireEvent.click(screen.getAllByText('Valider')[0]);
  await waitFor(() => expect(inboxAPI.validate).toHaveBeenCalledWith(
    expect.objectContaining({ transaction_id: 1, category_id: 1,
      rule: expect.objectContaining({ pattern: 'VIR AIRBNB PAYMENTS LUXEMBOU', match_type: 'prefix' }) })));
});
