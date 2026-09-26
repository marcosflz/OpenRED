import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type CSSProperties,
} from "react";
import {
  Button,
  Card,
  Checkbox,
  Console,
  Gauge,
  LineChart,
  Select,
  Table,
  TextField,
  useToast,
  type ConsoleLine,
  type EChartsOption,
  type TableColumn,
} from "../../components";
import {
  isCancel,
  onEngineEvent,
  pickFile,
  request,
  toRpcError,
  type ChecklistItem,
  type EngineEvent,
  type PortInfo,
  type SerialRecord,
  type TestbedRunResult,
} from "../../api/engine";
import { formatNumber } from "../../utils/numbers";
import type { TabModuleProps } from "../types";
import {
  DEMO_SCRIPT,
  INITIAL_STATUS,
  LED_COLORS,
  LED_LABELS,
  MAX_CONSOLE_LINES,
  NO_PORTS,
  normalizePortList,
  portDevice,
  readChecklistItems,
  readChecklistResult,
  readRecord,
  readRunInfo,
  readStatus,
  type LedColor,
  type TestbedRunInfo,
  type TestbedStatus,
} from "./helpers";

export interface TestbedTabProps extends TabModuleProps {}

type BusyAction = "run" | "connect" | "disconnect" | "wifi" | "abort" | "demo";

/* ------------------------------------------------------------------ */
/* Estilos auxiliares (el módulo no puede tocar src/styles)            */
/* ------------------------------------------------------------------ */

const moduleStyle: CSSProperties = { display: "flex", flexDirection: "column", gap: 12 };
const topRowStyle: CSSProperties = {
  display: "grid",
  gap: 12,
  gridTemplateColumns: "minmax(240px, 320px) minmax(320px, 1fr)",
  alignItems: "start",
};
const middleRowStyle: CSSProperties = {
  display: "grid",
  gap: 12,
  gridTemplateColumns: "minmax(320px, 1.2fr) minmax(280px, 1fr)",
  alignItems: "start",
};
const twoColsStyle: CSSProperties = {
  display: "grid",
  gap: 12,
  gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
};
const optionsRowStyle: CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  gap: 8,
  alignItems: "flex-end",
};
const metaGridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "auto 1fr",
  gap: "4px 12px",
  fontSize: "var(--font-size-sm)",
};
const metaLabelStyle: CSSProperties = { color: "var(--text-muted)" };
const metaValueStyle: CSSProperties = { wordBreak: "break-all" };
const gaugesStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
  gap: 12,
  justifyItems: "center",
};
const greenButtonStyle: CSSProperties = {
  background: LED_COLORS.green,
  borderColor: LED_COLORS.green,
  color: "#ffffff",
};
const recordingBadgeStyle: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  padding: "2px 8px",
  borderRadius: "var(--radius-pill)",
  background: "rgba(76, 175, 125, 0.18)",
  color: "var(--success)",
  fontSize: "var(--font-size-sm)",
  fontWeight: 600,
};

function LedIndicator({ kind, color }: { kind: "serial" | "wifi"; color: LedColor }) {
  const name = kind === "serial" ? "Serial" : "WiFi";
  return (
    <div
      data-testid={`led-${kind}`}
      data-color={color}
      style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "var(--font-size-sm)" }}
    >
      <span
        aria-hidden="true"
        style={{
          width: 10,
          height: 10,
          borderRadius: "50%",
          background: LED_COLORS[color],
          boxShadow: color === "off" ? "none" : `0 0 6px ${LED_COLORS[color]}`,
        }}
      />
      <span>
        {name}: {LED_LABELS[color]}
      </span>
    </div>
  );
}

const recordColumns: Array<TableColumn<SerialRecord>> = [
  { key: "t", header: "t (s)", align: "right", render: (row) => formatNumber(row.t, 4) },
  { key: "F", header: "F (kg)", align: "right", render: (row) => formatNumber(row.F, 4) },
  { key: "T", header: "T (K)", align: "right", render: (row) => formatNumber(row.T, 4) },
];

/** Aviso mostrado cuando el entorno no puede inicializar ECharts (sin canvas). */
function ChartFallback() {
  return (
    <p style={{ margin: 0, color: "var(--text-muted)", fontSize: "var(--font-size-sm)" }}>
      Gráfica no disponible: el entorno no soporta canvas 2D.
    </p>
  );
}

function formatMetric(value: number | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? formatNumber(value, 3) : "—";
}

/**
 * `true` cuando el entorno expone canvas 2D (WebView/WebView2, navegadores).
 * jsdom no lo implementa y `echarts.init` fallaría; en ese caso las tarjetas
 * muestran un aviso en lugar de romper el módulo.
 */
const CANVAS_2D_AVAILABLE = typeof CanvasRenderingContext2D !== "undefined";

/* ------------------------------------------------------------------ */
/* Módulo                                                              */
/* ------------------------------------------------------------------ */

/**
 * Pestaña T4 (banco de pruebas): puertos COM, máquina de estados del ESP32,
 * checklist, WiFi, registros en vivo (CSV + gauges) y aborto.
 *
 * Referencia funcional: `legacy/front_modules/front_test.py`.
 */
export function TestbedTab({ active = true, className }: TestbedTabProps) {
  const toast = useToast();

  const [status, setStatus] = useState<TestbedStatus>(INITIAL_STATUS);
  const [ports, setPorts] = useState<string[]>([NO_PORTS]);
  const [selectedPort, setSelectedPort] = useState<string>(NO_PORTS);
  const [serialLines, setSerialLines] = useState<ConsoleLine[]>([]);
  const [records, setRecords] = useState<SerialRecord[]>([]);
  const [run, setRun] = useState<TestbedRunInfo | null>(null);
  const [checklistTitle, setChecklistTitle] = useState("TEST CHECKLIST");
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
  const [ssid, setSsid] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState<BusyAction | null>(null);
  const [demoActive, setDemoActive] = useState(false);

  /** Muestra los RpcError como toast; 1005 (cancelado) es silencioso. */
  const report = useCallback(
    (error: unknown, title: string) => {
      const rpc = toRpcError(error);
      if (isCancel(rpc)) return;
      toast.error({ title, message: rpc.message });
    },
    [toast],
  );

  const clearLiveData = useCallback(() => {
    setRecords([]);
  }, []);

  const applyPorts = useCallback((next: string[]) => {
    setPorts(next);
    setSelectedPort((current) => (next.includes(current) ? current : next[0]));
  }, []);

  const loadChecklist = useCallback(async () => {
    try {
      const result = await request<unknown>("testbed.checklist.load");
      const normalized = readChecklistResult(result);
      setChecklistTitle(normalized.title);
      setChecklist(normalized.items);
      return normalized.items;
    } catch (error) {
      report(error, "No se pudo cargar la checklist");
      return [];
    }
  }, [report]);

  const syncState = useCallback(async () => {
    const snapshot = await request<unknown>("testbed.state");
    setStatus((current) => ({ ...current, ...readStatus(snapshot) }));
    const info = readRunInfo(snapshot);
    if (Object.keys(info).length > 0) setRun((current) => ({ ...current, ...info }));
  }, []);

  /* -------------------------------------------------------------- */
  /* Eventos del motor (T4-3, T4-4, T4-6, T4-7)                     */
  /* -------------------------------------------------------------- */

  useEffect(() => {
    let disposed = false;
    let unlisten: (() => void) | null = null;

    void onEngineEvent((event: EngineEvent) => {
      if (event.name === "serial_line") {
        const line = event.line;
        setSerialLines((current) => {
          // "SERIAL STARTED" limpia el monitor (paridad con front_test).
          const base = line.includes("SERIAL STARTED") ? [] : current;
          const next = [...base, { text: line }];
          return next.length > MAX_CONSOLE_LINES ? next.slice(next.length - MAX_CONSOLE_LINES) : next;
        });
        return;
      }
      if (event.name === "record") {
        const record = readRecord(event);
        if (record) setRecords((current) => [...current, record]);
        return;
      }
      if (event.name === "state") {
        setStatus((current) => ({ ...current, ...readStatus(event) }));
        const info = readRunInfo(event);
        if (Object.keys(info).length > 0) setRun((current) => ({ ...current, ...info }));
        return;
      }
      if (event.name === "ports") {
        applyPorts(normalizePortList((event as { ports?: unknown }).ports));
      }
    }).then((fn) => {
      if (disposed) fn();
      else unlisten = fn;
    });

    return () => {
      disposed = true;
      unlisten?.();
    };
  }, [applyPorts]);

  /* -------------------------------------------------------------- */
  /* Arranque: puertos COM + checklist + estado (T4-2)              */
  /* -------------------------------------------------------------- */

  useEffect(() => {
    let cancelled = false;
    const bootstrap = async () => {
      try {
        const listed = await request<{ ports: PortInfo[] }>("testbed.list_ports");
        if (!cancelled) applyPorts(normalizePortList(listed?.ports));
        await request("testbed.monitor_ports", { enabled: true });
      } catch (error) {
        if (!cancelled) report(error, "No se pudieron listar los puertos COM");
      }
      if (cancelled) return;
      await loadChecklist();
      if (cancelled) return;
      try {
        await syncState();
      } catch {
        // El estado inicial es opcional: los eventos lo refrescarán.
      }
    };
    void bootstrap();
    return () => {
      cancelled = true;
      void request("testbed.monitor_ports", { enabled: false }).catch(() => undefined);
    };
  }, [applyPorts, loadChecklist, report, syncState]);

  /* -------------------------------------------------------------- */
  /* Acciones                                                       */
  /* -------------------------------------------------------------- */

  /** T4-1: elegir boquilla, `testbed.run` y publicar el CSV creado. */
  const handleRun = useCallback(async () => {
    try {
      const file = await pickFile([{ name: "JSON files", extensions: ["json"] }]);
      if (!file) return; // diálogo cancelado
      setBusy("run");
      const result = await request<TestbedRunResult>("testbed.run", { nozzleFile: file });
      setRun(result);
      clearLiveData();
      setStatus((current) => ({ ...current, recording: false, checklistComplete: false }));
      toast.success({ title: "Test preparado", message: result.testFile });
      // Nueva sesión: checklist sin marcar y monitor de estado al día.
      await loadChecklist();
      try {
        await syncState();
      } catch {
        // Sin estado inicial; el monitor de eventos seguirá informando.
      }
    } catch (error) {
      report(error, "No se pudo iniciar el test");
    } finally {
      setBusy(null);
    }
  }, [clearLiveData, loadChecklist, report, syncState, toast]);

  /** T4-3: conectar al puerto seleccionado (se envía solo el device). */
  const handleConnect = useCallback(async () => {
    if (selectedPort === NO_PORTS || selectedPort.trim() === "") {
      toast.warning({ message: NO_PORTS });
      return;
    }
    setBusy("connect");
    try {
      await request("testbed.connect_com", { port: portDevice(selectedPort) });
      setStatus((current) => ({ ...current, connected: true }));
    } catch (error) {
      report(error, "No se pudo conectar al puerto COM");
    } finally {
      setBusy(null);
    }
  }, [report, selectedPort, toast]);

  /** T4-3: cerrar la conexión serie. */
  const handleDisconnect = useCallback(async () => {
    setBusy("disconnect");
    try {
      await request("testbed.disconnect");
      setStatus((current) => ({
        ...current,
        connected: false,
        wifiReady: false,
        recording: false,
        checklistEnabled: false,
        leds: { serial: "off", wifi: "off" },
      }));
    } catch (error) {
      report(error, "No se pudo desconectar el puerto COM");
    } finally {
      setBusy(null);
    }
  }, [report]);

  /** T4-5: enviar SSID/contraseña; la contraseña no se registra ni se conserva. */
  const handleConnectWifi = useCallback(async () => {
    if (ssid.trim() === "" || password === "") {
      toast.warning({ message: "Introduce SSID y contraseña." });
      return;
    }
    setBusy("wifi");
    try {
      await request("testbed.connect_wifi", { ssid, password });
      toast.info({ message: "Credenciales WiFi enviadas al banco de pruebas." });
    } catch (error) {
      report(error, "No se pudo enviar la conexión WiFi");
    } finally {
      setPassword("");
      setBusy(null);
    }
  }, [password, report, ssid, toast]);

  /** T4-6: marcar/desmarcar la checklist; al completar arranca la grabación. */
  const handleToggleChecklist = useCallback(
    async (index: number, done: boolean) => {
      setChecklist((current) => current.map((item, i) => (i === index ? { ...item, done } : item)));
      try {
        const result = await request<{ items: ChecklistItem[]; complete: boolean }>(
          "testbed.checklist.toggle",
          { index, done },
        );
        setChecklist(readChecklistItems(result?.items));
        if (result?.complete) clearLiveData();
      } catch (error) {
        setChecklist((current) => current.map((item, i) => (i === index ? { ...item, done: !done } : item)));
        report(error, "No se pudo actualizar la checklist");
      }
    },
    [clearLiveData, report],
  );

  /** T4-8: abortar (ABORT + RESET) y volver al estado desconectado. */
  const handleAbort = useCallback(async () => {
    setBusy("abort");
    try {
      await request("testbed.abort");
      setStatus((current) => ({
        ...current,
        connected: false,
        wifiReady: false,
        recording: false,
        checklistEnabled: false,
        checklistComplete: false,
        leds: { serial: "off", wifi: "off" },
      }));
      await loadChecklist();
      toast.info({ message: "Test aborted. Reset command sent." });
    } catch (error) {
      report(error, "No se pudo abortar el test");
    } finally {
      setBusy(null);
    }
  }, [loadChecklist, report, toast]);

  /** T4-9: transporte simulado con guion de ejemplo (dev/vitest sin hardware). */
  const handleDemo = useCallback(async () => {
    setBusy("demo");
    try {
      if (demoActive) {
        await request("testbed.mock", { enabled: false });
        setDemoActive(false);
        toast.info({ message: "Demo (mock) desactivada." });
      } else {
        await request("testbed.mock", { enabled: true, script: [...DEMO_SCRIPT], demo: true });
        setDemoActive(true);
        toast.info({ title: "Demo (mock)", message: "Transporte simulado activado con el guion de ejemplo." });
      }
    } catch (error) {
      report(error, "No se pudo cambiar el modo demo");
    } finally {
      setBusy(null);
    }
  }, [demoActive, report, toast]);

  /* -------------------------------------------------------------- */
  /* Derivados                                                      */
  /* -------------------------------------------------------------- */

  const checklistComplete = checklist.length > 0 && checklist.every((item) => item.done);
  const recordingStarted = checklistComplete || status.recording;
  const serialGreen = status.leds.serial === "green";
  const wifiGreen = status.leds.wifi === "green";
  const hasPort = selectedPort !== NO_PORTS && selectedPort.trim() !== "";
  const connectDisabled = !hasPort || status.connected || serialGreen || busy === "connect";
  const connectWifiDisabled =
    !status.wifiReady || wifiGreen || ssid.trim() === "" || password === "" || busy === "wifi";

  const lastRecord = records.length > 0 ? records[records.length - 1] : null;
  const thrust = lastRecord?.F ?? 0;
  const temperature = lastRecord?.T ?? 0;

  const thrustOption = useMemo<EChartsOption>(
    () => ({
      tooltip: { trigger: "axis" },
      grid: { left: 64, right: 16, top: 24, bottom: 46, containLabel: true },
      xAxis: { type: "value", name: "t (s)", nameGap: 26, nameLocation: "middle" },
      yAxis: { type: "value", name: "F (kg)", nameGap: 44, nameLocation: "middle" },
      series: [
        {
          name: "F (kg)",
          type: "line",
          showSymbol: false,
          data: records.map((record) => [record.t, record.F]),
        },
      ],
    }),
    [records],
  );

  const temperatureOption = useMemo<EChartsOption>(
    () => ({
      tooltip: { trigger: "axis" },
      grid: { left: 64, right: 16, top: 24, bottom: 46, containLabel: true },
      xAxis: { type: "value", name: "t (s)", nameGap: 26, nameLocation: "middle" },
      yAxis: { type: "value", name: "T (K)", nameGap: 48, nameLocation: "middle" },
      series: [
        {
          name: "T (K)",
          type: "line",
          showSymbol: false,
          data: records.map((record) => [record.t, record.T]),
        },
      ],
    }),
    [records],
  );

  return (
    <div className={className} data-module="testbed" data-active={active ? "true" : "false"} style={moduleStyle}>
      {/* Run (T4-1) + conexión / WiFi / aborto (T4-2, T4-3, T4-5, T4-8, T4-9) */}
      <div style={topRowStyle}>
        <Card
          title="Testing Bed"
          actions={
            <Button variant="primary" loading={busy === "run"} onClick={() => void handleRun()}>
              Run
            </Button>
          }
        >
          <div style={metaGridStyle} data-testid="testbed-run-info">
            <span style={metaLabelStyle}>CSV</span>
            <span style={metaValueStyle}>{run?.testFile ?? "—"}</span>
            <span style={metaLabelStyle}>Nozzle</span>
            <span style={metaValueStyle}>{run?.nozzle ?? "—"}</span>
            <span style={metaLabelStyle}>Engine</span>
            <span style={metaValueStyle}>{run?.engine ?? "—"}</span>
            <span style={metaLabelStyle}>Max. thrust</span>
            <span style={metaValueStyle}>{formatMetric(run?.maxThrust)} kg</span>
            <span style={metaLabelStyle}>Max. temp</span>
            <span style={metaValueStyle}>{formatMetric(run?.maxTemp)} K</span>
          </div>
        </Card>

        <Card title="Conexión">
          <div style={optionsRowStyle}>
            <div style={{ minWidth: 220 }}>
              <Select
                label="Puerto de conexión USB"
                value={selectedPort}
                options={ports}
                onChange={setSelectedPort}
              />
            </div>
            <Button
              loading={busy === "connect"}
              disabled={connectDisabled}
              style={serialGreen ? greenButtonStyle : undefined}
              onClick={() => void handleConnect()}
            >
              Conectar
            </Button>
            <Button
              variant="danger"
              loading={busy === "disconnect"}
              disabled={!status.connected || busy === "disconnect"}
              onClick={() => void handleDisconnect()}
            >
              Desconectar
            </Button>
            <div style={{ minWidth: 150 }}>
              <TextField
                label="SSID"
                value={ssid}
                disabled={!status.wifiReady}
                onChange={setSsid}
                autoComplete="off"
              />
            </div>
            <div style={{ minWidth: 150 }}>
              <TextField
                label="Password"
                type="password"
                value={password}
                disabled={!status.wifiReady}
                onChange={setPassword}
                autoComplete="new-password"
                data-testid="wifi-password"
              />
            </div>
            <Button
              loading={busy === "wifi"}
              disabled={connectWifiDisabled}
              style={wifiGreen ? greenButtonStyle : undefined}
              onClick={() => void handleConnectWifi()}
            >
              Conectar WiFi
            </Button>
            <Button variant="danger" loading={busy === "abort"} onClick={() => void handleAbort()}>
              Abortar
            </Button>
            <Button
              variant="ghost"
              loading={busy === "demo"}
              aria-pressed={demoActive}
              onClick={() => void handleDemo()}
            >
              Demo (mock)
            </Button>
          </div>
        </Card>
      </div>

      {/* Monitor serie + checklist + estado (T4-3, T4-4, T4-6) */}
      <div style={middleRowStyle}>
        <Card title="Monitor serie">
          <Console
            lines={serialLines}
            height={340}
            autoScroll
            emptyMessage="Sin salida serie"
            onClear={() => setSerialLines([])}
          />
        </Card>

        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <Card
            title="TEST CHECKLIST"
            actions={recordingStarted ? (
              <span role="status" style={recordingBadgeStyle}>
                <span
                  aria-hidden="true"
                  style={{ width: 8, height: 8, borderRadius: "50%", background: "currentColor" }}
                />
                Recording started
              </span>
            ) : null}
          >
            {checklist.length === 0 ? (
              <p style={{ color: "var(--text-muted)", fontSize: "var(--font-size-sm)", margin: 0 }}>
                {checklistTitle}: sin items (no se encontró <code>checklist.json</code>).
              </p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {checklist.map((item, index) => (
                  <Checkbox
                    key={`${index}-${item.text}`}
                    checked={item.done}
                    disabled={!status.checklistEnabled}
                    label={item.text}
                    onChange={(checked) => void handleToggleChecklist(index, checked)}
                  />
                ))}
              </div>
            )}
          </Card>

          <Card title="Estado del banco">
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
                <LedIndicator kind="serial" color={status.leds.serial} />
                <LedIndicator kind="wifi" color={status.leds.wifi} />
              </div>
              <div style={metaGridStyle} data-testid="testbed-status">
                <span style={metaLabelStyle}>Conexión</span>
                <span>{status.connected ? "Conectado" : "Desconectado"}</span>
                <span style={metaLabelStyle}>WiFi</span>
                <span>{status.wifiReady ? "Listo" : "No listo"}</span>
                <span style={metaLabelStyle}>Grabación</span>
                <span>{status.recording ? "Grabando" : "Detenida"}</span>
                <span style={metaLabelStyle}>Checklist</span>
                <span>
                  {status.checklistEnabled ? "Habilitada" : "Deshabilitada"}
                  {status.checklistComplete ? " · completa" : ""}
                </span>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Datos en vivo (T4-7) */}
      <div style={twoColsStyle}>
        <Card title="Thrust">
          {CANVAS_2D_AVAILABLE ? (
            <LineChart option={thrustOption} height={240} ariaLabel="Empuje frente al tiempo" />
          ) : (
            <ChartFallback />
          )}
        </Card>
        <Card title="Temperature">
          {CANVAS_2D_AVAILABLE ? (
            <LineChart option={temperatureOption} height={240} ariaLabel="Temperatura frente al tiempo" />
          ) : (
            <ChartFallback />
          )}
        </Card>
      </div>

      <Card title="Instrumentación (último registro)">
        <div style={gaugesStyle}>
          <Gauge value={thrust} max={run?.maxThrust ?? 0} label="THRUST" unit="kg" size={170} />
          <Gauge
            value={temperature}
            max={run?.maxTemp ?? 0}
            label="TEMPERATURE"
            unit="K"
            size={170}
          />
          <Gauge value={1} max={1} label="BATTERY" unit="%" size={170} />
          <Gauge value={1} max={1} label="WATER" unit="%" size={170} />
        </div>
      </Card>

      <Card
        title="Registros en vivo"
        actions={
          <span style={{ fontSize: "var(--font-size-sm)", color: "var(--text-muted)" }}>
            {records.length} registros
          </span>
        }
      >
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "4px 16px",
            marginBottom: 8,
            fontSize: "var(--font-size-sm)",
            color: "var(--text-muted)",
          }}
        >
          <span>
            Registros: <strong>{records.length}</strong>
          </span>
          <span>
            Filas CSV: <strong>{records.length + 1}</strong>
          </span>
          <span style={{ wordBreak: "break-all" }}>CSV: {run?.testFile ?? "—"}</span>
        </div>
        <Table
          columns={recordColumns}
          rows={records}
          rowKey={(_row, index) => index}
          height={220}
          emptyMessage="Sin registros todavía"
        />
      </Card>
    </div>
  );
}

export default TestbedTab;
