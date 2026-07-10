/**
 * AmortizationConfigCard - rechargement de la configuration existante
 *
 * ⚠️ Before making changes, read: ../docs/workflow/BEST_PRACTICES.md
 *
 * Bug (Task 6, Bloc A): le dropdown "Level 2" revenait vide au montage
 * même si des types d'amortissement existaient déjà en base pour la
 * property active (l'état initial n'était hydraté que depuis
 * localStorage, jamais depuis GET /api/amortization/types?property_id=).
 */

import { render, screen, waitFor, act } from '@testing-library/react';
import AmortizationConfigCard from '../src/components/AmortizationConfigCard';
import type { AmortizationType } from '../src/api/client';

const EVRY_PROPERTY_ID = 25;

// Les 4 types "propres" existants pour Evry (post Task 5 : plus les 7 types scramblés d'origine)
const EXISTING_TYPES: AmortizationType[] = [
  {
    id: 1,
    name: 'Immobilisation structure/GO',
    level_2_value: 'Immobilisations',
    level_1_values: [],
    start_date: null,
    duration: 25,
    annual_amount: null,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: 'Immobilisation mobilier',
    level_2_value: 'Immobilisations',
    level_1_values: [],
    start_date: null,
    duration: 10,
    annual_amount: null,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 3,
    name: 'Immobilisation agencements',
    level_2_value: 'Immobilisations',
    level_1_values: [],
    start_date: null,
    duration: 15,
    annual_amount: null,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 4,
    name: 'Part terrain',
    level_2_value: 'Immobilisations',
    level_1_values: [],
    start_date: null,
    duration: 0,
    annual_amount: null,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
];

const PROPERTY_EVRY = {
  id: EVRY_PROPERTY_ID,
  name: 'Evry',
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
};

const PROPERTY_B = {
  id: 26,
  name: 'Melun',
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
};

// Propriété active mutable pour simuler un changement de propriété entre deux renders
let mockActiveProperty: typeof PROPERTY_EVRY = PROPERTY_EVRY;

jest.mock('../src/contexts/PropertyContext', () => ({
  useProperty: () => ({
    activeProperty: mockActiveProperty,
  }),
}));

jest.mock('../src/api/client', () => {
  const actual = jest.requireActual('../src/api/client');
  return {
    ...actual,
    transactionsAPI: {
      ...actual.transactionsAPI,
      getUniqueValues: jest.fn(),
    },
    amortizationTypesAPI: {
      ...actual.amortizationTypesAPI,
      getAll: jest.fn(),
      create: jest.fn(),
      getTransactionCount: jest.fn(),
      getAmount: jest.fn(),
      getCumulated: jest.fn(),
    },
    amortizationAPI: {
      ...actual.amortizationAPI,
      recalculate: jest.fn(),
    },
  };
});

import { transactionsAPI, amortizationTypesAPI } from '../src/api/client';

describe('AmortizationConfigCard - rechargement de la config existante', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    window.localStorage.clear();
    mockActiveProperty = PROPERTY_EVRY;

    (transactionsAPI.getUniqueValues as jest.Mock).mockImplementation(
      (_propertyId: number, column: string) => {
        if (column === 'level_2') {
          return Promise.resolve({ column: 'level_2', values: ['Immobilisations', 'Autre'] });
        }
        return Promise.resolve({ column, values: [] });
      }
    );

    // GET /api/amortization/types?property_id=<id>[&level_2_value=<v>]
    (amortizationTypesAPI.getAll as jest.Mock).mockImplementation(
      (_propertyId: number, level2Value?: string) => {
        const items = level2Value
          ? EXISTING_TYPES.filter((t) => t.level_2_value === level2Value)
          : EXISTING_TYPES;
        return Promise.resolve({ items, total: items.length });
      }
    );

    (amortizationTypesAPI.getTransactionCount as jest.Mock).mockResolvedValue({
      type_id: 0,
      type_name: '',
      transaction_count: 0,
    });
    (amortizationTypesAPI.getAmount as jest.Mock).mockResolvedValue({
      type_id: 0,
      type_name: '',
      amount: 0,
    });
    (amortizationTypesAPI.getCumulated as jest.Mock).mockResolvedValue({
      type_id: 0,
      type_name: '',
      cumulated_amount: 0,
    });
  });

  it('affiche "Immobilisations" dans le select et les types existants dans le tableau, sans passer par localStorage', async () => {
    render(<AmortizationConfigCard />);

    // Le select Level 2 doit refléter la config déjà persistée en base (pas de valeur
    // sauvegardée en localStorage pour ce test : c'est bien GET /api/amortization/types
    // qui doit fournir la valeur "Immobilisations").
    await waitFor(() => {
      expect(screen.getByText('Immobilisations')).toBeInTheDocument();
    });
    expect(screen.queryByText('-- Sélectionner une valeur --')).not.toBeInTheDocument();

    // Le tableau doit lister les types existants pour ce Level 2
    for (const type of EXISTING_TYPES) {
      expect(await screen.findByText(type.name)).toBeInTheDocument();
    }
  });

  it("ignore la réponse tardive de l'ancienne propriété après un changement de propriété", async () => {
    // Type existant pour la propriété B (Melun)
    const TYPE_B: AmortizationType = {
      id: 10,
      name: 'Machine outil',
      level_2_value: 'Machines',
      level_1_values: [],
      start_date: null,
      duration: 5,
      annual_amount: null,
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    };

    // Deferred contrôlé manuellement : l'appel level_2 de la propriété A (Evry)
    // reste en vol jusqu'à ce qu'on le résolve explicitement, APRÈS le switch vers B.
    let resolveEvryLevel2!: (value: { column: string; values: string[] }) => void;
    const evryLevel2Deferred = new Promise<{ column: string; values: string[] }>((resolve) => {
      resolveEvryLevel2 = resolve;
    });

    (transactionsAPI.getUniqueValues as jest.Mock).mockImplementation(
      (propertyId: number, column: string) => {
        if (column !== 'level_2') {
          return Promise.resolve({ column, values: [] });
        }
        if (propertyId === EVRY_PROPERTY_ID) {
          return evryLevel2Deferred; // lent : résolu manuellement plus tard
        }
        return Promise.resolve({ column: 'level_2', values: ['Machines'] }); // B : rapide
      }
    );

    (amortizationTypesAPI.getAll as jest.Mock).mockImplementation(
      (propertyId: number, level2Value?: string) => {
        const all = propertyId === EVRY_PROPERTY_ID ? EXISTING_TYPES : [TYPE_B];
        const items = level2Value ? all.filter((t) => t.level_2_value === level2Value) : all;
        return Promise.resolve({ items, total: items.length });
      }
    );

    // Monte avec la propriété A (Evry) : son appel level_2 reste en vol
    mockActiveProperty = PROPERTY_EVRY;
    const { rerender } = render(<AmortizationConfigCard />);

    // L'utilisateur change de propriété pendant que l'appel de A est en vol
    mockActiveProperty = PROPERTY_B;
    rerender(<AmortizationConfigCard />);

    // B se charge normalement : select "Machines" + son type dans le tableau
    expect(await screen.findByText('Machines')).toBeInTheDocument();
    expect(await screen.findByText('Machine outil')).toBeInTheDocument();

    // La réponse de A arrive EN RETARD, après que B est affiché
    await act(async () => {
      resolveEvryLevel2({ column: 'level_2', values: ['Immobilisations', 'Autre'] });
    });

    // L'état doit rester celui de B : la réponse périmée de A ne doit rien écraser
    expect(screen.getByText('Machines')).toBeInTheDocument();
    expect(screen.getByText('Machine outil')).toBeInTheDocument();
    expect(screen.queryByText('Immobilisations')).not.toBeInTheDocument();
    for (const type of EXISTING_TYPES) {
      expect(screen.queryByText(type.name)).not.toBeInTheDocument();
    }
  });
});
