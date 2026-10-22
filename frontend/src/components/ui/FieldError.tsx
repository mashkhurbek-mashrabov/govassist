import { CircleAlert } from "lucide-react";

/** Props of {@link FieldError}. */
interface FieldErrorProps {
  id: string;
  children: string;
}

/**
 * Field error: icon + text, referenced by the field's `aria-describedby`.
 *
 * @param props Element id and message.
 * @returns The error line.
 */
export function FieldError({ id, children }: FieldErrorProps) {
  return (
    <p className="field__error" id={id}>
      <CircleAlert className="icon" aria-hidden="true" />
      <span>{children}</span>
    </p>
  );
}
