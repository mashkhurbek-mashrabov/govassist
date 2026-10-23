import { Info } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { Wordmark } from "../../components/ui/Wordmark";
import { LanguageMenu } from "../language/LanguageMenu";
import { SECTIONS } from "./landingContent";

/** Official sources named in the footer: plain text links, never their logos. */
const SOURCE_LINKS = [
  { label: "lex.uz", href: "https://lex.uz/" },
  { label: "my.gov.uz", href: "https://my.gov.uz/" },
] as const;

/**
 * Landing footer (components.md → Landing parts → Footer): brand column with the "not official" sentence and
 * the language menu, then Product / Sources / Legal columns, then © and the "not official" pill.
 *
 * @returns The footer.
 */
export function LandingFooter() {
  const { t } = useTranslation();
  return (
    <footer className="lp-footer" data-lang-region>
      <div className="lp__inner">
        <div className="lp-footer__top">
          <div className="lp-footer__brand">
            <Wordmark to="/welcome" />
            <p className="t-muted">{t("footer.tagline")}</p>
            <p className="t-small t-muted">{t("app.not_official_long")}</p>
            <LanguageMenu up />
          </div>
          <div className="lp-footer__col">
            <h2 className="lp-footer__title">{t("footer.product")}</h2>
            <ul>
              {SECTIONS.map(({ id, navKey }) => (
                <li key={id}>
                  <a href={`#${id}`}>{t(navKey)}</a>
                </li>
              ))}
            </ul>
          </div>
          <div className="lp-footer__col">
            <h2 className="lp-footer__title">{t("footer.sources")}</h2>
            <ul>
              {SOURCE_LINKS.map(({ label, href }) => (
                <li key={href}>
                  <a href={href} target="_blank" rel="noopener noreferrer">
                    {label}
                    <span className="sr-only"> {t("common.opens_new_tab")}</span>
                  </a>
                </li>
              ))}
              <li>
                <Link to="/about">{t("footer.source_list")}</Link>
              </li>
            </ul>
          </div>
          <div className="lp-footer__col">
            <h2 className="lp-footer__title">{t("footer.legal")}</h2>
            <ul>
              <li>
                <Link to="/about">{t("app.about")}</Link>
              </li>
              <li>
                <Link to="/about#privacy">{t("auth.privacy_link")}</Link>
              </li>
            </ul>
          </div>
        </div>
        <div className="lp-footer__legal">
          <span>{t("footer.copyright")}</span>
          <span className="lp-notofficial">
            <Info className="icon" aria-hidden="true" />
            {t("app.not_official")}
          </span>
        </div>
      </div>
    </footer>
  );
}
