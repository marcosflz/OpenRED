/**
 * Panel PERFORMANCE AND OPERATION (T2-7): sliders off-design (P1t y P0),
 * ratios/empuje/régimen del `nozzle.op_point` y mapas ECharts de Mach y
 * presión con las curvas `curves.{x,mach,pr}`.
 */

import { LineChart, Slider } from "../../components";
import type { EChartsOption } from "../../components";
import type { NozzleOpPointResult } from "../../api/engine";
import { formatPressure, formatRatio } from "./format";

/** Lista exacta de regímenes del legacy (`front_nozDes.updateMapPlots`). */
export const REGIMES = [
  "Subsonic",
  "Normal Shock Inside",
  "Normal Shock Exit",
  "Over-Expanded",
  "Design-Point",
  "Under-Expanded",
] as const;

export interface OffDesignPanelProps {
  op: NozzleOpPointResult | null;
  error: string | null;
  /** Fracción 0..1 sobre `[min(P_t), max(P_t)]`. */
  p1tPercent: number;
  /** Fracción 0..1 sobre `engine.P0`. */
  p0Percent: number;
  /** Presión de entrada resuelta (Pa). */
  p1t: number;
  /** Presión ambiente resuelta (Pa). */
  p0: number;
  p1tMin: number;
  p1tMax: number;
  disabled: boolean;
  /** `PR_Crit0..3` del cálculo (paridad `update_results_entries`). */
  prCrit: Record<string, number> | null;
  machOption: EChartsOption;
  presOption: EChartsOption;
  onP1tChange: (value: number) => void;
  onP0Change: (value: number) => void;
}

const RATIO_ROWS: Array<{ key: "p0_p1" | "pe_p1" | "pe_p0"; label: string }> = [
  { key: "p0_p1", label: "P0/P1t (Exp. Ratio)" },
  { key: "pe_p1", label: "Pe/P1t (Exit/Comb.)" },
  { key: "pe_p0", label: "Pe/P0 (Exit/Amb.)" },
];

const PR_CRIT_ROWS: Array<{ crit: string; ratio: "PR0" | "PR1" | "PR2" | "PR3"; label: string }> = [
  { crit: "PR_Crit0", ratio: "PR0", label: "(P0/P1t) - Choked" },
  { crit: "PR_Crit1", ratio: "PR1", label: "(Pe/P1t) - Sub." },
  { crit: "PR_Crit2", ratio: "PR2", label: "(Pe/P1t) - NS Exit" },
  { crit: "PR_Crit3", ratio: "PR3", label: "(Pe/P1t) - Op." },
];

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        gap: 8,
        borderBottom: "1px solid var(--border)",
        padding: "2px 0",
      }}
    >
      <span style={{ color: "var(--text-muted)" }}>{label}</span>
      <span className="or-mono">{value}</span>
    </div>
  );
}

export function OffDesignPanel({
  op,
  error,
  p1tPercent,
  p0Percent,
  p1t,
  p0,
  p1tMin,
  p1tMax,
  disabled,
  prCrit,
  machOption,
  presOption,
  onP1tChange,
  onP0Change,
}: OffDesignPanelProps) {
  const ratios = op?.ratios;
  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
          gap: 12,
        }}
      >
        <Slider
          label={`P1t - ${formatPressure(p1t)} Pa`}
          value={p1tPercent}
          min={0}
          max={1}
          step={0.001}
          onChange={onP1tChange}
          format={(value) => `${(value * 100).toFixed(1)} %`}
          disabled={disabled}
        />
        <Slider
          label={`P0 - ${formatPressure(p0)} Pa`}
          value={p0Percent}
          min={0}
          max={1}
          step={0.001}
          onChange={onP0Change}
          format={(value) => `${(value * 100).toFixed(1)} %`}
          disabled={disabled}
        />
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: "4px 16px",
        }}
      >
        {RATIO_ROWS.map(({ key, label }) => (
          <Metric key={key} label={label} value={formatRatio(ratios?.[key])} />
        ))}
        {PR_CRIT_ROWS.map(({ crit, ratio, label }) => (
          <Metric
            key={crit}
            label={label}
            value={formatRatio(
              typeof prCrit?.[crit] === "number" ? prCrit[crit] : ratios?.[ratio],
            )}
          />
        ))}
        <Metric label="F (kg)" value={formatRatio(op?.F)} />
        <Metric label="Pe (Pa)" value={formatPressure(op?.Pe ?? Number.NaN, 4)} />
        <Metric label="Operation" value={op?.regime ?? "—"} />
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          color: "var(--text-muted)",
        }}
      >
        <span title={REGIMES.join(" · ")}>Régimen:</span>
        <strong
          data-testid="nozzle-regime"
          data-regime={op?.regime ?? ""}
          style={{ color: "var(--accent)" }}
        >
          {op?.regime ?? "—"}
        </strong>
        <span>
          · Rango P1t [{formatPressure(p1tMin, 3)}, {formatPressure(p1tMax, 3)}] Pa
        </span>
      </div>

      {error ? (
        <div role="alert" style={{ color: "var(--danger)" }}>
          {error}
        </div>
      ) : null}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))",
          gap: 12,
        }}
      >
        <LineChart option={machOption} height={260} ariaLabel="Mapa de Mach off-design" />
        <LineChart option={presOption} height={260} ariaLabel="Mapa de presión off-design" />
      </div>
    </div>
  );
}
