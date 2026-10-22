import { createContext, use } from "react";

/** Shows a short status message at the bottom (components.md → Toast). */
export type ShowToast = (text: string) => void;

/** The toast function, provided by `ToastProvider`. */
export const ToastContext = createContext<ShowToast | null>(null);

/**
 * Get the toast function.
 *
 * @returns `showToast(text)`.
 * @throws {Error} Outside `ToastProvider`.
 */
export function useToast(): ShowToast {
  const show = use(ToastContext);
  if (!show) throw new Error("useToast() used outside ToastProvider");
  return show;
}
