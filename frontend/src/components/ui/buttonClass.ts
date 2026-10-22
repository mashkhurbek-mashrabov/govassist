/** Class names of the `.btn` component (components.md → Button). */

/** Button look. One `primary` per screen. */
export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger" | "danger-ghost" | "google";

/** Options of {@link buttonClass}. */
export interface ButtonLook {
  variant?: ButtonVariant;
  /** 44 px instead of 48 px. */
  small?: boolean;
  /** Full width. */
  block?: boolean;
  className?: string | undefined;
}

/**
 * Build the class list for a button-looking element.
 *
 * @param look Variant, size, width and extra classes.
 * @returns The class attribute.
 */
export function buttonClass({ variant = "secondary", small, block, className }: ButtonLook = {}): string {
  return ["btn", `btn--${variant}`, small && "btn--sm", block && "btn--block", className]
    .filter(Boolean)
    .join(" ");
}
