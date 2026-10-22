import type { PartialAnswer } from "./answerTypes";

/** Service blocks in schema order, for the one-skeleton-ahead rule. */
const SERVICE_BLOCKS = ["steps", "documents", "facts"] as const;
type ServiceBlock = (typeof SERVICE_BLOCKS)[number];

/**
 * Which service block gets a skeleton: the first missing one after the summary, only while streaming
 * ("at most one skeleton block ahead of the text", components.md → Streaming behaviour).
 *
 * @param answer The partial answer.
 * @param streaming Whether text is still arriving.
 * @returns The block to placeholder, or `null`.
 */
export function nextSkeleton(answer: PartialAnswer, streaming: boolean): ServiceBlock | null {
  if (!streaming || answer.summary === undefined) return null;
  const present: Record<ServiceBlock, boolean> = {
    steps: answer.steps !== undefined,
    documents: answer.documents !== undefined,
    facts: answer.fee !== undefined || answer.processing_time !== undefined,
  };
  return SERVICE_BLOCKS.find((block) => !present[block]) ?? null;
}
