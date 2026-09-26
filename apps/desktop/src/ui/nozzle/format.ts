/**
 * Formatos y utilidades numéricas con paridad literal con `front_nozDes.py`:
 * `update_results_entries` (`%.4e`/`%.4f`), la tabla GEOMETRY (`%.6f`) y la
 * interpolación inversa `interp1d(P, t, fill_value="extrapolate")`.
 */

/** Formato legacy de los resultados numéricos: `%.4e` si >=1e6, `%.4f` si no. */
export function formatLegacyValue(value: number): string {
  if (!Number.isFinite(value)) return "—";
  return value >= 1e6 ? value.toExponential(4) : value.toFixed(4);
}

/** Formato legacy de la tabla GEOMETRY (`%.6f`). */
export function formatFixed6(value: number): string {
  if (!Number.isFinite(value)) return "—";
  return value.toFixed(6);
}

/** Ratio con 4 decimales (paridad `updateMapPlots`: `f"{x:.4f}"`). */
export function formatRatio(value: number | null | undefined): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "—";
  return value.toFixed(4);
}

/** Presión en notación científica (p. ej. `1.2000e+6`). */
export function formatPressure(value: number, decimals = 4): string {
  if (!Number.isFinite(value)) return "—";
  return value.toExponential(decimals);
}

/** Porcentaje del slider off-design (`front_nozDes.updatePercentLabels`). */
export function formatPercent(value: number, decimals = 3): string {
  if (!Number.isFinite(value)) return "—";
  return value.toFixed(decimals);
}

/**
 * Tiempo correspondiente a una presión sobre la curva `p_curve`
 * (`interp1d(P, t, bounds_error=False, fill_value="extrapolate")`).
 * Si no hay cruce exacto, devuelve la muestra más próxima.
 */
export function timeAtPressure(
  pressure: number[],
  time: number[],
  target: number,
): number | null {
  if (pressure.length === 0 || time.length !== pressure.length) return null;
  for (let index = 1; index < pressure.length; index += 1) {
    const previous = pressure[index - 1];
    const current = pressure[index];
    if (previous === current) continue;
    const low = Math.min(previous, current);
    const high = Math.max(previous, current);
    if (target < low || target > high) continue;
    const ratio = (target - previous) / (current - previous);
    const candidate = time[index - 1] + ratio * (time[index] - time[index - 1]);
    if (Number.isFinite(candidate)) return candidate;
  }
  let best = 0;
  for (let index = 1; index < pressure.length; index += 1) {
    if (Math.abs(pressure[index] - target) < Math.abs(pressure[best] - target)) best = index;
  }
  return time[best] ?? null;
}

/** `[min, max]` de un array (0,0 si está vacío). */
export function extent(values: number[]): [number, number] {
  if (values.length === 0) return [0, 0];
  let min = Number.POSITIVE_INFINITY;
  let max = Number.NEGATIVE_INFINITY;
  for (const value of values) {
    if (!Number.isFinite(value)) continue;
    min = Math.min(min, value);
    max = Math.max(max, value);
  }
  if (!Number.isFinite(min) || !Number.isFinite(max)) return [0, 0];
  return [min, max];
}

/** Media aritmética (0 si está vacío o sin valores finitos). */
export function average(values: number[]): number {
  const finite = values.filter((value) => Number.isFinite(value));
  if (finite.length === 0) return 0;
  return finite.reduce((sum, value) => sum + value, 0) / finite.length;
}

/** Acota `value` a `[min, max]`. */
export function clamp(value: number, min: number, max: number): number {
  if (!Number.isFinite(value)) return min;
  const lo = Math.min(min, max);
  const hi = Math.max(min, max);
  return Math.min(Math.max(value, lo), hi);
}
