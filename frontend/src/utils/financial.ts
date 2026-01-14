/**
 * Fonctions financières équivalentes à Excel
 * 
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 * 
 * Implémentation des fonctions PMT, IPMT, PPMT pour les calculs de crédit
 * Formules équivalentes à Excel pour garantir la cohérence
 */

/**
 * Calcule le paiement périodique constant (PMT)
 * Équivalent à Excel: =PMT(rate, nper, pv, fv, type)
 * 
 * @param rate - Taux d'intérêt par période (ex: 0.02/12 pour 2% annuel mensuel)
 * @param nper - Nombre total de périodes
 * @param pv - Valeur actuelle (montant du crédit, négatif pour un emprunt)
 * @param fv - Valeur future (par défaut 0)
 * @param type - Type de paiement (0 = fin de période, 1 = début de période, par défaut 0)
 * @returns Le paiement périodique constant
 */
export function PMT(rate: number, nper: number, pv: number, fv: number = 0, type: number = 0): number {
  if (rate === 0) {
    // Si taux = 0, paiement = (pv + fv) / nper
    return -(pv + fv) / nper;
  }
  
  const pvif = Math.pow(1 + rate, nper); // (1 + rate)^nper
  const pmt = (pv * rate * pvif + fv * rate) / (pvif - 1);
  
  if (type === 1) {
    // Paiement en début de période
    return pmt / (1 + rate);
  }
  
  return pmt;
}

/**
 * Calcule la part d'intérêt pour une période donnée (IPMT)
 * Équivalent à Excel: =IPMT(rate, per, nper, pv, fv, type)
 * 
 * @param rate - Taux d'intérêt par période
 * @param per - Numéro de la période (1-based, ex: 1 pour la première mensualité)
 * @param nper - Nombre total de périodes
 * @param pv - Valeur actuelle (montant du crédit, négatif)
 * @param fv - Valeur future (par défaut 0)
 * @param type - Type de paiement (0 = fin de période, 1 = début de période, par défaut 0)
 * @returns La part d'intérêt pour la période donnée
 */
export function IPMT(rate: number, per: number, nper: number, pv: number, fv: number = 0, type: number = 0): number {
  if (per < 1 || per > nper) {
    throw new Error(`Période invalide: ${per} (doit être entre 1 et ${nper})`);
  }
  
  const pmt = PMT(rate, nper, pv, fv, type);
  
  // Calculer le solde restant dû au début de la période per
  // Le solde est toujours positif (on doit de l'argent)
  let balance = Math.abs(pv);
  
  if (type === 1) {
    // Ajuster pour paiement en début de période
    balance = balance * (1 + rate);
    // Soustraire le paiement immédiatement
    balance = balance - Math.abs(pmt);
  }
  
  // Calculer le solde jusqu'à la période per-1
  // À chaque période : solde augmente avec les intérêts, puis diminue avec le paiement
  for (let i = 1; i < per; i++) {
    // Ajouter les intérêts
    balance = balance * (1 + rate);
    // Soustraire le paiement (pmt est négatif, donc on soustrait sa valeur absolue)
    balance = balance - Math.abs(pmt);
    
    // Le solde ne peut pas être négatif
    if (balance < 0) {
      balance = 0;
    }
  }
  
  // La part d'intérêt = solde au début de la période * taux
  // Calculer le solde au début de la période per (avant le paiement)
  const balanceAtStart = balance;
  const interest = balanceAtStart * rate;
  
  // Retourner avec le signe opposé à pv pour cohérence avec Excel
  return pv < 0 ? -interest : interest;
}

/**
 * Calcule la part de capital pour une période donnée (PPMT)
 * Équivalent à Excel: =PPMT(rate, per, nper, pv, fv, type)
 * 
 * @param rate - Taux d'intérêt par période
 * @param per - Numéro de la période (1-based)
 * @param nper - Nombre total de périodes
 * @param pv - Valeur actuelle (montant du crédit, négatif)
 * @param fv - Valeur future (par défaut 0)
 * @param type - Type de paiement (0 = fin de période, 1 = début de période, par défaut 0)
 * @returns La part de capital pour la période donnée
 */
export function PPMT(rate: number, per: number, nper: number, pv: number, fv: number = 0, type: number = 0): number {
  // PPMT = PMT - IPMT
  const pmt = PMT(rate, nper, pv, fv, type);
  const ipmt = IPMT(rate, per, nper, pv, fv, type);
  
  return pmt - ipmt;
}

/**
 * Formate un montant en euros avec 2 décimales
 * 
 * @param amount - Montant à formater
 * @returns Montant formaté (ex: "1 234,56 €")
 */
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
}

/**
 * Arrondit un nombre à 2 décimales
 * 
 * @param value - Valeur à arrondir
 * @returns Valeur arrondie à 2 décimales
 */
export function roundTo2Decimals(value: number): number {
  return Math.round(value * 100) / 100;
}
