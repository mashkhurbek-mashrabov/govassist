import { useId, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSendFeedback } from "../../api/queries";
import type { AssistantMessage, Feedback } from "../../api/types";
import { Alert } from "../../components/ui/Alert";

/** Contract limit for feedback comments. */
const MAX_COMMENT_LENGTH = 1000;

/** Props of {@link FeedbackBar}. */
interface FeedbackBarProps {
  conversationId: string;
  message: AssistantMessage;
}

/**
 * 👍/👎 with an optional comment, upserted per message. Shows the saved state.
 *
 * @param props Conversation id and the assistant message.
 * @returns The feedback bar.
 */
export function FeedbackBar({ conversationId, message }: FeedbackBarProps) {
  const { t } = useTranslation();
  const commentId = useId();
  const mutation = useSendFeedback();
  const [saved, setSaved] = useState<Feedback | null>(message.feedback);
  const [rating, setRating] = useState<Feedback["rating"] | null>(message.feedback?.rating ?? null);
  const [comment, setComment] = useState(message.feedback?.comment ?? "");

  /**
   * Save a rating (and the current comment).
   *
   * @param value 1 or -1.
   */
  const save = (value: Feedback["rating"]) => {
    setRating(value);
    mutation.mutate(
      { conversationId, messageId: message.id, feedback: { rating: value, comment } },
      { onSuccess: setSaved },
    );
  };

  return (
    <section aria-label={t("feedback.question")} className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <span>{t("feedback.question")}</span>
        <button
          type="button"
          className="min-h-11 min-w-11 border"
          aria-pressed={rating === 1}
          aria-label={t("feedback.helpful")}
          onClick={() => save(1)}
        >
          <span aria-hidden="true">👍</span>
        </button>
        <button
          type="button"
          className="min-h-11 min-w-11 border"
          aria-pressed={rating === -1}
          aria-label={t("feedback.notHelpful")}
          onClick={() => save(-1)}
        >
          <span aria-hidden="true">👎</span>
        </button>
      </div>
      {rating !== null && (
        <form
          className="flex flex-col gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            save(rating);
          }}
        >
          <label htmlFor={commentId}>{t("feedback.comment")}</label>
          <textarea
            id={commentId}
            className="border p-2"
            maxLength={MAX_COMMENT_LENGTH}
            value={comment}
            onChange={(event) => setComment(event.target.value)}
          />
          <button type="submit" className="min-h-11 border" disabled={mutation.isPending}>
            {t("feedback.submit")}
          </button>
        </form>
      )}
      {saved && !mutation.isPending && !mutation.isError && <Alert>{t("feedback.saved")}</Alert>}
      {mutation.isError && <Alert tone="error">{t("feedback.error")}</Alert>}
    </section>
  );
}
