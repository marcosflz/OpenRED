/**
 * T2 — Nozzle Design (`front_modules/front_nozDes.py`).
 *
 * Implementa la pestaña completa sobre el contrato `nozzle.*`:
 * carga del motor (T2-1), P1 medio/slider/entrada (T2-2), tipos de tobera e
 * inputs dinámicos (T2-3), perfil de presión (T2-4), CALCULATE cancelable con
 * `ProgressDialog` (T2-5), resultados (T2-6), off-design en vivo con debounce
 * (T2-7), tablas (T2-8), figuras (T2-9) y persistencia `tab_2` (T2-10).
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { listen, type UnlistenFn } from "@tauri-apps/api/event";
import {
  isCancel,
  isTauri,
  onEngineEventOf,
  pickFile,
  request,
  toRpcError,
  type FileFilter,
  type NozzleCalculateResult,
  type NozzleOpPointResult,
  type PluginsListResult,
} from "../../api/engine";
import {
  Button,
  Card,
  Checkbox,
  LineChart,
  Modal,
  NumberField,
  ProgressDialog,
  Select,
  Slider,
  Tabs,
  TextField,
  useToast,
  type EChartsTheme,
} from "../../components";
import { onExportRequested } from "../../app/bus";
import { useWorkspace, type TabPatch } from "../../app/WorkspaceProvider";
import { useOptionalTheme } from "../../theme";
import { cx } from "../../utils/cx";
import {
  getEntryValue,
  normalizeNumericInput,
  parseNumeric,
  validateScientificNotation,
} from "../../utils/numbers";
import type { TabModuleProps } from "../types";
import { machMapOption, pressureMapOption, pressureProfileOption } from "./charts";
import { average, clamp, extent, formatPressure } from "./format";
import { OffDesignPanel } from "./offdesign";
import { FiguresPanel, NozzleTables, ResultsPanel } from "./results";
import {
  engineInputNumber,
  fileNameOf,
  INVALID_ENGINE_LABEL,
  NO_ENGINE_LABEL,
  specConfigKey,
  specKeys,
  withinRange,
  type LoadedEngine,
  type NozzlePlugins,
} from "./types";

export interface NozzleTabProps extends TabModuleProps {}

interface ProgressState {
  open: boolean;
  value: number;
  label: string;
  requestId: number | null;
}

interface EngineRequestEvent {
  id: number;
  method: string;
  phase: string;
}

const EMPTY_TAB: Record<string, unknown> = {};
const EMPTY_PROGRESS: ProgressState = { open: false, value: 0, label: "", requestId: null };
const FILTERS: FileFilter[] = [{ name: "JSON files", extensions: ["json"] }];

/** `true` si el texto es un número válido no vacío (paridad `float(entry.get())`). */
function isValidNumber(raw: string | undefined): boolean {
  const text = normalizeNumericInput((raw ?? "").trim());
  return text !== "" && validateScientificNotation(text);
}

/** Suscripción a `engine-request` (id de la petición en vuelo para cancelar). */
async function onEngineRequest(
  handler: (event: EngineRequestEvent) => void,
): Promise<UnlistenFn> {
  if (!isTauri()) return () => {};
  return listen<EngineRequestEvent>("engine-request", (event) => handler(event.payload));
}

/**
 * Diálogo de selección del JSON de motor.
 *
 * `pickFile` envía `filters: FileFilter[]`, pero el comando Rust `pick_file`
 * espera una lista de extensiones (`string[]`); si el comando rechaza los
 * argumentos se reintenta sin filtro para no dejar el botón LOAD inservible
 * (desviación documentada en el informe de A6).
 */
async function chooseEngineFile(): Promise<string | null> {
  try {
    return await pickFile(FILTERS);
  } catch (error) {
    const rpc = toRpcError(error);
    if (isCancel(rpc)) return null;
    return pickFile();
  }
}

export function NozzleTab({ active = true, className }: NozzleTabProps) {
  const toast = useToast();
  const { workdir, config, setTabConfig } = useWorkspace();
  const theme = useOptionalTheme();
  const chartMode: EChartsTheme = theme?.mode === "light" ? "light" : "dark";

  /* ------------------------------ estado ------------------------------ */

  const [plugins, setPlugins] = useState<NozzlePlugins | null>(null);
  const [nozzleType, setNozzleType] = useState("");
  const [specValues, setSpecValues] = useState<Record<string, string>>({});
  const [engine, setEngine] = useState<LoadedEngine | null>(null);
  const [engineLabel, setEngineLabel] = useState<string>(NO_ENGINE_LABEL);
  const [loadingEngine, setLoadingEngine] = useState(false);
  const [meanSwitch, setMeanSwitch] = useState(false);
  const [p1Text, setP1Text] = useState("0");
  const [sliderValue, setSliderValue] = useState(0);
  const [nRes, setNRes] = useState("50");
  const [dt, setDt] = useState("0.01");
  const [result, setResult] = useState<NozzleCalculateResult | null>(null);
  const [progress, setProgress] = useState<ProgressState>(EMPTY_PROGRESS);
  const [op, setOp] = useState<NozzleOpPointResult | null>(null);
  const [opError, setOpError] = useState<string | null>(null);
  const [p1tPercent, setP1tPercent] = useState(1);
  const [p0Percent, setP0Percent] = useState(1);
  const [resultsTab, setResultsTab] = useState("nozzle");
  const [exportOpen, setExportOpen] = useState(false);
  const [exportName, setExportName] = useState("");
  const [saving, setSaving] = useState(false);

  const jobRef = useRef(0);
  const opSeqRef = useRef(0);
  const lastOpErrorRef = useRef<string | null>(null);
  const progressOpenRef = useRef(false);
  const autoLoadRef = useRef<string | null>(null);
  /** Último valor aplicado de cada clave de `tab_2` (evita re-hidratar). */
  const appliedRef = useRef<Record<string, unknown>>({});
  /** Estado guardado en `config.json`, aplicado al cargar un motor. */
  const savedSwitchRef = useRef<boolean | null>(null);
  const savedP1Ref = useRef<string | null>(null);

  const tab2 = useMemo<Record<string, unknown>>(() => {
    const value = config.tabs?.tab_2;
    return value && typeof value === "object" ? (value as Record<string, unknown>) : EMPTY_TAB;
  }, [config.tabs]);

  const persist = useCallback(
    (patch: TabPatch) => {
      for (const [key, value] of Object.entries(patch)) appliedRef.current[key] = value;
      if ("SwitchState" in patch) {
        savedSwitchRef.current =
          patch.SwitchState === 1 || patch.SwitchState === "1" || patch.SwitchState === true;
      }
      if ("P1" in patch) {
        savedP1Ref.current =
          patch.P1 === undefined || patch.P1 === null ? null : String(patch.P1);
      }
      setTabConfig("tab_2", patch);
    },
    [setTabConfig],
  );

  /* --------------------------- plugins.list --------------------------- */

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const response = await request<PluginsListResult>("plugins.list", {
          library: "NozzleLibrary",
        });
        if (!cancelled) setPlugins(response.plugins ?? {});
      } catch (error) {
        if (cancelled) return;
        const rpc = toRpcError(error);
        if (!isCancel(rpc)) toast.error({ title: "Tipos de tobera", message: rpc.message });
        setPlugins({});
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [toast]);

  /* ------------------- progreso (event/progress) ---------------------- */

  useEffect(() => {
    progressOpenRef.current = progress.open;
  }, [progress.open]);

  useEffect(() => {
    let unlisten: UnlistenFn | null = null;
    void onEngineEventOf("progress", (event) => {
      if (!progressOpenRef.current || event.job !== "nozzle.calculate") return;
      const value = Math.min(Math.max(event.value ?? 0, 0), 1);
      setProgress((current) => ({
        ...current,
        value,
        label: event.label ?? `${Math.round(value * 100)}%`,
      }));
    }).then((fn) => {
      unlisten = fn;
    });
    return () => {
      unlisten?.();
    };
  }, []);

  /* -------------------- hidratación de config tab_2 ------------------- */

  useEffect(() => {
    const apply = (key: string, value: unknown): boolean => {
      if (value === undefined || value === appliedRef.current[key]) return false;
      appliedRef.current[key] = value;
      return true;
    };

    if (apply("SwitchState", tab2.SwitchState)) {
      const mean =
        tab2.SwitchState === 1 || tab2.SwitchState === "1" || tab2.SwitchState === true;
      savedSwitchRef.current = mean;
      setMeanSwitch(mean);
    }
    if (apply("P1", tab2.P1) && (typeof tab2.P1 === "string" || typeof tab2.P1 === "number")) {
      const text = String(tab2.P1);
      savedP1Ref.current = text;
      setP1Text(text);
      const numeric = Number(text);
      if (Number.isFinite(numeric)) setSliderValue(numeric);
    }
    if (
      apply("engine_config", tab2.engine_config) &&
      typeof tab2.engine_config === "string"
    ) {
      setEngineLabel(tab2.engine_config);
    }
    if (apply("n_res", tab2.n_res) && (typeof tab2.n_res === "string" || typeof tab2.n_res === "number")) {
      setNRes(String(tab2.n_res));
    }

    if (!plugins) return;
    const savedType = typeof tab2.nozzle_type === "string" ? tab2.nozzle_type : "";
    const nextType = savedType && plugins[savedType] ? savedType : (Object.keys(plugins)[0] ?? "");
    if (nextType && apply("nozzle_type", nextType)) {
      setNozzleType(nextType);
    }
    const hydrated: Record<string, string> = {};
    for (const type of Object.keys(plugins)) {
      for (const key of specKeys(plugins[type])) {
        const configKey = specConfigKey(type, key);
        const value = tab2[configKey];
        if ((typeof value === "string" || typeof value === "number") && apply(configKey, value)) {
          hydrated[configKey] = String(value);
        }
      }
    }
    if (Object.keys(hydrated).length > 0) {
      setSpecValues((current) => ({ ...current, ...hydrated }));
    }
  }, [plugins, tab2]);

  /* ------------------------- carga del motor -------------------------- */

  const meanPressure = useMemo(() => {
    if (!engine) return 0;
    const declared = engine.meanPressure;
    if (typeof declared === "number" && Number.isFinite(declared) && declared > 0) return declared;
    const computed = average(engine.p_curve.P);
    if (computed > 0) return computed;
    return (engine.p1_min + engine.p1_max) / 2;
  }, [engine]);

  const applyMeanPressure = useCallback(
    (payload: LoadedEngine) => {
      const declared = payload.meanPressure;
      const computed = average(payload.p_curve.P);
      const mean =
        typeof declared === "number" && Number.isFinite(declared) && declared > 0
          ? declared
          : computed > 0
            ? computed
            : (payload.p1_min + payload.p1_max) / 2;
      const text = String(mean);
      setMeanSwitch(true);
      setP1Text(text);
      setSliderValue(clamp(mean, payload.p1_min, payload.p1_max));
      persist({ SwitchState: 1, P1: text });
    },
    [persist],
  );

  const loadEngine = useCallback(
    async (path: string): Promise<void> => {
      setLoadingEngine(true);
      try {
        const payload = await request<LoadedEngine>("nozzle.load_engine", { path });
        const name = fileNameOf(path);
        setEngine(payload);
        setEngineLabel(name);
        setResult(null);
        setOp(null);
        setOpError(null);
        persist({ engine_config: name });
        const savedP1 = savedP1Ref.current;
        if (savedSwitchRef.current === false && savedP1 !== null && isValidNumber(savedP1)) {
          const text = String(Number(savedP1));
          setMeanSwitch(false);
          setP1Text(text);
          setSliderValue(clamp(Number(text), payload.p1_min, payload.p1_max));
          persist({ SwitchState: 0, P1: text });
        } else {
          applyMeanPressure(payload);
        }
        toast.success({ title: "Motor cargado", message: name });
      } catch (error) {
        const rpc = toRpcError(error);
        if (isCancel(rpc)) return;
        if (rpc.code === 1003) {
          setEngine(null);
          setEngineLabel(INVALID_ENGINE_LABEL);
          persist({ engine_config: INVALID_ENGINE_LABEL });
          toast.error({ title: "Nozzle Design", message: "Invalid file." });
          return;
        }
        toast.error({ title: "Nozzle Design", message: rpc.message });
      } finally {
        setLoadingEngine(false);
      }
    },
    [applyMeanPressure, persist, toast],
  );

  const handleLoadEngine = useCallback(async () => {
    try {
      const path = await chooseEngineFile();
      if (!path) return;
      await loadEngine(path);
    } catch (error) {
      const rpc = toRpcError(error);
      if (!isCancel(rpc)) toast.error({ title: "Nozzle Design", message: rpc.message });
    }
  }, [loadEngine, toast]);

  // Auto-carga del motor guardado en `tab_2` (paridad `app.load_configuration`).
  useEffect(() => {
    const name = typeof tab2.engine_config === "string" ? tab2.engine_config : "";
    if (!workdir || !name || name === NO_ENGINE_LABEL || name === INVALID_ENGINE_LABEL) return;
    if (engine || autoLoadRef.current === name) return;
    autoLoadRef.current = name;
    void loadEngine(name);
  }, [engine, loadEngine, tab2.engine_config, workdir]);

  /* ------------------------- valores derivados ------------------------ */

  const p1Min = engine?.p1_min ?? 0;
  const p1Max = engine?.p1_max ?? 0;
  const engineP0 = engine ? engineInputNumber(engine.inputs, "P0") : Number.NaN;
  const [p1tMin, p1tMax] = useMemo(() => extent(engine?.p_curve.P ?? []), [engine]);
  const p1Value = meanSwitch ? meanPressure : parseNumeric(p1Text);

  const plugin = nozzleType ? plugins?.[nozzleType] : undefined;
  const activeSpecKeys = useMemo(() => specKeys(plugin), [plugin]);
  const specValid = useMemo(
    () =>
      activeSpecKeys.every((key) => isValidNumber(specValues[specConfigKey(nozzleType, key)])),
    [activeSpecKeys, nozzleType, specValues],
  );
  const specPayload = useMemo<Record<string, number>>(() => {
    const values: Record<string, number> = {};
    for (const key of activeSpecKeys) {
      values[key] = parseNumeric(specValues[specConfigKey(nozzleType, key)]);
    }
    return values;
  }, [activeSpecKeys, nozzleType, specValues]);

  const p1tValue = useMemo(() => {
    if (!engine) return 0;
    return p1tMin + p1tPercent * (p1tMax - p1tMin);
  }, [engine, p1tMax, p1tMin, p1tPercent]);
  const p0Value = useMemo(
    () => (Number.isFinite(engineP0) ? p0Percent * engineP0 : 0),
    [engineP0, p0Percent],
  );

  const profileOption = useMemo(
    () =>
      pressureProfileOption(
        chartMode,
        engine?.p_curve ?? { t: [], P: [] },
        p1Value,
      ),
    [chartMode, engine, p1Value],
  );
  const machOption = useMemo(
    () =>
      machMapOption(
        chartMode,
        op?.curves ?? { x: [], mach: [], pr: [] },
        op?.regime ?? null,
      ),
    [chartMode, op],
  );
  const presOption = useMemo(
    () =>
      pressureMapOption(
        chartMode,
        op?.curves ?? { x: [], mach: [], pr: [] },
        typeof op?.ratios?.pe_p1 === "number" ? op.ratios.pe_p1 : null,
      ),
    [chartMode, op],
  );

  const prCrit = useMemo<Record<string, number> | null>(() => {
    if (!result) return null;
    return {
      PR_Crit0: Number(result.calculatedResults.PR_Crit0),
      PR_Crit1: Number(result.calculatedResults.PR_Crit1),
      PR_Crit2: Number(result.calculatedResults.PR_Crit2),
      PR_Crit3: Number(result.calculatedResults.PR_Crit3),
    };
  }, [result]);

  /* --------------------------- off-design ----------------------------- */

  const runOpPoint = useCallback(
    async (p1t: number, p0: number, n: number) => {
      if (!engine || !nozzleType) return;
      const seq = opSeqRef.current + 1;
      opSeqRef.current = seq;
      try {
        const response = await request<NozzleOpPointResult>("nozzle.op_point", {
          engine,
          nozzleType,
          p1t,
          p0,
          p1: p1Value,
          n,
          dt: parseNumeric(dt),
          defCheck: meanSwitch,
          spec: specPayload,
        });
        if (seq !== opSeqRef.current) return;
        setOp(response);
        setOpError(null);
        lastOpErrorRef.current = null;
      } catch (error) {
        if (seq !== opSeqRef.current) return;
        const rpc = toRpcError(error);
        if (isCancel(rpc)) return;
        setOpError(rpc.message);
        if (lastOpErrorRef.current !== rpc.message) {
          lastOpErrorRef.current = rpc.message;
          toast.error({ title: "Off-design", message: rpc.message });
        }
      }
    },
    [dt, engine, meanSwitch, nozzleType, p1Value, specPayload, toast],
  );

  // Debounce de 100 ms (T2-7).
  useEffect(() => {
    if (!active || !engine || !nozzleType || !specValid) return;
    const n = parseNumeric(nRes);
    if (!Number.isFinite(n) || n < 2) return;
    const p1t = p1tMin + p1tPercent * (p1tMax - p1tMin);
    const p0 = Number.isFinite(engineP0) ? p0Percent * engineP0 : 0;
    if (!(p1t > 0) || !(p0 > 0)) return;
    const timer = window.setTimeout(() => {
      void runOpPoint(p1t, p0, Math.trunc(n));
    }, 100);
    return () => window.clearTimeout(timer);
  }, [
    active,
    engineP0,
    engine,
    meanSwitch,
    nRes,
    nozzleType,
    p0Percent,
    p1tMax,
    p1tMin,
    p1tPercent,
    result,
    runOpPoint,
    specValid,
  ]);

  /* --------------------------- CALCULATE ------------------------------ */

  const handleCancelCompute = useCallback(() => {
    jobRef.current += 1;
    setProgress(EMPTY_PROGRESS);
  }, []);

  const handleCalculate = useCallback(async () => {
    if (!engine) {
      toast.error({
        title: "Nozzle Design",
        message: "Carga un motor (LOAD) antes de calcular.",
      });
      return;
    }
    if (!nozzleType) {
      toast.error({ title: "Nozzle Design", message: "Selecciona un tipo de tobera." });
      return;
    }
    const p1Raw = getEntryValue(meanSwitch ? String(meanPressure) : p1Text);
    if (!Number.isFinite(Number(p1Raw)) || Number(p1Raw) <= 0) {
      toast.error({ title: "P1", message: "Please enter a valid number." });
      return;
    }
    const n = parseNumeric(nRes);
    if (!Number.isFinite(n) || n < 2) {
      toast.error({ title: "Points - Resolution", message: "Introduce un número de puntos ≥ 2." });
      return;
    }
    const dtValue = parseNumeric(dt);
    if (!Number.isFinite(dtValue) || dtValue < 0) {
      toast.error({ title: "Temp. Step (s)", message: "Introduce un paso de tiempo válido." });
      return;
    }
    if (!specValid) {
      toast.error({
        title: "Nozzle Design",
        message: "Por favor, introduce valores numéricos válidos.",
      });
      return;
    }

    const runId = jobRef.current + 1;
    jobRef.current = runId;
    setProgress({ open: true, value: 0, label: "0%", requestId: null });
    let unlisten: UnlistenFn | null = null;
    if (isTauri()) {
      unlisten = await onEngineRequest((event) => {
        if (event.method !== "nozzle.calculate" || event.phase !== "start") return;
        if (jobRef.current !== runId) return;
        setProgress((current) => ({ ...current, requestId: event.id }));
      });
    }
    try {
      const calculated = await request<NozzleCalculateResult>("nozzle.calculate", {
        engine,
        engineName: engineLabel,
        nozzleType,
        p1: Number(p1Raw),
        n: Math.trunc(n),
        dt: dtValue,
        defCheck: meanSwitch,
        spec: specPayload,
      });
      if (jobRef.current !== runId) return;
      setResult(calculated);
      setOp(null);
      toast.success({
        title: "Cálculo completado",
        message: `${nozzleType} · P1 = ${formatPressure(Number(p1Raw))} Pa`,
      });
    } catch (error) {
      if (jobRef.current !== runId) return;
      const rpc = toRpcError(error);
      if (!isCancel(rpc)) toast.error({ title: "Nozzle Design", message: rpc.message });
    } finally {
      unlisten?.();
      if (jobRef.current === runId) setProgress(EMPTY_PROGRESS);
    }
  }, [
    dt,
    engine,
    engineLabel,
    meanPressure,
    meanSwitch,
    nRes,
    nozzleType,
    p1Text,
    specPayload,
    specValid,
    toast,
  ]);

  /* ---------------------------- EXPORT -------------------------------- */

  const persistAll = useCallback(() => {
    const patch: TabPatch = {
      engine_config: engineLabel,
      SwitchState: meanSwitch ? 1 : 0,
      P1: getEntryValue(meanSwitch ? String(meanPressure) : p1Text),
      n_res: getEntryValue(nRes),
      nozzle_type: nozzleType,
    };
    if (plugins) {
      for (const type of Object.keys(plugins)) {
        for (const key of specKeys(plugins[type])) {
          const configKey = specConfigKey(type, key);
          patch[configKey] = getEntryValue(specValues[configKey]);
        }
      }
    }
    persist(patch);
  }, [engineLabel, meanPressure, meanSwitch, nRes, nozzleType, p1Text, persist, plugins, specValues]);

  const openExport = useCallback(() => {
    if (!result) {
      toast.error({ title: "Export", message: "Realiza primero un cálculo (CALCULATE)." });
      return;
    }
    const base = engineLabel.endsWith(".json")
      ? engineLabel.slice(0, -".json".length)
      : fileNameOf(engineLabel);
    setExportName(`${base || "nozzle"}-${nozzleType || "nozzle"}`);
    setExportOpen(true);
  }, [engineLabel, nozzleType, result, toast]);

  const handleExport = useCallback(async () => {
    if (!result) return;
    const name = exportName.trim();
    if (!name) {
      toast.error({ title: "Export", message: "Introduce un nombre de fichero." });
      return;
    }
    setSaving(true);
    try {
      const response = await request<{ path: string }>("nozzle.save", {
        name,
        payload: result.payload,
      });
      persistAll();
      setExportOpen(false);
      toast.success({ title: "Tobera exportada", message: response.path });
    } catch (error) {
      const rpc = toRpcError(error);
      if (!isCancel(rpc)) toast.error({ title: "Export", message: rpc.message });
    } finally {
      setSaving(false);
    }
  }, [exportName, persistAll, result, toast]);

  const exportRequestRef = useRef(openExport);
  useEffect(() => {
    exportRequestRef.current = openExport;
  }, [openExport]);
  useEffect(() => {
    if (!active) return;
    return onExportRequested(() => exportRequestRef.current());
  }, [active]);

  /* ---------------------------- handlers ------------------------------ */

  const handleTypeChange = useCallback(
    (value: string) => {
      setNozzleType(value);
      setOp(null);
      setOpError(null);
      persist({ nozzle_type: value });
    },
    [persist],
  );

  const handleSpecChange = useCallback(
    (key: string, value: string) => {
      const configKey = specConfigKey(nozzleType, key);
      setSpecValues((current) => ({ ...current, [configKey]: value }));
      persist({ [configKey]: value });
    },
    [nozzleType, persist],
  );

  const handleP1Slider = useCallback(
    (value: number) => {
      setSliderValue(value);
      const text = String(value);
      setP1Text(text);
      persist({ P1: text });
    },
    [persist],
  );

  const handleMeanToggle = useCallback(
    (checked: boolean) => {
      setMeanSwitch(checked);
      if (checked) {
        const text = String(meanPressure);
        setP1Text(text);
        setSliderValue(clamp(meanPressure, p1Min, p1Max));
        persist({ SwitchState: 1, P1: text });
      } else {
        const text = String(sliderValue);
        setP1Text(text);
        persist({ SwitchState: 0, P1: text });
      }
    },
    [meanPressure, p1Max, p1Min, persist, sliderValue],
  );

  const commitP1 = useCallback(
    (raw: string) => {
      const text = getEntryValue(raw);
      if (!validateScientificNotation(text)) {
        setP1Text(text);
        toast.error({ title: "P1", message: "Please enter a valid number." });
        return;
      }
      const value = Number(text);
      if (engine && !withinRange(value, p1Min, p1Max)) {
        setP1Text(text);
        toast.error({
          title: "P1 fuera de rango",
          message: `The value must be between ${p1Min} and ${p1Max}.`,
        });
        return;
      }
      setP1Text(text);
      setSliderValue(value);
      persist({ P1: text });
    },
    [p1Max, p1Min, persist, toast],
  );

  /* ------------------------------ render ------------------------------ */

  const typeOptions = useMemo(() => Object.keys(plugins ?? {}), [plugins]);
  const activePlugin = plugins?.[nozzleType];
  const specInputs = useMemo(() => {
    if (!activePlugin) return [];
    return Object.entries(activePlugin.labels).map(([label, key]) => ({ label, key }));
  }, [activePlugin]);

  return (
    <div
      className={cx("or-nozzle", className)}
      data-module="nozzle"
      style={{ display: "grid", gap: 12, alignContent: "start", minHeight: "100%", padding: 12 }}
    >
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))",
          gap: 12,
          alignItems: "start",
        }}
      >
        <Card title="Inputs">
          <div style={{ display: "grid", gap: 10 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <Button
                variant="primary"
                onClick={() => void handleLoadEngine()}
                loading={loadingEngine}
              >
                Load engine
              </Button>
              <span
                data-testid="nozzle-engine-label"
                title={engineLabel}
                style={{
                  color: engineLabel === INVALID_ENGINE_LABEL ? "var(--danger)" : "var(--text-muted)",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {engineLabel}
              </span>
            </div>

            <Checkbox
              checked={meanSwitch}
              onChange={handleMeanToggle}
              disabled={!engine}
              label="P1 - Mean Value (Pa)"
            />
            <Slider
              label="P1 slider"
              value={sliderValue}
              min={p1Min}
              max={p1Max}
              step={Math.max((p1Max - p1Min) / 1000, 1)}
              onChange={handleP1Slider}
              format={(value) => `${formatPressure(value)} Pa`}
              disabled={!engine || meanSwitch}
            />
            <NumberField
              label="P1 - Design point (Pa)"
              value={p1Text}
              onChange={setP1Text}
              onBlur={(event) => commitP1(event.currentTarget.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") commitP1(event.currentTarget.value);
              }}
              disabled={meanSwitch}
              hint={
                engine
                  ? `Rango [${formatPressure(p1Min)}, ${formatPressure(p1Max)}] Pa`
                  : "Carga un motor para fijar el rango"
              }
            />

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
                gap: 10,
              }}
            >
              <NumberField
                label="Points - Resolution"
                value={nRes}
                onChange={(value) => {
                  setNRes(value);
                  persist({ n_res: value });
                }}
                min={2}
              />
              <NumberField
                label="Temp. Step (s)"
                value={dt}
                onChange={setDt}
                hint="0 = sin normalización"
              />
            </div>

            <Select
              label="Nozzle type"
              value={nozzleType}
              options={typeOptions}
              onChange={handleTypeChange}
              placeholder={typeOptions.length === 0 ? "Sin tipos disponibles" : undefined}
              disabled={typeOptions.length === 0}
            />

            {specInputs.length > 0 ? (
              <div
                data-testid="nozzle-spec-inputs"
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
                  gap: 10,
                }}
              >
                {specInputs.map(({ label, key }) => {
                  const configKey = specConfigKey(nozzleType, key);
                  return (
                    <NumberField
                      key={configKey}
                      label={label}
                      value={specValues[configKey] ?? ""}
                      onChange={(value) => handleSpecChange(key, value)}
                      normalizeCommas
                      placeholder="0"
                    />
                  );
                })}
              </div>
            ) : null}

            <div style={{ display: "flex", gap: 8 }}>
              <Button variant="primary" onClick={() => void handleCalculate()}>
                CALCULATE
              </Button>
              <Button onClick={openExport} disabled={!result}>
                EXPORT
              </Button>
            </div>
          </div>
        </Card>

        <Card
          title="Pressure profile (Pa)"
          actions={
            <span style={{ color: "var(--text-muted)" }}>
              P1/Pmax ={" "}
              {p1Max > 0 ? (p1Value / p1Max).toFixed(3) : "—"}
            </span>
          }
        >
          {engine ? (
            <LineChart
              option={profileOption}
              height={300}
              ariaLabel="Perfil de presión con P1 marcado"
            />
          ) : (
            <p style={{ color: "var(--text-muted)" }}>
              Carga un motor para ver el perfil de presión.
            </p>
          )}
        </Card>
      </div>

      <Card
        title="Results"
        actions={
          <Tabs
            items={[
              { id: "nozzle", label: "NOZZLE RESULTS" },
              { id: "performance", label: "PERFORMANCE AND OPERATION" },
            ]}
            value={resultsTab}
            onChange={setResultsTab}
            ariaLabel="Resultados de tobera"
          />
        }
      >
        {!result && resultsTab === "nozzle" ? (
          <p style={{ color: "var(--text-muted)" }}>
            Sin resultados: pulsa CALCULATE con un motor cargado.
          </p>
        ) : resultsTab === "nozzle" && result ? (
          <div style={{ display: "grid", gap: 12 }}>
            <ResultsPanel result={result} />
            <FiguresPanel figures={result.figures ?? {}} />
          </div>
        ) : (
          <OffDesignPanel
            op={op}
            error={opError}
            p1tPercent={p1tPercent}
            p0Percent={p0Percent}
            p1t={p1tValue}
            p0={p0Value}
            p1tMin={p1tMin}
            p1tMax={p1tMax}
            disabled={!engine || !specValid}
            prCrit={prCrit}
            machOption={machOption}
            presOption={presOption}
            onP1tChange={setP1tPercent}
            onP0Change={setP0Percent}
          />
        )}
      </Card>

      <Card title="Data">
        <NozzleTables
          timeResults={result?.timeResults_data ?? null}
          geometry={result?.geometry_data ?? null}
        />
      </Card>

      <ProgressDialog
        open={progress.open}
        title="Calculando tobera…"
        label={`${nozzleType} · ${progress.label}`}
        value={progress.value}
        requestId={progress.requestId}
        onCancel={handleCancelCompute}
        onClose={handleCancelCompute}
        closable={false}
      />

      <Modal
        open={exportOpen}
        onClose={() => setExportOpen(false)}
        title="Exportar tobera"
        width={460}
        footer={
          <>
            <Button variant="ghost" onClick={() => setExportOpen(false)} disabled={saving}>
              Cancelar
            </Button>
            <Button variant="primary" onClick={() => void handleExport()} loading={saving}>
              Guardar
            </Button>
          </>
        }
      >
        <div style={{ display: "grid", gap: 10 }}>
          <TextField
            label="Nombre del fichero"
            value={exportName}
            onChange={setExportName}
            hint="Se guardará en Nozzles/<nombre>.json (se añade .json si falta)"
          />
          <span style={{ color: "var(--text-muted)" }}>
            Config del motor: {engineLabel} · Tipo: {nozzleType || "—"}
          </span>
        </div>
      </Modal>
    </div>
  );
}

export default NozzleTab;
