import { render, screen, waitFor } from '@testing-library/react';
import CategorySelector from '@/components/CategorySelector';

jest.mock('@/api/client', () => ({
  categoriesAPI: {
    list: jest.fn().mockResolvedValue([
      { id: 2, label: 'Énergie', group_label: 'Charges Déductibles', nature: 'charges_deductibles' },
      { id: 1, label: 'Encaissement locataire et CAF', group_label: 'Produits', nature: 'produits' },
    ]),
  },
}));

test('affiche les catégories chargées', async () => {
  render(<CategorySelector value={null} onChange={() => {}} />);
  await waitFor(() => expect(screen.getByText('Énergie')).toBeInTheDocument());
  expect(screen.getByText('Encaissement locataire et CAF')).toBeInTheDocument();
});
