import { describe, expect, it } from "vitest";
import { assertBuildEnv } from "./build-env";

/** assertBuildEnv(): a real production build must carry the Turnstile site key. */
describe("assertBuildEnv", () => {
  it("fails a real build without the Turnstile key", () => {
    expect(() => assertBuildEnv({ command: "build", useMocks: false, env: {} })).toThrow(
      /VITE_TURNSTILE_SITE_KEY/,
    );
    expect(() =>
      assertBuildEnv({ command: "build", useMocks: false, env: { VITE_TURNSTILE_SITE_KEY: " " } }),
    ).toThrow(/VITE_TURNSTILE_SITE_KEY/);
  });

  it("passes a real build with the key, mock builds and the dev server", () => {
    const key = { VITE_TURNSTILE_SITE_KEY: "1x00000000000000000000AA" };
    expect(() => assertBuildEnv({ command: "build", useMocks: false, env: key })).not.toThrow();
    expect(() => assertBuildEnv({ command: "build", useMocks: true, env: {} })).not.toThrow();
    expect(() => assertBuildEnv({ command: "serve", useMocks: false, env: {} })).not.toThrow();
  });
});
