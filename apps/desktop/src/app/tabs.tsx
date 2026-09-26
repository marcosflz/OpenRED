import type { ComponentType } from "react";
import { AdiabaticTab } from "../ui/adiabatic";
import { CadTab } from "../ui/cad";
import { EngineTab } from "../ui/engine";
import { NozzleTab } from "../ui/nozzle";
import { DocumentationTab, OpenFoamTab, PostProcessingTab } from "../ui/placeholders";
import { TestbedTab } from "../ui/testbed";
import type { TabModuleProps } from "../ui/types";

export type TabId =
  | "adiabatic"
  | "engine"
  | "nozzle"
  | "cad"
  | "testbed"
  | "documentation"
  | "openfoam"
  | "post";

export interface TabDefinition {
  id: TabId;
  /** Etiqueta visible en el sidebar (nombres de la app original). */
  label: string;
  Component: ComponentType<TabModuleProps>;
}

/** Los 8 módulos del shell, en el mismo orden que la app original. */
export const TABS: TabDefinition[] = [
  { id: "adiabatic", label: "Adiabatic Temp", Component: AdiabaticTab },
  { id: "engine", label: "Engine Design", Component: EngineTab },
  { id: "nozzle", label: "Nozzle Design", Component: NozzleTab },
  { id: "cad", label: "CAD Design", Component: CadTab },
  { id: "testbed", label: "Testing Bed", Component: TestbedTab },
  { id: "documentation", label: "Documentation", Component: DocumentationTab },
  { id: "openfoam", label: "OpenFOAM Maker", Component: OpenFoamTab },
  { id: "post", label: "Post-Processing", Component: PostProcessingTab },
];

export const DEFAULT_TAB: TabId = "adiabatic";
export const TAB_STORAGE_KEY = "openred.tab";

export function isTabId(value: string | null): value is TabId {
  return value !== null && TABS.some((tab) => tab.id === value);
}

export function readStoredTab(): TabId {
  try {
    const stored = window.localStorage.getItem(TAB_STORAGE_KEY);
    return isTabId(stored) ? stored : DEFAULT_TAB;
  } catch {
    return DEFAULT_TAB;
  }
}
