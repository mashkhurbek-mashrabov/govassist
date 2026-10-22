import { SearchX } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useSuggestions } from "../../api/queries";
import type { PartialAnswer } from "./answerTypes";
import { Chips } from "./Chips";

/** Props of {@link NotFoundCard}. */
interface NotFoundCardProps {
  answer: PartialAnswer;
  onAsk: ((question: string) => void) | undefined;
}

/**
 * `not_found` / `off_topic` card (screen 11): title, summary, help line, topic chips (the answer's
 * follow-ups, else `/suggestions`).
 *
 * @param props The answer and the ask callback.
 * @returns The card.
 */
export function NotFoundCard({ answer, onAsk }: NotFoundCardProps) {
  const { t } = useTranslation();
  const suggestions = useSuggestions();
  const followUps = answer.follow_up_questions?.filter(Boolean) ?? [];
  const topics = followUps.length > 0 ? followUps : (suggestions.data?.map((item) => item.text) ?? []);
  return (
    <div className="card">
      <h2 className="card__head t-h2">
        <SearchX className="icon" aria-hidden="true" />
        {answer.title ?? ""}
      </h2>
      <p className="t-body-lg">{answer.summary ?? ""}</p>
      <p className="t-muted">
        {t(answer.answer_type === "off_topic" ? "answer.off_topic_help" : "answer.not_found_help")}
      </p>
      <Chips questions={topics} onAsk={onAsk} />
    </div>
  );
}
