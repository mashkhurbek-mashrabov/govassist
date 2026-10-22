import { Info } from "lucide-react";
import { useTranslation } from "react-i18next";

/**
 * Static "not legal advice" note under every answer (UI text, never model output).
 *
 * @returns The disclaimer.
 */
export function Disclaimer() {
  const { t } = useTranslation();
  return (
    <p className="disclaimer">
      <Info className="icon" aria-hidden="true" />
      <span>{t("app.disclaimer")}</span>
    </p>
  );
}
