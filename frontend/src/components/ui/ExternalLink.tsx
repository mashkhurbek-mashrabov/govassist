import { ExternalLink as ExternalIcon } from "lucide-react";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

/** Props of {@link ExternalLink}. */
interface ExternalLinkProps {
  href: string;
  children: ReactNode;
  className?: string;
}

/**
 * Link that opens in a new tab without an opener, says so to screen readers, and shows the icon.
 *
 * @param props Target, text and optional class.
 * @returns The link.
 */
export function ExternalLink({ href, children, className = "link-ext" }: ExternalLinkProps) {
  const { t } = useTranslation();
  return (
    <a className={className} href={href} target="_blank" rel="noopener noreferrer">
      {children}
      <ExternalIcon className="icon" aria-hidden="true" />
      <span className="sr-only"> {t("common.opens_new_tab")}</span>
    </a>
  );
}
