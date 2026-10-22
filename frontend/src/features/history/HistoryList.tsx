import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, NavLink, useNavigate, useParams } from "react-router";
import { useConversations, useDeleteConversation } from "../../api/queries";
import type { ConversationSummary, Lang } from "../../api/types";
import { Alert } from "../../components/ui/Alert";
import { ConfirmDialog } from "../../components/ui/ConfirmDialog";
import { formatDate } from "../../lib/format";
import { conversationLabel } from "./conversationLabel";

/**
 * Conversation history: newest first, "Load more" for the next cursor page, delete with confirmation.
 * A sidebar on wide screens and the `/history` page on phones.
 *
 * @returns The list.
 */
export function HistoryList() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { conversationId } = useParams();
  const conversations = useConversations();
  const deletion = useDeleteConversation();
  const [pendingDelete, setPendingDelete] = useState<ConversationSummary | null>(null);
  const items = conversations.data?.pages.flatMap((page) => page.results) ?? [];

  /** Delete the confirmed conversation; leave its page if it is open. */
  const confirmDelete = () => {
    if (!pendingDelete) return;
    const { id } = pendingDelete;
    deletion.mutate(id, {
      onSuccess: () => {
        setPendingDelete(null);
        if (id === conversationId) void navigate("/");
      },
    });
  };

  return (
    <div className="flex flex-col gap-3">
      <h2 className="font-bold">{t("history.title")}</h2>
      <Link to="/" className="min-h-11 border p-2">
        {t("nav.newChat")}
      </Link>
      {conversations.isError && <Alert tone="error">{t("history.error")}</Alert>}
      {conversations.isSuccess && items.length === 0 && <p>{t("history.empty")}</p>}
      <ul className="flex flex-col gap-2">
        {items.map((item) => (
          <li key={item.id} className="flex items-start gap-2">
            <NavLink to={`/c/${item.id}`} className="flex min-h-11 grow flex-col">
              <span>{conversationLabel(item)}</span>
              <span className="text-sm">{item.last_message_preview}</span>
              <span className="text-sm">{formatDate(item.updated_at, i18n.language as Lang)}</span>
            </NavLink>
            <button
              type="button"
              className="min-h-11 min-w-11"
              aria-label={t("history.delete", { title: conversationLabel(item) })}
              onClick={() => setPendingDelete(item)}
            >
              ✕
            </button>
          </li>
        ))}
      </ul>
      {conversations.hasNextPage && (
        <button
          type="button"
          className="min-h-11 border"
          disabled={conversations.isFetchingNextPage}
          onClick={() => void conversations.fetchNextPage()}
        >
          {t("history.loadMore")}
        </button>
      )}
      <ConfirmDialog
        open={pendingDelete !== null}
        title={t("history.deleteConfirmTitle")}
        body={t("history.deleteConfirmBody", {
          title: pendingDelete ? conversationLabel(pendingDelete) : "",
        })}
        confirmLabel={t("common.delete")}
        pending={deletion.isPending}
        onConfirm={confirmDelete}
        onCancel={() => setPendingDelete(null)}
      />
    </div>
  );
}
