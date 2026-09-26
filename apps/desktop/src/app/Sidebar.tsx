import type { ReactNode } from "react";
import { cx } from "../utils/cx";
import type { TabDefinition, TabId } from "./tabs";

export interface SidebarProps {
  items: TabDefinition[];
  active: TabId;
  onSelect: (id: TabId) => void;
  /** Pie del sidebar (estado del motor, directorio de trabajo, …). */
  footer?: ReactNode;
}

/** Sidebar de 220px con los 8 módulos; el activo se persiste en `openred.tab`. */
export function Sidebar({ items, active, onSelect, footer }: SidebarProps) {
  return (
    <aside className="or-sidebar" data-testid="sidebar">
      <nav className="or-sidebar__nav" aria-label="Modules" data-testid="module-nav">
        {items.map((item) => (
          <button
            key={item.id}
            type="button"
            data-testid={`nav-${item.id}`}
            className={cx("or-sidebar__item", active === item.id && "is-active")}
            aria-current={active === item.id ? "page" : undefined}
            onClick={() => onSelect(item.id)}
          >
            {item.label}
          </button>
        ))}
      </nav>
      {footer ? <div className="or-sidebar__footer">{footer}</div> : null}
    </aside>
  );
}
