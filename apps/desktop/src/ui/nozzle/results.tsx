/**
 * Paneles de resultados T2: 17 etiquetas de `calculatedResults` + PR_Crit0..3
 * (T2-6), figuras PNG (T2-9) y tablas TIME RESULTS / GEOMETRY (T2-8).
 */

import { useMemo, useState } from "react";
import { Card, FigureView, Table, Tabs, type TableColumn } from "../../components";
import type { NozzleCalculateResult } from "../../api/engine";
import type { NozzleFigures, NozzleGeometryData, NozzleTimeResults } from "../../api/types";import { formatFixed6, formatLegacyValue } from "./format";

const PR_CRIT_KEYS = ["PR_Crit0", "PR_Crit1", "PR_Crit2", "PR_Crit3"] as const;

type NumericRow = Record<string, number>;

const ROW_LABEL_STYLE = {
  color: "var(--text-muted)",
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "nowrap",
} as const;

const ROW_VALUE_STYLE = {
  textAlign: "right",
  whiteSpace: "nowrap",
} as const;

const RESULT_GRID_STYLE = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
  gap: "4px 16px",
} as const;

function ResultRow({ label, value }: { label: string; value: number }) {
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
      <span style={ROW_LABEL_STYLE} title={label}>
        {label}
      </span>
      <span className="or-mono" style={ROW_VALUE_STYLE}>
        {formatLegacyValue(value)}
      </span>
    </div>
  );
}

/** Etiquetas numéricas del cálculo, sin los `PR_Crit*`. */
export function resultLabels(result: NozzleCalculateResult): string[] {
  return Object.keys(result.calculatedResults).filter(
    (key) => !(PR_CRIT_KEYS as readonly string[]).includes(key),
  );
}

/** Panel numérico T2-6 (los valores ya vienen redondeados por el motor). */
export function ResultsPanel({ result }: { result: NozzleCalculateResult }) {
  const labels = resultLabels(result);
  return (
    <div style={{ display: "grid", gap: 10 }}>
      <div style={RESULT_GRID_STYLE} data-testid="nozzle-calculated-results">
        {labels.map((label) => (
          <ResultRow key={label} label={label} value={Number(result.calculatedResults[label])} />
        ))}
      </div>
      <div style={RESULT_GRID_STYLE} data-testid="nozzle-pr-crit">
        {PR_CRIT_KEYS.map((key) => (
          <ResultRow key={key} label={key} value={Number(result.calculatedResults[key])} />
        ))}
      </div>
    </div>
  );
}

const FIGURE_ITEMS: Array<{ key: keyof NozzleFigures; title: string }> = [
  { key: "geometry", title: "Nozzle Geometry" },
  { key: "thrust", title: "Thrust (kg)" },
  { key: "cf", title: "Thrust Coefficient" },
  { key: "mach", title: "Mach Number" },
  { key: "pres", title: "Pressure Ratio" },
];

/** Figuras PNG del cálculo (T2-9) con `FigureView`. */
export function FiguresPanel({ figures }: { figures: Partial<NozzleFigures> }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
        gap: 10,
      }}
    >
      {FIGURE_ITEMS.map(({ key, title }) => (
        <Card key={key} title={title} flush>
          <FigureView png={figures[key]} alt={title} height={260} />
        </Card>
      ))}
    </div>
  );
}

function asNumberArray(value: unknown): number[] {
  if (!Array.isArray(value)) return [];
  return value.map((item) => (typeof item === "number" ? item : Number(item)));
}

function rowsFromArrays(data: Record<string, unknown> | null | undefined): NumericRow[] {
  if (!data) return [];
  const entries = Object.entries(data).map(
    ([key, value]) => [key, asNumberArray(value)] as const,
  );
  if (entries.length === 0) return [];
  const length = entries.reduce((max, [, values]) => Math.max(max, values.length), 0);
  const rows: NumericRow[] = [];
  for (let index = 0; index < length; index += 1) {
    const row: NumericRow = {};
    for (const [key, values] of entries) row[key] = values[index] ?? 0;
    rows.push(row);
  }
  return rows;
}

const TIME_COLUMNS: Array<TableColumn<NumericRow>> = [
  {
    key: "Time (s)",
    header: "Time (s)",
    align: "right",
    render: (row) => formatLegacyValue(row["Time (s)"]),
  },
  {
    key: "Thrust (kg)",
    header: "Thrust (kg)",
    align: "right",
    render: (row) => formatLegacyValue(row["Thrust (kg)"]),
  },
  {
    key: "CF",
    header: "CF",
    align: "right",
    render: (row) => formatLegacyValue(row.CF),
  },
];

const GEOMETRY_COLUMNS: Array<TableColumn<NumericRow>> = [
  {
    key: "X (m)",
    header: "X (m)",
    align: "right",
    render: (row) => formatFixed6(row["X (m)"]),
  },
  {
    key: "Y (m)",
    header: "Y (m)",
    align: "right",
    render: (row) => formatFixed6(row["Y (m)"]),
  },
  {
    key: "AR (m)",
    header: "AR",
    align: "right",
    render: (row) => formatFixed6(row["AR (m)"]),
  },
];

/** Tablas TIME RESULTS / GEOMETRY (T2-8). */
export function NozzleTables({
  timeResults,
  geometry,
}: {
  timeResults: NozzleTimeResults | null;
  geometry: NozzleGeometryData | null;
}) {
  const [tab, setTab] = useState("time");
  const timeRows = useMemo(() => rowsFromArrays(timeResults), [timeResults]);
  const geometryRows = useMemo(() => rowsFromArrays(geometry), [geometry]);

  return (
    <div style={{ display: "grid", gap: 8 }}>
      <Tabs
        items={[
          { id: "time", label: "TIME RESULTS", badge: timeRows.length || undefined },
          { id: "geometry", label: "GEOMETRY", badge: geometryRows.length || undefined },
        ]}
        value={tab}
        onChange={setTab}
        ariaLabel="Tablas de resultados"
      />
      {tab === "time" ? (
        <Table
          columns={TIME_COLUMNS}
          rows={timeRows}
          height={260}
          emptyMessage="Sin resultados (CALCULATE)"
        />
      ) : (
        <Table
          columns={GEOMETRY_COLUMNS}
          rows={geometryRows}
          height={260}
          emptyMessage="Sin geometría (CALCULATE)"
        />
      )}
    </div>
  );
}
