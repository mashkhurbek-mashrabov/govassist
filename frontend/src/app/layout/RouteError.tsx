import { CircleAlert, RefreshCw } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useRouteError } from "react-router";
import { Button } from "../../components/ui/Button";
import { CenterState } from "../../components/ui/CenterState";

/**
 * Error boundary page (screen 16, error state). The error itself goes to the console.
 *
 * @returns The page.
 */
export function RouteError() {
  const { t } = useTranslation();
  console.error(useRouteError());
  return (
    <main className="auth__main" id="main">
      <CenterState
        icon={<CircleAlert className="icon" aria-hidden="true" />}
        tone="danger"
        title={t("error_page.title")}
        role="alert"
      >
        <p className="t-body-lg t-muted">{t("error_page.lead")}</p>
        <Button
          variant="primary"
          icon={<RefreshCw className="icon" aria-hidden="true" />}
          onClick={() => window.location.reload()}
        >
          {t("error_page.reload")}
        </Button>
        <a className="btn btn--ghost" href="/">
          <span>{t("notfound.home")}</span>
        </a>
      </CenterState>
    </main>
  );
}
