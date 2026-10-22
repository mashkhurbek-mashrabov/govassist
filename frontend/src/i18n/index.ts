/** i18next setup. All four locales are bundled; `uz-Cyrl.json` is generated from `uz-Latn.json`. */
import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import type { Lang } from "../api/types";
import en from "./locales/en.json";
import ru from "./locales/ru.json";
import uzCyrl from "./locales/uz-Cyrl.json";
import uzLatn from "./locales/uz-Latn.json";

/** Supported UI languages, default first. */
export const LANGUAGES: readonly Lang[] = ["uz-Latn", "uz-Cyrl", "ru", "en"];
/** Default UI language. */
export const DEFAULT_LANGUAGE: Lang = "uz-Latn";
/** Language names in their own language (endonyms), shown in every UI language as-is. */
export const LANGUAGE_NAMES: Record<Lang, string> = {
  "uz-Latn": "Oʻzbekcha",
  "uz-Cyrl": "Ўзбекча",
  ru: "Русский",
  en: "English",
};
/** Options for language pickers, labelled by endonym. */
export const LANGUAGE_OPTIONS = LANGUAGES.map((lang) => ({ value: lang, label: LANGUAGE_NAMES[lang] }));
/** Pre-login language preference (a convenience only: not PII, not a token). */
const LANGUAGE_STORAGE_KEY = "govassist.lang";

/**
 * Type guard for supported languages.
 *
 * @param value Any string.
 * @returns Whether it is a `Lang`.
 */
export function isLang(value: unknown): value is Lang {
  return typeof value === "string" && (LANGUAGES as readonly string[]).includes(value);
}

/**
 * Language remembered from before login, else the default.
 *
 * @returns The initial language.
 */
function storedLanguage(): Lang {
  try {
    const stored = localStorage.getItem(LANGUAGE_STORAGE_KEY);
    return isLang(stored) ? stored : DEFAULT_LANGUAGE;
  } catch {
    // Storage can be blocked (private mode); the default language is a correct fallback.
    return DEFAULT_LANGUAGE;
  }
}

/**
 * Keep `<html lang>` and the stored preference in sync with the active language.
 *
 * @param lang The new language.
 */
function onLanguageChanged(lang: string): void {
  document.documentElement.lang = lang;
  try {
    localStorage.setItem(LANGUAGE_STORAGE_KEY, lang);
  } catch {
    // Not persisting the preference only costs a re-pick after reload.
  }
}

i18n.on("languageChanged", onLanguageChanged);

void i18n.use(initReactI18next).init({
  resources: {
    "uz-Latn": { translation: uzLatn },
    "uz-Cyrl": { translation: uzCyrl },
    ru: { translation: ru },
    en: { translation: en },
  },
  lng: storedLanguage(),
  fallbackLng: DEFAULT_LANGUAGE,
  supportedLngs: [...LANGUAGES],
  load: "currentOnly",
  interpolation: { escapeValue: false },
  returnNull: false,
});

export default i18n;
