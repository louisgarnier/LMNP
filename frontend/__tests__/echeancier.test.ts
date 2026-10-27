/**
 * Échéancier de péremption de la tirelire déficit.
 *
 * Le déficit reportable meurt N ans après sa naissance, qu'il ait servi ou non.
 * Le moteur sert toujours la tranche la plus ancienne en premier (FIFO), donc
 * le premier euro de bénéfice attaque celle qui va mourir.
 * Cf. docs/project/analysis/TIRELIRES-FISCALES-EXPLICATION.md, partie 10.
 */
import { echeancierDeficit, delaiRestant } from '../src/utils/echeancier';

const MILLESIMES = [
  { annee: 2024, montant: 5479, expire_fin: 2034 },
  { annee: 2021, montant: 24097, expire_fin: 2031 },
  { annee: 2025, montant: 11001, expire_fin: 2035 },
];

const LE_JOUR = new Date('2026-07-29');

describe('echeancierDeficit', () => {
  test('trie du plus urgent au plus lointain, quel que soit l’ordre reçu', () => {
    const e = echeancierDeficit(MILLESIMES, LE_JOUR);
    expect(e.map((t) => t.expire_fin)).toEqual([2031, 2034, 2035]);
  });

  test('la tranche la plus urgente est servie en premier (FIFO)', () => {
    const e = echeancierDeficit(MILLESIMES, LE_JOUR);
    expect(e[0].rang).toBe(1);
    expect(e[0].annee).toBe(2021);
  });

  test('indique ce qu’il resterait après chaque échéance', () => {
    const e = echeancierDeficit(MILLESIMES, LE_JOUR);
    expect(e[0].resteApres).toBe(5479 + 11001);
    expect(e[1].resteApres).toBe(11001);
    expect(e[2].resteApres).toBe(0);
  });

  test('calcule la part de chaque tranche dans le total', () => {
    const e = echeancierDeficit(MILLESIMES, LE_JOUR);
    const total = 24097 + 5479 + 11001;
    expect(e[0].part).toBeCloseTo((24097 / total) * 100, 1);
  });

  test('marque comme urgente une tranche à moins de six ans', () => {
    const e = echeancierDeficit(MILLESIMES, LE_JOUR);
    expect(e[0].urgent).toBe(true);
    expect(e[2].urgent).toBe(false);
  });

  test('une tirelire vide renvoie un échéancier vide', () => {
    expect(echeancierDeficit([], LE_JOUR)).toEqual([]);
  });
});

describe('delaiRestant', () => {
  test('exprime le délai en années et mois', () => {
    expect(delaiRestant(2031, LE_JOUR)).toEqual({ annees: 5, mois: 5, ecoule: false });
  });

  test('une échéance de cette année laisse moins d’un an', () => {
    const d = delaiRestant(2026, LE_JOUR);
    expect(d.annees).toBe(0);
    expect(d.mois).toBeGreaterThan(0);
  });

  test('une échéance passée est signalée comme écoulée', () => {
    expect(delaiRestant(2020, LE_JOUR).ecoule).toBe(true);
  });
});
