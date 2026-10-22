import { useId, useState, type KeyboardEvent } from "react";
import { useTranslation } from "react-i18next";

/** Contract limit for `POST /chat` text. */
export const MAX_QUESTION_LENGTH = 1000;

/** Props of {@link InputBar}. */
interface InputBarProps {
  streaming: boolean;
  onSend: (text: string) => void;
  onStop: () => void;
}

/**
 * Question box. Enter sends, Shift+Enter adds a line. While streaming, Send becomes Stop and the
 * textarea stays focusable so focus never jumps.
 *
 * @param props Streaming flag, send and stop callbacks.
 * @returns The input bar.
 */
export function InputBar({ streaming, onSend, onStop }: InputBarProps) {
  const { t } = useTranslation();
  const id = useId();
  const [text, setText] = useState("");
  const question = text.trim();

  /** Send the trimmed question and clear the box. */
  const submit = () => {
    if (streaming || question.length === 0) return;
    onSend(question);
    setText("");
  };

  /**
   * Enter submits; Shift+Enter and IME composition insert normally.
   *
   * @param event Key event from the textarea.
   */
  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key !== "Enter" || event.shiftKey || event.nativeEvent.isComposing) return;
    event.preventDefault();
    submit();
  };

  return (
    <form
      className="sticky bottom-0 mt-auto flex flex-col gap-2 border-t bg-[Canvas] py-3"
      onSubmit={(event) => {
        event.preventDefault();
        submit();
      }}
    >
      <label htmlFor={id} className="sr-only">
        {t("chat.input.label")}
      </label>
      <textarea
        id={id}
        className="min-h-11 border p-2"
        rows={2}
        maxLength={MAX_QUESTION_LENGTH}
        placeholder={t("chat.input.placeholder")}
        value={text}
        onChange={(event) => setText(event.target.value)}
        onKeyDown={onKeyDown}
      />
      {streaming ? (
        <button type="button" className="min-h-11 border" onClick={onStop}>
          {t("chat.input.stop")}
        </button>
      ) : (
        <button type="submit" className="min-h-11 border" disabled={question.length === 0}>
          {t("chat.input.send")}
        </button>
      )}
    </form>
  );
}
