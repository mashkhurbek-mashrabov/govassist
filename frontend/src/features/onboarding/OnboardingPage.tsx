import { ChevronLeft } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Navigate, useNavigate } from "react-router";
import { useMaybeMe, useUpdateMe, useViewer } from "../../api/queries";
import type { Lang } from "../../api/types";
import { HOME_PATH, signedOutPath } from "../../app/guards";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { LanguageCards } from "../language/LanguageCards";
import { switchLanguage } from "../language/switchLanguage";
import { PlaceFields, type Place } from "./PlaceFields";
import { placeErrors, serverPlaceErrors, type PlaceErrors } from "./placeErrors";

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
  // A 400 validation_error from the server lands on its field; anything else is a form-level alert.
  const serverErrors = update.isError ? serverPlaceErrors(update.error) : null;
  const shown = { ...errors, ...serverErrors };

  /**
   * Pick a language and show the UI in it right away.
   *
   * @param next The language.
   */
  const chooseLanguage = (next: Lang) => {
    setLang(next);
    void switchLanguage(next);
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
          <LanguageCards value={lang} onChange={chooseLanguage} />
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
          {update.isError && serverErrors === null && <Alert tone="danger">{t("error.server")}</Alert>}
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
              onChange={(next) => {
                setPlace(next);
                update.reset();
              }}
              errors={{
                region: shown.region && t(shown.region),
                district: shown.district && t(shown.district),
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
