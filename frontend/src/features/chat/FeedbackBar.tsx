import { Check, ThumbsDown, ThumbsUp } from "lucide-react";
import { useId, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSendFeedback } from "../../api/queries";
import type { AssistantMessage, Feedback } from "../../api/types";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { IconButton } from "../../components/ui/IconButton";

/** Contract limit for feedback comments. */
const MAX_COMMENT_LENGTH = 1000;

/** Props of {@link FeedbackBar}. */
interface FeedbackBarProps {
  conversationId: string;
  message: AssistantMessage;
}

/**
 * "Was this helpful?" (components.md → FeedbackBar): 👍 saves at once; 👎 opens an optional comment that is
 * saved with Send. The saved rating stays pressed; changing it updates the same feedback (upsert).
 *
 * @param props Conversation id and the assistant message.
 * @returns The bar.
 */
export function FeedbackBar({ conversationId, message }: FeedbackBarProps) {
  const { t } = useTranslation();
  const questionId = useId();
  const commentId = useId();
  const mutation = useSendFeedback();
  const [saved, setSaved] = useState<Feedback | null>(message.feedback);
  const [rating, setRating] = useState<Feedback["rating"] | null>(message.feedback?.rating ?? null);
  const [comment, setComment] = useState(message.feedback?.comment ?? "");
  const commentOpen = rating === -1 && saved?.rating !== -1;

  /**
   * Upsert the feedback.
   *
   * @param feedback Rating and comment.
   */
  const save = (feedback: Feedback) =>
    mutation.mutate({ conversationId, messageId: message.id, feedback }, { onSuccess: setSaved });

  return (
    <section className="feedback" aria-labelledby={questionId}>
      <div className="feedback__row">
        <p className="feedback__q" id={questionId}>
          {t("feedback.question")}
        </p>
        <IconButton
          label={t("feedback.up")}
          pressed={rating === 1}
          icon={<ThumbsUp className="icon" aria-hidden="true" />}
          onClick={() => {
            setRating(1);
            save({ rating: 1, comment });
          }}
        />
        <IconButton
          label={t("feedback.down")}
          pressed={rating === -1}
          icon={<ThumbsDown className="icon" aria-hidden="true" />}
          onClick={() => setRating(-1)}
        />
      </div>
      {commentOpen && (
        <form
          className="form"
          onSubmit={(event) => {
            event.preventDefault();
            save({ rating: -1, comment });
          }}
        >
          <div className="field">
            <label className="field__label" htmlFor={commentId}>
              {t("feedback.comment_label")}
            </label>
            <textarea
              id={commentId}
              className="textarea"
              maxLength={MAX_COMMENT_LENGTH}
              value={comment}
              onChange={(event) => setComment(event.target.value)}
            />
          </div>
          <div className="row-actions">
            <Button type="submit" busy={mutation.isPending}>
              {t("feedback.send")}
            </Button>
          </div>
        </form>
      )}
      {saved && !mutation.isPending && (
        <p className="feedback__saved" role="status">
          <Check className="icon" aria-hidden="true" />
          {t("feedback.saved")}
        </p>
      )}
      {mutation.isError && <Alert tone="danger">{t("error.server")}</Alert>}
    </section>
  );
}
