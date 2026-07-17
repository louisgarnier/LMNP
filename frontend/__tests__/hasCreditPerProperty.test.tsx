import { creditFlagKey, readCreditFlag, writeCreditFlag } from '@/utils/creditFlag';

beforeEach(() => localStorage.clear());

test('la clé du drapeau crédit est distincte par bien', () => {
  expect(creditFlagKey(15)).not.toBe(creditFlagKey(25));
  expect(creditFlagKey(26)).not.toBe(creditFlagKey(15));
});

test('activer le crédit sur un bien ne le change pas sur un autre', () => {
  writeCreditFlag(26, true);

  expect(readCreditFlag(26)).toBe(true);
  // Le bug d'origine : la clé était globale, donc les 3 biens bougeaient ensemble.
  expect(readCreditFlag(15)).toBe(false);
  expect(readCreditFlag(25)).toBe(false);
});

test('désactiver le crédit sur un bien laisse les autres intacts', () => {
  writeCreditFlag(26, true);
  writeCreditFlag(15, true);
  writeCreditFlag(25, true);

  writeCreditFlag(26, false);

  expect(readCreditFlag(26)).toBe(false);
  expect(readCreditFlag(15)).toBe(true);
  expect(readCreditFlag(25)).toBe(true);
});

test('un bien sans drapeau enregistré est à false', () => {
  expect(readCreditFlag(15)).toBe(false);
});

test('un property_id absent ne lit ni n’écrit rien', () => {
  writeCreditFlag(null, true);
  expect(readCreditFlag(null)).toBe(false);
  expect(localStorage.length).toBe(0);
});
