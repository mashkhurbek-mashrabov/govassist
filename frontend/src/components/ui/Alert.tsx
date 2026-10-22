import { CircleAlert, CircleCheck, Info, TriangleAlert, type LucideIcon } from "lucide-react";
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
  /** Overrides the tone's icon (e.g. a clock on limit alerts, components.md → Icon inventory). */
  icon?: LucideIcon;
  /** Defaults: `alert` for danger, `status` otherwise. */
  role?: AriaRole;
  children?: ReactNode;
}

/**
 * Inline message box (components.md → Alert).
 *
 * @param props Tone, title, actions, icon, role and text.
 * @returns The alert.
 */
export function Alert({ tone = "info", title, actions, icon, role, children }: AlertProps) {
  const Icon = icon ?? ICONS[tone];
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
