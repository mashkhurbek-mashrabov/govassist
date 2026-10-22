import { useTranslation } from "react-i18next";
import { citationNumbers, sourceAnchorId } from "../../lib/citations";

/** Props of {@link CitationBadges}. */
interface CitationBadgesProps {
  sourceIds: string[] | undefined;
  /** `S` id → display number; empty while streaming (sources arrive with `final`). */
  index: Map<string, number>;
  messageId: string;
}

/**
 * `[n]` links that jump to the cited source. Nothing for items without valid sources.
 *
 * @param props Item source ids, numbering and message id.
 * @returns The badges, or nothing.
 */
export function CitationBadges({ sourceIds, index, messageId }: CitationBadgesProps) {
  const { t } = useTranslation();
  const numbers = citationNumbers(sourceIds ?? [], index);
  if (numbers.length === 0) return null;
  const idByNumber = new Map([...index].map(([id, number]) => [number, id]));
  return (
    <>
      {numbers.map((number) => (
        <a
          key={number}
          href={`#${sourceAnchorId(messageId, idByNumber.get(number) ?? "")}`}
          aria-label={t("answer.citation", { n: number })}
          className="ml-1 inline-block min-w-6 text-center"
        >
          [{number}]
        </a>
      ))}
    </>
  );
}
