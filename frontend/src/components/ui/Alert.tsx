import type { ReactNode } from "react";

/** Props of {@link Alert}. */
interface AlertProps {
  /** `error` interrupts screen readers (role=alert); `info` is polite (role=status). */
  tone?: "error" | "info";
  children: ReactNode;
}

/**
 * Inline message box.
 *
 * @param props Tone and content.
 * @returns The alert.
 */
export function Alert({ tone = "info", children }: AlertProps) {
  return (
    <div role={tone === "error" ? "alert" : "status"} className="border p-3">
      {children}
    </div>
  );
}
