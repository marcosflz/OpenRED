import { type ReactNode } from "react";
import { cx } from "../utils/cx";

export interface ProgressBarProps {
  /** Progreso 0..1 (o 0..`max`). */
  value?: number;
  max?: number;
  /** Barra animada sin valor conocido. */
  indeterminate?: boolean;
  label?: ReactNode;
  showPercent?: boolean;
  className?: string;
}

export function ProgressBar({
  value = 0,
  max = 1,
  indeterminate = false,
  label,
  showPercent = false,
  className,
}: ProgressBarProps) {
  const ratio = max > 0 ? Math.min(1, Math.max(0, value / max)) : 0;
  const percent = Math.round(ratio * 100);

  return (
    <div className={cx("or-progress", className)}>
      {label || showPercent ? (
        <div className="or-progress__header">
          {label ? <span className="or-progress__label">{label}</span> : <span />}
          {showPercent ? <span className="or-progress__value">{percent}%</span> : null}
        </div>
      ) : null}
      <div
        className={cx("or-progress__track", indeterminate && "or-progress__track--indeterminate")}
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={indeterminate ? undefined : max}
        aria-valuenow={indeterminate ? undefined : value}
        aria-valuetext={indeterminate ? "En curso" : `${percent}%`}
        aria-label={typeof label === "string" ? label : "Progreso"}
      >
        <div
          className="or-progress__fill"
          style={indeterminate ? undefined : { width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
