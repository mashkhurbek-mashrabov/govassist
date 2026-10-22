import { useTranslation } from "react-i18next";
import { Link } from "react-router";

/**
 * "Check your email" after signup, while verification is pending.
 *
 * @returns The page.
 */
export function CheckEmailPage() {
  const { t } = useTranslation();
  return (
    <>
      <h1>{t("auth.checkEmail.title")}</h1>
      <p>{t("auth.checkEmail.body")}</p>
      <Link to="/login">{t("auth.backToLogin")}</Link>
    </>
  );
}
