/** Switching the UI language in place (components.md → LanguageMenu → Switching). */
import { useCallback } from "react";
import { useMaybeMe, useUpdateMe } from "../../api/queries";
import type { Lang } from "../../api/types";
import i18n from "../../i18n";

/** Class that fades the translated regions while the text swaps. */
const SWITCHING_CLASS = "is-switching";
/** Token holding the fade duration; it is 0 ms under reduced motion, so the swap is then instant. */
const FADE_TOKEN = "--motion-duration-base";

/**
 * The fade duration from the design tokens.
 *
 * @returns Milliseconds (0 when unset or under reduced motion).
 */
function fadeMs(): number {
  const value = getComputedStyle(document.documentElement).getPropertyValue(FADE_TOKEN).trim();
  const ms = Number.parseFloat(value);
  return Number.isFinite(ms) ? ms : 0;
}

/**
 * Change the UI language with a short fade of every `[data-lang-region]`: fade out, swap the text, fade in.
 *
 * @param lang The new language.
 * @returns Resolves once the new language is active.
 */
export async function switchLanguage(lang: Lang): Promise<void> {
  const regions = [...document.querySelectorAll<HTMLElement>("[data-lang-region]")];
  const duration = regions.length > 0 ? fadeMs() : 0;
  if (duration > 0) {
    regions.forEach((region) => region.classList.add(SWITCHING_CLASS));
    await new Promise((resolve) => setTimeout(resolve, duration));
  }
  await i18n.changeLanguage(lang);
  regions.forEach((region) => region.classList.remove(SWITCHING_CLASS));
}

/**
 * Switch the language and, when signed in, save it with `PATCH /me`. Signed out, `i18n` keeps it in
 * localStorage (the pre-login preference).
 *
 * @returns The switch function; it resolves once the new language is active.
 */
export function useSwitchLanguage(): (lang: Lang) => Promise<void> {
  const me = useMaybeMe();
  const { mutate } = useUpdateMe();
  const signedInAs = me?.ui_language ?? null;
  return useCallback(
    (lang: Lang) => {
      if (signedInAs !== null && signedInAs !== lang) mutate({ ui_language: lang });
      return switchLanguage(lang);
    },
    [mutate, signedInAs],
  );
}
