import { useMemo } from "react";
import { cx } from "../utils/cx";

export interface GaugeZone {
  from: number;
  to: number;
  color: string;
}

export interface GaugeProps {
  value: number;
  min?: number;
  max?: number;
  label?: string;
  unit?: string;
  /** Diámetro del SVG en px. */
  size?: number;
  zones?: GaugeZone[];
  className?: string;
}

const START_ANGLE = -135;
const SWEEP = 270;

function polar(cx: number, cy: number, radius: number, angle: number) {
  const radians = ((angle - 90) * Math.PI) / 180;
  return { x: cx + radius * Math.cos(radians), y: cy + radius * Math.sin(radians) };
}

function arcPath(cx: number, cy: number, radius: number, from: number, to: number): string {
  const start = polar(cx, cy, radius, from);
  const end = polar(cx, cy, radius, to);
  const largeArc = to - from <= 180 ? 0 : 1;
  return `M ${start.x.toFixed(3)} ${start.y.toFixed(3)} A ${radius} ${radius} 0 ${largeArc} 1 ${end.x.toFixed(3)} ${end.y.toFixed(3)}`;
}

/**
 * Gauge SVG (aguja + zonas) para el Test Bed: THRUST, TEMPERATURE, etc.
 * Equivalente funcional a `front_test.gaugePlot` sin matplotlib.
 */
export function Gauge({
  value,
  min = 0,
  max = 1,
  label,
  unit,
  size = 180,
  zones,
  className,
}: GaugeProps) {
  const clamped = Math.min(Math.max(value, min), max);
  const ratio = max - min === 0 ? 0 : (clamped - min) / (max - min);
  const angle = START_ANGLE + ratio * SWEEP;
  const radius = size / 2 - 18;
  const center = size / 2;
  const needle = polar(center, center, radius - 6, angle);

  const zonePaths = useMemo(
    () =>
      (zones ?? []).map((zone) => {
        const from = START_ANGLE + ((Math.min(Math.max(zone.from, min), max) - min) / (max - min)) * SWEEP;
        const to = START_ANGLE + ((Math.min(Math.max(zone.to, min), max) - min) / (max - min)) * SWEEP;
        return { path: arcPath(center, center, radius, from, to), color: zone.color };
      }),
    [zones, min, max, radius, center],
  );

  return (
    <svg
      className={cx("or-gauge", className)}
      width={size}
      height={size * 0.78}
      viewBox={`0 0 ${size} ${size * 0.78}`}
      role="meter"
      aria-valuemin={min}
      aria-valuemax={max}
      aria-valuenow={clamped}
      aria-label={label ?? "Medidor"}
    >
      <path className="or-gauge__track" d={arcPath(center, center, radius, START_ANGLE, START_ANGLE + SWEEP)} />
      {zonePaths.map((zone, index) => (
        <path key={index} d={zone.path} stroke={zone.color} className="or-gauge__zone" />
      ))}
      <path
        className="or-gauge__value"
        d={arcPath(center, center, radius, START_ANGLE, Math.max(START_ANGLE + 0.01, angle))}
      />
      <line
        className="or-gauge__needle"
        x1={center}
        y1={center}
        x2={needle.x}
        y2={needle.y}
        strokeWidth={2.5}
      />
      <circle className="or-gauge__hub" cx={center} cy={center} r={4} />
      <text className="or-gauge__readout" x={center} y={center + 4} textAnchor="middle">
        {clamped.toFixed(2)}
      </text>
      {unit ? (
        <text className="or-gauge__unit" x={center} y={center + 20} textAnchor="middle">
          {unit}
        </text>
      ) : null}
    </svg>
  );
}
