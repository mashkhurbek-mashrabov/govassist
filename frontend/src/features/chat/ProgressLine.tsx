import { useTranslation } from "react-i18next";
import type { Stage } from "../../api/types";
import { stageText } from "./stageText";

/** Props of {@link ProgressLine}. */
interface ProgressLineProps {
  stage: Stage | null;
  sourceCount: number | null;
}

/**
 * Visible progress line while an answer is being prepared. Screen readers get it from the live region.
 *
 * @param props Stage and source count.
 * @returns The progress line.
 */
export function ProgressLine({ stage, sourceCount }: ProgressLineProps) {
  const { t } = useTranslation();
  return (
    <p aria-hidden="true" className="italic">
      {stageText(stage, sourceCount, t)}
    </p>
  );
}
