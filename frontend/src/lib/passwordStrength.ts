/** Password strength for the 3-segment hint (components.md → PasswordField). A hint only; the backend decides. */

/** Minimum length (contract/backend rule). */
export const MIN_PASSWORD_LENGTH = 10;
/** Length from which a varied password counts as strong. */
const STRONG_LENGTH = 12;
/** Character classes: lower, upper, digit, other. */
const CLASSES = [/[a-zа-яёўқғҳ]/, /[A-ZА-ЯЁЎҚҒҲ]/, /\d/, /[^\p{L}\d]/u];
/** Classes needed for "strong". */
const STRONG_CLASSES = 3;

/** 1 weak · 2 fair · 3 strong. */
export type StrengthLevel = 1 | 2 | 3;

/**
 * Rate a password.
 *
 * @param password The candidate.
 * @returns 1 when shorter than the minimum, 3 when long and varied, else 2.
 */
export function passwordStrength(password: string): StrengthLevel {
  if (password.length < MIN_PASSWORD_LENGTH) return 1;
  const classes = CLASSES.filter((pattern) => pattern.test(password)).length;
  return password.length >= STRONG_LENGTH && classes >= STRONG_CLASSES ? 3 : 2;
}
