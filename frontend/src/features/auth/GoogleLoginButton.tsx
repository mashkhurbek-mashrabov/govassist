import { useTranslation } from "react-i18next";
import { PROVIDER_REDIRECT_URL, providerRedirectFields } from "../../api/auth";
import { useProviders } from "../../api/queries";

/** allauth provider id for Google. */
const GOOGLE = "google";

/**
 * "Continue with Google": a native form POST to allauth's provider redirect (full page navigation).
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
    <form method="post" action={PROVIDER_REDIRECT_URL}>
      {Object.entries(fields).map(([name, value]) => (
        <input key={name} type="hidden" name={name} value={value} />
      ))}
      <button type="submit" className="min-h-11 w-full border">
        {t("auth.google")}
      </button>
    </form>
  );
}
