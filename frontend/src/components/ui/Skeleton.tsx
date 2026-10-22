/**
 * Placeholder block for content that is still streaming, so the layout does not jump.
 *
 * @returns A decorative, hidden-from-AT block.
 */
export function Skeleton() {
  return <div aria-hidden="true" className="h-6 animate-pulse border motion-reduce:animate-none" />;
}
