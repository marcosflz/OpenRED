import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  isCancel,
  pickFile,
  pickSaveFile,
  request,
  toRpcError,
  type CadExportResult,
  type CadViews,
  type CadViewsResult,
  type FileFilter,
} from "../../api/engine";
import { onExportRequested } from "../../app/bus";
import { useWorkspace } from "../../app/WorkspaceProvider";
import {
  Button,
  Card,
  Checkbox,
  EmptyState,
  FigureView,
  Modal,
  NumberField,
  Select,
  Tabs,
  useToast,
} from "../../components";
import { cx } from "../../utils/cx";
import type { TabModuleProps } from "../types";
import {
  applyFields,
  AS_NOZZLE_MESSAGE,
  baseName,
  collectPatch,
  collectSettings,
  defaultExportName,
  EXPORT_LABELS,
  mergeFields,
  VIEW_DEBOUNCE_MS,
  type CadFieldDef,
  type CadLoadPayload,
  type ExportKind,
} from "./settings";

export interface CadTabProps extends TabModuleProps {}

type CadViewKey = keyof CadViews;

const VIEW_TABS: Array<{ id: CadViewKey; label: string }> = [
  { id: "engine", label: "Engine" },
  { id: "coverFront", label: "Cover Front" },
  { id: "nozzleFront", label: "Nozzle Front" },
  { id: "tools", label: "Tools" },
  { id: "toolMould", label: "Tool Mould" },
  { id: "toolMouldFix", label: "Tool Mould Fix" },
];

/**
 * `pick_file` de Rust recibe una lista de extensiones (`commands.rs`), si bien
 * el tipo `FileFilter[]` de `src/api/engine.ts` conserva la forma antigua.
 */
const JSON_EXTENSIONS = ["json"] as unknown as FileFilter[];

function viewLabel(view: CadViewKey): string {
  return VIEW_TABS.find((tab) => tab.id === view)?.label ?? "CAD view";
}

/**
 * Pestaña T3 (CAD para Fusion360): carga de toberas (`cad.load_nozzle`),
 * 6 vistas (`cad.views` con debounce de 150 ms) y export CSV (`cad.export`,
 * con confirmación de sobrescritura ante error 1004).
 */
export function CadTab({ active, className }: CadTabProps) {
  const toast = useToast();
  const { config, workdir, ready, loadConfig, setTabConfig } = useWorkspace();

  const [loading, setLoading] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [architecture, setArchitecture] = useState<string | null>(null);
  const [unsupportedMessage, setUnsupportedMessage] = useState(AS_NOZZLE_MESSAGE);
  const [nozzle, setNozzle] = useState<Record<string, unknown> | null>(null);
  const [fields, setFields] = useState<CadFieldDef[]>([]);
  const [values, setValues] = useState<Record<string, string>>({});
  const [checks, setChecks] = useState<Record<string, boolean>>({});
  const [view, setView] = useState<CadViewKey>("engine");
  const [views, setViews] = useState<CadViews | null>(null);
  const [viewsLoading, setViewsLoading] = useState(false);
  const [viewsError, setViewsError] = useState<string | null>(null);
  const [exporting, setExporting] = useState<ExportKind | null>(null);
  const [conflict, setConflict] = useState<{ kind: ExportKind; name: string; message: string } | null>(
    null,
  );

  const tab3 = useMemo<Record<string, unknown>>(() => {
    const raw = config.tabs?.tab_3;
    return raw !== null && typeof raw === "object" ? (raw as Record<string, unknown>) : {};
  }, [config]);
  const tab3Ref = useRef(tab3);
  tab3Ref.current = tab3;

  const persistedNozzle =
    typeof tab3.NozzleConfig === "string" && tab3.NozzleConfig.trim() !== ""
      ? tab3.NozzleConfig
      : null;

  const supported = architecture === "conventional" && nozzle !== null;

  const loadedFileRef = useRef<string | null>(null);
  const restoreRef = useRef(false);
  const attemptedRef = useRef<string | null>(null);
  const viewTokenRef = useRef(0);

  /** `cad.load_nozzle` + reconstrucción de los controles dinámicos. */
  const loadFile = useCallback(
    async (path: string) => {
      setLoading(true);
      try {
        const result = await request<CadLoadPayload>("cad.load_nozzle", { path });
        const architectureValue = result.architecture === "as-nozzle" ? "as-nozzle" : "conventional";
        const merged = mergeFields(result.fields ?? [], result.checks ?? []);
        const initial = applyFields(merged, tab3Ref.current, result.suggested ?? {});
        const name = baseName(path);
        loadedFileRef.current = name;
        setFileName(name);
        setArchitecture(architectureValue);
        setUnsupportedMessage(result.message ?? AS_NOZZLE_MESSAGE);
        setNozzle(result.config ?? {});
        setFields(merged);
        setValues(initial.values);
        setChecks(initial.checks);
        setViews(null);
        setViewsError(null);
        setView("engine");
      } catch (error) {
        const rpc = toRpcError(error);
        if (!isCancel(rpc)) toast.error({ title: "No se pudo cargar la tobera", message: rpc.message });
      } finally {
        setLoading(false);
      }
    },
    [toast],
  );

  // Al montar: si el workspace aún no tiene `tab_3`, cárgalo de `config.json`.
  useEffect(() => {
    if (!ready || !workdir || restoreRef.current) return;
    restoreRef.current = true;
    if (!persistedNozzle) void loadConfig();
  }, [ready, workdir, persistedNozzle, loadConfig]);

  // Restaura `NozzleConfig` del workdir (una vez por nombre persistido).
  useEffect(() => {
    if (!persistedNozzle) return;
    if (loadedFileRef.current === persistedNozzle || attemptedRef.current === persistedNozzle) return;
    attemptedRef.current = persistedNozzle;
    void loadFile(persistedNozzle);
  }, [persistedNozzle, loadFile]);

  const patch = useMemo(() => {
    if (!fileName) return null;
    return supported ? collectPatch(fileName, values, checks) : { NozzleConfig: fileName };
  }, [fileName, supported, values, checks]);

  useEffect(() => {
    if (patch) setTabConfig("tab_3", patch);
  }, [patch, setTabConfig]);

  const settings = useMemo(() => collectSettings(values, checks), [values, checks]);

  const refreshViews = useCallback(
    async (configValue: Record<string, unknown>, settingsValue: Record<string, string | number>) => {
      const token = ++viewTokenRef.current;
      try {
        const result = await request<CadViewsResult>("cad.views", {
          config: configValue,
          settings: settingsValue,
          type: String(settingsValue.type ?? "Fitted"),
        });
        if (token !== viewTokenRef.current) return;
        setViews(result.views);
        setViewsError(null);
      } catch (error) {
        if (token !== viewTokenRef.current) return;
        const rpc = toRpcError(error);
        if (!isCancel(rpc)) setViewsError(rpc.message);
      } finally {
        if (token === viewTokenRef.current) setViewsLoading(false);
      }
    },
    [],
  );

  // Regenera las 6 vistas al cargar y ante cualquier cambio (debounce 150 ms).
  useEffect(() => {
    if (!supported || !nozzle) {
      setViewsLoading(false);
      return;
    }
    setViewsLoading(true);
    const timer = window.setTimeout(() => {
      void refreshViews(nozzle, settings);
    }, VIEW_DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [supported, nozzle, settings, refreshViews]);

  const handlePick = useCallback(async () => {
    try {
      const path = await pickFile(JSON_EXTENSIONS);
      if (!path) return;
      await loadFile(path);
    } catch (error) {
      const rpc = toRpcError(error);
      if (!isCancel(rpc)) toast.error({ title: "No se pudo abrir el diálogo", message: rpc.message });
    }
  }, [loadFile, toast]);

  const updateValue = useCallback((key: string, value: string) => {
    setValues((current) => ({ ...current, [key]: value }));
  }, []);

  const updateCheck = useCallback((key: string, checked: boolean) => {
    setChecks((current) => ({ ...current, [key]: checked }));
  }, []);

  const handleExport = useCallback(
    async (kind: ExportKind, options: { overwrite?: boolean; name?: string } = {}) => {
      if (!supported || !nozzle) {
        toast.warning({
          title: "Exportar CAD",
          message: "Carga primero una tobera convencional.",
        });
        return;
      }
      setExporting(kind);
      let name = options.name;
      try {
        if (!name) {
          const picked = await pickSaveFile(defaultExportName(fileName, kind));
          if (!picked) return; // diálogo cancelado
          name = baseName(picked);
        }
        if (!name.toLowerCase().endsWith(".csv")) name += ".csv";
        const result = await request<CadExportResult>("cad.export", {
          kind,
          config: nozzle,
          settings,
          name,
          ...(options.overwrite ? { overwrite: true } : {}),
        });
        setConflict(null);
        toast.success({
          title: `Sketch ${EXPORT_LABELS[kind]} exportado`,
          message: result.path ?? name,
        });
      } catch (error) {
        const rpc = toRpcError(error);
        if (isCancel(rpc)) return;
        if (rpc.code === 1004 && !options.overwrite) {
          const conflictName = options.name ?? name ?? defaultExportName(fileName, kind);
          setConflict({
            kind,
            name: conflictName,
            message: rpc.message || `El archivo ${conflictName} ya existe. ¿Quieres sobrescribirlo?`,
          });
          return;
        }
        toast.error({ title: "Error al exportar", message: rpc.message });
      } finally {
        setExporting(null);
      }
    },
    [supported, nozzle, settings, fileName, toast],
  );

  // `File > Export…` del menú: exporta el sketch del motor si la pestaña está activa.
  useEffect(() => {
    if (!active) return;
    return onExportRequested(() => {
      void handleExport("engine");
    });
  }, [active, handleExport]);

  const selectFields = useMemo(() => fields.filter((field) => field.type === "select"), [fields]);
  const numberFields = useMemo(() => fields.filter((field) => field.type === "number"), [fields]);
  const checkFields = useMemo(() => fields.filter((field) => field.type === "checkbox"), [fields]);

  return (
    <div className={cx("or-cad", className)} data-module="cad">
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(300px, 360px) minmax(0, 1fr)",
          gap: "var(--space-3)",
          alignItems: "start",
        }}
      >
        <div style={{ display: "grid", gap: "var(--space-3)" }}>
          <Card
            title="Nozzle file"
            actions={
              <Button variant="primary" size="sm" loading={loading} onClick={() => void handlePick()}>
                LOAD
              </Button>
            }
          >
            <span data-testid="cad-file-name">{fileName ?? "No file loaded"}</span>
          </Card>

          {architecture === "as-nozzle" ? (
            <Card title="Architecture">
              <p role="alert" data-testid="cad-unsupported" style={{ margin: 0 }}>
                {unsupportedMessage}
              </p>
            </Card>
          ) : null}

          {supported ? (
            <>
              <Card title="Entries">
                <div style={{ display: "grid", gap: "var(--space-2)" }}>
                  {selectFields.map((field) => (
                    <div key={field.key} data-field={field.key}>
                      <Select
                        label={field.label}
                        value={values[field.key] ?? ""}
                        options={field.options ?? ["Fitted", "Bulk"]}
                        onChange={(value) => updateValue(field.key, value)}
                      />
                    </div>
                  ))}
                  {numberFields.map((field) => (
                    <div key={field.key} data-field={field.key}>
                      <NumberField
                        label={field.label}
                        value={values[field.key] ?? ""}
                        onChange={(value) => updateValue(field.key, value)}
                      />
                    </div>
                  ))}
                </div>
              </Card>

              <Card title="Checkboxes">
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fill, minmax(210px, 1fr))",
                    gap: "var(--space-1) var(--space-2)",
                  }}
                >
                  {checkFields.map((field) => (
                    <div key={field.key} data-field={field.key}>
                      <Checkbox
                        label={field.label}
                        checked={checks[field.key] ?? false}
                        onChange={(checked) => updateCheck(field.key, checked)}
                      />
                    </div>
                  ))}
                </div>
              </Card>
            </>
          ) : null}

          <Card title="Export">
            <div style={{ display: "grid", gap: "var(--space-2)" }}>
              <Button
                block
                disabled={!supported}
                loading={exporting === "engine"}
                onClick={() => void handleExport("engine")}
              >
                EXPORT ENGINE
              </Button>
              <Button
                block
                disabled={!supported}
                loading={exporting === "cover"}
                onClick={() => void handleExport("cover")}
              >
                EXPORT COVER
              </Button>
              <Button
                block
                disabled={!supported}
                loading={exporting === "tools"}
                onClick={() => void handleExport("tools")}
              >
                EXPORT TOOLS
              </Button>
            </div>
          </Card>
        </div>

        <Card title="Views">
          {supported ? (
            <>
              <Tabs
                items={VIEW_TABS}
                value={view}
                onChange={(id) => setView(id as CadViewKey)}
                ariaLabel="CAD views"
              />
              <div data-testid="cad-view" data-view={view} style={{ marginTop: "var(--space-2)" }}>
                <FigureView
                  png={views ? views[view] : null}
                  alt={viewLabel(view)}
                  loading={viewsLoading}
                  error={viewsError}
                  height={520}
                />
              </div>
            </>
          ) : (
            <EmptyState
              title="CAD Design"
              description={
                architecture === "as-nozzle"
                  ? unsupportedMessage
                  : "Carga un fichero de tobera convencional (.json) para generar las vistas."
              }
            />
          )}
        </Card>
      </div>

      <Modal
        open={conflict !== null}
        onClose={() => setConflict(null)}
        title="Sobrescribir archivo"
        footer={
          <>
            <Button variant="secondary" onClick={() => setConflict(null)}>
              Cancelar
            </Button>
            <Button
              variant="danger"
              loading={exporting !== null}
              onClick={() => {
                if (conflict) void handleExport(conflict.kind, { overwrite: true, name: conflict.name });
              }}
            >
              Sobrescribir
            </Button>
          </>
        }
      >
        <p style={{ margin: 0 }}>{conflict?.message ?? ""}</p>
      </Modal>
    </div>
  );
}

export default CadTab;
