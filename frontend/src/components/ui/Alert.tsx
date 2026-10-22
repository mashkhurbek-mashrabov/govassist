import { CircleAlert, CircleCheck, Info, TriangleAlert } from "lucide-react";
import type { AriaRole, ReactNode } from "react";

/** Alert colour and icon. */
export type AlertTone = "info" | "success" | "warning" | "danger";

/** Icon per tone. */
const ICONS = { info: Info, success: CircleCheck, warning: TriangleAlert, danger: CircleAlert } as const;

/** Props of {@link Alert}. */
interface AlertProps {
  tone?: AlertTone;
  title?: string | undefined;
  /** Buttons under the text (e.g. Retry). */
  actions?: ReactNode;
  /** Defaults: `alert` for danger, `status` otherwise. */
  role?: AriaRole;
  children?: ReactNode;
}

/**
 * Inline message box (components.md → Alert).
 *
 * @param props Tone, title, actions, role and text.
 * @returns The alert.
 */
export function Alert({ tone = "info", title, actions, role, children }: AlertProps) {
  const Icon = ICONS[tone];
  return (
    <div
      className={tone === "info" ? "alert" : `alert alert--${tone}`}
      role={role ?? (tone === "danger" ? "alert" : "status")}
    >
      <Icon className="icon" aria-hidden="true" />
      <div className="alert__body">
        {title && <p className="alert__title">{title}</p>}
        {typeof children === "string" ? <p>{children}</p> : children}
        {actions && <div className="alert__actions">{actions}</div>}
      </div>
    </div>
  );
}
