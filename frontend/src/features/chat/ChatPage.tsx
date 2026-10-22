import { useTranslation } from "react-i18next";
import { useParams } from "react-router";
import { ApiError } from "../../api/http";
import { useConversation } from "../../api/queries";
import { Alert } from "../../components/ui/Alert";
import { AssistantMessageView } from "./AssistantMessageView";
import { useChatContext } from "./chatContext";
import { EmptyChat } from "./EmptyChat";
import { InputBar } from "./InputBar";
import { LiveAnnouncer } from "./LiveAnnouncer";
import { LiveTurnView } from "./LiveTurnView";
import { UserBubble } from "./UserBubble";
import { visibleMessages } from "./visibleMessages";

/**
 * New chat (`/`) or an existing conversation (`/c/:id`): stored messages, the live turn, the input bar.
 *
 * @returns The page.
 */
export function ChatPage() {
  const { t } = useTranslation();
  const { conversationId = null } = useParams();
  const { turn, send, stop, retry } = useChatContext();
  const conversation = useConversation(conversationId);
  const { messages, showTurn } = visibleMessages(conversation.data?.messages ?? [], turn);
  const streaming = turn?.isStreaming ?? false;
  const lastAssistantId = messages.findLast((message) => message.role === "assistant")?.id;
  const notFound = conversation.error instanceof ApiError && conversation.error.status === 404;

  /**
   * Ask a question in this conversation.
   *
   * @param text Question text.
   */
  const ask = (text: string) => send(text, conversationId);

  return (
    <div className="mx-auto flex w-full max-w-3xl grow flex-col gap-4">
      <h1 className="sr-only">{conversation.data?.title ?? t("nav.newChat")}</h1>
      <LiveAnnouncer turn={turn} />
      {conversationId === null && !turn && <EmptyChat onAsk={ask} />}
      {conversation.isError && <Alert tone="error">{t(notFound ? "chat.notFound" : "chat.loadError")}</Alert>}
      {conversationId &&
        messages.map((message) =>
          message.role === "user" ? (
            <UserBubble key={message.id} text={message.text} />
          ) : (
            <AssistantMessageView
              key={message.id}
              message={message}
              conversationId={conversationId}
              onAsk={!showTurn && !streaming && message.id === lastAssistantId ? ask : undefined}
            />
          ),
        )}
      {showTurn && turn && <LiveTurnView turn={turn} onRetry={retry} onAsk={ask} />}
      <InputBar streaming={streaming} onSend={ask} onStop={stop} />
    </div>
  );
}
