import { Compass, House } from "lucide-react";
import { useTranslation } from "react-i18next";
import { CenterState } from "../../components/ui/CenterState";
import { LinkButton } from "../../components/ui/LinkButton";

/**
 * 404 (screen 16, not-found state).
 *
 * @returns The page.
 */
export function NotFoundPage() {
  const { t } = useTranslation();
  return (
    <CenterState icon={<Compass className="icon" aria-hidden="true" />} title={t("notfound.title")}>
      <p className="t-body-lg t-muted">{t("notfound.lead")}</p>
      <LinkButton variant="primary" to="/" icon={<House className="icon" aria-hidden="true" />}>
        {t("notfound.home")}
      </LinkButton>
    </CenterState>
  );
}
