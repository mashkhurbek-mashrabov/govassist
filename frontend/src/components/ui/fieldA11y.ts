/** Shared id/ARIA wiring for form fields (label, hint, error). */

/** ARIA attributes of a field control. */
export interface FieldA11y {
  hintId: string;
  errorId: string;
  describedBy: string | undefined;
  invalid: true | undefined;
}

/**
 * Ids for the hint and error, and the matching `aria-describedby` / `aria-invalid`.
 *
 * @param id The control's id.
 * @param hasHint Whether a hint is rendered.
 * @param error Error text, if any.
 * @param extra Extra described-by ids (e.g. a strength line).
 * @returns The wiring.
 */
export function fieldA11y(
  id: string,
  hasHint: boolean,
  error: string | undefined,
  extra: string[] = [],
): FieldA11y {
  const hintId = `${id}-hint`;
  const errorId = `${id}-error`;
  const ids = [hasHint && hintId, ...extra, error && errorId].filter(Boolean);
  return {
    hintId,
    errorId,
    describedBy: ids.length > 0 ? ids.join(" ") : undefined,
    invalid: error ? true : undefined,
  };
}
