import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { requestExport } from "../app/bus";
import { WorkspaceProvider } from "../app/WorkspaceProvider";
import { RpcError } from "../api/errors";
import { ToastProvider } from "../components/Toast";
import { CadTab } from "../ui/cad";
import { AS_NOZZLE_MESSAGE } from "../ui/cad/settings";

/**
 * `cad.*` va contra el backend mock de `src/api/mock.ts`, pero el mock solo
 * devuelve 2 campos: aquí se sustituye `request`/`pick_*` para controlar las
 * respuestas de `cad.load_nozzle`, `cad.views` y `cad.export`.
 */
const mocks = vi.hoisted(() => ({
  request: vi.fn(),
  pickFile: vi.fn(),
  pickSaveFile: vi.fn(),
}));

vi.mock("../api/engine", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/engine")>();
  return {
    ...actual,
    request: mocks.request,
    pickFile: mocks.pickFile,
    pickSaveFile: mocks.pickSaveFile,
  };
});

interface FieldFixture {
  key: string;
  label: string;
  type: "select" | "number" | "checkbox";
  options?: string[];
  default?: unknown;
}

const NUMBER_FIELDS: FieldFixture[] = [
  { key: "n_conv", label: "Puntos Arco Convergente (n)", type: "number" },
  { key: "t_cartridge", label: "Espesor de Cartucho (m)", type: "number" },
  { key: "KIn", label: "Coeficiente radio entrada (%)", type: "number" },
  { key: "alpha", label: "Angulo zona convergente (deg)", type: "number" },
  { key: "wall_t", label: "Espesor de pared (m)", type: "number" },
  { key: "bolt_OffSet", label: "Longitud tornillo (m)", type: "number" },
  { key: "hBoltFactor", label: "Factor de altura del tornillo (%)", type: "number" },
  { key: "cover_t", label: "Espesor de la cubierta (m)", type: "number" },
  { key: "dy_elect", label: "Distancia entre electrodos (m)", type: "number" },
  { key: "d_elect", label: "Diámetro del electrodo (m)", type: "number" },
  { key: "t_factor", label: "Factor Espesor Tools (%)", type: "number" },
  { key: "extra_len", label: "Longitud Extra de molde (m)", type: "number" },
  { key: "cover_len", label: "Longitud exterior molde (m)", type: "number" },
  { key: "nut_h", label: "Altura de Tuerca (m)", type: "number" },
  { key: "nut_dr", label: "Incremento radio de Tuerca (m)", type: "number" },
];

const CHECK_FIELDS: FieldFixture[] = [
  { key: "on_Cartridge", label: "Mostrar Cartucho", type: "checkbox", default: true },
  { key: "on_Propellant", label: "Mostrar Propelente", type: "checkbox", default: true },
  { key: "on_Engine", label: "Mostrar Motor", type: "checkbox", default: true },
  { key: "on_Cover", label: "Mostrar Cubierta", type: "checkbox", default: true },
  { key: "on_CoverCast1", label: "Cubierta de molde", type: "checkbox", default: true },
  { key: "on_CoverCast2", label: "Sujección de molde", type: "checkbox", default: true },
  { key: "on_CastBolt", label: "Tornillo de Tuerca", type: "checkbox", default: true },
  { key: "on_Mould", label: "Molde de propelente", type: "checkbox", default: true },
  { key: "on_CastNut", label: "Tuerca de molde", type: "checkbox", default: true },
];

/** 25 campos como los del motor: 1 select + 15 numéricos + 9 checkboxes. */
const CONVENTIONAL_FIELDS: FieldFixture[] = [
  {
    key: "type",
    label: "Tipo de pared en la tobera",
    type: "select",
    options: ["Fitted", "Bulk"],
    default: "Fitted",
  },
  ...NUMBER_FIELDS,
  ...CHECK_FIELDS,
];

const PNG_1PX =
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==";

function viewsPayload() {
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

function conventionalResult(suggested: Record<string, unknown> = {}) {
  return {
    config: { Inputs: { NozzleConfig: "BN1" } },
    architecture: "conventional",
    fields: CONVENTIONAL_FIELDS,
    checks: CHECK_FIELDS,
    suggested,
  };
}

function mockBackend(
  loadNozzle: () => unknown,
  exportImpl?: (params: Record<string, unknown>) => unknown,
) {
  mocks.request.mockImplementation(async (method: string, params: Record<string, unknown>) => {
    switch (method) {
      case "workspace.get":
        return { workdir: "C:\\work", workdirSelected: true };
      case "workspace.load_config":
        return { config: { tabs: {} }, hasConfig: false };
      case "cad.load_nozzle":
        return loadNozzle();
      case "cad.views":
        return viewsPayload();
      case "cad.export":
        return exportImpl ? exportImpl(params) : { path: "C:\\work\\Sketches\\out.csv", written: [] };
      default:
        throw new Error(`Petición inesperada: ${method}`);
    }
  });
}

function renderCad() {
  return render(
    <ToastProvider>
      <WorkspaceProvider>
        <CadTab active />
      </WorkspaceProvider>
    </ToastProvider>,
  );
}

function viewsCalls() {
  return mocks.request.mock.calls.filter(([method]) => method === "cad.views");
}

async function loadNozzle(path = "C:\\work\\Nozzles\\BN1.json") {
  mocks.pickFile.mockResolvedValue(path);
  fireEvent.click(await screen.findByRole("button", { name: "LOAD" }));
}

beforeEach(() => {
  mocks.request.mockReset();
  mocks.pickFile.mockReset();
  mocks.pickSaveFile.mockReset();
  mockBackend(() => conventionalResult());
});

describe("CadTab (T3)", () => {
  it("no crea campos para AS-Nozzle y muestra el aviso (T3-5)", async () => {
    mockBackend(() => ({
      config: { Inputs: { NozzleConfig: "AS-Nozzle" } },
      architecture: "as-nozzle",
      fields: [],
      checks: [],
      message: AS_NOZZLE_MESSAGE,
    }));
    const { container } = renderCad();
    await loadNozzle("C:\\work\\Nozzles\\AS-Nozzle.json");

    const warning = await screen.findByTestId("cad-unsupported");
    expect(warning).toHaveTextContent(
      "AS-Nozzle architecture is not supported by the CAD module.",
    );
    expect(container.querySelectorAll("[data-field]")).toHaveLength(0);
    expect(screen.queryAllByRole("combobox")).toHaveLength(0);
    expect(screen.queryAllByRole("textbox")).toHaveLength(0);
    expect(screen.queryAllByRole("checkbox")).toHaveLength(0);
    expect(viewsCalls()).toHaveLength(0);
    expect(mocks.pickFile).toHaveBeenCalledWith(["json"]);
  });

  it("construye los 25 campos de una tobera convencional y aplica `suggested`", async () => {
    mockBackend(() => conventionalResult({ n_conv: "50", type: "Bulk", on_Cover: 0 }));
    const { container } = renderCad();
    await loadNozzle();

    await waitFor(() => expect(container.querySelectorAll("[data-field]")).toHaveLength(25));
    expect(container.querySelectorAll("select")).toHaveLength(1);
    expect(container.querySelectorAll('input[type="text"]')).toHaveLength(15);
    expect(container.querySelectorAll('input[type="checkbox"]')).toHaveLength(9);
    expect(screen.getByLabelText("Tipo de pared en la tobera")).toHaveValue("Bulk");
    expect(screen.getByLabelText("Puntos Arco Convergente (n)")).toHaveValue("50");
    expect(screen.getByLabelText("Mostrar Cubierta")).not.toBeChecked();
  });

  it("un cambio de checkbox regenera las vistas con el nuevo valor (T3-2)", async () => {
    renderCad();
    await loadNozzle();

    await waitFor(() => expect(viewsCalls().length).toBeGreaterThanOrEqual(1));
    await waitFor(() => expect(screen.getByRole("img", { name: "Engine" })).toBeInTheDocument());
    const before = viewsCalls().length;

    fireEvent.click(screen.getByLabelText("Mostrar Cartucho"));
    await waitFor(() => expect(viewsCalls().length).toBeGreaterThan(before));

    const last = viewsCalls()[viewsCalls().length - 1];
    const params = last[1] as {
      config: unknown;
      settings: Record<string, unknown>;
      type: string;
    };
    expect(params.settings.on_Cartridge).toBe(0);
    expect(params.type).toBe("Fitted");
    expect(params.config).toEqual({ Inputs: { NozzleConfig: "BN1" } });
  });

  it("ante el error 1004 pide confirmación y reintenta con overwrite (T3-3/T3-4)", async () => {
    const exports: Array<Record<string, unknown>> = [];
    let first = true;
    mockBackend(
      () => conventionalResult(),
      (params) => {
        exports.push(params);
        if (first) {
          first = false;
          throw new RpcError(
            1004,
            "El archivo BN1_ENGINE_CAD.csv ya existe. ¿Quieres sobrescribirlo?",
            null,
          );
        }
        return { path: "C:\\work\\Sketches\\BN1_ENGINE_CAD.csv", written: ["BN1_ENGINE_CAD.csv"] };
      },
    );
    mocks.pickSaveFile.mockResolvedValue("C:\\work\\Sketches\\BN1_ENGINE_CAD.csv");

    renderCad();
    await loadNozzle();
    await waitFor(() => expect(screen.getByRole("button", { name: "EXPORT ENGINE" })).toBeEnabled());
    expect(mocks.pickSaveFile).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "EXPORT ENGINE" }));
    const confirm = await screen.findByRole("button", { name: "Sobrescribir" });
    expect(screen.getByText(/BN1_ENGINE_CAD\.csv ya existe/)).toBeInTheDocument();
    expect(mocks.pickSaveFile).toHaveBeenCalledWith("BN1_ENGINE_CAD.csv");

    fireEvent.click(confirm);
    await waitFor(() => expect(exports).toHaveLength(2));
    expect(exports[0]).toMatchObject({ kind: "engine", name: "BN1_ENGINE_CAD.csv" });
    expect(exports[0].overwrite).toBeUndefined();
    expect(exports[1]).toMatchObject({
      kind: "engine",
      name: "BN1_ENGINE_CAD.csv",
      overwrite: true,
    });
  });

  it("exporta `engine` al recibir `openred:export` con la pestaña activa", async () => {
    const exports: Array<Record<string, unknown>> = [];
    mockBackend(
      () => conventionalResult(),
      (params) => {
        exports.push(params);
        return { path: "C:\\work\\Sketches\\menu.csv", written: [] };
      },
    );
    mocks.pickSaveFile.mockResolvedValue("C:\\work\\Sketches\\menu.csv");

    renderCad();
    await loadNozzle();
    await waitFor(() => expect(screen.getByRole("button", { name: "EXPORT ENGINE" })).toBeEnabled());

    act(() => requestExport());
    await waitFor(() => expect(exports).toHaveLength(1));
    expect(exports[0].kind).toBe("engine");
    expect(mocks.pickSaveFile).toHaveBeenCalledWith("BN1_ENGINE_CAD.csv");
  });
});
