/**
 * Génère le récit d'un exercice fiscal.
 *
 * Trois gabarits FIXES — la couche pédagogique — choisis par le seul signe du
 * résultat AVANT amortissement, puis remplis avec les montants réels de
 * l'application. Aucune phrase n'est écrite par année : ajouter un exercice ne
 * demande aucun texte supplémentaire.
 *
 * La règle, en une ligne :
 *   résultat comptable + amortissement de l'année = résultat AVANT amortissement
 *     négatif              → déduit 0 ; la perte va en tirelire déficit, tout l'amort en tirelire amort
 *     positif, < amort     → l'amort efface jusqu'à zéro ; le surplus en tirelire amort
 *     positif, ≥ amort     → tout passe, puis on PUISE dans la tirelire choisie
 *
 * Cf. docs/project/analysis/TIRELIRES-FISCALES-EXPLICATION.md
 *
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

import type { ChaineLigne } from '@/utils/positionFiscale';

const EPS = 0.5;

const eur = (n: number) =>
  Math.abs(n).toLocaleString('fr-FR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + ' €';

/** Où va (ou d'où vient) un mouvement de l'exercice. */
export type Cible = 't1' | 't2' | 'deduit' | 'aucun';

export interface Mouvement {
  cible: Cible;
  texte: string;
  /** Positif = entrée en tirelire ou déduction ; négatif = puisage. */
  montant: number;
}

export interface Recit {
  annee: number;
  cas: 'negatif' | 'positif' | 'positifFort';
  /** Étiquette courte, pour le bandeau de l'exercice. */
  etiquette: string;
  titre: string;
  phrase: string;
  calcul: { resultatComptable: number; amort: number; avantAmort: number };
  mouvements: Mouvement[];
  soldeDeficit: number;
  soldeAmort: number;
}

export function recitAnnee(c: ChaineLigne): Recit {
  const { amort_annee: amort, r_ha: avantAmort } = c;
  const calcul = { resultatComptable: c.resultat_comptable, amort, avantAmort };
  const base = { annee: c.year, calcul, soldeDeficit: c.deficit_fin_app, soldeAmort: c.amort_fin_app };

  // ── Cas 1 : on perd de l'argent avant même de compter l'amortissement ──
  if (avantAmort < -EPS) {
    const perte = -avantAmort;
    return {
      ...base,
      cas: 'negatif',
      etiquette: 'avant amort négatif',
      titre: 'les DEUX tirelires se remplissent',
      phrase:
        `Tu perds ${eur(perte)} avant même de compter l'amortissement. ` +
        `Les ${eur(amort)} ne peuvent rien déduire : il n'y a aucun bénéfice à effacer.`,
      mouvements: [
        { cible: 'aucun', texte: "L'amortissement ne peut rien déduire", montant: 0 },
        { cible: 't2', texte: `Les ${eur(amort)} d'amortissement sont reportés → tirelire amortissements`, montant: c.amort_mis_de_cote },
        { cible: 't1', texte: `La perte de ${eur(perte)} est reportée → tirelire déficit`, montant: Math.max(0, c.deficit_mouvement) },
      ],
    };
  }

  // ── Cas 2 : bénéfice, mais l'amortissement est plus gros ──
  if (avantAmort < amort) {
    return {
      ...base,
      cas: 'positif',
      etiquette: 'avant amort positif',
      titre: 'seule la tirelire amortissements se remplit',
      phrase:
        `Tu gagnes ${eur(avantAmort)} avant amortissement. L'amortissement peut effacer ce bénéfice, ` +
        `mais il s'arrête à zéro — il n'a pas le droit de creuser une perte.`,
      mouvements: [
        { cible: 'deduit', texte: "L'amortissement efface le bénéfice — déduit pour de vrai", montant: c.amort_deductible },
        { cible: 't2', texte: `Le surplus (${eur(amort)} − ${eur(c.amort_deductible)}) est reporté → tirelire amortissements`, montant: c.amort_mis_de_cote },
        { cible: 'aucun', texte: 'Pas de perte cette année → la tirelire déficit ne bouge pas', montant: 0 },
      ],
    };
  }

  // ── Cas 3 : bénéfice plus gros que l'amortissement → on puise ──
  const reste = avantAmort - amort;
  const versAmort = c.mode === 'amort';
  const cible: Cible = versAmort ? 't2' : 't1';
  const nomCible = versAmort ? 'amortissements' : 'déficit';
  const nomAutre = versAmort ? 'déficit' : 'amortissements';
  const puise = versAmort ? c.amort_impute : Math.abs(c.deficit_mouvement);

  const mouvements: Mouvement[] = [
    { cible: 'deduit', texte: "Tout l'amortissement de l'année passe — déduit pour de vrai", montant: c.amort_deductible },
  ];
  if (c.amort_mis_de_cote > EPS) {
    mouvements.push({ cible: 't2', texte: 'Le surplus est reporté → tirelire amortissements', montant: c.amort_mis_de_cote });
  }
  mouvements.push({ cible, texte: `Les ${eur(reste)} restants sont pris dans la tirelire ${nomCible}`, montant: -Math.abs(puise) });
  mouvements.push({ cible: 'aucun', texte: `La tirelire ${nomAutre} n'a pas été utilisée`, montant: 0 });

  return {
    ...base,
    cas: 'positifFort',
    etiquette: 'avant amort très positif',
    titre: 'une tirelire SE VIDE',
    phrase:
      `Gros bénéfice. Tout l'amortissement de l'année passe — mais ça ne suffit pas : ` +
      `il reste ${eur(reste)} de bénéfice imposable. Il faut puiser dans une tirelire.`,
    mouvements,
  };
}
