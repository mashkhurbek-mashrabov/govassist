/** Vitest setup: jest-dom matchers, MSW server, fresh mock state and CSRF cookie per test. */
import "@testing-library/jest-dom/vitest";
import { cleanup, configure } from "@testing-library/react";
import { afterAll, afterEach, beforeAll, beforeEach } from "vitest";
import "../i18n";
import { resetMockDb } from "../mocks/db";
import { MOCK_CSRF_TOKEN } from "../mocks/handlers";
import { server } from "../mocks/server";

// Full-route tests stream ~60 SSE frames through jsdom; 1 s (the default) is tight on a loaded CI runner.
configure({ asyncUtilTimeout: 3000 });

beforeAll(() => server.listen({ onUnhandledFrame: "error" }));
beforeEach(() => {
  resetMockDb();
  document.cookie = `csrftoken=${MOCK_CSRF_TOKEN}`;
});
afterEach(() => {
  cleanup();
  server.resetHandlers();
});
afterAll(() => server.close());

// jsdom has no <dialog> modal API; a minimal stand-in keeps ConfirmDialog testable.
if (!("showModal" in HTMLDialogElement.prototype)) {
  Object.assign(HTMLDialogElement.prototype, {
    showModal(this: HTMLDialogElement) {
      this.open = true;
    },
    close(this: HTMLDialogElement) {
      this.open = false;
    },
  });
}
