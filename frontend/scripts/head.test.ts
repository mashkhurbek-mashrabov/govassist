import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

/** A path in the frontend package (Vitest runs from there). */
const root = (path: string) => resolve(process.cwd(), path);
const html = readFileSync(root("index.html"), "utf8");
const manifest = JSON.parse(readFileSync(root("public/manifest.webmanifest"), "utf8")) as {
  name: string;
  theme_color: string;
  background_color: string;
  icons: { src: string; sizes: string; purpose: string }[];
};
const tokens = readFileSync(root("src/styles/tokens.css"), "utf8");

/**
 * The value of a design token in tokens.css.
 *
 * @param name Token name without `--`.
 * @returns Its literal value.
 */
function token(name: string): string {
  return new RegExp(`--${name}:\\s*([^;]+);`).exec(tokens)?.[1]?.trim() ?? "";
}

/** The app head (components.md → Logo → Web app head) and the web manifest. */
describe("index.html and manifest", () => {
  it("links the ico fallback, the SVG favicon, the touch icon and the manifest", () => {
    expect(html).toContain('<link rel="icon" href="/favicon.ico" sizes="48x48" />');
    expect(html).toContain('<link rel="icon" type="image/svg+xml" href="/favicon.svg" />');
    expect(html).toContain('<link rel="apple-touch-icon" href="/apple-touch-icon.png" />');
    expect(html).toContain('<link rel="manifest" href="/manifest.webmanifest" />');
    for (const file of ["favicon.ico", "favicon.svg", "apple-touch-icon.png"]) {
      expect(existsSync(root(`public/${file}`))).toBe(true);
    }
  });

  it("lists the 192/512 icons and the maskable one, all present", () => {
    expect(manifest.name).toBe("GovAssist");
    expect(manifest.icons.map(({ src, sizes, purpose }) => `${src} ${sizes} ${purpose}`)).toEqual([
      "/icon-192.png 192x192 any",
      "/icon-512.png 512x512 any",
      "/icon-512-maskable.png 512x512 maskable",
    ]);
    for (const icon of manifest.icons) expect(existsSync(root(`public${icon.src}`))).toBe(true);
  });

  it("takes its colours from the design tokens (primary and white)", () => {
    expect(token("color-primary")).toBe("var(--palette-indigo-600)");
    expect(manifest.theme_color).toBe(token("palette-indigo-600"));
    expect(manifest.background_color).toBe(token("palette-white"));
  });
});
