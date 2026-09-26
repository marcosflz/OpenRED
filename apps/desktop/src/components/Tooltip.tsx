import { useId, useState, type ReactNode } from "react";
import { cx } from "../utils/cx";

export type TooltipPlacement = "top" | "bottom" | "left" | "right";

export interface TooltipProps {
  content: ReactNode;
  children: ReactNode;
  placement?: TooltipPlacement;
  /** Retardo en ms antes de mostrarlo (0 = inmediato). */
  delay?: number;
  className?: string;
}

export function Tooltip({ content, children, placement = "top", delay = 250, className }: TooltipProps) {
  const id = useId();
  const [open, setOpen] = useState(false);
  const [timer, setTimer] = useState<number | null>(null);

  const show = () => {
    if (delay <= 0) {
      setOpen(true);
      return;
    }
    const handle = window.setTimeout(() => setOpen(true), delay);
    setTimer(handle);
  };

  const hide = () => {
    if (timer !== null) {
      window.clearTimeout(timer);
      setTimer(null);
    }
    setOpen(false);
  };

  return (
    <span
      className={cx("or-tooltip", className)}
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
      onKeyDown={(event) => {
        if (event.key === "Escape") hide();
      }}
      aria-describedby={open ? id : undefined}
    >
      {children}
      {open ? (
        <span id={id} role="tooltip" className={cx("or-tooltip__bubble", `or-tooltip__bubble--${placement}`)}>
          {content}
        </span>
      ) : null}
    </span>
  );
}
