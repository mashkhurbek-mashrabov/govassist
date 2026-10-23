import { Check, ChevronDown, Globe } from "lucide-react";
import { useId, useState } from "react";
import { useTranslation } from "react-i18next";
import type { Lang } from "../../api/types";
import { MenuPopup } from "../../components/ui/MenuPopup";
import { useMenuButton } from "../../components/ui/useMenuButton";
import { DEFAULT_LANGUAGE, isLang, LANGUAGES } from "../../i18n";
import { LANGUAGE_INFO } from "./languageInfo";
import { useSwitchLanguage } from "./switchLanguage";

/** Props of {@link LanguageMenu}. */
interface LanguageMenuProps {
  /** `block`: full width with the native name (sidebar); default: the compact header button. */
  block?: boolean;
  /** Open the popover above the button (footer, sidebar). */
  up?: boolean;
}

/**
 * Language menu button: globe + fixed-width code, opening a popover (a bottom sheet on phones) with the four
 * languages in their own names. Menu-button pattern: Enter / Space / ↓ open and focus the current language,
 * ↑ / ↓ / Home / End move, Enter / Space choose, Esc / Tab / an outside click close, focus returns to the
 * button. Choosing switches the UI in place and announces it in the new language.
 *
 * @param props Variant flags.
 * @returns The menu.
 */
export function LanguageMenu({ block = false, up = false }: LanguageMenuProps) {
  const { t, i18n } = useTranslation();
  const current = isLang(i18n.language) ? i18n.language : DEFAULT_LANGUAGE;
  const currentIndex = Math.max(0, LANGUAGES.indexOf(current));
  const switchTo = useSwitchLanguage();
  const menu = useMenuButton(LANGUAGES.length);
  const { open, focusIndex, rootRef, buttonRef, itemRef, openAt, close, onButtonKeyDown } = menu;
  const [announce, setAnnounce] = useState(false);
  const id = useId();
  const buttonId = `${id}-btn`;
  const panelId = `${id}-list`;

  /**
   * Choose a language, close, and announce the change.
   *
   * @param lang The chosen language.
   */
  const choose = (lang: Lang) => {
    close(true);
    if (lang === current) return;
    // Announce once the text has switched, so the message is read in the new language.
    void switchTo(lang).then(() => setAnnounce(true));
  };

  const classes = ["lang-menu", block && "lang-menu--block", up && "lang-menu--up"].filter(Boolean).join(" ");
  return (
    <div ref={rootRef} className={classes} data-open={open ? "" : undefined}>
      <button
        ref={buttonRef}
        className="lang-menu__btn"
        type="button"
        id={buttonId}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => (open ? close(false) : openAt(currentIndex))}
        onKeyDown={(event) => onButtonKeyDown(event, currentIndex)}
      >
        <Globe className="icon" aria-hidden="true" />
        {block && (
          <span className="lang-menu__label" lang={current}>
            {t(`lang.name.${current}`)}
          </span>
        )}
        <span className="sr-only">{t("lang.menu_label")}: </span>
        <span className="lang-menu__code">{LANGUAGE_INFO[current].code}</span>
        <ChevronDown className="icon" aria-hidden="true" />
      </button>
      <MenuPopup menu={menu} id={panelId} labelledBy={buttonId} title={t("lang.label")}>
        {LANGUAGES.map((lang, index) => {
          const { code, hintKey } = LANGUAGE_INFO[lang];
          return (
            <button
              key={lang}
              ref={itemRef(index)}
              type="button"
              className="lang-menu__item"
              role="menuitemradio"
              aria-checked={lang === current}
              tabIndex={index === focusIndex ? 0 : -1}
              onClick={() => choose(lang)}
            >
              <span className="lang-menu__name">
                <span lang={lang}>{t(`lang.name.${lang}`)}</span>
                {hintKey && <span className="lang-menu__hint">{t(hintKey)}</span>}
              </span>
              <span className="lang-tag" aria-hidden="true">
                {code}
              </span>
              <Check className="icon" aria-hidden="true" />
            </button>
          );
        })}
      </MenuPopup>
      <p className="sr-only" role="status">
        {announce ? t("lang.switched") : ""}
      </p>
    </div>
  );
}
