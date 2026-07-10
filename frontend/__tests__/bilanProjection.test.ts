import { computeCompteBancairePrevu, extractCategory } from '../src/utils/bilanProjection';
import { BilanResponse } from '../src/api/client';

test('compte bancaire prévu = réel N-1 + CR prévisionnel - crédit annuel + variation CCA', () => {
  expect(computeCompteBancairePrevu({
    reelN1: 2540.72, totalCrPrevisionnel: 10217.50,
    creditAnnuel: 13798.44, variationCca: 2323.00,
  })).toBeCloseTo(1282.78, 2);
});

const buildBilanResponse = (): BilanResponse => ({
  year: 2025,
  actif_total: 1234.56,
  passif_total: 0,
  difference: 1234.56,
  difference_percent: 0,
  types: [
    {
      type: 'ACTIF',
      total: 1234.56,
      sub_categories: [
        {
          sub_category: 'Trésorerie',
          total: 1234.56,
          categories: [
            { category_name: 'Compte bancaire', amount: 1234.56, is_special: false },
          ],
        },
      ],
    },
  ],
});

test('extractCategory renvoie le montant quand la catégorie existe', () => {
  const bilan = buildBilanResponse();
  expect(extractCategory(bilan, 'actif', 'Compte bancaire')).toBe(1234.56);
});

test('extractCategory renvoie 0 quand la catégorie est absente', () => {
  const bilan = buildBilanResponse();
  expect(extractCategory(bilan, 'actif', 'Catégorie inexistante')).toBe(0);
  expect(extractCategory(bilan, 'passif', 'Compte bancaire')).toBe(0);
});
