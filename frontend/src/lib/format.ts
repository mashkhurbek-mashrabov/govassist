/** Locale-aware formatting helpers. */
import type { Lang, Weekday } from "../api/types";
import { WEEK } from "./openNow";

/** Seconds in a minute. */
const SECONDS_PER_MINUTE = 60;

/** Office and app time zone. */
const TIME_ZONE = "Asia/Tashkent";

/**
 * A `dd.mm.yyyy` formatter in Tashkent time.
 *
 * @returns The formatter.
 */
function numericDate(): Intl.DateTimeFormat {
  return new Intl.DateTimeFormat("ru", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    timeZone: TIME_ZONE,
  });
}

/**
 * Date formats per UI language. Browsers often ship no Uzbek date data, so Uzbek uses the numeric
 * `dd.mm.yyyy` form common in Uzbekistan (via the `ru` locale, which always has it).
 */
const DATE_FORMATS: Record<Lang, Intl.DateTimeFormat> = {
  "uz-Latn": numericDate(),
  "uz-Cyrl": numericDate(),
  ru: numericDate(),
  en: new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeZone: TIME_ZONE }),
};

/**
 * Format an ISO date or datetime for the UI language, in Tashkent time.
 *
 * @param value `YYYY-MM-DD` or ISO datetime.
 * @param lang UI language.
 * @returns The formatted date.
 */
export function formatDate(value: string, lang: Lang): string {
  return DATE_FORMATS[lang].format(new Date(value));
}

/**
 * Whole minutes to wait, rounded up, for `retry_after` messages.
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
