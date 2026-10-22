import { Compass, Scale } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Skeleton } from "../../components/ui/Skeleton";
import type { PartialAnswer } from "./answerTypes";

/** Props of {@link AnswerHeader}. */
interface AnswerHeaderProps {
  answer: PartialAnswer;
  streaming: boolean;
  /** Caret on the summary while it grows. */
  typing: boolean;
}

/**
 * Kind label, title (h2) and summary; skeleton bars until they arrive.
 *
 * @param props The answer, streaming and caret flags.
 * @returns The header.
 */
export function AnswerHeader({ answer, streaming, typing }: AnswerHeaderProps) {
  const { t } = useTranslation();
  const legal = answer.answer_type === "legal";
  const Icon = legal ? Scale : Compass;
  return (
    <header className="answer-head">
      <p className="answer-head__kind t-small">
        <Icon className="icon" aria-hidden="true" />
        {t(legal ? "answer.kind_legal" : "answer.kind_service")}
      </p>
      {answer.title ? <h2>{answer.title}</h2> : streaming && <Skeleton width="title" />}
      {answer.summary ? (
        <p className={typing ? "t-body-lg typing" : "t-body-lg"}>{answer.summary}</p>
      ) : (
        streaming && (
          <>
            <Skeleton />
            <Skeleton width="80" />
          </>
        )
      )}
    </header>
  );
}
