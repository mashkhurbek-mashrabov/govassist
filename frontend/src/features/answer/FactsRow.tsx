import { useTranslation } from "react-i18next";
import type { DeepPartialItem } from "./answerTypes";
import { CitedItem } from "./CitedItem";

/** Props of {@link FactsRow}. */
interface FactsRowProps {
  fee: DeepPartialItem | null | undefined;
  processingTime: DeepPartialItem | null | undefined;
  index: Map<string, number>;
  messageId: string;
}

/**
 * Fee and processing time. Hidden when both are null.
 *
 * @param props Fee, processing time, numbering and message id.
 * @returns The facts, or nothing.
 */
export function FactsRow({ fee, processingTime, index, messageId }: FactsRowProps) {
  const { t } = useTranslation();
  if (!fee && !processingTime) return null;
  return (
    <dl className="flex flex-wrap gap-4">
      {fee && (
        <div>
          <dt className="font-bold">{t("answer.fee")}</dt>
          <dd>
            <CitedItem item={fee} index={index} messageId={messageId} />
          </dd>
        </div>
      )}
      {processingTime && (
        <div>
          <dt className="font-bold">{t("answer.processingTime")}</dt>
          <dd>
            <CitedItem item={processingTime} index={index} messageId={messageId} />
          </dd>
        </div>
      )}
    </dl>
  );
}
