/** MSW request interception for Vitest (Node). */
import { setupServer } from "msw/node";
import { handlers } from "./handlers";

/** The Node mock server. */
export const server = setupServer(...handlers);
