import { useTranslation } from "react-i18next";
import { Link, Outlet, useMatch } from "react-router";
import type { Lang } from "../../api/types";
import { LanguageSelect } from "../../components/ui/LanguageSelect";
import { LinkButton } from "../../components/ui/LinkButton";
import { Wordmark } from "../../components/ui/Wordmark";
import { OfflineBanner } from "./OfflineBanner";

/**
 * Layout for signed-out pages (screens 0–6, 16): wordmark + language switch, one column, footer with the
 * "not official" note. The landing page gets a wider column and a "Log in" link in the header.
 *
 * @returns The layout.
 */
export function AuthLayout() {
  const { t, i18n } = useTranslation();
  const isLanding = useMatch("/welcome") !== null;
  return (
    <div className={isLanding ? "auth landing" : "auth"}>
      <a className="skip-link" href="#main">
        {t("app.skip_to_main")}
      </a>
      <header className="auth__header">
        <Wordmark to="/" />
        <div className="row-actions">
          <LanguageSelect value={i18n.language as Lang} onChange={(lang) => void i18n.changeLanguage(lang)} />
          {isLanding && (
            <LinkButton variant="ghost" small to="/login">
              {t("landing.login")}
            </LinkButton>
          )}
        </div>
      </header>
      <OfflineBanner />
      <main className={isLanding ? "landing__main" : "auth__main"} id="main">
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
