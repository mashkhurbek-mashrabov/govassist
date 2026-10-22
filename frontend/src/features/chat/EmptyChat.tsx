import { useTranslation } from "react-i18next";
import { useSuggestions } from "../../api/queries";
import { FollowUpChips } from "../answer/FollowUpChips";

/** Props of {@link EmptyChat}. */
interface EmptyChatProps {
  onAsk: (question: string) => void;
}

/**
 * New-chat welcome with starter questions.
 *
 * @param props Ask callback.
 * @returns The empty state.
 */
export function EmptyChat({ onAsk }: EmptyChatProps) {
  const { t } = useTranslation();
  const suggestions = useSuggestions();
  return (
    <section className="flex flex-col gap-3">
      <h2 className="font-bold">{t("chat.empty.title")}</h2>
      <p>{t("chat.empty.body")}</p>
      <FollowUpChips
        heading={t("chat.suggestions")}
        questions={suggestions.data?.map((item) => item.text)}
        onAsk={onAsk}
        disabled={false}
      />
    </section>
  );
}
