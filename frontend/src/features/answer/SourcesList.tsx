import { useTranslation } from "react-i18next";
import type { Lang, Source } from "../../api/types";
import { sourceAnchorId } from "../../lib/citations";
import { formatDate } from "../../lib/format";

/** Props of {@link SourcesList}. */
interface SourcesListProps {
  sources: Source[];
  messageId: string;
}

/**
 * Numbered sources the badges jump to. External links open in a new tab without an opener.
 *
 * @param props Sources (in citation order) and message id.
 * @returns The section, or nothing when there are no sources.
 */
export function SourcesList({ sources, messageId }: SourcesListProps) {
  const { t, i18n } = useTranslation();
  if (sources.length === 0) return null;
  const lang = i18n.language as Lang;
  return (
    <section className="flex flex-col gap-1">
      <h3 className="font-bold">{t("answer.sources")}</h3>
      <ol className="list-decimal pl-6">
        {sources.map((source) => (
          <li
            key={source.id}
            id={sourceAnchorId(messageId, source.id)}
            tabIndex={-1}
            className="target:font-bold"
          >
            <a href={source.url} target="_blank" rel="noopener noreferrer">
              {source.title}
            </a>
            {" · "}
            {source.publisher}
            {source.section && ` · ${source.section}`}
            {source.published_at &&
              ` · ${t("answer.published", { date: formatDate(source.published_at, lang) })}`}
          </li>
        ))}
      </ol>
    </section>
  );
}
