/**
 * Tipos de dominio compartidos entre la UI y el motor (contrato IPC v1,
 * `contracts/methods.md`). Los valores numéricos de `config.json` viajan como
 * cadenas (paridad G3), por eso se usa el alias `Numeric`.
 */

export type Numeric = number | string;

/* ------------------------------------------------------------------ */
/* workspace                                                           */
/* ------------------------------------------------------------------ */

export type TabKey = "tab_0" | "tab_1" | "tab_2" | "tab_3";

export interface Tab0Config {
  reactivos: Array<[Numeric, string]>;
  productos: Array<[Numeric, string]>;
  initial_temp: Numeric;
  temp_Int_step: Numeric;
  temp_guess: Numeric;
}

export interface Tab1Config {
  propellant?: string;
  geoConfig?: string;
  P0?: Numeric;
  Rt?: Numeric;
  Rc?: Numeric;
  Lc?: Numeric;
  dt?: Numeric;
  dh?: Numeric;
  ItMax?: Numeric;
  [key: string]: unknown;
}

export interface Tab2Config {
  engine_config?: string;
  SwitchState?: string;
  P1?: Numeric;
  n_res?: Numeric;
  nozzle_type?: string;
  [key: string]: unknown;
}

export interface Tab3Config {
  NozzleConfig?: string;
  type?: string;
  n_conv?: Numeric;
  [key: string]: unknown;
}

export type TabConfig =
  | Tab0Config
  | Tab1Config
  | Tab2Config
  | Tab3Config
  | Record<string, unknown>;

export interface TabsConfig {
  tab_0?: Tab0Config;
  tab_1?: Tab1Config;
  tab_2?: Tab2Config;
  tab_3?: Tab3Config;
  [key: string]: unknown;
}

/** `config.json` del directorio de trabajo; el motor lo guarda tal cual. */
export interface WorkspaceConfig {
  tabs: TabsConfig;
  [key: string]: unknown;
}

export interface WorkspaceGetResult {
  workdir: string | null;
  workdirSelected: boolean;
}

export interface WorkspaceSetDirResult {
  workdir: string;
  created: string[];
  hasConfig: boolean;
  config: WorkspaceConfig | null;
}

export interface WorkspaceLoadConfigResult {
  config: WorkspaceConfig | null;
  hasConfig: boolean;
}

export interface WorkspaceSaveResult {
  path: string;
}

export interface WorkspaceFile {
  name: string;
  size: number;
  mtime: number;
}

export interface WorkspaceListResult {
  files: WorkspaceFile[];
}

/* ------------------------------------------------------------------ */
/* app                                                                 */
/* ------------------------------------------------------------------ */

export interface AppInfo {
  version: string;
  dataDir: string;
  resourceDir: string;
  workdir: string | null;
  workdirSelected: boolean;
}

export interface AppPingResult extends AppInfo {
  pid: number;
  python: string;
}

export interface EngineStatus {
  running: boolean;
  pid?: number | null;
  version?: string | null;
  lastError?: string | null;
  [key: string]: unknown;
}

export interface FileFilter {
  name: string;
  extensions: string[];
}

/* ------------------------------------------------------------------ */
/* db                                                                  */
/* ------------------------------------------------------------------ */

export interface ComponentRow {
  id: number;
  Component: string;
  MolWeight: number;
  Hf0: number;
  minColdTemp: number;
  maxColdTemp: number;
  minHotTemp: number;
  maxHotTemp: number;
  a1_cold: number;
  a2_cold: number;
  a3_cold: number;
  a4_cold: number;
  a5_cold: number;
  a1_hot: number;
  a2_hot: number;
  a3_hot: number;
  a4_hot: number;
  a5_hot: number;
  latex?: string;
  [key: string]: unknown;
}

export interface PropellantRow {
  id: number;
  Propelente: string;
  T_ad: number;
  MolWeight: number;
  Cp: number;
  Cv: number;
  R: number;
  gamma: number;
  cChar: number;
  Density: number;
  P1_min: number;
  P1_max: number;
  a: number;
  n: number;
  [key: string]: unknown;
}

export interface BurningRateResult {
  P: number[];
  r: number[];
  a: number;
  n: number;
  P1_min: number;
  P1_max: number;
}

/* ------------------------------------------------------------------ */
/* adiabatic (T0)                                                      */
/* ------------------------------------------------------------------ */

export interface AdiabaticSpecies {
  moles: number;
  component: string;
}

export interface AdiabaticCalculateParams {
  reac: AdiabaticSpecies[];
  prod: AdiabaticSpecies[];
  t0: number;
  tGuess: number;
  hStep: number;
}

export interface AdiabaticCalculateResult {
  tSol: number;
  molWeight: number;
  cp: number;
  cv: number;
  R: number;
  gamma: number;
  cChar: number;
}

export interface AdiabaticComponentInfo {
  MolWeight: number;
  Hf0: number;
  minColdTemp: number;
  maxColdTemp: number;
  minHotTemp: number;
  maxHotTemp: number;
}

/* ------------------------------------------------------------------ */
/* engine (T1)                                                         */
/* ------------------------------------------------------------------ */

export interface EngineInputs {
  Propellant?: string;
  GrainGeo?: string;
  CADx?: number[];
  CADy?: number[];
  CAD0?: number[];
  [key: string]: unknown;
}

export interface EngineTreeData {
  "Time (s)": number[];
  "Pressure (Pa)": number[];
  "Mass Flow (kg/s)": number[];
  "Mass (kg)": number[];
}

export interface EngineResults {
  meanPressure: number;
  maxPressure: number;
  minPressure: number;
  meanMassFlow: number;
  maxMassFlow: number;
  minMassFlow: number;
  totalTime: number;
  totalMass: number;
  tree_data: EngineTreeData;
}

export interface EnginePayload {
  inputs: EngineInputs;
  results: EngineResults;
}

export interface EngineArrays {
  time: number[];
  pressure: number[];
  massFlow: number[];
  mass: number[];
  phi_samples?: unknown[];
}

export interface EngineFigures {
  regression: string;
  pressure: string;
  massFlow: string;
  massBurn: string;
}

export interface EngineCalculateResult {
  payload: EnginePayload;
  arrays: EngineArrays;
  figures: EngineFigures;
}

export interface EngineGeometryResult {
  png_b64: string;
  cad: { center: [number, number]; x: number[]; y: number[] };
}

export interface EngineLoadResult {
  payload: EnginePayload;
  arrays: EngineArrays;
}

/* ------------------------------------------------------------------ */
/* nozzle (T2)                                                         */
/* ------------------------------------------------------------------ */

export interface NozzleGeometryData {
  "X (m)": number[];
  "Y (m)": number[];
  "AR (m)": number[];
  [key: string]: unknown;
}

export interface NozzleTimeResults {
  "Time (s)": number[];
  "Thrust (kg)": number[];
  CF: number[];
  [key: string]: unknown;
}

export interface NozzleFigures {
  geometry: string;
  mach: string;
  pres: string;
  thrust: string;
  cf: string;
}

export interface NozzleCalculateResult {
  calculatedResults: Record<string, Numeric>;
  geometry_data: NozzleGeometryData;
  timeResults_data: NozzleTimeResults;
  figures: NozzleFigures;
  payload: Record<string, unknown>;
}

export interface NozzleLoadEngineResult {
  inputs: Record<string, unknown>;
  n_samples: number;
  p1_min: number;
  p1_max: number;
  p_curve: { t: number[]; P: number[] };
  nozzleConfig: Record<string, unknown>;
}

export interface NozzleOpPointResult {
  F: number;
  Pe: number;
  /** `pe/p1` (ratio mostrado en la leyenda del mapa de presión). */
  PR: number;
  ratios: {
    PR0: number;
    PR1: number;
    PR2: number;
    PR3: number;
    p0_p1: number;
    pe_p1: number;
    pe_p0: number;
  };
  regime: string;
  nozzleType?: string;
  /** Curvas del punto off-design (para mach_plot / pres_plot nativos). */
  curves?: { x: number[]; mach: number[]; pr: number[] };
}

/* ------------------------------------------------------------------ */
/* cad (T3)                                                            */
/* ------------------------------------------------------------------ */

export interface CadField {
  key: string;
  label: string;
  type: string;
  default: Numeric;
}

export interface CadCheck {
  key: string;
  label: string;
  default: boolean;
}

export interface CadLoadResult {
  config: Record<string, unknown>;
  architecture: "conventional" | "as-nozzle";
  fields: CadField[];
  checks: CadCheck[];
}

export interface CadViews {
  engine: string;
  coverFront: string;
  nozzleFront: string;
  tools: string;
  toolMould: string;
  toolMouldFix: string;
}

export interface CadViewsResult {
  views: CadViews;
}

export interface CadExportResult {
  path: string;
  written: string[];
}

/* ------------------------------------------------------------------ */
/* testbed (T4)                                                        */
/* ------------------------------------------------------------------ */

export interface PortInfo {
  device: string;
  description: string;
}

export interface ChecklistItem {
  text: string;
  done: boolean;
}

export interface ChecklistResult {
  title: string;
  items: ChecklistItem[];
}

export type LedState = "green" | "blue" | "off";

export interface SerialLeds {
  serial: LedState;
  wifi: LedState;
}

export interface SerialState {
  connected: boolean;
  wifiReady: boolean;
  recording: boolean;
  checklistComplete: boolean;
  checklistEnabled?: boolean;
  leds: SerialLeds;
  testFile?: string | null;
  nozzle?: string | null;
  maxThrust?: number;
  maxTemp?: number;
  records?: number;
}

export interface TestbedRunResult {
  testFile: string;
  nozzle: string;
  engine: string;
  maxThrust: number;
  maxTemp: number;
}

export interface SerialRecord {
  t: number;
  F: number;
  T: number;
}

/* ------------------------------------------------------------------ */
/* plugins                                                             */
/* ------------------------------------------------------------------ */

export interface PluginEntry {
  labels: Record<string, string>;
}

export interface PluginsListResult {
  plugins: Record<string, PluginEntry>;
}

/* ------------------------------------------------------------------ */
/* eventos transversales (`engine-event`)                              */
/* ------------------------------------------------------------------ */

export interface EngineEventMap {
  ready: { name: "ready"; version: string; pid: number };
  console: { name: "console"; job: string; line: string };
  progress: { name: "progress"; job: string; value: number; label?: string };
  job_done: {
    name: "job_done";
    job: string;
    status: "ok" | "cancelled" | "error";
    error?: string;
  };
  log: { name: "log"; level: string; message: string };
  serial_line: { name: "serial_line"; line: string };
  record: { name: "record"; t: number; F: number; T: number; index?: number };
  state: { name: "state" } & SerialState;
  ports: { name: "ports"; ports: string[] };
  exiting: { name: "exiting" };
}

export type EngineEventName = keyof EngineEventMap;
export type EngineEvent<N extends EngineEventName = EngineEventName> = EngineEventMap[N];

/* ------------------------------------------------------------------ */
/* Alias con los nombres del enunciado del contrato                    */
/* ------------------------------------------------------------------ */

export type Component = ComponentRow;
export type Propellant = PropellantRow;
export type NozzleResults = NozzleCalculateResult;
export type Ports = PortInfo[];
export type Checklist = ChecklistResult;
