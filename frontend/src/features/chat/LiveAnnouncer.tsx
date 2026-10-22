import { useTranslation } from "react-i18next";
import { stageText } from "./stageText";
import type { LiveTurn } from "./useChatStream";

/** Props of {@link LiveAnnouncer}. */
interface LiveAnnouncerProps {
  turn: LiveTurn | null;
}

/**
 * Polite live region: announces stage changes and the final summary, never individual deltas.
 *
 * @param props The live turn.
 * @returns A visually hidden live region.
 */
export function LiveAnnouncer({ turn }: LiveAnnouncerProps) {
  const { t } = useTranslation();
  let text = "";
  if (turn?.finalMessage) text = turn.finalMessage.answer?.summary ?? "";
  else if (turn?.isStreaming) text = stageText(turn.stage, turn.sourceCount, t);
  return (
    <div aria-live="polite" className="sr-only">
      {text}
    </div>
  );
}
