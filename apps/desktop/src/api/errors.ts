/**
 * Errores del contrato JSON-RPC del motor (`contracts/methods.md` §2).
 *
 * - `RpcError` normaliza tanto los errores lanzados por Rust (objeto plano
 *   `{code, message, detail}`) como los `Error` nativos.
 * - El código 1005 (cancelado por el usuario) es silencioso por convención:
 *   usa `isCancel()` para no mostrar nada en la UI.
 */

export interface RpcErrorShape {
  code: number;
  message: string;
  detail: unknown;
}

/** Cancelado por el usuario (`request.cancel`). */
export const RPC_CANCELLED = 1005;

export class RpcError extends Error {
  readonly code: number;
  readonly detail: unknown;

  constructor(code: number, message: string, detail: unknown = null) {
    super(message);
    this.name = "RpcError";
    this.code = code;
    this.detail = detail;
  }
}

export function isRpcErrorShape(value: unknown): value is RpcErrorShape {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as { code?: unknown; message?: unknown };
  return typeof candidate.code === "number" && typeof candidate.message === "string";
}

/** Normaliza cualquier error a `RpcError`. */
export function toRpcError(error: unknown, fallbackCode = 2000): RpcError {
  if (error instanceof RpcError) return error;
  if (isRpcErrorShape(error)) return new RpcError(error.code, error.message, error.detail);
  if (error instanceof Error) {
    return new RpcError(fallbackCode, error.message, error.stack ?? null);
  }
  if (typeof error === "string") return new RpcError(fallbackCode, error, null);
  return new RpcError(fallbackCode, "Unknown error", error ?? null);
}

/** `true` si el error es una cancelación del usuario (código 1005). */
export function isCancel(error: unknown): boolean {
  if (error instanceof RpcError) return error.code === RPC_CANCELLED;
  if (isRpcErrorShape(error)) return error.code === RPC_CANCELLED;
  return false;
}
