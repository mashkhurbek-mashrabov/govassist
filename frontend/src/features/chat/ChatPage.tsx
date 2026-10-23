import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router";
import { ApiError } from "../../api/http";
import { useConversation } from "../../api/queries";
import { Alert } from "../../components/ui/Alert";
import { takePendingQuestion } from "../../lib/pendingQuestion";
import { useChatContext } from "./chatContext";
import { AssistantMessage } from "./AssistantMessage";
import { Composer } from "./Composer";
import { EmptyChat } from "./EmptyChat";
import { useInputBlocked } from "./useInputBlocked";
import { UserMessage } from "./UserMessage";
import { settleStaleStreaming } from "./streamingMessages";
import { retryableQuestion, visibleMessages } from "./visibleMessages";

/**
 * New chat (`/`) or a conversation (`/c/:id`): the thread (stored messages + the live turn) and the composer.
 *
 * @returns The page.
 */
export function ChatPage() {
  const { t } = useTranslation();
  const { conversationId = null } = useParams();
  const { turn, send, resend, stop, retry } = useChatContext();
  const streaming = turn?.isStreaming ?? false;
  const conversation = useConversation(conversationId, !streaming);
  const blocked = useInputBlocked(turn);
  // A `streaming` row older than the backend's stream lock is shown as stopped, with Retry.
  const stored = settleStaleStreaming(conversation.data?.messages ?? [], conversation.dataUpdatedAt);
  const { messages, showTurn } = visibleMessages(stored, turn);
  const lastAssistantId = messages.findLast((message) => message.role === "assistant")?.id;
  const retryText = showTurn || streaming ? null : retryableQuestion(messages);
  const notFound = conversation.error instanceof ApiError && conversation.error.status === 404;
  const isNew = conversationId === null && !turn;
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // A question carried from the landing (sessionStorage) becomes the first question of a new chat, once.
  useEffect(() => {
    if (!isNew) return;
    const carried = takePendingQuestion();
    if (carried) send(carried, null);
  }, [isNew, send]);

  /**
   * Ask a question in this conversation.
   *
   * @param text Question text.
   */
  const ask = (text: string) => {
    send(text, conversationId);
    // Focus stays in the question box after sending, also from a chip (components.md → InputBar).
    inputRef.current?.focus();
  };

  // One flat list keyed by message id: when the live turn's stored copy arrives it takes the same key and
  // React keeps the DOM (no lost focus or clicks right after `final`).
  const threadItems = [
    ...(conversationId
      ? messages.map((message) =>
          message.role === "user" ? (
            <UserMessage key={message.id} text={message.text} />
          ) : (
            <AssistantMessage
              key={message.id}
              source={{ kind: "stored", message }}
              conversationId={conversationId}
              onAsk={!showTurn && !streaming && message.id === lastAssistantId ? ask : undefined}
              onRetry={
                retryText !== null && message.id === lastAssistantId
                  ? () => resend(retryText, conversationId)
                  : undefined
              }
            />
          ),
        )
      : []),
    ...(showTurn && turn
      ? [
          <UserMessage key={turn.userMessageId ?? "live-user"} text={turn.text} />,
          <AssistantMessage
            key={turn.assistantMessageId ?? "live-assistant"}
            source={{ kind: "live", turn }}
            conversationId={turn.conversationId}
            onAsk={ask}
            onRetry={retry}
          />,
        ]
      : []),
  ];

  return (
    <>
      <main className="page page--chat" id="main">
        {isNew ? (
          <EmptyChat onAsk={ask} />
        ) : (
          <>
            <h1 className="sr-only">{conversation.data?.title || t("chat.new")}</h1>
            {conversation.isError && (
              <Alert tone="danger">{t(notFound ? "notfound.title" : "error.server")}</Alert>
            )}
            <ol className="thread">{threadItems}</ol>
          </>
        )}
      </main>
      <Composer streaming={streaming} blocked={blocked} onSend={ask} onStop={stop} inputRef={inputRef} />
    </>
  );
}
