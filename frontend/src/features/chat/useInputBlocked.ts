import { useEffect, useState } from "react";
import { useOnline } from "../../app/layout/useOnline";
import { blockedUntil } from "./inputBlock";
import type { LiveTurn } from "./useChatStream";

/**
 * Whether the composer is off: offline, or waiting out a limit (re-enables itself when it ends).
 *
 * @param turn The live turn.
 * @returns `true` while asking is not possible.
 */
export function useInputBlocked(turn: LiveTurn | null): boolean {
  const online = useOnline();
  const until = blockedUntil(turn);
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (until === null) return;
    const timer = setTimeout(() => setNow(Date.now()), Math.max(0, until - Date.now()));
    return () => clearTimeout(timer);
  }, [until]);

  return !online || (until !== null && now < until);
}
