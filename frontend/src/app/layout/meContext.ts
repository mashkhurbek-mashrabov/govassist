import { createContext, use } from "react";
import type { Me } from "../../api/types";

/**
 * The signed-in user, provided by `AppShell`. Pages read it from here instead of subscribing to the
 * session query, so after logout only the shell re-renders (and redirects) and no page renders without `Me`.
 */
export const MeContext = createContext<Me | null>(null);

/**
 * The signed-in user. Only valid below `AppShell`.
 *
 * @returns `Me`.
 * @throws {Error} When used outside `AppShell`.
 */
export function useMe(): Me {
  const me = use(MeContext);
  if (!me) throw new Error("useMe() used outside AppShell");
  return me;
}
