/**
 * Drapeau « J'ai un crédit » — persisté PAR BIEN.
 *
 * ⚠️ Historique : la clé était `etats_financiers_has_credit`, sans property_id.
 * L'onglet Crédit apparaissait donc — ou disparaissait — pour les 3 biens d'un
 * seul coup, alors que chacun a ses propres crédits en base. Pire : décocher la
 * case supprimait les crédits du seul bien ACTIF, mais masquait l'onglet pour
 * les autres, dont les données subsistaient — devenues inatteignables.
 *
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */

const PREFIX = 'etats_financiers_has_credit';

/** Clé de stockage du drapeau pour un bien donné. */
export function creditFlagKey(propertyId: number): string {
  return `${PREFIX}_${propertyId}`;
}

/** Lit le drapeau d'un bien. Absent / property_id invalide → false. */
export function readCreditFlag(propertyId: number | null | undefined): boolean {
  if (typeof window === 'undefined') return false;
  if (propertyId == null || propertyId <= 0) return false;
  return localStorage.getItem(creditFlagKey(propertyId)) === 'true';
}

/** Écrit le drapeau d'un bien. property_id invalide → ne fait rien. */
export function writeCreditFlag(propertyId: number | null | undefined, value: boolean): void {
  if (typeof window === 'undefined') return;
  if (propertyId == null || propertyId <= 0) return;
  localStorage.setItem(creditFlagKey(propertyId), value ? 'true' : 'false');
}
