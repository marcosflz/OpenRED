import * as echarts from "echarts";
import { useEffect, useRef, type RefObject } from "react";

export type EChartsOption = echarts.EChartsOption;
export type EChartsTheme = "dark" | "light";

export interface UseEChartsResult<T extends HTMLElement> {
  /** Ref para el contenedor del chart. */
  ref: RefObject<T | null>;
  /** Instancia viva de ECharts (o `null`). */
  getChart: () => echarts.ECharts | null;
}

/**
 * Hook ECharts: inicializa, reacciona a `option`/tema, redimensiona con
 * `ResizeObserver` y libera la instancia al desmontar.
 */
export function useECharts<T extends HTMLElement = HTMLDivElement>(
  option: EChartsOption,
  theme: EChartsTheme = "dark",
): UseEChartsResult<T> {
  const ref = useRef<T>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    const chart = echarts.init(element, theme === "dark" ? "dark" : undefined);
    chartRef.current = chart;

    let observer: ResizeObserver | null = null;
    if (typeof ResizeObserver !== "undefined") {
      observer = new ResizeObserver(() => chart.resize());
      observer.observe(element);
    }
    return () => {
      observer?.disconnect();
      chart.dispose();
      chartRef.current = null;
    };
  }, [theme]);

  useEffect(() => {
    chartRef.current?.setOption(option, { notMerge: true });
  }, [option]);

  return { ref, getChart: () => chartRef.current };
}
