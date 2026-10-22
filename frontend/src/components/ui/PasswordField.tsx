import { Eye, EyeOff } from "lucide-react";
import { useId, useState, type ChangeEvent, type InputHTMLAttributes, type Ref } from "react";
import { useTranslation } from "react-i18next";
import { passwordStrength } from "../../lib/passwordStrength";
import { fieldA11y } from "./fieldA11y";
import { FieldError } from "./FieldError";
import { IconButton } from "./IconButton";

/** Strength level → copy key. */
const STRENGTH_KEYS = {
  1: "auth.strength_weak",
  2: "auth.strength_fair",
  3: "auth.strength_strong",
} as const;

/** Props of {@link PasswordField}. */
interface PasswordFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label: string;
  hint?: string | undefined;
  error?: string | undefined;
  /** Show the 3-segment strength meter and its live text (signup, reset, new password). */
  showStrength?: boolean;
  ref?: Ref<HTMLInputElement>;
}

/**
 * Password input with a show/hide toggle and an optional strength hint (components.md → PasswordField).
 *
 * @param props Label, hint, error, strength flag and native input props.
 * @returns The field.
 */
export function PasswordField({
  label,
  hint,
  error,
  showStrength,
  ref,
  onChange,
  ...input
}: PasswordFieldProps) {
  const { t } = useTranslation();
  const id = useId();
  const [visible, setVisible] = useState(false);
  const [value, setValue] = useState("");
  const strengthId = `${id}-strength`;
  const showMeter = showStrength === true && value !== "";
  const a11y = fieldA11y(id, Boolean(hint), error, showMeter ? [strengthId] : []);
  const level = passwordStrength(value);

  /**
   * Track the value for the meter, then forward the change.
   *
   * @param event Input change.
   */
  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    setValue(event.target.value);
    onChange?.(event);
  };

  return (
    <div className="field">
      <label className="field__label" htmlFor={id}>
        {label}
      </label>
      <div className="input-group">
        <input
          id={id}
          ref={ref}
          className="input"
          type={visible ? "text" : "password"}
          aria-invalid={a11y.invalid}
          aria-describedby={a11y.describedBy}
          onChange={handleChange}
          {...input}
        />
        <span className="input-group__trail">
          <IconButton
            label={t(visible ? "auth.password_hide" : "auth.password_show")}
            pressed={visible}
            aria-controls={id}
            icon={
              visible ? (
                <EyeOff className="icon" aria-hidden="true" />
              ) : (
                <Eye className="icon" aria-hidden="true" />
              )
            }
            onClick={() => setVisible((current) => !current)}
          />
        </span>
      </div>
      {showMeter && (
        <>
          <div className="strength" data-level={level} aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
          <p className="field__hint" id={strengthId} aria-live="polite">
            {t("auth.strength_label")} <strong>{t(STRENGTH_KEYS[level])}</strong>
          </p>
        </>
      )}
      {hint && (
        <p className="field__hint" id={a11y.hintId}>
          {hint}
        </p>
      )}
      {error && <FieldError id={a11y.errorId}>{error}</FieldError>}
    </div>
  );
}
