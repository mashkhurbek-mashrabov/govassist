import { describe, expect, it } from "vitest";
import { passwordStrength } from "./passwordStrength";

/** Strength hint levels. */
describe("passwordStrength", () => {
  it.each([
    ["", 1],
    ["qwerty", 1],
    ["abcdefghij", 2],
    ["abcdefghij12", 2],
    ["Abcdefghij12", 3],
    ["parol-1234-xy", 3],
  ] as const)("%s → %s", (password, level) => {
    expect(passwordStrength(password)).toBe(level);
  });
});
