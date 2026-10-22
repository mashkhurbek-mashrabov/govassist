import { useEffect, useRef } from "react";
import { Outlet, useNavigate, useParams } from "react-router";
import { useChatStream, type ChatStream } from "./useChatStream";

/**
 * Forget the live turn when the user moves to another conversation or a new chat.
 * Runs only on route changes, so the `meta` → `/c/:id` navigation of a new chat keeps the stream.
 *
 * @param stream The chat stream.
 * @param conversationId Conversation in the URL, or `null` on `/`.
 */
function useResetOnConversationChange(stream: ChatStream, conversationId: string | null): void {
  const previous = useRef(conversationId);
  const { turn, reset } = stream;
  useEffect(() => {
    if (previous.current === conversationId) return;
    previous.current = conversationId;
    if (turn && turn.conversationId !== conversationId) reset();
  }, [conversationId, turn, reset]);
}

/**
 * Owns the chat stream for `/` and `/c/:id`, so moving from a new chat to its URL does not remount the stream.
 *
 * @returns The layout.
 */
export function ChatLayout() {
  const navigate = useNavigate();
  const { conversationId = null } = useParams();
  const stream = useChatStream({
    onConversationStarted: (id) => void navigate(`/c/${id}`, { replace: true }),
  });
  useResetOnConversationChange(stream, conversationId);
  return <Outlet context={stream} />;
}
