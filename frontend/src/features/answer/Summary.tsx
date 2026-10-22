import { Skeleton } from "../../components/ui/Skeleton";

/** Props of {@link Summary}. */
interface SummaryProps {
  title: string | undefined;
  summary: string | undefined;
  streaming: boolean;
}

/**
 * Answer title and 1–2 sentence summary; skeletons until they arrive.
 *
 * @param props Title, summary and streaming flag.
 * @returns The header block.
 */
export function Summary({ title, summary, streaming }: SummaryProps) {
  return (
    <header className="flex flex-col gap-1">
      {title ? <h2 className="font-bold">{title}</h2> : streaming && <Skeleton />}
      {summary ? <p>{summary}</p> : streaming && <Skeleton />}
    </header>
  );
}
