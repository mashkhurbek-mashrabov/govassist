import { describe, expect, it } from "vitest";
import type { Source } from "../api/types";
import { citationIndex, citationNumbers, sourceAnchorId } from "./citations";

/**
 * Minimal source with only the fields numbering uses.
 *
 * @param id Source id.
 * @returns A source.
 */
function source(id: string): Source {
  return {
    id,
    kind: "law",
    title: "NAMUNA",
    publisher: "lex.uz",
    url: "https://lex.uz/",
    section: null,
    published_at: null,
    fetched_at: "2026-10-20T08:00:00Z",
  };
}

/** Citation numbering follows source order and drops unknown ids. */
describe("citations", () => {
  const index = citationIndex([source("S3"), source("S1")]);

  it("numbers sources by position, keeping original ids", () => {
    expect(index.get("S3")).toBe(1);
    expect(index.get("S1")).toBe(2);
  });

  it("drops unknown ids and duplicates and sorts", () => {
    expect(citationNumbers(["S1", "S9", "S3", "S1"], index)).toEqual([1, 2]);
  });

  it("gives no badge for items without valid sources", () => {
    expect(citationNumbers([], index)).toEqual([]);
    expect(citationNumbers(["S7"], index)).toEqual([]);
  });

  it("builds per-message anchor ids", () => {
    expect(sourceAnchorId("m1", "S1")).toBe("source-m1-S1");
  });
});
