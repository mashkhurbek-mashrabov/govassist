import type { DeepPartialItem } from "./answerTypes";
import { CitationBadges } from "./CitationBadges";

/** Props of {@link CitedItem}. */
interface CitedItemProps {
  item: DeepPartialItem;
  index: Map<string, number>;
  messageId: string;
}

/**
 * Plain-text item followed by its citation badges.
 *
 * @param props The (possibly partial) item, numbering and message id.
 * @returns The text and badges.
 */
export function CitedItem({ item, index, messageId }: CitedItemProps) {
  return (
    <>
      {item.text ?? ""}
      <CitationBadges sourceIds={item.source_ids} index={index} messageId={messageId} />
    </>
  );
}
