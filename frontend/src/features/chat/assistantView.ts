/** One shape for a stored assistant message and the live turn, so both render through the same tree. */
import type { AssistantMessage, Lang, OfficeMatch, Source, Stage } from "../../api/types";
import type { PartialAnswer } from "../answer/answerTypes";
import { failureMessage, storedFailureMessage, type FailureMessage } from "./failureMessage";
import type { LiveTurn } from "./useChatStream";

/** Where an assistant message comes from. */
export type AssistantSource =
  { kind: "stored"; message: AssistantMessage } | { kind: "live"; turn: LiveTurn };

/** Everything the assistant thread item renders. */
export interface AssistantView {
  messageId: string;
  answer: PartialAnswer | null;
  sources: Source[];
  office: OfficeMatch | null;
  streaming: boolean;
  complete: boolean;
  /** Progress line, or `null` when not preparing. */
  progress: { stage: Stage | null; sourceCount: number | null } | null;
  failure: FailureMessage | null;
  stopped: boolean;
  /** The saved message once final (for feedback). */
  final: AssistantMessage | null;
  lang: Lang | undefined;
}

/**
 * Derive what to render.
 *
 * @param source Stored message or live turn.
 * @param hourLimit `Me.quota.hour_limit` (rate-limit copy).
 * @returns The view.
 */
export function assistantView(source: AssistantSource, hourLimit: number): AssistantView {
  if (source.kind === "stored") {
    const { message } = source;
    const complete = message.status === "complete" && message.answer !== null;
    return {
      messageId: message.id,
      answer: message.answer,
      sources: message.sources,
      office: message.office,
      streaming: false,
      complete,
      progress: message.status === "streaming" ? { stage: "writing", sourceCount: null } : null,
      failure: message.status === "failed" ? storedFailureMessage(message.error_code, hourLimit) : null,
      stopped: false,
      final: complete ? message : null,
      lang: message.answer?.language,
    };
  }
  const { turn } = source;
  const { finalMessage, failure } = turn;
  const answer = finalMessage?.answer ?? turn.partialAnswer;
  return {
    messageId: turn.assistantMessageId ?? "live",
    answer,
    sources: finalMessage?.sources ?? [],
    office: turn.office,
    streaming: turn.isStreaming,
    complete: finalMessage !== null,
    progress: turn.isStreaming ? { stage: turn.stage, sourceCount: turn.sourceCount } : null,
    failure: failure && failure.kind !== "stopped" ? failureMessage(failure, hourLimit) : null,
    stopped: failure?.kind === "stopped",
    final: finalMessage,
    lang: answer?.language,
  };
}
