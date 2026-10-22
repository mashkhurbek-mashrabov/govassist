import type { ButtonHTMLAttributes, ReactNode } from "react";
import { buttonClass, type ButtonLook } from "./buttonClass";
import { Spinner } from "./Spinner";

/** Props of {@link Button}. */
interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement>, Omit<ButtonLook, "className"> {
  /** Leading icon (decorative). */
  icon?: ReactNode;
  /** Loading: spinner replaces the icon, label becomes `busyLabel`, the button is disabled. */
  busy?: boolean;
  busyLabel?: string;
}

/**
 * Native button with the design's variants and the shared loading state.
 *
 * @param props Look, icon, busy state and native button props.
 * @returns The button.
 */
export function Button({
  variant,
  small,
  block,
  icon,
  busy = false,
  busyLabel,
  className,
  children,
  disabled,
  type = "button",
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      className={buttonClass({ variant, small, block, className })}
      disabled={disabled === true || busy}
      aria-busy={busy || undefined}
      {...rest}
    >
      {busy ? <Spinner /> : icon}
      <span>{busy && busyLabel ? busyLabel : children}</span>
    </button>
  );
}
