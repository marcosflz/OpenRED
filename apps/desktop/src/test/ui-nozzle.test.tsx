/**
 * Tests del módulo T2 (Nozzle Design, agente A6).
 *
 * - Carga de motor mockeada (`pick_file` + `nozzle.load_engine`) y P1 medio.
 * - Validación de P1 fuera de rango.
 * - El cambio de tipo de tobera reconstruye los inputs dinámicos (T2-3).
 * - `nozzle.op_point` (con debounce 100 ms) actualiza ratios y régimen (T2-7).
 * - Cancelación con `engine-request` + `request.cancel` sin resultados
 *   parciales (T2-5) y aviso claro sin motor (T2-10).
 * - Tablas (T2-8), export del cálculo (T2-9) y export desde el menú.
 */

import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { ToastProvider } from "../components";
import { WorkspaceProvider } from "../app/WorkspaceProvider";
import { NozzleTab } from "../ui/nozzle";
import type { NozzleCalculateResult, NozzleOpPointResult } from "../api/engine";

const hoisted = vi.hoisted(() => ({
  request: vi.fn(),
  invokeCommand: vi.fn(),
  listeners: [] as Array<{
    name: string;
    handler: (event: { payload: unknown }) => void;
  }>,
}));

// ECharts no inicializa en jsdom (canvas); en las pruebas basta el marcador.
vi.mock("../components/LineChart", () => ({
  baseChartOption: () => ({}),
  LineChart: ({ ariaLabel }: { ariaLabel?: string }) => (
    <div data-testid="line-chart" aria-label={ariaLabel} />
  ),
}));

// `listen` de Tauri simulado: permite emitir `engine-request`/`progress`.
vi.mock("@tauri-apps/api/event", () => ({
  listen: async (name: string, handler: (event: { payload: unknown }) => void) => {
    hoisted.listeners.push({ name, handler });
    return () => {};
  },
}));

vi.mock("../api/engine", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/engine")>();
  return {
    ...actual,
    // El módulo se prueba con la rama Tauri activa (cancelación con requestId).
    isTauri: () => true,
    request: hoisted.request,
    invokeCommand: hoisted.invokeCommand,
    // Enruta los diálogos por el spy compartido (los bindings internos del
    // módulo real no pasan por `invokeCommand` mockeado).
    pickFile: (filters?: unknown) =>
      hoisted.invokeCommand("pick_file", filters ? { filters } : {}),
    pickSaveFile: (defaultName?: string) =>
      hoisted.invokeCommand("pick_save_file", defaultName ? { defaultName } : {}),
  };
});

const WORKDIR = "C:\\Users\\dev\\Documents\\OpenRED";

const ENGINE_PATH = `${WORKDIR}\\Engines\\KNSU-32-RT65.json`;

const PLUGINS = {
  plugins: {
    "CONE-LN": {
      labels: {
        "K (Factor Garganta)": "CONE-LN_k",
        "theta_t (deg)": "CONE-LN_theta_t",
      },
    },
    "TOPN-BN": {
      labels: {
        "K (Factor Garganta)": "TOP-BN_k",
        "theta_t (deg)": "TOP-BN_theta_t",
        "theta_e (deg)": "TOP-BN_theta_e",
        "% (L. Cono)": "TOP-BN_cone_length_percent",
      },
    },
  },
};

const ENGINE = {
  inputs: { Propellant: "KNSU", P0: 100000, Rt: 0.0065, GrainGeo: "Tubular-Grain" },
  n_samples: 5,
  p1_min: 1.2e6,
  p1_max: 2.8e6,
  meanPressure: 2e6,
  p_curve: { t: [0, 0.5, 1, 1.5, 2], P: [1.2e6, 1.9e6, 2.4e6, 2.0e6, 1.4e6] },
  nozzleConfig: "Tubular-Grain",
};

const CALCULATED: NozzleCalculateResult = {
  calculatedResults: {
    "DP. Thrust (kg)": 132.4123,
    "Med. Thrust (kg)": 120.5,
    "CF (DP.)": 1.48,
    "CF (Med.)": 1.4,
    "Vs (DP.)": 1800.2,
    "Vs (Med.)": 1750.1,
    "Ts (DP.)": 1500.3,
    "Ts (Med.)": 1450.2,
    "Ps (DP.)": 98765.4,
    "Ps (Med.)": 99000.1,
    It: 1200.5,
    Isp: 158.2,
    AR: 6.4,
    MS: 2.71,
    "Longitud (m)": 0.25,
    "Rt (m)": 0.0065,
    "R2 (m)": 0.0164,
    PR_Crit0: 1.83,
    PR_Crit1: 2.2,
    PR_Crit2: 3.1,
    PR_Crit3: 3.9,
  },
  geometry_data: {
    "X (m)": [0, 0.001],
    "Y (m)": [0.0065, 0.0164],
    "AR (m)": [1, 6.4],
  },
  timeResults_data: { "Time (s)": [0, 0.1], "Thrust (kg)": [140, 120], CF: [1.5, 1.4] },
  figures: { geometry: "AAAA", mach: "BBBB", pres: "CCCC", thrust: "DDDD", cf: "EEEE" },
  payload: { Inputs: { NozzleConfig: "TOPN-BN" } },
};

const OP_POINT: NozzleOpPointResult = {
  F: 118.5,
  Pe: 101325,
  PR: 0.05,
  ratios: {
    PR0: 1.83,
    PR1: 2.2,
    PR2: 3.1,
    PR3: 3.9,
    p0_p1: 0.05,
    pe_p1: 0.0507,
    pe_p0: 1.0133,
  },
  regime: "Subsonic",
  nozzleType: "TOPN-BN",
  curves: { x: [0, 0.02, 0.04], mach: [0, 1.2, 2.7], pr: [1, 0.4, 0.2] },
};

function handleRequest(method: string, params: Record<string, unknown>): unknown {
  switch (method) {
    case "app.info":
      return {
        version: "test",
        dataDir: "C:\\data",
        resourceDir: "C:\\res",
        workdir: WORKDIR,
        workdirSelected: true,
      };
    case "workspace.get":
      return { workdir: WORKDIR, workdirSelected: true };
    case "plugins.list":
      return PLUGINS;
    case "nozzle.load_engine":
      expect(params.path).toBe(ENGINE_PATH);
      return ENGINE;
    case "nozzle.calculate":
      return CALCULATED;
    case "nozzle.op_point":
      return OP_POINT;
    case "nozzle.save":
      return { path: `${WORKDIR}\\Nozzles\\${String(params.name ?? "")}.json` };
    case "request.cancel":
      return { cancelled: true };
    default:
      throw new Error(`Método inesperado en el test: ${method}`);
  }
}

function renderNozzle() {
  return render(
    <ToastProvider>
      <WorkspaceProvider>
        <NozzleTab active />
      </WorkspaceProvider>
    </ToastProvider>,
  );
}

async function loadEngine() {
  fireEvent.click(screen.getByRole("button", { name: "Load engine" }));
  await waitFor(() => {
    expect(screen.getByTestId("nozzle-engine-label")).toHaveTextContent("KNSU-32-RT65.json");
  });
}

/** Rellena los inputs dinámicos del tipo CONE-LN por defecto (k, theta_t). */
async function fillSpecInputs() {
  fireEvent.change(await screen.findByLabelText("K (Factor Garganta)"), {
    target: { value: "0.25" },
  });
  fireEvent.change(await screen.findByLabelText("theta_t (deg)"), { target: { value: "15" } });
}

async function calculate() {
  fireEvent.click(screen.getByRole("button", { name: "CALCULATE" }));
  await waitFor(() => {
    expect(screen.getByText("DP. Thrust (kg)")).toBeInTheDocument();
  });
}

describe("NozzleTab (T2)", () => {
  beforeEach(() => {
    hoisted.request.mockReset();
    hoisted.invokeCommand.mockReset();
    hoisted.listeners.length = 0;
    hoisted.request.mockImplementation(
      async (method: string, params: Record<string, unknown> = {}) =>
        handleRequest(method, params),
    );
    hoisted.invokeCommand.mockImplementation(async (command: string) => {
      if (command === "pick_file") return ENGINE_PATH;
      throw new Error(`Comando inesperado en el test: ${command}`);
    });
  });

  it("carga el motor mockeado y aplica P1 medio (T2-1/T2-2)", async () => {
    renderNozzle();
    await loadEngine();

    // El diálogo se pidió con el filtro JSON y el payload del motor se guardó.
    expect(hoisted.invokeCommand).toHaveBeenCalledWith("pick_file", expect.anything());
    await waitFor(() => {
      expect(screen.getByLabelText("P1 - Design point (Pa)")).toHaveValue("2000000");
    });
    expect(screen.getByLabelText("P1 - Mean Value (Pa)")).toBeChecked();
    expect(screen.getByRole("combobox", { name: "Nozzle type" })).toHaveValue("CONE-LN");
  });

  it("valida P1 fuera de rango sin mover el slider (T2-2)", async () => {
    renderNozzle();
    await loadEngine();

    // Desactiva P1 medio para poder editar la entrada.
    fireEvent.click(screen.getByLabelText("P1 - Mean Value (Pa)"));
    const entry = screen.getByLabelText("P1 - Design point (Pa)");
    fireEvent.change(entry, { target: { value: "500" } });
    fireEvent.blur(entry);

    expect(
      await screen.findByText("The value must be between 1200000 and 2800000."),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("P1 slider")).toHaveValue("2000000");
  });

  it("cambia de tipo de tobera y reconstruye los inputs dinámicos (T2-3)", async () => {
    renderNozzle();
    await loadEngine();

    const specInputs = await screen.findByTestId("nozzle-spec-inputs");
    expect(within(specInputs).getByText("K (Factor Garganta)")).toBeInTheDocument();
    expect(within(specInputs).getByText("theta_t (deg)")).toBeInTheDocument();
    expect(within(specInputs).queryByText("theta_e (deg)")).not.toBeInTheDocument();

    fireEvent.change(screen.getByRole("combobox", { name: "Nozzle type" }), {
      target: { value: "TOPN-BN" },
    });

    await waitFor(() => {
      expect(within(specInputs).getByText("theta_e (deg)")).toBeInTheDocument();
    });
    expect(within(specInputs).getByText("% (L. Cono)")).toBeInTheDocument();
    expect(hoisted.request).toHaveBeenCalledWith("plugins.list", { library: "NozzleLibrary" });
  });

  it("nozzle.op_point (debounce) actualiza ratios y régimen (T2-7)", async () => {
    renderNozzle();
    await loadEngine();
    await fillSpecInputs();

    fireEvent.click(screen.getByRole("tab", { name: /PERFORMANCE AND OPERATION/ }));
    await waitFor(() => {
      expect(screen.getByTestId("nozzle-regime")).toHaveTextContent("Subsonic");
    });

    const opCalls = hoisted.request.mock.calls.filter(
      ([method]) => method === "nozzle.op_point",
    );
    expect(opCalls.length).toBeGreaterThan(0);
    expect(opCalls[opCalls.length - 1][1]).toMatchObject({ nozzleType: "CONE-LN" });

    // Ratios calculados (P0/P1t, Pe/P1t, Pe/P0) visibles en el panel.
    expect(screen.getByText("P0/P1t (Exp. Ratio)").parentElement).toHaveTextContent("0.0500");
    expect(screen.getByText("Pe/P0 (Exit/Amb.)").parentElement).toHaveTextContent("1.0133");

    // Cambiar el régimen devuelto por el motor actualiza la etiqueta.
    hoisted.request.mockImplementation(async (method: string, params: Record<string, unknown> = {}) => {
      if (method === "nozzle.op_point") {
        return { ...OP_POINT, regime: "Over-Expanded" };
      }
      return handleRequest(method, params);
    });
    fireEvent.change(screen.getByLabelText(/P1t -/), { target: { value: "0.5" } });
    await waitFor(() => {
      expect(screen.getByTestId("nozzle-regime")).toHaveTextContent("Over-Expanded");
    });
  });

  it("CALCULATE sin motor avisa sin romper (T2-10)", async () => {
    renderNozzle();
    fireEvent.click(screen.getByRole("button", { name: "CALCULATE" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Carga un motor (LOAD) antes de calcular.",
    );
    expect(screen.getByTestId("nozzle-engine-label")).toHaveTextContent(
      "No file has been loaded",
    );
  });

  it("marca Invalid File cuando el motor es ilegible (T2-1)", async () => {
    renderNozzle();
    hoisted.request.mockImplementation(async (method: string, params: Record<string, unknown> = {}) => {
      if (method === "nozzle.load_engine") {
        const { RpcError } = await import("../api/errors");
        throw new RpcError(1003, "Invalid file.", null);
      }
      return handleRequest(method, params);
    });

    fireEvent.click(screen.getByRole("button", { name: "Load engine" }));
    await waitFor(() => {
      expect(screen.getByTestId("nozzle-engine-label")).toHaveTextContent("Invalid File");
    });
    expect(await screen.findByText("Invalid file.")).toBeInTheDocument();
  });

  it("cancela el cálculo sin dejar resultados parciales (T2-5)", async () => {
    renderNozzle();
    await loadEngine();
    await fillSpecInputs();

    hoisted.request.mockImplementation(async (method: string, params: Record<string, unknown> = {}) => {
      if (method === "nozzle.calculate") return new Promise(() => {});
      return handleRequest(method, params);
    });

    fireEvent.click(screen.getByRole("button", { name: "CALCULATE" }));
    const dialog = await screen.findByRole("dialog");

    // El sidecar emite `engine-request {id, method, phase}` al despachar.
    const requestHandlers = hoisted.listeners
      .filter((entry) => entry.name === "engine-request")
      .map((entry) => entry.handler);
    expect(requestHandlers.length).toBeGreaterThan(0);
    await act(async () => {
      for (const handler of requestHandlers) {
        handler({ payload: { id: 42, method: "nozzle.calculate", phase: "start" } });
      }
    });

    fireEvent.click(within(dialog).getByRole("button", { name: "Cancel" }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
    await waitFor(() => {
      expect(hoisted.request).toHaveBeenCalledWith("request.cancel", { id: 42 });
    });
    expect(screen.queryByText("DP. Thrust (kg)")).not.toBeInTheDocument();
  });

  it("muestra tablas y exporta el payload del cálculo (T2-8/T2-9)", async () => {
    renderNozzle();
    await loadEngine();
    await fillSpecInputs();
    await calculate();

    // Tabla TIME RESULTS (Time, Thrust, CF).
    expect(within(screen.getByRole("table")).getByText("Time (s)")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: /GEOMETRY/ }));
    await waitFor(() => {
      expect(within(screen.getByRole("table")).getByText("AR")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "EXPORT" }));
    const dialog = await screen.findByRole("dialog");
    const nameField = within(dialog).getByLabelText("Nombre del fichero");
    fireEvent.change(nameField, { target: { value: "BN-test" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "Guardar" }));

    await waitFor(() => {
      expect(hoisted.request).toHaveBeenCalledWith("nozzle.save", {
        name: "BN-test",
        payload: CALCULATED.payload,
      });
    });

    // Export desde el menú (`openred:export`, src/app/bus.ts).
    fireEvent.click(within(dialog).getByRole("button", { name: "Cancelar" }));
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
    window.dispatchEvent(new CustomEvent("openred:export"));
    expect(await screen.findByRole("dialog")).toBeInTheDocument();
  });
});
