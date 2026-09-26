/**
 * Backend simulado para desarrollo en navegador (`npm run dev` sin Tauri) y
 * para los tests de vitest. Se activa automáticamente cuando
 * `window.__TAURI_INTERNALS__` no existe (ver `src/api/engine.ts`).
 *
 * Los datos son de ejemplo y no pretenden ser numéricamente válidos.
 */

import { RpcError } from "./errors";
import type {
  AdiabaticCalculateResult,
  AppInfo,
  BurningRateResult,
  CadLoadResult,
  CadViewsResult,
  ChecklistResult,
  ComponentRow,
  EngineCalculateResult,
  EngineGeometryResult,
  EngineLoadResult,
  EngineStatus,
  NozzleCalculateResult,
  NozzleLoadEngineResult,
  NozzleOpPointResult,
  PluginsListResult,
  PortInfo,
  PropellantRow,
  SerialState,
  Tab0Config,
  Tab1Config,
  Tab2Config,
  Tab3Config,
  TestbedRunResult,
  WorkspaceConfig,
  WorkspaceFile,
  WorkspaceSetDirResult,
} from "./types";

/* ------------------------------------------------------------------ */
/* Introspección para tests                                            */
/* ------------------------------------------------------------------ */

export interface MockCall {
  target: "request" | "command";
  name: string;
  params: Record<string, unknown>;
}

const calls: MockCall[] = [];

/** Llamadas registradas por el backend mock (útil en tests). */
export function mockCalls(): readonly MockCall[] {
  return calls;
}

export function resetMockCalls(): void {
  calls.length = 0;
}

/* ------------------------------------------------------------------ */
/* Datos de ejemplo                                                    */
/* ------------------------------------------------------------------ */

const MOCK_WORKDIR = "C:\\Users\\dev\\Documents\\OpenRED";

/** PNG 1x1 transparente para figuras de ejemplo. */
const PNG_1PX =
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==";

export const MOCK_APP_INFO: AppInfo = {
  version: "0.1.0-dev",
  dataDir: "C:\\Users\\dev\\AppData\\Roaming\\OpenRED",
  resourceDir: "C:\\Program Files\\OpenRED\\engine",
  workdir: MOCK_WORKDIR,
  workdirSelected: true,
};

export const MOCK_ENGINE_STATUS: EngineStatus = {
  running: true,
  pid: 4242,
  version: MOCK_APP_INFO.version,
};

const TAB_0: Tab0Config = {
  reactivos: [
    [0.5, "KNO3 (S)"],
    [0.35, "C12H22O11 (Solid/Liquid)"],
  ],
  productos: [
    [0.03, "CO2"],
    [0.05, "CO"],
    [0.08, "H2O"],
    [0.02, "H2"],
    [0.04, "N2"],
    [0.05, "K2CO3 (S/L)"],
    [0.02, "KOH (L/G/S)"],
  ],
  initial_temp: "298",
  temp_Int_step: "0.001",
  temp_guess: "1500",
};

const TAB_1: Tab1Config = {
  propellant: "KNSU",
  geoConfig: "Tubular-Grain",
  P0: "101325",
  Rt: "0.008",
  Rc: "0.02",
  Lc: "0.12",
  dt: "0.001",
  dh: "0.0005",
  ItMax: "1500",
};

const TAB_2: Tab2Config = {
  engine_config: "Engines/KNSU-32-RT65.json",
  SwitchState: "false",
  P1: "2000000",
  n_res: "10",
  nozzle_type: "CONE-LN",
};

const TAB_3: Tab3Config = {
  NozzleConfig: "CONE-LN",
  type: "Fitted",
  n_conv: "1",
};

export const MOCK_WORKSPACE_CONFIG: WorkspaceConfig = {
  tabs: { tab_0: TAB_0, tab_1: TAB_1, tab_2: TAB_2, tab_3: TAB_3 },
};

export const MOCK_FILES: WorkspaceFile[] = [
  { name: "KNSU-32-RT65.json", size: 59123, mtime: 1725000000 },
  { name: "KNSU-32mm.json", size: 41044, mtime: 1724000000 },
  { name: "TKNO-3.json", size: 38210, mtime: 1723000000 },
];

export const MOCK_PORTS: PortInfo[] = [
  { device: "COM3", description: "USB Serial Device (COM3)" },
  { device: "COM4", description: "Silicon Labs CP210x (COM4)" },
];

const component = (
  id: number,
  name: string,
  molWeight: number,
  hf0: number,
  latex: string,
): ComponentRow => ({
  id,
  Component: name,
  MolWeight: molWeight,
  Hf0: hf0,
  minColdTemp: 298,
  maxColdTemp: 1000,
  minHotTemp: 1000,
  maxHotTemp: 6000,
  a1_cold: 1.2,
  a2_cold: -3.4e-3,
  a3_cold: 5.6e-6,
  a4_cold: -2.1e-9,
  a5_cold: 3.3e-13,
  a1_hot: 2.1,
  a2_hot: 2.4e-3,
  a3_hot: -6.1e-7,
  a4_hot: 8.2e-11,
  a5_hot: -3.4e-15,
  latex,
});

export const MOCK_COMPONENTS: ComponentRow[] = [
  component(1, "KNO3 (S)", 101.103, -494.6, "\\mathrm{KNO_3}"),
  component(2, "C12H22O11 (Solid/Liquid)", 342.297, -2226.1, "\\mathrm{C_{12}H_{22}O_{11}}"),
  component(3, "CO2", 44.01, -393.5, "\\mathrm{CO_2}"),
  component(4, "H2O", 18.015, -241.8, "\\mathrm{H_2O}"),
  component(5, "K2CO3 (S/L)", 138.205, -1151.0, "\\mathrm{K_2CO_3}"),
];

const propellant = (
  id: number,
  name: string,
  tAd: number,
  gamma: number,
  cChar: number,
  density: number,
  pMin: number,
  pMax: number,
  a: number,
  n: number,
): PropellantRow => ({
  id,
  Propelente: name,
  T_ad: tAd,
  MolWeight: 41.2,
  Cp: 1.85,
  Cv: 1.45,
  R: 287,
  gamma,
  cChar,
  Density: density,
  P1_min: pMin,
  P1_max: pMax,
  a,
  n,
});

export const MOCK_PROPELLANTS: PropellantRow[] = [
  propellant(1, "KNSU", 1720.5, 1.133, 1450.2, 1.84, 1e5, 7e6, 8.26e-5, 0.319),
  propellant(2, "KNSU2", 1705.9, 1.128, 1441.7, 1.83, 1e5, 7e6, 9.0e-5, 0.3),
  propellant(3, "KNSL", 1640.2, 1.12, 1402.4, 1.79, 1e5, 6e6, 7.4e-5, 0.35),
];

function mean(values: number[]): number {
  if (values.length === 0) return 0;
  let sum = 0;
  for (const value of values) sum += value;
  return sum / values.length;
}

function synthEngine(): EngineCalculateResult {
  const count = 80;
  const time = Array.from({ length: count }, (_, i) => (i + 1) * 0.05);
  const pressure = time.map((t, i) => 1.9e6 * Math.exp(-0.02 * t) + 4e4 * Math.sin(i / 4));
  const massFlow = pressure.map((p) => 0.45 * (p / 1.9e6));
  const mass: number[] = [];
  massFlow.forEach((flow, i) => mass.push((mass[i - 1] ?? 0) + flow * 0.05));
  const totalMass = mass[mass.length - 1] ?? 0;
  const figures = {
    regression: PNG_1PX,
    pressure: PNG_1PX,
    massFlow: PNG_1PX,
    massBurn: PNG_1PX,
  };
  return {
    payload: {
      inputs: {
        Propellant: "KNSU",
        GrainGeo: "Tubular-Grain",
        CADx: [0, 0.016, 0.016, 0],
        CADy: [0, 0, 0.032, 0.032],
        CAD0: [0, 1, 2, 3],
        P0: 101325,
        Rt: 0.008,
        It: 1500,
      },
      results: {
        meanPressure: mean(pressure),
        maxPressure: Math.max(...pressure),
        minPressure: Math.min(...pressure),
        meanMassFlow: mean(massFlow),
        maxMassFlow: Math.max(...massFlow),
        minMassFlow: Math.min(...massFlow),
        totalTime: time[time.length - 1] ?? 0,
        totalMass,
        tree_data: {
          "Time (s)": time,
          "Pressure (Pa)": pressure,
          "Mass Flow (kg/s)": massFlow,
          "Mass (kg)": mass,
        },
      },
    },
    arrays: { time, pressure, massFlow, mass, phi_samples: [] },
    figures,
  };
}

export const MOCK_ENGINE_RESULT: EngineCalculateResult = synthEngine();

function synthNozzle(): NozzleCalculateResult {
  const count = 40;
  const x = Array.from({ length: count }, (_, i) => i * 0.005);
  const y = x.map((v) => 0.004 + 0.02 * Math.sqrt(v));
  const ar = x.map((v) => 1 + v * 40);
  const time = Array.from({ length: 12 }, (_, i) => i * 0.1);
  const thrust = time.map((t) => 130 * Math.exp(-0.05 * t));
  const cf = time.map((_, i) => 1.5 - i * 0.01);
  return {
    calculatedResults: {
      "F (kg)": 132.4,
      "Pe (Pa)": 98765,
      "PR": 12.3,
      "CF": 1.48,
      "Isp (s)": 158.2,
      "Thrust (kg)": 132.4,
      Mexit: 2.71,
      "Ae/At": 6.4,
      "PR_Crit0": 3.2,
      "PR_Crit1": 5.1,
      "PR_Crit2": 7.4,
      "PR_Crit3": 9.9,
    },
    geometry_data: { "X (m)": x, "Y (m)": y, "AR (m)": ar },
    timeResults_data: { "Time (s)": time, "Thrust (kg)": thrust, CF: cf },
    figures: {
      geometry: PNG_1PX,
      mach: PNG_1PX,
      pres: PNG_1PX,
      thrust: PNG_1PX,
      cf: PNG_1PX,
    },
    payload: { Inputs: { NozzleConfig: "CONE-LN", P1: 2e6, n: 10 } },
  };
}

function synthViews(): CadViewsResult {
  return {
    views: {
      engine: PNG_1PX,
      coverFront: PNG_1PX,
      nozzleFront: PNG_1PX,
      tools: PNG_1PX,
      toolMould: PNG_1PX,
      toolMouldFix: PNG_1PX,
    },
  };
}

const MOCK_CHECKLIST: ChecklistResult = {
  title: "Test checklist",
  items: [
    { text: "Retirar seguros", done: false },
    { text: "Comprobar célula de carga", done: false },
    { text: "Activar grabación", done: false },
  ],
};

const MOCK_SERIAL_STATE: SerialState = {
  connected: false,
  wifiReady: false,
  recording: false,
  checklistComplete: false,
  leds: { serial: "off", wifi: "off" },
};

/* ------------------------------------------------------------------ */
/* Dispatcher de métodos JSON-RPC                                      */
/* ------------------------------------------------------------------ */

export async function mockRequest<T>(
  method: string,
  params: Record<string, unknown> = {},
): Promise<T> {
  calls.push({ target: "request", name: method, params });
  await Promise.resolve();

  switch (method) {
    case "app.ping":
    case "app.info":
      return MOCK_APP_INFO as T;
    case "app.shutdown":
      return { ok: true } as T;
    case "request.cancel":
      return { cancelled: true } as T;

    case "workspace.get":
      return { workdir: MOCK_WORKDIR, workdirSelected: true } as T;
    case "workspace.set_dir": {
      const result: WorkspaceSetDirResult = {
        workdir: (params.path as string) || MOCK_WORKDIR,
        created: ["Engines", "Nozzles", "Sketches", "Tests"],
        hasConfig: true,
        config: MOCK_WORKSPACE_CONFIG,
      };
      return result as T;
    }
    case "workspace.load_config":
      return { config: MOCK_WORKSPACE_CONFIG, hasConfig: true } as T;
    case "workspace.save_config":
      return { path: `${MOCK_WORKDIR}\\config.json` } as T;
    case "workspace.list":
      return { files: MOCK_FILES } as T;
    case "workspace.ensure_workdir":
      return { workdir: MOCK_WORKDIR } as T;

    case "db.components.list":
      return { items: MOCK_COMPONENTS } as T;
    case "db.components.add":
    case "db.components.edit":
    case "db.components.delete":
      return { items: MOCK_COMPONENTS } as T;
    case "db.propellants.list":
      return { items: MOCK_PROPELLANTS } as T;
    case "db.propellants.add":
    case "db.propellants.edit":
    case "db.propellants.delete":
    case "adiabatic.save_propellant":
      return { items: MOCK_PROPELLANTS } as T;
    case "db.propellants.burning_rate": {
      const points = Math.min(Number(params.n_points ?? 100), 200);
      const p1Min = 1e5;
      const p1Max = 7e6;
      const a = 8.26e-5;
      const n = 0.319;
      const P = Array.from({ length: points }, (_, i) => p1Min + ((p1Max - p1Min) * i) / (points - 1));
      const result: BurningRateResult = {
        P,
        r: P.map((p) => a * Math.pow(p, n)),
        a,
        n,
        P1_min: p1Min,
        P1_max: p1Max,
      };
      return result as T;
    }
    case "db.clean_name": {
      const name = String(params.name ?? "");
      return { clean: name.replace(/\s*\(\d+\)\s*$/, "") } as T;
    }

    case "adiabatic.calculate": {
      const result: AdiabaticCalculateResult = {
        tSol: 1720.5,
        molWeight: 41.2,
        cp: 1.85,
        cv: 1.45,
        R: 287,
        gamma: 1.277,
        cChar: 1450.2,
      };
      return result as T;
    }
    case "adiabatic.component_info": {
      const requested = String(params.component ?? "");
      const found = MOCK_COMPONENTS.find(
        (row) => row.Component === requested || row.Component.startsWith(requested),
      );
      if (!found) {
        throw new RpcError(-32602, `No data found for component: ${requested}`, null);
      }
      return {
        MolWeight: found.MolWeight,
        Hf0: found.Hf0,
        minColdTemp: found.minColdTemp,
        maxColdTemp: found.maxColdTemp,
        minHotTemp: found.minHotTemp,
        maxHotTemp: found.maxHotTemp,
      } as T;
    }

    case "engine.geometry": {
      const result: EngineGeometryResult = {
        png_b64: PNG_1PX,
        cad: { center: [0, 0], x: [0, 0.016, 0.016, 0], y: [0, 0, 0.032, 0.032] },
      };
      return result as T;
    }
    case "engine.calculate":
      return MOCK_ENGINE_RESULT as T;
    case "engine.save":
      return { path: `${MOCK_WORKDIR}\\Engines\\${String(params.name ?? "untitled")}.json` } as T;
    case "engine.load": {
      const result: EngineLoadResult = {
        payload: MOCK_ENGINE_RESULT.payload,
        arrays: MOCK_ENGINE_RESULT.arrays,
      };
      return result as T;
    }
    case "engine.list":
      return { files: MOCK_FILES } as T;

    case "nozzle.load_engine": {
      const result: NozzleLoadEngineResult = {
        inputs: MOCK_ENGINE_RESULT.payload.inputs,
        n_samples: 10,
        p1_min: 1.2e6,
        p1_max: 2.8e6,
        p_curve: {
          t: [0, 0.5, 1, 1.5, 2],
          P: [1.2e6, 1.9e6, 2.4e6, 2.0e6, 1.4e6],
        },
        nozzleConfig: { NozzleConfig: "CONE-LN" },
      };
      return result as T;
    }
    case "nozzle.calculate":
      return synthNozzle() as T;
    case "nozzle.op_point": {
      const result: NozzleOpPointResult = {
        F: 132.4,
        Pe: 98765,
        PR: 0.97,
        ratios: { PR0: 1.2, PR1: 1.05, PR2: 0.97, PR3: 0.42, p0_p1: 1.2, pe_p1: 1.05, pe_p0: 0.97 },
        regime: "Under-Expanded",
        nozzleType: "TOPN-BN",
        curves: { x: [0, 0.02, 0.04], mach: [0.2, 1.8, 3.1], pr: [1, 0.5, 0.08] },
      };
      return result as T;
    }
    case "nozzle.save":
      return { path: `${MOCK_WORKDIR}\\Nozzles\\${String(params.name ?? "untitled")}.json` } as T;
    case "nozzle.load":
      return { payload: synthNozzle().payload } as T;

    case "cad.load_nozzle": {
      const result: CadLoadResult = {
        config: { NozzleConfig: "CONE-LN" },
        architecture: "conventional",
        fields: [
          { key: "n_conv", label: "Nº de conos", type: "number", default: 1 },
          { key: "throat", label: "Diámetro garganta (mm)", type: "number", default: 16 },
        ],
        checks: [
          { key: "on_engine", label: "Engine", default: true },
          { key: "on_cover", label: "Cover", default: true },
        ],
      };
      return result as T;
    }
    case "cad.views":
      return synthViews() as T;
    case "cad.export":
      return {
        path: `${MOCK_WORKDIR}\\Sketches\\engine.csv`,
        written: ["engine.csv"],
      } as T;

    case "testbed.list_ports":
      return { ports: MOCK_PORTS } as T;
    case "testbed.monitor_ports":
      return { ok: true } as T;
    case "testbed.connect_com":
      return { connected: true } as T;
    case "testbed.disconnect":
      return { connected: false } as T;
    case "testbed.connect_wifi":
      return { sent: true } as T;
    case "testbed.abort":
      return { ok: true } as T;
    case "testbed.run": {
      const result: TestbedRunResult = {
        testFile: `${MOCK_WORKDIR}\\Tests\\KNSU-32-RT65-19.28.35-15.09.24.csv`,
        nozzle: "BN1",
        engine: "KNSU-32-RT65",
        maxThrust: 150,
        maxTemp: 1200,
      };
      return result as T;
    }
    case "testbed.checklist.load":
      return MOCK_CHECKLIST as T;
    case "testbed.checklist.toggle":
      return { items: MOCK_CHECKLIST.items, complete: false } as T;
    case "testbed.state":
      return MOCK_SERIAL_STATE as T;
    case "testbed.mock":
      return { ok: true } as T;

    case "plugins.list": {
      const result: PluginsListResult = {
        plugins: {
          "Tubular-Grain": {
            labels: { "X  (m)": "cx_real", "Y  (m)": "cy_real", "R1 (m)": "r_in" },
          },
        },
      };
      return result as T;
    }
    case "plugins.reload":
      return { grain: ["Tubular-Grain"], nozzle: ["CONE-LN", "TOPN-BN"] } as T;

    default:
      throw new RpcError(-32601, `Unknown method: ${method}`, null);
  }
}

/* ------------------------------------------------------------------ */
/* Dispatcher de comandos Tauri                                        */
/* ------------------------------------------------------------------ */

export async function mockInvoke<T>(
  command: string,
  args: Record<string, unknown> = {},
): Promise<T> {
  calls.push({ target: "command", name: command, params: args });
  await Promise.resolve();

  switch (command) {
    case "pick_workdir":
      return MOCK_WORKDIR as T;
    case "pick_file":
      return `${MOCK_WORKDIR}\\Engines\\KNSU-32-RT65.json` as T;
    case "pick_save_file": {
      const name = typeof args.defaultName === "string" ? args.defaultName : "export.json";
      return `${MOCK_WORKDIR}\\Exports\\${name}` as T;
    }
    case "save_workdir":
    case "open_logs_folder":
      return undefined as unknown as T;
    case "app_info":
      return MOCK_APP_INFO as T;
    case "engine_status":
    case "engine_restart":
      return MOCK_ENGINE_STATUS as T;
    default:
      throw new RpcError(-32601, `Unknown command: ${command}`, null);
  }
}
