#!/usr/bin/env node
/**
 * Screenshots every prototype state and audits it.
 *
 * For each prototype page and each state in its state bar, at 375x812 and 1440x900 (reduced motion on):
 *   - writes screenshots/<page>--<state>--<width>.png (full page; viewport only when a drawer or dialog is open);
 *   - reports horizontal overflow, interactive targets under 44 px and axe-core serious/critical violations (375 only);
 *   - writes screenshots/glyph-proof.png from type.html.
 *
 * Needs `playwright` and `axe-core`, which no package in the repo installs. Run from a scratch folder:
 *   npm i playwright axe-core && npx playwright install chromium
 *   node <repo>/docs/design/shoot.cjs            # all pages
 *   node <repo>/docs/design/shoot.cjs settings   # pages whose file name starts with "settings"
 *   CHROME_PATH=/path/to/chrome node …            # use an already installed Chromium
 * Exit code 1 if any audit finds a problem.
 */
const fs = require("node:fs");
const path = require("node:path");
const { createRequire } = require("node:module");

// Resolve playwright and axe-core from the folder the script is run in, not from the repo.
const requireFromCwd = createRequire(path.join(process.cwd(), "noop.js"));
const { chromium } = requireFromCwd("playwright");

const DESIGN = __dirname;
const PROTO = path.join(DESIGN, "prototype");
const OUT = path.join(DESIGN, "screenshots");
const VIEWPORTS = [{ width: 375, height: 812 }, { width: 1440, height: 900 }];
const MIN_TARGET = 43.5; // 44 px, allowing sub-pixel rounding
/** Unsticks the composer and sidebar so a full-page shot shows them once, in place; hides the prototype bar. */
const SHOT_CSS = ".proto-bar{display:none!important} .composer,body:not(.drawer-open) .sidebar{position:static!important} body:not(.drawer-open) .sidebar{height:auto!important}";

/**
 * Lists prototype pages with the states their state bar offers.
 * @returns {Array<[string, string[]]>} File name and states.
 */
function listPages() {
  return fs.readdirSync(PROTO)
    .filter((f) => f.endsWith(".html") && f !== "index.html")
    .map((f) => {
      const html = fs.readFileSync(path.join(PROTO, f), "utf8");
      const states = [...html.matchAll(/<button type="button" data-state="([\w-]+)"/g)].map((m) => m[1]);
      return [f, states.length ? states : ["default"]];
    });
}

/**
 * Measures overflow and small targets on the current page (runs in the browser).
 * @param {{viewportWidth: number, minTarget: number}} limits Viewport width and minimum target size, in CSS px.
 * @returns {{overflow: boolean, small: string[]}} Findings.
 */
function auditInPage({ viewportWidth, minTarget }) {
  const small = [];
  for (const el of document.querySelectorAll("a[href], button, input, select, textarea, summary, [role=option]")) {
    const box = el.getBoundingClientRect();
    if (!box.width || !box.height || el.closest(".proto-bar")) continue;
    const inlineTextLink = el.tagName === "A" && !el.className && el.closest("p, li, dd") && getComputedStyle(el).display === "inline";
    if (inlineTextLink) continue; // WCAG 2.5.8 inline exception
    const label = (el.type === "checkbox" || el.type === "radio") && el.closest("label");
    if (label && label.getBoundingClientRect().height >= minTarget) continue;
    const size = el.classList.contains("cite") ? minTarget : Math.min(box.width, box.height); // .cite hit area comes from ::after
    if (size < minTarget) small.push(`${el.tagName.toLowerCase()}.${el.className} ${Math.round(box.width)}x${Math.round(box.height)}`);
  }
  return { overflow: document.documentElement.scrollWidth > viewportWidth + 0.5, small };
}

/** Entry point. */
async function main() {
  const only = process.argv[2] ?? "";
  const axeSource = fs.readFileSync(requireFromCwd.resolve("axe-core/axe.min.js"), "utf8");
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || undefined });
  const problems = [];
  for (const viewport of VIEWPORTS) {
    const context = await browser.newContext({ viewport, reducedMotion: "reduce" });
    const page = await context.newPage();
    for (const [file, states] of listPages().filter(([f]) => f.startsWith(only))) {
      for (const state of states) {
        const name = `${file.replace(".html", "")}--${state}--${viewport.width}.png`;
        await page.goto(`file://${path.join(PROTO, file)}#${state}`);
        await page.evaluate(() => document.fonts.ready);
        await page.addStyleTag({ content: SHOT_CSS });
        const overlay = await page.evaluate(() =>
          [...document.querySelectorAll(".scrim, .toast")].some((e) => e.getClientRects().length > 0) ||
          document.body.classList.contains("drawer-open"));
        await page.screenshot({ path: path.join(OUT, name), fullPage: !overlay });
        const audit = await page.evaluate(auditInPage, { viewportWidth: viewport.width, minTarget: MIN_TARGET });
        if (audit.overflow) problems.push(`${name}: horizontal overflow`);
        if (audit.small.length) problems.push(`${name}: small targets ${[...new Set(audit.small)].join(", ")}`);
        if (viewport.width === VIEWPORTS[0].width) {
          await page.addScriptTag({ content: axeSource });
          const violations = await page.evaluate(async () => {
            const result = await axe.run(document, { runOnly: ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"], resultTypes: ["violations"] });
            return result.violations.filter((v) => v.impact === "serious" || v.impact === "critical").map((v) => v.id);
          });
          if (violations.length) problems.push(`${name}: axe ${violations.join(", ")}`);
          if (file === "type.html") await (await page.$(".section")).screenshot({ path: path.join(OUT, "glyph-proof.png") });
        }
      }
    }
    await context.close();
  }
  await browser.close();
  for (const p of problems) console.error(p);
  console.log(problems.length ? `${problems.length} problem(s)` : "screenshots written, audits clean");
  process.exit(problems.length ? 1 : 0);
}

main();
