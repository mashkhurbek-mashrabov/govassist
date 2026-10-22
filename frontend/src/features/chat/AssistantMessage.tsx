import { useTranslation } from "react-i18next";
import { useMe } from "../../app/layout/meContext";
import { AnswerView } from "../answer/AnswerView";
import { assistantView, type AssistantSource } from "./assistantView";
import { FailureAlert } from "./FailureAlert";
import { FeedbackBar } from "./FeedbackBar";
import { ProgressLine } from "./ProgressLine";
import { StoppedLine } from "./StoppedLine";

/** Props of {@link AssistantMessage}. */
interface AssistantMessageProps {
  source: AssistantSource;
  conversationId: string | null;
  /** Only the latest answer offers follow-up questions. */
  onAsk?: ((question: string) => void) | undefined;
  /** Retry for a failed or stopped answer. */
  onRetry?: (() => void) | undefined;
}

/**
 * An assistant thread item (components.md → AssistantMessage), for the live turn and stored messages alike.
 * Keyed by message id in the thread, so the live copy turns into the stored one without remounting
 * (no lost focus or clicks right after `final`).
 *
 * @param props Source, conversation id, ask and retry callbacks.
 * @returns The thread item.
 */
export function AssistantMessage({ source, conversationId, onAsk, onRetry }: AssistantMessageProps) {
  const { t } = useTranslation();
  const me = useMe();
  const view = assistantView(source, me.quota.hour_limit);
  const showAnswer = (view.answer !== null || view.office !== null) && view.failure === null;
  return (
    <li className="assistant" lang={view.lang}>
      <p className="sr-only">{t("chat.assistant")}:</p>
      {view.progress && <ProgressLine stage={view.progress.stage} sourceCount={view.progress.sourceCount} />}
      {showAnswer && (
        // aria-busy only around the growing answer: the progress line above stays a live status region.
        <div className="assistant__answer" aria-busy={view.streaming}>
          <AnswerView
            answer={view.answer ?? {}}
            sources={view.sources}
            office={view.office}
            messageId={view.messageId}
            streaming={view.streaming}
            complete={view.complete}
            feedback={
              view.final &&
              conversationId && <FeedbackBar conversationId={conversationId} message={view.final} />
            }
            onAsk={onAsk}
          />
        </div>
      )}
      {source.kind === "live" && (
        <p className="sr-only" role="status">
          {view.final?.answer?.summary ?? ""}
        </p>
      )}
      {view.stopped && <StoppedLine />}
      {view.failure && <FailureAlert message={view.failure} onRetry={onRetry} />}
    </li>
  );
}
