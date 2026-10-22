import { useEffect, useLayoutEffect, useRef } from "react";

/** Cloudflare Turnstile script (explicit rendering). Allowed by the SPA's CSP. */
const TURNSTILE_SCRIPT = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";

/** The subset of the Turnstile API the widget uses. */
interface TurnstileApi {
  render: (element: HTMLElement, options: Record<string, unknown>) => string;
  remove: (widgetId: string) => void;
}

declare global {
  interface Window {
    turnstile?: TurnstileApi;
  }
}

/** Shared script load, so remounts do not inject the script twice. */
let scriptPromise: Promise<TurnstileApi> | null = null;

/**
 * Load the Turnstile script once.
 *
 * @returns The Turnstile API.
 */
function loadTurnstile(): Promise<TurnstileApi> {
  scriptPromise ??= new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = TURNSTILE_SCRIPT;
    script.async = true;
    script.onload = () =>
      window.turnstile ? resolve(window.turnstile) : reject(new Error("Turnstile missing"));
    script.onerror = () => reject(new Error("Turnstile script failed to load"));
    document.head.append(script);
  });
  return scriptPromise;
}

/** Props of {@link TurnstileWidget}. */
interface TurnstileWidgetProps {
  siteKey: string;
  language: string;
  /** Called with a fresh token, or `""` when it expires. */
  onToken: (token: string) => void;
}

/**
 * Cloudflare Turnstile challenge for signup.
 *
 * @param props Site key, language and token callback.
 * @returns The widget container.
 */
export function TurnstileWidget({ siteKey, language, onToken }: TurnstileWidgetProps) {
  const container = useRef<HTMLDivElement>(null);
  const tokenCallback = useRef(onToken);
  useLayoutEffect(() => {
    tokenCallback.current = onToken;
  });

  useEffect(() => {
    let widgetId: string | null = null;
    let cancelled = false;
    loadTurnstile()
      .then((turnstile) => {
        if (cancelled || !container.current) return;
        widgetId = turnstile.render(container.current, {
          sitekey: siteKey,
          language,
          callback: (token: string) => tokenCallback.current(token),
          "expired-callback": () => tokenCallback.current(""),
        });
      })
      .catch((error: unknown) => console.error(error));
    return () => {
      cancelled = true;
      if (widgetId) window.turnstile?.remove(widgetId);
    };
  }, [siteKey, language]);

  return <div ref={container} />;
}
