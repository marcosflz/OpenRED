/**
 * Utilidades puras del módulo CAD (T3).
 *
 * El motor (`cad.load_nozzle`) devuelve `fields` con `type` `select|number|checkbox`,
 * `suggested` (valores de `tabs.tab_3` de `config.json`) y `checks` (redundante con
 * los checkbox de `fields`, se fusiona por robustez). Estas funciones normalizan
 * esos datos, construyen el `settings` de `cad.views`/`cad.export` y el patch de
 * `tab_3` con las claves exactas del legacy (`legacy/app.py`, `legacy/front_modules/front_cad.py`).
 */

export type CadFieldType = "select" | "number" | "checkbox";

export interface CadFieldDef {
  key: string;
  label: string;
  type: CadFieldType | string;
  options?: string[];
  default?: unknown;
}

/** Respuesta de `cad.load_nozzle` (incluye `message` en AS-Nozzle). */
export interface CadLoadPayload {
  config: Record<string, unknown>;
  architecture?: string;
  fields?: CadFieldDef[];
  checks?: CadFieldDef[];
  suggested?: Record<string, unknown>;
  message?: string;
}

export interface CadValues {
  values: Record<string, string>;
  checks: Record<string, boolean>;
}

export type ExportKind = "engine" | "cover" | "tools";

/** Debounce de `cad.views` tras un cambio de campo/checkbox (T3-2). */
export const VIEW_DEBOUNCE_MS = 150;

/** Texto exacto que devuelve el motor para AS-Nozzle (T3-5). */
export const AS_NOZZLE_MESSAGE = "AS-Nozzle architecture is not supported by the CAD module.";

export const EXPORT_LABELS: Record<ExportKind, string> = {
  engine: "ENGINE",
  cover: "COVER",
  tools: "TOOLS",
};

/** `1`, `"1"`, `true`, `"true"`… -> `true` (paridad con `front_cad`/`app.py`). */
export function isTruthySetting(value: unknown): boolean {
  if (value === true || value === 1) return true;
  const text = String(value ?? "")
    .trim()
    .toLowerCase();
  return text === "1" || text === "true" || text === "on" || text === "yes";
}

/** Fusiona `checks` en `fields` sin duplicar claves (el motor los repite). */
export function mergeFields(fields: CadFieldDef[], checks: CadFieldDef[]): CadFieldDef[] {
  const extra = checks.filter((check) => !fields.some((field) => field.key === check.key));
  return [...fields, ...extra];
}

/**
 * Inicializa los controles: valores de `tab_3` en memoria > `suggested` del motor >
 * default del campo. Los numéricos sin valor quedan vacíos (NumberField: vacío -> "0",
 * paridad con `build_entries` del legacy).
 */
export function applyFields(
  fields: CadFieldDef[],
  saved: Record<string, unknown>,
  suggested: Record<string, unknown>,
): CadValues {
  const values: Record<string, string> = {};
  const checks: Record<string, boolean> = {};

  for (const field of fields) {
    const hasSaved = Object.prototype.hasOwnProperty.call(saved, field.key);
    const hasSuggested = Object.prototype.hasOwnProperty.call(suggested, field.key);
    const raw = hasSaved ? saved[field.key] : hasSuggested ? suggested[field.key] : undefined;

    if (field.type === "checkbox") {
      checks[field.key] = raw === undefined ? field.default !== false : isTruthySetting(raw);
      continue;
    }
    if (field.type === "select") {
      const fallback = String(field.default ?? field.options?.[0] ?? "");
      values[field.key] = raw === undefined || raw === "" ? fallback : String(raw);
      continue;
    }
    values[field.key] = raw === undefined ? "" : String(raw);
  }

  return { values, checks };
}

/** `settings` de `cad.views`/`cad.export` (checkbox como 1/0, como el legacy). */
export function collectSettings(
  values: Record<string, string>,
  checks: Record<string, boolean>,
): Record<string, string | number> {
  const settings: Record<string, string | number> = { ...values };
  for (const [key, checked] of Object.entries(checks)) {
    settings[key] = checked ? 1 : 0;
  }
  return settings;
}

/**
 * Patch de `tabs.tab_3` con las claves exactas del legacy: `NozzleConfig`, `type`
 * y todos los settings como cadenas; los checkbox como "1"/"0" (requisito T3-4).
 */
export function collectPatch(
  fileName: string,
  values: Record<string, string>,
  checks: Record<string, boolean>,
): Record<string, string> {
  const patch: Record<string, string> = { NozzleConfig: fileName, ...values };
  for (const [key, checked] of Object.entries(checks)) {
    patch[key] = checked ? "1" : "0";
  }
  return patch;
}

/** Último segmento de una ruta (`C:\a\BN1.json` -> `BN1.json`). */
export function baseName(path: string): string {
  const parts = path.split(/[\\/]/);
  return parts[parts.length - 1] || path;
}

/** Nombre sin extensión (`BN1.json` -> `BN1`). */
export function fileStem(name: string): string {
  return name.replace(/\.[^.]+$/, "") || name;
}

/** `<nozzle>_ENGINE_CAD.csv` (por defecto en el diálogo "Guardar como"). */
export function defaultExportName(fileName: string | null, kind: ExportKind): string {
  const stem = fileName ? fileStem(fileName) : "nozzle";
  return `${stem}_${EXPORT_LABELS[kind]}_CAD.csv`;
}
