import { ArrowRight } from "lucide-react";
import { useId, useState, type SubmitEvent } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router";
import { savePendingQuestion } from "../../lib/pendingQuestion";
import { POPULAR_SERVICES } from "./landingContent";

/** Where a carried question leads: sign-up (signed-in users are sent on into the app by the guard). */
export const CARRY_TO = "/signup";

/**
 * The hero's ask box and popular-question chips (components.md → AskBox, Popular chips). The question is
 * kept in sessionStorage, never in the URL, and the user goes to sign-up; after onboarding it becomes the
 * first chat message.
 *
 * @returns The form and the chips.
 */
export function AskBox() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [text, setText] = useState("");
  const id = useId();

  /**
   * Keep the question and go to sign-up (an empty box is stopped by `required`).
   *
   * @param event Submit event.
   */
  const onSubmit = (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!text.trim()) return;
    savePendingQuestion(text);
    void navigate(CARRY_TO);
  };

  return (
    <>
      <form className="lp-ask" onSubmit={onSubmit}>
        <label className="lp-ask__label" htmlFor={id}>
          {t("landing.ask_label")}
        </label>
        <div className="lp-ask__box">
          <textarea
            id={id}
            name="question"
            rows={1}
            required
            placeholder={t("landing.ask_placeholder")}
            value={text}
            onChange={(event) => setText(event.target.value)}
          />
          <button className="btn btn--primary" type="submit">
            <span>{t("landing.ask_submit")}</span>
            <ArrowRight className="icon" aria-hidden="true" />
          </button>
        </div>
      </form>
      <div className="lp-popular">
        <span className="lp-popular__label">{t("landing.popular")}</span>
        {POPULAR_SERVICES.map((key) => {
          const question = t(`service.${key}_q`);
          return (
            <Link key={key} className="chip" to={CARRY_TO} onClick={() => savePendingQuestion(question)}>
              {question}
            </Link>
          );
        })}
      </div>
    </>
  );
}
