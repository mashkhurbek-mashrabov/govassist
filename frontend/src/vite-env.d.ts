/// <reference types="vite/client" />

/** Typed Vite env variables (see `.env.example`). */
interface ImportMetaEnv {
  readonly VITE_USE_MOCKS?: string;
  readonly VITE_TURNSTILE_SITE_KEY?: string;
}

/** Build-time flag injected by `vite.config.ts` (`define`): mocks on in mode "mock" or with VITE_USE_MOCKS=true. */
declare const __USE_MOCKS__: boolean;
