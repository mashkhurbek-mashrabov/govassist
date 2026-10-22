/**
 * Build-time settings from Vite env (see `.env.example`). The mocks switch is the `__USE_MOCKS__`
 * constant from `vite.config.ts`, so normal builds drop the mock code.
 */

/** Cloudflare Turnstile site key; empty disables the widget (mocks, tests). */
export const TURNSTILE_SITE_KEY: string = import.meta.env.VITE_TURNSTILE_SITE_KEY ?? "";
