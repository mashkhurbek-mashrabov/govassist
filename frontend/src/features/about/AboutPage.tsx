import { useTranslation } from "react-i18next";

/**
 * What GovAssist is, where answers come from, and the disclaimer. Public.
 *
 * @returns The page.
 */
export function AboutPage() {
  const { t } = useTranslation();
  return (
    <>
      <h1 className="font-bold">{t("about.title")}</h1>
      <p>{t("about.body")}</p>
      <p>{t("about.sources")}</p>
      <p>{t("answer.disclaimer")}</p>
    </>
  );
}
