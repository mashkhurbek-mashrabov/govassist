import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import type { OfficeMatch, Source } from "../../api/types";
import { citationIndex } from "../../lib/citations";
import type { PartialAnswer } from "./answerTypes";
import { CitedList } from "./CitedList";
import { Disclaimer } from "./Disclaimer";
import { FactsRow } from "./FactsRow";
import { FollowUpChips } from "./FollowUpChips";
import { LawPoints } from "./LawPoints";
import { OfficeCard } from "./OfficeCard";
import { SourcesList } from "./SourcesList";
import { Summary } from "./Summary";

/** Props of {@link AnswerView}. */
interface AnswerViewProps {
  answer: PartialAnswer;
  /** Resolved sources; empty while streaming. */
  sources: Source[];
  office: OfficeMatch | null;
  messageId: string;
  streaming: boolean;
  /** Feedback bar, placed after the disclaimer. */
  feedback?: ReactNode;
  onAsk?: ((question: string) => void) | undefined;
  askDisabled?: boolean;
}

/**
 * Render an answer (partial or final) in schema order for its type (plan §5). Text is always plain text.
 *
 * @param props Answer, sources, office, message id, streaming flag, feedback slot, ask callback.
 * @returns The answer card.
 */
export function AnswerView({
  answer,
  sources,
  office,
  messageId,
  streaming,
  feedback,
  onAsk,
  askDisabled = false,
}: AnswerViewProps) {
  const { t } = useTranslation();
  const index = citationIndex(sources);
  const type = answer.answer_type;
  const steps = (
    <CitedList
      heading={t(type === "legal" ? "answer.whatToDo" : "answer.steps")}
      items={answer.steps}
      ordered
      index={index}
      messageId={messageId}
    />
  );
  const lawPoints = <LawPoints points={answer.law_points} index={index} messageId={messageId} />;
  const followUps = (
    <FollowUpChips questions={answer.follow_up_questions} onAsk={onAsk} disabled={askDisabled} />
  );
  const isAnswer = type === "service" || type === "legal";

  return (
    <article className="flex flex-col gap-4">
      <Summary title={answer.title} summary={answer.summary} streaming={streaming} />
      {type === "service" && (
        <>
          {steps}
          <CitedList
            heading={t("answer.documents")}
            items={answer.documents}
            ordered={false}
            index={index}
            messageId={messageId}
          />
          <FactsRow
            fee={answer.fee}
            processingTime={answer.processing_time}
            index={index}
            messageId={messageId}
          />
        </>
      )}
      {type !== "legal" && office && <OfficeCard match={office} />}
      {type === "service" && lawPoints}
      {type === "legal" && (
        <>
          {lawPoints}
          {steps}
        </>
      )}
      {isAnswer && <SourcesList sources={sources} messageId={messageId} />}
      {isAnswer && <Disclaimer />}
      {feedback}
      {type !== "legal" && followUps}
    </article>
  );
}
