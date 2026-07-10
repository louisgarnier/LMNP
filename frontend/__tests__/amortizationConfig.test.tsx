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

import { render, screen, waitFor } from '@testing-library/react';
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

jest.mock('../src/contexts/PropertyContext', () => ({
  useProperty: () => ({
    activeProperty: {
      id: EVRY_PROPERTY_ID,
      name: 'Evry',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    },
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
});
