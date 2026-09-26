/**
 * Tipos y utilidades locales del módulo T2 (Nozzle Design).
 *
 * `src/api/types.ts` describe el contrato congelado, pero `nozzle.load_engine`
 * devuelve además `meanPressure` (usado por el switch "P1 medio" del legacy) y
 * deja `inputs` sin tipar; se amplía aquí sin tocar la capa `api/`.
 */

import type { NozzleLoadEngineResult, PluginEntry } from "../../api/types";

/** Texto del label cuando todavía no se ha cargado ningún motor. */
export const NO_ENGINE_LABEL = "No file has been loaded";
/** Texto del label cuando `nozzle.load_engine` responde 1003. */
export const INVALID_ENGINE_LABEL = "Invalid File";

/**
 * Payload de `nozzle.load_engine` con los extras que añade el motor.
 *
 * Se usa una intersección (no `extends`) para seguir siendo compatible si
 * `src/api/types.ts` llega a declarar `meanPressure` como requerido.
 */
export type LoadedEngine = NozzleLoadEngineResult & {
  /** Presión media del motor (`results.meanPressure`); fallback sobre `p_curve`. */
  meanPressure?: number;
};

/** Resultado de `plugins.list {library:"NozzleLibrary"}`. */
export type NozzlePlugins = Record<string, PluginEntry>;

/** Claves (`labels` del plugin) de los inputs dinámicos de un tipo de tobera. */
export function specKeys(plugin: PluginEntry | undefined): string[] {
  return plugin ? Object.values(plugin.labels) : [];
}

/** Clave de persistencia en `config.json`: `<tipo>_<clave>` (paridad app.py). */
export function specConfigKey(nozzleType: string, specKey: string): string {
  return `${nozzleType}_${specKey}`;
}

/** Valor numérico de `inputs` (número o cadena); `NaN` si falta o no es válido. */
export function engineInputNumber(inputs: Record<string, unknown>, key: string): number {
  const value = inputs[key];
  if (typeof value === "number") return value;
  if (typeof value === "string") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : Number.NaN;
  }
  return Number.NaN;
}

/** `true` si `value` está dentro de `[min, max]` (rangos degenerados incluidos). */
export function withinRange(value: number, min: number, max: number): boolean {
  if (!Number.isFinite(value)) return false;
  return value >= Math.min(min, max) && value <= Math.max(min, max);
}

/** `basename` compatible con rutas Windows y POSIX. */
export function fileNameOf(path: string): string {
  const parts = path.split(/[\\/]/);
  return parts[parts.length - 1] || path;
}
