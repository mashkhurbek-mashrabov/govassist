/** Vitest setup: jest-dom matchers, MSW server, fresh mock state and CSRF cookie per test. */
import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll, beforeEach } from "vitest";
import i18n, { DEFAULT_LANGUAGE } from "../i18n";
import { resetMockDb } from "../mocks/db";
import { MOCK_CSRF_TOKEN } from "../mocks/handlers";
import { server } from "../mocks/server";

beforeAll(() => server.listen({ onUnhandledFrame: "error" }));
beforeEach(() => {
  resetMockDb();
  document.cookie = `csrftoken=${MOCK_CSRF_TOKEN}`;
});
afterEach(async () => {
  cleanup();
  server.resetHandlers();
  // A test that switches the UI language must not leak it into the next one.
  localStorage.clear();
  await i18n.changeLanguage(DEFAULT_LANGUAGE);
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
