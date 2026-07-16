import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import ParametresScreen, { localBounceTarget } from '@/components/ParametresScreen';

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

function makeConnection(overrides: Partial<{
  id: number;
  bank_name: string;
  account_name: string;
  iban_masked: string;
  currency: string;
  bank_balance: number | null;
  last_sync_at: string | null;
  session_valid_until: string | null;
  eb_account_uid: string;
}> = {}) {
  return {
    id: 1,
    bank_name: 'Crédit Agricole',
    account_name: 'Compte courant',
    iban_masked: 'FR76 **** **** **** 1234',
    currency: 'EUR',
    bank_balance: 1234.56,
    last_sync_at: '2026-07-01T10:00:00Z',
    session_valid_until: '2026-12-31T00:00:00Z',
    eb_account_uid: 'uid-1',
    ...overrides,
  };
}

test('le bouton Synchroniser est désactivé en mode démo (status.live === false)', async () => {
  const { bankingAPI } = require('@/api/client');
  bankingAPI.connections.mockResolvedValueOnce([makeConnection()]);

  render(<ParametresScreen />);

  await waitFor(() => expect(screen.getByText('Mode démo')).toBeInTheDocument());
  await waitFor(() => expect(screen.getByRole('button', { name: 'Synchroniser' })).toBeDisabled());
  expect(screen.getByText('connecte tes credentials pour synchroniser')).toBeInTheDocument();
});

test("le bouton Synchroniser est désactivé tant que le statut n'est pas encore chargé (status === null)", async () => {
  const { bankingAPI } = require('@/api/client');
  // status ne se résout jamais avant l'assertion : status reste null au premier rendu.
  let resolveStatus: (v: any) => void = () => {};
  bankingAPI.status.mockReturnValueOnce(new Promise((resolve) => { resolveStatus = resolve; }));
  bankingAPI.connections.mockResolvedValueOnce([makeConnection()]);

  render(<ParametresScreen />);

  await waitFor(() => expect(screen.getByRole('button', { name: 'Synchroniser' })).toBeDisabled());

  // Résout la promesse en attente et laisse React flusher la mise à jour d'état
  // avant la fin du test, pour éviter un warning "not wrapped in act" résiduel.
  resolveStatus({ live: false, message: 'Mode démo actif' });
  await waitFor(() => expect(screen.getByText('Mode démo actif')).toBeInTheDocument());
});

test('le bouton Synchroniser est actif quand le connecteur est en mode réel', async () => {
  const { bankingAPI } = require('@/api/client');
  bankingAPI.status.mockResolvedValueOnce({ live: true, message: 'Connecté' });
  bankingAPI.connections.mockResolvedValueOnce([makeConnection()]);

  render(<ParametresScreen />);

  await waitFor(() => expect(screen.getByRole('button', { name: 'Synchroniser' })).not.toBeDisabled());
});

test("l'alerte J-30 apparaît quand l'échéance du consentement est proche", async () => {
  const { bankingAPI } = require('@/api/client');
  const soon = new Date(Date.now() + 10 * 24 * 60 * 60 * 1000).toISOString(); // dans 10 jours
  bankingAPI.connections.mockResolvedValueOnce([makeConnection({ session_valid_until: soon })]);

  render(<ParametresScreen />);

  await waitFor(() => expect(screen.getByText('⚠️ consentement à renouveler')).toBeInTheDocument());
});

test("l'alerte J-30 n'apparaît pas quand l'échéance du consentement est lointaine", async () => {
  const { bankingAPI } = require('@/api/client');
  const far = new Date(Date.now() + 200 * 24 * 60 * 60 * 1000).toISOString(); // dans 200 jours
  bankingAPI.connections.mockResolvedValueOnce([makeConnection({ session_valid_until: far })]);

  render(<ParametresScreen />);

  await waitFor(() => expect(screen.getByText('Compte(s) connecté(s)')).toBeInTheDocument());
  expect(screen.queryByText('⚠️ consentement à renouveler')).not.toBeInTheDocument();
});

test('le bouton Déconnecter appelle bankingAPI.disconnect avec le bon account_id', async () => {
  const { bankingAPI } = require('@/api/client');
  bankingAPI.connections.mockResolvedValueOnce([makeConnection({ id: 42 })]);
  bankingAPI.connections.mockResolvedValueOnce([]); // rechargement après déconnexion
  bankingAPI.disconnect.mockResolvedValueOnce({ deleted: true });
  window.confirm = jest.fn().mockReturnValue(true);

  render(<ParametresScreen />);

  await waitFor(() => expect(screen.getByText('Déconnecter')).toBeInTheDocument());
  fireEvent.click(screen.getByText('Déconnecter'));

  await waitFor(() => expect(bankingAPI.disconnect).toHaveBeenCalledWith(42));
});

describe('localBounceTarget (retour tunnel → localhost)', () => {
  const path = '/dashboard/transactions';
  const search = '?tab=parametres&eb_callback=1&code=ABC&state=XYZ';

  test('host public (tunnel) → rebond vers localhost en gardant code+state', () => {
    expect(localBounceTarget('lmnp-louis.ngrok-free.app', path, search)).toBe(
      `http://localhost:3000${path}${search}`,
    );
  });

  test('déjà en localhost → pas de rebond (null)', () => {
    expect(localBounceTarget('localhost', path, search)).toBeNull();
  });

  test('déjà en 127.0.0.1 → pas de rebond (null)', () => {
    expect(localBounceTarget('127.0.0.1', path, search)).toBeNull();
  });
});

describe('ebCallbackTarget (chemin propre /eb-callback → onglet Paramètres)', () => {
  test('reforme l\'URL Paramètres locale en gardant code+state de la banque', () => {
    const { ebCallbackTarget } = require('@/components/ParametresScreen');
    expect(ebCallbackTarget('?code=ABC&state=XYZ')).toBe(
      'http://localhost:3000/dashboard/transactions?tab=parametres&eb_callback=1&code=ABC&state=XYZ',
    );
  });

  test('sans query (retour vide) → onglet Paramètres seul', () => {
    const { ebCallbackTarget } = require('@/components/ParametresScreen');
    expect(ebCallbackTarget('')).toBe(
      'http://localhost:3000/dashboard/transactions?tab=parametres&eb_callback=1',
    );
  });

  test('propage aussi un éventuel error= renvoyé par la banque', () => {
    const { ebCallbackTarget } = require('@/components/ParametresScreen');
    expect(ebCallbackTarget('?error=access_denied')).toBe(
      'http://localhost:3000/dashboard/transactions?tab=parametres&eb_callback=1&error=access_denied',
    );
  });
});

test('le champ de recherche filtre la liste des banques', async () => {
  const { bankingAPI } = require('@/api/client');
  render(<ParametresScreen />);

  // Les deux banques du mock sont visibles au départ.
  await waitFor(() => expect(screen.getByText('Crédit Agricole')).toBeInTheDocument());
  expect(screen.getByText('BNP Paribas')).toBeInTheDocument();

  // On tape "BNP" → seule BNP reste.
  const search = screen.getByPlaceholderText(/Rechercher ta banque/i);
  fireEvent.change(search, { target: { value: 'BNP' } });

  expect(screen.getByText('BNP Paribas')).toBeInTheDocument();
  expect(screen.queryByText('Crédit Agricole')).not.toBeInTheDocument();
});

test('retour Enable Banking : échange le code UNE fois (StrictMode) et affiche la sélection de compte', async () => {
  const { bankingAPI } = require('@/api/client');
  (window as any).location = {
    href: '',
    pathname: '/dashboard/transactions',
    search: '?tab=parametres&eb_callback=1&code=ABC&state=XYZ',
    hostname: 'localhost',
    replace: jest.fn(),
  };
  bankingAPI.createSession.mockResolvedValue({
    session_id: 'sess-1',
    session_valid_until: '2026-12-31T00:00:00Z',
    property_id: 25,
    accounts: [
      { account_uid: 'uid-1', name: 'Compte courant', iban_masked: 'FR76****1234', currency: 'EUR' },
    ],
  });

  const { StrictMode } = require('react');
  render(
    <StrictMode>
      <ParametresScreen />
    </StrictMode>,
  );

  // Le compte remonté par la banque s'affiche → le spinner « Récupération… » est bien débloqué.
  await waitFor(() => expect(screen.getByText('Rattacher ce compte')).toBeInTheDocument());
  // Code d'autorisation à usage unique : échangé exactement une fois malgré le double-rendu.
  expect(bankingAPI.createSession).toHaveBeenCalledTimes(1);
  expect(bankingAPI.createSession).toHaveBeenCalledWith({ code: 'ABC', state: 'XYZ' });
});
