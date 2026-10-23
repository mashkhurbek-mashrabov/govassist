import { Menu } from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { LinkButton } from "../../components/ui/LinkButton";
import { Wordmark } from "../../components/ui/Wordmark";
import { LanguageMenu } from "../language/LanguageMenu";
import { SECTIONS } from "./landingContent";

/** Props of {@link LandingHeader}. */
interface LandingHeaderProps {
  /** Log-in target (keeps `?next=`). */
  loginTo: string;
}

/**
 * Landing header (components.md → Landing parts → Header): wordmark, the section nav (≥ 1280 px), the
 * language menu, Kirish + Roʻyxatdan oʻtish (≥ 768 px) and a hamburger below 1280 px whose panel holds the
 * nav and both buttons. Esc closes the panel and returns focus; choosing a link closes it.
 *
 * @param props Log-in target.
 * @returns The header.
 */
export function LandingHeader({ loginTo }: LandingHeaderProps) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const toggleRef = useRef<HTMLButtonElement>(null);
  const panelId = useId();

  useEffect(() => {
    if (!open) return;
    /**
     * Esc closes the panel and gives focus back to the hamburger.
     *
     * @param event Key event.
     */
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      setOpen(false);
      toggleRef.current?.focus();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  const links = SECTIONS.map(({ id, navKey }) => (
    <a key={id} href={`#${id}`} onClick={() => setOpen(false)}>
      {t(navKey)}
    </a>
  ));
  return (
    <header className="lp__header">
      <Wordmark to="/welcome" />
      <nav className="lp-nav" aria-label={t("nav.label")}>
        {links}
      </nav>
      <LanguageMenu />
      <div className="lp-header__auth">
        <LinkButton variant="ghost" small to={loginTo}>
          {t("landing.login")}
        </LinkButton>
        <LinkButton variant="primary" small to="/signup">
          {t("landing.signup")}
        </LinkButton>
      </div>
      <button
        ref={toggleRef}
        className="icon-btn lp-nav-toggle"
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        aria-label={t("nav.open")}
        onClick={() => setOpen((value) => !value)}
      >
        <Menu className="icon" aria-hidden="true" />
      </button>
      <div className="lp-nav-panel" id={panelId} hidden={!open}>
        <nav className="lp-nav-panel__links" aria-label={t("nav.label")}>
          {links}
        </nav>
        <div className="lp-nav-panel__auth">
          <LinkButton to={loginTo}>{t("landing.login")}</LinkButton>
          <LinkButton variant="primary" to="/signup">
            {t("landing.signup")}
          </LinkButton>
        </div>
      </div>
    </header>
  );
}
