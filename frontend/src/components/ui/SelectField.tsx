import { useId, type Ref, type SelectHTMLAttributes } from "react";

/** One option of {@link SelectField}. */
export interface SelectOption {
  value: string;
  label: string;
}

/** Props of {@link SelectField}. */
export interface SelectFieldProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  options: SelectOption[];
  /** Text of the empty first option; omit to have none. */
  placeholder?: string;
  /** Already-translated error text. */
  error?: string | undefined;
  ref?: Ref<HTMLSelectElement>;
}

/**
 * Labelled native select. F2 may swap it for a searchable combobox.
 *
 * @param props Label, options, placeholder, error and native select props.
 * @returns The field.
 */
export function SelectField({ label, options, placeholder, error, ref, ...select }: SelectFieldProps) {
  const id = useId();
  const errorId = `${id}-error`;
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id}>{label}</label>
      <select
        id={id}
        ref={ref}
        className="min-h-11 border px-2"
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        {...select}
      >
        {placeholder !== undefined && <option value="">{placeholder}</option>}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error && (
        <p id={errorId} role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
