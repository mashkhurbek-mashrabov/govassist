import { describe, expect, it } from "vitest";
import { dayRanges, formatDate, retryMinutes } from "./format";

/** Formatting helpers. */
describe("format", () => {
  it("collapses consecutive days and keeps gaps", () => {
    expect(dayRanges(["fri", "mon", "tue", "wed", "thu"])).toEqual([{ from: "mon", to: "fri" }]);
    expect(dayRanges(["mon", "wed", "thu", "sun"])).toEqual([
      { from: "mon", to: "mon" },
      { from: "wed", to: "thu" },
      { from: "sun", to: "sun" },
    ]);
    expect(dayRanges([])).toEqual([]);
  });

  it("rounds retry_after up to whole minutes, at least one", () => {
    expect(retryMinutes(1260)).toBe(21);
    expect(retryMinutes(61)).toBe(2);
    expect(retryMinutes(0)).toBe(1);
  });

  it("formats dates per UI language in Tashkent time", () => {
    expect(formatDate("2026-10-20", "en")).toBe("20 Oct 2026");
    expect(formatDate("2026-10-20", "uz-Latn")).toBe("20.10.2026");
    expect(formatDate("2026-10-19T20:30:00Z", "ru")).toBe("20.10.2026");
  });
});
