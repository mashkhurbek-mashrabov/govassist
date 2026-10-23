import { Check, ChevronDown, Globe } from "lucide-react";
import {
  useEffect,
  useId,
  useRef,
  useState,
  useSyncExternalStore,
  type KeyboardEvent as ReactKeyboardEvent,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";
import { useTranslation } from "react-i18next";
import type { Lang } from "../../api/types";
import { DEFAULT_LANGUAGE, isLang, LANGUAGES } from "../../i18n";
import { LANGUAGE_INFO } from "./languageInfo";
import { useSwitchLanguage } from "./switchLanguage";

/** Below this width the list is a bottom sheet (components.md → LanguageMenu → Phone). */
const PHONE_QUERY = "(max-width: 767px)";

/**
 * Subscribe to the phone media query.
 *
 * @param onChange Called when it starts or stops matching.
 * @returns Unsubscribe.
 */
function subscribePhone(onChange: () => void): () => void {
  if (typeof window.matchMedia !== "function") return () => undefined;
  const query = window.matchMedia(PHONE_QUERY);
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
}

/**
 * Whether the viewport is phone-sized (false where `matchMedia` is missing, e.g. tests).
 *
 * @returns `true` below 768 px.
 */
function isPhone(): boolean {
  return typeof window.matchMedia === "function" && window.matchMedia(PHONE_QUERY).matches;
}

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
  const switchTo = useSwitchLanguage();
  const phone = useSyncExternalStore(subscribePhone, isPhone, () => false);
  const [open, setOpen] = useState(false);
  const [focusIndex, setFocusIndex] = useState(0);
  const [announce, setAnnounce] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const itemRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const id = useId();
  const buttonId = `${id}-btn`;
  const panelId = `${id}-list`;

  /**
   * Close the list.
   *
   * @param refocus Give focus back to the button (keyboard and choosing; not on an outside click).
   */
  const close = (refocus: boolean) => {
    setOpen(false);
    if (refocus) buttonRef.current?.focus();
  };

  /** Open the list with the current language focused. */
  const openList = () => {
    setFocusIndex(Math.max(0, LANGUAGES.indexOf(current)));
    setOpen(true);
  };

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

  useEffect(() => {
    if (open) itemRefs.current[focusIndex]?.focus();
  }, [open, focusIndex]);

  useEffect(() => {
    if (!open) return;
    /**
     * Close on a press outside the button and the list.
     *
     * @param event Pointer event.
     */
    const onPointerDown = (event: PointerEvent) => {
      const target = event.target as Node;
      if (rootRef.current?.contains(target) || panelRef.current?.contains(target)) return;
      setOpen(false);
    };
    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [open]);

  /**
   * Button keys: ↓ / ↑ open (Enter and Space open through the click).
   *
   * @param event Key event.
   */
  const onButtonKeyDown = (event: ReactKeyboardEvent) => {
    if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;
    event.preventDefault();
    openList();
  };

  /**
   * List keys: move, choose (native button click), close.
   *
   * @param event Key event.
   */
  const onPanelKeyDown = (event: ReactKeyboardEvent) => {
    const last = LANGUAGES.length - 1;
    const moves: Record<string, number> = {
      ArrowDown: focusIndex === last ? 0 : focusIndex + 1,
      ArrowUp: focusIndex === 0 ? last : focusIndex - 1,
      Home: 0,
      End: last,
    };
    const next = moves[event.key];
    if (next !== undefined) {
      event.preventDefault();
      setFocusIndex(next);
      return;
    }
    if (event.key === "Escape" || event.key === "Tab") {
      event.preventDefault();
      close(true);
    }
  };

  const panel = (
    <>
      {open && <div className="lang-menu__scrim" aria-hidden="true" data-portal={phone ? "" : undefined} />}
      <div
        ref={panelRef}
        className="lang-menu__panel"
        id={panelId}
        role="menu"
        aria-labelledby={buttonId}
        hidden={!open}
        tabIndex={-1}
        onKeyDown={onPanelKeyDown}
      >
        <p className="lang-menu__title" aria-hidden="true">
          {t("lang.label")}
        </p>
        {LANGUAGES.map((lang, index) => {
          const { code, hintKey } = LANGUAGE_INFO[lang];
          return (
            <button
              key={lang}
              ref={(element) => {
                itemRefs.current[index] = element;
              }}
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
      </div>
    </>
  );

  const classes = ["lang-menu", block && "lang-menu--block", up && "lang-menu--up"].filter(Boolean).join(" ");
  // On phones the open sheet goes to <body>: a glass (backdrop-filter) ancestor would trap a fixed sheet.
  const portaled: ReactNode = open && phone ? createPortal(panel, document.body) : panel;
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
        onClick={() => (open ? close(false) : openList())}
        onKeyDown={onButtonKeyDown}
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
      {portaled}
      <p className="sr-only" role="status">
        {announce ? t("lang.switched") : ""}
      </p>
    </div>
  );
}
