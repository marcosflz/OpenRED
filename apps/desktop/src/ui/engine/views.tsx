import { useMemo } from "react";
import type { EngineCalculateResult, EngineResults } from "../../api/types";
import { FigureView, Table, TextField, type TableColumn } from "../../components";
import { formatCell, formatMetric, timeDecimals, treeRows, type TreeRow } from "./helpers";

interface MetricField {
  key: keyof EngineResults;
  label: string;
}

/** 8 métricas del legacy, en el mismo orden visual (2 columnas x 4 filas). */
const METRICS: readonly MetricField[] = [
  { key: "meanPressure", label: "Mean Pressure (Pa)" },
  { key: "meanMassFlow", label: "Mean Mass Flow (kg/s)" },
  { key: "maxPressure", label: "Max. Pressure (Pa)" },
  { key: "maxMassFlow", label: "Max. Mass Flow (kg/s)" },
  { key: "minPressure", label: "Min. Pressure (Pa)" },
  { key: "minMassFlow", label: "Min. Mass Flow (kg/s)" },
  { key: "totalTime", label: "Burning Time (s)" },
  { key: "totalMass", label: "Propellant Mass (kg)" },
];

const TREE_COLUMNS: Array<TableColumn<TreeRow>> = [
  { key: "time", header: "Time (s)", align: "center" },
  {
    key: "pressure",
    header: "Pressure (Pa)",
    align: "center",
    render: (row) => formatCell(row.pressure),
  },
  {
    key: "massFlow",
    header: "Mass Flow (kg/s)",
    align: "center",
    render: (row) => formatCell(row.massFlow),
  },
  { key: "mass", header: "Mass (kg)", align: "center", render: (row) => formatCell(row.mass) },
];

/** Sub-pestaña DATA: métricas + tabla `tree_data` (T1-6). */
export function DataView({ result, dt }: { result: EngineCalculateResult | null; dt: string }) {
  const results = result?.payload.results;
  const rows = useMemo(
    () => treeRows(results?.tree_data, timeDecimals(dt)),
    [results?.tree_data, dt],
  );

  return (
    <div style={{ display: "grid", gap: 12, marginTop: 4 }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
        {METRICS.map((metric) => (
          <TextField
            key={metric.key}
            label={metric.label}
            value={formatMetric(results?.[metric.key] as number | undefined)}
            onChange={() => {}}
            readOnly
            data-testid={`metric-${metric.key}`}
          />
        ))}
      </div>
      <Table<TreeRow>
        columns={TREE_COLUMNS}
        rows={rows}
        rowKey={(_, index) => index}
        height={280}
        emptyMessage="Sin resultados"
      />
    </div>
  );
}

/** Sub-pestaña GRAPHS: las 3 figuras PNG del cálculo (T1-7). */
export function GraphsView({ result }: { result: EngineCalculateResult | null }) {
  return (
    <div style={{ display: "grid", gap: 12, marginTop: 4 }}>
      <FigureView png={result?.figures.pressure} alt="Chamber pressure" height={260} />
      <FigureView png={result?.figures.massFlow} alt="Mass flow" height={260} />
      <FigureView png={result?.figures.massBurn} alt="Propellant mass" height={260} />
    </div>
  );
}
