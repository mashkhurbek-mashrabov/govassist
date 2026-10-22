import { useId, type InputHTMLAttributes, type ReactNode, type Ref } from "react";

/** Props of {@link TextField}. */
export interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  /** Already-translated error text. */
  error?: string | undefined;
  /** Already-translated helper text. */
  hint?: string;
  ref?: Ref<HTMLInputElement>;
  /** Rendered after the input (e.g. a show-password toggle). */
  children?: ReactNode;
}

/**
 * Labelled text input with an accessible error and hint.
 *
 * @param props Label, error, hint and native input props.
 * @returns The field.
 */
export function TextField({ label, error, hint, children, ref, ...input }: TextFieldProps) {
  const id = useId();
  const hintId = `${id}-hint`;
  const errorId = `${id}-error`;
  const describedBy = [hint && hintId, error && errorId].filter(Boolean).join(" ") || undefined;
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id}>{label}</label>
      <div className="flex gap-2">
        <input
          id={id}
          ref={ref}
          className="min-h-11 grow border px-2"
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          {...input}
        />
        {children}
      </div>
      {hint && <p id={hintId}>{hint}</p>}
      {error && (
        <p id={errorId} role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
