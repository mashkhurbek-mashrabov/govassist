import { useId } from "react";
import { useTranslation } from "react-i18next";
import { Chips } from "./Chips";

/** Props of {@link FollowUps}. */
interface FollowUpsProps {
  questions: (string | undefined)[] | undefined;
  onAsk: ((question: string) => void) | undefined;
  disabled?: boolean;
}

/**
 * "You can also ask" follow-up chips (≤ 3); hidden when empty or when asking is not offered.
 *
 * @param props Questions, ask callback and disabled flag.
 * @returns The section, or nothing.
 */
export function FollowUps({ questions, onAsk, disabled }: FollowUpsProps) {
  const { t } = useTranslation();
  const headingId = useId();
  if (!onAsk || !questions?.some(Boolean)) return null;
  return (
    <section className="followups" aria-labelledby={headingId}>
      <h3 className="t-small t-muted" id={headingId}>
        {t("answer.followups")}
      </h3>
      <Chips questions={questions} onAsk={onAsk} disabled={disabled} />
    </section>
  );
}
