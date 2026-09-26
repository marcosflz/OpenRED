import { useId, useState, type FocusEvent, type InputHTMLAttributes } from "react";
import { cx } from "../utils/cx";
import {
  getEntryValue,
  normalizeNumericInput,
  validateScientificNotation,
} from "../utils/numbers";

export { getEntryValue, validateScientificNotation } from "../utils/numbers";

export interface NumberFieldProps
  extends Omit<
    InputHTMLAttributes<HTMLInputElement>,
    "onChange" | "value" | "size" | "type" | "min" | "max" | "step"
  > {
  /** Valor como cadena (paridad con `config.json`). */
  value: string;
  onChange: (value: string) => void;
  label?: string;
  hint?: string;
  error?: string | null;
  units?: string;
  min?: number;
  max?: number;
  step?: number;
  /** Sustituye comas por puntos al salir del campo (ventanas DB del original). */
  normalizeCommas?: boolean;
  /** Mensaje mostrado cuando el texto no es numérico válido. */
  invalidMessage?: string;
  containerClassName?: string;
  inputClassName?: string;
}

/**
 * Campo numérico de texto (no `type="number"`, para preservar notación
 * científica y la semántica `get_entry_value`: vacío -> "0" al perder foco).
 */
export function NumberField({
  value,
  onChange,
  label,
  hint,
  error,
  units,
  min,
  max,
  step,
  normalizeCommas = false,
  invalidMessage = "Notación numérica no válida",
  className,
  containerClassName,
  inputClassName,
  id,
  disabled,
  onBlur,
  ...rest
}: NumberFieldProps) {
  const autoId = useId();
  const inputId = id ?? autoId;
  const [touched, setTouched] = useState(false);

  const trimmed = value.trim();
  const candidate = normalizeCommas ? normalizeNumericInput(trimmed) : trimmed;
  const invalid = touched && trimmed !== "" && !validateScientificNotation(candidate);
  const shownError = error ?? (invalid ? invalidMessage : null);
  const describedBy = shownError ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined;

  const handleBlur = (event: FocusEvent<HTMLInputElement>) => {
    setTouched(true);
    const raw = event.currentTarget.value;
    if (raw.trim() === "") {
      onChange(getEntryValue(raw)); // vacío -> "0"
    } else if (normalizeCommas) {
      const normalized = normalizeNumericInput(raw);
      if (normalized !== raw) onChange(normalized);
    }
    onBlur?.(event);
  };

  return (
    <div className={cx("or-field", containerClassName, className)}>
      {label ? (
        <label className="or-field__label" htmlFor={inputId}>
          {label}
        </label>
      ) : null}
      <div className="or-number">
        <input
          id={inputId}
          type="text"
          inputMode="decimal"
          autoComplete="off"
          spellCheck={false}
          className={cx("or-input", "or-number__input", shownError && "or-input--invalid", inputClassName)}
          value={value}
          onChange={(event) => onChange(event.currentTarget.value)}
          onBlur={handleBlur}
          disabled={disabled}
          aria-invalid={shownError ? true : undefined}
          aria-describedby={describedBy}
          {...rest}
        />
        {units ? <span className="or-number__units">{units}</span> : null}
      </div>
      {shownError ? (
        <span id={`${inputId}-error`} className="or-field__error" role="alert">
          {shownError}
        </span>
      ) : hint ? (
        <span id={`${inputId}-hint`} className="or-field__hint">
          {hint}
        </span>
      ) : null}
      {(min !== undefined || max !== undefined || step !== undefined) && (
        <span className="or-field__range">
          {min !== undefined ? `min ${min}` : ""}
          {max !== undefined ? `${min !== undefined ? " · " : ""}max ${max}` : ""}
          {step !== undefined ? ` · paso ${step}` : ""}
        </span>
      )}
    </div>
  );
}
