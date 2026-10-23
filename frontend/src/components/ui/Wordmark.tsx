import { Link } from "react-router";
import { LogoMark } from "./LogoMark";

/** Props of {@link Wordmark}. */
interface WordmarkProps {
  to: string;
}

/**
 * The GovAssist wordmark: the logo mark (hidden from assistive tech, the text names it) and "GovAssist".
 * Not an emblem and not a sign of official status.
 *
 * @param props Link target.
 * @returns The wordmark link.
 */
export function Wordmark({ to }: WordmarkProps) {
  return (
    <Link className="wordmark" to={to}>
      <span className="wordmark__mark">
        <LogoMark />
      </span>
      GovAssist
    </Link>
  );
}
