import { describe, expect, it } from "vitest";
import { dayRanges, formatDate, relativeDay, retryMinutes } from "./format";

/** Formatting helpers. */
describe("format", () => {
  it("collapses consecutive days and keeps gaps", () => {
    expect(dayRanges(["fri", "mon", "tue", "wed", "thu"])).toEqual([{ from: "mon", to: "fri" }]);
    expect(dayRanges(["mon", "wed", "thu", "sun"])).toEqual([
      { from: "mon", to: "mon" },
      { from: "wed", to: "thu" },
      { from: "sun", to: "sun" },
    ]);
  });

  it("rounds retry_after up to whole minutes, at least one", () => {
    expect(retryMinutes(1260)).toBe(21);
    expect(retryMinutes(61)).toBe(2);
    expect(retryMinutes(0)).toBe(1);
  });

  it("formats DD.MM.YYYY in Tashkent time", () => {
    expect(formatDate("2026-10-20")).toBe("20.10.2026");
    expect(formatDate("2026-10-19T20:30:00Z")).toBe("20.10.2026");
  });

  it("labels today, yesterday and older days by the Tashkent calendar", () => {
    const now = new Date("2026-10-22T10:00:00+05:00");
    expect(relativeDay("2026-10-22T00:30:00+05:00", now)).toEqual({ kind: "today" });
    expect(relativeDay("2026-10-21T23:00:00+05:00", now)).toEqual({ kind: "yesterday" });
    expect(relativeDay("2026-10-18T09:00:00Z", now)).toEqual({ kind: "date", text: "18.10.2026" });
  });
});
