import { describe, expect, it } from "vitest";
import { db, SEED_EMAIL, WRONG_PASSWORD } from "../mocks/db";
import {
  AuthError,
  authStateOf,
  getProviders,
  getSession,
  login,
  logout,
  providerRedirectFields,
  signup,
} from "./auth";

/** allauth envelope parsing and the calls that change the session. */
describe("auth", () => {
  it("maps envelopes to session states", () => {
    expect(authStateOf({ status: 200 })).toBe("authenticated");
    expect(authStateOf({ status: 401, data: { flows: [{ id: "verify_email", is_pending: true }] } })).toBe(
      "pending_verification",
    );
    expect(authStateOf({ status: 401, data: { flows: [{ id: "login" }] } })).toBe("anonymous");
    expect(authStateOf({ status: 410 })).toBe("anonymous");
  });

  it("signs up into a pending verification", async () => {
    await expect(
      signup({ email: "new@example.com", password: "long-enough-1", turnstile_token: "" }),
    ).resolves.toBe("pending_verification");
    await expect(getSession()).resolves.toBe("pending_verification");
  });

  it("throws AuthError with codes on rejected input", async () => {
    const error = await login({ email: SEED_EMAIL, password: WRONG_PASSWORD }).catch(
      (caught: unknown) => caught,
    );
    expect(error).toBeInstanceOf(AuthError);
    expect((error as AuthError).codes).toEqual(["email_password_mismatch"]);
  });

  it("logs in and out", async () => {
    await expect(login({ email: SEED_EMAIL, password: "any-password" })).resolves.toBe("authenticated");
    expect(db.sessionEmail).toBe(SEED_EMAIL);
    await expect(logout()).resolves.toBe("anonymous");
    expect(db.sessionEmail).toBeNull();
  });

  it("reads providers and builds the redirect form with the CSRF token", async () => {
    await expect(getProviders()).resolves.toEqual([]);
    expect(providerRedirectFields("google", "http://localhost/")).toEqual({
      provider: "google",
      callback_url: "http://localhost/",
      process: "login",
      csrfmiddlewaretoken: "mock-csrf-token",
    });
  });
});
