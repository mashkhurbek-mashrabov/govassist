import { useId } from "react";

/** Props of {@link LogoMark}. */
interface LogoMarkProps {
  /** Accessible name when the mark stands alone; omit next to the "GovAssist" text (then it is hidden). */
  label?: string;
}

/**
 * The GovAssist mark (components.md → Logo and wordmark): a ring with a speech tail, a map-pin point and a
 * check. This is the small cut (`brand/favicon.svg`), the one for 16–32 px and the wordmark. Gradient stops
 * come from `--color-logo-start` / `--color-logo-end`, so the dark theme lightens them; gradient and mask ids
 * are unique per instance.
 *
 * @param props Optional accessible name.
 * @returns The inline SVG.
 */
export function LogoMark({ label }: LogoMarkProps) {
  const id = useId();
  const gradient = `${id}-gradient`;
  const mask = `${id}-mask`;
  const a11y = label ? { role: "img", "aria-label": label } : { "aria-hidden": true };
  return (
    <svg className="logo-mark" viewBox="0 0 64 64" focusable="false" {...a11y}>
      <defs>
        <linearGradient id={gradient} x1="4" y1="0" x2="60" y2="0" gradientUnits="userSpaceOnUse">
          <stop className="logo-mark__start" offset="0" />
          <stop className="logo-mark__end" offset="1" />
        </linearGradient>
        <mask id={mask} maskUnits="userSpaceOnUse" x="0" y="0" width="64" height="64">
          <rect width="64" height="64" fill="white" />
          <path d="M30.95 24.98L30.95 52.06A27.08 27.08 0 0 1 3.88 24.98Z" fill="black" />
        </mask>
      </defs>
      <g fill="none" stroke={`url(#${gradient})`} strokeLinecap="round" strokeLinejoin="round">
        <path d="M13.9 37.1A20.92 20.92 0 1 1 20.65 43.2L12.12 45.29Z" strokeWidth="6.4" />
        <path d="M14.77 38.29L30.95 59.99L47.73 37.49" strokeWidth="6.4" mask={`url(#${mask})`} />
        <path d="M24.92 25.23L29.11 29.42L38.22 20.43" strokeWidth="5.66" />
      </g>
    </svg>
  );
}
