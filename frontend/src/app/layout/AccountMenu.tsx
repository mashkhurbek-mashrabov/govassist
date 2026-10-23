import { LogOut, Settings2 } from "lucide-react";
import { useId } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { useLogout } from "../../api/queries";
import { MenuPopup } from "../../components/ui/MenuPopup";
import { useMenuButton } from "../../components/ui/useMenuButton";
import { initials } from "../../lib/initials";
import { useMe } from "./meContext";

/** Focusable items: Settings, Log out. */
const ITEM_COUNT = 2;

/**
 * Account menu in the top bar (approved addition to design v1.3): a round avatar with the user's initials
 * opening the shared menu-button list: who is signed in (plain text), Settings, Log out. Log out uses the same
 * flow as the Settings page, after which `AppShell` goes to the landing page.
 *
 * @returns The menu.
 */
export function AccountMenu() {
  const { t } = useTranslation();
  const me = useMe();
  const logout = useLogout();
  const menu = useMenuButton(ITEM_COUNT);
  const { open, focusIndex, rootRef, buttonRef, itemRef, openAt, close, onButtonKeyDown } = menu;
  const id = useId();
  const buttonId = `${id}-btn`;
  const panelId = `${id}-list`;
  const name = me.display_name?.trim() || null;

  return (
    <div ref={rootRef} className="lang-menu account-menu" data-open={open ? "" : undefined}>
      <button
        ref={buttonRef}
        className="avatar-btn"
        type="button"
        id={buttonId}
        aria-label={t("account.menu_label")}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => (open ? close(false) : openAt(0))}
        onKeyDown={(event) => onButtonKeyDown(event, 0)}
      >
        <span aria-hidden="true">{initials(name, me.email)}</span>
      </button>
      <MenuPopup
        menu={menu}
        id={panelId}
        labelledBy={buttonId}
        title={t("account.menu_label")}
        className="account-menu__panel"
      >
        <div className="account-menu__who">
          {name && <span className="account-menu__name">{name}</span>}
          <span className="account-menu__email" title={me.email}>
            {me.email}
          </span>
        </div>
        <Link
          ref={itemRef(0)}
          className="lang-menu__item"
          role="menuitem"
          tabIndex={focusIndex === 0 ? 0 : -1}
          to="/settings"
          onClick={() => close(false)}
        >
          <Settings2 className="icon" aria-hidden="true" />
          <span>{t("settings.title")}</span>
        </Link>
        <button
          ref={itemRef(1)}
          className="lang-menu__item"
          type="button"
          role="menuitem"
          tabIndex={focusIndex === 1 ? 0 : -1}
          disabled={logout.isPending}
          onClick={() => logout.mutate()}
        >
          <LogOut className="icon" aria-hidden="true" />
          <span>{t("settings.logout")}</span>
        </button>
      </MenuPopup>
    </div>
  );
}
