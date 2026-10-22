import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { loadEnv } from "vite";
import { defineConfig } from "vitest/config";
import { assertBuildEnv } from "./scripts/build-env";

/** Backend origin used by the dev-server proxy when mocks are off. */
const BACKEND_ORIGIN = "http://localhost:8000";

/** Same-origin paths that the dev server forwards to Django. */
const PROXIED_PATHS = ["/api", "/_allauth", "/static", "/admin"];

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd());
  const useMocks = mode === "mock" || env.VITE_USE_MOCKS === "true";
  assertBuildEnv({ command, useMocks, env });
  return {
    plugins: [react(), tailwindcss()],
    define: {
      __USE_MOCKS__: JSON.stringify(useMocks),
    },
    server: {
      proxy: Object.fromEntries(PROXIED_PATHS.map((path) => [path, { target: BACKEND_ORIGIN }])),
    },
    build: {
      target: "es2023",
    },
    test: {
      environment: "jsdom",
      setupFiles: ["./src/test/setup.ts"],
      include: ["src/**/*.test.{ts,tsx}", "scripts/**/*.test.ts"],
      coverage: {
        provider: "v8",
        include: ["src/**/*.{ts,tsx}"],
        exclude: ["src/**/*.test.{ts,tsx}", "src/test/**", "src/main.tsx"],
      },
    },
  };
});
