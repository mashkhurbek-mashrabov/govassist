import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Link, Navigate, NavLink, Outlet, useMatch } from "react-router";
import { useMaybeMe } from "../../api/queries";
import type { Me } from "../../api/types";
import { LOGIN_PATH } from "../guards";
import { MeContext } from "./meContext";
import { HistoryList } from "../../features/history/HistoryList";

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
 * Signed-in layout. Leaves for the login page as soon as the session ends, so no child renders without `Me`.
 *
 * @returns The layout, or a redirect.
 */
export function AppShell() {
  const me = useMaybeMe();
  return me ? <Shell me={me} /> : <Navigate to={LOGIN_PATH} replace />;
}

/** Props of {@link Shell}. */
interface ShellProps {
  me: Me;
}

/**
 * Top bar, history sidebar on wide screens (a page on phones), main content.
 *
 * @param props The signed-in user.
 * @returns The layout.
 */
function Shell({ me }: ShellProps) {
  const { t } = useTranslation();
  useProfileLanguage(me.ui_language);
  const onHistoryPage = useMatch("/history") !== null;
  return (
    <MeContext value={me}>
      <div className="flex min-h-dvh flex-col">
        <a href="#main" className="sr-only focus:not-sr-only">
          {t("nav.skipToContent")}
        </a>
        <header className="flex flex-wrap items-center gap-4 border-b p-3">
          <Link to="/" className="font-bold">
            {t("app.name")}
          </Link>
          <nav aria-label={t("nav.main")} className="flex flex-wrap gap-4">
            <NavLink to="/" end>
              {t("nav.newChat")}
            </NavLink>
            <NavLink to="/history" className="lg:hidden">
              {t("nav.history")}
            </NavLink>
            <NavLink to="/settings">{t("nav.settings")}</NavLink>
            <NavLink to="/about">{t("nav.about")}</NavLink>
          </nav>
        </header>
        <div className="flex grow">
          {me.profile_complete && !onHistoryPage && (
            <aside aria-label={t("nav.history")} className="hidden w-72 shrink-0 border-r p-3 lg:block">
              <HistoryList />
            </aside>
          )}
          <main id="main" className="flex min-w-0 grow flex-col p-3">
            <Outlet />
          </main>
        </div>
      </div>
    </MeContext>
  );
}
