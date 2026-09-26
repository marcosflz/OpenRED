import { useId, type SelectHTMLAttributes } from "react";
import { cx } from "../utils/cx";

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export type SelectOptionInput = string | number | SelectOption;

export interface SelectProps
  extends Omit<SelectHTMLAttributes<HTMLSelectElement>, "onChange" | "value" | "children"> {
  value: string;
  options: SelectOptionInput[];
  onChange: (value: string) => void;
  label?: string;
  hint?: string;
  error?: string | null;
  /** Opción inicial deshabilitada cuando `value` está vacío. */
  placeholder?: string;
  containerClassName?: string;
  selectClassName?: string;
}

function normalizeOption(option: SelectOptionInput): SelectOption {
  return typeof option === "object"
    ? option
    : { value: String(option), label: String(option) };
}

export function Select({
  value,
  options,
  onChange,
  label,
  hint,
  error,
  placeholder,
  className,
  containerClassName,
  selectClassName,
  id,
  disabled,
  ...rest
}: SelectProps) {
  const autoId = useId();
  const selectId = id ?? autoId;
  const describedBy = error ? `${selectId}-error` : hint ? `${selectId}-hint` : undefined;

  return (
    <div className={cx("or-field", containerClassName, className)}>
      {label ? (
        <label className="or-field__label" htmlFor={selectId}>
          {label}
        </label>
      ) : null}
      <select
        id={selectId}
        className={cx("or-select", error && "or-input--invalid", selectClassName)}
        value={value}
        onChange={(event) => onChange(event.currentTarget.value)}
        disabled={disabled}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        {...rest}
      >
        {placeholder !== undefined ? (
          <option value="" disabled>
            {placeholder}
          </option>
        ) : null}
        {options.map((raw) => {
          const option = normalizeOption(raw);
          return (
            <option key={option.value} value={option.value} disabled={option.disabled}>
              {option.label}
            </option>
          );
        })}
      </select>
      {error ? (
        <span id={`${selectId}-error`} className="or-field__error" role="alert">
          {error}
        </span>
      ) : hint ? (
        <span id={`${selectId}-hint`} className="or-field__hint">
          {hint}
        </span>
      ) : null}
    </div>
  );
}
