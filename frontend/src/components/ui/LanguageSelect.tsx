import { Globe } from "lucide-react";
import { useId, type ChangeEvent } from "react";
import { useTranslation } from "react-i18next";
import type { Lang } from "../../api/types";
import { LANGUAGES } from "../../i18n";

/** Props of {@link LanguageSelect}. */
interface LanguageSelectProps {
  value: Lang;
  onChange: (lang: Lang) => void;
  /** `compact`: the header switch with a globe icon; `field`: a full-width select. */
  look?: "compact" | "field";
  /** Visible label for the field look. */
  label?: string;
}

/**
 * Native select of the four UI languages, each named in its own script.
 *
 * @param props Value, change callback and look.
 * @returns The select.
 */
export function LanguageSelect({ value, onChange, look = "compact", label }: LanguageSelectProps) {
  const { t } = useTranslation();
  const id = useId();
  const select = (
    <select
      className="select"
      id={id}
      value={value}
      onChange={(event: ChangeEvent<HTMLSelectElement>) => onChange(event.target.value as Lang)}
    >
      {LANGUAGES.map((lang) => (
        <option key={lang} value={lang} lang={lang}>
          {t(`lang.${lang}`)}
        </option>
      ))}
    </select>
  );
  if (look === "field") {
    return (
      <div className="field">
        <label className="sr-only" htmlFor={id}>
          {label ?? t("lang.label")}
        </label>
        {select}
      </div>
    );
  }
  return (
    <div className="lang-switch">
      <Globe className="icon" aria-hidden="true" />
      <label className="sr-only" htmlFor={id}>
        {t("lang.label")}
      </label>
      {select}
    </div>
  );
}
