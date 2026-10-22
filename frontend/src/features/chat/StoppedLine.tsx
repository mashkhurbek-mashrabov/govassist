import { Square } from "lucide-react";
import { useTranslation } from "react-i18next";

/**
 * The line after the user pressed Stop: the partial cards stay for this view only.
 *
 * @returns The stopped line.
 */
export function StoppedLine() {
  const { t } = useTranslation();
  return (
    <p className="progress progress--done" role="status">
      <Square className="icon" aria-hidden="true" />
      <span>
        {t("progress.stopped")} {t("progress.stopped_hint")}
      </span>
    </p>
  );
}
