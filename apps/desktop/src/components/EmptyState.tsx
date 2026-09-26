import type { ReactNode } from "react";
import { cx } from "../utils/cx";

export interface EmptyStateProps {
  title: ReactNode;
  description?: ReactNode;
  icon?: ReactNode;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({ title, description, icon, action, className }: EmptyStateProps) {
  return (
    <div className={cx("or-empty", className)}>
      {icon ? <div className="or-empty__icon">{icon}</div> : null}
      <div className="or-empty__title">{title}</div>
      {description ? <div className="or-empty__description">{description}</div> : null}
      {action ? <div className="or-empty__action">{action}</div> : null}
    </div>
  );
}
