#!/usr/bin/env node
/**
 * Keeps tokens.json in step with tokens.css and guards the prototype.
 *
 *   node docs/design/tokens.mjs           rewrite tokens.json from tokens.css
 *   node docs/design/tokens.mjs --check   exit 1 if tokens.json is stale, or if the prototype
 *                                         uses a raw hex color, a raw length, an undefined --variable,
 *                                         or an inline icon that is not an exact Lucide icon from ./icons
 *
 * tokens.css is the source; tokens.json is derived (W3C Design Tokens format). No dependencies.
 */
import { readFileSync, writeFileSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const CSS_PATH = join(HERE, "tokens.css");
const JSON_PATH = join(HERE, "tokens.json");
const PROTOTYPE_DIR = join(HERE, "prototype");

/** Context name for each CSS block that declares tokens. */
const BLOCKS = [
  { name: "base", match: (sel, media) => sel === ":root" && media === null },
  { name: "md", match: (sel, media) => sel === ":root" && media?.includes("min-width: 768px") },
  { name: "reducedMotion", match: (sel, media) => sel === ":root" && media?.includes("prefers-reduced-motion") },
  { name: "solidGlass", match: (sel, media) => sel === ":root" && (media?.includes("prefers-reduced-transparency") || media?.startsWith("@supports not")) },
  { name: "dark", match: (sel, media) => sel === ':root[data-theme="dark"]' && media === null },
];

/**
 * Reads every `--name: value;` declaration from tokens.css, grouped by block.
 * @param {string} css The stylesheet text.
 * @returns {Record<string, Array<[string, string]>>} Declarations per block name.
 */
function parseTokens(css) {
  const clean = css.replace(/\/\*[\s\S]*?\*\//g, "");
  const out = Object.fromEntries(BLOCKS.map((b) => [b.name, []]));
  const ruleRe = /(@(?:media|supports)[^{]+)\{\s*(:root[^{]*)\{([^}]*)\}\s*\}|(:root[^{]*)\{([^}]*)\}/g;
  for (const m of clean.matchAll(ruleRe)) {
    const media = m[1] ? m[1].trim() : null;
    const selector = (m[2] ?? m[4]).trim();
    const body = m[3] ?? m[5];
    const block = BLOCKS.find((b) => b.match(selector, media));
    if (!block) throw new Error(`Unexpected token block: ${media ?? ""} ${selector}`);
    for (const d of body.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)) out[block.name].push([d[1], d[2].trim()]);
  }
  return out;
}

/**
 * Maps a CSS variable name to its dotted path in tokens.json.
 * @param {string} name A variable name such as `--color-primary`.
 * @param {string} block The block it was declared in.
 * @returns {string[]} The path segments.
 */
function pathOf(name, block = "base") {
  const [group, ...rest] = name.slice(2).split("-");
  const key = rest.join("-");
  if (group === "palette") return ["color", "palette", key];
  if (group === "color") return ["color", block === "dark" ? "dark" : "light", key];
  return [group, key];
}

/**
 * Infers the W3C token type of a raw CSS value.
 * @param {string} name The variable name.
 * @param {string} value The CSS value.
 * @returns {string} A Design Tokens `$type`.
 */
function typeOf(name, value) {
  if (name.startsWith("--palette-") || name.startsWith("--color-")) return "color";
  if (name.startsWith("--gradient-")) return "gradient";
  if (name.startsWith("--shadow-")) return "shadow";
  if (value.includes("gradient(")) return "gradient";
  if (name.startsWith("--font-sans")) return "fontFamily";
  if (name.startsWith("--font-weight")) return "fontWeight";
  if (/^cubic-bezier/.test(value)) return "cubicBezier";
  if (/ms$/.test(value)) return "duration";
  if (/(rem|px|em)$/.test(value) || value === "0") return "dimension";
  return "number";
}

/**
 * Converts a CSS value to its Design Tokens `$value`.
 * @param {string} type The token type.
 * @param {string} value The CSS value.
 * @returns {unknown} The JSON value; `var(--x)` becomes an alias like `{color.palette.x}`.
 */
function valueOf(type, value) {
  const alias = value.match(/^var\((--[\w-]+)\)$/);
  if (alias) return `{${pathOf(alias[1]).join(".")}}`;
  if (type === "fontFamily") return value.split(",").map((f) => f.trim().replace(/"/g, ""));
  if (type === "fontWeight" || type === "number") return Number(value);
  if (type === "cubicBezier") return value.slice(13, -1).split(",").map(Number);
  if (type === "shadow") {
    return value.split(/,(?![^(]*\))/).map((layer) => {
      const [x, y, blur, ...color] = layer.trim().split(/\s+(?![^(]*\))/);
      return { offsetX: x, offsetY: y, blur, spread: "0", color: color.join(" ") };
    });
  }
  return value;
}

/**
 * Builds the tokens.json document from parsed CSS.
 * @param {ReturnType<typeof parseTokens>} parsed Declarations per block.
 * @returns {object} The Design Tokens tree.
 */
function buildJson(parsed) {
  const tree = {
    $description: "GovAssist design tokens v1. Generated from tokens.css by tokens.mjs; do not edit by hand.",
    breakpoint: {
      $type: "dimension",
      md: { $value: "768px" },
      lg: { $value: "1280px" },
    },
  };
  const set = (path, token) => {
    let node = tree;
    for (const seg of path.slice(0, -1)) node = node[seg] ??= {};
    node[path.at(-1)] = token;
  };
  const base = new Map(parsed.base);
  const resolve = (value) => {
    const alias = value.match(/^var\((--[\w-]+)\)$/);
    return alias ? resolve(base.get(alias[1])) : value;
  };
  for (const [name, value] of parsed.base) {
    const type = typeOf(name, resolve(value));
    set(pathOf(name), { $type: type, $value: valueOf(type, value) });
  }
  for (const [name, value] of parsed.dark) {
    set(pathOf(name, "dark"), { $type: "color", $value: valueOf("color", value) });
  }
  const seen = new Set();
  for (const [ctx, ext] of [["md", "govassist.md"], ["reducedMotion", "govassist.reducedMotion"], ["solidGlass", "govassist.solidGlass"]]) {
    for (const [name, value] of parsed[ctx]) {
      if (seen.has(`${ctx}${name}`)) continue; // the two solid-glass blocks repeat the same values
      seen.add(`${ctx}${name}`);
      const path = pathOf(name);
      let node = tree;
      for (const seg of path) node = node[seg];
      node.$extensions = { ...node.$extensions, [ext]: valueOf(node.$type, value) };
    }
  }
  return tree;
}

/**
 * Lists the prototype's CSS and HTML files.
 * @returns {string[]} Absolute file paths.
 */
function prototypeFiles() {
  return readdirSync(PROTOTYPE_DIR)
    .filter((f) => f.endsWith(".css") || f.endsWith(".html"))
    .map((f) => join(PROTOTYPE_DIR, f));
}

/**
 * Finds raw hex colors and undefined variables in the prototype.
 * @param {Set<string>} defined Every variable tokens.css declares.
 * @returns {string[]} Human-readable problems.
 */
function lintPrototype(defined) {
  const problems = [];
  for (const file of prototypeFiles()) {
    const text = readFileSync(file, "utf8");
    const styles = file.endsWith(".css")
      ? text
      : [...text.matchAll(/<style[^>]*>([\s\S]*?)<\/style>|style="([^"]*)"/g)].map((m) => m[1] ?? m[2]).join("\n");
    for (const hex of styles.matchAll(/#[0-9a-fA-F]{3,8}\b/g)) problems.push(`${file}: raw hex ${hex[0]}`);
    for (const fn of styles.matchAll(/\b(rgba?|hsla?)\(/g)) problems.push(`${file}: raw color ${fn[0]}`);
    // Raw lengths: only 1px (hairlines, .sr-only) and breakpoints inside @media are allowed.
    const withoutMedia = styles.replace(/@media[^{]*/g, "");
    for (const len of withoutMedia.matchAll(/(?<![\w-])-?(\d*\.?\d+)(rem|px)\b/g)) {
      if (len[1] !== "1" || len[2] !== "px") problems.push(`${file}: raw length ${len[0]}`);
    }
    const localVars = new Set([...styles.matchAll(/(--[\w-]+)\s*:/g)].map((m) => m[1]));
    for (const use of styles.matchAll(/var\((--[\w-]+)/g)) {
      if (!defined.has(use[1]) && !localVars.has(use[1])) problems.push(`${file}: undefined ${use[1]}`);
    }
  }
  return problems;
}

/**
 * Checks that every inline icon in the prototype is an unmodified Lucide icon from ./icons.
 * The Google mark (class "icon--brand") is the one allowed non-Lucide brand mark.
 * @returns {string[]} Human-readable problems.
 */
function lintIcons() {
  const iconDir = join(HERE, "icons");
  const inner = (svg) => svg.slice(svg.indexOf(">", svg.indexOf("<svg")) + 1, svg.lastIndexOf("</svg>"))
    .split("\n").map((l) => l.trim()).join("");
  const lucide = new Set(readdirSync(iconDir).filter((f) => f.endsWith(".svg")).map((f) => inner(readFileSync(join(iconDir, f), "utf8"))));
  const problems = [];
  for (const file of prototypeFiles().filter((f) => f.endsWith(".html"))) {
    for (const m of readFileSync(file, "utf8").matchAll(/<svg class="icon[^"]*"[^>]*>([\s\S]*?)<\/svg>/g)) {
      if (m[0].includes("icon--brand")) continue;
      if (!lucide.has(m[1])) problems.push(`${file}: icon is not an unmodified Lucide icon: ${m[1].slice(0, 60)}…`);
    }
  }
  return problems;
}

/** Entry point: write tokens.json, or check it and the prototype. */
function main() {
  const parsed = parseTokens(readFileSync(CSS_PATH, "utf8"));
  const json = `${JSON.stringify(buildJson(parsed), null, 2)}\n`;
  if (!process.argv.includes("--check")) {
    writeFileSync(JSON_PATH, json);
    console.log(`Wrote ${JSON_PATH}`);
    return;
  }
  const problems = [];
  if (readFileSync(JSON_PATH, "utf8") !== json) problems.push("tokens.json is out of date: run node docs/design/tokens.mjs");
  problems.push(...lintPrototype(new Set(parsed.base.map(([n]) => n))));
  problems.push(...lintIcons());
  for (const p of problems) console.error(p);
  console.log(problems.length ? `${problems.length} problem(s)` : "tokens OK, prototype OK");
  process.exit(problems.length ? 1 : 0);
}

main();
