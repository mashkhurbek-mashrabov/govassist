import { ArrowRight, Check, ChevronDown, CircleCheck, ClockAlert, FileX, MapPinX } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link, useSearchParams } from "react-router";
import { withNext } from "../../app/guards";
import { LinkButton } from "../../components/ui/LinkButton";
import { savePendingQuestion } from "../../lib/pendingQuestion";
import { AskBox, CARRY_TO } from "./AskBox";
import { Comparison } from "./Comparison";
import { LandingFooter } from "./LandingFooter";
import { LandingHeader } from "./LandingHeader";
import { LandingPreview } from "./LandingPreview";
import { FAQ, PROBLEMS, SERVICES, STEPS } from "./landingContent";

/** Icons of the three problem cards (`landing.p1` … `p3`). */
const PROBLEM_ICONS = [MapPinX, FileX, ClockAlert] as const;

/**
 * Landing (screen 0, design v1.3): why GovAssist and not an ordinary chatbot. Header with section nav and a
 * hamburger, mesh hero with the ask box and the translated streaming preview, problem framing, the
 * comparison table, popular-service tiles, how it works, FAQ, CTA band and footer. Questions from the ask
 * box, chips and tiles are carried to sign-up in sessionStorage (never the URL).
 *
 * @returns The page.
 */
export function WelcomePage() {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  return (
    <div className="lp">
      <a className="skip-link" href="#main">
        {t("app.skip_to_main")}
      </a>
      <LandingHeader loginTo={withNext("/login", params.get("next"))} />
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
              <AskBox />
              <p className="lp-note">
                <Check className="icon" aria-hidden="true" />
                {t("landing.cta_note")}
              </p>
            </div>
            <LandingPreview />
          </div>
        </section>
        <Problem />
        <section className="lp-section" id="why" aria-labelledby="landing-why" tabIndex={-1}>
          <div className="lp__inner">
            <div className="lp-section__head">
              <p className="lp-kicker">{t("nav.why")}</p>
              <h2 id="landing-why">{t("landing.compare_title")}</h2>
              <p>{t("landing.compare_lead")}</p>
            </div>
            <Comparison />
          </div>
        </section>
        <Services />
        <section className="lp-section" id="how" aria-labelledby="landing-how" tabIndex={-1}>
          <div className="lp__inner">
            <div className="lp-section__head">
              <h2 id="landing-how">{t("landing.how_title")}</h2>
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
        <section className="lp-section" id="faq" aria-labelledby="landing-faq" tabIndex={-1}>
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
      <LandingFooter />
    </div>
  );
}

/**
 * Problem framing: three pain points and the one-line answer. Qualitative only, no numbers.
 *
 * @returns The section.
 */
function Problem() {
  const { t } = useTranslation();
  return (
    <section className="lp-section lp-section--tint" aria-labelledby="landing-problem">
      <div className="lp__inner">
        <div className="lp-section__head">
          <h2 id="landing-problem">{t("landing.problem_title")}</h2>
          <p>{t("landing.problem_lead")}</p>
        </div>
        <ul className="lp-problem">
          {PROBLEMS.map((n, index) => {
            const Icon = PROBLEM_ICONS[index] ?? MapPinX;
            return (
              <li key={n} className="card">
                <span className="lp-problem__icon">
                  <Icon className="icon" aria-hidden="true" />
                </span>
                <h3>{t(`landing.p${String(n)}_title`)}</h3>
                <p className="t-muted">{t(`landing.p${String(n)}`)}</p>
              </li>
            );
          })}
        </ul>
        <p className="lp-answer">
          <CircleCheck className="icon" aria-hidden="true" />
          {t("landing.problem_answer")}
        </p>
      </div>
    </section>
  );
}

/**
 * Popular-service tiles: each is one link that carries its example question to sign-up.
 *
 * @returns The section.
 */
function Services() {
  const { t } = useTranslation();
  return (
    <section
      className="lp-section lp-section--tint"
      id="services"
      aria-labelledby="landing-services"
      tabIndex={-1}
    >
      <div className="lp__inner">
        <div className="lp-section__head">
          <h2 id="landing-services">{t("landing.services_title")}</h2>
          <p>{t("landing.services_lead")}</p>
        </div>
        <ul className="lp-services">
          {SERVICES.map(({ key, Icon }) => {
            const question = t(`service.${key}_q`);
            return (
              <li key={key}>
                <Link className="lp-service" to={CARRY_TO} onClick={() => savePendingQuestion(question)}>
                  <span className="lp-service__icon">
                    <Icon className="icon" aria-hidden="true" />
                  </span>
                  <span className="lp-service__title">{t(`service.${key}`)}</span>
                  <span className="lp-service__q">{question}</span>
                  <span className="lp-service__go">
                    {t("landing.ask_submit")}
                    <ArrowRight className="icon" aria-hidden="true" />
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
