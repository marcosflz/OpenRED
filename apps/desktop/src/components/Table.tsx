import { useState, type ReactNode } from "react";
import { cx } from "../utils/cx";

export interface TableColumn<T> {
  /** Clave de la propiedad a mostrar (o identificador si usas `render`). */
  key: string;
  header: ReactNode;
  width?: number | string;
  align?: "left" | "center" | "right";
  render?: (row: T, index: number) => ReactNode;
  className?: string;
}

export interface TableProps<T> {
  columns: Array<TableColumn<T>>;
  rows: T[];
  rowKey?: (row: T, index: number) => string | number;
  /** A partir de este número de filas solo se pintan las visibles. */
  virtualizeThreshold?: number;
  rowHeight?: number;
  /** Altura del viewport en px cuando se virtualiza. */
  height?: number;
  emptyMessage?: ReactNode;
  className?: string;
  onRowClick?: (row: T, index: number) => void;
  selectedKey?: string | number | null;
}

const DEFAULT_VIEWPORT = 320;

function defaultCell(row: unknown, key: string): ReactNode {
  if (typeof row !== "object" || row === null) return "";
  const value = (row as Record<string, unknown>)[key];
  if (value === null || value === undefined) return "";
  return String(value);
}

/**
 * Tabla compacta con virtualización simple (ventana de filas + espaciadores).
 * Suficiente para las tablas del original (miles de filas como máximo).
 */
export function Table<T>({
  columns,
  rows,
  rowKey,
  virtualizeThreshold = 200,
  rowHeight = 28,
  height = DEFAULT_VIEWPORT,
  emptyMessage = "Sin datos",
  className,
  onRowClick,
  selectedKey = null,
}: TableProps<T>) {
  const [scrollTop, setScrollTop] = useState(0);
  const total = rows.length;
  const virtualize = total > virtualizeThreshold;
  const start = virtualize ? Math.max(0, Math.floor(scrollTop / rowHeight) - 2) : 0;
  const visibleCount = virtualize ? Math.ceil(height / rowHeight) + 4 : total;
  const end = Math.min(total, start + visibleCount);
  const slice = virtualize ? rows.slice(start, end) : rows;
  const topPad = virtualize ? start * rowHeight : 0;
  const bottomPad = virtualize ? Math.max(0, (total - end) * rowHeight) : 0;

  return (
    <div
      className={cx("or-table-wrap", className)}
      style={virtualize ? { height } : undefined}
      onScroll={(event) => setScrollTop(event.currentTarget.scrollTop)}
    >
      <table className="or-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className={column.className}
                style={{ width: column.width, textAlign: column.align }}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {topPad > 0 ? (
            <tr className="or-table__spacer" aria-hidden="true" style={{ height: topPad }}>
              <td colSpan={columns.length} />
            </tr>
          ) : null}
          {slice.map((row, offset) => {
            const index = start + offset;
            const key = rowKey ? rowKey(row, index) : index;
            const selected = selectedKey !== null && selectedKey === key;
            return (
              <tr
                key={key}
                className={cx(
                  "or-table__row",
                  onRowClick && "or-table__row--clickable",
                  selected && "is-selected",
                )}
                onClick={onRowClick ? () => onRowClick(row, index) : undefined}
              >
                {columns.map((column) => (
                  <td
                    key={column.key}
                    className={column.className}
                    style={{ textAlign: column.align }}
                  >
                    {column.render ? column.render(row, index) : defaultCell(row, column.key)}
                  </td>
                ))}
              </tr>
            );
          })}
          {bottomPad > 0 ? (
            <tr className="or-table__spacer" aria-hidden="true" style={{ height: bottomPad }}>
              <td colSpan={columns.length} />
            </tr>
          ) : null}
        </tbody>
      </table>
      {total === 0 ? <div className="or-table__empty">{emptyMessage}</div> : null}
    </div>
  );
}
