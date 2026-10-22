import { QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";
import { AuthError } from "../../api/auth";
import { server } from "../../mocks/server";
import { testQueryClient } from "../../test/render";
import { authErrorInfo } from "./authErrors";
import { GoogleLoginButton } from "./GoogleLoginButton";
import { TurnstileWidget } from "./TurnstileWidget";

/**
 * An allauth 400 with one error.
 *
 * @param code Error code.
 * @param param Field.
 * @returns The error.
 */
function authError(code: string, param?: string): AuthError {
  return new AuthError(400, [{ code, message: "Raw allauth text", ...(param && { param }) }]);
}

/** allauth codes → copy keys and target fields (contract v1.8 §2). */
describe("authErrorInfo", () => {
  it.each([
    [
      authError("turnstile_failed", "turnstile_token"),
      { key: "error.turnstile", field: "turnstile_token", warning: false },
    ],
    [authError("email_password_mismatch"), { key: "error.login_failed", field: null, warning: false }],
    [authError("too_many_login_attempts"), { key: "error.too_many_logins", field: null, warning: true }],
    [
      authError("password_too_short", "password"),
      { key: "error.password_short", field: "password", warning: false },
    ],
    [
      authError("password_too_common", "password"),
      { key: "error.password_common", field: "password", warning: false },
    ],
    [
      authError("password_entirely_numeric", "password"),
      { key: "error.password_numeric", field: "password", warning: false },
    ],
    [
      authError("enter_current_password", "current_password"),
      { key: "error.current_password_wrong", field: "current_password", warning: false },
    ],
    [new AuthError(429, []), { key: "error.too_many_attempts", field: null, warning: true }],
    [authError("something_new"), { key: "error.server", field: null, warning: false }],
    [new Error("network"), { key: "error.server", field: null, warning: false }],
  ])("%o", (error, expected) => {
    expect(authErrorInfo(error)).toEqual(expected);
  });
});

/** Google login is a native form POST, shown only when the backend enables it. */
describe("GoogleLoginButton", () => {
  it("renders the provider-redirect form with CSRF and the 'or' divider", async () => {
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
    expect(screen.getByText("yoki")).toBeInTheDocument();
    const form = container.querySelector("form");
    expect(form).toHaveAttribute("action", "/_allauth/browser/v1/auth/provider/redirect");
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
