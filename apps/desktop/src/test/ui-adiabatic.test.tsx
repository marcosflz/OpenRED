import { beforeEach, describe, expect, it, vi } from "vitest";
import { useEffect } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { ToastProvider } from "../components/Toast";
import { WorkspaceProvider, useWorkspace } from "../app/WorkspaceProvider";
import { AdiabaticTab } from "../ui/adiabatic";
import { formatLegacyResult } from "../ui/adiabatic/format";
import { ComponentsWindow, PropellantsWindow } from "../ui/db-windows";
import { mockCalls, resetMockCalls } from "../api/mock";

// ECharts no inicializa en jsdom (canvas); en las pruebas basta el marcador.
vi.mock("../components/LineChart", () => ({
  baseChartOption: () => ({}),
  LineChart: ({ ariaLabel }: { ariaLabel?: string }) => (
    <div data-testid="line-chart" aria-label={ariaLabel} />
  ),
}));

/** `tab_0` de `legacy/workingDirectory/config.json` (G2/G3). */
const TAB0 = vi.hoisted(() => ({
  tabs: {
    tab_0: {
      reactivos: [
        ["1", "C12H22O11 (Solid/Liquid)"],
        ["6.288", "KNO3 (S)"],
      ],
      productos: [
        ["3.796", "CO2"],
        ["7.794", "H2O"],
      ],
      initial_temp: "293",
      temp_Int_step: "1",
      temp_guess: "1500",
    },
  },
}));

vi.mock("../api/engine", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/engine")>();
  const { mockRequest } = await import("../api/mock");
  return {
    ...actual,
    request: async (method: string, params: Record<string, unknown> = {}) => {
      if (method === "workspace.load_config") {
        return { config: TAB0, hasConfig: true };
      }
      // Paridad T0-4: el motor rechaza hStep <= 0 con este mensaje.
      if (method === "adiabatic.calculate" && Number(params.hStep) <= 0) {
        throw new actual.RpcError(-32602, "Invalid integration step value.", null);
      }
      return mockRequest(method, params);
    },
  };
});

function Harness({ load }: { load: boolean }) {
  const { loadConfig, config } = useWorkspace();
  useEffect(() => {
    if (load) void loadConfig();
  }, [load, loadConfig]);
  return (
    <>
      <AdiabaticTab />
      <pre data-testid="tab0-config">{JSON.stringify(config.tabs?.tab_0 ?? null)}</pre>
    </>
  );
}

function renderTab(load = false) {
  return render(
    <ToastProvider>
      <WorkspaceProvider>
        <Harness load={load} />
      </WorkspaceProvider>
    </ToastProvider>,
  );
}

beforeEach(() => {
  resetMockCalls();
});

describe("AdiabaticTab (T0)", () => {
  it("añade y elimina filas dinámicas de reactivos y productos (T0-1)", async () => {
    renderTab();
    expect(await screen.findByLabelText("Reactant 1 component")).toBeInTheDocument();
    expect(screen.getByLabelText("Product 1 component")).toBeInTheDocument();
    // La reacción se renderiza con KaTeX (T0-2).
    expect(document.querySelector(".katex")).not.toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Add Reactant" }));
    fireEvent.click(screen.getByRole("button", { name: "Add Product" }));
    expect(screen.getByLabelText("Reactant 2 component")).toBeInTheDocument();
    expect(screen.getByLabelText("Product 2 component")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Remove Reactant" }));
    expect(screen.queryByLabelText("Reactant 2 component")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Reactant 1 component")).toBeInTheDocument();
  });

  it("persiste tab_0 en config.json al editar las filas (G3)", async () => {
    renderTab();
    await screen.findByLabelText("Reactant 1 component");
    fireEvent.change(screen.getByLabelText("Reactant 1 moles"), { target: { value: "2.5" } });

    await waitFor(() => {
      const tab0 = JSON.parse(screen.getByTestId("tab0-config").textContent ?? "null");
      expect(tab0?.reactivos?.[0]?.[0]).toBe("2.5");
    });
    const tab0 = JSON.parse(screen.getByTestId("tab0-config").textContent ?? "null");
    expect(tab0.initial_temp).toBe("293");
    expect(tab0.temp_Int_step).toBe("1");
    expect(tab0.temp_guess).toBe("1500");
    expect(tab0.productos).toHaveLength(1);
    expect(tab0.reactivos[0][1]).toBe("KNO3 (S)");
  });

  it("restaura tab_0 de config.json tal cual, sin validar (G2/G3)", async () => {
    renderTab(true);
    await waitFor(() =>
      expect(screen.getByLabelText("Reactant 1 moles")).toHaveValue("1"),
    );
    expect(screen.getByLabelText("Reactant 2 moles")).toHaveValue("6.288");
    expect(screen.getByLabelText("Reactant 2 component")).toHaveValue("KNO3 (S)");
    expect(screen.getByLabelText("Product 1 component")).toHaveValue("CO2");
    expect(screen.getByLabelText("Product 2 moles")).toHaveValue("7.794");
    expect(screen.getByLabelText("Inlet Temperature (K):")).toHaveValue("293");
    expect(screen.getByLabelText("Integration Step (K):")).toHaveValue("1");
    expect(screen.getByLabelText("Initial Temperature (K):")).toHaveValue("1500");
  });

  it("CALCULATE llama a adiabatic.calculate y muestra los 7 resultados (T0-3)", async () => {
    renderTab(true);
    await waitFor(() => expect(screen.getByLabelText("Reactant 1 moles")).toHaveValue("1"));

    fireEvent.click(screen.getByRole("button", { name: "Calculate" }));
    await screen.findByDisplayValue("1720.5000");

    expect(screen.getByLabelText("Molecular Weight of Product (kg/mol):")).toHaveValue("41.2000");
    expect(screen.getByLabelText("Specific Heat at Constant Pressure (J/(kg*K)):")).toHaveValue(
      "1.8500",
    );
    expect(screen.getByLabelText("Specific Heat at Constant Volume (J/(kg*K)):")).toHaveValue(
      "1.4500",
    );
    expect(screen.getByLabelText("Gas Constant of Product (J/(kg*K)):")).toHaveValue("287.0000");
    expect(screen.getByLabelText("Gamma (Cp/Cv):")).toHaveValue("1.2770");
    expect(screen.getByLabelText("Characteristic Velocity (m/s):")).toHaveValue("1450.2000");

    const call = mockCalls().find((entry) => entry.name === "adiabatic.calculate");
    expect(call?.params).toMatchObject({ t0: 293, tGuess: 1500, hStep: 1 });
    expect(call?.params.reac).toEqual([
      { moles: 1, component: "C12H22O11 (Solid/Liquid)" },
      { moles: 6.288, component: "KNO3 (S)" },
    ]);
    expect(call?.params.prod).toEqual([
      { moles: 3.796, component: "CO2" },
      { moles: 7.794, component: "H2O" },
    ]);
  });

  it("hStep=0 muestra el aviso del motor (T0-4)", async () => {
    renderTab(true);
    await waitFor(() => expect(screen.getByLabelText("Reactant 1 moles")).toHaveValue("1"));

    fireEvent.change(screen.getByLabelText("Integration Step (K):"), { target: { value: "0" } });
    fireEvent.click(screen.getByRole("button", { name: "Calculate" }));
    expect(await screen.findByText("Invalid integration step value.")).toBeInTheDocument();
  });

  it("guarda el propelente calculado con adiabatic.save_propellant (T0-5)", async () => {
    renderTab(true);
    await waitFor(() => expect(screen.getByLabelText("Reactant 1 moles")).toHaveValue("1"));

    fireEvent.click(screen.getByRole("button", { name: "Calculate" }));
    await screen.findByDisplayValue("1720.5000");
    fireEvent.click(screen.getByRole("button", { name: "Save Propellant" }));

    fireEvent.change(screen.getByLabelText("Propellant Name:"), {
      target: { value: "KNSU-test" },
    });
    fireEvent.change(screen.getByLabelText("Propellant Density (kg/m^3):"), {
      target: { value: "1.84" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(mockCalls().some((entry) => entry.name === "adiabatic.save_propellant")).toBe(true);
    });
    const call = mockCalls().find((entry) => entry.name === "adiabatic.save_propellant");
    expect(call?.params).toMatchObject({
      values: { Propelente: "KNSU-test", T_ad: 1720.5, Density: 1.84 },
    });
  });
});

describe("formatLegacyResult", () => {
  it("reproduce el formato .4e/.4f del legacy", () => {
    expect(formatLegacyResult(1720.5)).toBe("1720.5000");
    expect(formatLegacyResult(1.5e6)).toBe("1.5000e+06");
    expect(formatLegacyResult(-5e6)).toBe("-5000000.0000");
    expect(formatLegacyResult(Number.NaN)).toBe("");
  });
});

describe("ventanas de base de datos (D/G)", () => {
  it("ComponentsWindow rellena los campos al elegir el ID (D-1)", async () => {
    render(
      <ToastProvider>
        <ComponentsWindow open onClose={() => {}} />
      </ToastProvider>,
    );
    const select = await screen.findByLabelText("Component (id)");
    await waitFor(() => expect(select).toHaveValue(""));

    fireEvent.change(select, { target: { value: "2" } });
    await waitFor(() =>
      expect(screen.getByLabelText("Component")).toHaveValue("C12H22O11 (Solid/Liquid)"),
    );
    expect(screen.getByLabelText("MolWeight")).toHaveValue("342.297");
    expect(screen.getByLabelText("Hf0 (298K)")).toHaveValue("-2226.1");
  });

  it("sustituye comas por puntos mostrando el aviso del legacy (D-1)", async () => {
    render(
      <ToastProvider>
        <ComponentsWindow open onClose={() => {}} />
      </ToastProvider>,
    );
    const molWeight = await screen.findByLabelText("MolWeight");
    fireEvent.change(molWeight, { target: { value: "342,5" } });
    expect(molWeight).toHaveValue("342.5");
    expect(
      screen.getByText("The comma has been replaced with a period to maintain numerical format."),
    ).toBeInTheDocument();
  });

  it("ComponentsWindow limpia el nombre y rellena los vacíos con '0' al añadir (D-1/D-4)", async () => {
    render(
      <ToastProvider>
        <ComponentsWindow open onClose={() => {}} />
      </ToastProvider>,
    );
    await screen.findByLabelText("Component (id)");
    fireEvent.change(screen.getByLabelText("Component"), { target: { value: "H2O (12)" } });
    fireEvent.change(screen.getByLabelText("MolWeight"), { target: { value: "18.015" } });
    fireEvent.click(screen.getByRole("button", { name: "Add" }));

    await waitFor(() =>
      expect(mockCalls().some((entry) => entry.name === "db.components.add")).toBe(true),
    );
    const call = mockCalls().find((entry) => entry.name === "db.components.add");
    expect(call?.params).toMatchObject({
      values: { Component: "H2O", MolWeight: "18.015", Hf0: "0" },
    });
  });

  it("ComponentsWindow edita y borra por ID (D-3)", async () => {
    render(
      <ToastProvider>
        <ComponentsWindow open onClose={() => {}} />
      </ToastProvider>,
    );
    const select = await screen.findByLabelText("Component (id)");
    fireEvent.change(select, { target: { value: "2" } });
    await waitFor(() => expect(screen.getByLabelText("MolWeight")).toHaveValue("342.297"));

    fireEvent.change(screen.getByLabelText("MolWeight"), { target: { value: "343" } });
    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    await waitFor(() =>
      expect(mockCalls().some((entry) => entry.name === "db.components.edit")).toBe(true),
    );
    const edit = mockCalls().find((entry) => entry.name === "db.components.edit");
    expect(edit?.params).toMatchObject({ id: 2, values: { Component: "C12H22O11 (Solid/Liquid)" } });

    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    await waitFor(() =>
      expect(mockCalls().some((entry) => entry.name === "db.components.delete")).toBe(true),
    );
    expect(mockCalls().find((entry) => entry.name === "db.components.delete")?.params).toEqual({
      id: 2,
    });
  });

  it("PropellantsWindow pide la curva de quemado con 1000 puntos y la dibuja (G9)", async () => {
    render(
      <ToastProvider>
        <PropellantsWindow open onClose={() => {}} />
      </ToastProvider>,
    );
    const select = await screen.findByLabelText("Propellant (id)");
    fireEvent.change(select, { target: { value: "1" } });
    await waitFor(() => expect(screen.getByLabelText("Propellant")).toHaveValue("KNSU"));

    fireEvent.click(screen.getByRole("button", { name: "Show Burning Rate Curve" }));
    expect(await screen.findByTestId("line-chart")).toBeInTheDocument();

    const call = mockCalls().find((entry) => entry.name === "db.propellants.burning_rate");
    expect(call?.params).toMatchObject({ name: "KNSU", n_points: 1000 });
  });
});
