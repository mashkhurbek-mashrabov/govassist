import { ListChecks } from "lucide-react";
import { useId } from "react";
import { useTranslation } from "react-i18next";
import { Skeleton } from "../../components/ui/Skeleton";
import type { DeepPartialItem } from "./answerTypes";
import { CitedText } from "./CitedText";

/** Placeholder step rows while the steps are about to stream. */
const SKELETON_ROWS = 2;

/** Props of {@link StepsCard}. */
interface StepsCardProps {
  /** "What to do" (service) or "What you can do" (legal). */
  headingKey: "answer.steps" | "answer.what_you_can_do";
  items: DeepPartialItem[] | undefined;
  index: Map<string, number>;
  messageId: string;
  /** Show skeleton rows instead of items. */
  placeholder?: boolean;
  /** Caret on the last item. */
  typing?: boolean;
}

/**
 * Numbered steps card (components.md → StepsList).
 *
 * @param props Heading, items, numbering, message id, placeholder and caret flags.
 * @returns The card, or nothing when there are no steps.
 */
export function StepsCard({ headingKey, items, index, messageId, placeholder, typing }: StepsCardProps) {
  const { t } = useTranslation();
  const headingId = useId();
  if (!placeholder && !items?.length) return null;
  return (
    <section className="card" aria-labelledby={headingId}>
      <h3 className="card__head" id={headingId}>
        <ListChecks className="icon" aria-hidden="true" />
        {t(headingKey)}
      </h3>
      <ol className="steps">
        {placeholder
          ? Array.from({ length: SKELETON_ROWS }, (_, row) => (
              <li key={row} aria-hidden="true">
                <p>
                  <Skeleton />
                  <Skeleton width="60" />
                </p>
              </li>
            ))
          : items?.map((item, position) => (
              <li key={position}>
                <p>
                  <CitedText
                    item={item}
                    index={index}
                    messageId={messageId}
                    typing={typing === true && position === items.length - 1}
                  />
                </p>
              </li>
            ))}
      </ol>
    </section>
  );
}
