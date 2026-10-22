import { MessageSquare } from "lucide-react";
import { Link } from "react-router";

/** Props of {@link Wordmark}. */
interface WordmarkProps {
  to: string;
}

/**
 * The plain GovAssist wordmark with the neutral speech-bubble mark (no emblem, not official).
 *
 * @param props Link target.
 * @returns The wordmark link.
 */
export function Wordmark({ to }: WordmarkProps) {
  return (
    <Link className="wordmark" to={to}>
      <span className="wordmark__mark">
        <MessageSquare className="icon" aria-hidden="true" />
      </span>
      GovAssist
    </Link>
  );
}
