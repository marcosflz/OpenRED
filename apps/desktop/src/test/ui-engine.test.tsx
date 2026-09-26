import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { useEffect } from "react";
import type {
  EngineCalculateResult,
  EngineEventMap,
  EngineGeometryResult,
  PluginsListResult,
  PropellantRow,
} from "../api/types";
import { WorkspaceProvider, useWorkspace } from "../app/WorkspaceProvider";
import { requestExport } from "../app/bus";
import { ToastProvider } from "../components/Toast";
import { EngineTab } from "../ui/engine";
import type { EngineGeometryParams, EngineCalculateParams } from "../ui/engine/api";

/* El módulo RPC se mockea para controlar el motor sin tocar `src/api/**`. */
const engineApiMock = vi.hoisted(() => ({
  listPropellants: vi.fn(),
  listGrainPlugins: vi.fn(),
  fetchGeometry: vi.fn(),
  calculateEngine: vi.fn(),
  saveEngine: vi.fn(),
  onConsole: vi.fn(),
  onProgress: vi.fn(),
  onEngineRequest: vi.fn(),
}));

vi.mock("../ui/engine/api", () => engineApiMock);

const PROPELLANTS: PropellantRow[] = [
  {
    id: 1,
    Propelente: "KNSU",
    T_ad: 1720.5,
    MolWeight: 41.2,
    Cp: 1.85,
    Cv: 1.45,
    R: 287,
    gamma: 1.133,
    cChar: 1450.2,
    Density: 1.84,
    P1_min: 1e5,
    P1_max: 7e6,
    a: 8.26e-5,
    n: 0.319,
  },
  {
    id: 2,
    Propelente: "KNSL",
    T_ad: 1640.2,
    MolWeight: 40.1,
    Cp: 1.8,
    Cv: 1.4,
    R: 280,
    gamma: 1.12,
    cChar: 1402.4,
    Density: 1.79,
    P1_min: 1e5,
    P1_max: 6e6,
    a: 7.4e-5,
    n: 0.35,
  },
];

const GRAINS: PluginsListResult["plugins"] = {
  "Tubular-Grain": {
    labels: { "X  (m)": "cx_real", "Y  (m)": "cy_real", "R1 (m)": "r_in" },
  },
  "Star-Grain": {
    labels: { "R (m)": "r_star" },
  },
};

const GEOMETRY: EngineGeometryResult = {
  png_b64: "R0lGODlhAQABAAAAACw=",
  cad: { center: [0, 0], x: [0, 0.016, 0.016, 0], y: [0, 0, 0.032, 0.032] },
};

const CALC_RESULT: EngineCalculateResult = {
  payload: {
    inputs: { Propellant: "KNSU", GrainGeo: "Tubular-Grain" },
    results: {
      meanPressure: 790190.522109697,
      maxPressure: 1618087.27745501,
      minPressure: 100000,
      meanMassFlow: 0.105963226671605,
      maxMassFlow: 0.21698279612066,
      minMassFlow: 0.0134098326551296,
      totalTime: 1.875,
      totalMass: 0.148383704214353,
      tree_data: {
        "Time (s)": [0.005, 0.01],
        "Pressure (Pa)": [100000, 175698.055235937],
        "Mass Flow (kg/s)": [0.0134, 0.0165],
        "Mass (kg)": [0.1483, 0.1482],
      },
    },
  },
  arrays: {
    time: [0.005, 0.01],
    pressure: [100000, 175698.055235937],
    massFlow: [0.0134, 0.0165],
    mass: [0.1483, 0.1482],
    phi_samples: [],
  },
  figures: { regression: "REG", pressure: "PRES", massFlow: "MF", massBurn: "MB" },
};

/** Expone `config.tabs.tab_1` para comprobar la persistencia (T1-9). */
function ConfigProbe() {
  const { config } = useWorkspace();
  return <pre data-testid="engine-config">{JSON.stringify(config.tabs?.tab_1 ?? null)}</pre>;
}

/** Carga `workspace.load_config` (config.json del directorio de trabajo mock). */
function ConfigLoader() {
  const { loadConfig } = useWorkspace();
  useEffect(() => {
    void loadConfig();
  }, [loadConfig]);
  return null;
}

function renderEngine(options?: { loadConfig?: boolean }) {
  return render(
    <ToastProvider>
      <WorkspaceProvider>
        {options?.loadConfig ? <ConfigLoader /> : null}
        <EngineTab active />
        <ConfigProbe />
      </WorkspaceProvider>
    </ToastProvider>,
  );
}

beforeEach(() => {
  engineApiMock.listPropellants.mockResolvedValue(PROPELLANTS);
  engineApiMock.listGrainPlugins.mockResolvedValue(GRAINS);
  engineApiMock.fetchGeometry.mockResolvedValue(GEOMETRY);
  engineApiMock.calculateEngine.mockResolvedValue(CALC_RESULT);
  engineApiMock.saveEngine.mockResolvedValue("C:\\Users\\dev\\Documents\\OpenRED\\Engines\\test.json");
  engineApiMock.onConsole.mockResolvedValue(() => {});
  engineApiMock.onProgress.mockResolvedValue(() => {});
  engineApiMock.onEngineRequest.mockResolvedValue(() => {});
});

describe("EngineTab", () => {
  it("renderiza los selectores con los propelentes (Nombre (id)) y las geometrías del plugin", async () => {
    renderEngine();

    const propellantSelect = await screen.findByLabelText("Propellant");
    await waitFor(() =>
      expect(within(propellantSelect).getByRole("option", { name: "KNSU (1)" })).toBeInTheDocument(),
    );
    await waitFor(() =>
      expect(within(propellantSelect).getByRole("option", { name: "KNSL (2)" })).toBeInTheDocument(),
    );

    const grainSelect = screen.getByLabelText("Grain Geometry");
    await waitFor(() =>
      expect(within(grainSelect).getByRole("option", { name: "Tubular-Grain" })).toBeInTheDocument(),
    );
    expect(within(grainSelect).getByRole("option", { name: "Star-Grain" })).toBeInTheDocument();

    // 7 entradas comunes con los valores por defecto del legacy.
    expect(screen.getByTestId("common-P0")).toHaveValue("1e5");
    expect(screen.getByTestId("common-Rt")).toHaveValue("0.0065");
    expect(screen.getByTestId("common-Rc")).toHaveValue("0.016");
    expect(screen.getByTestId("common-Lc")).toHaveValue("0.1");
    expect(screen.getByTestId("common-dt")).toHaveValue("0.005");
    expect(screen.getByTestId("common-dh")).toHaveValue("0.0001");
    expect(screen.getByTestId("common-ItMax")).toHaveValue("10000");

    // Inputs dinámicos del grano por defecto (`label -> clave`).
    expect(await screen.findByTestId("grain-field-Tubular-Grain-cx_real")).toBeInTheDocument();
    expect(screen.getByTestId("grain-field-Tubular-Grain-r_in")).toBeInTheDocument();
  });

  it("al cambiar de geometría reconstruye los inputs y persiste <grain>_<clave> de todas", async () => {
    renderEngine();
    await screen.findByTestId("grain-field-Tubular-Grain-cx_real");

    fireEvent.change(screen.getByLabelText("Grain Geometry"), {
      target: { value: "Star-Grain" },
    });

    await screen.findByTestId("grain-field-Star-Grain-r_star");
    expect(screen.queryByTestId("grain-field-Tubular-Grain-cx_real")).toBeNull();

    await waitFor(() => expect(engineApiMock.fetchGeometry).toHaveBeenCalledTimes(1));
    const params = engineApiMock.fetchGeometry.mock.calls[0][0] as EngineGeometryParams;
    expect(params.propellant).toBe("KNSU");
    expect(params.grain).toBe("Star-Grain");
    expect(params.spec).toMatchObject({
      P0: 100000,
      Rt: 0.0065,
      R2: 0.016,
      Lc: 0.1,
      dt: 0.005,
      dh: 0.0001,
      It: 10000,
      r_star: 0,
    });

    const saved = JSON.parse(screen.getByTestId("engine-config").textContent ?? "{}") as Record<
      string,
      unknown
    >;
    expect(saved.geoConfig).toBe("Star-Grain");
    // Todas las geometrías (no solo la activa) quedan en config con cadenas.
    expect(saved["Tubular-Grain_cx_real"]).toBe("0");
    expect(saved["Tubular-Grain_r_in"]).toBe("0");
    expect(saved["Star-Grain_r_star"]).toBe("0");
  });

  it("engine.calculate pinta métricas, tabla y figuras", async () => {
    renderEngine();
    await screen.findByTestId("grain-field-Tubular-Grain-cx_real");
    await waitFor(() => expect(screen.getByLabelText("Propellant")).toHaveValue("KNSU (1)"));

    fireEvent.click(screen.getByRole("tab", { name: "CONSOLE" }));
    fireEvent.click(screen.getByRole("button", { name: "CALCULATE" }));

    await waitFor(() => expect(engineApiMock.calculateEngine).toHaveBeenCalledTimes(1));
    const params = engineApiMock.calculateEngine.mock.calls[0][0] as EngineCalculateParams;
    expect(params.propellant).toBe("KNSU");
    expect(params.grain).toBe("Tubular-Grain");
    expect(params.spec).toMatchObject({
      P0: 100000,
      R2: 0.016,
      It: 10000,
      cx_real: 0,
      cy_real: 0,
      r_in: 0,
    });
    expect(params.propellantData).toEqual({
      a: 8.26e-5,
      n: 0.319,
      R: 287,
      T1: 1720.5,
      cChar: 1450.2,
      rho_b: 1.84,
      P1_min: 1e5,
      P1_max: 7e6,
    });

    // Como el legacy, al terminar se muestra la figura de regresión.
    await waitFor(() =>
      expect(screen.getByRole("tab", { name: "REGRESSION" })).toHaveAttribute(
        "aria-selected",
        "true",
      ),
    );
    expect(screen.getByAltText("Regression")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "DATA" }));
    expect(await screen.findByTestId("metric-meanPressure")).toHaveValue("790190.522109697");
    expect(screen.getByTestId("metric-totalTime")).toHaveValue("1.875");
    expect(screen.getByTestId("metric-totalMass")).toHaveValue("0.148383704214353");
    // Tiempo formateado con los decimales de dt ("0.005" -> 3).
    expect(screen.getByText("0.005")).toBeInTheDocument();
    expect(screen.getByText("175698.055235937")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "GRAPHS" }));
    expect(screen.getByAltText("Chamber pressure")).toBeInTheDocument();
    expect(screen.getByAltText("Mass flow")).toBeInTheDocument();
    expect(screen.getByAltText("Propellant mass")).toBeInTheDocument();
  });

  it("restaura los valores y la selección de config.json al montar (T1-9)", async () => {
    renderEngine({ loadConfig: true });

    await waitFor(() => expect(screen.getByTestId("common-P0")).toHaveValue("101325"));
    expect(screen.getByTestId("common-Rt")).toHaveValue("0.008");
    expect(screen.getByTestId("common-Rc")).toHaveValue("0.02");
    expect(screen.getByTestId("common-Lc")).toHaveValue("0.12");
    expect(screen.getByTestId("common-dt")).toHaveValue("0.001");
    expect(screen.getByTestId("common-dh")).toHaveValue("0.0005");
    expect(screen.getByTestId("common-ItMax")).toHaveValue("1500");

    await waitFor(() => expect(screen.getByLabelText("Propellant")).toHaveValue("KNSU (1)"));
    await waitFor(() =>
      expect(screen.getByLabelText("Grain Geometry")).toHaveValue("Tubular-Grain"),
    );
  });

  it("lanza la exportación desde el menú (openred:export) y guarda el payload", async () => {
    renderEngine();
    await screen.findByTestId("grain-field-Tubular-Grain-cx_real");
    await waitFor(() => expect(screen.getByLabelText("Propellant")).toHaveValue("KNSU (1)"));

    fireEvent.click(screen.getByRole("tab", { name: "CONSOLE" }));
    fireEvent.click(screen.getByRole("button", { name: "CALCULATE" }));
    await waitFor(() =>
      expect(screen.getByRole("tab", { name: "REGRESSION" })).toHaveAttribute(
        "aria-selected",
        "true",
      ),
    );

    act(() => {
      requestExport();
    });
    const nameInput = await screen.findByTestId("export-name");
    fireEvent.change(nameInput, { target: { value: "mi-motor" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(engineApiMock.saveEngine).toHaveBeenCalledTimes(1));
    expect(engineApiMock.saveEngine).toHaveBeenCalledWith("mi-motor", CALC_RESULT.payload);
    expect(await screen.findByText("Results exported")).toBeInTheDocument();
  });

  it("añade la consola del job en curso y muestra el progreso (filtrando por job)", async () => {
    const consoleHandlers: Array<(event: EngineEventMap["console"]) => void> = [];
    const progressHandlers: Array<(event: EngineEventMap["progress"]) => void> = [];
    engineApiMock.onConsole.mockImplementation(
      async (handler: (event: EngineEventMap["console"]) => void) => {
        consoleHandlers.push(handler);
        return () => {};
      },
    );
    engineApiMock.onProgress.mockImplementation(
      async (handler: (event: EngineEventMap["progress"]) => void) => {
        progressHandlers.push(handler);
        return () => {};
      },
    );
    // Cálculo que nunca termina: deja el diálogo de progreso abierto.
    engineApiMock.calculateEngine.mockImplementation(() => new Promise<EngineCalculateResult>(() => {}));

    renderEngine();
    await screen.findByTestId("grain-field-Tubular-Grain-cx_real");
    await waitFor(() => expect(screen.getByLabelText("Propellant")).toHaveValue("KNSU (1)"));

    fireEvent.click(screen.getByRole("tab", { name: "CONSOLE" }));
    fireEvent.click(screen.getByRole("button", { name: "CALCULATE" }));
    await waitFor(() => expect(engineApiMock.calculateEngine).toHaveBeenCalledTimes(1));
    expect(screen.getByText("Calculating…")).toBeInTheDocument();

    act(() => {
      for (const handler of consoleHandlers) {
        handler({ name: "console", job: "engine.calculate", line: "Iter: 1" });
      }
    });
    expect(screen.getByText("Iter: 1")).toBeInTheDocument();

    act(() => {
      for (const handler of consoleHandlers) {
        handler({ name: "console", job: "nozzle.calculate", line: "Otro job" });
      }
    });
    expect(screen.queryByText("Otro job")).toBeNull();

    act(() => {
      for (const handler of progressHandlers) {
        handler({ name: "progress", job: "engine.calculate", value: 0.5, label: "Step" });
      }
    });
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "0.5");
  });
});
