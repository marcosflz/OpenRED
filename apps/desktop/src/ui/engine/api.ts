/**
 * Capa tipada sobre `src/api/engine.ts` para el módulo Engine Design (T1).
 *
 * Los tests del módulo mockean este fichero (`vi.mock`) para controlar las
 * respuestas del motor sin tocar `src/api/**`.
 */

import { listen, type UnlistenFn } from "@tauri-apps/api/event";
import { isTauri, onEngineEventOf, request } from "../../api/engine";
import type {
  EngineCalculateResult,
  EngineEventMap,
  EngineGeometryResult,
  EnginePayload,
  PluginsListResult,
  PropellantRow,
} from "../../api/types";
import type { PluginsMap, PropellantData } from "./helpers";

export type SpecValues = Record<string, number>;

export interface EngineGeometryParams {
  propellant: string;
  grain: string;
  spec: SpecValues;
}

export interface EngineCalculateParams {
  propellant: string;
  grain: string;
  spec: SpecValues;
  propellantData: PropellantData;
}

/** `db.propellants.list` → filas de la tabla `propelente`. */
export async function listPropellants(): Promise<PropellantRow[]> {
  const result = await request<{ items: PropellantRow[] }>("db.propellants.list");
  return result.items ?? [];
}

/** `plugins.list {library:"GrainLibrary"}` → `{<grain>: {labels}}`. */
export async function listGrainPlugins(): Promise<PluginsMap> {
  const result = await request<PluginsListResult>("plugins.list", { library: "GrainLibrary" });
  return result.plugins ?? {};
}

export function fetchGeometry(params: EngineGeometryParams): Promise<EngineGeometryResult> {
  return request<EngineGeometryResult>("engine.geometry", {
    propellant: params.propellant,
    grain: params.grain,
    spec: params.spec,
  });
}

export function calculateEngine(params: EngineCalculateParams): Promise<EngineCalculateResult> {
  return request<EngineCalculateResult>("engine.calculate", {
    propellant: params.propellant,
    grain: params.grain,
    spec: params.spec,
    propellantData: params.propellantData,
  });
}

/** `engine.save {name, payload}` → ruta escrita (`Engines/<name>.json`). */
export async function saveEngine(name: string, payload: EnginePayload): Promise<string> {
  const result = await request<{ path: string }>("engine.save", { name, payload });
  return result.path;
}

export function onConsole(
  handler: (event: EngineEventMap["console"]) => void,
): Promise<UnlistenFn> {
  return onEngineEventOf("console", handler);
}

export function onProgress(
  handler: (event: EngineEventMap["progress"]) => void,
): Promise<UnlistenFn> {
  return onEngineEventOf("progress", handler);
}

/** `{id, method, phase}` emitido por Rust en `engine-request` (cancelar por id). */
export interface EngineRequestEvent {
  id: number;
  method: string;
  phase: string;
}

export async function onEngineRequest(
  handler: (event: EngineRequestEvent) => void,
): Promise<UnlistenFn> {
  if (!isTauri()) return () => {};
  return listen<EngineRequestEvent>("engine-request", (event) => handler(event.payload));
}
