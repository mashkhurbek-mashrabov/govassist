import { describe, expect, it } from "vitest";
import { initials } from "./initials";

/** initials(): two words of the name, else the email's first letter. */
describe("initials", () => {
  it.each([
    ["Mashhurbek Mashrabov", "m@example.com", "MM"],
    ["  ali   vali  soli ", "a@example.com", "AV"],
    ["Ўктам", "u@example.com", "Ў"],
    [null, "namuna@example.com", "N"],
    ["   ", "zarina@example.com", "Z"],
  ])("%s / %s → %s", (name, email, expected) => {
    expect(initials(name, email)).toBe(expected);
  });
});
