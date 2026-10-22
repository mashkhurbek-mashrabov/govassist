/** Bootstrap: mocks (optional), i18n, CSRF cookie, query client, router. */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router";
import { fetchCsrf } from "./api/endpoints";
import { ApiError, setUnauthorizedHandler } from "./api/http";
import { resetToAnonymous } from "./api/queries";
import { createAppRouter } from "./app/router";
import "./i18n";
import "./styles/index.css";

/** Retries for failed queries; client errors (4xx) are never retried. */
const MAX_QUERY_RETRIES = 2;

/**
 * Start the MSW service worker when mocks are on. `__USE_MOCKS__` is a build-time constant, so normal
 * builds drop the mock chunk entirely.
 */
async function startMocks(): Promise<void> {
  if (__USE_MOCKS__) {
    const { worker } = await import("./mocks/browser");
    await worker.start({ onUnhandledFrame: "bypass", quiet: true });
  }
}

/**
 * Retry server and network errors only.
 *
 * @param failureCount Attempts so far.
 * @param error The last error.
 * @returns Whether to retry.
 */
function shouldRetry(failureCount: number, error: Error): boolean {
  if (error instanceof ApiError && error.status < 500) return false;
  return failureCount < MAX_QUERY_RETRIES;
}

/**
 * Boot the SPA (plan §3: CSRF → session → /me → guards).
 */
async function boot(): Promise<void> {
  await startMocks();
  // Without the cookie the app still renders; unsafe requests then fail visibly with 403.
  await fetchCsrf().catch((error: unknown) => console.error("CSRF bootstrap failed", error));
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: shouldRetry } } });
  const router = createAppRouter(queryClient);
  // AppShell sees the anonymous viewer and leaves for the login page with the "session ended" notice.
  setUnauthorizedHandler(() => resetToAnonymous(queryClient, true));
  const root = document.getElementById("root");
  if (!root) throw new Error("#root element missing from index.html");
  createRoot(root).render(
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </StrictMode>,
  );
}

void boot();
