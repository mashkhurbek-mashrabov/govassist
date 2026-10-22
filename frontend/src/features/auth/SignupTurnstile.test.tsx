import { act, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { server } from "../../mocks/server";
import { renderApp } from "../../test/render";

vi.mock("../../config", () => ({ TURNSTILE_SITE_KEY: "SAMPLE-site-key" }));

/** Options the page passes to `turnstile.render`, one entry per rendered widget. */
interface RenderOptions {
  callback: (token: string) => void;
}

/** Signup with Turnstile: a failed submit spends the token, so the widget restarts for a fresh one. */
describe("SignupPage Turnstile", () => {
  const rendered: RenderOptions[] = [];
  const removed: string[] = [];
  const sentTokens: string[] = [];

  beforeEach(() => {
    rendered.length = 0;
    removed.length = 0;
    sentTokens.length = 0;
    vi.stubGlobal("turnstile", {
      render: (_element: HTMLElement, options: RenderOptions) => {
        rendered.push(options);
        return `widget-${String(rendered.length)}`;
      },
      remove: (widgetId: string) => removed.push(widgetId),
    });
    server.events.on("request:start", ({ request }) => {
      if (!request.url.endsWith("/auth/signup")) return;
      void request
        .clone()
        .json()
        .then((body: { turnstile_token: string }) => sentTokens.push(body.turnstile_token));
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    server.events.removeAllListeners();
  });

  it("clears the spent token and renders a new widget after a failed submit", async () => {
    const user = userEvent.setup();
    renderApp("/signup");
    await waitFor(() => expect(rendered).toHaveLength(1));
    const submit = screen.getByRole("button", { name: "Hisob yaratish" });
    expect(submit).toBeDisabled();
    act(() => rendered[0]?.callback("SAMPLE-token-1"));

    await user.type(screen.getByLabelText("Elektron pochta"), "yangi@example.com");
    await user.type(screen.getByLabelText("Parol", { exact: true }), "1234567890");
    await user.click(submit);
    expect(await screen.findByText("Parol faqat raqamlardan iborat boʻlmasin.")).toBeInTheDocument();

    await waitFor(() => expect(rendered).toHaveLength(2));
    expect(removed).toEqual(["widget-1"]);
    expect(screen.getByRole("button", { name: "Hisob yaratish" })).toBeDisabled();

    act(() => rendered[1]?.callback("SAMPLE-token-2"));
    await user.clear(screen.getByLabelText("Parol", { exact: true }));
    await user.type(screen.getByLabelText("Parol", { exact: true }), "yangi-Parol-123");
    await user.click(screen.getByRole("button", { name: "Hisob yaratish" }));
    await screen.findByRole("heading", { name: /pochtangizni tekshiring/i });
    expect(sentTokens).toEqual(["SAMPLE-token-1", "SAMPLE-token-2"]);
  });
});
