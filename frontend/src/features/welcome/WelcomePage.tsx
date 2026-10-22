import { useTranslation } from "react-i18next";
import { Link, useSearchParams } from "react-router";
import { withNext } from "../../app/guards";

/** Landing points, in order (keys under `welcome.points`). */
const POINTS = ["steps", "office", "sources"] as const;

/**
 * Public landing page: what GovAssist does, then sign up or log in. Keeps `?next=` for the login link.
 *
 * @returns The page.
 */
export function WelcomePage() {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  return (
    <>
      <h1 className="font-bold">{t("welcome.title")}</h1>
      <p>{t("welcome.body")}</p>
      <ul className="list-disc pl-6">
        {POINTS.map((point) => (
          <li key={point}>{t(`welcome.points.${point}`)}</li>
        ))}
      </ul>
      <Link to="/signup" className="min-h-11 border p-2 text-center">
        {t("welcome.signup")}
      </Link>
      <Link to={withNext("/login", params.get("next"))} className="min-h-11 border p-2 text-center">
        {t("welcome.login")}
      </Link>
      <p className="text-sm">{t("answer.disclaimer")}</p>
    </>
  );
}
