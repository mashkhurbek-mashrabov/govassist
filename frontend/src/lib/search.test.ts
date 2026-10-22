import { describe, expect, it } from "vitest";
import { matchesQuery, searchKey } from "./search";

/** Two-script combobox filtering. */
describe("search", () => {
  it("maps Cyrillic to the Latin key", () => {
    expect(searchKey("Чилонзор тумани")).toBe("chilonzor tumani");
    expect(searchKey("Ғўзор")).toBe("gozor");
    expect(searchKey("Ташкент")).toBe("tashkent");
  });

  it("ignores case and apostrophes", () => {
    expect(searchKey("Gʻuzor")).toBe("guzor");
    expect(matchesQuery("Gʻuzor tumani", "guz")).toBe(true);
  });

  it("matches across scripts", () => {
    expect(matchesQuery("Chilonzor tumani", "Чил")).toBe(true);
    expect(matchesQuery("Chilonzor tumani", "Yunus")).toBe(false);
    expect(matchesQuery("Anything", "  ")).toBe(true);
  });
});
