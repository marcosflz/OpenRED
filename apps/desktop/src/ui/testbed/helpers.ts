/**
 * Tipos y utilidades del módulo T4 (Testing Bed).
 *
 * El motor real (`engine/openred_engine/services/testbed.py`) publica el estado
 * con `checklistEnabled` y los LEDs como cadenas (`"off" | "green" | "blue"`),
 * mientras que `src/api/types.ts` refleja la primera versión del contrato
 * (`leds.boolean`, sin `checklistEnabled`). Este módulo normaliza ambos.
 */

import type { ChecklistItem, ChecklistResult, PortInfo, SerialRecord } from "../../api/types";

/** Color de un LED del banco de pruebas (protocolo ESP32). */
export type LedColor = "off" | "green" | "blue";

export interface TestbedLeds {
  serial: LedColor;
  wifi: LedColor;
}

/** Estado de la máquina de protocolo visible en la UI (T4-4). */
export interface TestbedStatus {
  connected: boolean;
  wifiReady: boolean;
  recording: boolean;
  checklistEnabled: boolean;
  checklistComplete: boolean;
  leds: TestbedLeds;
}

/** Datos del test en curso; `testbed.run` los completa y `event/state` los refresca. */
export interface TestbedRunInfo {
  testFile?: string;
  nozzle?: string;
  engine?: string;
  maxThrust?: number;
  maxTemp?: number;
}

export const NO_PORTS = "No COM ports found";

export const INITIAL_STATUS: TestbedStatus = {
  connected: false,
  wifiReady: false,
  recording: false,
  checklistEnabled: false,
  checklistComplete: false,
  leds: { serial: "off", wifi: "off" },
};

/** Colores de los LEDs (indicador de la UI). */
export const LED_COLORS: Record<LedColor, string> = {
  green: "#4caf7d",
  blue: "#4d9fdc",
  off: "#6c757d",
};

/** Etiquetas legibles de los LEDs. */
export const LED_LABELS: Record<LedColor, string> = {
  green: "Verde",
  blue: "Azul",
  off: "Apagado",
};

/** Número máximo de líneas conservadas en el monitor serie. */
export const MAX_CONSOLE_LINES = 2000;

/** Guion de ejemplo del transporte simulado (`testbed.mock`, T4-9). */
export const DEMO_SCRIPT: readonly string[] = [
  "SERIAL STARTED",
  "RESET",
  "TEST-BENCH CONNECTED",
  "t(s): 0.025 F(kg): 0.049 T(K): 301.4",
  "t(s): 0.050 F(kg): 0.062 T(K): 302.0",
  "t(s): 0.075 F(kg): 0.075 T(K): 302.8",
  "t(s): 0.100 F(kg): 0.089 T(K): 303.7",
  "t(s): 0.125 F(kg): 0.102 T(K): 304.9",
  "t(s): 0.150 F(kg): 0.118 T(K): 306.2",
  "t(s): 0.175 F(kg): 0.131 T(K): 307.6",
  "t(s): 0.200 F(kg): 0.145 T(K): 309.1",
];

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

/** Normaliza el valor de un LED (cadenas actuales y booleanos del contrato antiguo). */
export function readLed(value: unknown): LedColor {
  if (value === true) return "green";
  if (value === "green" || value === "blue") return value;
  return "off";
}

/** Lee los campos conocidos de `event/state` / `testbed.state`. */
export function readStatus(payload: unknown): Partial<TestbedStatus> {
  const raw = asRecord(payload);
  const status: Partial<TestbedStatus> = {};
  if (typeof raw.connected === "boolean") status.connected = raw.connected;
  if (typeof raw.wifiReady === "boolean") status.wifiReady = raw.wifiReady;
  if (typeof raw.recording === "boolean") status.recording = raw.recording;
  if (typeof raw.checklistEnabled === "boolean") status.checklistEnabled = raw.checklistEnabled;
  if (typeof raw.checklistComplete === "boolean") status.checklistComplete = raw.checklistComplete;
  if (raw.leds !== null && typeof raw.leds === "object") {
    const leds = asRecord(raw.leds);
    status.leds = { serial: readLed(leds.serial), wifi: readLed(leds.wifi) };
  }
  return status;
}

/** Lee los datos del test (`testFile`, `nozzle`, `maxThrust`, …) si vienen informados. */
export function readRunInfo(payload: unknown): Partial<TestbedRunInfo> {
  const raw = asRecord(payload);
  const info: Partial<TestbedRunInfo> = {};
  if (typeof raw.testFile === "string" && raw.testFile !== "") info.testFile = raw.testFile;
  if (typeof raw.nozzle === "string" && raw.nozzle !== "") info.nozzle = raw.nozzle;
  if (typeof raw.engine === "string" && raw.engine !== "") info.engine = raw.engine;
  if (typeof raw.maxThrust === "number" && Number.isFinite(raw.maxThrust)) info.maxThrust = raw.maxThrust;
  if (typeof raw.maxTemp === "number" && Number.isFinite(raw.maxTemp)) info.maxTemp = raw.maxTemp;
  return info;
}

/** `"COM3 - USB Serial Device"` (formato legacy de `front_test.monitor_ports`). */
export function portLabel(port: PortInfo): string {
  return `${port.device} - ${port.description}`;
}

/**
 * Convierte la lista de puertos del motor (`string[]` ya formateada en
 * `event/ports`, u objetos `{device, description}` de `testbed.list_ports`) al
 * formato del desplegable legacy, con `"No COM ports found"` si está vacía.
 */
export function normalizePortList(value: unknown): string[] {
  if (!Array.isArray(value) || value.length === 0) return [NO_PORTS];
  const labels = value
    .map((item) => {
      if (typeof item === "string") return item;
      const raw = asRecord(item);
      return portLabel({
        device: String(raw.device ?? ""),
        description: String(raw.description ?? ""),
      });
    })
    .filter((label) => label.trim() !== "");
  return labels.length > 0 ? labels : [NO_PORTS];
}

/** Extrae `"COM3"` de `"COM3 - USB Serial Device"` (igual que `com_port_changed`). */
export function portDevice(label: string): string {
  return label.split(" - ")[0].trim();
}

/** Normaliza la lista de items de la checklist. */
export function readChecklistItems(value: unknown): ChecklistItem[] {
  if (!Array.isArray(value)) return [];
  return value.map((entry) => {
    const raw = asRecord(entry);
    return { text: String(raw.text ?? ""), done: raw.done === true };
  });
}

/** Normaliza el resultado de `testbed.checklist.load`. */
export function readChecklistResult(value: unknown): ChecklistResult {
  const raw = asRecord(value);
  const title = typeof raw.title === "string" && raw.title !== "" ? raw.title : "TEST CHECKLIST";
  return { title, items: readChecklistItems(raw.items) };
}

/** Normaliza `event/record {t,F,T}`; devuelve `null` si los valores no son numéricos. */
export function readRecord(payload: unknown): SerialRecord | null {
  const raw = asRecord(payload);
  const t = Number(raw.t);
  const F = Number(raw.F);
  const T = Number(raw.T);
  if (!Number.isFinite(t) || !Number.isFinite(F) || !Number.isFinite(T)) return null;
  return { t, F, T };
}
