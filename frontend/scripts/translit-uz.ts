/**
 * Generate `src/i18n/locales/uz-Cyrl.json` from `uz-Latn.json` (plan §7).
 * Uses the backend's fixed v1 rules (`02-backend-plan.md` §6) in reverse. `--check` fails if the file is stale.
 * The output needs native-speaker review.
 *
 * Usage: `node scripts/translit-uz.ts [--check]`
 */
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";

/** Apostrophe variants accepted for oʻ/gʻ and the tutuq belgisi (backend `canonicalize`). */
const APOSTROPHES = new Set(["ʻ", "ʼ", "'", "`", "‘", "’", "ʹ"]);
/** Latin vowels, for the `ye` rule. */
const VOWELS = new Set(["a", "e", "i", "o", "u"]);
/** Two-letter Latin sequences with one Cyrillic letter. `ye` is handled separately. */
const DIGRAPHS: Record<string, string> = { sh: "ш", ch: "ч", yo: "ё", yu: "ю", ya: "я" };
/** Single Latin letters. `e` is handled separately (э at word start). */
const LETTERS: Record<string, string> = {
  a: "а",
  b: "б",
  c: "ц",
  d: "д",
  f: "ф",
  g: "г",
  h: "ҳ",
  i: "и",
  j: "ж",
  k: "к",
  l: "л",
  m: "м",
  n: "н",
  o: "о",
  p: "п",
  q: "қ",
  r: "р",
  s: "с",
  t: "т",
  u: "у",
  v: "в",
  w: "в",
  x: "х",
  y: "й",
  z: "з",
};
/** Tokens that stay Latin: interpolation placeholders, brand names, domains. */
const PROTECTED = /\{\{[^}]+\}\}|\bGovAssist\b|\bGoogle\b|\b[\w-]+(?:\.[\w-]+)+\b/g;

/**
 * Whether a character is a Latin letter.
 *
 * @param char One character (or undefined past the end).
 * @returns `true` for a–z / A–Z.
 */
function isLatinLetter(char: string | undefined): boolean {
  return char !== undefined && /[a-z]/i.test(char);
}

/**
 * Match the case of the Latin source.
 *
 * @param cyrillic Lowercase Cyrillic output.
 * @param source The Latin sequence it came from.
 * @returns Uppercased when the source starts uppercase.
 */
function withCase(cyrillic: string, source: string): string {
  return source[0] === source[0]?.toUpperCase() ? cyrillic.toUpperCase() : cyrillic;
}

/**
 * Transliterate a run of plain text (no protected tokens).
 *
 * @param text Uzbek Latin text.
 * @returns Uzbek Cyrillic text.
 */
function transliterateRun(text: string): string {
  let out = "";
  let position = 0;
  while (position < text.length) {
    const char = text[position] ?? "";
    const lower = char.toLowerCase();
    const next = text[position + 1];
    const afterNext = text[position + 2];
    const previous = text[position - 1];
    const wordStart = !isLatinLetter(previous) && !APOSTROPHES.has(previous ?? "");

    if ((lower === "o" || lower === "g") && next !== undefined && APOSTROPHES.has(next)) {
      out += withCase(lower === "o" ? "ў" : "ғ", char);
      position += 2;
      continue;
    }
    const pair = `${lower}${next?.toLowerCase() ?? ""}`;
    const pairBlockedByApostrophe = pair[1] === "o" && afterNext !== undefined && APOSTROPHES.has(afterNext);
    if (pair === "ye" && (wordStart || VOWELS.has(previous?.toLowerCase() ?? ""))) {
      out += withCase("е", char);
      position += 2;
      continue;
    }
    const digraph = DIGRAPHS[pair];
    if (digraph && !pairBlockedByApostrophe) {
      out += withCase(digraph, char);
      position += 2;
      continue;
    }
    if (APOSTROPHES.has(char)) {
      out += "ъ";
    } else if (lower === "e") {
      out += withCase(wordStart ? "э" : "е", char);
    } else {
      out += LETTERS[lower] ? withCase(LETTERS[lower], char) : char;
    }
    position += 1;
  }
  return out;
}

/**
 * Transliterate Uzbek Latin to Uzbek Cyrillic, keeping placeholders, brands and domains as-is.
 *
 * @param text Uzbek Latin text.
 * @returns Uzbek Cyrillic text.
 */
export function latnToCyrl(text: string): string {
  let out = "";
  let last = 0;
  for (const match of text.matchAll(PROTECTED)) {
    out += transliterateRun(text.slice(last, match.index)) + match[0];
    last = match.index + match[0].length;
  }
  return out + transliterateRun(text.slice(last));
}

/** A locale tree: nested objects with string leaves. */
export type LocaleTree = { [key: string]: string | LocaleTree };

/**
 * Transliterate every string in a locale tree, keeping keys.
 *
 * @param tree `uz-Latn` messages.
 * @returns `uz-Cyrl` messages with identical keys.
 */
export function transliterateTree(tree: LocaleTree): LocaleTree {
  return Object.fromEntries(
    Object.entries(tree).map(([key, value]) => [
      key,
      typeof value === "string" ? latnToCyrl(value) : transliterateTree(value),
    ]),
  );
}

/**
 * Write (or with `--check`, verify) `uz-Cyrl.json`.
 *
 * @param check Only compare; exit 1 when the committed file differs.
 */
function main(check: boolean): void {
  const locales = fileURLToPath(new URL("../src/i18n/locales/", import.meta.url));
  const latn = JSON.parse(readFileSync(`${locales}uz-Latn.json`, "utf8")) as LocaleTree;
  const generated = `${JSON.stringify(transliterateTree(latn), null, 2)}\n`;
  const target = `${locales}uz-Cyrl.json`;
  if (!check) {
    writeFileSync(target, generated);
    console.info(`Wrote ${target}`);
    return;
  }
  if (readFileSync(target, "utf8") !== generated) {
    console.error("uz-Cyrl.json is stale. Run `npm run i18n:cyrl`.");
    process.exit(1);
  }
  console.info("uz-Cyrl.json is up to date.");
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main(process.argv.includes("--check"));
}
