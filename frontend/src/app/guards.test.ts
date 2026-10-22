import { describe, expect, it } from "vitest";
import type { Viewer } from "../api/queries";
import type { Me } from "../api/types";
import { redirectFor, safeNext, withNext } from "./guards";

/**
 * A signed-in viewer with overrides on `Me`.
 *
 * @param me Fields to override.
 * @returns The viewer.
 */
function signedIn(me: Partial<Me> = {}): Viewer {
  return {
    state: "authenticated",
    me: {
      id: "u",
      email: "u@example.com",
      email_verified: true,
      has_password: true,
      display_name: null,
      ui_language: "uz-Latn",
      region: { id: 1, name: "R" },
      district: { id: 2, name: "D" },
      profile_complete: true,
      quota: { hour_limit: 1, hour_used: 0, day_limit: 1, day_used: 0 },
      ...me,
    },
  };
}

const anonymous: Viewer = { state: "anonymous" };
const pending: Viewer = { state: "pending_verification" };

/** Guard rules for every requirement and viewer state (plan §3). */
describe("redirectFor", () => {
  it.each([
    ["guest", anonymous, null],
    ["guest", pending, null],
    ["guest", signedIn(), "/"],
    ["unverified", pending, null],
    ["unverified", signedIn({ email_verified: false }), null],
    ["unverified", signedIn(), "/"],
    ["guest", anonymous, null],
    ["auth", anonymous, "/welcome?next=%2Fsettings%3Fx%3D1"],
    ["profile", anonymous, "/welcome?next=%2Fsettings%3Fx%3D1"],
    ["auth", pending, "/check-email"],
    ["auth", signedIn({ email_verified: false }), "/check-email"],
    ["auth", signedIn({ profile_complete: false }), null],
    ["profile", signedIn({ profile_complete: false }), "/onboarding"],
    ["profile", signedIn(), null],
  ] as const)("%s with %o → %s", (requirement, viewer, expected) => {
    expect(redirectFor(viewer, requirement, "/settings?x=1")).toBe(expected);
  });
});

/** `next` is only carried when it is not the home page. */
describe("withNext", () => {
  it("keeps useful targets and drops the home page", () => {
    expect(withNext("/login", "/c/1")).toBe("/login?next=%2Fc%2F1");
    expect(withNext("/login", "/")).toBe("/login");
    expect(withNext("/login", null)).toBe("/login");
  });
});

/** Post-login redirects stay on this origin. */
describe("safeNext", () => {
  it.each([
    [null, "/"],
    ["/c/1", "/c/1"],
    ["//evil.example", "/"],
    ["/\\evil.example", "/"],
    ["https://evil.example", "/"],
  ])("%s → %s", (next, expected) => {
    expect(safeNext(next)).toBe(expected);
  });
});
