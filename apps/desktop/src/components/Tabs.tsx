import { useId, type ReactNode } from "react";
import { cx } from "../utils/cx";

export interface TabItem {
  id: string;
  label: ReactNode;
  disabled?: boolean;
  badge?: ReactNode;
}

export interface TabsProps {
  items: TabItem[];
  value: string;
  onChange: (id: string) => void;
  ariaLabel?: string;
  className?: string;
}

/** Sub-pestañas segmentadas (GEOMETRY / CONSOLE / REGRESSION, etc.). */
export function Tabs({ items, value, onChange, ariaLabel, className }: TabsProps) {
  const groupId = useId();

  return (
    <div className={cx("or-tabs", className)} role="tablist" aria-label={ariaLabel}>
      {items.map((item) => {
        const selected = item.id === value;
        return (
          <button
            key={item.id}
            id={`${groupId}-tab-${item.id}`}
            type="button"
            role="tab"
            aria-selected={selected}
            aria-controls={`${groupId}-panel-${item.id}`}
            tabIndex={selected ? 0 : -1}
            className={cx("or-tabs__tab", selected && "is-active")}
            disabled={item.disabled}
            onClick={() => onChange(item.id)}
          >
            <span className="or-tabs__label">{item.label}</span>
            {item.badge !== undefined ? <span className="or-tabs__badge">{item.badge}</span> : null}
          </button>
        );
      })}
    </div>
  );
}
