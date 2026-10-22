import { useTranslation } from "react-i18next";
import { SelectField } from "../../components/ui/SelectField";
import { LANGUAGE_OPTIONS } from "../../i18n";

/**
 * Pre-login language picker. Signed-in users change language in Settings (saved to the profile).
 *
 * @returns The picker.
 */
export function LanguageSwitcher() {
  const { t, i18n } = useTranslation();
  return (
    <SelectField
      label={t("profile.language")}
      options={LANGUAGE_OPTIONS}
      value={i18n.language}
      onChange={(event) => void i18n.changeLanguage(event.target.value)}
    />
  );
}
