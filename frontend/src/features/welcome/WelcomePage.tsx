import { Building2, Compass, Info, ListChecks, MapPin, MessageSquare } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router";
import { withNext } from "../../app/guards";
import { LinkButton } from "../../components/ui/LinkButton";
import { SAMPLE_PREVIEW } from "./samplePreview";

/** The three "How it works" cards: copy key prefix and icon. */
const HOW_STEPS = [
  { key: "step_1", Icon: MessageSquare },
  { key: "step_2", Icon: ListChecks },
  { key: "step_3", Icon: MapPin },
] as const;

/**
 * Landing (screen 0): what GovAssist does, a static sample answer, how it works, and the way to sign up.
 * Keeps `?next=` for the login link.
 *
 * @returns The page.
 */
export function WelcomePage() {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  return (
    <>
      <section className="landing__hero" aria-labelledby="landing-title">
        <div className="landing__intro">
          <h1 className="t-display" id="landing-title">
            {t("landing.title")}
          </h1>
          <p className="t-body-lg t-muted">{t("landing.lead")}</p>
          <div className="landing__actions">
            <LinkButton variant="primary" to="/signup">
              {t("landing.signup")}
            </LinkButton>
            <LinkButton to={withNext("/login", params.get("next"))}>{t("landing.login")}</LinkButton>
          </div>
          <p className="t-small t-muted">{t("landing.cta_note")}</p>
        </div>
        <SamplePreview />
      </section>
      <section className="section" aria-labelledby="landing-how">
        <h2 id="landing-how">{t("landing.how_title")}</h2>
        <ol className="how">
          {HOW_STEPS.map(({ key, Icon }) => (
            <li key={key} className="card how-step">
              <span className="how-step__icon">
                <Icon className="icon" aria-hidden="true" />
              </span>
              <h3>{t(`landing.${key}_title`)}</h3>
              <p className="t-muted">{t(`landing.${key}`)}</p>
            </li>
          ))}
        </ol>
      </section>
      <p className="disclaimer">
        <Info className="icon" aria-hidden="true" />
        <span>{t("app.not_official_long")}</span>
      </p>
    </>
  );
}

/**
 * Static sample answer card (NAMUNA, contract §6). Its citation badges are decorative, not links.
 *
 * @returns The preview figure.
 */
function SamplePreview() {
  const { t } = useTranslation();
  return (
    <figure className="landing__preview" aria-labelledby="landing-preview">
      <figcaption id="landing-preview" className="t-small t-muted">
        {t("landing.preview_label")} · NAMUNA
      </figcaption>
      <div className="card card--raised" lang={SAMPLE_PREVIEW.lang}>
        <p className="answer-head__kind t-small">
          <Compass className="icon" aria-hidden="true" />
          {SAMPLE_PREVIEW.kind}
        </p>
        <p className="t-h3 t-strong">{SAMPLE_PREVIEW.title}</p>
        <ol className="steps">
          {SAMPLE_PREVIEW.steps.map((step) => (
            <li key={step.text}>
              <p>
                {step.text}
                <span className="cites">
                  <span className="cite" aria-hidden="true">
                    {step.cite}
                  </span>
                </span>
              </p>
            </li>
          ))}
        </ol>
        <div className="office__type">
          <span className="office__type-label">
            <Building2 className="icon" aria-hidden="true" />
            {SAMPLE_PREVIEW.officeType}
          </span>
          <span className="badge badge--open">{SAMPLE_PREVIEW.badge}</span>
        </div>
        <p className="office__row">
          <MapPin className="icon" aria-hidden="true" />
          <span>{SAMPLE_PREVIEW.address}</span>
        </p>
      </div>
    </figure>
  );
}
