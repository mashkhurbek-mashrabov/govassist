/** MSW service worker for `npm run dev:mock` / `VITE_USE_MOCKS=true`. */
import { setupWorker } from "msw/browser";
import { handlers } from "./handlers";

/** The browser mock worker. */
export const worker = setupWorker(...handlers);
