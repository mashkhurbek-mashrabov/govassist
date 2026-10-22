import { http, HttpResponse } from "msw";
import { afterEach, describe, expect, it, vi } from "vitest";
import { server } from "../mocks/server";
import { ApiError, CSRF_HEADER, request, setUnauthorizedHandler } from "./http";

/** The HTTP client: same-origin, CSRF on unsafe methods, problem+json → ApiError, 401 hook. */
describe("request", () => {
  afterEach(() => setUnauthorizedHandler(null));

  it("sends the CSRF header on unsafe methods only", async () => {
    const seen: (string | null)[] = [];
    server.use(
      http.all("/x", ({ request: incoming }) => {
        seen.push(incoming.headers.get(CSRF_HEADER));
        return HttpResponse.json({ ok: true });
      }),
    );
    await request("/x");
    await request("/x", { method: "POST", body: {} });
    expect(seen).toEqual([null, "mock-csrf-token"]);
  });

  it("returns undefined for 204", async () => {
    server.use(http.delete("/x", () => new HttpResponse(null, { status: 204 })));
    await expect(request("/x", { method: "DELETE" })).resolves.toBeUndefined();
  });

  it("parses problem+json into ApiError", async () => {
    server.use(
      http.get("/x", () =>
        HttpResponse.json(
          { type: "about:blank", title: "Too many", status: 429, code: "rate_limited", retry_after: 60 },
          { status: 429, headers: { "Content-Type": "application/problem+json" } },
        ),
      ),
    );
    const error = await request("/x").catch((caught: unknown) => caught);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 429, code: "rate_limited", retryAfter: 60 });
  });

  it("handles non-JSON errors and calls the 401 handler", async () => {
    const onUnauthorized = vi.fn();
    setUnauthorizedHandler(onUnauthorized);
    server.use(http.get("/x", () => new HttpResponse("nope", { status: 401 })));
    const error = await request("/x").catch((caught: unknown) => caught);
    expect(error).toMatchObject({ status: 401, code: null, retryAfter: null, problem: null });
    expect(onUnauthorized).toHaveBeenCalledOnce();
  });
});
