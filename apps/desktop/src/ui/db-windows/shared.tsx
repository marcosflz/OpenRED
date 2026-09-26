import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  Button,
  Card,
  Modal,
  NumberField,
  Select,
  Table,
  TextField,
  useToast,
  type TableColumn,
} from "../../components";
import { isCancel, request, toRpcError } from "../../api/engine";
import { getEntryValue, normalizeNumericInput } from "../../utils/numbers";

/** Registro genérico de `termoquimica`/`propelente` (siempre con `id`). */
export type DbRecord = { id: number } & Record<string, unknown>;

/** Props comunes de las ventanas CRUD de base de datos. */
export interface DbWindowProps {
  open: boolean;
  onClose: () => void;
}

/** Campo numérico editable de una ventana DB. */
export interface DbField {
  key: string;
  label: string;
}

/** Contexto que recibe la acción extra (p. ej. curva de quemado). */
export interface CrudContext {
  selected: DbRecord | null;
  selectedName: string;
  items: DbRecord[];
  reload: () => Promise<void>;
}

export interface DbCrudModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  width?: number;
  /** Prefijo RPC: `db.components` | `db.propellants`. */
  namespace: string;
  /** Clave de la columna de nombre (`Component` | `Propelente`). */
  nameKey: string;
  /** Etiqueta visible del nombre (`Component` | `Propellant`). */
  nameLabel: string;
  /** Campos numéricos (sin `id` ni nombre). */
  fields: DbField[];
  /** Columnas de la tabla (incluye `id` y el nombre). */
  columns: Array<TableColumn<DbRecord>>;
  /** Mensaje exacto del legacy al sustituir una coma por un punto. */
  commaMessage: string;
  /** Contenido extra bajo los campos (botones específicos de la ventana). */
  extraActions?: (context: CrudContext) => ReactNode;
  /** Deshabilita el cierre con ESC (p. ej. mientras hay un modal encima). */
  closeOnEsc?: boolean;
}

/** `validate_component` del legacy: al menos una letra. */
export function hasLetter(value: string): boolean {
  return /\p{L}/u.test(value);
}

/** `tkinter` mostraba el valor crudo (`str(row)`); las celdas quedan igual. */
export function formatDbCell(value: unknown): string {
  if (value === null || value === undefined) return "";
  return String(value);
}

function signatureOf(record: DbRecord, nameKey: string, fields: DbField[]): Record<string, string> {
  const values: Record<string, string> = { [nameKey]: formatDbCell(record[nameKey]) };
  for (const field of fields) values[field.key] = formatDbCell(record[field.key]);
  return values;
}

/**
 * CRUD compartido de las ventanas Database (D-1..D-4): combobox `Nombre (id)`
 * que rellena los campos, validación científica con reemplazo coma→punto y
 * recarga completa de items tras cada operación (IDs reasignados por el motor).
 */
export function DbCrudModal({
  open,
  onClose,
  title,
  width = 1100,
  namespace,
  nameKey,
  nameLabel,
  fields,
  columns,
  commaMessage,
  extraActions,
  closeOnEsc = true,
}: DbCrudModalProps) {
  const toast = useToast();
  const [items, setItems] = useState<DbRecord[]>([]);
  const [cleanNames, setCleanNames] = useState<Record<string, string>>({});
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);

  const blankValues = useMemo(() => {
    const values: Record<string, string> = { [nameKey]: "" };
    for (const field of fields) values[field.key] = "";
    return values;
  }, [fields, nameKey]);

  const [values, setValues] = useState<Record<string, string>>(blankValues);

  const loadCleanNames = useCallback(
    async (records: DbRecord[]) => {
      const unique = Array.from(
        new Set(records.map((record) => formatDbCell(record[nameKey])).filter((name) => name !== "")),
      );
      const pairs = await Promise.all(
        unique.map(async (name) => {
          try {
            const response = await request<{ clean: string }>("db.clean_name", { name });
            return [name, response.clean] as const;
          } catch {
            return [name, name] as const;
          }
        }),
      );
      setCleanNames(Object.fromEntries(pairs));
    },
    [nameKey],
  );

  const reload = useCallback(async () => {
    try {
      const response = await request<{ items?: DbRecord[] }>(`${namespace}.list`);
      const next = Array.isArray(response.items) ? response.items : [];
      setItems(next);
      void loadCleanNames(next);
      setSelectedId((current) =>
        current !== null && next.some((record) => record.id === current) ? current : null,
      );
    } catch (error) {
      const rpc = toRpcError(error);
      if (!isCancel(rpc)) toast.error({ title, message: rpc.message });
    }
  }, [namespace, title, toast, loadCleanNames]);

  useEffect(() => {
    if (!open) return;
    setSelectedId(null);
    setValues(blankValues);
    void reload();
  }, [open, reload, blankValues]);

  const handleSelect = useCallback(
    (raw: string) => {
      const id = Number(raw);
      const record = items.find((item) => item.id === id) ?? null;
      if (!record) {
        setSelectedId(null);
        setValues(blankValues);
        return;
      }
      setSelectedId(id);
      setValues(signatureOf(record, nameKey, fields));
    },
    [items, nameKey, fields, blankValues],
  );

  const handleSelectChange = useCallback((id: number) => {
    setSelectedId(id);
    const record = items.find((item) => item.id === id) ?? null;
    if (record) setValues(signatureOf(record, nameKey, fields));
  }, [items, nameKey, fields]);

  const handleNumericChange = useCallback(
    (key: string, raw: string) => {
      if (raw.includes(",")) {
        toast.warning({ title: "Number Format", message: commaMessage });
        setValues((current) => ({ ...current, [key]: normalizeNumericInput(raw) }));
        return;
      }
      setValues((current) => ({ ...current, [key]: raw }));
    },
    [commaMessage, toast],
  );

  /** Nombre limpio (`db.clean_name`) + valores con `get_entry_value` (vacío→"0"). */
  const buildPayload = useCallback(async (): Promise<Record<string, string> | null> => {
    const rawName = values[nameKey] ?? "";
    if (!hasLetter(rawName)) {
      toast.error({
        title: "Invalid Input",
        message: "The component must contain at least one letter.",
      });
      return null;
    }
    let cleanName = rawName.trim();
    try {
      const response = await request<{ clean: string }>("db.clean_name", { name: cleanName });
      cleanName = response.clean;
    } catch {
      // Sin motor disponible se conserva el nombre tal cual.
    }
    const payload: Record<string, string> = { [nameKey]: cleanName };
    for (const field of fields) {
      payload[field.key] = normalizeNumericInput(getEntryValue(values[field.key] ?? ""));
    }
    return payload;
  }, [values, nameKey, fields, toast]);

  const handleAdd = useCallback(async () => {
    const payload = await buildPayload();
    if (!payload) return;
    setBusy(true);
    try {
      const response = await request<{ items?: DbRecord[] }>(`${namespace}.add`, {
        values: payload,
      });
      const next = Array.isArray(response.items) ? response.items : [];
      setItems(next);
      void loadCleanNames(next);
      setSelectedId(null);
      toast.success({ title, message: `${nameLabel} added` });
    } catch (error) {
      const rpc = toRpcError(error);
      if (!isCancel(rpc)) toast.error({ title, message: rpc.message });
    } finally {
      setBusy(false);
    }
  }, [buildPayload, namespace, nameLabel, title, toast, loadCleanNames]);

  const handleEdit = useCallback(async () => {
    if (selectedId === null) {
      toast.error({ title: "Invalid Operation", message: "Select a component to edit." });
      return;
    }
    const payload = await buildPayload();
    if (!payload) return;
    setBusy(true);
    try {
      const response = await request<{ items?: DbRecord[] }>(`${namespace}.edit`, {
        id: selectedId,
        values: payload,
      });
      const next = Array.isArray(response.items) ? response.items : [];
      setItems(next);
      void loadCleanNames(next);
      const updated = next.find((record) => record.id === selectedId) ?? null;
      setValues(updated ? signatureOf(updated, nameKey, fields) : blankValues);
      toast.success({ title, message: `${nameLabel} updated` });
    } catch (error) {
      const rpc = toRpcError(error);
      if (!isCancel(rpc)) toast.error({ title, message: rpc.message });
    } finally {
      setBusy(false);
    }
  }, [selectedId, buildPayload, namespace, nameKey, fields, blankValues, nameLabel, title, toast, loadCleanNames]);

  const handleDelete = useCallback(async () => {
    if (selectedId === null) {
      toast.warning({ title: "Invalid Operation", message: "Select a record to delete." });
      return;
    }
    setBusy(true);
    try {
      const response = await request<{ items?: DbRecord[] }>(`${namespace}.delete`, {
        id: selectedId,
      });
      const next = Array.isArray(response.items) ? response.items : [];
      setItems(next);
      void loadCleanNames(next);
      setSelectedId(null);
      setValues(blankValues);
      toast.success({ title, message: `${nameLabel} deleted` });
    } catch (error) {
      const rpc = toRpcError(error);
      if (!isCancel(rpc)) toast.error({ title, message: rpc.message });
    } finally {
      setBusy(false);
    }
  }, [selectedId, namespace, blankValues, nameLabel, title, toast, loadCleanNames]);

  const options = useMemo(
    () =>
      items.map((record) => {
        const name = formatDbCell(record[nameKey]);
        return { value: String(record.id), label: `${cleanNames[name] ?? name} (${record.id})` };
      }),
    [items, nameKey, cleanNames],
  );

  const selected = selectedId === null ? null : items.find((record) => record.id === selectedId) ?? null;
  const selectedName = selected ? cleanNames[formatDbCell(selected[nameKey])] ?? formatDbCell(selected[nameKey]) : "";

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      width={width}
      closeOnEsc={closeOnEsc}
      footer={
        <>
          <Button variant="ghost" onClick={() => void reload()}>
            Refresh
          </Button>
          <Button onClick={() => void handleAdd()} loading={busy}>
            Add
          </Button>
          <Button onClick={() => void handleEdit()} loading={busy}>
            Edit
          </Button>
          <Button variant="danger" onClick={() => void handleDelete()} loading={busy}>
            Delete
          </Button>
        </>
      }
    >
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(300px, 360px) minmax(0, 1fr)",
          gap: 12,
          alignItems: "start",
        }}
      >
        <Card title={`${nameLabel} Data`}>
          <div style={{ display: "grid", gap: 10, maxHeight: "58vh", overflowY: "auto", paddingRight: 4 }}>
            <Select
              label={`${nameLabel} (id)`}
              value={selectedId === null ? "" : String(selectedId)}
              options={options}
              onChange={handleSelect}
              placeholder="—"
            />
            <TextField
              label={nameLabel}
              value={values[nameKey] ?? ""}
              onChange={(value) => setValues((current) => ({ ...current, [nameKey]: value }))}
            />
            {fields.map((field) => (
              <NumberField
                key={field.key}
                label={field.label}
                value={values[field.key] ?? ""}
                onChange={(value) => handleNumericChange(field.key, value)}
                normalizeCommas
              />
            ))}
            {extraActions?.({ selected, selectedName, items, reload })}
          </div>
        </Card>
        <Card title={title} flush>
          <Table
            columns={columns}
            rows={items}
            rowKey={(record) => record.id}
            onRowClick={(record) => handleSelectChange(record.id)}
            selectedKey={selectedId}
            emptyMessage="Sin registros"
            height={430}
          />
        </Card>
      </div>
    </Modal>
  );
}
