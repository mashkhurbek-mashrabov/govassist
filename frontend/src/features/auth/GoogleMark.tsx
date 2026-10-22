/**
 * The Google "G" mark, coloured only by the `--color-google-*` tokens (Google brand rules).
 * Slot for the official logo SVG from the design follow-up PR.
 *
 * @returns The decorative mark.
 */
export function GoogleMark() {
  return (
    <svg className="icon google-mark" viewBox="0 0 24 24" aria-hidden="true">
      <path
        className="g-blue"
        d="M22.6 12.3c0-.8-.1-1.5-.2-2.3H12v4.3h5.9a5 5 0 0 1-2.2 3.3v2.8h3.6c2.1-1.9 3.3-4.7 3.3-8.1z"
      />
      <path
        className="g-green"
        d="M12 23c3 0 5.5-1 7.3-2.7l-3.6-2.8c-1 .7-2.2 1.1-3.7 1.1-2.9 0-5.3-1.9-6.2-4.5H2.2v2.8A11 11 0 0 0 12 23z"
      />
      <path className="g-yellow" d="M5.8 14.1a6.6 6.6 0 0 1 0-4.2V7.1H2.2a11 11 0 0 0 0 9.8z" />
      <path
        className="g-red"
        d="M12 5.4c1.6 0 3.1.6 4.2 1.6l3.2-3.1A11 11 0 0 0 2.2 7.1l3.6 2.8C6.7 7.3 9.1 5.4 12 5.4z"
      />
    </svg>
  );
}
