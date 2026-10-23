import { Building2, Compass, MapPin } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { Lang } from "../../api/types";
import { DEFAULT_LANGUAGE, isLang } from "../../i18n";
import { PREVIEW, PREVIEW_OFFICE } from "./samplePreview";

/** CSS classes that reveal the steps one after another (`pp-step-1` …). */
const STEP_CLASSES = ["pp-step-1", "pp-step-2", "pp-step-3"] as const;

/**
 * Whether the preview is on screen, so its CSS animation only plays while someone can see it.
 *
 * @param element The preview element.
 * @returns `true` while it intersects the viewport (always `true` without IntersectionObserver).
 */
function useOnScreen(element: HTMLElement | null): boolean {
  const [visible, setVisible] = useState(typeof IntersectionObserver === "undefined");
  useEffect(() => {
    if (!element || typeof IntersectionObserver === "undefined") return;
    const observer = new IntersectionObserver(([entry]) => setVisible(entry?.isIntersecting ?? false));
    observer.observe(element);
    return () => observer.disconnect();
  }, [element]);
  return visible;
}

/**
 * The landing's auto-playing answer preview (screens.md → Landing → Streaming preview): the NAMUNA sample,
 * translated into the UI language (the office name and address stay as stored), streams in the way the chat does (question → progress → summary → steps → office), as pure CSS
 * keyframes. It is paused off screen; under reduced motion it shows the finished card. Citation badges are
 * decorative `span`s, because the page has no sources.
 *
 * @returns The preview figure.
 */
export function LandingPreview() {
  const { t, i18n } = useTranslation();
  const lang: Lang = isLang(i18n.language) ? i18n.language : DEFAULT_LANGUAGE;
  const preview = PREVIEW[lang];
  const ref = useRef<HTMLElement>(null);
  const [element, setElement] = useState<HTMLElement | null>(null);
  useEffect(() => setElement(ref.current), []);
  const playing = useOnScreen(element);
  return (
    <figure
      ref={ref}
      className="lp-preview"
      aria-labelledby="landing-preview"
      data-playing={playing ? "" : undefined}
    >
      <figcaption className="sr-only" id="landing-preview">
        {t("landing.preview_label")} · NAMUNA
      </figcaption>
      <div className="lp-preview__bar">
        <span className="answer-head__kind t-small">
          <Compass className="icon" aria-hidden="true" />
          {preview.kind}
        </span>
        <span className="lang-tag">NAMUNA</span>
      </div>
      <p className="lp-preview__q">{preview.question}</p>
      <p className="progress pp-progress" aria-hidden="true">
        <span className="progress__dots" aria-hidden="true">
          <span />
          <span />
          <span />
        </span>
        <span>{t("progress.searching")}</span>
      </p>
      <div className="pp-summary">
        <p className="t-h3 t-strong">{preview.title}</p>
        <p className="t-muted">{preview.summary}</p>
      </div>
      <ol className="steps">
        {preview.steps.map((step, index) => (
          <li key={step.text} className={STEP_CLASSES[index]}>
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
      <div className="lp-preview__office pp-office">
        <div className="office__type">
          <span className="office__type-label">
            <Building2 className="icon" aria-hidden="true" />
            {preview.officeType}
          </span>
          <span className="badge badge--open">{preview.badge}</span>
        </div>
        <p className="t-strong" lang={PREVIEW_OFFICE.lang}>
          {PREVIEW_OFFICE.name}
        </p>
        <p className="office__row">
          <MapPin className="icon" aria-hidden="true" />
          <span lang={PREVIEW_OFFICE.lang}>{PREVIEW_OFFICE.address}</span>
        </p>
      </div>
    </figure>
  );
}
