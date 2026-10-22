import { Trash2 } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import type { ConversationSummary } from "../../api/types";
import { IconButton } from "../../components/ui/IconButton";
import { relativeDay } from "../../lib/format";
import { conversationLabel } from "./conversationLabel";

/** Props of {@link HistoryItem}. */
interface HistoryItemProps {
  item: ConversationSummary;
  current: boolean;
  deleting: boolean;
  onDelete: (item: ConversationSummary) => void;
  /** Injected for tests; defaults to now. */
  now?: Date;
}

/**
 * One history row: title, date + last question, and a delete button.
 *
 * @param props The conversation, whether it is open, delete state and callback.
 * @returns The row.
 */
export function HistoryItem({ item, current, deleting, onDelete, now = new Date() }: HistoryItemProps) {
  const { t } = useTranslation();
  const day = relativeDay(item.updated_at, now);
  const date = day.kind === "date" ? day.text : t(day.kind === "today" ? "common.today" : "common.yesterday");
  const label = conversationLabel(item);
  return (
    <li className={deleting ? "history__item is-deleting" : "history__item"}>
      <Link className="history__link" to={`/c/${item.id}`} aria-current={current ? "page" : undefined}>
        <span className="history__title">{label}</span>
        <span className="history__preview">
          <span className="history__date">{date}</span> · {item.last_message_preview}
        </span>
      </Link>
      <IconButton
        label={t("history.delete_named", { title: label })}
        icon={<Trash2 className="icon" aria-hidden="true" />}
        disabled={deleting}
        onClick={() => onDelete(item)}
      />
    </li>
  );
}
