import { useCallback, useMemo, useState } from "react";
import {
  Button,
  LineChart,
  Modal,
  Spinner,
  useToast,
  type EChartsOption,
  type TableColumn,
} from "../../components";
import { isCancel, request, toRpcError, type BurningRateResult } from "../../api/engine";
import {
  DbCrudModal,
  formatDbCell,
  type CrudContext,
  type DbField,
  type DbRecord,
  type DbWindowProps,
} from "./shared";

/** Campos numéricos de `propelente` (13 columnas sin id, en orden de esquema). */
const PROPELLANT_FIELDS: DbField[] = [
  { key: "T_ad", label: "T_ad" },
  { key: "MolWeight", label: "MolWeight" },
  { key: "Cp", label: "Cp" },
  { key: "Cv", label: "Cv" },
  { key: "R", label: "R" },
  { key: "gamma", label: "gamma" },
  { key: "cChar", label: "cChar" },
  { key: "Density", label: "Density" },
  { key: "P1_min", label: "P1_min" },
  { key: "P1_max", label: "P1_max" },
  { key: "a", label: "a" },
  { key: "n", label: "n" },
];

export const PROPELLANT_COLUMNS: Array<TableColumn<DbRecord>> = [
  { key: "id", header: "ID", align: "center" },
  { key: "Propelente", header: "Propelente" },
  ...PROPELLANT_FIELDS.map((field) => ({ key: field.key, header: field.label })),
];

/** Ventana `Database > Propellants Data` (tabla `propelente`, D-2/D-3 + G9). */
export function PropellantsWindow({ open, onClose }: DbWindowProps) {
  const toast = useToast();
  const [chartName, setChartName] = useState<string | null>(null);
  const [chart, setChart] = useState<BurningRateResult | null>(null);

  const showBurningRate = useCallback(
    async (name: string) => {
      if (!name) {
        toast.warning({ title: "Burning Rate", message: "Select a propellant." });
        return;
      }
      setChartName(name);
      setChart(null);
      try {
        const response = await request<BurningRateResult>("db.propellants.burning_rate", {
          name,
          n_points: 1000,
        });
        setChart(response);
      } catch (error) {
        const rpc = toRpcError(error);
        if (!isCancel(rpc)) toast.error({ title: "Burning Rate", message: rpc.message });
        setChartName(null);
      }
    },
    [toast],
  );

  const chartOption = useMemo<EChartsOption | null>(() => {
    if (!chart) return null;
    return {
      xAxis: { type: "value", name: "Chamber Pressure P1 (Pa)" },
      yAxis: { type: "value", name: "Burning Rate r (cm/s)" },
      tooltip: { trigger: "axis" },
      series: [
        {
          type: "line",
          name: chartName ?? "r(P1)",
          showSymbol: false,
          data: chart.P.map((pressure, index) => [pressure, chart.r[index] ?? 0]),
        },
      ],
    };
  }, [chart, chartName]);

  const extraActions = useCallback(
    (context: CrudContext) => {
      // El motor busca por el nombre exacto en la tabla: se usa el valor crudo,
      // no el nombre limpio que solo sirve para mostrar.
      const name = context.selected ? formatDbCell(context.selected.Propelente) : "";
      return (
        <Button block disabled={name === ""} onClick={() => void showBurningRate(name)}>
          Show Burning Rate Curve
        </Button>
      );
    },
    [showBurningRate],
  );

  return (
    <>
      <DbCrudModal
        open={open}
        onClose={onClose}
        title="Propellants Data"
        namespace="db.propellants"
        nameKey="Propelente"
        nameLabel="Propellant"
        fields={PROPELLANT_FIELDS}
        columns={PROPELLANT_COLUMNS}
        commaMessage="The comma has been replaced with a dot to maintain numerical format."
        closeOnEsc={chartName === null}
        extraActions={extraActions}
      />
      <Modal
        open={chartName !== null}
        onClose={() => setChartName(null)}
        title={`Burning Rate — ${chartName ?? ""}`}
        width={780}
      >
        {chart && chartOption ? (
          <LineChart
            option={chartOption}
            height={380}
            ariaLabel={`Burning rate of ${chartName ?? "propellant"}`}
          />
        ) : (
          <div style={{ display: "flex", justifyContent: "center", padding: 32 }}>
            <Spinner size={22} label="Cargando curva" />
          </div>
        )}
      </Modal>
    </>
  );
}
