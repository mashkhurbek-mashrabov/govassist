import { afterEach, describe, expect, it } from "vitest";
import { readPendingQuestion, savePendingQuestion, takePendingQuestion } from "./pendingQuestion";

/** The carried question: kept once, trimmed, taken once. */
describe("pendingQuestion", () => {
  afterEach(() => sessionStorage.clear());

  it("keeps a trimmed question and ignores blank ones", () => {
    savePendingQuestion("   ");
    expect(readPendingQuestion()).toBeNull();
    savePendingQuestion("  NAMUNA savol  ");
    expect(readPendingQuestion()).toBe("NAMUNA savol");
  });

  it("caps the length", () => {
    savePendingQuestion("a".repeat(1500));
    expect(readPendingQuestion()).toHaveLength(1000);
  });

  it("is taken out once", () => {
    savePendingQuestion("NAMUNA savol");
    expect(takePendingQuestion()).toBe("NAMUNA savol");
    expect(takePendingQuestion()).toBeNull();
  });
});
