import { Check } from "lucide-react";
import { useTranslation } from "react-i18next";
import type { Stage } from "../../api/types";

/** Props of {@link ProgressLine}. */
interface ProgressLineProps {
  stage: Stage | null;
  sourceCount: number | null;
}

/**
 * Stage line while an answer is prepared (components.md → ProgressLine). A polite live region: it announces
 * stage changes, never individual deltas. The found count stays once known.
 *
 * @param props Stage and source count.
 * @returns The line.
 */
export function ProgressLine({ stage, sourceCount }: ProgressLineProps) {
  const { t } = useTranslation();
  const found = sourceCount !== null && stage !== "searching";
  return (
    <p className="progress" role="status" aria-live="polite">
      <span className="progress__dots" aria-hidden="true">
        <span />
        <span />
        <span />
      </span>
      {found && (
        <span className="progress__found">
          <Check className="icon" aria-hidden="true" />
          {t("progress.found", { count: sourceCount })}
        </span>
      )}
      {(stage === null || stage === "searching") && <span>{t("progress.searching")}</span>}
      {stage === "writing" && <span>· {t("progress.writing")}</span>}
    </p>
  );
}
