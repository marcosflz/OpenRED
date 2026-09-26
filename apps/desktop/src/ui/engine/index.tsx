import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { isCancel, toRpcError } from "../../api/engine";
import type { EngineCalculateResult, PluginEntry, PropellantRow } from "../../api/types";
import { onExportRequested } from "../../app/bus";
import { useWorkspace } from "../../app/WorkspaceProvider";
import {
  Button,
  Card,
  Console,
  FigureView,
  Modal,
  NumberField,
  ProgressDialog,
  Select,
  SplitPane,
  Tabs,
  TextField,
  useToast,
  type ConsoleLine,
  type TabItem,
} from "../../components";
import type { TabModuleProps } from "../types";
import * as engineApi from "./api";
import {
  COMMON_FIELDS,
  DEFAULT_COMMON,
  TAB_KEY,
  buildSpec,
  cleanPropellantName,
  ensureGrainValues,
  findPropellant,
  grainConfigPatch,
  parseTab1,
  propellantLabel,
  resolvePropellant,
  toPropellantData,
  type CommonKey,
  type CommonValues,
  type GrainValues,
} from "./helpers";
import { DataView, GraphsView } from "./views";

export interface EngineTabProps extends TabModuleProps {}

const PRE_TABS: TabItem[] = [
  { id: "GEOMETRY", label: "GEOMETRY" },
  { id: "CONSOLE", label: "CONSOLE" },
  { id: "REGRESSION", label: "REGRESSION" },
];

const OUT_TABS: TabItem[] = [
  { id: "GRAPHS", label: "GRAPHS" },
  { id: "DATA", label: "DATA" },
];

const STACK_STYLE = { display: "grid", gap: 10 } as const;

/**
 * Pestaña T1 (Engine Design, `front_propDes.py`): selectores de propelente y
 * geometría, entradas dinámicas por grano, geometría PNG (`engine.geometry`),
 * cálculo cancelable con consola (`engine.calculate`), métricas/tabla y
 * exportación JSON (`engine.save`, evento `openred:export`).
 */
export function EngineTab({ active, className }: EngineTabProps) {
  const toast = useToast();
  const { workdir, config, setTabConfig } = useWorkspace();

  const [propellants, setPropellants] = useState<PropellantRow[]>([]);
  const [plugins, setPlugins] = useState<Record<string, PluginEntry>>({});
  const [propellant, setPropellant] = useState("");
  const [grain, setGrain] = useState("");
  const [common, setCommon] = useState<CommonValues>(DEFAULT_COMMON);
  const [grainValues, setGrainValues] = useState<GrainValues>({});
  const [preTab, setPreTab] = useState("GEOMETRY");
  const [outTab, setOutTab] = useState("GRAPHS");
  const [geometryPng, setGeometryPng] = useState<string | null>(null);
  const [geometryLoading, setGeometryLoading] = useState(false);
  const [consoleLines, setConsoleLines] = useState<ConsoleLine[]>([]);
  const [result, setResult] = useState<EngineCalculateResult | null>(null);
  const [progress, setProgress] = useState(0);
  const [progressLabel, setProgressLabel] = useState<string | undefined>(undefined);
  const [progressOpen, setProgressOpen] = useState(false);
  const [requestId, setRequestId] = useState<number | null>(null);
  const [exportOpen, setExportOpen] = useState(false);
  const [exportName, setExportName] = useState("");
  const [exporting, setExporting] = useState(false);

  const calculatingRef = useRef(false);
  const geometrySeqRef = useRef(0);
  const propellantRef = useRef("");

  /** Muestra `RpcError` como toast; 1005 (cancelado) es silencioso. */
  const report = useCallback(
    (error: unknown, title: string) => {
      const rpc = toRpcError(error);
      if (isCancel(rpc)) return;
      toast.error({ title, message: rpc.message });
    },
    [toast],
  );

  /* ---------------------------------------------------------------- */
  /* Carga de datos (T1-1)                                             */
  /* ---------------------------------------------------------------- */

  const refreshPropellants = useCallback(async () => {
    try {
      const rows = await engineApi.listPropellants();
      setPropellants(rows);
      const resolved = resolvePropellant(propellantRef.current, rows);
      if (resolved !== propellantRef.current) {
        propellantRef.current = resolved;
        setPropellant(resolved);
        if (resolved) setTabConfig(TAB_KEY, { propellant: resolved });
      }
    } catch (error) {
      report(error, "Propellants");
    }
  }, [report, setTabConfig]);

  const refreshGrains = useCallback(async () => {
    try {
      setPlugins(await engineApi.listGrainPlugins());
    } catch (error) {
      report(error, "Grain library");
    }
  }, [report]);

  // Refresco al abrir la pestaña (y de nuevo cuando el selector recibe foco).
  useEffect(() => {
    if (active === false) return;
    void refreshPropellants();
    void refreshGrains();
  }, [active, refreshPropellants, refreshGrains]);

  /* ---------------------------------------------------------------- */
  /* Persistencia en config.tabs.tab_1 (T1-9)                          */
  /* ---------------------------------------------------------------- */

  const tab1 = (config.tabs?.tab_1 ?? undefined) as Record<string, unknown> | undefined;

  useEffect(() => {
    const names = Object.keys(plugins);
    const parsed = parseTab1(tab1, names);
    if (parsed.propellant) {
      // `config.json` guarda `Nombre (id)`; si viene un nombre sin id (o el
      // id cambió) se resuelve contra la lista actual y se normaliza.
      const resolved =
        propellants.length > 0
          ? resolvePropellant(parsed.propellant, propellants)
          : parsed.propellant;
      propellantRef.current = resolved;
      setPropellant(resolved);
      if (resolved !== parsed.propellant) setTabConfig(TAB_KEY, { propellant: resolved });
    }
    if (parsed.geoConfig && names.includes(parsed.geoConfig)) setGrain(parsed.geoConfig);
    if (Object.keys(parsed.common).length > 0) {
      setCommon((prev) => ({ ...prev, ...parsed.common }));
    }
    if (Object.keys(parsed.grainValues).length > 0) {
      setGrainValues((prev) => {
        const next: GrainValues = { ...prev };
        for (const [name, values] of Object.entries(parsed.grainValues)) {
          next[name] = { ...(next[name] ?? {}), ...values };
        }
        return next;
      });
    }
  }, [tab1, plugins, propellants, setTabConfig]);

  useEffect(() => {
    const names = Object.keys(plugins);
    if (names.length === 0) return;
    setGrain((prev) => (prev && plugins[prev] ? prev : names[0]));
  }, [plugins]);

  const handlePropellantChange = useCallback(
    (value: string) => {
      propellantRef.current = value;
      setPropellant(value);
      setTabConfig(TAB_KEY, { propellant: value });
    },
    [setTabConfig],
  );

  const handleCommonChange = useCallback(
    (key: CommonKey, value: string) => {
      setCommon((prev) => ({ ...prev, [key]: value }));
      setTabConfig(TAB_KEY, { [key]: value });
    },
    [setTabConfig],
  );

  /* ---------------------------------------------------------------- */
  /* Geometría (T1-2)                                                  */
  /* ---------------------------------------------------------------- */

  const requestGeometry = useCallback(
    (params: {
      grain: string;
      propellant: string;
      common: CommonValues;
      grainValues: GrainValues;
      switchTab?: boolean;
    }) => {
      const entry = plugins[params.grain];
      if (!entry || !params.propellant) return;
      const spec = buildSpec(
        params.common,
        params.grainValues[params.grain],
        Object.values(entry.labels ?? {}),
      );
      const seq = ++geometrySeqRef.current;
      setGeometryLoading(true);
      engineApi
        .fetchGeometry({
          propellant: cleanPropellantName(params.propellant),
          grain: params.grain,
          spec,
        })
        .then((response) => {
          if (seq !== geometrySeqRef.current) return;
          setGeometryPng(response.png_b64);
          if (params.switchTab) setPreTab("GEOMETRY");
        })
        .catch((error: unknown) => {
          if (seq !== geometrySeqRef.current) return;
          report(error, "Geometry");
        })
        .finally(() => {
          if (seq === geometrySeqRef.current) setGeometryLoading(false);
        });
    },
    [plugins, report],
  );

  const handleFieldBlur = useCallback(() => {
    requestGeometry({ grain, propellant, common, grainValues, switchTab: true });
  }, [requestGeometry, grain, propellant, common, grainValues]);

  const handleGrainChange = useCallback(
    (next: string) => {
      const merged = ensureGrainValues(grainValues, plugins);
      setGrain(next);
      setGrainValues(merged);
      setTabConfig(TAB_KEY, { geoConfig: next, ...grainConfigPatch(merged, plugins) });
      requestGeometry({ grain: next, propellant, common, grainValues: merged, switchTab: true });
    },
    [grainValues, plugins, setTabConfig, requestGeometry, propellant, common],
  );

  const handleGrainValueChange = useCallback(
    (key: string, value: string) => {
      setGrainValues((prev) => ({ ...prev, [grain]: { ...(prev[grain] ?? {}), [key]: value } }));
      setTabConfig(TAB_KEY, { [`${grain}_${key}`]: value });
    },
    [grain, setTabConfig],
  );

  /* ---------------------------------------------------------------- */
  /* Cálculo (T1-5, T1-6)                                              */
  /* ---------------------------------------------------------------- */

  const runCalculate = useCallback(async () => {
    const entry = plugins[grain];
    const row = findPropellant(propellants, propellant);
    if (!entry || !row) {
      toast.error({
        title: "Calculation",
        message: "Select a propellant and a grain geometry first.",
      });
      return;
    }
    const spec = buildSpec(common, grainValues[grain], Object.values(entry.labels ?? {}));
    setConsoleLines([]);
    setProgress(0);
    setProgressLabel(undefined);
    setRequestId(null);
    setProgressOpen(true);
    calculatingRef.current = true;
    try {
      const calculation = await engineApi.calculateEngine({
        propellant: cleanPropellantName(propellant),
        grain,
        spec,
        propellantData: toPropellantData(row),
      });
      setResult(calculation);
      setPreTab("REGRESSION");
    } catch (error) {
      report(error, "Calculation");
    } finally {
      calculatingRef.current = false;
      setProgressOpen(false);
      setRequestId(null);
    }
  }, [plugins, grain, propellants, propellant, common, grainValues, report, toast]);

  /* ---------------------------------------------------------------- */
  /* Eventos del motor (T1-4) y export (T1-7/T1-10)                    */
  /* ---------------------------------------------------------------- */

  useEffect(() => {
    const unlisteners: Array<() => void> = [];
    let disposed = false;
    const add = (pending: Promise<() => void>) => {
      void pending.then((unlisten) => {
        if (disposed) unlisten();
        else unlisteners.push(unlisten);
      });
    };
    add(
      engineApi.onConsole((event) => {
        if (event.job !== "engine.calculate") return;
        setConsoleLines((prev) => [...prev, { text: event.line }]);
      }),
    );
    add(
      engineApi.onProgress((event) => {
        if (event.job !== "engine.calculate") return;
        setProgress(Math.min(1, Math.max(0, event.value)));
        setProgressLabel(event.label);
      }),
    );
    add(
      engineApi.onEngineRequest((event) => {
        if (calculatingRef.current && event.method === "engine.calculate" && event.phase === "start") {
          setRequestId(event.id);
        }
      }),
    );
    return () => {
      disposed = true;
      for (const unlisten of unlisteners) unlisten();
    };
  }, []);

  const openExport = useCallback(() => {
    if (!workdir) {
      toast.error({ title: "Export results", message: "No working directory has been selected." });
      return;
    }
    if (!result) {
      toast.warning({
        title: "Export results",
        message: "There are no results to export. Run a calculation first.",
      });
      return;
    }
    setExportName(`${cleanPropellantName(propellant) || "engine"}-${grain || "engine"}`);
    setExportOpen(true);
  }, [workdir, result, toast, propellant, grain]);

  useEffect(() => {
    if (active === false) return;
    return onExportRequested(() => openExport());
  }, [active, openExport]);

  const confirmExport = useCallback(async () => {
    if (!result) return;
    const name = exportName.trim();
    if (!name) return;
    setExporting(true);
    try {
      const path = await engineApi.saveEngine(name, result.payload);
      setExportOpen(false);
      toast.success({ title: "Results exported", message: path });
    } catch (error) {
      report(error, "Export");
    } finally {
      setExporting(false);
    }
  }, [result, exportName, report, toast]);

  /* ---------------------------------------------------------------- */
  /* Render                                                            */
  /* ---------------------------------------------------------------- */

  const propellantOptions = useMemo(
    () => propellants.map((row) => propellantLabel(row)),
    [propellants],
  );
  const grainOptions = useMemo(() => Object.keys(plugins), [plugins]);
  const grainLabels = useMemo(
    () => Object.entries(plugins[grain]?.labels ?? {}),
    [plugins, grain],
  );

  return (
    <div
      className={className}
      data-module="engine"
      style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: 0 }}
    >
      <SplitPane direction="horizontal" initialSize={470} minSize={340}>
        <Card title="Engine Design" style={{ marginBottom: 0 }}>
          <div style={STACK_STYLE}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <Select
                label="Propellant"
                value={propellant}
                options={propellantOptions}
                onChange={handlePropellantChange}
                onFocus={() => void refreshPropellants()}
                placeholder="Selecciona…"
                data-testid="propellant-select"
              />
              <Select
                label="Grain Geometry"
                value={grain}
                options={grainOptions}
                onChange={handleGrainChange}
                onFocus={() => void refreshGrains()}
                placeholder="Selecciona…"
                data-testid="grain-select"
              />
            </div>

            <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: 0 }} />

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              {COMMON_FIELDS.map((field) => (
                <NumberField
                  key={field.key}
                  label={field.label}
                  value={common[field.key]}
                  onChange={(value) => handleCommonChange(field.key, value)}
                  onBlur={handleFieldBlur}
                  data-testid={`common-${field.key}`}
                />
              ))}
            </div>

            {grainLabels.length > 0 ? (
              <>
                <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: 0 }} />
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                  {grainLabels.map(([label, key]) => (
                    <NumberField
                      key={key}
                      label={label}
                      value={grainValues[grain]?.[key] ?? "0"}
                      onChange={(value) => handleGrainValueChange(key, value)}
                      onBlur={handleFieldBlur}
                      data-testid={`grain-field-${grain}-${key}`}
                    />
                  ))}
                </div>
              </>
            ) : null}

            <Tabs items={PRE_TABS} value={preTab} onChange={setPreTab} ariaLabel="Engine pre-run" />

            {preTab === "GEOMETRY" ? (
              <FigureView
                png={geometryPng}
                loading={geometryLoading}
                alt="Grain geometry"
                height={340}
              />
            ) : null}

            {preTab === "CONSOLE" ? (
              <div style={{ display: "grid", gap: 10 }}>
                <Console
                  lines={consoleLines}
                  title="Console"
                  height={200}
                  onClear={() => setConsoleLines([])}
                />
                <div style={{ display: "flex", gap: 10 }}>
                  <Button variant="secondary" block onClick={openExport}>
                    EXPORT
                  </Button>
                  <Button
                    variant="primary"
                    block
                    loading={progressOpen}
                    onClick={() => void runCalculate()}
                  >
                    CALCULATE
                  </Button>
                </div>
              </div>
            ) : null}

            {preTab === "REGRESSION" ? (
              <FigureView png={result?.figures.regression} alt="Regression" height={340} />
            ) : null}
          </div>
        </Card>

        <Card title="Results" style={{ marginBottom: 0 }}>
          <Tabs items={OUT_TABS} value={outTab} onChange={setOutTab} ariaLabel="Engine results" />
          {outTab === "DATA" ? <DataView result={result} dt={common.dt} /> : <GraphsView result={result} />}
        </Card>
      </SplitPane>

      <ProgressDialog
        open={progressOpen}
        title="Calculating…"
        label={progressLabel ?? "engine.calculate"}
        value={progress}
        requestId={requestId}
        onClose={() => setProgressOpen(false)}
      />

      <Modal
        open={exportOpen}
        onClose={() => setExportOpen(false)}
        title="Export results"
        width={440}
        footer={
          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", width: "100%" }}>
            <Button variant="ghost" onClick={() => setExportOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              loading={exporting}
              disabled={exportName.trim() === ""}
              onClick={() => void confirmExport()}
            >
              Save
            </Button>
          </div>
        }
      >
        <TextField
          label="File name"
          value={exportName}
          onChange={setExportName}
          placeholder="KNSU-Tubular-Grain"
          hint={workdir ? `Se guardará en ${workdir}\\Engines` : undefined}
          data-testid="export-name"
          onKeyDown={(event) => {
            if (event.key === "Enter") void confirmExport();
          }}
        />
      </Modal>
    </div>
  );
}

export default EngineTab;
