import type { ReactNode } from "react";
import type { OfficeMatch, Source } from "../../api/types";
import { citationIndex } from "../../lib/citations";
import { AnswerHeader } from "./AnswerHeader";
import type { PartialAnswer } from "./answerTypes";
import { Disclaimer } from "./Disclaimer";
import { DocumentsCard } from "./DocumentsCard";
import { FactsRow } from "./FactsRow";
import { FollowUps } from "./FollowUps";
import { LawPointsCard } from "./LawPointsCard";
import { NotFoundCard } from "./NotFoundCard";
import { OfficeCard } from "./OfficeCard";
import { SourcesCard } from "./SourcesCard";
import { nextSkeleton } from "./skeleton";
import { StepsCard } from "./StepsCard";
import { useLeavingOffice } from "./useLeavingOffice";

/** Props of {@link AnswerView}. */
interface AnswerViewProps {
  answer: PartialAnswer;
  /** Resolved sources; empty while streaming. */
  sources: Source[];
  office: OfficeMatch | null;
  messageId: string;
  /** Text still arriving: skeletons and the caret. */
  streaming: boolean;
  /** `final` arrived: sources, disclaimer, feedback and follow-ups are shown. A stopped answer is neither. */
  complete: boolean;
  /** Feedback bar, placed after the disclaimer once the answer is final. */
  feedback?: ReactNode;
  onAsk?: ((question: string) => void) | undefined;
}

/**
 * An answer (partial or final) in schema order for its type (screens 8–11). Text is always plain text.
 * Sources, disclaimer, feedback and follow-ups are added below the content on `final`, so nothing moves.
 * A refused answer withdraws an early office card with an exit animation (contract v1.7).
 *
 * @param props Answer, sources, office, message id, streaming flag, feedback slot, ask callback.
 * @returns The answer blocks.
 */
export function AnswerView({
  answer,
  sources,
  office,
  messageId,
  streaming,
  complete,
  feedback,
  onAsk,
}: AnswerViewProps) {
  const index = citationIndex(sources);
  const type = answer.answer_type;
  const growing = streaming ? Object.keys(answer).at(-1) : undefined;
  const skeleton = nextSkeleton(answer, streaming);
  // Chips and feedback only once the stream has closed, so a click is never swallowed by the running stream.
  const done = complete && !streaming;
  const shared = { index, messageId };
  const refused = type === "not_found" || type === "off_topic";
  // Contract v1.7: a refused answer withdraws the early office card, which animates out.
  const officeSlot = useLeavingOffice(refused ? null : office);
  const officeCard = officeSlot.office && (
    <div
      className={officeSlot.leaving ? "office-leave" : "office-slot"}
      inert={officeSlot.leaving}
      onAnimationEnd={(event) => event.target === event.currentTarget && officeSlot.onLeft()}
    >
      <OfficeCard match={officeSlot.office} />
    </div>
  );

  if (refused) {
    return (
      <>
        <NotFoundCard answer={answer} onAsk={done ? onAsk : undefined} />
        {officeCard}
        <Disclaimer />
        {done && feedback}
      </>
    );
  }

  if (type === "legal") {
    return (
      <>
        <AnswerHeader answer={answer} streaming={streaming} typing={growing === "summary"} />
        <LawPointsCard points={answer.law_points} {...shared} />
        <StepsCard
          headingKey="answer.what_you_can_do"
          items={answer.steps}
          typing={growing === "steps"}
          {...shared}
        />
        {done && <SourcesCard sources={sources} messageId={messageId} />}
        {done && <Disclaimer />}
        {done && feedback}
        {done && <FollowUps questions={answer.follow_up_questions} onAsk={onAsk} />}
      </>
    );
  }

  return (
    <>
      <AnswerHeader answer={answer} streaming={streaming} typing={growing === "summary"} />
      <StepsCard
        headingKey="answer.steps"
        items={answer.steps}
        placeholder={skeleton === "steps"}
        typing={growing === "steps"}
        {...shared}
      />
      <DocumentsCard
        items={answer.documents}
        placeholder={skeleton === "documents"}
        typing={growing === "documents"}
        {...shared}
      />
      {(skeleton === "facts" || answer.fee !== undefined || answer.processing_time !== undefined) && (
        <FactsRow
          fee={answer.fee}
          processingTime={answer.processing_time}
          placeholder={skeleton === "facts"}
          {...shared}
        />
      )}
      {officeCard}
      <LawPointsCard points={answer.law_points} {...shared} />
      {done && <SourcesCard sources={sources} messageId={messageId} />}
      {done && <Disclaimer />}
      {done && feedback}
      {done && <FollowUps questions={answer.follow_up_questions} onAsk={onAsk} />}
    </>
  );
}
