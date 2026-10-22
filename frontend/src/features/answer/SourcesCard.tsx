import { BookOpen } from "lucide-react";
import { useId } from "react";
import { useTranslation } from "react-i18next";
import type { Source } from "../../api/types";
import { ExternalLink } from "../../components/ui/ExternalLink";
import { sourceAnchorId } from "../../lib/citations";
import { formatDate } from "../../lib/format";

/** Props of {@link SourcesCard}. */
interface SourcesCardProps {
  sources: Source[];
  messageId: string;
}

/**
 * Numbered sources the badges jump to; numbers match the badges (components.md → SourcesList).
 *
 * @param props Sources in citation order and the message id.
 * @returns The card, or nothing without sources.
 */
export function SourcesCard({ sources, messageId }: SourcesCardProps) {
  const { t } = useTranslation();
  const headingId = useId();
  if (sources.length === 0) return null;
  return (
    <section className="card" aria-labelledby={headingId}>
      <h3 className="card__head" id={headingId}>
        <BookOpen className="icon" aria-hidden="true" />
        {t("answer.sources")}
      </h3>
      <ol className="sources">
        {sources.map((source, position) => {
          const meta = [
            source.publisher,
            t(`answer.source_kind_${source.kind}`),
            source.section,
            source.published_at && t("answer.source_published", { date: formatDate(source.published_at) }),
            t("answer.source_fetched", { date: formatDate(source.fetched_at) }),
          ].filter(Boolean);
          return (
            <li key={source.id} className="source" id={sourceAnchorId(messageId, source.id)} tabIndex={-1}>
              <span className="source__num" aria-hidden="true">
                {position + 1}
              </span>
              <div>
                <p className="source__title">
                  <ExternalLink href={source.url}>{source.title}</ExternalLink>
                </p>
                <p className="source__meta">{meta.join(" · ")}</p>
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
