import { useId, type ReactNode } from "react";
import { cx } from "../utils/cx";

export interface RadioOption {
  value: string;
  label: ReactNode;
  disabled?: boolean;
}

export interface RadioGroupProps {
  /** Nombre del grupo (`name` de los inputs). */
  name: string;
  value: string;
  options: RadioOption[];
  onChange: (value: string) => void;
  label?: string;
  direction?: "row" | "column";
  disabled?: boolean;
  className?: string;
}

export function RadioGroup({
  name,
  value,
  options,
  onChange,
  label,
  direction = "row",
  disabled = false,
  className,
}: RadioGroupProps) {
  const groupId = useId();

  return (
    <fieldset className={cx("or-radio-group", `or-radio-group--${direction}`, className)}>
      {label ? <legend className="or-field__label">{label}</legend> : null}
      {options.map((option) => {
        const optionId = `${groupId}-${option.value}`;
        return (
          <label key={option.value} className="or-radio" htmlFor={optionId}>
            <input
              id={optionId}
              type="radio"
              name={name}
              value={option.value}
              checked={value === option.value}
              onChange={() => onChange(option.value)}
              disabled={disabled || option.disabled}
              className="or-radio__input"
            />
            <span className="or-radio__label">{option.label}</span>
          </label>
        );
      })}
    </fieldset>
  );
}
