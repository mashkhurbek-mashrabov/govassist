import { describe, expect, it } from "vitest";
import type { WorkingHours } from "../api/types";
import { openStatus, toMinutes } from "./openNow";

/** Contract §6 sample hours: weekdays with a lunch break, a short Saturday, closed on Sunday. */
const HOURS: WorkingHours[] = [
  {
    days: ["mon", "tue", "wed", "thu", "fri"],
    open: "09:00",
    close: "18:00",
    break: { start: "13:00", end: "14:00" },
  },
  { days: ["sat"], open: "09:00", close: "13:00", break: null },
];

/**
 * Build a UTC instant for a Tashkent wall-clock time (UTC+5, no DST).
 *
 * @param isoDate Tashkent calendar date (`2026-10-22` is a Thursday).
 * @param time Tashkent time `HH:MM`.
 * @returns The instant.
 */
function tashkent(isoDate: string, time: string): Date {
  return new Date(`${isoDate}T${time}:00+05:00`);
}

/** openStatus(): every branch of the open/break/closed logic, independent of the runner's time zone. */
describe("openStatus", () => {
  it("is unknown without hours", () => {
    expect(openStatus([], new Date())).toEqual({ state: "unknown" });
  });

  it("is open before lunch and points at the break", () => {
    expect(openStatus(HOURS, tashkent("2026-10-22", "10:15"))).toEqual({
      state: "open",
      closesAt: "13:00",
      forBreak: true,
    });
  });

  it("reports the lunch break and when it ends", () => {
    expect(openStatus(HOURS, tashkent("2026-10-22", "13:30"))).toEqual({
      state: "break",
      reopensAt: "14:00",
    });
  });

  it("is open after lunch until closing", () => {
    expect(openStatus(HOURS, tashkent("2026-10-22", "14:00"))).toEqual({
      state: "open",
      closesAt: "18:00",
      forBreak: false,
    });
  });

  it("is open on a rule without a break", () => {
    expect(openStatus(HOURS, tashkent("2026-10-24", "09:00"))).toEqual({
      state: "open",
      closesAt: "13:00",
      forBreak: false,
    });
  });

  it("opens later today when it is early", () => {
    expect(openStatus(HOURS, tashkent("2026-10-22", "07:59"))).toEqual({
      state: "closed",
      opensAt: { day: "thu", time: "09:00", today: true },
    });
  });

  it("treats the closing minute as closed and finds the next day", () => {
    expect(openStatus(HOURS, tashkent("2026-10-23", "18:00"))).toEqual({
      state: "closed",
      opensAt: { day: "sat", time: "09:00", today: false },
    });
  });

  it("skips a closed Sunday", () => {
    expect(openStatus(HOURS, tashkent("2026-10-24", "15:00"))).toEqual({
      state: "closed",
      opensAt: { day: "mon", time: "09:00", today: false },
    });
  });

  it("uses Tashkent time, not UTC (23:30 UTC Friday is Saturday morning)", () => {
    expect(openStatus(HOURS, new Date("2026-10-23T23:30:00Z")).state).toBe("closed");
    expect(openStatus(HOURS, new Date("2026-10-24T04:30:00Z"))).toMatchObject({ state: "open" });
  });

  it("returns no next opening when no rule has days", () => {
    const never: WorkingHours[] = [{ days: [], open: "09:00", close: "18:00", break: null }];
    expect(openStatus(never, tashkent("2026-10-22", "10:00"))).toEqual({ state: "closed", opensAt: null });
  });
});

/** toMinutes(): HH:MM parsing. */
describe("toMinutes", () => {
  it("converts HH:MM", () => {
    expect(toMinutes("13:45")).toBe(825);
  });
});
