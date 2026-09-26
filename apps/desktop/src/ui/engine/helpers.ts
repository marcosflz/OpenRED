/**
 * Utilidades puras del módulo Engine Design (T1).
 *
 * Reproduce la semántica de `legacy/front_modules/front_propDes.py`:
 * - 7 entradas comunes (`P0, Rt, Rc, Lc, dt, dh, ItMax`) con los mismos
 *   valores por defecto, aunque el RPC use `R2`/`It` para Rc/ItMax.
 * - Entradas dinámicas por geometría (`<grain>_<clave>` en `config.json`,
 *   `<clave>` a secas en el `spec` del RPC).
 * - Formato de tiempo de la tabla con los decimales de `dt`.
 */

import type { EngineTreeData, PluginEntry, PropellantRow } from "../../api/types";
import { getEntryValue, parseNumeric } from "../../utils/numbers";

/** Pestaña de `config.json` que persiste el módulo. */
export const TAB_KEY = "tab_1";

export type CommonKey = "P0" | "Rt" | "Rc" | "Lc" | "dt" | "dh" | "ItMax";

export type CommonValues = Record<CommonKey, string>;

/** `{grain: {clave: valor}}` — valores de todas las geometrías conocidas. */
export type GrainValues = Record<string, Record<string, string>>;

export type PluginsMap = Record<string, PluginEntry>;

/** Valores por defecto del legacy (mismos que `legacy/workingDirectory/config.json`). */
export const DEFAULT_COMMON: CommonValues = {
  P0: "1e5",
  Rt: "0.0065",
  Rc: "0.016",
  Lc: "0.1",
  dt: "0.005",
  dh: "0.0001",
  ItMax: "10000",
};

export interface CommonField {
  key: CommonKey;
  label: string;
}

export const COMMON_FIELDS: readonly CommonField[] = [
  { key: "P0", label: "Ambient Pressure (Pa)" },
  { key: "Rt", label: "Throat Radius (m)" },
  { key: "Rc", label: "Case Radius (m)" },
  { key: "Lc", label: "Length (mm)" },
  { key: "dt", label: "Time Step (s)" },
  { key: "dh", label: "Space Step (m)" },
  { key: "ItMax", label: "Maximum Iterations" },
];

/** Clave RPC (`engine.*`) para cada clave de `config.json` (Rc→R2, ItMax→It). */
export const RPC_KEYS: Record<CommonKey, string> = {
  P0: "P0",
  Rt: "Rt",
  Rc: "R2",
  Lc: "Lc",
  dt: "dt",
  dh: "dh",
  ItMax: "It",
};

export interface ParsedTab1 {
  propellant?: string;
  geoConfig?: string;
  common: Partial<CommonValues>;
  grainValues: GrainValues;
}

/** Lee `config.tabs.tab_1` sin aplicar valores por defecto (solo lo presente). */
export function parseTab1(
  config: Record<string, unknown> | undefined,
  grains: readonly string[],
): ParsedTab1 {
  const common: Partial<CommonValues> = {};
  for (const field of COMMON_FIELDS) {
    const value = config?.[field.key];
    if (typeof value === "string" || typeof value === "number") {
      common[field.key] = String(value);
    }
  }

  const propellant =
    typeof config?.propellant === "string" && config.propellant ? config.propellant : undefined;
  const geoConfig =
    typeof config?.geoConfig === "string" && config.geoConfig ? config.geoConfig : undefined;

  const grainValues: GrainValues = {};
  const ordered = [...grains].sort((a, b) => b.length - a.length);
  for (const [key, value] of Object.entries(config ?? {})) {
    if (typeof value !== "string" && typeof value !== "number") continue;
    const grain = ordered.find((name) => key.startsWith(`${name}_`));
    if (!grain) continue;
    const labelKey = key.slice(grain.length + 1);
    if (!labelKey) continue;
    grainValues[grain] = { ...(grainValues[grain] ?? {}), [labelKey]: String(value) };
  }

  return { propellant, geoConfig, common, grainValues };
}

/** Garantiza una entrada por cada `clave` de labels de todas las geometrías. */
export function ensureGrainValues(grainValues: GrainValues, plugins: PluginsMap): GrainValues {
  const next: GrainValues = { ...grainValues };
  for (const [grain, entry] of Object.entries(plugins)) {
    const values = { ...(next[grain] ?? {}) };
    for (const labelKey of Object.values(entry.labels ?? {})) {
      if (values[labelKey] === undefined) values[labelKey] = "0";
    }
    next[grain] = values;
  }
  return next;
}

/** `{"<grain>_<clave>": "valor"}` para TODAS las geometrías (paridad config.json). */
export function grainConfigPatch(grainValues: GrainValues, plugins: PluginsMap): Record<string, string> {
  const patch: Record<string, string> = {};
  for (const [grain, entry] of Object.entries(plugins)) {
    for (const labelKey of Object.values(entry.labels ?? {})) {
      patch[`${grain}_${labelKey}`] = grainValues[grain]?.[labelKey] ?? "0";
    }
  }
  return patch;
}

function entryNumber(raw: string | undefined): number {
  return parseNumeric(getEntryValue(raw));
}

/** `spec` del RPC: comunes con nombres RPC + claves de labels de la geometría. */
export function buildSpec(
  common: CommonValues,
  values: Record<string, string> | undefined,
  labelKeys: readonly string[],
): Record<string, number> {
  const spec: Record<string, number> = {
    [RPC_KEYS.P0]: entryNumber(common.P0),
    [RPC_KEYS.Rt]: entryNumber(common.Rt),
    [RPC_KEYS.Rc]: entryNumber(common.Rc),
    [RPC_KEYS.Lc]: entryNumber(common.Lc),
    [RPC_KEYS.dt]: entryNumber(common.dt),
    [RPC_KEYS.dh]: entryNumber(common.dh),
    [RPC_KEYS.ItMax]: entryNumber(common.ItMax),
  };
  for (const key of labelKeys) spec[key] = entryNumber(values?.[key] ?? "0");
  return spec;
}

/**
 * Decimales del tiempo en la tabla: `len(str(dt).split('.')[-1])` del legacy
 * (con el `dt` numérico ya parseado, como `float(get_entry_value(...))`).
 */
export function timeDecimals(dt: string): number {
  const text = String(entryNumber(dt));
  const dot = text.indexOf(".");
  return dot < 0 ? 0 : text.length - dot - 1;
}

export interface TreeRow {
  time: string;
  pressure: number;
  massFlow: number;
  mass: number;
}

/** Filas de la tabla DATA a partir de `results.tree_data`. */
export function treeRows(tree: EngineTreeData | undefined, decimals: number): TreeRow[] {
  if (!tree) return [];
  const times = tree["Time (s)"] ?? [];
  const pressure = tree["Pressure (Pa)"] ?? [];
  const massFlow = tree["Mass Flow (kg/s)"] ?? [];
  const mass = tree["Mass (kg)"] ?? [];
  return times.map((value, index) => ({
    time: value.toFixed(decimals),
    pressure: pressure[index] ?? 0,
    massFlow: massFlow[index] ?? 0,
    mass: mass[index] ?? 0,
  }));
}

export function formatMetric(value: number | undefined): string {
  if (value === undefined || !Number.isFinite(value)) return "";
  return String(value);
}

export function formatCell(value: number): string {
  return Number.isFinite(value) ? String(value) : "—";
}

/* ------------------------------------------------------------------ */
/* Propelentes                                                         */
/* ------------------------------------------------------------------ */

/** Quita el sufijo `" (id)"` (equivalente a `re.sub(r'\s*\(\d+\)\s*$', '', ...)`). */
export function cleanPropellantName(text: string): string {
  return text.replace(/\s*\(\d+\)\s*$/, "").trim();
}

/** Texto del selector: `"Nombre (id)"`. */
export function propellantLabel(row: PropellantRow): string {
  return `${row.Propelente} (${row.id})`;
}

/** Resuelve la selección actual contra la lista (mantiene el id si sigue existiendo). */
export function resolvePropellant(current: string, rows: PropellantRow[]): string {
  if (rows.length === 0) return current;
  if (rows.some((row) => propellantLabel(row) === current)) return current;
  const clean = cleanPropellantName(current);
  const byName = clean ? rows.find((row) => row.Propelente === clean) : undefined;
  return propellantLabel(byName ?? rows[0]);
}

export function findPropellant(rows: PropellantRow[], value: string): PropellantRow | null {
  const exact = rows.find((row) => propellantLabel(row) === value);
  if (exact) return exact;
  const clean = cleanPropellantName(value);
  return rows.find((row) => row.Propelente === clean) ?? null;
}

export interface PropellantData {
  a: number;
  n: number;
  R: number;
  T1: number;
  cChar: number;
  rho_b: number;
  P1_min: number;
  P1_max: number;
}

/** Mapeo de columnas de `db.propellants.list` a `propellantData` del RPC. */
export function toPropellantData(row: PropellantRow): PropellantData {
  return {
    a: parseNumeric(String(row.a)),
    n: parseNumeric(String(row.n)),
    R: parseNumeric(String(row.R)),
    T1: parseNumeric(String(row.T_ad)),
    cChar: parseNumeric(String(row.cChar)),
    rho_b: parseNumeric(String(row.Density)),
    P1_min: parseNumeric(String(row.P1_min)),
    P1_max: parseNumeric(String(row.P1_max)),
  };
}
