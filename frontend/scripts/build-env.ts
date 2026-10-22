/**
 * Build-time env checks for `vite.config.ts`. A real (non-mock) production build without a Turnstile site key
 * would hide the widget, and the backend would then reject every email signup, so the build fails instead.
 */

/** What the check needs to know about the Vite run. */
export interface BuildEnvInput {
  /** Vite command: `build` or `serve`. */
  command: string;
  /** Whether MSW mocks are compiled in (mock builds need no real keys). */
  useMocks: boolean;
  /** Env from `loadEnv` (`.env*` files plus `VITE_*` process variables). */
  env: Record<string, string>;
}

/**
 * Throw when a real production build lacks required public keys.
 *
 * @param input The Vite command, the mocks flag and the env.
 * @throws {Error} When `VITE_TURNSTILE_SITE_KEY` is empty in a non-mock build.
 */
export function assertBuildEnv({ command, useMocks, env }: BuildEnvInput): void {
  if (command !== "build" || useMocks) return;
  if ((env.VITE_TURNSTILE_SITE_KEY ?? "").trim() !== "") return;
  throw new Error(
    "VITE_TURNSTILE_SITE_KEY is empty. Email signup needs it: pass `--build-arg VITE_TURNSTILE_SITE_KEY=…` " +
      "to docker build, or set it in the environment (Cloudflare's test key is in .env.example).",
  );
}
