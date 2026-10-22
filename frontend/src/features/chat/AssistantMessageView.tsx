import { useTranslation } from "react-i18next";
import type { AssistantMessage } from "../../api/types";
import { Alert } from "../../components/ui/Alert";
import { AnswerView } from "../answer/AnswerView";
import { FeedbackBar } from "./FeedbackBar";

/** Props of {@link AssistantMessageView}. */
interface AssistantMessageViewProps {
  message: AssistantMessage;
  conversationId: string;
  /** Only the latest answer offers follow-up questions. */
  onAsk?: ((question: string) => void) | undefined;
}

/**
 * A stored assistant message: the answer card with feedback, or a failed / still-writing notice.
 *
 * @param props Message, conversation id and optional ask callback.
 * @returns The message.
 */
export function AssistantMessageView({ message, conversationId, onAsk }: AssistantMessageViewProps) {
  const { t } = useTranslation();
  if (message.status === "streaming") return <Alert>{t("chat.streamingElsewhere")}</Alert>;
  if (message.status === "failed" || !message.answer)
    return <Alert tone="error">{t("chat.failedMessage")}</Alert>;
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
