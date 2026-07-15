import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import RulesScreen from '@/components/RulesScreen';

jest.mock('@/contexts/PropertyContext', () => ({ useProperty: () => ({ activeProperty: { id: 25 } }) }));
jest.mock('@/api/client', () => ({
  rulesAPI: { list: jest.fn().mockResolvedValue([
      { id: 1, pattern: 'VIR AIRBNB PAYMENTS LUXEMBOU', match_type: 'prefix', category_id: 1,
        property_id: 25, priority: 0, source: 'migrated', strict_ratio: true, tx_count: 37 }]),
    preview: jest.fn().mockResolvedValue({ would_classify: 3, conflicts: [] }),
    create: jest.fn(), update: jest.fn(), remove: jest.fn() },
  categoriesAPI: { list: jest.fn().mockResolvedValue([{ id: 1, label: 'Encaissement locataire et CAF', group_label: 'Produits', nature: 'produits' }]) },
}));
test('affiche une règle avec son libellé de catégorie et son compte', async () => {
  render(<RulesScreen />);
  await waitFor(() => expect(screen.getByText('VIR AIRBNB PAYMENTS LUXEMBOU')).toBeInTheDocument());
  expect(screen.getByText('Encaissement locataire et CAF')).toBeInTheDocument();
  expect(screen.getByText('37')).toBeInTheDocument();
});

test('la case Appliquer aux existantes est désactivée (bientôt disponible)', async () => {
  render(<RulesScreen />);
  await waitFor(() => expect(screen.getByText('VIR AIRBNB PAYMENTS LUXEMBOU')).toBeInTheDocument());

  // Déclenche la préversion (motif + catégorie) pour faire apparaître le bloc contenant la case.
  fireEvent.change(screen.getByPlaceholderText('CB CASTORAMA'), { target: { value: 'CB TEST' } });
  const selects = screen.getAllByRole('combobox');
  await waitFor(() => expect(selects[1]).not.toBeDisabled());
  fireEvent.change(selects[1], { target: { value: '1' } });

  await waitFor(() => expect(screen.getByRole('checkbox')).toBeInTheDocument());
  expect(screen.getByRole('checkbox')).toBeDisabled();
});
