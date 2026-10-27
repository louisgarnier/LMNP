/**
 * Logique de la carte « Position fiscale » de l'accueil.
 *
 * Tout ce que la carte affiche doit être DÉRIVÉ de /api/fiscal/chaine et
 * /api/reconciliation — aucun montant en dur, aucun nom d'appartement en dur.
 * Cf. ADR « L'application est la source de vérité fiscale » (2026-07-29).
 */
import { resumeFiscal, compterEcarts, anneesAvant } from '../src/utils/positionFiscale';
import type { ChaineLigne } from '../src/utils/positionFiscale';

const ligne = (over: Partial<ChaineLigne> & { year: number }): ChaineLigne => ({
  year: over.year,
  brouillon: false,
  profitable: false,
  mode: 'deficit',
  resultat_comptable: 0,
  resultat_fiscal_imposable: 0,
  amort_annee: 0,
  r_ha: 0,
  amort_deductible: 0,
  amort_mis_de_cote: 0,
  amort_impute: 0,
  deficit_depart: 0,
  deficit_mouvement: 0,
  deficit_fin_app: 0,
  deficit_fin_officiel: null,
  deficit_ecart: null,
  amort_depart: 0,
  amort_fin_app: 0,
  amort_fin_officiel: null,
  amort_ecart: null,
  amort_total_cumul: 0,
  amort_deduit_cumul: 0,
  deficit_millesimes: [],
  ...over,
});

const CHAINE = {
  years: [2021, 2025, 2026],
  chain: {
    '2021': ligne({ year: 2021, deficit_fin_app: 24097, amort_fin_app: 632 }),
    '2025': ligne({ year: 2025, deficit_fin_app: 40576, amort_fin_app: 35872 }),
    '2026': ligne({
      year: 2026,
      brouillon: true,
      deficit_fin_app: 40576,
      amort_fin_app: 49545,
      amort_total_cumul: 84060,
      amort_deduit_cumul: 34516,
      deficit_millesimes: [
        { annee: 2021, montant: 24097, expire_fin: 2031 },
        { annee: 2024, montant: 5479, expire_fin: 2034 },
        { annee: 2025, montant: 11001, expire_fin: 2035 },
      ],
    }),
  },
};

describe('resumeFiscal', () => {
  test("se place sur le dernier exercice, pas sur une année écrite en dur", () => {
    const r = resumeFiscal(CHAINE);
    expect(r.exercice).toBe(2026);
    expect(r.deficit).toBe(40576);
    expect(r.amort).toBe(49545);
  });

  test('le total en réserve est la somme des deux tirelires', () => {
    expect(resumeFiscal(CHAINE).total).toBe(40576 + 49545);
  });

  test('le millésime menacé est celui qui expire le plus tôt', () => {
    const r = resumeFiscal(CHAINE);
    expect(r.menace).not.toBeNull();
    expect(r.menace!.annee).toBe(2021);
    expect(r.menace!.montant).toBe(24097);
    expect(r.menace!.expire_fin).toBe(2031);
  });

  test('signale que le dernier exercice est un brouillon', () => {
    expect(resumeFiscal(CHAINE).brouillon).toBe(true);
  });

  test("pas de millésime → pas d'alerte, et rien ne casse", () => {
    const vide = { years: [2021], chain: { '2021': ligne({ year: 2021 }) } };
    const r = resumeFiscal(vide);
    expect(r.menace).toBeNull();
    expect(r.total).toBe(0);
  });

  test('une chaîne vide ne fait pas planter la carte', () => {
    const r = resumeFiscal({ years: [], chain: {} });
    expect(r.exercice).toBeNull();
    expect(r.total).toBe(0);
    expect(r.menace).toBeNull();
  });
});

describe('anneesAvant', () => {
  test("compte les années entières restantes jusqu'à la fin de l'exercice", () => {
    expect(anneesAvant(2031, new Date('2026-07-29'))).toBe(5);
  });

  test('renvoie 0 quand la date est dépassée', () => {
    expect(anneesAvant(2020, new Date('2026-07-29'))).toBe(0);
  });
});

describe('compterEcarts', () => {
  const recon = {
    annees: [2025, 2026],
    results: {
      '2025': {
        annee: 2025, brouillon: false, biens_inclus: [25],
        lignes: [
          { poste: 'Produits', par_bien: null, app: 1, liasse: 1, ecart: 0, ok: true, explication: null },
          { poste: 'Charges', par_bien: null, app: 1, liasse: 2, ecart: -1, ok: false, explication: null },
          { poste: 'Résultat', par_bien: null, app: 1, liasse: 3, ecart: -2, ok: false, explication: null },
        ],
      },
      '2026': {
        annee: 2026, brouillon: true, biens_inclus: [25],
        lignes: [{ poste: 'Produits', par_bien: null, app: 1, liasse: null, ecart: null, ok: null, explication: null }],
      },
    },
  };

  test('compte les lignes en écart du dernier exercice AVEC liasse', () => {
    // 2026 est un brouillon : on doit compter sur 2025
    expect(compterEcarts(recon)).toEqual({ annee: 2025, nombre: 2 });
  });

  test("aucune liasse déposée → rien à compter", () => {
    const brouillonSeul = { annees: [2026], results: { '2026': recon.results['2026'] } };
    expect(compterEcarts(brouillonSeul)).toEqual({ annee: null, nombre: 0 });
  });
});

describe('cumulImposable — plus aucun « 0 € » écrit en dur', () => {
  test('somme le résultat imposable de tous les exercices', () => {
    const { cumulImposable } = require('../src/utils/positionFiscale');
    expect(cumulImposable(CHAINE)).toBe(0);
  });

  test('remonte un vrai montant le jour où un exercice devient imposable', () => {
    const { cumulImposable } = require('../src/utils/positionFiscale');
    const imposable = {
      years: [2025, 2026],
      chain: {
        '2025': ligne({ year: 2025, resultat_fiscal_imposable: 0 }),
        '2026': ligne({ year: 2026, resultat_fiscal_imposable: 12500 }),
      },
    };
    expect(cumulImposable(imposable)).toBe(12500);
  });

  test('une chaîne vide renvoie 0 sans planter', () => {
    const { cumulImposable } = require('../src/utils/positionFiscale');
    expect(cumulImposable({ years: [], chain: {} })).toBe(0);
  });
});
