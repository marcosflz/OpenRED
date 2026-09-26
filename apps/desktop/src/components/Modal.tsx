import { useEffect, useId, useRef, type KeyboardEvent as ReactKeyboardEvent, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { cx } from "../utils/cx";
import { IconButton } from "./IconButton";

export interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  /** Ancho del panel (px o CSS). */
  width?: number | string;
  closeOnOverlay?: boolean;
  closeOnEsc?: boolean;
  showCloseButton?: boolean;
  ariaLabel?: string;
  className?: string;
}

const FOCUSABLE_SELECTOR = [
  "button:not([disabled])",
  "[href]",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  '[tabindex]:not([tabindex="-1"])',
].join(", ");

/** Diálogo accesible: foco atrapado, cierre con ESC y overlay opcional. */
export function Modal({
  open,
  onClose,
  title,
  children,
  footer,
  width = 520,
  closeOnOverlay = true,
  closeOnEsc = true,
  showCloseButton = true,
  ariaLabel,
  className,
}: ModalProps) {
  const titleId = useId();
  const panelRef = useRef<HTMLDivElement>(null);
  const previousFocus = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!open) return;
    previousFocus.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const panel = panelRef.current;
    const first = panel?.querySelector<HTMLElement>(FOCUSABLE_SELECTOR);
    (first ?? panel)?.focus();
    return () => {
      previousFocus.current?.focus?.();
    };
  }, [open]);

  useEffect(() => {
    if (!open || !closeOnEsc) return;
    const onKeyDown = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") {
        event.stopPropagation();
        onClose();
      }
    };
    document.addEventListener("keydown", onKeyDown, true);
    return () => document.removeEventListener("keydown", onKeyDown, true);
  }, [open, closeOnEsc, onClose]);

  const trapFocus = (event: ReactKeyboardEvent<HTMLDivElement>) => {
    if (event.key !== "Tab") return;
    const panel = panelRef.current;
    if (!panel) return;
    const focusable = Array.from(panel.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)).filter(
      (node) => node.offsetParent !== null || node === document.activeElement,
    );
    if (focusable.length === 0) {
      event.preventDefault();
      panel.focus();
      return;
    }
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    const active = document.activeElement;
    if (event.shiftKey && (active === first || active === panel)) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && active === last) {
      event.preventDefault();
      first.focus();
    }
  };

  if (!open) return null;

  return createPortal(
    <div
      className="or-modal__overlay"
      onMouseDown={(event) => {
        if (closeOnOverlay && event.target === event.currentTarget) onClose();
      }}
    >
      <div
        ref={panelRef}
        className={cx("or-modal", className)}
        role="dialog"
        aria-modal="true"
        aria-label={title ? undefined : ariaLabel}
        aria-labelledby={title ? titleId : undefined}
        tabIndex={-1}
        style={{ width }}
        onKeyDown={trapFocus}
      >
        {(title || showCloseButton) && (
          <header className="or-modal__header">
            {title ? (
              <h2 id={titleId} className="or-modal__title">
                {title}
              </h2>
            ) : (
              <span />
            )}
            {showCloseButton ? (
              <IconButton label="Cerrar" onClick={onClose} className="or-modal__close">
                ✕
              </IconButton>
            ) : null}
          </header>
        )}
        <div className="or-modal__body">{children}</div>
        {footer ? <footer className="or-modal__footer">{footer}</footer> : null}
      </div>
    </div>,
    document.body,
  );
}
