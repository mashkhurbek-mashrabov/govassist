/**
 * Build `uz-Latn.json` and `en.json` from the design lane's `docs/design/copy.md` tables, plus the few
 * app strings copy.md does not have yet (`src/i18n/extra-copy.json`, to be upstreamed to copy.md).
 * `--check` fails when the committed files differ. ru is translated by hand; uz-Cyrl is generated.
 *
 * Usage: `node scripts/import-copy.ts [--check]`
 */
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

/** A locale tree: nested objects with string leaves. */
type Tree = { [key: string]: string | Tree };
/** One table row: `| `key` | uz-Latn | en | max |`. */
const ROW = /^\|\s*`([a-z0-9_.-]+)`\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*\d+\s*\|$/i;

/**
 * Set a dotted key in a tree.
 *
 * @param tree Target tree.
 * @param key Dotted key, e.g. `app.name`.
 * @param value String value.
 */
function setKey(tree: Tree, key: string, value: string): void {
  const [head, ...rest] = key.split(".");
  if (head === undefined) return;
  if (rest.length === 0) {
    tree[head] = value;
    return;
  }
  const child = tree[head];
  const next: Tree = typeof child === "object" ? child : {};
  tree[head] = next;
  setKey(next, rest.join("."), value);
}

/**
 * Deep-merge `extra` into `base` (extra wins).
 *
 * @param base Base tree (mutated).
 * @param extra Additional keys.
 * @returns The merged tree.
 */
function merge(base: Tree, extra: Tree): Tree {
  for (const [key, value] of Object.entries(extra)) {
    const current = base[key];
    base[key] = typeof value === "object" && typeof current === "object" ? merge(current, value) : value;
  }
  return base;
}

/**
 * Parse copy.md into one tree per language.
 *
 * @param markdown copy.md text.
 * @returns uz-Latn and en trees.
 */
export function parseCopy(markdown: string): { uz: Tree; en: Tree } {
  const uz: Tree = {};
  const en: Tree = {};
  for (const line of markdown.split("\n")) {
    const match = ROW.exec(line.trim());
    if (!match) continue;
    const [, key = "", uzText = "", enText = ""] = match;
    setKey(uz, key, uzText);
    setKey(en, key, enText);
  }
  return { uz, en };
}

/**
 * Write (or with `--check`, verify) the two locale files.
 *
 * @param check Only compare.
 */
function main(check: boolean): void {
  const locales = fileURLToPath(new URL("../src/i18n/locales/", import.meta.url));
  const copy = readFileSync(fileURLToPath(new URL("../../docs/design/copy.md", import.meta.url)), "utf8");
  const extra = JSON.parse(
    readFileSync(fileURLToPath(new URL("../src/i18n/extra-copy.json", import.meta.url)), "utf8"),
  ) as {
    "uz-Latn": Tree;
    en: Tree;
  };
  const { uz, en } = parseCopy(copy);
  const outputs: [string, Tree][] = [
    ["uz-Latn.json", merge(uz, extra["uz-Latn"])],
    ["en.json", merge(en, extra.en)],
  ];
  let stale = false;
  for (const [name, tree] of outputs) {
    const text = `${JSON.stringify(tree, null, 2)}\n`;
    if (!check) writeFileSync(`${locales}${name}`, text);
    else if (readFileSync(`${locales}${name}`, "utf8") !== text) stale = true;
  }
  if (stale) {
    console.error("uz-Latn.json / en.json differ from docs/design/copy.md. Run `npm run i18n:copy`.");
    process.exit(1);
  }
  console.info(
    check ? "uz-Latn.json and en.json match copy.md." : "Wrote uz-Latn.json and en.json from copy.md.",
  );
}

if (process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href) {
  main(process.argv.includes("--check"));
}
