import { MessageSquare, SquarePen } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router";
import { useConversations, useDeleteConversation } from "../../api/queries";
import type { ConversationSummary } from "../../api/types";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { CenterState } from "../../components/ui/CenterState";
import { ConfirmDialog } from "../../components/ui/ConfirmDialog";
import { LinkButton } from "../../components/ui/LinkButton";
import { Skeleton } from "../../components/ui/Skeleton";
import { useToast } from "../../components/ui/toastContext";
import { conversationLabel } from "./conversationLabel";
import { HistoryItem } from "./HistoryItem";

/** Props of {@link HistoryList}. */
interface HistoryListProps {
  /** `sidebar`: compact list + "Show more" link; `page`: the full /history page body. */
  variant: "sidebar" | "page";
}

/**
 * Conversation history (screen 13): rows, cursor "Show more", delete with confirmation and a toast.
 *
 * @param props Where it is shown.
 * @returns The list.
 */
export function HistoryList({ variant }: HistoryListProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const showToast = useToast();
  const { conversationId } = useParams();
  const conversations = useConversations();
  const deletion = useDeleteConversation();
  const [pending, setPending] = useState<ConversationSummary | null>(null);
  const items = conversations.data?.pages.flatMap((page) => page.results) ?? [];
  const isPage = variant === "page";

  /** Delete the confirmed conversation; leave its page if it is open. */
  const confirmDelete = () => {
    if (!pending) return;
    const { id } = pending;
    deletion.mutate(id, {
      onSuccess: () => {
        setPending(null);
        showToast(t("history.deleted"));
        if (id === conversationId) void navigate("/");
      },
    });
  };

  if (conversations.isPending) {
    return isPage ? (
      <div role="status">
        <p className="sr-only">{t("common.loading")}</p>
        {[0, 1, 2].map((row) => (
          <div key={row} className="card" aria-hidden="true">
            <Skeleton width="60" />
            <Skeleton />
          </div>
        ))}
      </div>
    ) : null;
  }
  if (conversations.isError) return <Alert tone="danger">{t("error.server")}</Alert>;
  if (items.length === 0) {
    return isPage ? (
      <CenterState
        icon={<MessageSquare className="icon" aria-hidden="true" />}
        title={t("history.empty_title")}
        level={2}
      >
        <p className="t-muted">{t("history.empty_lead")}</p>
        <LinkButton variant="primary" to="/" icon={<SquarePen className="icon" aria-hidden="true" />}>
          {t("chat.new")}
        </LinkButton>
      </CenterState>
    ) : null;
  }

  return (
    <>
      <ul className="history">
        {items.map((item) => (
          <HistoryItem
            key={item.id}
            item={item}
            current={item.id === conversationId}
            deleting={deletion.isPending && deletion.variables === item.id}
            onDelete={setPending}
          />
        ))}
      </ul>
      {isPage && <p className="t-small t-muted">{t("history.pii_note")}</p>}
      {isPage && conversations.hasNextPage && (
        <Button
          variant="ghost"
          busy={conversations.isFetchingNextPage}
          onClick={() => void conversations.fetchNextPage()}
        >
          {t("history.load_more")}
        </Button>
      )}
      {!isPage && (
        <Link className="nav-link t-small" to="/history">
          {t("history.load_more")}
        </Link>
      )}
      <ConfirmDialog
        open={pending !== null}
        title={t("history.confirm_title")}
        body={t("history.confirm_body", { title: pending ? conversationLabel(pending) : "" })}
        confirmLabel={t("history.delete")}
        busy={deletion.isPending}
        busyLabel={t("history.deleting")}
        onConfirm={confirmDelete}
        onCancel={() => setPending(null)}
      />
    </>
  );
}
