import type { ConversationSummary } from "../../api/types";

/**
 * Visible name of a history item. The contract guarantees a title; the preview keeps the link named anyway.
 *
 * @param item History item.
 * @returns Title, else the last question.
 */
export function conversationLabel(item: ConversationSummary): string {
  return item.title || item.last_message_preview;
}
