/**
 * Formato numérico heredado de T0: `f"{v:.4e}"` si el valor es ≥ 1e6 y
 * `f"{v:.4f}"` en caso contrario. El exponente reproduce el estilo de Python
 * (`1.2345e+06`), no el de `Number.prototype.toExponential` (`1.2345e+6`).
 */

/** Formatea un resultado adiabático igual que las entradas `readonly` del legacy. */
export function formatLegacyResult(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "";
  if (value >= 1e6) return pythonExponential(value, 4);
  return value.toFixed(4);
}

/** `toExponential` con signo explícito y exponente a dos dígitos (estilo Python). */
export function pythonExponential(value: number, digits = 4): string {
  const raw = value.toExponential(digits);
  const [mantissa, exponent = "+0"] = raw.split("e");
  const sign = exponent.startsWith("-") ? "-" : "+";
  const magnitude = exponent.replace(/^[+-]/, "").padStart(2, "0");
  return `${mantissa}e${sign}${magnitude}`;
}
