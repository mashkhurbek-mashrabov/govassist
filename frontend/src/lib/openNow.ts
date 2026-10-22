/** "Open now" for office working hours, computed in Asia/Tashkent whatever the browser's time zone. */
import type { Weekday, WorkingHours } from "../api/types";

/** Office time zone (contract §1: times of day are Asia/Tashkent). */
const OFFICE_TIME_ZONE = "Asia/Tashkent";
/** Week in display order; also used to walk forward to the next opening. */
export const WEEK: readonly Weekday[] = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];
/** Minutes in an hour. */
const MINUTES_PER_HOUR = 60;

/** Next time the office opens. */
export interface NextOpening {
  day: Weekday;
  time: string;
  today: boolean;
}

/** Whether an office is open at a given moment. */
export type OpenStatus =
  | { state: "unknown" }
  | { state: "open"; closesAt: string; forBreak: boolean }
  | { state: "break"; reopensAt: string }
  | { state: "closed"; opensAt: NextOpening | null };

/**
 * Convert `HH:MM` to minutes since midnight.
 *
 * @param time Time of day, e.g. `"09:30"`.
 * @returns Minutes since midnight.
 */
export function toMinutes(time: string): number {
  const [hours = 0, minutes = 0] = time.split(":").map(Number);
  return hours * MINUTES_PER_HOUR + minutes;
}

/**
 * Weekday and minutes since midnight in Tashkent.
 *
 * @param now The moment to convert.
 * @returns Tashkent weekday and minute of day.
 */
function tashkentClock(now: Date): { day: Weekday; minutes: number } {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: OFFICE_TIME_ZONE,
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(now);
  /** Value of one formatted part, e.g. the hour. */
  const part = (type: Intl.DateTimeFormatPartTypes) => parts.find((p) => p.type === type)?.value ?? "";
  return {
    day: part("weekday").toLowerCase() as Weekday,
    minutes: toMinutes(`${part("hour")}:${part("minute")}`),
  };
}

/**
 * Rules that apply on a weekday, earliest opening first.
 *
 * @param hours All rules.
 * @param day Weekday.
 * @returns Matching rules sorted by opening time.
 */
function rulesFor(hours: WorkingHours[], day: Weekday): WorkingHours[] {
  return hours
    .filter((rule) => rule.days.includes(day))
    .sort((a, b) => toMinutes(a.open) - toMinutes(b.open));
}

/**
 * Find the next opening after a moment, looking up to a week ahead.
 *
 * @param hours All rules.
 * @param day Current weekday.
 * @param minutes Current minute of day.
 * @returns The next opening, or `null` when the office never opens.
 */
function nextOpening(hours: WorkingHours[], day: Weekday, minutes: number): NextOpening | null {
  const laterToday = rulesFor(hours, day).find((rule) => toMinutes(rule.open) > minutes);
  if (laterToday) return { day, time: laterToday.open, today: true };
  const start = WEEK.indexOf(day);
  for (let offset = 1; offset <= WEEK.length; offset += 1) {
    const nextDay = WEEK[(start + offset) % WEEK.length] as Weekday;
    const first = rulesFor(hours, nextDay)[0];
    if (first) return { day: nextDay, time: first.open, today: false };
  }
  return null;
}

/**
 * Open/closed/lunch-break status of an office at `now`.
 *
 * @param hours The office's working hours (empty means unknown).
 * @param now The moment to check.
 * @returns The status, with the next relevant time.
 */
export function openStatus(hours: WorkingHours[], now: Date): OpenStatus {
  if (hours.length === 0) return { state: "unknown" };
  const { day, minutes } = tashkentClock(now);
  for (const rule of rulesFor(hours, day)) {
    if (minutes < toMinutes(rule.open) || minutes >= toMinutes(rule.close)) continue;
    if (!rule.break) return { state: "open", closesAt: rule.close, forBreak: false };
    const breakStart = toMinutes(rule.break.start);
    if (minutes < breakStart) return { state: "open", closesAt: rule.break.start, forBreak: true };
    if (minutes < toMinutes(rule.break.end)) return { state: "break", reopensAt: rule.break.end };
    return { state: "open", closesAt: rule.close, forBreak: false };
  }
  return { state: "closed", opensAt: nextOpening(hours, day, minutes) };
}
