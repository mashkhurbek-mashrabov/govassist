import { useTranslation } from "react-i18next";
import { Navigate, useNavigate } from "react-router";
import { useMaybeMe } from "../../api/queries";
import { HOME_PATH, LOGIN_PATH } from "../../app/guards";
import { ProfileForm } from "./ProfileForm";

/**
 * First-run setup: language, region, district. Required before the first question.
 *
 * @returns The page.
 */
export function OnboardingPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const me = useMaybeMe();
  if (!me) return <Navigate to={LOGIN_PATH} replace />;
  return (
    <>
      <h1>{t("onboarding.title")}</h1>
      <p>{t("onboarding.body")}</p>
      <ProfileForm me={me} submitLabel={t("onboarding.submit")} onSaved={() => void navigate(HOME_PATH)} />
    </>
  );
}
