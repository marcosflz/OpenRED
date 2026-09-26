import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { ToastProvider } from "../components/Toast";
import { mockCalls, resetMockCalls } from "../api/mock";
import { request } from "../api/engine";
import type { EngineEvent } from "../api/types";
import { TestbedTab } from "../ui/testbed";

type Listener = (event: EngineEvent) => void;

/**
 * Simula el canal `engine-event` fuera de Tauri: el `request` mockeado emite
 * el guion de `testbed.mock` y los estados del protocolo como haría el motor.
 */
const bus = vi.hoisted(() => {
  const handlers = new Set<(event: unknown) => void>();
  return {
    handlers,
    emit(event: unknown) {
      for (const handler of [...handlers]) handler(event);
    },
  };
});

vi.mock("../api/engine", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/engine")>();
  const { mockRequest } = await import("../api/mock");
  return {
    ...actual,
    onEngineEvent: async (handler: Listener) => {
      const listener = handler as (event: unknown) => void;
      bus.handlers.add(listener);
      return () => {
        bus.handlers.delete(listener);
      };
    },
    request: vi.fn(async (method: string, params: Record<string, unknown> = {}) => {
      if (method === "testbed.mock") {
        const script = Array.isArray(params.script) ? (params.script as string[]) : [];
        for (const line of script) {
          bus.emit({ name: "serial_line", line });
          if (line.includes("SERIAL STARTED")) {
            bus.emit({
              name: "state",
              connected: true,
              wifiReady: false,
              recording: false,
              checklistEnabled: false,
              checklistComplete: false,
              leds: { serial: "green", wifi: "off" },
            });
          }
          if (line.includes("TEST-BENCH CONNECTED")) {
            bus.emit({
              name: "state",
              connected: true,
              wifiReady: false,
              recording: false,
              checklistEnabled: true,
              checklistComplete: false,
              leds: { serial: "green", wifi: "green" },
            });
          }
        }
        return { ok: true, enabled: params.enabled === true };
      }
      return mockRequest(method, params);
    }),
  };
});

function renderTab() {
  return render(
    <ToastProvider>
      <TestbedTab active />
    </ToastProvider>,
  );
}

describe("TestbedTab (T4)", () => {
  beforeEach(() => {
    resetMockCalls();
    bus.handlers.clear();
  });

  it("activa la demo mock y vuelca el guion en el Console", async () => {
    renderTab();

    // La checklist se carga al montar y arranca deshabilitada.
    const boxes = await screen.findAllByRole("checkbox");
    expect(boxes).toHaveLength(3);
    for (const box of boxes) expect(box).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Demo (mock)" }));

    expect(await screen.findByText("SERIAL STARTED")).toBeInTheDocument();
    expect(await screen.findByText("TEST-BENCH CONNECTED")).toBeInTheDocument();
    expect(
      await screen.findByText(/t\(s\): 0\.025 F\(kg\): 0\.049 T\(K\): 301\.4/),
    ).toBeInTheDocument();

    // El estado simulado de "TEST-BENCH CONNECTED" habilita la checklist.
    await waitFor(() => {
      for (const box of screen.getAllByRole("checkbox")) expect(box).toBeEnabled();
    });

    const call = vi
      .mocked(request)
      .mock.calls.find(([method]) => method === "testbed.mock");
    expect(call?.[1]).toMatchObject({ enabled: true });
    expect(Array.isArray(call?.[1]?.script)).toBe(true);
    expect(bus.handlers.size).toBe(1); // suscripción única y viva
  });

  it("Run crea el CSV y muestra los datos del test", async () => {
    renderTab();

    fireEvent.click(screen.getByRole("button", { name: "Run" }));

    const runInfo = await screen.findByTestId("testbed-run-info");
    expect(
      within(runInfo).getByText(/KNSU-32-RT65-19\.28\.35-15\.09\.24\.csv/),
    ).toBeInTheDocument();
    expect(within(runInfo).getByText("BN1")).toBeInTheDocument();
    expect(within(runInfo).getByText("150 kg")).toBeInTheDocument();
    expect(within(runInfo).getByText("1200 K")).toBeInTheDocument();

    const call = mockCalls().find((entry) => entry.name === "testbed.run");
    expect(call?.params.nozzleFile).toContain("KNSU-32-RT65.json");
  });

  it("Abortar avisa del reset y la contraseña WiFi no se conserva", async () => {
    renderTab();
    await screen.findAllByRole("checkbox");
    // Espera al `testbed.state` inicial para que no pise el estado simulado.
    await waitFor(() =>
      expect(mockCalls().some((entry) => entry.name === "testbed.state")).toBe(true),
    );

    act(() => {
      bus.emit({
        name: "state",
        connected: true,
        // El protocolo habilita SSID/password al recibir RESET (LED WiFi aún off).
        wifiReady: true,
        recording: false,
        checklistEnabled: true,
        checklistComplete: false,
        leds: { serial: "green", wifi: "off" },
      });
    });

    const password = screen.getByTestId("wifi-password") as HTMLInputElement;
    expect(password).toBeEnabled();

    fireEvent.change(screen.getByLabelText("SSID"), { target: { value: "OpenRED-AP" } });
    fireEvent.change(password, { target: { value: "super-secret" } });
    fireEvent.click(screen.getByRole("button", { name: "Conectar WiFi" }));

    await waitFor(() => {
      const call = vi
        .mocked(request)
        .mock.calls.find(([method]) => method === "testbed.connect_wifi");
      expect(call?.[1]).toMatchObject({ ssid: "OpenRED-AP", password: "super-secret" });
    });
    await waitFor(() => expect((screen.getByTestId("wifi-password") as HTMLInputElement).value).toBe(""));
    expect(screen.queryByDisplayValue("super-secret")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Abortar" }));
    expect(await screen.findByText("Test aborted. Reset command sent.")).toBeInTheDocument();
    expect(mockCalls().some((entry) => entry.name === "testbed.abort")).toBe(true);
  });
});
