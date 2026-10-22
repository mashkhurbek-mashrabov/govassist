import type { ButtonHTMLAttributes, ReactNode, Ref } from "react";

/** Props of {@link IconButton}. */
interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Accessible name (required: the button has no visible text). */
  label: string;
  icon: ReactNode;
  /** Filled primary look (Send). */
  primary?: boolean;
  /** Toggle state (feedback buttons). */
  pressed?: boolean;
  ref?: Ref<HTMLButtonElement>;
}

/**
 * 44 × 44 icon-only button.
 *
 * @param props Label, icon, look, toggle state and native button props.
 * @returns The button.
 */
export function IconButton({
  label,
  icon,
  primary,
  pressed,
  className,
  type = "button",
  ...rest
}: IconButtonProps) {
  return (
    <button
      type={type}
      className={["icon-btn", primary && "icon-btn--primary", className].filter(Boolean).join(" ")}
      aria-label={label}
      aria-pressed={pressed}
      {...rest}
    >
      {icon}
    </button>
  );
}
