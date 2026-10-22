/** Props of {@link Skeleton}. */
interface SkeletonProps {
  /** Bar width in percent (100 by default) or the taller title bar. */
  width?: "80" | "60" | "40" | "title";
}

/**
 * Placeholder bar for content that is still loading or streaming. Hidden from assistive tech;
 * pair it with a visually hidden status text.
 *
 * @param props Width variant.
 * @returns The bar.
 */
export function Skeleton({ width }: SkeletonProps) {
  const modifier = width === "title" ? "skeleton--title" : width ? `skeleton--w${width}` : "";
  return <span className={["skeleton", modifier].filter(Boolean).join(" ")} aria-hidden="true" />;
}
