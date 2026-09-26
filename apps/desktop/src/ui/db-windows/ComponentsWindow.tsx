import type { TableColumn } from "../../components";
import { DbCrudModal, type DbField, type DbRecord, type DbWindowProps } from "./shared";

/** Campos numéricos de `termoquimica` (17 columnas sin id, en orden de esquema). */
const COMPONENT_FIELDS: DbField[] = [
  { key: "MolWeight", label: "MolWeight" },
  { key: "Hf0", label: "Hf0 (298K)" },
  { key: "minColdTemp", label: "minColdTemp" },
  { key: "maxColdTemp", label: "maxColdTemp" },
  { key: "minHotTemp", label: "minHotTemp" },
  { key: "maxHotTemp", label: "maxHotTemp" },
  { key: "a1_cold", label: "a1_cold" },
  { key: "a2_cold", label: "a2_cold" },
  { key: "a3_cold", label: "a3_cold" },
  { key: "a4_cold", label: "a4_cold" },
  { key: "a5_cold", label: "a5_cold" },
  { key: "a1_hot", label: "a1_hot" },
  { key: "a2_hot", label: "a2_hot" },
  { key: "a3_hot", label: "a3_hot" },
  { key: "a4_hot", label: "a4_hot" },
  { key: "a5_hot", label: "a5_hot" },
];

/** Cabeceras de `front_chemWin.columnTags`. */
export const COMPONENT_COLUMNS: Array<TableColumn<DbRecord>> = [
  { key: "id", header: "ID", align: "center" },
  { key: "Component", header: "Component" },
  ...COMPONENT_FIELDS.map((field) => ({ key: field.key, header: field.label })),
];

/** Ventana `Database > Thermochemical Data` (tabla `termoquimica`, D-1/D-3/D-4). */
export function ComponentsWindow({ open, onClose }: DbWindowProps) {
  return (
    <DbCrudModal
      open={open}
      onClose={onClose}
      title="Thermochemical Data"
      namespace="db.components"
      nameKey="Component"
      nameLabel="Component"
      fields={COMPONENT_FIELDS}
      columns={COMPONENT_COLUMNS}
      commaMessage="The comma has been replaced with a period to maintain numerical format."
    />
  );
}
