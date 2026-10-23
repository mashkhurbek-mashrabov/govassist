/** Turnstile widget sizing for the signup column. */

/** Narrowest width Cloudflare's `flexible` widget supports; below it the `compact` widget is used. */
export const FLEXIBLE_MIN_WIDTH_PX = 300;

/**
 * Widget size for the space it gets: `flexible` fills the container, `compact` fits narrow phones.
 *
 * @param width Container width in px.
 * @returns The Turnstile `size` option.
 */
export function turnstileSize(width: number): "flexible" | "compact" {
  return width >= FLEXIBLE_MIN_WIDTH_PX ? "flexible" : "compact";
}
