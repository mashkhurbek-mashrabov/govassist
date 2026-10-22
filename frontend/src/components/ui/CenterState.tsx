import type { AriaRole, ReactNode } from "react";

/** Props of {@link CenterState}. */
interface CenterStateProps {
  icon: ReactNode;
  tone?: "default" | "success" | "danger";
  title: string;
  /** Heading level: the page title (1) or a section inside a page (2). */
  level?: 1 | 2;
  role?: AriaRole;
  children?: ReactNode;
}

/**
 * Centred icon + title + text block (check email, verify, empty history, 404).
 *
 * @param props Icon, tone, title, heading level, role and body.
 * @returns The block.
 */
export function CenterState({ icon, tone = "default", title, level = 1, role, children }: CenterStateProps) {
  const Heading = level === 1 ? "h1" : "h2";
  return (
    <div className="center-state" role={role}>
      <div
        className={
          tone === "default" ? "center-state__icon" : `center-state__icon center-state__icon--${tone}`
        }
      >
        {icon}
      </div>
      <Heading>{title}</Heading>
      {children}
    </div>
  );
}
