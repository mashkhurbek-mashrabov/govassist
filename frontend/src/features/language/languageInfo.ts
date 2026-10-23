/** Per-language details shown by the language menu and cards (components.md → LanguageMenu, v1.2). */
import type { Lang } from "../../api/types";

/** What the UI shows for one language besides its native name (`lang.name.*`). */
export interface LanguageInfo {
  /** Short code in the language's own script; fixed width in the menu button. */
  code: string;
  /** Script hint under the two Uzbek variants (copy key), or `null`. */
  hintKey: string | null;
}

/** The four UI languages. Codes are design constants, not translatable copy. */
export const LANGUAGE_INFO: Record<Lang, LanguageInfo> = {
  "uz-Latn": { code: "UZ", hintKey: "lang.hint_latin" },
  "uz-Cyrl": { code: "ЎЗ", hintKey: "lang.hint_cyrillic" },
  ru: { code: "RU", hintKey: null },
  en: { code: "EN", hintKey: null },
};
