/** Formatting helpers. Dates are `DD.MM.YYYY` in Asia/Tashkent for every UI language (copy.md). */
import type { Weekday } from "../api/types";
import { WEEK } from "./openNow";

/** Seconds in a minute. */
const SECONDS_PER_MINUTE = 60;
/** Office and app time zone. */
const TIME_ZONE = "Asia/Tashkent";
/** `DD.MM.YYYY` formatter (the `ru` locale always ships this numeric form). */
const NUMERIC_DATE = new Intl.DateTimeFormat("ru", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  timeZone: TIME_ZONE,
});

/**
 * Format an ISO date or datetime as `DD.MM.YYYY` in Tashkent time.
 *
 * @param value `YYYY-MM-DD` or ISO datetime.
 * @returns The formatted date.
 */
export function formatDate(value: string): string {
  return NUMERIC_DATE.format(new Date(value));
}

/** How a history date is shown. */
export type RelativeDay = { kind: "today" } | { kind: "yesterday" } | { kind: "date"; text: string };

/**
 * "Today" / "Yesterday" / `DD.MM.YYYY`, by Tashkent calendar day.
 *
 * @param value ISO datetime.
 * @param now The current moment.
 * @returns Which label to show.
 */
export function relativeDay(value: string, now: Date): RelativeDay {
  const day = formatDate(value);
  if (day === formatDate(now.toISOString())) return { kind: "today" };
  const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  if (day === formatDate(yesterday.toISOString())) return { kind: "yesterday" };
  return { kind: "date", text: day };
}

/**
 * Whole minutes to wait, rounded up (minutes = ⌈retry_after / 60⌉, screens.md §12).
 *
 * @param seconds `retry_after` in seconds.
 * @returns Minutes, at least 1.
 */
export function retryMinutes(seconds: number): number {
  return Math.max(1, Math.ceil(seconds / SECONDS_PER_MINUTE));
}

/** A run of consecutive weekdays, e.g. mon–fri. */
export interface DayRange {
  from: Weekday;
  to: Weekday;
}

/**
 * Collapse weekdays into consecutive runs in week order (`mon,tue,wed` → `mon–wed`).
 *
 * @param days Weekdays in any order.
 * @returns Runs; a single day has `from === to`.
 */
export function dayRanges(days: Weekday[]): DayRange[] {
  const ranges: DayRange[] = [];
  let previous = -2;
  for (const day of WEEK.filter((weekday) => days.includes(weekday))) {
    const position = WEEK.indexOf(day);
    const last = ranges.at(-1);
    if (last && position === previous + 1) last.to = day;
    else ranges.push({ from: day, to: day });
    previous = position;
  }
  return ranges;
}
