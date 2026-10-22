import { Menu, SquarePen } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { flushSync } from "react-dom";
import { useTranslation } from "react-i18next";
import { Link, Navigate, Outlet, useLocation } from "react-router";
import { useViewer } from "../../api/queries";
import type { Me } from "../../api/types";
import { IconButton } from "../../components/ui/IconButton";
import { signedOutPath } from "../guards";
import { MeContext } from "./meContext";
import { OfflineBanner } from "./OfflineBanner";
import { Sidebar, SIDEBAR_ID } from "./Sidebar";
import { useTopbarTitle } from "./useTopbarTitle";

/** Where the sidebar stops being a drawer (tokens.css breakpoint `lg`, as in the stylesheet). */
const PERSISTENT_SIDEBAR_QUERY = "(min-width: 1280px)";

/**
 * Apply the profile's UI language whenever it changes.
 *
 * @param lang `Me.ui_language`.
 */
function useProfileLanguage(lang: string): void {
  const { i18n } = useTranslation();
  useEffect(() => {
    if (i18n.language !== lang) void i18n.changeLanguage(lang);
  }, [i18n, lang]);
}

/**
 * Signed-in layout (screens 7–15). Leaves as soon as the session ends, so no page renders without `Me`:
 * to the landing after logout, to login with a notice after a 401.
 *
 * @returns The layout, or a redirect.
 */
export function AppShell() {
  const { data: viewer } = useViewer();
  if (viewer?.state !== "authenticated") return <Navigate to={signedOutPath(viewer)} replace />;
  return <Shell me={viewer.me} />;
}

/** Props of {@link Shell}. */
interface ShellProps {
  me: Me;
}

/**
 * Sidebar/drawer, sticky top bar, offline banner and the page.
 *
 * @param props The signed-in user.
 * @returns The layout.
 */
function Shell({ me }: ShellProps) {
  const { t } = useTranslation();
  useProfileLanguage(me.ui_language);
  const title = useTopbarTitle();
  const location = useLocation();
  // The drawer remembers the page it was opened on, so navigating anywhere closes it.
  const [drawerPath, setDrawerPath] = useState<string | null>(null);
  const drawerOpen = drawerPath === location.pathname;
  const menuRef = useRef<HTMLButtonElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);

  /** Close the drawer and give focus back to the menu button (after the page stops being inert). */
  const closeDrawer = useCallback(() => {
    flushSync(() => setDrawerPath(null));
    menuRef.current?.focus();
  }, []);

  // Widening to the persistent sidebar closes the drawer, so the page is never left inert behind it.
  useEffect(() => {
    if (!drawerOpen || typeof window.matchMedia !== "function") return;
    const query = window.matchMedia(PERSISTENT_SIDEBAR_QUERY);
    /** Close the drawer once the sidebar is persistent. */
    const onChange = () => {
      if (query.matches) setDrawerPath(null);
    };
    query.addEventListener("change", onChange);
    return () => query.removeEventListener("change", onChange);
  }, [drawerOpen]);

  useEffect(() => {
    if (!drawerOpen) return;
    closeRef.current?.focus();
    /**
     * Esc closes the drawer.
     *
     * @param event Key event.
     */
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") closeDrawer();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [drawerOpen, closeDrawer]);

  return (
    <MeContext value={me}>
      <a className="skip-link" href="#main">
        {t("app.skip_to_main")}
      </a>
      <div className={drawerOpen ? "shell drawer-open" : "shell"}>
        <Sidebar showHistory={me.profile_complete} onClose={closeDrawer} closeRef={closeRef} />
        <div className="scrim scrim--drawer" aria-hidden="true" onClick={closeDrawer} />
        {/* The open drawer is modal: the top bar, page and composer behind the scrim are inert. */}
        <div className="main-col" inert={drawerOpen}>
          <header className="topbar">
            <IconButton
              ref={menuRef}
              className="topbar__drawer"
              label={t("chat.menu")}
              aria-controls={SIDEBAR_ID}
              aria-expanded={drawerOpen}
              icon={<Menu className="icon" aria-hidden="true" />}
              onClick={() => setDrawerPath(location.pathname)}
            />
            <p className="topbar__title">{title}</p>
            <Link className="icon-btn topbar__new" to="/" aria-label={t("chat.new")}>
              <SquarePen className="icon" aria-hidden="true" />
            </Link>
          </header>
          <OfflineBanner />
          <Outlet />
        </div>
      </div>
    </MeContext>
  );
}
