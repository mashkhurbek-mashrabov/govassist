import { useTranslation } from "react-i18next";

/** Props of {@link FollowUpChips}. */
interface FollowUpChipsProps {
  questions: (string | undefined)[] | undefined;
  /** Ask a question; `undefined` hides the chips (older answers). */
  onAsk: ((question: string) => void) | undefined;
  disabled: boolean;
  /** Heading key, e.g. follow-ups or starter suggestions. */
  heading?: string;
}

/**
 * Suggested next questions as buttons that ask them.
 *
 * @param props Questions, ask callback, disabled flag, optional heading.
 * @returns The chips, or nothing.
 */
export function FollowUpChips({ questions, onAsk, disabled, heading }: FollowUpChipsProps) {
  const { t } = useTranslation();
  const ready = (questions ?? []).filter((question): question is string => Boolean(question));
  if (!onAsk || ready.length === 0) return null;
  return (
    <section className="flex flex-col gap-1">
      <h3 className="font-bold">{heading ?? t("answer.followUps")}</h3>
      <ul className="flex flex-wrap gap-2">
        {ready.map((question) => (
          <li key={question}>
            <button
              type="button"
              className="min-h-11 border px-3"
              disabled={disabled}
              onClick={() => onAsk(question)}
            >
              {question}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
