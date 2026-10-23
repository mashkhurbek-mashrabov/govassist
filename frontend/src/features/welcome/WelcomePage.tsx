import {
  BookOpen,
  ChevronDown,
  CircleCheck,
  Check,
  Gift,
  Info,
  Languages,
  MapPin,
  type LucideIcon,
} from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link, useSearchParams } from "react-router";
import { withNext } from "../../app/guards";
import { LinkButton } from "../../components/ui/LinkButton";
import { Wordmark } from "../../components/ui/Wordmark";
import { LANGUAGES } from "../../i18n";
import { LanguageMenu } from "../language/LanguageMenu";
import { LandingPreview } from "./LandingPreview";

/** Feature cards (copy key `landing.f{n}`), their icons and the text chips some of them show. */
const FEATURES: { n: number; Icon: LucideIcon; tags?: "sources" | "languages" }[] = [
  { n: 1, Icon: MapPin },
  { n: 2, Icon: BookOpen, tags: "sources" },
  { n: 3, Icon: Languages, tags: "languages" },
  { n: 4, Icon: Gift },
];
/** Publishers named on the sources feature: text only, never their logos. */
const SOURCE_TAGS = ["lex.uz", "my.gov.uz"] as const;
/** "How it works" steps (`landing.step_{n}`). */
const STEPS = [1, 2, 3] as const;
/** FAQ entries (`landing.q{n}` / `landing.a{n}`). */
const FAQ = [1, 2, 3, 4] as const;
/** Target of "See how it works". */
const HOW_ID = "landing-how";

/**
 * Landing (screen 0, design v1.2): sticky glass header with the language menu, mesh hero with the
 * auto-playing preview, features, how it works, FAQ, CTA band and footer. Keeps `?next=` for the login link.
 *
 * @returns The page.
 */
export function WelcomePage() {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  const loginTo = withNext("/login", params.get("next"));
  return (
    <div className="lp">
      <a className="skip-link" href="#main">
        {t("app.skip_to_main")}
      </a>
      <header className="lp__header">
        <Wordmark to="/welcome" />
        <LanguageMenu />
        <LinkButton variant="ghost" small to={loginTo}>
          {t("landing.login")}
        </LinkButton>
      </header>
      <main id="main" data-lang-region>
        <section className="lp-hero" aria-labelledby="landing-title">
          <div className="lp__inner">
            <div className="lp-hero__copy">
              <p className="lp-eyebrow">
                <CircleCheck className="icon" aria-hidden="true" />
                {t("landing.eyebrow")}
              </p>
              <h1 className="lp-title" id="landing-title">
                {t("landing.title")}
              </h1>
              <p className="lp-lead">{t("landing.lead")}</p>
              <div className="lp-actions">
                <LinkButton variant="primary" to="/signup">
                  {t("landing.signup")}
                </LinkButton>
                <a className="btn btn--secondary" href={`#${HOW_ID}`}>
                  <span>{t("landing.see_how")}</span>
                </a>
              </div>
              <p className="lp-note">
                <Check className="icon" aria-hidden="true" />
                {t("landing.cta_note")}
              </p>
            </div>
            <LandingPreview />
          </div>
        </section>
        <Features />
        <section className="lp-section" id={HOW_ID} aria-labelledby="landing-how-title" tabIndex={-1}>
          <div className="lp__inner">
            <div className="lp-section__head">
              <h2 id="landing-how-title">{t("landing.how_title")}</h2>
            </div>
            <ol className="lp-steps">
              {STEPS.map((n) => (
                <li key={n} className="card lp-step">
                  <h3>{t(`landing.step_${String(n)}_title`)}</h3>
                  <p className="t-muted">{t(`landing.step_${String(n)}`)}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>
        <section className="lp-section" aria-labelledby="landing-faq">
          <div className="lp__inner">
            <div className="lp-section__head">
              <h2 id="landing-faq">{t("landing.faq_title")}</h2>
            </div>
            <div className="lp-faq">
              {FAQ.map((n) => (
                <details key={n}>
                  <summary>
                    {t(`landing.q${String(n)}`)}
                    <ChevronDown className="icon" aria-hidden="true" />
                  </summary>
                  <p>{t(`landing.a${String(n)}`)}</p>
                </details>
              ))}
            </div>
          </div>
        </section>
        <section className="lp-section" aria-labelledby="landing-band">
          <div className="lp__inner">
            <div className="lp-band">
              <div className="section">
                <h2 id="landing-band">{t("landing.band_title")}</h2>
                <p className="t-body-lg">{t("landing.band_text")}</p>
              </div>
              <LinkButton className="btn--on-brand" to="/signup">
                {t("landing.signup")}
              </LinkButton>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}

/**
 * The four feature cards; the sources and languages cards carry text chips.
 *
 * @returns The features section.
 */
function Features() {
  const { t } = useTranslation();
  return (
    <section className="lp-section" aria-labelledby="landing-features">
      <div className="lp__inner">
        <div className="lp-section__head">
          <p className="lp-kicker">GovAssist</p>
          <h2 id="landing-features">{t("landing.features_title")}</h2>
        </div>
        <ul className="lp-features">
          {FEATURES.map(({ n, Icon, tags }) => (
            <li key={n} className="card lp-feature">
              <span className="lp-feature__icon">
                <Icon className="icon" aria-hidden="true" />
              </span>
              <h3>{t(`landing.f${String(n)}_title`)}</h3>
              <p className="t-muted">{t(`landing.f${String(n)}`)}</p>
              {tags === "sources" && (
                <ul className="lp-tags">
                  {SOURCE_TAGS.map((tag) => (
                    <li key={tag}>{tag}</li>
                  ))}
                </ul>
              )}
              {tags === "languages" && (
                <ul className="lp-tags">
                  {LANGUAGES.map((lang) => (
                    <li key={lang} lang={lang}>
                      {t(`lang.name.${lang}`)}
                    </li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

/**
 * Landing footer: brand and the not-official note, links, language menu (opens upwards), legal row.
 *
 * @returns The footer.
 */
function Footer() {
  const { t } = useTranslation();
  return (
    <footer className="lp-footer" data-lang-region>
      <div className="lp__inner">
        <div className="lp-footer__top">
          <div className="lp-footer__brand">
            <Wordmark to="/welcome" />
            <p className="t-muted">{t("footer.tagline")}</p>
            <p className="t-small t-muted">{t("app.not_official_long")}</p>
          </div>
          <nav className="lp-footer__nav" aria-label={t("app.about")}>
            <Link to="/about">{t("app.about")}</Link>
            <Link to="/about#privacy">{t("auth.privacy_link")}</Link>
            <Link to="/about">{t("footer.sources")}</Link>
          </nav>
          <div>
            <LanguageMenu up />
          </div>
        </div>
        <div className="lp-footer__legal">
          <span className="lp-notofficial">
            <Info className="icon" aria-hidden="true" />
            {t("app.not_official")}
          </span>
          <span>{t("footer.thesis")}</span>
        </div>
      </div>
    </footer>
  );
}
