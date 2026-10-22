import type { ReactNode } from "react";
import { Link, type LinkProps } from "react-router";
import { buttonClass, type ButtonLook } from "./buttonClass";

/** Props of {@link LinkButton}. */
interface LinkButtonProps extends LinkProps, Omit<ButtonLook, "className"> {
  icon?: ReactNode;
}

/**
 * A navigating button: a router link with the `.btn` look.
 *
 * @param props Look, icon and link props.
 * @returns The link.
 */
export function LinkButton({ variant, small, block, icon, className, children, ...rest }: LinkButtonProps) {
  return (
    <Link
      className={buttonClass({
        variant,
        small,
        block,
        className: typeof className === "string" ? className : undefined,
      })}
      {...rest}
    >
      {icon}
      <span>{children}</span>
    </Link>
  );
}
