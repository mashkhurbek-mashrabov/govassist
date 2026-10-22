import { useTranslation } from "react-i18next";
import { useMatches, useParams } from "react-router";
import { useConversation } from "../../api/queries";

/** Route `handle` used for the top-bar title. */
export interface RouteHandle {
  titleKey?: string;
}

/**
 * Title shown in the top bar: the conversation's title in a chat, else the route's title, else "New chat".
 *
 * @returns The translated title.
 */
export function useTopbarTitle(): string {
  const { t } = useTranslation();
  const matches = useMatches();
  const { conversationId } = useParams();
  const conversation = useConversation(conversationId ?? null);
  if (conversationId) return conversation.data?.title || t("chat.new");
  const titleKey = matches
    .map((match) => (match.handle as RouteHandle | undefined)?.titleKey)
    .findLast((key) => key !== undefined);
  return t(titleKey ?? "chat.new");
}
