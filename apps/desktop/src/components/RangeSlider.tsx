import { useId } from "react";
import { cx } from "../utils/cx";

export interface RangeSliderProps {
  /** Par [mínimo, máximo]. */
  values: [number, number];
  onChange: (values: [number, number]) => void;
  min?: number;
  max?: number;
  step?: number;
  label?: string;
  format?: (value: number) => string;
  disabled?: boolean;
  className?: string;
}

export function RangeSlider({
  values,
  onChange,
  min = 0,
  max = 1,
  step = 0.01,
  label,
  format,
  disabled = false,
  className,
}: RangeSliderProps) {
  const groupId = useId();
  const [low, high] = values;
  const display = format ?? ((value: number) => String(value));
  const span = max - min || 1;
  const lowPercent = ((low - min) / span) * 100;
  const highPercent = ((high - min) / span) * 100;

  const setLow = (next: number) => onChange([Math.min(next, high), high]);
  const setHigh = (next: number) => onChange([low, Math.max(next, low)]);

  return (
    <div className={cx("or-range", className)}>
      {label ? <span className="or-field__label">{label}</span> : null}
      <div className="or-range__track" aria-hidden="true">
        <span
          className="or-range__fill"
          style={{ left: `${lowPercent}%`, width: `${Math.max(0, highPercent - lowPercent)}%` }}
        />
      </div>
      <input
        id={`${groupId}-low`}
        type="range"
        aria-label={`${label ?? "Rango"} mínimo`}
        className="or-range__input"
        value={low}
        min={min}
        max={max}
        step={step}
        disabled={disabled}
        onChange={(event) => setLow(Number(event.currentTarget.value))}
      />
      <input
        id={`${groupId}-high`}
        type="range"
        aria-label={`${label ?? "Rango"} máximo`}
        className="or-range__input"
        value={high}
        min={min}
        max={max}
        step={step}
        disabled={disabled}
        onChange={(event) => setHigh(Number(event.currentTarget.value))}
      />
      <div className="or-range__values">
        <span>{display(low)}</span>
        <span>{display(high)}</span>
      </div>
    </div>
  );
}
