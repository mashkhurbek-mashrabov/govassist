import { ChevronLeft } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Navigate, useNavigate } from "react-router";
import { ApiError } from "../../api/http";
import { useMaybeMe, useUpdateMe, useViewer } from "../../api/queries";
import type { Lang } from "../../api/types";
import { HOME_PATH, signedOutPath } from "../../app/guards";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { LANGUAGES } from "../../i18n";
import { PlaceFields, type Place } from "./PlaceFields";
import { placeErrors, type PlaceErrors } from "./placeErrors";

/** Number of onboarding steps. */
const STEP_COUNT = 2;

/**
 * Onboarding (screen 6): step 1 picks the UI language (applied at once), step 2 the region and district.
 * Saved together with `PATCH /me` (region and district in one request, contract v1.4).
 *
 * @returns The page.
 */
export function OnboardingPage() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { data: viewer } = useViewer();
  const me = useMaybeMe();
  const update = useUpdateMe();
  const [step, setStep] = useState(1);
  const [lang, setLang] = useState<Lang>((me?.ui_language ?? i18n.language) as Lang);
  const [place, setPlace] = useState<Place>({
    regionId: me?.region?.id ?? null,
    districtId: me?.district?.id ?? null,
  });
  const [errors, setErrors] = useState<PlaceErrors>({});
  if (!me) return <Navigate to={signedOutPath(viewer)} replace />;

  /**
   * Pick a language and show the UI in it right away.
   *
   * @param next The language.
   */
  const chooseLanguage = (next: Lang) => {
    setLang(next);
    void i18n.changeLanguage(next);
  };

  /** Validate and save, then start chatting. */
  const save = () => {
    const missing = placeErrors(place);
    setErrors(missing);
    if (Object.keys(missing).length > 0 || place.regionId === null || place.districtId === null) return;
    update.mutate(
      { ui_language: lang, region_id: place.regionId, district_id: place.districtId },
      { onSuccess: () => void navigate(HOME_PATH) },
    );
  };

  return (
    <>
      <div className="steps-indicator">
        <div className="steps-indicator__bar" aria-hidden="true">
          <span className="is-done" />
          <span className={step === 2 ? "is-done" : undefined} />
        </div>
        <span>{t("onboarding.step", { n: step, total: STEP_COUNT })}</span>
      </div>
      {step === 1 ? (
        <>
          <div className="auth__intro">
            <h1>{t("onboarding.lang_title")}</h1>
            <p className="t-muted">{t("onboarding.lang_lead")}</p>
          </div>
          <fieldset className="form fieldset-reset">
            <legend className="sr-only">{t("lang.label")}</legend>
            {LANGUAGES.map((option) => (
              <label key={option} className="radio-card">
                <input
                  type="radio"
                  name="lang"
                  checked={lang === option}
                  onChange={() => chooseLanguage(option)}
                />
                <span lang={option}>{t(`lang.${option}`)}</span>
              </label>
            ))}
          </fieldset>
          <Button variant="primary" block onClick={() => setStep(2)}>
            {t("common.next")}
          </Button>
        </>
      ) : (
        <>
          <div className="auth__intro">
            <h1>{t("onboarding.place_title")}</h1>
          </div>
          <Alert title={t("onboarding.why_title")} role="note">
            {t("onboarding.why")}
          </Alert>
          {update.isError &&
            !(update.error instanceof ApiError && update.error.code === "validation_error") && (
              <Alert tone="danger">{t("error.server")}</Alert>
            )}
          <form
            className="form"
            noValidate
            onSubmit={(event) => {
              event.preventDefault();
              save();
            }}
          >
            <PlaceFields
              value={place}
              onChange={setPlace}
              errors={{
                region: errors.region && t(errors.region),
                district: errors.district && t(errors.district),
              }}
            />
            <div className="form__actions">
              <Button
                type="submit"
                variant="primary"
                block
                busy={update.isPending}
                busyLabel={t("common.saving")}
              >
                {t("onboarding.submit")}
              </Button>
              <Button
                variant="ghost"
                block
                icon={<ChevronLeft className="icon" aria-hidden="true" />}
                onClick={() => setStep(1)}
              >
                {t("common.back")}
              </Button>
            </div>
          </form>
        </>
      )}
    </>
  );
}
