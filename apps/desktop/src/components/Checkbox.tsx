import { useEffect, useId, useRef, type InputHTMLAttributes, type ReactNode } from "react";
import { cx } from "../utils/cx";

export interface CheckboxProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, "onChange" | "checked" | "type" | "children"> {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: ReactNode;
  /** Estado mixto (solo visual). */
  indeterminate?: boolean;
  containerClassName?: string;
}

export function Checkbox({
  checked,
  onChange,
  label,
  indeterminate = false,
  className,
  containerClassName,
  id,
  disabled,
  ...rest
}: CheckboxProps) {
  const autoId = useId();
  const inputId = id ?? autoId;
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (inputRef.current) inputRef.current.indeterminate = indeterminate;
  }, [indeterminate]);

  return (
    <label className={cx("or-checkbox", containerClassName, className)} htmlFor={inputId}>
      <input
        ref={inputRef}
        id={inputId}
        type="checkbox"
        className="or-checkbox__input"
        checked={checked}
        onChange={(event) => onChange(event.currentTarget.checked)}
        disabled={disabled}
        {...rest}
      />
      {label !== undefined ? <span className="or-checkbox__label">{label}</span> : null}
    </label>
  );
}
