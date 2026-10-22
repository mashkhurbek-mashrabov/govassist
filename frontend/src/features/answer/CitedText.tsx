import type { DeepPartialItem } from "./answerTypes";
import { CitationBadges } from "./CitationBadges";

/** Props of {@link CitedText}. */
interface CitedTextProps {
  item: DeepPartialItem;
  index: Map<string, number>;
  messageId: string;
  /** Show the typing caret (the item still growing). */
  typing?: boolean;
}

/**
 * Plain-text statement followed by its citation badges.
 *
 * @param props The (possibly partial) item, numbering, message id and caret flag.
 * @returns The text and badges.
 */
export function CitedText({ item, index, messageId, typing }: CitedTextProps) {
  return (
    <>
      <span className={typing ? "typing" : undefined}>{item.text ?? ""}</span>
      <CitationBadges sourceIds={item.source_ids} index={index} messageId={messageId} />
    </>
  );
}
