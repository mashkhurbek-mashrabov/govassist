/** Avatar initials for the account menu. */

/** How many words of the name give a letter. */
const NAME_WORDS = 2;

/**
 * The first character of a string (a whole code point, so non-BMP letters stay intact), upper-cased.
 *
 * @param word Any text.
 * @returns The letter, or "".
 */
function firstLetter(word: string): string {
  const code = word.codePointAt(0);
  return code === undefined ? "" : String.fromCodePoint(code).toLocaleUpperCase();
}

/**
 * Initials from the first two words of the display name, else the first letter of the email.
 *
 * @param displayName `Me.display_name` (may be empty or null).
 * @param email `Me.email`.
 * @returns One or two upper-case letters.
 */
export function initials(displayName: string | null, email: string): string {
  const words = (displayName ?? "").trim().split(/\s+/u).filter(Boolean).slice(0, NAME_WORDS);
  return words.length > 0 ? words.map(firstLetter).join("") : firstLetter(email);
}
