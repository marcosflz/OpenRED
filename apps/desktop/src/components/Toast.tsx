import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { cx } from "../utils/cx";
import { IconButton } from "./IconButton";

export type ToastLevel = "info" | "success" | "warning" | "error";

export interface ToastOptions {
  title?: string;
  message: ReactNode;
  level?: ToastLevel;
  /** Duración en ms; 0 = no se autocierra. */
  duration?: number;
}

export interface ToastItem extends ToastOptions {
  id: string;
  level: ToastLevel;
  duration: number;
}

export interface ToastApi {
  show(options: ToastOptions | string): string;
  info(options: ToastOptions | string): string;
  success(options: ToastOptions | string): string;
  warning(options: ToastOptions | string): string;
  error(options: ToastOptions | string): string;
  dismiss(id: string): void;
  clear(): void;
}

const ToastContext = createContext<ToastApi | null>(null);

const DEFAULT_DURATION: Record<ToastLevel, number> = {
  info: 4000,
  success: 3500,
  warning: 6000,
  error: 8000,
};

const LEVEL_ICON: Record<ToastLevel, string> = {
  info: "ⓘ",
  success: "✓",
  warning: "⚠",
  error: "✕",
};

export interface ToastProviderProps {
  children: ReactNode;
  /** Máximo de toasts simultáneos. */
  max?: number;
}

export function ToastProvider({ children, max = 4 }: ToastProviderProps) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const counter = useRef(0);
  const timers = useRef(new Map<string, number>());

  const dismiss = useCallback((id: string) => {
    const timer = timers.current.get(id);
    if (timer !== undefined) {
      window.clearTimeout(timer);
      timers.current.delete(id);
    }
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const show = useCallback(
    (options: ToastOptions | string): string => {
      const normalized: ToastOptions = typeof options === "string" ? { message: options } : options;
      const level = normalized.level ?? "info";
      const id = `toast-${++counter.current}`;
      const item: ToastItem = {
        id,
        level,
        title: normalized.title,
        message: normalized.message,
        duration: normalized.duration ?? DEFAULT_DURATION[level],
      };
      setToasts((current) => [...current.slice(-(max - 1)), item]);
      if (item.duration > 0) {
        timers.current.set(
          id,
          window.setTimeout(() => dismiss(id), item.duration),
        );
      }
      return id;
    },
    [dismiss, max],
  );

  const clear = useCallback(() => {
    for (const timer of timers.current.values()) window.clearTimeout(timer);
    timers.current.clear();
    setToasts([]);
  }, []);

  useEffect(() => {
    const pending = timers.current;
    return () => {
      for (const timer of pending.values()) window.clearTimeout(timer);
      pending.clear();
    };
  }, []);

  const api = useMemo<ToastApi>(
    () => ({
      show,
      info: (options) => show({ ...normalize(options), level: "info" }),
      success: (options) => show({ ...normalize(options), level: "success" }),
      warning: (options) => show({ ...normalize(options), level: "warning" }),
      error: (options) => show({ ...normalize(options), level: "error" }),
      dismiss,
      clear,
    }),
    [show, dismiss, clear],
  );

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div className="or-toasts" aria-live="polite" aria-relevant="additions text">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={cx("or-toast", `or-toast--${toast.level}`)}
            role={toast.level === "error" ? "alert" : "status"}
          >
            <span className="or-toast__icon" aria-hidden="true">
              {LEVEL_ICON[toast.level]}
            </span>
            <div className="or-toast__content">
              {toast.title ? <div className="or-toast__title">{toast.title}</div> : null}
              <div className="or-toast__message">{toast.message}</div>
            </div>
            <IconButton label="Descartar" size="sm" onClick={() => dismiss(toast.id)}>
              ✕
            </IconButton>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

function normalize(options: ToastOptions | string): ToastOptions {
  return typeof options === "string" ? { message: options } : options;
}

/** API para lanzar toasts. Lanza si no hay `ToastProvider` por encima. */
export function useToast(): ToastApi {
  const context = useContext(ToastContext);
  if (!context) throw new Error("useToast debe usarse dentro de <ToastProvider>");
  return context;
}
