import type { Stage } from "../../api/types";

/**
 * Translated text for a stream stage.
 *
 * @param stage Current stage (`null` before the first status event).
 * @param sourceCount Sources found, for the `found` stage.
 * @param t Translation function.
 * @returns The text.
 */
export function stageText(
  stage: Stage | null,
  sourceCount: number | null,
  t: (key: string, options?: Record<string, number>) => string,
): string {
  if (stage === "found") return t("chat.stage.found", { count: sourceCount ?? 0 });
  return t(`chat.stage.${stage ?? "searching"}`);
}
