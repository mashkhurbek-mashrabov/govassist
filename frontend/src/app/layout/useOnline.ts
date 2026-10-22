import { useSyncExternalStore } from "react";

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
export function useOnline(): boolean {
  return useSyncExternalStore(subscribe, () => navigator.onLine);
}
