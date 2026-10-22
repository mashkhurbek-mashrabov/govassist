import { Banknote, Hourglass } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Skeleton } from "../../components/ui/Skeleton";
import type { DeepPartialItem } from "./answerTypes";
import { CitedText } from "./CitedText";

/** Props of {@link FactsRow}. */
interface FactsRowProps {
  fee: DeepPartialItem | null | undefined;
  processingTime: DeepPartialItem | null | undefined;
  index: Map<string, number>;
  messageId: string;
  placeholder?: boolean;
}

/**
 * Fee and processing-time tiles; `null` shows "Not stated in the sources" (components.md → FactsRow).
 *
 * @param props Fee, time, numbering, message id and placeholder flag.
 * @returns The tiles.
 */
export function FactsRow({ fee, processingTime, index, messageId, placeholder }: FactsRowProps) {
  const { t } = useTranslation();
  const facts = [
    { key: "answer.fee", Icon: Banknote, item: fee },
    { key: "answer.processing_time", Icon: Hourglass, item: processingTime },
  ];
  return (
    <div className="facts">
      {facts.map(({ key, Icon, item }) => (
        <div key={key} className="card fact">
          <h3 className="fact__label t-small">
            <Icon className="icon" aria-hidden="true" />
            {t(key)}
          </h3>
          {placeholder || item === undefined ? (
            <Skeleton />
          ) : (
            <p>
              {item ? <CitedText item={item} index={index} messageId={messageId} /> : t("answer.not_stated")}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
