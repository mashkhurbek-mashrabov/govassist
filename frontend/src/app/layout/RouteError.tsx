import { useTranslation } from "react-i18next";
import { useRouteError } from "react-router";

/**
 * Route error boundary: a generic message plus a reload button. The error goes to the console.
 *
 * @returns The error page.
 */
export function RouteError() {
  const { t } = useTranslation();
  console.error(useRouteError());
  return (
    <main className="mx-auto flex max-w-md flex-col gap-4 p-4">
      <h1>{t("errorPage.title")}</h1>
      <p>{t("errorPage.body")}</p>
      <button type="button" className="min-h-11" onClick={() => window.location.reload()}>
        {t("errorPage.reload")}
      </button>
    </main>
  );
}
