import { useCallback, useState, type ReactNode } from "react";
import { isCancel, request } from "../api/engine";
import { Button } from "./Button";
import { Modal } from "./Modal";
import { ProgressBar } from "./ProgressBar";

export interface ProgressDialogProps {
  open: boolean;
  title?: string;
  label?: ReactNode;
  /** Progreso 0..1. */
  value?: number;
  indeterminate?: boolean;
  /**
   * Id de la petición en curso (`id` de la request JSON-RPC). Si se indica,
   * el botón Cancel llama a `request.cancel {id}` antes de notificar.
   */
  requestId?: string | number | null;
  onCancel?: () => void;
  onClose?: () => void;
  cancelLabel?: string;
  /** Permite cerrar con ESC/overlay (el botón Cancel sigue disponible). */
  closable?: boolean;
}

/**
 * Diálogo de progreso cancelable, equivalente a
 * `front_nozDes.create_progress_window` + `on_progress_window_close`.
 */
export function ProgressDialog({
  open,
  title = "Procesando…",
  label,
  value = 0,
  indeterminate = false,
  requestId = null,
  onCancel,
  onClose,
  cancelLabel = "Cancel",
  closable = true,
}: ProgressDialogProps) {
  const [cancelling, setCancelling] = useState(false);

  const handleCancel = useCallback(async () => {
    setCancelling(true);
    try {
      if (requestId !== null && requestId !== undefined) {
        try {
          await request("request.cancel", { id: requestId });
        } catch (error) {
          if (!isCancel(error)) {
            // El cálculo ya pudo terminar; la cancelación es best-effort.
          }
        }
      }
    } finally {
      setCancelling(false);
      onCancel?.();
      onClose?.();
    }
  }, [requestId, onCancel, onClose]);

  return (
    <Modal
      open={open}
      onClose={() => onClose?.()}
      title={title}
      width={460}
      closeOnEsc={closable}
      closeOnOverlay={false}
      showCloseButton={false}
      footer={
        <Button
          variant="secondary"
          onClick={() => void handleCancel()}
          disabled={cancelling}
          loading={cancelling}
        >
          {cancelLabel}
        </Button>
      }
    >
      <ProgressBar value={value} indeterminate={indeterminate} label={label} showPercent={!indeterminate} />
    </Modal>
  );
}
