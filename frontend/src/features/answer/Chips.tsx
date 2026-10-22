/** Props of {@link Chips}. */
interface ChipsProps {
  questions: (string | undefined)[];
  /** Sends the chip text as a new question; `undefined` renders nothing. */
  onAsk: ((question: string) => void) | undefined;
  disabled?: boolean;
}

/**
 * Question chips (suggestions, follow-ups, topics): buttons in a list (components.md → Chip).
 *
 * @param props Questions, ask callback and disabled flag.
 * @returns The chips, or nothing.
 */
export function Chips({ questions, onAsk, disabled }: ChipsProps) {
  const ready = questions.filter((question): question is string => Boolean(question));
  if (!onAsk || ready.length === 0) return null;
  return (
    <ul className="chips">
      {ready.map((question) => (
        <li key={question}>
          <button type="button" className="chip" disabled={disabled} onClick={() => onAsk(question)}>
            {question}
          </button>
        </li>
      ))}
    </ul>
  );
}
