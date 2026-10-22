import type { ReactNode } from "react";

/** Marker passed as an interpolation value and replaced by a React node. */
export const SLOT = "⁣slot⁣";

/** Props of {@link Interpolate}. */
interface InterpolateProps {
  /** Translated text in which {@link SLOT} marks where `children` go. */
  text: string;
  children: ReactNode;
}

/**
 * Put markup (e.g. `<strong>{email}</strong>`) inside a translated sentence without HTML in the copy.
 *
 * @param props Text with the slot marker, and the node for it.
 * @returns The sentence.
 */
export function Interpolate({ text, children }: InterpolateProps) {
  const [before, after = ""] = text.split(SLOT);
  return (
    <>
      {before}
      {children}
      {after}
    </>
  );
}
