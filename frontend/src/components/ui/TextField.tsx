import { useId, type InputHTMLAttributes, type Ref } from "react";
import { fieldA11y } from "./fieldA11y";
import { FieldError } from "./FieldError";

/** Props of {@link TextField}. */
export interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  /** Visually hidden label (still announced). */
  labelHidden?: boolean;
  /** Already-translated helper text. */
  hint?: string | undefined;
  /** Already-translated error text. */
  error?: string | undefined;
  ref?: Ref<HTMLInputElement>;
}

/**
 * Labelled input with hint and error (components.md → TextField).
 *
 * @param props Label, hint, error and native input props.
 * @returns The field.
 */
export function TextField({ label, labelHidden, hint, error, ref, className, ...input }: TextFieldProps) {
  const id = useId();
  const a11y = fieldA11y(id, Boolean(hint), error);
  return (
    <div className="field">
      <label className={labelHidden ? "sr-only" : "field__label"} htmlFor={id}>
        {label}
      </label>
      <input
        id={id}
        ref={ref}
        className={["input", className].filter(Boolean).join(" ")}
        aria-invalid={a11y.invalid}
        aria-describedby={a11y.describedBy}
        {...input}
      />
      {hint && (
        <p className="field__hint" id={a11y.hintId}>
          {hint}
        </p>
      )}
      {error && <FieldError id={a11y.errorId}>{error}</FieldError>}
    </div>
  );
}
