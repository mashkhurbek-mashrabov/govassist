import { Scale } from "lucide-react";
import { useId } from "react";
import { useTranslation } from "react-i18next";
import type { DeepPartialLawPoint } from "./answerTypes";
import { CitationBadges } from "./CitationBadges";

/** Props of {@link LawPointsCard}. */
interface LawPointsCardProps {
  points: DeepPartialLawPoint[] | undefined;
  index: Map<string, number>;
  messageId: string;
}

/**
 * "What the law says": quote + plain-language explanation + badge per point (components.md → LawPointCard).
 *
 * @param props Law points, numbering and message id.
 * @returns The card, or nothing when empty.
 */
export function LawPointsCard({ points, index, messageId }: LawPointsCardProps) {
  const { t } = useTranslation();
  const headingId = useId();
  if (!points?.length) return null;
  return (
    <section className="card" aria-labelledby={headingId}>
      <h3 className="card__head" id={headingId}>
        <Scale className="icon" aria-hidden="true" />
        {t("answer.law_says")}
      </h3>
      {points.map((point, position) => (
        <div key={position} className="law">
          <p className="law__label">{t("answer.quote_label")}</p>
          <blockquote>
            <p>{point.quote ?? ""}</p>
          </blockquote>
          <p className="law__label">{t("answer.explanation_label")}</p>
          <p>
            {point.explanation ?? ""}
            <CitationBadges sourceIds={point.source_ids} index={index} messageId={messageId} />
          </p>
        </div>
      ))}
    </section>
  );
}
