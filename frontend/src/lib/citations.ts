/** Citation badge numbering: `[n]` is the position of the source in `sources` (contract §5). */
import type { Source } from "../api/types";

/**
 * Map each source id to its 1-based display number.
 *
 * @param sources Sources in order of first citation.
 * @returns `S` id → number.
 */
export function citationIndex(sources: Source[]): Map<string, number> {
  return new Map(sources.map((source, position) => [source.id, position + 1]));
}

/**
 * Badge numbers for one item: known ids only, without duplicates, ascending.
 *
 * @param sourceIds The item's `source_ids`.
 * @param index Result of {@link citationIndex}.
 * @returns Numbers to show; empty means no badge.
 */
export function citationNumbers(sourceIds: string[], index: Map<string, number>): number[] {
  const numbers = sourceIds.flatMap((id) => {
    const number = index.get(id);
    return number === undefined ? [] : [number];
  });
  return [...new Set(numbers)].sort((a, b) => a - b);
}

/**
 * DOM id of a source entry, unique per message so badges jump to the right list.
 *
 * @param messageId Assistant message id.
 * @param sourceId Source id (`S1`).
 * @returns Element id.
 */
export function sourceAnchorId(messageId: string, sourceId: string): string {
  return `source-${messageId}-${sourceId}`;
}
