/** Merge stored messages with the live turn without showing anything twice. */
import type { Message } from "../../api/types";
import type { LiveTurn } from "./useChatStream";

/** What the chat page renders. */
export interface VisibleChat {
  messages: Message[];
  showTurn: boolean;
}

/**
 * Decide which copy of the latest exchange to show.
 * A cleanly finished turn yields to the stored copy once it is fetched (it has the saved feedback);
 * otherwise the live turn wins, because it carries the stop/retry state.
 *
 * @param messages Stored messages of the conversation.
 * @param turn The live turn, or `null`.
 * @returns Messages to render and whether to render the live turn after them.
 */
export function visibleMessages(messages: Message[], turn: LiveTurn | null): VisibleChat {
  if (!turn) return { messages, showTurn: false };
  const finishedCleanly = !turn.isStreaming && !turn.failure && turn.finalMessage !== null;
  if (finishedCleanly && messages.some((message) => message.id === turn.assistantMessageId)) {
    return { messages, showTurn: false };
  }
  const liveIds = new Set([turn.userMessageId, turn.assistantMessageId]);
  return { messages: messages.filter((message) => !liveIds.has(message.id)), showTurn: true };
}

/**
 * The question to resend when the latest stored answer failed (e.g. stopped, then the page reloaded).
 *
 * @param messages Stored messages, oldest first.
 * @returns The user text before the latest assistant message when that message failed, else `null`.
 */
export function retryableQuestion(messages: Message[]): string | null {
  const last = messages.at(-1);
  const question = messages.at(-2);
  if (last?.role !== "assistant" || last.status !== "failed" || question?.role !== "user") return null;
  return question.text;
}
