import { describe, expect, it } from "vitest";
import { transliterateTree, type LocaleTree } from "../../scripts/translit-uz";
import en from "./locales/en.json";
import ru from "./locales/ru.json";
import uzCyrl from "./locales/uz-Cyrl.json";
import uzLatn from "./locales/uz-Latn.json";

/**
 * Flatten a locale tree to sorted dotted keys.
 *
 * @param tree Locale messages.
 * @param prefix Key prefix for recursion.
 * @returns Sorted keys such as `chat.input.send`.
 */
function keys(tree: LocaleTree, prefix = ""): string[] {
  return Object.entries(tree)
    .flatMap(([key, value]) =>
      typeof value === "string" ? [`${prefix}${key}`] : keys(value, `${prefix}${key}.`),
    )
    .sort();
}

/** The four locale files stay in lockstep (AGENTS.md → i18n). */
describe("locales", () => {
  const reference = keys(uzLatn);

  it.each([
    ["en", en],
    ["ru", ru],
    ["uz-Cyrl", uzCyrl],
  ])("%s has exactly the uz-Latn keys", (_name, locale) => {
    expect(keys(locale)).toEqual(reference);
  });

  it("uz-Cyrl is the committed output of the transliteration script", () => {
    expect(uzCyrl).toEqual(transliterateTree(uzLatn));
  });

  it("has no empty messages", () => {
    for (const locale of [uzLatn, uzCyrl, ru, en] as LocaleTree[]) {
      const values = JSON.stringify(locale);
      expect(values).not.toContain('""');
    }
  });
});
