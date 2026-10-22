import { useTranslation } from "react-i18next";
import type { AssistantMessage } from "../../api/types";
import { Alert } from "../../components/ui/Alert";
import { AnswerView } from "../answer/AnswerView";
import { FailureAlert } from "./FailureAlert";
import { storedFailureMessage } from "./failureMessage";
import { FeedbackBar } from "./FeedbackBar";

/** Props of {@link AssistantMessageView}. */
interface AssistantMessageViewProps {
  message: AssistantMessage;
  conversationId: string;
  /** Only the latest answer offers follow-up questions. */
  onAsk?: ((question: string) => void) | undefined;
  /** Only the latest failed answer offers Retry. */
  onRetry?: (() => void) | undefined;
}

/**
 * A stored assistant message: the answer card with feedback, a failed notice ("Answer stopped" or the
 * error copy for its `error_code`), or a still-writing notice.
 *
 * @param props Message, conversation id, optional ask and retry callbacks.
 * @returns The message.
 */
export function AssistantMessageView({ message, conversationId, onAsk, onRetry }: AssistantMessageViewProps) {
  const { t } = useTranslation();
  if (message.status === "streaming") return <Alert>{t("chat.streamingElsewhere")}</Alert>;
  if (message.status === "failed" || !message.answer) {
    return (
      <FailureAlert
        message={storedFailureMessage(message.error_code)}
        tone={message.error_code === "stopped" ? "info" : "error"}
        onRetry={onRetry}
      />
    );
  }
  return (
    <AnswerView
      answer={message.answer}
      sources={message.sources}
      office={message.office}
      messageId={message.id}
      streaming={false}
      feedback={<FeedbackBar conversationId={conversationId} message={message} />}
      onAsk={onAsk}
    />
  );
}
