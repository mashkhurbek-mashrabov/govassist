import { useTranslation } from "react-i18next";
import { Link, Outlet } from "react-router";
import { Wordmark } from "../../components/ui/Wordmark";
import { LanguageMenu } from "../../features/language/LanguageMenu";
import { OfflineBanner } from "./OfflineBanner";

/**
 * Layout for signed-out pages (screens 1–6, 16): wordmark + language menu, one column, footer with the
 * "not official" note. The landing page has its own layout (`WelcomePage`).
 *
 * @returns The layout.
 */
export function AuthLayout() {
  const { t } = useTranslation();
  return (
    <div className="auth">
      <a className="skip-link" href="#main">
        {t("app.skip_to_main")}
      </a>
      <header className="auth__header">
        <Wordmark to="/" />
        <LanguageMenu />
      </header>
      <OfflineBanner />
      <main className="auth__main" id="main" data-lang-region>
        <Outlet />
      </main>
      <footer className="auth__footer">
        <p className="footer-note">{t("app.not_official")}</p>
        <nav className="footer-links" aria-label={t("app.about")}>
          <Link to="/about">{t("app.about")}</Link>
          <Link to="/about#privacy">{t("auth.privacy_link")}</Link>
        </nav>
      </footer>
    </div>
  );
}
