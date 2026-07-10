import { computeCompteBancairePrevu } from '../src/utils/bilanProjection';

test('compte bancaire prévu = réel N-1 + CR prévisionnel - crédit annuel + variation CCA', () => {
  expect(computeCompteBancairePrevu({
    reelN1: 2540.72, totalCrPrevisionnel: 10217.50,
    creditAnnuel: 13798.44, variationCca: 2323.00,
  })).toBeCloseTo(1282.78, 2);
});
