import { CircleCheck } from "lucide-react";
import { useCallback, useEffect, useState, type ReactNode } from "react";
import { ToastContext } from "./toastContext";

/** How long a toast stays (components.md: 4 s). */
const TOAST_MS = 4000;

/** Props of {@link ToastProvider}. */
interface ToastProviderProps {
  children: ReactNode;
}

/**
 * Renders one toast at a time and provides `useToast()`. Toasts are never the only place an error is shown.
 *
 * @param props Children.
 * @returns The provider and the toast.
 */
export function ToastProvider({ children }: ToastProviderProps) {
  const [toast, setToast] = useState<{ id: number; text: string } | null>(null);
  const show = useCallback((text: string) => setToast({ id: Date.now(), text }), []);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), TOAST_MS);
    return () => clearTimeout(timer);
  }, [toast]);

  return (
    <ToastContext value={show}>
      {children}
      {toast && (
        <div key={toast.id} className="toast" role="status">
          <CircleCheck className="icon" aria-hidden="true" />
          <span>{toast.text}</span>
        </div>
      )}
    </ToastContext>
  );
}
