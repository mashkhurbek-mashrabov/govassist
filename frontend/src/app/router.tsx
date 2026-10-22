/** Route table (plan §3). Pages are lazy-loaded per route to keep the initial bundle small. */
import type { QueryClient } from "@tanstack/react-query";
import { createBrowserRouter, type RouteObject } from "react-router";
import { guard } from "./guards";
import { AppShell } from "./layout/AppShell";
import { AuthLayout } from "./layout/AuthLayout";
import { PublicPageLayout } from "./layout/PublicPageLayout";
import { RootLayout } from "./layout/RootLayout";
import { RouteError } from "./layout/RouteError";
import type { RouteHandle } from "./layout/useTopbarTitle";

/**
 * Route `handle` with the top-bar title key.
 *
 * @param titleKey i18n key.
 * @returns The handle.
 */
function titled(titleKey: string): RouteHandle {
  return { titleKey };
}

/**
 * Build the app routes.
 *
 * @param client Query client used by the guard loaders.
 * @returns Route objects for the data router.
 */
export function appRoutes(client: QueryClient): RouteObject[] {
  return [
    {
      element: <RootLayout />,
      errorElement: <RouteError />,
      children: [
        {
          element: <AuthLayout />,
          children: [
            {
              path: "/welcome",
              loader: guard(client, "guest"),
              lazy: async () => ({
                Component: (await import("../features/welcome/WelcomePage")).WelcomePage,
              }),
            },
            {
              path: "/signup",
              loader: guard(client, "guest"),
              lazy: async () => ({ Component: (await import("../features/auth/SignupPage")).SignupPage }),
            },
            {
              path: "/login",
              loader: guard(client, "guest"),
              lazy: async () => ({ Component: (await import("../features/auth/LoginPage")).LoginPage }),
            },
            {
              path: "/forgot-password",
              loader: guard(client, "guest"),
              lazy: async () => ({
                Component: (await import("../features/auth/ForgotPasswordPage")).ForgotPasswordPage,
              }),
            },
            {
              path: "/check-email",
              loader: guard(client, "unverified"),
              lazy: async () => ({
                Component: (await import("../features/auth/CheckEmailPage")).CheckEmailPage,
              }),
            },
            {
              path: "/verify-email/:key",
              lazy: async () => ({
                Component: (await import("../features/auth/VerifyEmailPage")).VerifyEmailPage,
              }),
            },
            {
              path: "/reset-password/:key",
              lazy: async () => ({
                Component: (await import("../features/auth/ResetPasswordPage")).ResetPasswordPage,
              }),
            },
            {
              path: "/onboarding",
              loader: guard(client, "auth"),
              lazy: async () => ({
                Component: (await import("../features/onboarding/OnboardingPage")).OnboardingPage,
              }),
            },
            {
              path: "*",
              lazy: async () => ({ Component: (await import("./layout/NotFoundPage")).NotFoundPage }),
            },
          ],
        },
        {
          element: <PublicPageLayout />,
          children: [
            {
              path: "/about",
              handle: titled("app.about"),
              lazy: async () => ({ Component: (await import("../features/about/AboutPage")).AboutPage }),
            },
          ],
        },
        {
          element: <AppShell />,
          loader: guard(client, "auth"),
          children: [
            {
              lazy: async () => ({ Component: (await import("../features/chat/ChatLayout")).ChatLayout }),
              loader: guard(client, "profile"),
              children: [
                {
                  index: true,
                  lazy: async () => ({ Component: (await import("../features/chat/ChatPage")).ChatPage }),
                },
                {
                  path: "/c/:conversationId",
                  lazy: async () => ({ Component: (await import("../features/chat/ChatPage")).ChatPage }),
                },
              ],
            },
            {
              path: "/history",
              handle: titled("history.title"),
              loader: guard(client, "profile"),
              lazy: async () => ({
                Component: (await import("../features/history/HistoryPage")).HistoryPage,
              }),
            },
            {
              path: "/settings",
              handle: titled("settings.title"),
              lazy: async () => ({
                Component: (await import("../features/settings/SettingsPage")).SettingsPage,
              }),
            },
          ],
        },
      ],
    },
  ];
}

/**
 * Create the browser router.
 *
 * @param client Query client used by the guard loaders.
 * @returns The data router.
 */
export function createAppRouter(client: QueryClient) {
  return createBrowserRouter(appRoutes(client));
}
