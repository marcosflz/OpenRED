import { useId, type InputHTMLAttributes } from "react";
import { cx } from "../utils/cx";

export interface TextFieldProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, "onChange" | "value" | "size"> {
  label?: string;
  value: string;
  onChange: (value: string) => void;
  hint?: string;
  error?: string | null;
  containerClassName?: string;
  inputClassName?: string;
}

export function TextField({
  label,
  value,
  onChange,
  hint,
  error,
  className,
  containerClassName,
  inputClassName,
  id,
  disabled,
  ...rest
}: TextFieldProps) {
  const autoId = useId();
  const inputId = id ?? autoId;
  const describedBy = error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined;

  return (
    <div className={cx("or-field", containerClassName, className)}>
      {label ? (
        <label className="or-field__label" htmlFor={inputId}>
          {label}
        </label>
      ) : null}
      <input
        id={inputId}
        className={cx("or-input", error && "or-input--invalid", inputClassName)}
        value={value}
        onChange={(event) => onChange(event.currentTarget.value)}
        disabled={disabled}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        {...rest}
      />
      {error ? (
        <span id={`${inputId}-error`} className="or-field__error" role="alert">
          {error}
        </span>
      ) : hint ? (
        <span id={`${inputId}-hint`} className="or-field__hint">
          {hint}
        </span>
      ) : null}
    </div>
  );
}
