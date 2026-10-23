import { MessageSquare } from "lucide-react";
import type { PartialAnswer } from "./answerTypes";
import { Chips } from "./Chips";

/** Props of {@link SmalltalkCard}. */
interface SmalltalkCardProps {
  answer: PartialAnswer;
  onAsk: ((question: string) => void) | undefined;
}

/**
 * `smalltalk` card (contract v1.10): a greeting, thanks or "what can you do?" answered in the assistant's
 * voice: the speech-bubble mark, title, friendly summary and example questions as chips. Unlike `not_found`
 * there is no "rephrase" hint, no sources and no disclaimer.
 *
 * @param props The answer and the ask callback.
 * @returns The card.
 */
export function SmalltalkCard({ answer, onAsk }: SmalltalkCardProps) {
  const questions = answer.follow_up_questions?.filter(Boolean) ?? [];
  return (
    <div className="card">
      <h2 className="card__head t-h2">
        <MessageSquare className="icon" aria-hidden="true" />
        {answer.title ?? ""}
      </h2>
      <p className="t-body-lg">{answer.summary ?? ""}</p>
      <Chips questions={questions} onAsk={onAsk} />
    </div>
  );
}
