/**
 * Generate `src/i18n/locales/uz-Cyrl.json` from `uz-Latn.json` (plan §7) with `src/lib/translit.ts`.
 * `--check` fails if the file is stale. The output needs native-speaker review.
 *
 * Usage: `node scripts/translit-uz.ts [--check]`
 */
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import { transliterateTree, type LocaleTree } from "../src/lib/translit.ts";

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
