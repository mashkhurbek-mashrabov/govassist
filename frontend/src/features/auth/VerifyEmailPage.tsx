import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router";
import { verifyEmail } from "../../api/auth";
import { useAuthMutation } from "../../api/queries";
import { HOME_PATH } from "../../app/guards";
import { Alert } from "../../components/ui/Alert";
import { AuthErrorAlert } from "./AuthErrorAlert";

/**
 * Confirm the email from the link. Needs a click, so link scanners that open the page do not consume the key.
 *
 * @returns The page.
 */
export function VerifyEmailPage() {
  const { t } = useTranslation();
  const { key = "" } = useParams();
  const navigate = useNavigate();
  const mutation = useAuthMutation(verifyEmail);

  /** Verify; continue into the app when allauth also logged the user in. */
  const confirm = () =>
    mutation.mutate(key, {
      onSuccess: (viewer) => {
        if (viewer.state === "authenticated") void navigate(HOME_PATH);
      },
    });

  if (mutation.data && mutation.data.state !== "authenticated") {
    return (
      <>
        <h1>{t("auth.verify.title")}</h1>
        <Alert>{t("auth.verify.success")}</Alert>
        <Link to="/login">{t("auth.verify.loginLink")}</Link>
      </>
    );
  }

  return (
    <>
      <h1>{t("auth.verify.title")}</h1>
      <p>{t("auth.verify.body")}</p>
      <AuthErrorAlert error={mutation.error} />
      <button type="button" className="min-h-11 border" onClick={confirm} disabled={mutation.isPending}>
        {t("auth.verify.submit")}
      </button>
    </>
  );
}
