/**
 * Dérivations de la carte « Position fiscale » (accueil) et du module fiscal.
 *
 * Règle du projet : aucun montant, aucune année, aucun nom d'appartement écrit
 * en dur. Tout provient de /api/fiscal/chaine et /api/reconciliation.
 * Cf. ADR « L'application est la source de vérité fiscale ; la liasse est un
 * contrôle » (2026-07-29).
 *
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

export interface Millesime {
  annee: number;
  montant: number;
  expire_fin: number;
}

export interface ChaineLigne {
  year: number;
  brouillon: boolean;
  profitable: boolean;
  mode: 'deficit' | 'amort';
  resultat_comptable: number;
  resultat_fiscal_imposable: number;
  amort_annee: number;
  r_ha: number;
  amort_deductible: number;
  amort_mis_de_cote: number;
  amort_impute: number;
  deficit_depart: number;
  deficit_mouvement: number;
  deficit_fin_app: number;
  deficit_fin_officiel: number | null;
  deficit_ecart: number | null;
  amort_depart: number;
  amort_fin_app: number;
  amort_fin_officiel: number | null;
  amort_ecart: number | null;
  amort_total_cumul: number;
  amort_deduit_cumul: number;
  deficit_millesimes: Millesime[];
}

export interface ChaineResponse {
  years: number[];
  chain: Record<string, ChaineLigne>;
}

export interface ExplicationEcart {
  statut: 'erreur_cabinet' | 'difference_presentation' | 'difference_date' | 'a_investiguer';
  libelle: string;
  ton: 'rouge' | 'neutre' | 'info';
  action: string;
  cause: string;
}

export interface LigneRecon {
  poste: string;
  par_bien: Record<string, number> | null;
  app: number;
  liasse: number | null;
  ecart: number | null;
  ok: boolean | null;
  /** Résultat d'enquête sur l'écart, porté par le fichier de liasse. */
  explication: ExplicationEcart | null;
}

export interface ReconResponse {
  annees: number[];
  results: Record<string, { annee: number; brouillon: boolean; biens_inclus: number[]; lignes: LigneRecon[] }>;
}

export interface ResumeFiscal {
  exercice: number | null;
  brouillon: boolean;
  deficit: number;
  amort: number;
  total: number;
  /** Millésime de déficit qui expire le plus tôt — celui qu'il faut consommer d'abord. */
  menace: Millesime | null;
}

/** Photo de la position au dernier exercice connu. */
export function resumeFiscal(data: ChaineResponse): ResumeFiscal {
  const years = [...(data.years ?? [])].sort((a, b) => a - b);
  const dernier = years.length ? years[years.length - 1] : null;
  const c = dernier !== null ? data.chain[String(dernier)] : undefined;

  if (!c) {
    return { exercice: null, brouillon: false, deficit: 0, amort: 0, total: 0, menace: null };
  }

  const millesimes = [...(c.deficit_millesimes ?? [])].sort((a, b) => a.expire_fin - b.expire_fin);

  return {
    exercice: c.year,
    brouillon: c.brouillon,
    deficit: c.deficit_fin_app,
    amort: c.amort_fin_app,
    total: c.deficit_fin_app + c.amort_fin_app,
    menace: millesimes.length ? millesimes[0] : null,
  };
}

/**
 * Base imposable cumulée sur tous les exercices connus.
 * Vaut 0 tant que les tirelires absorbent les bénéfices — mais c'est CALCULÉ,
 * pas écrit en dur : le jour où un exercice devient imposable, la carte le dit.
 */
export function cumulImposable(data: ChaineResponse): number {
  return (data.years ?? []).reduce((somme, y) => {
    const c = data.chain[String(y)];
    return somme + (c?.resultat_fiscal_imposable ?? 0);
  }, 0);
}

/** Années entières restantes avant la fin de l'exercice `anneeFin`. */
export function anneesAvant(anneeFin: number, aujourdhui: Date = new Date()): number {
  const fin = new Date(anneeFin, 11, 31);
  const jours = Math.floor((fin.getTime() - aujourdhui.getTime()) / 86_400_000);
  return jours <= 0 ? 0 : Math.floor(jours / 365.25);
}

/**
 * Nombre de lignes en écart sur le dernier exercice comparable.
 * Les brouillons (sans liasse déposée) n'ont rien à comparer : on les ignore.
 */
export function compterEcarts(data: ReconResponse): { annee: number | null; nombre: number } {
  const avecLiasse = [...(data.annees ?? [])]
    .sort((a, b) => a - b)
    .filter((y) => data.results[String(y)] && !data.results[String(y)].brouillon);

  if (!avecLiasse.length) return { annee: null, nombre: 0 };

  const annee = avecLiasse[avecLiasse.length - 1];
  const nombre = data.results[String(annee)].lignes.filter((l) => l.ok === false).length;
  return { annee, nombre };
}
