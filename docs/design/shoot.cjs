#!/usr/bin/env node
/**
 * Screenshots every prototype state and audits it.
 *
 * For each prototype page and each state in its state bar, at 375x812 and 1440x900 (reduced motion on):
 *   - writes screenshots/<page>--<state>--<width>.png (full page; viewport only when a drawer or dialog is open);
 *   - reports horizontal overflow, interactive targets under 44 px and axe-core serious/critical violations (375 only);
 *   - writes screenshots/glyph-proof.png from type.html.
 * For each journey (j*.html), every step at 375x812 (J2 and J6 also at 1440x900):
 *   - writes screenshots/journeys/<J>-<nn>-<step>.png, with the same audits;
 *   - checks every in-journey link target exists and every step but the last has a way forward;
 *   - plays J1's streaming steps in real time (normal and reduced motion) and checks it reaches the final answer.
 * Glass (v1.1): scrolled viewport shots with content under the glass chrome, each in three variants:
 *   glass, solid via prefers-reduced-transparency (real media emulation), solid via no backdrop-filter
 *   (simulated: the @supports-not block's token values are applied and backdrop-filter is removed).
 *   Written to screenshots/glass/.
 * If `sharp` is installed next to playwright, every PNG is then re-saved as a 256-colour palette PNG
 * (about 70 % smaller; `node shoot.cjs compress` does only this step).
 *
 * Needs `playwright` and `axe-core`, which no package in the repo installs. Run from a scratch folder:
 *   npm i playwright axe-core && npx playwright install chromium
 *   node <repo>/docs/design/shoot.cjs            # all pages
 *   node <repo>/docs/design/shoot.cjs settings   # pages whose file name starts with "settings"
 *   node <repo>/docs/design/shoot.cjs j          # journeys only
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
const JOURNEY_OUT = path.join(OUT, "journeys");
const JOURNEY_FILE = /^j\d+\.html$/;
const DESKTOP_JOURNEYS = ["j2.html", "j6.html"];
const PLAYBACK = { file: "j1.html", from: "a-searching", to: "a-final", timeoutMs: 20000 };
const VIEWPORTS = [{ width: 375, height: 812 }, { width: 1440, height: 900 }];
const MIN_TARGET = 43.5; // 44 px, allowing sub-pixel rounding
const GLASS_OUT = path.join(OUT, "glass");
const GLASS_SHOTS = [
  { file: "answer-service.html", hash: "complete", scroll: 700, viewport: VIEWPORTS[0] },
  { file: "chat-streaming.html", hash: "office", scroll: 260, viewport: VIEWPORTS[0] },
  { file: "chat-empty.html", hash: "drawer", scroll: 0, viewport: VIEWPORTS[0] },
  { file: "history.html", hash: "confirm", scroll: 0, viewport: VIEWPORTS[0] },
  { file: "answer-service.html", hash: "complete", scroll: 600, viewport: VIEWPORTS[1] },
];
/** Same values as the @supports-not block in tokens.css, plus no backdrop-filter. */
const NO_BACKDROP_CSS = ":root{--color-glass:var(--palette-white)!important;--color-glass-strong:var(--palette-white)!important;--glass-blur:0px!important;--glass-saturate:1!important}*{backdrop-filter:none!important;-webkit-backdrop-filter:none!important}";
/** Unsticks the composer and sidebar so a full-page shot shows them once, in place; hides the prototype bar. */
const SHOT_CSS = ".proto-bar{display:none!important} .composer,body:not(.drawer-open) .sidebar{position:static!important} body:not(.drawer-open) .sidebar{height:auto!important}";

/**
 * Lists prototype pages with the states their state bar offers.
 * @returns {Array<[string, string[]]>} File name and states.
 */
function listPages() {
  return fs.readdirSync(PROTO)
    .filter((f) => f.endsWith(".html") && !["index.html", "journeys.html"].includes(f) && !JOURNEY_FILE.test(f))
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

/**
 * Lists journey files with their step ids and screenshot names.
 * @returns {Array<[string, Array<[string, string]>]>} File and [id, shot name] per step.
 */
function listJourneys() {
  return fs.readdirSync(PROTO).filter((f) => JOURNEY_FILE.test(f)).sort().map((f) => {
    const html = fs.readFileSync(path.join(PROTO, f), "utf8");
    return [f, [...html.matchAll(/<section class="flow-step" id="([\w-]+)"[^>]*data-shot="([\w-]+)"/g)].map((m) => [m[1], m[2]])];
  });
}

/**
 * Finds broken step links and dead ends in a journey (runs in the browser).
 * @returns {string[]} Problems.
 */
function linkAuditInPage() {
  const steps = [...document.querySelectorAll(".flow-step")];
  const ids = new Set(steps.map((s) => s.id));
  const problems = [];
  steps.forEach((step, i) => {
    const targets = [...step.querySelectorAll("[data-go]")].map((el) => el.getAttribute("data-go"))
      .concat([...step.querySelectorAll("a[href^='#']")].map((a) => a.getAttribute("href").slice(1)).filter((id) => ids.has(id)));
    targets.filter((t) => !ids.has(t)).forEach((t) => problems.push(`${step.id}: link to missing step "${t}"`));
    const forward = targets.some((t) => ids.has(t) && t !== step.id) || step.hasAttribute("data-auto");
    if (!forward && i < steps.length - 1) problems.push(`${step.id}: dead end (no link forward, no auto-advance)`);
  });
  return problems;
}

/**
 * Plays J1's streaming in real time and checks it ends on the final answer.
 * @param {import("playwright").Browser} browser
 * @param {"no-preference" | "reduce"} reducedMotion
 * @returns {Promise<string|null>} A problem, or null.
 */
async function checkPlayback(browser, reducedMotion) {
  const context = await browser.newContext({ viewport: VIEWPORTS[0], reducedMotion });
  const page = await context.newPage();
  await page.goto(`file://${path.join(PROTO, PLAYBACK.file)}#${PLAYBACK.from}`);
  try {
    await page.waitForFunction((id) => location.hash === `#${id}`, PLAYBACK.to, { timeout: PLAYBACK.timeoutMs });
    return null;
  } catch {
    return `playback (${reducedMotion}): stuck at ${await page.evaluate(() => location.hash)}`;
  } finally {
    await context.close();
  }
}

/**
 * Screenshots and audits every journey step.
 * @param {import("playwright").Browser} browser
 * @param {string} axeSource
 * @param {string[]} problems Collects findings.
 */
async function shootJourneys(browser, axeSource, problems) {
  fs.mkdirSync(JOURNEY_OUT, { recursive: true });
  for (const viewport of VIEWPORTS) {
    const context = await browser.newContext({ viewport, reducedMotion: "reduce" });
    const page = await context.newPage();
    for (const [file, steps] of listJourneys()) {
      if (viewport !== VIEWPORTS[0] && !DESKTOP_JOURNEYS.includes(file)) continue;
      for (const [id, shotName] of steps) {
        const name = viewport === VIEWPORTS[0] ? `${shotName}.png` : `${shotName}-${viewport.width}.png`;
        await page.goto(`file://${path.join(PROTO, file)}?shot#${id}`);
        await page.evaluate(() => document.fonts.ready);
        await page.addStyleTag({ content: SHOT_CSS });
        const overlay = await page.evaluate(() =>
          [...document.querySelectorAll(".flow-step:not([hidden]) .scrim")].some((e) => e.getClientRects().length > 0));
        await page.screenshot({ path: path.join(JOURNEY_OUT, name), fullPage: !overlay });
        const audit = await page.evaluate(auditInPage, { viewportWidth: viewport.width, minTarget: MIN_TARGET });
        if (audit.overflow) problems.push(`journeys/${name}: horizontal overflow`);
        if (audit.small.length) problems.push(`journeys/${name}: small targets ${[...new Set(audit.small)].join(", ")}`);
        if (viewport === VIEWPORTS[0]) {
          await page.addScriptTag({ content: axeSource });
          const violations = await page.evaluate(async () => {
            const result = await axe.run(document.querySelector(".flow-step:not([hidden])"), { runOnly: ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"], resultTypes: ["violations"] });
            return result.violations.filter((v) => v.impact === "serious" || v.impact === "critical").map((v) => v.id);
          });
          if (violations.length) problems.push(`journeys/${name}: axe ${violations.join(", ")}`);
        }
      }
      if (viewport === VIEWPORTS[0]) problems.push(...(await page.evaluate(linkAuditInPage)).map((p) => `${file} ${p}`));
    }
    await context.close();
  }
  for (const motion of ["no-preference", "reduce"]) {
    const problem = await checkPlayback(browser, motion);
    if (problem) problems.push(problem);
  }
}

/**
 * Screenshots the glass chrome over scrolled content, plus its two solid fallbacks.
 * @param {import("playwright").Browser} browser
 */
async function shootGlass(browser) {
  fs.mkdirSync(GLASS_OUT, { recursive: true });
  const variants = [
    { name: "glass", css: "" , transparency: "no-preference" },
    { name: "solid-reduced-transparency", css: "", transparency: "reduce" },
    { name: "solid-no-backdrop", css: NO_BACKDROP_CSS, transparency: "no-preference" },
  ];
  for (const shot of GLASS_SHOTS) {
    for (const v of variants) {
      const context = await browser.newContext({ viewport: shot.viewport, reducedMotion: "reduce" });
      const page = await context.newPage();
      const cdp = await context.newCDPSession(page);
      await cdp.send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-transparency", value: v.transparency }] });
      await page.goto(`file://${path.join(PROTO, shot.file)}#${shot.hash}`);
      await page.evaluate(() => document.fonts.ready);
      await page.addStyleTag({ content: ".proto-bar{display:none!important}" + v.css });
      await page.evaluate((y) => window.scrollTo(0, y), shot.scroll);
      const name = `${shot.file.replace(".html", "")}--${shot.hash}--${shot.viewport.width}--${v.name}.png`;
      await page.screenshot({ path: path.join(GLASS_OUT, name) });
      await context.close();
    }
  }
}

/**
 * Re-saves every screenshot as a palette PNG when sharp is available; skips silently otherwise.
 * @returns {Promise<number>} Files compressed.
 */
async function compressScreenshots() {
  let sharp;
  try { sharp = requireFromCwd("sharp"); } catch { return 0; }
  const files = fs.readdirSync(OUT, { recursive: true }).filter((f) => f.endsWith(".png")).map((f) => path.join(OUT, f));
  for (const file of files) {
    const buffer = await sharp(file).png({ palette: true, quality: 90, effort: 10, dither: 1 }).toBuffer();
    fs.writeFileSync(file, buffer);
  }
  return files.length;
}

/** Entry point. */
async function main() {
  const only = process.argv[2] ?? "";
  if (only === "compress") { console.log(`compressed ${await compressScreenshots()} screenshots`); return; }
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
          [...document.querySelectorAll(".scrim, .toast, .lang-menu__scrim[data-portal]")].some((e) => e.getClientRects().length > 0 && getComputedStyle(e).display !== "none") ||
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
  if (!only || only === "j") await shootJourneys(browser, axeSource, problems);
  if (!only || only === "glass") await shootGlass(browser);
  await browser.close();
  const compressed = await compressScreenshots();
  if (compressed) console.log(`compressed ${compressed} screenshots (palette PNG)`);
  for (const p of problems) console.error(p);
  console.log(problems.length ? `${problems.length} problem(s)` : "screenshots written, audits clean");
  process.exit(problems.length ? 1 : 0);
}

main();
