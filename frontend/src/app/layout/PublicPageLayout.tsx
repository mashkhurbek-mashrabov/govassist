import { useViewer } from "../../api/queries";
import { AppShell } from "./AppShell";
import { AuthLayout } from "./AuthLayout";

/**
 * Layout for pages open to everyone (About): the app shell when signed in, the auth layout otherwise.
 *
 * @returns The matching layout.
 */
export function PublicPageLayout() {
  const { data: viewer } = useViewer();
  return viewer?.state === "authenticated" && viewer.me.email_verified ? <AppShell /> : <AuthLayout />;
}
