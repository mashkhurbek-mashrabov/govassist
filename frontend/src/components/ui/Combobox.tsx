import { Check, ChevronDown, Search } from "lucide-react";
import { useId, useState, type KeyboardEvent } from "react";
import { useTranslation } from "react-i18next";
import { matchesQuery } from "../../lib/search";
import { fieldA11y } from "./fieldA11y";
import { FieldError } from "./FieldError";
import { Skeleton } from "./Skeleton";
import { Spinner } from "./Spinner";

/** One choice. */
export interface ComboboxOption {
  value: number;
  label: string;
}

/** Props of {@link Combobox}. */
interface ComboboxProps {
  label: string;
  options: ComboboxOption[];
  value: number | null;
  onChange: (value: number) => void;
  /** Shown while the options load (spinner + skeleton rows). */
  loading?: boolean;
  loadingText?: string;
  /** When set, the field is disabled and this text explains why. */
  disabledReason?: string | undefined;
  error?: string | undefined;
}

/**
 * Searchable combobox for region and district (components.md → Combobox; ARIA 1.2 pattern).
 * Typing filters in both scripts; ↓/↑ move, Enter selects, Esc closes.
 *
 * @param props Label, options, value, change callback, loading/disabled/error states.
 * @returns The field.
 */
export function Combobox({
  label,
  options,
  value,
  onChange,
  loading,
  loadingText,
  disabledReason,
  error,
}: ComboboxProps) {
  const { t } = useTranslation();
  const id = useId();
  const listId = `${id}-list`;
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const selected = options.find((option) => option.value === value);
  const filtered = options.filter((option) => matchesQuery(option.label, query));
  const a11y = fieldA11y(id, Boolean(disabledReason), error);
  const disabled = disabledReason !== undefined;
  const activeOption = open ? filtered[active] : undefined;

  /**
   * Choose an option and close the list.
   *
   * @param option The option.
   */
  const choose = (option: ComboboxOption) => {
    onChange(option.value);
    setOpen(false);
    setQuery("");
  };

  /**
   * Keyboard support.
   *
   * @param event Key event on the input.
   */
  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      const step = event.key === "ArrowDown" ? 1 : -1;
      setOpen(true);
      setActive((current) =>
        filtered.length === 0 ? 0 : (current + step + filtered.length) % filtered.length,
      );
    } else if (event.key === "Enter" && activeOption) {
      event.preventDefault();
      choose(activeOption);
    } else if (event.key === "Escape") {
      setOpen(false);
      setQuery("");
    }
  };

  return (
    <div className="field combobox">
      <label className="field__label" htmlFor={id}>
        {label}
      </label>
      <div className="input-group">
        <span className="input-group__lead">
          <Search className="icon" aria-hidden="true" />
        </span>
        <input
          id={id}
          className="input input--lead"
          role="combobox"
          aria-expanded={open}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={activeOption ? `${listId}-${activeOption.value}` : undefined}
          aria-invalid={a11y.invalid}
          aria-describedby={a11y.describedBy}
          placeholder={t("onboarding.search")}
          autoComplete="off"
          disabled={disabled}
          value={open ? query : (selected?.label ?? "")}
          onFocus={() => {
            setOpen(true);
            setActive(0);
          }}
          onBlur={() => {
            setOpen(false);
            setQuery("");
          }}
          onChange={(event) => {
            setQuery(event.target.value);
            setActive(0);
            setOpen(true);
          }}
          onKeyDown={onKeyDown}
        />
        <span className="input-group__trail">
          <span className="icon-btn" aria-hidden="true">
            <ChevronDown className="icon" />
          </span>
        </span>
      </div>
      {open && loading && (
        <div className="listbox" id={listId} role="status">
          <p className="listbox__empty">
            <Spinner /> {loadingText ?? t("common.loading")}
          </p>
          <Skeleton />
          <Skeleton width="60" />
        </div>
      )}
      {open && !loading && (
        <ul className="listbox" id={listId} role="listbox" aria-label={label}>
          {filtered.length === 0 && <li className="listbox__empty">{t("onboarding.no_results")}</li>}
          {filtered.map((option, position) => (
            // eslint-disable-next-line jsx-a11y/click-events-have-key-events -- keys are handled on the combobox input (aria-activedescendant pattern)
            <li
              key={option.value}
              id={`${listId}-${option.value}`}
              role="option"
              aria-selected={option.value === value}
              className={position === active ? "is-active" : undefined}
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => choose(option)}
            >
              <span>{option.label}</span>
              {option.value === value && <Check className="icon" aria-hidden="true" />}
            </li>
          ))}
        </ul>
      )}
      {disabledReason && (
        <p className="field__hint" id={a11y.hintId}>
          {disabledReason}
        </p>
      )}
      {error && <FieldError id={a11y.errorId}>{error}</FieldError>}
    </div>
  );
}
