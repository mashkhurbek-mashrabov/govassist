import { Lock } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

/**
 * "Personal data in your questions is removed…" note with the privacy link (signup).
 *
 * @returns The note.
 */
export function PrivacyNote() {
  const { t } = useTranslation();
  return (
    <p className="t-small t-muted">
      <Lock className="icon" aria-hidden="true" /> {t("auth.privacy_note")}{" "}
      <Link to="/about#privacy">{t("auth.privacy_link")}</Link>
    </p>
  );
}
