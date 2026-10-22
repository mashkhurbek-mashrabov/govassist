/**
 * Fail when the initial JS (entry script + modulepreloads in `dist/index.html`) exceeds the budget
 * (plan §8: ≤ 200 KB gzip). Run after `npm run build`.
 *
 * Usage: `node scripts/check-bundle-size.ts`
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";

/** Initial JS budget in bytes (gzip). */
const BUDGET_BYTES = 200 * 1024;
const dist = fileURLToPath(new URL("../dist/", import.meta.url));
const html = readFileSync(`${dist}index.html`, "utf8");
const scripts = [...html.matchAll(/(?:src|href)="\/(assets\/[^"]+\.js)"/g)].map((match) => match[1] ?? "");

let total = 0;
for (const script of scripts) {
  const size = gzipSync(readFileSync(`${dist}${script}`)).length;
  total += size;
  console.info(`${(size / 1024).toFixed(1).padStart(7)} KB  ${script}`);
}
console.info(
  `${(total / 1024).toFixed(1).padStart(7)} KB  initial JS total (budget ${BUDGET_BYTES / 1024} KB gzip)`,
);
if (total > BUDGET_BYTES) {
  console.error("Initial JS is over budget.");
  process.exit(1);
}
