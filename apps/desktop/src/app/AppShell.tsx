import { useCallback, useEffect, useState } from "react";
import { isCancel, exitApp, openLogsFolder, toRpcError } from "../api/engine";
import { ToastProvider, useToast } from "../components/Toast";
import { ThemeProvider } from "../theme";
import { ComponentsWindow, PropellantsWindow } from "../ui/db-windows";
import { AboutDialog } from "./AboutDialog";
import { requestExport } from "./bus";
import { MenuBar } from "./MenuBar";
import { Sidebar } from "./Sidebar";
import { StatusBar } from "./StatusBar";
import { readStoredTab, TAB_STORAGE_KEY, TABS, type TabId } from "./tabs";
import { useWorkspace, WorkspaceProvider } from "./WorkspaceProvider";

/**
 * Raíz del shell: proveedores (tema, toasts, workspace) + layout navegable.
 * Se monta desde `src/main.tsx`.
 */
export function AppShell() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <WorkspaceProvider>
          <Shell />
        </WorkspaceProvider>
      </ToastProvider>
    </ThemeProvider>
  );
}

function Shell() {
  const toast = useToast();
  const { openWorkdir, saveConfig } = useWorkspace();
  const [active, setActive] = useState<TabId>(() => readStoredTab());
  const [componentsOpen, setComponentsOpen] = useState(false);
  const [propellantsOpen, setPropellantsOpen] = useState(false);
  const [aboutOpen, setAboutOpen] = useState(false);

  useEffect(() => {
    try {
      window.localStorage.setItem(TAB_STORAGE_KEY, active);
    } catch {
      // Persistencia best-effort.
    }
  }, [active]);

  // Manejo global de errores RPC no capturados (1005 silencioso).
  useEffect(() => {
    const onUnhandled = (event: PromiseRejectionEvent) => {
      const rpc = toRpcError(event.reason);
      if (isCancel(rpc)) {
        event.preventDefault();
        return;
      }
      toast.error({ title: "Error del motor", message: rpc.message });
    };
    window.addEventListener("unhandledrejection", onUnhandled);
    return () => window.removeEventListener("unhandledrejection", onUnhandled);
  }, [toast]);

  const handleOpenWorkdir = useCallback(async () => {
    const result = await openWorkdir();
    if (result) {
      toast.success({ title: "Directorio de trabajo", message: result.workdir });
    }
  }, [openWorkdir, toast]);

  const handleSaveConfig = useCallback(async () => {
    const path = await saveConfig();
    if (path) toast.success({ title: "Configuración guardada", message: path });
  }, [saveConfig, toast]);

  const handleExport = useCallback(() => {
    requestExport();
    toast.info({ message: "Solicitud de export enviada al módulo activo." });
  }, [toast]);

  const handleOpenLogs = useCallback(() => {
    openLogsFolder().catch((error: unknown) => {
      const rpc = toRpcError(error);
      if (!isCancel(rpc)) toast.error({ title: "Logs", message: rpc.message });
    });
  }, [toast]);

  const handleExit = useCallback(() => {
    void exitApp();
  }, []);

  const activeTab = TABS.find((tab) => tab.id === active) ?? TABS[0];
  const ActiveComponent = activeTab.Component;

  return (
    <div className="or-shell" data-testid="app-shell">
      <MenuBar
        onOpenWorkdir={() => void handleOpenWorkdir()}
        onSaveConfig={() => void handleSaveConfig()}
        onExport={handleExport}
        onOpenComponents={() => setComponentsOpen(true)}
        onOpenPropellants={() => setPropellantsOpen(true)}
        onOpenLogs={handleOpenLogs}
        onAbout={() => setAboutOpen(true)}
        onExit={handleExit}
      />
      <div className="or-shell__body">
        <Sidebar items={TABS} active={active} onSelect={setActive} footer={<StatusBar />} />
        <main className="or-shell__content" data-testid="module-content">
          <ActiveComponent active />
        </main>
      </div>
      <ComponentsWindow open={componentsOpen} onClose={() => setComponentsOpen(false)} />
      <PropellantsWindow open={propellantsOpen} onClose={() => setPropellantsOpen(false)} />
      <AboutDialog open={aboutOpen} onClose={() => setAboutOpen(false)} />
    </div>
  );
}
