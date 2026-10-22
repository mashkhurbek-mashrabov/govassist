import { useSyncExternalStore } from "react";
import { useTranslation } from "react-i18next";

/**
 * Subscribe to the browser's online/offline events.
 *
 * @param onChange Called on every change.
 * @returns Unsubscribe function.
 */
function subscribe(onChange: () => void): () => void {
  window.addEventListener("online", onChange);
  window.addEventListener("offline", onChange);
  return () => {
    window.removeEventListener("online", onChange);
    window.removeEventListener("offline", onChange);
  };
}

/**
 * Whether the browser reports a network connection.
 *
 * @returns `true` when online.
 */
function useOnline(): boolean {
  return useSyncExternalStore(subscribe, () => navigator.onLine);
}

/**
 * Global banner shown while the browser is offline.
 *
 * @returns The banner, or nothing when online.
 */
export function OfflineBanner() {
  const { t } = useTranslation();
  if (useOnline()) return null;
  return (
    <div role="status" className="border-b p-2 text-center">
      {t("offline.banner")}
    </div>
  );
}
