import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  appInfo as fetchAppInfo,
  isCancel,
  onEngineEvent,
  pickWorkdir,
  request,
  saveWorkdir,
  toRpcError,
  type AppInfo,
  type WorkspaceConfig,
  type WorkspaceGetResult,
  type WorkspaceLoadConfigResult,
  type WorkspaceSaveResult,
  type WorkspaceSetDirResult,
} from "../api/engine";
import { useToast } from "../components/Toast";

export const EMPTY_WORKSPACE_CONFIG: WorkspaceConfig = { tabs: {} };

export type TabPatch = Record<string, unknown>;

export interface WorkspaceContextValue {
  /** `app.info` del motor. */
  info: AppInfo | null;
  workdir: string | null;
  config: WorkspaceConfig;
  hasConfig: boolean;
  /** `true` cuando se ha intentado la carga inicial (aunque falle). */
  ready: boolean;
  /** Diálogo nativo + `workspace.set_dir` + `save_workdir`. */
  openWorkdir: () => Promise<WorkspaceSetDirResult | null>;
  /** `workspace.save_config {config, force:true}`. */
  saveConfig: () => Promise<string | null>;
  loadConfig: () => Promise<WorkspaceConfig | null>;
  refresh: () => Promise<void>;
  setConfig: (config: WorkspaceConfig) => void;
  /** Fusiona un patch en `config.tabs[tab]` (p. ej. `setTabConfig("tab_1", {P0:"..."})`). */
  setTabConfig: (tab: string, patch: TabPatch) => void;
}

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

function normalizeConfig(config: WorkspaceConfig | null | undefined): WorkspaceConfig {
  if (!config || typeof config !== "object") return EMPTY_WORKSPACE_CONFIG;
  const tabs = config.tabs && typeof config.tabs === "object" ? config.tabs : {};
  return { ...config, tabs };
}

export interface WorkspaceProviderProps {
  children: ReactNode;
}

/** Estado del directorio de trabajo y `config.json` (G2/G3/G11). */
export function WorkspaceProvider({ children }: WorkspaceProviderProps) {
  const toast = useToast();
  const [info, setInfo] = useState<AppInfo | null>(null);
  const [workdir, setWorkdir] = useState<string | null>(null);
  const [config, setConfigState] = useState<WorkspaceConfig>(EMPTY_WORKSPACE_CONFIG);
  const [hasConfig, setHasConfig] = useState(false);
  const [ready, setReady] = useState(false);

  /** Muestra los RpcError como toast; 1005 (cancelado) es silencioso. */
  const report = useCallback(
    (error: unknown, title: string) => {
      const rpc = toRpcError(error);
      if (isCancel(rpc)) return;
      toast.error({ title, message: rpc.message });
    },
    [toast],
  );

  const refresh = useCallback(async () => {
    try {
      const [appInfoResult, workspace] = await Promise.all([
        fetchAppInfo(),
        request<WorkspaceGetResult>("workspace.get"),
      ]);
      setInfo(appInfoResult);
      setWorkdir(workspace.workdir ?? null);
    } catch (error) {
      report(error, "No se pudo contactar con el motor");
    } finally {
      setReady(true);
    }
  }, [report]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    let unlisten: (() => void) | null = null;
    void onEngineEvent((event) => {
      if (event.name === "ready") void refresh();
      if (event.name === "log" && (event.level === "error" || event.level === "critical")) {
        toast.error({ title: "Motor", message: event.message });
      }
    }).then((fn) => {
      unlisten = fn;
    });
    return () => {
      unlisten?.();
    };
  }, [refresh, toast]);

  const openWorkdir = useCallback(async (): Promise<WorkspaceSetDirResult | null> => {
    try {
      const path = await pickWorkdir();
      if (!path) return null; // diálogo cancelado
      const result = await request<WorkspaceSetDirResult>("workspace.set_dir", { path });
      await saveWorkdir(path);
      setWorkdir(result.workdir ?? path);
      setHasConfig(result.hasConfig);
      if (result.config) setConfigState(normalizeConfig(result.config));
      return result;
    } catch (error) {
      report(error, "No se pudo abrir el directorio de trabajo");
      return null;
    }
  }, [report]);

  const saveConfig = useCallback(async (): Promise<string | null> => {
    try {
      const result = await request<WorkspaceSaveResult>("workspace.save_config", {
        config,
        force: true,
      });
      setHasConfig(true);
      return result.path;
    } catch (error) {
      report(error, "No se pudo guardar la configuración");
      return null;
    }
  }, [config, report]);

  const loadConfig = useCallback(async (): Promise<WorkspaceConfig | null> => {
    try {
      const result = await request<WorkspaceLoadConfigResult>("workspace.load_config");
      if (result.config) {
        setConfigState(normalizeConfig(result.config));
        setHasConfig(true);
      }
      return result.config;
    } catch (error) {
      report(error, "No se pudo cargar la configuración");
      return null;
    }
  }, [report]);

  const setConfig = useCallback((next: WorkspaceConfig) => {
    setConfigState(normalizeConfig(next));
  }, []);

  const setTabConfig = useCallback((tab: string, patch: TabPatch) => {
    setConfigState((current) => {
      const tabs = current.tabs ?? {};
      const previous = tabs[tab];
      const base =
        previous !== null && typeof previous === "object"
          ? (previous as Record<string, unknown>)
          : {};
      return { ...current, tabs: { ...tabs, [tab]: { ...base, ...patch } } };
    });
  }, []);

  const value = useMemo<WorkspaceContextValue>(
    () => ({
      info,
      workdir,
      config,
      hasConfig,
      ready,
      openWorkdir,
      saveConfig,
      loadConfig,
      refresh,
      setConfig,
      setTabConfig,
    }),
    [
      info,
      workdir,
      config,
      hasConfig,
      ready,
      openWorkdir,
      saveConfig,
      loadConfig,
      refresh,
      setConfig,
      setTabConfig,
    ],
  );

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

export function useWorkspace(): WorkspaceContextValue {
  const context = useContext(WorkspaceContext);
  if (!context) throw new Error("useWorkspace debe usarse dentro de <WorkspaceProvider>");
  return context;
}
