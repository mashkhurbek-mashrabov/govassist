import { useTranslation } from "react-i18next";
import type { WorkingHours } from "../../api/types";
import { openStatus } from "../../lib/openNow";
import { badgeFor } from "./officeBadge";

/** Props of {@link OpenBadge}. */
interface OpenBadgeProps {
  hours: WorkingHours[];
  now: Date;
}

/**
 * Open-now badge computed in the browser for Asia/Tashkent. The text carries the meaning, not the colour.
 *
 * @param props Working hours and the current moment.
 * @returns The badge.
 */
export function OpenBadge({ hours, now }: OpenBadgeProps) {
  const { t } = useTranslation();
  const { tone, text } = badgeFor(openStatus(hours, now), t);
  return <span className={`badge badge--${tone}`}>{text}</span>;
}
