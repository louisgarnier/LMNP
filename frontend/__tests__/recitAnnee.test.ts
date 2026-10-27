/**
 * Le récit d'un exercice est GÉNÉRÉ, jamais rédigé année par année.
 *
 * Règle validée avec Louis le 2026-07-29 : les explications sont trois gabarits
 * fixes (couche pédagogique), choisis par le signe du résultat AVANT
 * amortissement, et remplis avec les montants réels de l'application.
 * Cf. docs/project/analysis/TIRELIRES-FISCALES-EXPLICATION.md.
 */
import { recitAnnee } from '../src/utils/recitAnnee';
import type { ChaineLigne } from '../src/utils/positionFiscale';

const ligne = (o: Partial<ChaineLigne> & { year: number }): ChaineLigne => ({
  year: o.year, brouillon: false, profitable: false, mode: 'deficit',
  resultat_comptable: 0, resultat_fiscal_imposable: 0, amort_annee: 0, r_ha: 0, amort_deductible: 0,
  amort_mis_de_cote: 0, amort_impute: 0, deficit_depart: 0,
  deficit_mouvement: 0,
  deficit_fin_app: 0, deficit_fin_officiel: null, deficit_ecart: null,
  amort_depart: 0, amort_fin_app: 0, amort_fin_officiel: null, amort_ecart: null,
  amort_total_cumul: 0, amort_deduit_cumul: 0, deficit_millesimes: [], ...o,
});

// Exercices réels de Louis, tels que l'API les renvoie.
const A2021 = ligne({
  year: 2021, resultat_comptable: -24729.17, amort_annee: 632.49, r_ha: -24096.68,
  amort_deductible: 0, amort_mis_de_cote: 632.49, deficit_mouvement: 24096.68,
  deficit_fin_app: 24096.68, amort_fin_app: 632.49,
});
const A2022 = ligne({
  year: 2022, resultat_comptable: -4410.58, amort_annee: 10350.94, r_ha: 5940.36,
  amort_deductible: 5940.36, amort_mis_de_cote: 4410.58, deficit_mouvement: 0,
  deficit_fin_app: 24096.68, amort_fin_app: 5043.07,
});
const A2023 = ligne({
  year: 2023, profitable: true, mode: 'amort',
  resultat_comptable: 4061.59, amort_annee: 11119.15, r_ha: 15180.74,
  amort_deductible: 11119.15, amort_mis_de_cote: 0, amort_impute: 4061.59,
  deficit_mouvement: 0, deficit_fin_app: 24096.68, amort_fin_app: 981.48,
});

describe('choix du gabarit selon le signe du résultat avant amortissement', () => {
  test('négatif → les deux tirelires se remplissent', () => {
    const r = recitAnnee(A2021);
    expect(r.cas).toBe('negatif');
    expect(r.titre).toContain('DEUX tirelires');
  });

  test('positif mais plus petit que l’amortissement → seule la tirelire amort se remplit', () => {
    const r = recitAnnee(A2022);
    expect(r.cas).toBe('positif');
    expect(r.titre).toContain('amortissements');
  });

  test('positif et plus gros que l’amortissement → une tirelire se vide', () => {
    const r = recitAnnee(A2023);
    expect(r.cas).toBe('positifFort');
    expect(r.titre).toContain('VIDE');
  });
});

describe('les montants du récit sortent de la ligne, jamais du texte', () => {
  test('2021 : la perte reportée vaut le résultat avant amortissement', () => {
    const r = recitAnnee(A2021);
    const versDeficit = r.mouvements.find((m) => m.cible === 't1');
    expect(versDeficit!.montant).toBeCloseTo(24096.68, 2);
    const versAmort = r.mouvements.find((m) => m.cible === 't2');
    expect(versAmort!.montant).toBeCloseTo(632.49, 2);
  });

  test('2022 : déduit = le bénéfice avant amort, le surplus part en tirelire', () => {
    const r = recitAnnee(A2022);
    expect(r.mouvements.find((m) => m.cible === 'deduit')!.montant).toBeCloseTo(5940.36, 2);
    expect(r.mouvements.find((m) => m.cible === 't2')!.montant).toBeCloseTo(4410.58, 2);
  });

  test('2023 : le puisage est négatif et cible la tirelire choisie', () => {
    const r = recitAnnee(A2023);
    const puise = r.mouvements.find((m) => m.montant < 0);
    expect(puise!.cible).toBe('t2');            // mode "amort"
    expect(puise!.montant).toBeCloseTo(-4061.59, 2);
  });

  test("le puisage suit le mode d'imputation choisi", () => {
    const enDeficit = recitAnnee({ ...A2023, mode: 'deficit', amort_impute: 0, deficit_mouvement: -4061.59 });
    const puise = enDeficit.mouvements.find((m) => m.montant < 0);
    expect(puise!.cible).toBe('t1');
  });
});

describe('robustesse', () => {
  test('un exercice sans amortissement ni perte ne casse pas', () => {
    const r = recitAnnee(ligne({ year: 2030 }));
    expect(r.cas).toBeDefined();
    expect(Array.isArray(r.mouvements)).toBe(true);
  });

  test('la phrase mentionne le montant en euros, pas un nombre brut', () => {
    expect(recitAnnee(A2021).phrase).toMatch(/24\s?097\s?€/);
  });

  test('le calcul affiché reprend les trois lignes de la règle', () => {
    const r = recitAnnee(A2021);
    expect(r.calcul.resultatComptable).toBeCloseTo(-24729.17, 2);
    expect(r.calcul.amort).toBeCloseTo(632.49, 2);
    expect(r.calcul.avantAmort).toBeCloseTo(-24096.68, 2);
  });
});
