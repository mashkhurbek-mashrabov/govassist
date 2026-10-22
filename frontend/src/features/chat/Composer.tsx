import { ArrowUp, Square } from "lucide-react";
import { useId, useState, type KeyboardEvent, type RefObject } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "../../components/ui/Button";
import { FieldError } from "../../components/ui/FieldError";
import { IconButton } from "../../components/ui/IconButton";

/** Contract limit for a question. */
export const MAX_QUESTION_LENGTH = 1000;
/** The counter appears from here (components.md → InputBar). */
const COUNTER_FROM = 900;
/** Typing may go a little past the limit so the over-limit state can be shown. */
const HARD_MAX_LENGTH = 1100;

/** Props of {@link Composer}. */
interface ComposerProps {
  streaming: boolean;
  /** Offline or waiting out a limit: typing and sending are off. */
  blocked: boolean;
  onSend: (text: string) => void;
  onStop: () => void;
  /** The textarea, so the page can keep focus here after asking from a chip. */
  inputRef: RefObject<HTMLTextAreaElement | null>;
}

/**
 * Sticky question bar (components.md → InputBar): Enter sends, Shift+Enter adds a line, Send becomes Stop while
 * streaming, a counter from 900 characters and an error over 1000. Focus stays in the textarea.
 *
 * @param props Streaming and blocked flags, send and stop callbacks, the textarea ref.
 * @returns The composer.
 */
export function Composer({ streaming, blocked, onSend, onStop, inputRef }: ComposerProps) {
  const { t } = useTranslation();
  const id = useId();
  const noteId = `${id}-note`;
  const errorId = `${id}-error`;
  const [text, setText] = useState("");
  const question = text.trim();
  const tooLong = text.length > MAX_QUESTION_LENGTH;
  const canSend = !streaming && !blocked && !tooLong && question.length > 0;
  const counterClass = tooLong ? "counter counter--over" : "counter counter--warn";

  /** Send the trimmed question and clear the box. */
  const submit = () => {
    if (!canSend) return;
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
    <div className="composer">
      <form
        className="composer__inner"
        noValidate
        onSubmit={(event) => {
          event.preventDefault();
          submit();
        }}
      >
        <div className="inputbar" data-invalid={tooLong || undefined}>
          <label className="sr-only" htmlFor={id}>
            {t("chat.input_label")}
          </label>
          <textarea
            ref={inputRef}
            id={id}
            rows={1}
            maxLength={HARD_MAX_LENGTH}
            placeholder={t("chat.input_placeholder")}
            aria-describedby={tooLong ? `${noteId} ${errorId}` : noteId}
            aria-invalid={tooLong || undefined}
            disabled={blocked}
            value={text}
            onChange={(event) => setText(event.target.value)}
            onKeyDown={onKeyDown}
          />
          {streaming ? (
            <Button
              className="btn-stop"
              icon={<Square className="icon" aria-hidden="true" />}
              onClick={() => {
                onStop();
                // The Stop button disappears; keep focus in the question box.
                inputRef.current?.focus();
              }}
            >
              {t("chat.stop")}
            </Button>
          ) : (
            <IconButton
              type="submit"
              primary
              label={t("chat.send")}
              icon={<ArrowUp className="icon" aria-hidden="true" />}
              disabled={!canSend}
            />
          )}
        </div>
        {tooLong && <FieldError id={errorId}>{t("chat.too_long")}</FieldError>}
        <div className="composer__meta">
          <p className="footer-note" id={noteId}>
            {t("app.not_official")}. {t("app.may_be_wrong")}
          </p>
          {text.length >= COUNTER_FROM && (
            <span className={counterClass}>{t("chat.counter", { n: text.length })}</span>
          )}
        </div>
      </form>
    </div>
  );
}
