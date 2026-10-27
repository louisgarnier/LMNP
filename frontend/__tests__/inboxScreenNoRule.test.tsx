/**
 * Régression : le backend renvoie `proposed_rule: null` quand il refuse de
 * proposer une règle jetable (garde « annuaire », inbox.py). L'écran doit
 * rester utilisable : on classe la transaction SANS créer de règle, et
 * « Modifier » ne doit pas planter.
 */
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import InboxScreen from '@/components/InboxScreen';

jest.mock('@/contexts/PropertyContext', () => ({ useProperty: () => ({ activeProperty: { id: 25 } }) }));
jest.mock('@/api/client', () => ({
  inboxAPI: {
    list: jest.fn().mockResolvedValue([{
      transaction_id: 2045, nom: 'VIR INST CANDICE', date: '2026-07-22',
      montant: -718, suggestion: { category_id: 16 },
      proposed_rule: null }]),
    validate: jest.fn().mockResolvedValue({}),
    validateAll: jest.fn().mockResolvedValue({ rules_created: 0, transactions_validated: 1 }),
  },
  categoriesAPI: { list: jest.fn().mockResolvedValue([{ id: 16, label: 'Charges de copropriété', group_label: 'Charges', nature: 'charges' }]) },
}));

test('sans règle proposée : Valider classe la transaction sans créer de règle', async () => {
  const { inboxAPI } = require('@/api/client');
  render(<InboxScreen />);
  await waitFor(() => expect(screen.getByText(/VIR INST CANDICE/)).toBeInTheDocument());

  fireEvent.click(screen.getAllByText('Valider')[0]);

  await waitFor(() => expect(inboxAPI.validate).toHaveBeenCalledWith(
    expect.objectContaining({ transaction_id: 2045, category_id: 16 })));
  const body = inboxAPI.validate.mock.calls[0][0];
  expect(body.rule ?? null).toBeNull();
});

test('sans règle proposée : Modifier ouvre l’éditeur sans planter, motif vide', async () => {
  render(<InboxScreen />);
  await waitFor(() => expect(screen.getByText(/VIR INST CANDICE/)).toBeInTheDocument());

  fireEvent.click(screen.getByText('Modifier'));

  const input = await screen.findByPlaceholderText(/motif/i);
  expect((input as HTMLInputElement).value).toBe('');
});

test('sans règle proposée : valider depuis l’éditeur avec un motif vide ne crée pas de règle', async () => {
  const { inboxAPI } = require('@/api/client');
  render(<InboxScreen />);
  await waitFor(() => expect(screen.getByText(/VIR INST CANDICE/)).toBeInTheDocument());

  fireEvent.click(screen.getByText('Modifier'));
  await screen.findByPlaceholderText(/motif/i);
  fireEvent.click(screen.getAllByText('Valider')[0]);

  await waitFor(() => expect(inboxAPI.validate).toHaveBeenCalled());
  const body = inboxAPI.validate.mock.calls[0][0];
  expect(body.rule ?? null).toBeNull();
});
