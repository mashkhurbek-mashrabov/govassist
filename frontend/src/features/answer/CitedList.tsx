import type { DeepPartialItem } from "./answerTypes";
import { CitedItem } from "./CitedItem";

/** Props of {@link CitedList}. */
interface CitedListProps {
  heading: string;
  items: DeepPartialItem[] | undefined;
  /** `ol` for steps, `ul` for a documents checklist. */
  ordered: boolean;
  index: Map<string, number>;
  messageId: string;
}

/**
 * A titled list of cited items (steps or documents). Hidden when empty.
 *
 * @param props Heading, items, list kind, numbering and message id.
 * @returns The section, or nothing.
 */
export function CitedList({ heading, items, ordered, index, messageId }: CitedListProps) {
  if (!items?.length) return null;
  const List = ordered ? "ol" : "ul";
  return (
    <section className="flex flex-col gap-1">
      <h3 className="font-bold">{heading}</h3>
      <List className={ordered ? "list-decimal pl-6" : "list-disc pl-6"}>
        {items.map((item, position) => (
          <li key={position}>
            <CitedItem item={item} index={index} messageId={messageId} />
          </li>
        ))}
      </List>
    </section>
  );
}
