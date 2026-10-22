/**
 * Two-script search for the region/district combobox: "Чилонзор" finds "Chilonzor" (components.md).
 * Uzbek Cyrillic is mapped to Latin with the backend's fixed rules (02-backend-plan.md §6), then both
 * sides are canonicalized (lowercase, apostrophes dropped).
 */

/** Uzbek/Russian Cyrillic → Latin, one letter at a time (е at a word start is handled below). */
const CYRILLIC_TO_LATIN: Record<string, string> = {
  а: "a",
  б: "b",
  в: "v",
  г: "g",
  д: "d",
  е: "e",
  ё: "yo",
  ж: "j",
  з: "z",
  и: "i",
  й: "y",
  к: "k",
  л: "l",
  м: "m",
  н: "n",
  о: "o",
  п: "p",
  р: "r",
  с: "s",
  т: "t",
  у: "u",
  ф: "f",
  х: "x",
  ц: "ts",
  ч: "ch",
  ш: "sh",
  щ: "sh",
  ъ: "",
  ы: "i",
  ь: "",
  э: "e",
  ю: "yu",
  я: "ya",
  ў: "o",
  қ: "q",
  ғ: "g",
  ҳ: "h",
};
/** Every apostrophe variant (ʻ ʼ ' ` ‘ ’ ʹ). */
const APOSTROPHES = /[ʻʼ'`‘’ʹ]/g;

/**
 * Canonical, Latin-only form of a name for matching.
 *
 * @param text A name in either script.
 * @returns Lowercase Latin without apostrophes.
 */
export function searchKey(text: string): string {
  const lower = text.toLowerCase().replace(APOSTROPHES, "");
  let out = "";
  for (let position = 0; position < lower.length; position += 1) {
    const char = lower[position] ?? "";
    const wordStart = position === 0 || /\s|-/.test(lower[position - 1] ?? "");
    out += char === "е" && wordStart ? "ye" : (CYRILLIC_TO_LATIN[char] ?? char);
  }
  return out.replace(/\s+/g, " ").trim();
}

/**
 * Whether an option matches the typed query in either script.
 *
 * @param option Option label.
 * @param query What the user typed.
 * @returns `true` when the query is empty or contained in the option.
 */
export function matchesQuery(option: string, query: string): boolean {
  const needle = searchKey(query);
  return needle === "" || searchKey(option).includes(needle);
}
