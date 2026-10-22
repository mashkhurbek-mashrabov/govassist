import { FileText } from "lucide-react";
import { useId } from "react";
import { useTranslation } from "react-i18next";
import { Skeleton } from "../../components/ui/Skeleton";
import type { DeepPartialItem } from "./answerTypes";
import { CitedText } from "./CitedText";

/** Props of {@link DocumentsCard}. */
interface DocumentsCardProps {
  items: DeepPartialItem[] | undefined;
  index: Map<string, number>;
  messageId: string;
  placeholder?: boolean;
  typing?: boolean;
}

/**
 * "Documents to bring" checklist; ticks are visual only and not saved (components.md → DocumentsChecklist).
 *
 * @param props Items, numbering, message id, placeholder and caret flags.
 * @returns The card, or nothing when there are no documents.
 */
export function DocumentsCard({ items, index, messageId, placeholder, typing }: DocumentsCardProps) {
  const { t } = useTranslation();
  const headingId = useId();
  if (!placeholder && !items?.length) return null;
  return (
    <section className="card" aria-labelledby={headingId}>
      <h3 className="card__head" id={headingId}>
        <FileText className="icon" aria-hidden="true" />
        {t("answer.documents")}
      </h3>
      {placeholder ? (
        <div aria-hidden="true">
          <Skeleton />
          <Skeleton width="60" />
        </div>
      ) : (
        <>
          <p className="field__hint">{t("answer.documents_hint")}</p>
          <ul className="doc-list">
            {items?.map((item, position) => (
              <li key={position}>
                <label className="check">
                  <input type="checkbox" />
                  <span>
                    <CitedText
                      item={item}
                      index={index}
                      messageId={messageId}
                      typing={typing === true && position === items.length - 1}
                    />
                  </span>
                </label>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
