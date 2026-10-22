import { QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";
import { AuthError } from "../../api/auth";
import { server } from "../../mocks/server";
import { testQueryClient } from "../../test/render";
import { authErrorKey } from "./authErrors";
import { GoogleLoginButton } from "./GoogleLoginButton";
import { TurnstileWidget } from "./TurnstileWidget";

/** allauth codes → i18n keys. */
describe("authErrorKey", () => {
  it.each([
    [new AuthError(400, [{ code: "email_taken", message: "" }]), "auth.errors.emailTaken"],
    [
      new AuthError(400, [{ code: "turnstile_failed", param: "turnstile_token", message: "" }]),
      "auth.errors.turnstile",
    ],
    [
      new AuthError(400, [{ code: "email_password_mismatch", message: "" }]),
      "auth.errors.invalidCredentials",
    ],
    [new AuthError(400, [{ code: "too_many_login_attempts", message: "" }]), "auth.errors.tooManyAttempts"],
    [new AuthError(400, [{ code: "password_entirely_numeric", message: "" }]), "auth.errors.weakPassword"],
    [
      new AuthError(400, [
        { code: "unknown", message: "" },
        { code: "password_too_common", message: "" },
      ]),
      "auth.errors.weakPassword",
    ],
    [new AuthError(400, [{ code: "something_new", message: "Raw allauth text" }]), "auth.errors.generic"],
    [new Error("network"), "auth.errors.generic"],
  ])("%o → %s", (error, key) => {
    expect(authErrorKey(error)).toBe(key);
  });
});

/** Google login is a native form POST, shown only when the backend enables it. */
describe("GoogleLoginButton", () => {
  it("renders the provider-redirect form with CSRF when Google is enabled", async () => {
    server.use(
      http.get("/_allauth/browser/v1/config", () =>
        HttpResponse.json({
          status: 200,
          data: { socialaccount: { providers: [{ id: "google", name: "Google" }] } },
        }),
      ),
    );
    const { container } = render(
      <QueryClientProvider client={testQueryClient()}>
        <GoogleLoginButton />
      </QueryClientProvider>,
    );
    await screen.findByRole("button", { name: "Google orqali davom etish" });
    const form = container.querySelector("form");
    expect(form).toHaveAttribute("action", "/_allauth/browser/v1/auth/provider/redirect");
    expect(form).toHaveAttribute("method", "post");
    expect(form).toHaveFormValues({
      provider: "google",
      process: "login",
      csrfmiddlewaretoken: "mock-csrf-token",
    });
  });
});

/** Turnstile loads its script once, renders explicitly and forwards tokens. */
describe("TurnstileWidget", () => {
  it("renders the widget and reports tokens and expiry", async () => {
    const onToken = vi.fn();
    const remove = vi.fn();
    let options: Record<string, (token?: string) => void> = {};
    const { unmount } = render(<TurnstileWidget siteKey="test-key" language="uz-Latn" onToken={onToken} />);
    const script = document.head.querySelector<HTMLScriptElement>("script[src*='challenges.cloudflare.com']");
    expect(script?.src).toContain("render=explicit");
    window.turnstile = {
      render: (_element, given) => {
        options = given as typeof options;
        return "widget-1";
      },
      remove,
    };
    await act(async () => {
      script?.dispatchEvent(new Event("load"));
      await Promise.resolve();
    });
    expect(options).toMatchObject({ sitekey: "test-key", language: "uz-Latn" });
    options.callback?.("token-1");
    options["expired-callback"]?.();
    expect(onToken.mock.calls).toEqual([["token-1"], [""]]);
    unmount();
    expect(remove).toHaveBeenCalledWith("widget-1");
  });
});
