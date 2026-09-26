import { useMemo } from "react";
import { useOptionalTheme } from "../theme";
import { cx } from "../utils/cx";
import { useECharts, type EChartsOption, type EChartsTheme } from "./useECharts";

/** Opciones base (colores del tema, grid, ejes y tooltip). */
export function baseChartOption(mode: EChartsTheme): EChartsOption {
  const dark = mode === "dark";
  const text = dark ? "#dce4ee" : "#1a1a1a";
  const muted = dark ? "#9e9e9e" : "#666666";
  const axisLine = dark ? "#474747" : "#a6a6a6";
  const splitLine = dark ? "rgba(255, 255, 255, 0.08)" : "rgba(0, 0, 0, 0.08)";

  return {
    backgroundColor: "transparent",
    textStyle: { color: text, fontFamily: "system-ui, -apple-system, Segoe UI, sans-serif", fontSize: 12 },
    grid: { left: 48, right: 16, top: 28, bottom: 32, containLabel: true },
    tooltip: {
      trigger: "axis",
      backgroundColor: dark ? "#333333" : "#f9f9fa",
      borderColor: axisLine,
      textStyle: { color: text, fontSize: 12 },
    },
    legend: { textStyle: { color: muted }, icon: "roundRect", itemWidth: 12, itemHeight: 8 },
    xAxis: {
      axisLine: { lineStyle: { color: axisLine } },
      axisTick: { lineStyle: { color: axisLine } },
      axisLabel: { color: muted },
      splitLine: { show: false },
    },
    yAxis: {
      axisLine: { show: false },
      axisLabel: { color: muted },
      splitLine: { lineStyle: { color: splitLine } },
    },
  };
}

export interface LineChartProps {
  option: EChartsOption;
  height?: number | string;
  /** Por defecto toma el modo del `ThemeProvider`. */
  theme?: EChartsTheme;
  className?: string;
  ariaLabel?: string;
}

/** Wrapper de ECharts con el tema activo (dark/light). */
export function LineChart({ option, height = 280, theme, className, ariaLabel }: LineChartProps) {
  const contextTheme = useOptionalTheme();
  const mode: EChartsTheme = theme ?? (contextTheme?.mode === "light" ? "light" : "dark");
  const merged = useMemo<EChartsOption>(
    () => ({ ...baseChartOption(mode), ...option }),
    [mode, option],
  );
  const { ref } = useECharts<HTMLDivElement>(merged, mode);

  return (
    <div
      ref={ref}
      className={cx("or-chart", className)}
      style={{ height }}
      role="img"
      aria-label={ariaLabel ?? "Gráfica"}
    />
  );
}
