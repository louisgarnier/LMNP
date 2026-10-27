/**
 * Échéancier de péremption de la tirelire déficit.
 *
 * Le déficit reportable a une durée de vie (10 ans par défaut, réglable en
 * base) : chaque tranche naît l'année de la perte et meurt N ans plus tard,
 * qu'elle ait servi ou non. L'amortissement reporté, lui, ne périme jamais —
 * d'où un échéancier qui ne concerne qu'une seule des deux tirelires.
 *
 * Le moteur consomme en FIFO : la tranche la plus ancienne part en premier,
 * donc le premier euro de bénéfice attaque celle qui va mourir.
 *
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

import type { Millesime } from '@/utils/positionFiscale';

/** En deçà de ce délai, la tranche est signalée comme urgente. */
const SEUIL_URGENCE_ANNEES = 6;

export interface TrancheEcheancier extends Millesime {
  /** Ordre de consommation : 1 = servie en premier. */
  rang: number;
  /** Part de cette tranche dans la tirelire, en pourcentage. */
  part: number;
  /** Ce qu'il resterait dans la tirelire une fois cette tranche périmée. */
  resteApres: number;
  annees: number;
  mois: number;
  urgent: boolean;
}

export interface Delai {
  annees: number;
  mois: number;
  ecoule: boolean;
}

/** Délai restant jusqu'au 31/12 de l'année d'expiration. */
export function delaiRestant(anneeFin: number, aujourdhui: Date = new Date()): Delai {
  const fin = new Date(anneeFin, 11, 31);
  const jours = Math.floor((fin.getTime() - aujourdhui.getTime()) / 86_400_000);
  if (jours <= 0) return { annees: 0, mois: 0, ecoule: true };
  const annees = Math.floor(jours / 365.25);
  const mois = Math.floor((jours - annees * 365.25) / 30.44);
  return { annees, mois, ecoule: false };
}

/**
 * Construit l'échéancier, du plus urgent au plus lointain.
 * L'ordre d'arrivée n'a pas d'importance : on trie sur l'année d'expiration.
 */
export function echeancierDeficit(
  millesimes: Millesime[],
  aujourdhui: Date = new Date()
): TrancheEcheancier[] {
  if (!millesimes?.length) return [];

  const tries = [...millesimes].sort((a, b) => a.expire_fin - b.expire_fin);
  const total = tries.reduce((s, m) => s + m.montant, 0);

  let cumul = 0;
  return tries.map((m, i) => {
    cumul += m.montant;
    const d = delaiRestant(m.expire_fin, aujourdhui);
    return {
      ...m,
      rang: i + 1,
      part: total > 0 ? (m.montant / total) * 100 : 0,
      resteApres: total - cumul,
      annees: d.annees,
      mois: d.mois,
      urgent: !d.ecoule && d.annees < SEUIL_URGENCE_ANNEES,
    };
  });
}
