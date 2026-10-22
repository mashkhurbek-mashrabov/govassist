/**
 * Copy the design lane's single sources into the app, unchanged:
 * `docs/design/tokens.css` → `src/styles/tokens.css` and `docs/design/fonts/*` → `src/styles/fonts/`.
 * `--check` fails when any copy differs (CI). Never edit the copies by hand.
 *
 * Usage: `node scripts/sync-tokens.ts [--check]`
 */
import { copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

/**
 * Absolute path relative to this script.
 *
 * @param path Relative path.
 * @returns Absolute path.
 */
function here(path: string): string {
  return fileURLToPath(new URL(path, import.meta.url));
}

const design = here("../../docs/design/");
const styles = here("../src/styles/");
/** Source → target pairs. */
const pairs: [string, string][] = [
  [`${design}tokens.css`, `${styles}tokens.css`],
  ...readdirSync(`${design}fonts`).map((name): [string, string] => [
    `${design}fonts/${name}`,
    `${styles}fonts/${name}`,
  ]),
];
const check = process.argv.includes("--check");

const stale = pairs.filter(
  ([source, target]) => !existsSync(target) || !readFileSync(source).equals(readFileSync(target)),
);
if (check) {
  if (stale.length > 0) {
    console.error(
      `Out of sync with docs/design: ${stale.map(([, target]) => target).join(", ")}. Run \`npm run sync:tokens\`.`,
    );
    process.exit(1);
  }
  console.info("tokens.css and fonts are in sync.");
} else {
  mkdirSync(`${styles}fonts`, { recursive: true });
  for (const [source, target] of pairs) copyFileSync(source, target);
  console.info(`Synced ${pairs.length} files from docs/design.`);
}
