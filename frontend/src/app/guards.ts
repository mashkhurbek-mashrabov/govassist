/** Route guards (plan §3), as pure rules plus a loader factory. */
import type { QueryClient } from "@tanstack/react-query";
import { redirect, type LoaderFunctionArgs } from "react-router";
import { viewerQuery, type Viewer } from "../api/queries";

/** What a route needs from the viewer. */
export type Requirement =
  /** Signup/login/forgot: not signed in. */
  | "guest"
  /** Check-email: anyone not yet verified. */
  | "unverified"
  /** Signed in with a verified email. */
  | "auth"
  /** Signed in, verified, region + district set. */
  | "profile";

/** Where unauthenticated users go. */
export const LOGIN_PATH = "/login";
/** Where users without a district go. */
export const ONBOARDING_PATH = "/onboarding";
/** Where users with a pending verification go. */
export const CHECK_EMAIL_PATH = "/check-email";
/** Home: the new-chat page. */
export const HOME_PATH = "/";

/**
 * Accept only same-origin relative paths as a post-login target (prevents open redirects).
 *
 * @param next Raw `next` query value.
 * @returns A safe path, or the home path.
 */
export function safeNext(next: string | null): string {
  if (!next?.startsWith("/") || next.startsWith("//") || next.startsWith("/\\")) return HOME_PATH;
  return next;
}

/**
 * Decide whether a viewer may open a route.
 *
 * @param viewer Current viewer.
 * @param requirement The route's requirement.
 * @param path Requested path + query, kept as `next` for login.
 * @returns The redirect target, or `null` to allow.
 */
export function redirectFor(viewer: Viewer, requirement: Requirement, path: string): string | null {
  const signedIn = viewer.state === "authenticated";
  const verified = signedIn && viewer.me.email_verified;
  switch (requirement) {
    case "guest":
      return signedIn ? HOME_PATH : null;
    case "unverified":
      return verified ? HOME_PATH : null;
    case "auth":
    case "profile":
      if (viewer.state === "anonymous") return `${LOGIN_PATH}?next=${encodeURIComponent(path)}`;
      if (!verified) return CHECK_EMAIL_PATH;
      if (requirement === "profile" && !viewer.me.profile_complete) return ONBOARDING_PATH;
      return null;
  }
}

/**
 * Build a route loader that enforces a requirement.
 *
 * @param client Query client holding the viewer.
 * @param requirement The route's requirement.
 * @returns A loader that redirects or allows.
 */
export function guard(client: QueryClient, requirement: Requirement) {
  return async function guardLoader({ request }: LoaderFunctionArgs) {
    const viewer = await client.query({ ...viewerQuery, staleTime: "static" });
    const url = new URL(request.url);
    const target = redirectFor(viewer, requirement, `${url.pathname}${url.search}`);
    return target ? redirect(target) : null;
  };
}
