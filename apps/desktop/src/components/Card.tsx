import type { HTMLAttributes, ReactNode } from "react";
import { cx } from "../utils/cx";

export interface CardProps extends Omit<HTMLAttributes<HTMLDivElement>, "title"> {
  title?: ReactNode;
  /** Acciones alineadas a la derecha del encabezado. */
  actions?: ReactNode;
  /** Sin padding interno (p. ej. contenedores de tablas). */
  flush?: boolean;
}

export function Card({ title, actions, flush = false, className, children, ...rest }: CardProps) {
  return (
    <section className={cx("or-card", flush && "or-card--flush", className)} {...rest}>
      {title || actions ? (
        <header className="or-card__header">
          {title ? <h3 className="or-card__title">{title}</h3> : <span />}
          {actions ? <div className="or-card__actions">{actions}</div> : null}
        </header>
      ) : null}
      <div className="or-card__body">{children}</div>
    </section>
  );
}
