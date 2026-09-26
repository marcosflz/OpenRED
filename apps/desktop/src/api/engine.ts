/**
 * Cliente RPC tipado sobre el contrato IPC (`contracts/methods.md`).
 *
 * - `request()` habla con el sidecar a través del comando Rust
 *   `engine_request`. Fuera de Tauri (dev en navegador / vitest) responde el
 *   backend simulado de `src/api/mock.ts`.
 * - `invokeCommand()` cubre los comandos nativos (diálogos, logs, estado).
 * - `onEngineEvent()` suscribe a las notificaciones `engine-event`.
 */

import { invoke } from "@tauri-apps/api/core";
import { listen, type UnlistenFn } from "@tauri-apps/api/event";
import { toRpcError } from "./errors";
import { mockInvoke, mockRequest } from "./mock";
import type { AppInfo, EngineEvent, EngineEventName, EngineStatus, FileFilter } from "./types";

export { RPC_CANCELLED, RpcError, isCancel, toRpcError } from "./errors";
export type { RpcErrorShape } from "./errors";
export type {
  AdiabaticCalculateParams,
  AdiabaticCalculateResult,
  AdiabaticComponentInfo,
  AppInfo,
  BurningRateResult,
  CadCheck,
  CadExportResult,
  CadField,
  CadLoadResult,
  CadViews,
  CadViewsResult,
  ChecklistItem,
  ChecklistResult,
  ComponentRow,
  EngineArrays,
  EngineCalculateResult,
  EngineEvent,
  EngineEventMap,
  EngineEventName,
  EngineFigures,
  EngineGeometryResult,
  EngineInputs,
  EngineLoadResult,
  EnginePayload,
  EngineResults,
  EngineStatus,
  EngineTreeData,
  FileFilter,
  NozzleCalculateResult,
  NozzleLoadEngineResult,
  NozzleOpPointResult,
  PluginEntry,
  PluginsListResult,
  PortInfo,
  PropellantRow,
  SerialLeds,
  SerialRecord,
  SerialState,
  Tab0Config,
  Tab1Config,
  Tab2Config,
  Tab3Config,
  TabConfig,
  TabKey,
  TabsConfig,
  TestbedRunResult,
  WorkspaceConfig,
  WorkspaceFile,
  WorkspaceGetResult,
  WorkspaceListResult,
  WorkspaceLoadConfigResult,
  WorkspaceSaveResult,
  WorkspaceSetDirResult,
} from "./types";

/** `true` cuando la UI corre dentro del webview de Tauri. */
export function isTauri(): boolean {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
}

/**
 * Ejecuta un método del motor. Rechaza con `RpcError` normalizado.
 *
 * @example
 * const info = await request<AppInfo>("app.info");
 */
export async function request<T = unknown>(
  method: string,
  params: Record<string, unknown> = {},
): Promise<T> {
  if (!isTauri()) return mockRequest<T>(method, params);
  try {
    return await invoke<T>("engine_request", { method, params });
  } catch (error) {
    throw toRpcError(error);
  }
}

/** Ejecuta un comando nativo de Tauri (`pick_workdir`, `engine_status`, …). */
export async function invokeCommand<T = unknown>(
  command: string,
  args: Record<string, unknown> = {},
): Promise<T> {
  if (!isTauri()) return mockInvoke<T>(command, args);
  try {
    return await invoke<T>(command, args);
  } catch (error) {
    throw toRpcError(error);
  }
}

/* ------------------------------------------------------------------ */
/* Atajos del contrato                                                 */
/* ------------------------------------------------------------------ */

export const appInfo = () => request<AppInfo>("app.info");

export const engineStatus = () => invokeCommand<EngineStatus>("engine_status");

export const engineRestart = () => invokeCommand<EngineStatus>("engine_restart");

export const pickWorkdir = () => invokeCommand<string | null>("pick_workdir");

export const pickFile = (filters?: FileFilter[]) =>
  invokeCommand<string | null>("pick_file", filters ? { filters } : {});

export const pickSaveFile = (defaultName?: string) =>
  invokeCommand<string | null>("pick_save_file", defaultName ? { defaultName } : {});

export const saveWorkdir = (path: string) => invokeCommand<void>("save_workdir", { path });

export const openLogsFolder = () => invokeCommand<void>("open_logs_folder");

/** Pide el apagado ordenado del sidecar y cierra la ventana. */
export async function exitApp(): Promise<void> {
  try {
    await request("app.shutdown");
  } catch {
    // El motor puede haberse cerrado ya; el cierre de la ventana manda.
  }
  try {
    window.close();
  } catch {
    // `window.close` puede estar bloqueado fuera de Tauri.
  }
}

/* ------------------------------------------------------------------ */
/* Eventos                                                             */
/* ------------------------------------------------------------------ */

export type EngineEventHandler<E extends EngineEvent = EngineEvent> = (event: E) => void;

/**
 * Suscribe un handler al evento `engine-event`. Devuelve la función para
 * desuscribirse (no-op fuera de Tauri).
 */
export async function onEngineEvent<E extends EngineEvent = EngineEvent>(
  handler: EngineEventHandler<E>,
): Promise<UnlistenFn> {
  if (!isTauri()) return () => {};
  return listen<E>("engine-event", (event) => handler(event.payload));
}

/** Igual que `onEngineEvent`, filtrando por nombre de evento. */
export async function onEngineEventOf<N extends EngineEventName>(
  name: N,
  handler: (event: EngineEvent<N>) => void,
): Promise<UnlistenFn> {
  return onEngineEvent((event) => {
    if (event.name === name) handler(event as EngineEvent<N>);
  });
}
