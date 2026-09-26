/**
 * Semántica numérica heredada de `legacy/functions.py`:
 * - `get_entry_value`: entry vacío -> "0".
 * - `validate_scientific_notation`: `^-?\d*\.?\d+(?:[eE][-+]?\d+)?$`.
 */

/** Valor de un campo de texto vacío -> "0" (paridad con `get_entry_value`). */
export function getEntryValue(raw: string | null | undefined): string {
  const value = raw ?? "";
  return value.trim() === "" ? "0" : value;
}

/** Valida notación decimal/científica (acepta `-`, `.5`, `1e-3`, `1.2E+4`). */
export function validateScientificNotation(raw: string | null | undefined): boolean {
  return /^-?\d*\.?\d+(?:[eE][-+]?\d+)?$/.test((raw ?? "").trim());
}

/** Reemplaza comas por puntos (paridad con la UI original de las ventanas DB). */
export function normalizeNumericInput(raw: string): string {
  return raw.replace(/,/g, ".");
}

/** Convierte texto a número aplicando `getEntryValue` y coma->punto. */
export function parseNumeric(raw: string | null | undefined): number {
  const value = Number(normalizeNumericInput(getEntryValue(raw)));
  return Number.isFinite(value) ? value : 0;
}

/** Formatea un número con un máximo de decimales, sin ceros sobrantes. */
export function formatNumber(value: number, decimals = 3): string {
  if (!Number.isFinite(value)) return "—";
  const fixed = value.toFixed(decimals);
  return fixed.replace(/\.?0+$/, "") || "0";
}

/** Formatea con notación científica (paridad con las tablas del original). */
export function formatScientific(value: number, decimals = 4): string {
  if (!Number.isFinite(value)) return "—";
  return value.toExponential(decimals);
}
