import { useTranslation } from "react-i18next";
import { citationNumbers, sourceAnchorId } from "../../lib/citations";

/** Props of {@link CitationBadges}. */
interface CitationBadgesProps {
  sourceIds: (string | undefined)[] | undefined;
  /** `S` id → display number; empty while streaming (sources arrive with `final`). */
  index: Map<string, number>;
  messageId: string;
}

/**
 * `[n]` citation badges linking to the source (components.md → Badge). None for items without valid sources.
 *
 * @param props Item source ids, numbering and message id.
 * @returns The badges, or nothing.
 */
export function CitationBadges({ sourceIds, index, messageId }: CitationBadgesProps) {
  const { t } = useTranslation();
  const ids = (sourceIds ?? []).filter((id): id is string => typeof id === "string");
  const numbers = citationNumbers(ids, index);
  if (numbers.length === 0) return null;
  const idByNumber = new Map([...index].map(([id, number]) => [number, id]));
  return (
    <span className="cites">
      {numbers.map((number) => (
        <a
          key={number}
          className="cite"
          href={`#${sourceAnchorId(messageId, idByNumber.get(number) ?? "")}`}
          aria-label={t("answer.source_n", { n: number })}
        >
          {number}
        </a>
      ))}
    </span>
  );
}
