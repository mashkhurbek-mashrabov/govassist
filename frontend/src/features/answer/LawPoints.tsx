import { useTranslation } from "react-i18next";
import type { DeepPartialLawPoint } from "./answerTypes";
import { CitationBadges } from "./CitationBadges";

/** Props of {@link LawPoints}. */
interface LawPointsProps {
  points: DeepPartialLawPoint[] | undefined;
  index: Map<string, number>;
  messageId: string;
}

/**
 * Quoted legal clauses with plain-language explanations. Hidden when empty.
 *
 * @param props Law points, numbering and message id.
 * @returns The section, or nothing.
 */
export function LawPoints({ points, index, messageId }: LawPointsProps) {
  const { t } = useTranslation();
  if (!points?.length) return null;
  return (
    <section className="flex flex-col gap-2">
      <h3 className="font-bold">{t("answer.lawPoints")}</h3>
      {points.map((point, position) => (
        <figure key={position} className="flex flex-col gap-1">
          <blockquote className="border-l-4 pl-3">{point.quote ?? ""}</blockquote>
          <figcaption>
            {point.explanation ?? ""}
            <CitationBadges sourceIds={point.source_ids} index={index} messageId={messageId} />
          </figcaption>
        </figure>
      ))}
    </section>
  );
}
