import { Plus } from "lucide-react";
import { useTranslation } from "react-i18next";
import { LinkButton } from "../../components/ui/LinkButton";
import { HistoryList } from "./HistoryList";

/**
 * History as its own page (screen 13; on desktop the sidebar shows the same rows).
 *
 * @returns The page.
 */
export function HistoryPage() {
  const { t } = useTranslation();
  return (
    <main className="page" id="main">
      <div className="section">
        <h1>{t("history.title")}</h1>
        <LinkButton to="/" icon={<Plus className="icon" aria-hidden="true" />}>
          {t("chat.new")}
        </LinkButton>
      </div>
      <HistoryList variant="page" />
    </main>
  );
}
