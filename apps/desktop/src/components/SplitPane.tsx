import { useCallback, useRef, useState, type PointerEvent as ReactPointerEvent, type ReactNode } from "react";
import { cx } from "../utils/cx";

export interface SplitPaneProps {
  /** `horizontal` reparte en columnas; `vertical` en filas. */
  direction?: "horizontal" | "vertical";
  /** Tamaño inicial del primer panel (px). */
  initialSize?: number;
  minSize?: number;
  /** Tamaño del divider en px. */
  dividerSize?: number;
  children: [ReactNode, ReactNode];
  className?: string;
}

/** Panel dividido con divisor arrastrable (sin dependencias). */
export function SplitPane({
  direction = "horizontal",
  initialSize = 320,
  minSize = 120,
  dividerSize = 6,
  children,
  className,
}: SplitPaneProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState(initialSize);
  const [dragging, setDragging] = useState(false);

  const onPointerDown = useCallback((event: ReactPointerEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.currentTarget.setPointerCapture(event.pointerId);
    setDragging(true);
  }, []);

  const onPointerMove = useCallback(
    (event: ReactPointerEvent<HTMLDivElement>) => {
      if (!dragging) return;
      const container = containerRef.current;
      if (!container) return;
      const rect = container.getBoundingClientRect();
      const total = direction === "horizontal" ? rect.width : rect.height;
      const offset = direction === "horizontal" ? event.clientX - rect.left : event.clientY - rect.top;
      const next = Math.min(Math.max(offset, minSize), Math.max(minSize, total - minSize - dividerSize));
      setSize(next);
    },
    [dragging, direction, minSize, dividerSize],
  );

  const stopDragging = useCallback(() => setDragging(false), []);

  const firstStyle = direction === "horizontal"
    ? { width: size, flex: "0 0 auto" as const }
    : { height: size, flex: "0 0 auto" as const };

  return (
    <div
      ref={containerRef}
      className={cx("or-split", `or-split--${direction}`, dragging && "is-dragging", className)}
    >
      <div className="or-split__pane" style={firstStyle}>
        {children[0]}
      </div>
      <div
        className="or-split__divider"
        role="separator"
        aria-orientation={direction === "horizontal" ? "vertical" : "horizontal"}
        tabIndex={0}
        style={direction === "horizontal" ? { width: dividerSize } : { height: dividerSize }}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={stopDragging}
        onPointerCancel={stopDragging}
      />
      <div className="or-split__pane or-split__pane--grow">{children[1]}</div>
    </div>
  );
}
