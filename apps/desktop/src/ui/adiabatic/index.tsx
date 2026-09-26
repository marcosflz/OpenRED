import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Button,
  Card,
  MathText,
  Modal,
  NumberField,
  Select,
  Table,
  TextField,
  useToast,
  type SelectOption,
  type TableColumn,
} from "../../components";
import {
  isCancel,
  request,
  toRpcError,
  type AdiabaticCalculateResult,
  type ComponentRow,
  type PropellantRow,
} from "../../api/engine";
import { useWorkspace } from "../../app/WorkspaceProvider";
import { getEntryValue, parseNumeric } from "../../utils/numbers";
import type { TabModuleProps } from "../types";
import { formatLegacyResult } from "./format";

export interface AdiabaticTabProps extends TabModuleProps {}

/** Fila editable de reactivo/producto: moles como texto + componente. */
interface SpeciesRow {
  key: number;
  moles: string;
  component: string;
}

/** Subconjunto de `tab_0` que este módulo persiste (valores string, G3). */
interface Tab0Patch {
  reactivos: Array<[string, string]>;
  productos: Array<[string, string]>;
  initial_temp: string;
  temp_Int_step: string;
  temp_guess: string;
  [key: string]: unknown;
}

/** Etiquetas y claves de los 7 resultados, en el orden del legacy (T0-3). */
const RESULT_FIELDS: Array<{ key: keyof AdiabaticCalculateResult; label: string }> = [
  { key: "tSol", label: "Solution Temperature (K):" },
  { key: "molWeight", label: "Molecular Weight of Product (kg/mol):" },
  { key: "cp", label: "Specific Heat at Constant Pressure (J/(kg*K)):" },
  { key: "cv", label: "Specific Heat at Constant Volume (J/(kg*K)):" },
  { key: "R", label: "Gas Constant of Product (J/(kg*K)):" },
  { key: "gamma", label: "Gamma (Cp/Cv):" },
  { key: "cChar", label: "Characteristic Velocity (m/s):" },
];

const DEFAULT_INITIAL_TEMP = "293";
const DEFAULT_INT_STEP = "1";
const DEFAULT_TEMP_GUESS = "1500";

const PROPELLANT_COLUMNS: Array<TableColumn<PropellantRow>> = [
  { key: "id", header: "ID", align: "center" },
  { key: "Propelente", header: "Propelente" },
  { key: "T_ad", header: "T_ad" },
  { key: "MolWeight", header: "MolWeight" },
  { key: "Cp", header: "Cp" },
  { key: "Cv", header: "Cv" },
  { key: "R", header: "R" },
  { key: "gamma", header: "gamma" },
  { key: "cChar", header: "cChar" },
  { key: "Density", header: "Density" },
  { key: "P1_min", header: "P1_min" },
  { key: "P1_max", header: "P1_max" },
  { key: "a", header: "a" },
  { key: "n", header: "n" },
];

interface SavePropellantDraft {
  name: string;
  density: string;
  p1min: string;
  p1max: string;
  a: string;
  n: string;
}

const EMPTY_DRAFT: SavePropellantDraft = {
  name: "",
  density: "",
  p1min: "",
  p1max: "",
  a: "",
  n: "",
};

function hasLetter(value: string): boolean {
  return /\p{L}/u.test(value);
}

function tabSignature(tab: {
  reactivos?: unknown;
  productos?: unknown;
  initial_temp?: unknown;
  temp_Int_step?: unknown;
  temp_guess?: unknown;
}): string {
  return JSON.stringify([
    tab.reactivos ?? null,
    tab.productos ?? null,
    tab.initial_temp ?? null,
    tab.temp_Int_step ?? null,
    tab.temp_guess ?? null,
  ]);
}

/** `f"{v} {latex}"` del legacy; el coeficiente es el texto tal cual se escribió. */
function reactionSide(rows: SpeciesRow[], latexByName: Map<string, string>): string {
  return rows
    .filter((row) => row.moles !== "" && row.component !== "")
    .map((row) => `${row.moles}\\,${latexByName.get(row.component) ?? row.component}`)
    .join(" + ");
}

/**
 * Pestaña T0 (temperatura adiabática): filas dinámicas de reactivos/productos,
 * reacción KaTeX con auto-ajuste, cálculo `adiabatic.calculate`, guardado de
 * propelentes (`adiabatic.save_propellant`) y tabla `db.propellants.list`
 * refrescada al recibir foco/hover (T0-1..T0-6, G3).
 */
export function AdiabaticTab({ active, className }: AdiabaticTabProps) {
  const toast = useToast();
  const { config, setTabConfig } = useWorkspace();
  const tab0 = config.tabs?.tab_0;

  const [components, setComponents] = useState<ComponentRow[]>([]);
  const [reactants, setReactants] = useState<SpeciesRow[]>([]);
  const [products, setProducts] = useState<SpeciesRow[]>([]);
  const [initialTemp, setInitialTemp] = useState(DEFAULT_INITIAL_TEMP);
  const [intStep, setIntStep] = useState(DEFAULT_INT_STEP);
  const [tempGuess, setTempGuess] = useState(DEFAULT_TEMP_GUESS);
  const [result, setResult] = useState<AdiabaticCalculateResult | null>(null);
  const [calculating, setCalculating] = useState(false);
  const [propellants, setPropellants] = useState<PropellantRow[]>([]);
  const [saveOpen, setSaveOpen] = useState(false);
  const [draft, setDraft] = useState<SavePropellantDraft>(EMPTY_DRAFT);

  const keyRef = useRef(0);
  const seededRef = useRef(false);
  const appliedRef = useRef<string | null>(null);
  const propellantsLoadingRef = useRef(false);

  const makeRow = useCallback((component: string): SpeciesRow => {
    keyRef.current += 1;
    return { key: keyRef.current, moles: "", component };
  }, []);

  /* ------------------------------------------------------------------ */
  /* Carga de datos                                                      */
  /* ------------------------------------------------------------------ */

  const loadComponents = useCallback(async () => {
    try {
      const response = await request<{ items: ComponentRow[] }>("db.components.list");
      setComponents(Array.isArray(response.items) ? response.items : []);
    } catch (error) {
      const rpc = toRpcError(error);
      if (!isCancel(rpc)) toast.error({ title: "Thermochemical Data", message: rpc.message });
    }
  }, [toast]);

  const loadPropellants = useCallback(async () => {
    if (propellantsLoadingRef.current) return;
    propellantsLoadingRef.current = true;
    try {
      const response = await request<{ items: PropellantRow[] }>("db.propellants.list");
      setPropellants(Array.isArray(response.items) ? response.items : []);
    } catch (error) {
      const rpc = toRpcError(error);
      if (!isCancel(rpc)) toast.error({ title: "Propellants Data", message: rpc.message });
    } finally {
      propellantsLoadingRef.current = false;
    }
  }, [toast]);

  useEffect(() => {
    if (active === false) return;
    void loadComponents();
  }, [active, loadComponents]);

  useEffect(() => {
    void loadPropellants();
  }, [loadPropellants]);

  /* ------------------------------------------------------------------ */
  /* Restauración / persistencia en config.json (G3)                     */
  /* ------------------------------------------------------------------ */

  const persist = useCallback(
    (next: {
      reactivos: SpeciesRow[];
      productos: SpeciesRow[];
      initialTemp: string;
      intStep: string;
      tempGuess: string;
    }) => {
      const payload: Tab0Patch = {
        reactivos: next.reactivos.map((row) => [getEntryValue(row.moles), row.component]),
        productos: next.productos.map((row) => [getEntryValue(row.moles), row.component]),
        initial_temp: getEntryValue(next.initialTemp),
        temp_Int_step: getEntryValue(next.intStep),
        temp_guess: getEntryValue(next.tempGuess),
      };
      appliedRef.current = tabSignature(payload);
      setTabConfig("tab_0", payload);
    },
    [setTabConfig],
  );

  useEffect(() => {
    if (!tab0) return;
    const signature = tabSignature(tab0);
    if (signature === appliedRef.current) return;
    appliedRef.current = signature;

    if (Array.isArray(tab0.reactivos)) {
      setReactants(
        tab0.reactivos.map(([moles, component]) => ({
          key: (keyRef.current += 1),
          moles: String(moles ?? ""),
          component: String(component ?? ""),
        })),
      );
    }
    if (Array.isArray(tab0.productos)) {
      setProducts(
        tab0.productos.map(([moles, component]) => ({
          key: (keyRef.current += 1),
          moles: String(moles ?? ""),
          component: String(component ?? ""),
        })),
      );
    }
    if (tab0.initial_temp !== undefined && tab0.initial_temp !== null) {
      setInitialTemp(String(tab0.initial_temp));
    }
    if (tab0.temp_Int_step !== undefined && tab0.temp_Int_step !== null) {
      setIntStep(String(tab0.temp_Int_step));
    }
    if (tab0.temp_guess !== undefined && tab0.temp_guess !== null) {
      setTempGuess(String(tab0.temp_guess));
    }
    seededRef.current = true;
  }, [tab0]);

  // Primera fila por defecto (una de reactivo y otra de producto) como el legacy.
  useEffect(() => {
    if (components.length === 0 || seededRef.current) return;
    seededRef.current = true;
    const first = components[0]?.Component ?? "";
    const reactantRow = makeRow(first);
    const productRow = makeRow(first);
    setReactants((rows) => (rows.length > 0 ? rows : [reactantRow]));
    setProducts((rows) => (rows.length > 0 ? rows : [productRow]));
  }, [components, makeRow]);

  /* ------------------------------------------------------------------ */
  /* Edición de filas/inputs                                             */
  /* ------------------------------------------------------------------ */

  const patchReactant = useCallback(
    (key: number, patch: Partial<SpeciesRow>) => {
      const next = reactants.map((row) => (row.key === key ? { ...row, ...patch } : row));
      setReactants(next);
      persist({ reactivos: next, productos: products, initialTemp, intStep, tempGuess });
    },
    [reactants, products, initialTemp, intStep, tempGuess, persist],
  );

  const patchProduct = useCallback(
    (key: number, patch: Partial<SpeciesRow>) => {
      const next = products.map((row) => (row.key === key ? { ...row, ...patch } : row));
      setProducts(next);
      persist({ reactivos: reactants, productos: next, initialTemp, intStep, tempGuess });
    },
    [reactants, products, initialTemp, intStep, tempGuess, persist],
  );

  const addReactant = useCallback(() => {
    const next = [...reactants, makeRow(components[0]?.Component ?? "")];
    setReactants(next);
    persist({ reactivos: next, productos: products, initialTemp, intStep, tempGuess });
  }, [reactants, products, components, initialTemp, intStep, tempGuess, makeRow, persist]);

  const removeReactant = useCallback(() => {
    const next = reactants.slice(0, -1);
    setReactants(next);
    persist({ reactivos: next, productos: products, initialTemp, intStep, tempGuess });
  }, [reactants, products, initialTemp, intStep, tempGuess, persist]);

  const addProduct = useCallback(() => {
    const next = [...products, makeRow(components[0]?.Component ?? "")];
    setProducts(next);
    persist({ reactivos: reactants, productos: next, initialTemp, intStep, tempGuess });
  }, [reactants, products, components, initialTemp, intStep, tempGuess, makeRow, persist]);

  const removeProduct = useCallback(() => {
    const next = products.slice(0, -1);
    setProducts(next);
    persist({ reactivos: reactants, productos: next, initialTemp, intStep, tempGuess });
  }, [reactants, products, initialTemp, intStep, tempGuess, persist]);

  const handleInitialTemp = useCallback(
    (value: string) => {
      setInitialTemp(value);
      persist({ reactivos: reactants, productos: products, initialTemp: value, intStep, tempGuess });
    },
    [reactants, products, intStep, tempGuess, persist],
  );

  const handleIntStep = useCallback(
    (value: string) => {
      setIntStep(value);
      persist({
        reactivos: reactants,
        productos: products,
        initialTemp,
        intStep: value,
        tempGuess,
      });
    },
    [reactants, products, initialTemp, tempGuess, persist],
  );

  const handleTempGuess = useCallback(
    (value: string) => {
      setTempGuess(value);
      persist({
        reactivos: reactants,
        productos: products,
        initialTemp,
        intStep,
        tempGuess: value,
      });
    },
    [reactants, products, initialTemp, intStep, persist],
  );

  /* ------------------------------------------------------------------ */
  /* Reacción (KaTeX) y opciones de componente                           */
  /* ------------------------------------------------------------------ */

  const latexByName = useMemo(() => {
    const map = new Map<string, string>();
    for (const item of components) {
      if (!map.has(item.Component)) {
        map.set(item.Component, item.latex?.trim() ? item.latex : item.Component);
      }
    }
    return map;
  }, [components]);

  const reactionLatex = useMemo(
    () =>
      `${reactionSide(reactants, latexByName)} \\longrightarrow ${reactionSide(
        products,
        latexByName,
      )}`,
    [reactants, products, latexByName],
  );

  // Auto-ajuste simple: reducción escalonada del tamaño según la longitud.
  const reactionFontSize =
    reactionLatex.length > 170 ? 13 : reactionLatex.length > 120 ? 16 : reactionLatex.length > 80 ? 20 : 24;

  const componentOptions = useCallback(
    (current: string): SelectOption[] => {
      const seen = new Set<string>();
      const options: SelectOption[] = [];
      for (const item of components) {
        if (seen.has(item.Component)) continue;
        seen.add(item.Component);
        options.push({ value: item.Component, label: item.Component });
      }
      if (current !== "" && !seen.has(current)) options.push({ value: current, label: current });
      return options;
    },
    [components],
  );

  /* ------------------------------------------------------------------ */
  /* Cálculo (T0-3/T0-4)                                                 */
  /* ------------------------------------------------------------------ */

  const handleCalculate = useCallback(async () => {
    setCalculating(true);
    try {
      const response = await request<AdiabaticCalculateResult>("adiabatic.calculate", {
        reac: reactants.map((row) => ({
          moles: parseNumeric(row.moles),
          component: row.component,
        })),
        prod: products.map((row) => ({
          moles: parseNumeric(row.moles),
          component: row.component,
        })),
        t0: parseNumeric(initialTemp),
        tGuess: parseNumeric(tempGuess),
        hStep: parseNumeric(intStep),
      });
      setResult(response);
    } catch (error) {
      const rpc = toRpcError(error);
      if (!isCancel(rpc)) toast.error({ title: "Adiabatic Temperature", message: rpc.message });
    } finally {
      setCalculating(false);
    }
  }, [reactants, products, initialTemp, tempGuess, intStep, toast]);

  /* ------------------------------------------------------------------ */
  /* Guardar propelente (T0-5)                                           */
  /* ------------------------------------------------------------------ */

  const setDraftField = useCallback((key: keyof SavePropellantDraft, value: string) => {
    setDraft((current) => ({ ...current, [key]: value }));
  }, []);

  const handleSavePropellant = useCallback(async () => {
    if (!result) return;
    const name = draft.name.trim();
    if (!hasLetter(name)) {
      toast.error({
        title: "Invalid Input",
        message: "The component must contain at least one letter.",
      });
      return;
    }
    try {
      const response = await request<{ items?: PropellantRow[] }>("adiabatic.save_propellant", {
        values: {
          Propelente: name,
          T_ad: result.tSol,
          MolWeight: result.molWeight,
          Cp: result.cp,
          Cv: result.cv,
          R: result.R,
          gamma: result.gamma,
          cChar: result.cChar,
          Density: parseNumeric(draft.density),
          P1_min: parseNumeric(draft.p1min),
          P1_max: parseNumeric(draft.p1max),
          a: parseNumeric(draft.a),
          n: parseNumeric(draft.n),
        },
      });
      if (Array.isArray(response.items)) setPropellants(response.items);
      else void loadPropellants();
      setSaveOpen(false);
      toast.success({ title: "Propellant saved", message: name });
    } catch (error) {
      const rpc = toRpcError(error);
      if (!isCancel(rpc)) toast.error({ title: "Save Propellant", message: rpc.message });
    }
  }, [result, draft, toast, loadPropellants]);

  /* ------------------------------------------------------------------ */
  /* Render                                                              */
  /* ------------------------------------------------------------------ */

  const renderSpeciesRows = (
    side: "Reactant" | "Product",
    rows: SpeciesRow[],
    onPatch: (key: number, patch: Partial<SpeciesRow>) => void,
    onAdd: () => void,
    onRemove: () => void,
  ) => (
    <Card title={`${side}s`}>
      <div style={{ display: "grid", gap: 8 }}>
        {rows.map((row, index) => (
          <div
            key={row.key}
            style={{
              display: "grid",
              gridTemplateColumns: "minmax(80px, 0.7fr) minmax(140px, 1.6fr)",
              gap: 8,
              alignItems: "end",
            }}
          >
            <NumberField
              value={row.moles}
              onChange={(value) => onPatch(row.key, { moles: value })}
              placeholder="0"
              aria-label={`${side} ${index + 1} moles`}
            />
            <Select
              value={row.component}
              options={componentOptions(row.component)}
              onChange={(value) => onPatch(row.key, { component: value })}
              aria-label={`${side} ${index + 1} component`}
            />
          </div>
        ))}
        <div style={{ display: "flex", gap: 8 }}>
          <Button onClick={onAdd}>Add {side}</Button>
          <Button variant="ghost" onClick={onRemove} disabled={rows.length === 0}>
            Remove {side}
          </Button>
        </div>
      </div>
    </Card>
  );

  return (
    <div className={className} data-module="adiabatic" style={{ display: "grid", gap: 12 }}>
      <Card title="Reaction">
        <div
          style={{
            fontSize: reactionFontSize,
            minHeight: 56,
            overflowX: "auto",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <MathText display text={reactionLatex} />
        </div>
      </Card>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(2, minmax(220px, 1fr)) minmax(300px, 1.35fr)",
          gap: 12,
          alignItems: "start",
        }}
      >
        {renderSpeciesRows("Reactant", reactants, patchReactant, addReactant, removeReactant)}
        {renderSpeciesRows("Product", products, patchProduct, addProduct, removeProduct)}

        <Card title="Results">
          <div style={{ display: "grid", gap: 8 }}>
            {RESULT_FIELDS.map((field) => (
              <NumberField
                key={field.key}
                label={field.label}
                value={result ? formatLegacyResult(result[field.key]) : ""}
                onChange={() => {}}
                readOnly
              />
            ))}
            <Button variant="primary" block onClick={() => setSaveOpen(true)} disabled={!result}>
              Save Propellant
            </Button>
          </div>
        </Card>
      </div>

      <Card title="Calculation">
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: 12,
            alignItems: "end",
          }}
        >
          <NumberField
            label="Inlet Temperature (K):"
            value={initialTemp}
            onChange={handleInitialTemp}
          />
          <NumberField label="Integration Step (K):" value={intStep} onChange={handleIntStep} />
          <NumberField
            label="Initial Temperature (K):"
            value={tempGuess}
            onChange={handleTempGuess}
          />
          <Button variant="primary" loading={calculating} onClick={() => void handleCalculate()}>
            Calculate
          </Button>
        </div>
      </Card>

      <Card title="Propellants" flush>
        <div
          onMouseEnter={() => void loadPropellants()}
          onFocusCapture={() => void loadPropellants()}
        >
          <Table
            columns={PROPELLANT_COLUMNS}
            rows={propellants}
            rowKey={(row) => row.id}
            emptyMessage="Sin propelentes guardados"
            height={280}
          />
        </div>
      </Card>

      <Modal
        open={saveOpen}
        onClose={() => setSaveOpen(false)}
        title="Save Propellant"
        width={620}
        footer={
          <>
            <Button variant="ghost" onClick={() => setSaveOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={() => void handleSavePropellant()}>
              Save
            </Button>
          </>
        }
      >
        <div style={{ display: "grid", gap: 10 }}>
          <TextField
            label="Propellant Name:"
            value={draft.name}
            onChange={(value) => setDraftField("name", value)}
          />
          <NumberField
            label="Propellant Density (kg/m^3):"
            value={draft.density}
            onChange={(value) => setDraftField("density", value)}
            normalizeCommas
          />
          <NumberField
            label="P1 (Min. - Pa):"
            value={draft.p1min}
            onChange={(value) => setDraftField("p1min", value)}
            normalizeCommas
          />
          <NumberField
            label="P1 (Max. - Pa):"
            value={draft.p1max}
            onChange={(value) => setDraftField("p1max", value)}
            normalizeCommas
          />
          <NumberField
            label="Coefficient a:"
            value={draft.a}
            onChange={(value) => setDraftField("a", value)}
            normalizeCommas
          />
          <NumberField
            label="Coefficient n:"
            value={draft.n}
            onChange={(value) => setDraftField("n", value)}
            normalizeCommas
          />
        </div>
      </Modal>
    </div>
  );
}

export default AdiabaticTab;
