import type { ReactNode } from "react";
import { createPortal } from "react-dom";
import type { MenuButton } from "./useMenuButton";

/** Props of {@link MenuPopup}. */
interface MenuPopupProps {
  menu: MenuButton;
  /** Id of the panel (the button's `aria-controls`). */
  id: string;
  /** Id of the button that names the menu. */
  labelledBy: string;
  /** Sheet title shown on phones (decorative; the button names the menu). */
  title: string;
  /** Extra class on the panel (it may be portaled out of the menu's root on phones). */
  className?: string;
  children: ReactNode;
}

/**
 * The list of a menu button (components.md → LanguageMenu): a solid popover under the button, a bottom sheet
 * over a scrim on phones. On phones the open sheet is portaled to `<body>`, because a glass
 * (`backdrop-filter`) ancestor would trap a fixed sheet.
 *
 * @param props The menu state, ids, sheet title, optional panel class and the items.
 * @returns The panel (and scrim).
 */
export function MenuPopup({ menu, id, labelledBy, title, className, children }: MenuPopupProps) {
  const { open, phone, panelRef, onPanelKeyDown } = menu;
  const panel = (
    <>
      {open && <div className="lang-menu__scrim" aria-hidden="true" data-portal={phone ? "" : undefined} />}
      <div
        ref={panelRef}
        className={className ? `lang-menu__panel ${className}` : "lang-menu__panel"}
        id={id}
        role="menu"
        aria-labelledby={labelledBy}
        hidden={!open}
        tabIndex={-1}
        onKeyDown={onPanelKeyDown}
      >
        <p className="lang-menu__title" aria-hidden="true">
          {title}
        </p>
        {children}
      </div>
    </>
  );
  return open && phone ? createPortal(panel, document.body) : panel;
}
