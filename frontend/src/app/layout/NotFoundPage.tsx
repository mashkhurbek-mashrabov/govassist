import { useTranslation } from "react-i18next";
import { Link } from "react-router";

/**
 * 404 page.
 *
 * @returns The page.
 */
export function NotFoundPage() {
  const { t } = useTranslation();
  return (
    <>
      <h1>{t("notFound.title")}</h1>
      <p>{t("notFound.body")}</p>
      <Link to="/">{t("notFound.home")}</Link>
    </>
  );
}
