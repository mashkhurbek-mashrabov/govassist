import { useTranslation } from "react-i18next";
import { PROVIDER_REDIRECT_URL, providerRedirectFields } from "../../api/auth";
import { useProviders } from "../../api/queries";
import { GoogleMark } from "./GoogleMark";

/** allauth provider id for Google. */
const GOOGLE = "google";

/**
 * "Continue with Google" plus the "or" divider: a native form POST to allauth's provider redirect.
 * Hidden when Google is not enabled on the backend.
 *
 * @returns The button form, or nothing.
 */
export function GoogleLoginButton() {
  const { t } = useTranslation();
  const { data: providers } = useProviders();
  if (!providers?.some((provider) => provider.id === GOOGLE)) return null;
  const fields = providerRedirectFields(GOOGLE, `${window.location.origin}/`);
  return (
    <>
      <form method="post" action={PROVIDER_REDIRECT_URL}>
        {Object.entries(fields).map(([name, value]) => (
          <input key={name} type="hidden" name={name} value={value} />
        ))}
        <button type="submit" className="btn btn--google btn--block">
          <GoogleMark />
          <span>{t("auth.google")}</span>
        </button>
      </form>
      <p className="divider-text">{t("common.or")}</p>
    </>
  );
}
