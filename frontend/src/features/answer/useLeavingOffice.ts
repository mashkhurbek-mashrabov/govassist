import { useState } from "react";
import type { OfficeMatch } from "../../api/types";

/** What {@link useLeavingOffice} tells the answer view to render. */
export interface OfficeSlot {
  /** Office card to show: the current one, or the removed one while it animates out. */
  office: OfficeMatch | null;
  /** The card was withdrawn and is playing its exit animation. */
  leaving: boolean;
  /** Call when the exit animation ends. */
  onLeft: () => void;
}

/**
 * Whether the user asked for reduced motion (then the exit animation never runs).
 *
 * @returns `true` under `prefers-reduced-motion: reduce`.
 */
function prefersReducedMotion(): boolean {
  return (
    typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}

/**
 * Keep a withdrawn office card on screen while it animates out. Contract v1.7: the early `office` event is
 * provisional, and a refused answer drops it. Under reduced motion the card goes at once.
 *
 * @param office The office to show now (`null` once withdrawn or never sent).
 * @returns The office to render, whether it is leaving, and the animation-end callback.
 */
export function useLeavingOffice(office: OfficeMatch | null): OfficeSlot {
  const [shown, setShown] = useState(office);
  if (office !== null && office !== shown) setShown(office);
  const withdrawn = office === null && shown !== null;
  if (withdrawn && prefersReducedMotion()) setShown(null);
  return {
    office: office ?? (withdrawn ? shown : null),
    leaving: withdrawn,
    onLeft: () => setShown(null),
  };
}
