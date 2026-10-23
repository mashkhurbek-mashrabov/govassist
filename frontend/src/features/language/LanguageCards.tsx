import { Check } from "lucide-react";
import { useId } from "react";
import { useTranslation } from "react-i18next";
import type { Lang } from "../../api/types";
import { LANGUAGES } from "../../i18n";
import { LANGUAGE_INFO } from "./languageInfo";

/** Props of {@link LanguageCards}. */
interface LanguageCardsProps {
  value: Lang;
  onChange: (lang: Lang) => void;
  /** Visually hidden legend (defaults to "Til"). */
  legend?: string;
}

/**
 * Large radio cards for choosing the UI language (onboarding step 1, Settings → App language). Native radios
 * keep focus and arrow-key behaviour; each card shows the native name, the script hint and the code.
 *
 * @param props Current language, change callback and legend.
 * @returns The fieldset.
 */
export function LanguageCards({ value, onChange, legend }: LanguageCardsProps) {
  const { t } = useTranslation();
  const name = useId();
  return (
    <fieldset className="lang-cards lang-cards--grid">
      <legend className="sr-only">{legend ?? t("lang.label")}</legend>
      {LANGUAGES.map((lang) => {
        const { code, hintKey } = LANGUAGE_INFO[lang];
        return (
          <label key={lang} className="lang-card">
            <input
              type="radio"
              name={name}
              value={lang}
              checked={value === lang}
              onChange={() => onChange(lang)}
            />
            <span>
              <span className="lang-card__name" lang={lang}>
                {t(`lang.name.${lang}`)}
              </span>
              {hintKey && <span className="lang-card__hint">{t(hintKey)}</span>}
            </span>
            <span className="lang-card__end">
              <span className="lang-tag" aria-hidden="true">
                {code}
              </span>
              <span className="lang-card__check" aria-hidden="true">
                <Check className="icon" aria-hidden="true" />
              </span>
            </span>
          </label>
        );
      })}
    </fieldset>
  );
}
