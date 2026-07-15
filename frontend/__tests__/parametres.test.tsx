import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import ParametresScreen from '@/components/ParametresScreen';

jest.mock('@/contexts/PropertyContext', () => ({ useProperty: () => ({ activeProperty: { id: 25 } }) }));
jest.mock('@/api/client', () => ({
  bankingAPI: {
    status: jest.fn().mockResolvedValue({ live: false, message: 'Mode démo actif' }),
    aspsps: jest.fn().mockResolvedValue([{ name: 'Crédit Agricole', country: 'FR' }, { name: 'BNP Paribas', country: 'FR' }]),
    connect: jest.fn().mockResolvedValue({ authorization_url: 'https://mock-eb.example/auth', state: 'state-123' }),
    createSession: jest.fn(),
    selectAccount: jest.fn(),
    connections: jest.fn().mockResolvedValue([]),
    sync: jest.fn(),
    disconnect: jest.fn(),
  },
}));

// jsdom lève une erreur "Not implemented: navigation" si on assigne
// window.location.href sans mock explicite.
beforeEach(() => {
  delete (window as any).location;
  (window as any).location = { href: '', search: '', pathname: '/dashboard/transactions' };
  window.sessionStorage.clear();
});

test('charge le statut au montage et déclenche la connexion à une banque', async () => {
  const { bankingAPI } = require('@/api/client');
  render(<ParametresScreen />);

  await waitFor(() => expect(bankingAPI.status).toHaveBeenCalled());
  await waitFor(() => expect(screen.getByText('Mode démo')).toBeInTheDocument());
  expect(screen.getByText('Mode démo actif')).toBeInTheDocument();

  await waitFor(() => expect(screen.getByText('Crédit Agricole')).toBeInTheDocument());
  fireEvent.click(screen.getByText('Crédit Agricole'));

  await waitFor(() =>
    expect(bankingAPI.connect).toHaveBeenCalledWith({ property_id: 25, aspsp_name: 'Crédit Agricole' })
  );
  await waitFor(() => expect(window.location.href).toBe('https://mock-eb.example/auth'));
});
