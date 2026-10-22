import { useTranslation } from "react-i18next";
import type { WorkingHours } from "../../api/types";
import { dayRanges } from "../../lib/format";
import { openStatus, type OpenStatus } from "../../lib/openNow";

/** Props of {@link OfficeHours}. */
interface OfficeHoursProps {
  hours: WorkingHours[];
  now: Date;
}

/**
 * Translated open/closed line for an office status.
 *
 * @param status Result of `openStatus`.
 * @param t Translation function.
 * @returns The status text.
 */
function statusText(
  status: OpenStatus,
  t: (key: string, options?: Record<string, string>) => string,
): string {
  switch (status.state) {
    case "unknown":
      return t("office.status.unknown");
    case "open":
      return t(status.forBreak ? "office.status.openUntilBreak" : "office.status.open", {
        time: status.closesAt,
      });
    case "break":
      return t("office.status.break", { time: status.reopensAt });
    case "closed":
      if (!status.opensAt) return t("office.status.closed");
      return status.opensAt.today
        ? t("office.status.opensToday", { time: status.opensAt.time })
        : t("office.status.opensOn", { day: t(`days.${status.opensAt.day}`), time: status.opensAt.time });
  }
}

/**
 * "Open now" status plus the weekly schedule.
 *
 * @param props Working hours and the current moment.
 * @returns The hours block.
 */
export function OfficeHours({ hours, now }: OfficeHoursProps) {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col gap-1">
      <p className="font-bold">{statusText(openStatus(hours, now), t)}</p>
      {hours.length > 0 && (
        <ul>
          {hours.map((rule, position) => (
            <li key={position}>
              {dayRanges(rule.days)
                .map((range) =>
                  range.from === range.to
                    ? t(`days.${range.from}`)
                    : `${t(`days.${range.from}`)}–${t(`days.${range.to}`)}`,
                )
                .join(", ")}{" "}
              {rule.open}–{rule.close}
              {rule.break && ` (${t("office.break", { start: rule.break.start, end: rule.break.end })})`}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
