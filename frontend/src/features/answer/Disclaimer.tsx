import { useTranslation } from "react-i18next";

/**
 * Static "not legal advice" note (UI text, never model output).
 *
 * @returns The disclaimer.
 */
export function Disclaimer() {
  const { t } = useTranslation();
  return <p className="text-sm">{t("answer.disclaimer")}</p>;
}
