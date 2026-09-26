import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { cx } from "../utils/cx";
import { IconButton } from "./IconButton";

export interface ConsoleLine {
  text: string;
  level?: "info" | "warn" | "error";
}

export type ConsoleLineInput = string | ConsoleLine;

export interface ConsoleProps {
  lines: ConsoleLineInput[];
  title?: string;
  /** Autoscroll al final mientras el usuario no suba manualmente. */
  autoScroll?: boolean;
  searchable?: boolean;
  onClear?: () => void;
  height?: number | string;
  className?: string;
  emptyMessage?: string;
}

function normalizeLine(line: ConsoleLineInput): ConsoleLine {
  return typeof line === "string" ? { text: line } : line;
}

function highlight(text: string, query: string): ReactNode {
  if (!query) return text;
  const index = text.toLowerCase().indexOf(query.toLowerCase());
  if (index < 0) return text;
  return (
    <>
      {text.slice(0, index)}
      <mark className="or-console__mark">{text.slice(index, index + query.length)}</mark>
      {text.slice(index + query.length)}
    </>
  );
}

/** Consola de log con autoscroll, búsqueda y resaltado (paridad con las consolas Tk). */
export function Console({
  lines,
  title,
  autoScroll = true,
  searchable = true,
  onClear,
  height = 260,
  className,
  emptyMessage = "Sin salida",
}: ConsoleProps) {
  const [query, setQuery] = useState("");
  const scrollerRef = useRef<HTMLDivElement>(null);
  const stickRef = useRef(true);

  const normalized = useMemo(() => lines.map(normalizeLine), [lines]);
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return normalized;
    return normalized.filter((line) => line.text.toLowerCase().includes(needle));
  }, [normalized, query]);

  useEffect(() => {
    const element = scrollerRef.current;
    if (element && autoScroll && stickRef.current) {
      element.scrollTop = element.scrollHeight;
    }
  }, [filtered, autoScroll]);

  const handleScroll = () => {
    const element = scrollerRef.current;
    if (!element) return;
    stickRef.current = element.scrollHeight - element.scrollTop - element.clientHeight < 24;
  };

  return (
    <div className={cx("or-console", className)}>
      {title || searchable || onClear ? (
        <div className="or-console__header">
          {title ? <span className="or-console__title">{title}</span> : <span />}
          <div className="or-console__tools">
            {searchable ? (
              <input
                className="or-input or-console__search"
                type="search"
                value={query}
                placeholder="Buscar…"
                aria-label="Buscar en la consola"
                onChange={(event) => setQuery(event.currentTarget.value)}
              />
            ) : null}
            {onClear ? (
              <IconButton label="Limpiar consola" size="sm" onClick={onClear}>
                ⌫
              </IconButton>
            ) : null}
          </div>
        </div>
      ) : null}
      <div
        ref={scrollerRef}
        className="or-console__body"
        style={{ height }}
        onScroll={handleScroll}
        tabIndex={0}
        role="log"
        aria-label={title ?? "Consola"}
      >
        {filtered.length === 0 ? (
          <div className="or-console__empty">{normalized.length === 0 ? emptyMessage : "Sin coincidencias"}</div>
        ) : (
          filtered.map((line, index) => (
            <div key={index} className={cx("or-console__line", line.level && `is-${line.level}`)}>
              {highlight(line.text, query.trim())}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
