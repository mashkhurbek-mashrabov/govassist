/**
 * Copy `docs/design/tokens.css` (the single source of design values) to `src/styles/tokens.css`.
 * `--check` fails when the copy differs. Before gate G2 the source does not exist yet; both modes then
 * report that and succeed.
 *
 * Usage: `node scripts/sync-tokens.ts [--check]`
 */
import { copyFileSync, existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const source = fileURLToPath(new URL("../../docs/design/tokens.css", import.meta.url));
const target = fileURLToPath(new URL("../src/styles/tokens.css", import.meta.url));
const check = process.argv.includes("--check");

if (!existsSync(source)) {
  console.info("docs/design/tokens.css does not exist yet (before G2); nothing to sync.");
} else if (!check) {
  copyFileSync(source, target);
  console.info(`Copied ${source} → ${target}`);
} else if (!existsSync(target) || readFileSync(source, "utf8") !== readFileSync(target, "utf8")) {
  console.error("src/styles/tokens.css differs from docs/design/tokens.css. Run `npm run sync:tokens`.");
  process.exit(1);
} else {
  console.info("tokens.css is in sync.");
}
