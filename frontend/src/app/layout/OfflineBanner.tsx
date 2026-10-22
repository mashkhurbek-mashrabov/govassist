import { WifiOff } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useOnline } from "./useOnline";

/**
 * Full-width offline strip under the top bar (components.md → Banner).
 *
 * @returns The banner, or nothing when online.
 */
export function OfflineBanner() {
  const { t } = useTranslation();
  if (useOnline()) return null;
  return (
    <div className="banner" role="status">
      <WifiOff className="icon" aria-hidden="true" />
      <span>{t("chat_error.offline")}</span>
    </div>
  );
}
