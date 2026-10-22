import { Link, Outlet } from "react-router";
import { useTranslation } from "react-i18next";
import { LanguageSwitcher } from "./LanguageSwitcher";

/**
 * Layout for signed-out pages: brand, language switcher, one centred column.
 *
 * @returns The layout.
 */
export function AuthLayout() {
  const { t } = useTranslation();
  return (
    <div className="mx-auto flex min-h-dvh max-w-md flex-col gap-6 p-4">
      <header className="flex items-center justify-between gap-2">
        <Link to="/" className="font-bold">
          {t("app.name")}
        </Link>
        <LanguageSwitcher />
      </header>
      <main className="flex flex-col gap-4">
        <Outlet />
      </main>
      <footer>
        <Link to="/about">{t("nav.about")}</Link>
      </footer>
    </div>
  );
}
