import { Info, Plus, Settings2, X } from "lucide-react";
import type { Ref } from "react";
import { useTranslation } from "react-i18next";
import { NavLink } from "react-router";
import { IconButton } from "../../components/ui/IconButton";
import { LinkButton } from "../../components/ui/LinkButton";
import { Wordmark } from "../../components/ui/Wordmark";
import { LanguageMenu } from "../../features/language/LanguageMenu";
import { HistoryList } from "../../features/history/HistoryList";

/** Element id the top-bar menu button controls. */
export const SIDEBAR_ID = "sidebar";

/** Props of {@link Sidebar}. */
interface SidebarProps {
  /** History needs a complete profile (chat routes are behind onboarding). */
  showHistory: boolean;
  onClose: () => void;
  closeRef: Ref<HTMLButtonElement>;
}

/**
 * Permanent sidebar from 1280 px and the history drawer below it (components.md → Drawer).
 *
 * @param props History flag, close callback and a ref for focusing the close button.
 * @returns The sidebar.
 */
export function Sidebar({ showHistory, onClose, closeRef }: SidebarProps) {
  const { t } = useTranslation();
  return (
    <aside className="sidebar" id={SIDEBAR_ID} aria-label={t("history.title")}>
      <div className="sidebar__top">
        <Wordmark to="/" />
        <IconButton
          ref={closeRef}
          className="sidebar__close"
          label={t("common.close")}
          icon={<X className="icon" aria-hidden="true" />}
          onClick={onClose}
        />
      </div>
      <LinkButton block to="/" icon={<Plus className="icon" aria-hidden="true" />}>
        {t("chat.new")}
      </LinkButton>
      {showHistory && (
        <section className="sidebar__section" aria-labelledby="sidebar-history">
          <h2 className="sidebar__heading t-small t-muted" id="sidebar-history">
            {t("history.title")}
          </h2>
          <HistoryList variant="sidebar" />
        </section>
      )}
      <nav className="sidebar__nav" aria-label={t("chat.menu")}>
        <NavLink className="nav-link" to="/settings">
          <Settings2 className="icon" aria-hidden="true" />
          <span>{t("settings.title")}</span>
        </NavLink>
        <NavLink className="nav-link" to="/about">
          <Info className="icon" aria-hidden="true" />
          <span>{t("app.about")}</span>
        </NavLink>
        <LanguageMenu block up />
        <p className="footer-note sidebar__note">{t("app.not_official")}</p>
      </nav>
    </aside>
  );
}
