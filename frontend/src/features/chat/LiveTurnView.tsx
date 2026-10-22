import { AnswerView } from "../answer/AnswerView";
import { FeedbackBar } from "./FeedbackBar";
import { ProgressLine } from "./ProgressLine";
import { TurnFailureAlert } from "./TurnFailureAlert";
import type { LiveTurn } from "./useChatStream";
import { UserBubble } from "./UserBubble";

/** Props of {@link LiveTurnView}. */
interface LiveTurnViewProps {
  turn: LiveTurn;
  onRetry: () => void;
  onAsk: (question: string) => void;
}

/**
 * The exchange in progress: question, progress, the answer filling in live, then final + feedback, or an error.
 *
 * @param props The live turn, retry and ask callbacks.
 * @returns The turn.
 */
export function LiveTurnView({ turn, onRetry, onAsk }: LiveTurnViewProps) {
  const { finalMessage } = turn;
  const answer = finalMessage?.answer ?? turn.partialAnswer;
  const messageId = turn.assistantMessageId ?? "live";
  return (
    <>
      <UserBubble text={turn.text} />
      {turn.isStreaming && <ProgressLine stage={turn.stage} sourceCount={turn.sourceCount} />}
      {(answer ?? turn.office) && (
        <AnswerView
          answer={answer ?? {}}
          sources={finalMessage?.sources ?? []}
          office={turn.office}
          messageId={messageId}
          streaming={turn.isStreaming}
          feedback={
            finalMessage &&
            turn.conversationId && <FeedbackBar conversationId={turn.conversationId} message={finalMessage} />
          }
          onAsk={onAsk}
          askDisabled={turn.isStreaming}
        />
      )}
      {turn.failure && <TurnFailureAlert failure={turn.failure} onRetry={onRetry} />}
    </>
  );
}
