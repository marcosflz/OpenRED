import { useId, type InputHTMLAttributes } from "react";
import { cx } from "../utils/cx";

export interface SliderProps
  extends Omit<
    InputHTMLAttributes<HTMLInputElement>,
    "onChange" | "value" | "type" | "size" | "min" | "max" | "step"
  > {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  label?: string;
  /** Formatea el valor mostrado a la derecha. */
  format?: (value: number) => string;
  showValue?: boolean;
  containerClassName?: string;
}

export function Slider({
  value,
  onChange,
  min = 0,
  max = 1,
  step = 0.01,
  label,
  format,
  showValue = true,
  className,
  containerClassName,
  id,
  disabled,
  ...rest
}: SliderProps) {
  const autoId = useId();
  const inputId = id ?? autoId;
  const display = format ? format(value) : String(value);

  return (
    <div className={cx("or-slider", containerClassName, className)}>
      {label || showValue ? (
        <div className="or-slider__header">
          {label ? (
            <label className="or-field__label" htmlFor={inputId}>
              {label}
            </label>
          ) : (
            <span />
          )}
          {showValue ? <span className="or-slider__value">{display}</span> : null}
        </div>
      ) : null}
      <input
        id={inputId}
        type="range"
        className="or-slider__input"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(event) => onChange(Number(event.currentTarget.value))}
        disabled={disabled}
        {...rest}
      />
    </div>
  );
}
