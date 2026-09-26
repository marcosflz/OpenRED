/**
 * Opciones ECharts del módulo T2: perfil de presión (T2-4) y mapas off-design
 * de Mach y presión (T2-7). Se parte de `baseChartOption` para heredar los
 * colores del tema activo (oscuro/claro).
 */

import { baseChartOption, type EChartsOption, type EChartsTheme } from "../../components";
import { formatPressure, timeAtPressure } from "./format";

/** Curva de presión del motor (`nozzle.load_engine.p_curve`). */
export interface PressureCurve {
  t: number[];
  P: number[];
}

/** Curvas del punto off-design (`nozzle.op_point.curves`). */
export interface OffDesignCurves {
  x: number[];
  mach: number[];
  pr: number[];
}

function pressureSeriesData(curve: PressureCurve): Array<[number, number]> {
  return curve.t.map((t, index) => [t, curve.P[index] ?? 0]);
}

/**
 * Perfil de presión con el punto P1 marcado y el ratio `P1/Pmax` en la leyenda
 * (paridad `front_nozDes.update_plot`).
 */
export function pressureProfileOption(
  mode: EChartsTheme,
  curve: PressureCurve,
  p1: number,
): EChartsOption {
  const base = baseChartOption(mode);
  let maxPressure = 0;
  for (const value of curve.P) {
    if (Number.isFinite(value)) maxPressure = Math.max(maxPressure, value);
  }
  const ratio = maxPressure > 0 && Number.isFinite(p1) ? p1 / maxPressure : 0;
  const markerTime = timeAtPressure(curve.P, curve.t, p1);
  const option: EChartsOption = {
    ...base,
    xAxis: { ...(base.xAxis as object), type: "value", name: "Time (s)" },
    yAxis: { ...(base.yAxis as object), type: "value", name: "Pressure (Pa)" },
    series: [
      {
        name: `P1/Pmax = ${ratio.toFixed(3)}`,
        type: "line",
        showSymbol: false,
        lineStyle: { width: 2 },
        data: pressureSeriesData(curve),
        markLine: {
          silent: true,
          symbol: "none",
          data: [{ yAxis: p1 }],
          label: { formatter: `P1 = ${formatPressure(p1, 3)} Pa` },
        },
        markPoint:
          markerTime === null
            ? undefined
            : {
                symbolSize: 11,
                itemStyle: { color: "#d03434" },
                data: [{ name: "P1", coord: [markerTime, p1], value: Number(p1.toFixed(4)) }],
              },
      },
    ],
  };
  return option;
}

/** Mapa de Mach del punto off-design (paridad `mach_plot`). */
export function machMapOption(
  mode: EChartsTheme,
  curves: OffDesignCurves,
  regime: string | null,
): EChartsOption {
  const base = baseChartOption(mode);
  const data: Array<[number, number]> = curves.x.map((x, index) => [x, curves.mach[index] ?? 0]);
  const last = data[data.length - 1];
  const option: EChartsOption = {
    ...base,
    xAxis: { ...(base.xAxis as object), type: "value", name: "Nozzle Position (m)" },
    yAxis: { ...(base.yAxis as object), type: "value", name: "Mach" },
    series: [
      {
        name: regime ? `Mach (Off-Design) · ${regime}` : "Mach (Off-Design)",
        type: "line",
        showSymbol: false,
        lineStyle: { width: 2, type: "dashed" },
        data,
        markPoint: last
          ? {
              symbolSize: 10,
              itemStyle: { color: "#d03434" },
              data: [{ name: "Me", coord: last, value: Number(last[1].toFixed(4)) }],
            }
          : undefined,
      },
    ],
  };
  return option;
}

/** Mapa de presión (Pe/P1t) del punto off-design (paridad `pres_plot`). */
export function pressureMapOption(
  mode: EChartsTheme,
  curves: OffDesignCurves,
  exitRatio: number | null,
): EChartsOption {
  const base = baseChartOption(mode);
  const data: Array<[number, number]> = curves.x.map((x, index) => [x, curves.pr[index] ?? 0]);
  const option: EChartsOption = {
    ...base,
    xAxis: { ...(base.xAxis as object), type: "value", name: "Nozzle Position (m)" },
    yAxis: { ...(base.yAxis as object), type: "value", name: "Pressure Ratio (Pe/P1t)" },
    series: [
      {
        name: "PR (Off-Design)",
        type: "line",
        showSymbol: false,
        lineStyle: { width: 2, type: "dashed" },
        data,
        markLine:
          exitRatio === null || !Number.isFinite(exitRatio)
            ? undefined
            : {
                silent: true,
                symbol: "none",
                data: [{ yAxis: exitRatio }],
                label: { formatter: "Pe/P1t" },
              },
      },
    ],
  };
  return option;
}
