import { ChevronDown, Clock } from "lucide-react";
import { useTranslation } from "react-i18next";
import type { WorkingHours } from "../../api/types";
import { hoursTable } from "../../lib/openNow";

/** Props of {@link OfficeHours}. */
interface OfficeHoursProps {
  hours: WorkingHours[];
  now: Date;
}

/**
 * Collapsible weekly hours table: day groups, lunch break, days off, today's row in bold.
 *
 * @param props Working hours (non-empty) and the current moment.
 * @returns The details element.
 */
export function OfficeHours({ hours, now }: OfficeHoursProps) {
  const { t } = useTranslation();
  return (
    <details className="hours">
      <summary>
        <Clock className="icon" aria-hidden="true" />
        <span>{t("office.hours")}</span>
        <ChevronDown className="icon" aria-hidden="true" />
      </summary>
      <table>
        <caption className="sr-only">{t("office.hours")}</caption>
        <tbody>
          {hoursTable(hours, now).map((row) => (
            <tr key={row.from} className={row.isToday ? "is-today" : undefined}>
              <th scope="row">
                {row.from === row.to
                  ? t(`day.${row.from}`)
                  : `${t(`day.${row.from}`)} – ${t(`day.${row.to}`)}`}
              </th>
              <td>
                {row.rule ? (
                  <>
                    {row.rule.open} – {row.rule.close}
                    {row.rule.break && (
                      <span className="hours__break">
                        {t("office.break")}: {row.rule.break.start} – {row.rule.break.end}
                      </span>
                    )}
                  </>
                ) : (
                  t("office.day_off")
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </details>
  );
}
