import { useTranslation } from "react-i18next";
import { HistoryList } from "./HistoryList";

/**
 * History as its own page (phones; wide screens show it in the sidebar too).
 *
 * @returns The page.
 */
export function HistoryPage() {
  const { t } = useTranslation();
  return (
    <>
      <h1 className="sr-only">{t("history.title")}</h1>
      <HistoryList />
    </>
  );
}
