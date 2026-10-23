/** Test helpers: render with a fresh QueryClient, or mount the whole app on a memory router. */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, type RenderResult } from "@testing-library/react";
import type { ReactNode } from "react";
import { createMemoryRouter, RouterProvider, type RouteObject } from "react-router";
import { appRoutes } from "../app/router";
import { db, SEED_EMAIL } from "../mocks/db";

/**
 * A query client without retries, so failures surface immediately.
 *
 * @returns The client.
 */
export function testQueryClient(): QueryClient {
  return new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
}

/**
 * Load every lazy route module once. Pages are lazy-loaded (router.tsx), and the first visit to a route in a
 * test file otherwise waits for a cold dynamic import, which on a slow CI runner with coverage can take longer
 * than `findBy*`'s 1 s default. Run before each test file (setup.ts), so navigation never waits on an import.
 *
 * @returns Resolves once every route module is loaded.
 */
export async function preloadRoutes(): Promise<void> {
  const loading: Promise<unknown>[] = [];
  /**
   * Start each lazy route's import, depth first.
   *
   * @param routes A level of the route tree.
   */
  const visit = (routes: RouteObject[]) => {
    for (const route of routes) {
      if (typeof route.lazy === "function") loading.push(route.lazy());
      if (route.children) visit(route.children);
    }
  };
  visit(appRoutes(testQueryClient()));
  await Promise.all(loading);
}

/**
 * Wrapper component factory for `renderHook`.
 *
 * @param client Query client to provide.
 * @returns A wrapper component.
 */
export function queryWrapper(client: QueryClient) {
  return function QueryWrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

/**
 * Sign the seeded, onboarded mock user in.
 */
export function signInSeedUser(): void {
  db.sessionEmail = SEED_EMAIL;
}

/** Result of {@link renderApp}. */
export interface AppHandle extends RenderResult {
  router: ReturnType<typeof createMemoryRouter>;
  client: QueryClient;
}

/**
 * Mount the real route table at a path, against MSW.
 *
 * @param path Initial URL.
 * @returns Render result plus router and client.
 */
export function renderApp(path: string): AppHandle {
  const client = testQueryClient();
  const router = createMemoryRouter(appRoutes(client), { initialEntries: [path] });
  const result = render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
  return { ...result, router, client };
}
