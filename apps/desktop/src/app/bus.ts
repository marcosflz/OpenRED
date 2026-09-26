/**
 * Bus mínimo de eventos de aplicación (ventana) para desacoplar el menú de
 * los módulos: `File > Export…` emite la petición y el módulo activo decide
 * si la atiende.
 */

export const EXPORT_REQUESTED_EVENT = "openred:export";

export function requestExport(): void {
  window.dispatchEvent(new CustomEvent(EXPORT_REQUESTED_EVENT));
}

/** Suscribe un handler a `Export…`; devuelve la función de baja. */
export function onExportRequested(handler: () => void): () => void {
  const listener = () => handler();
  window.addEventListener(EXPORT_REQUESTED_EVENT, listener);
  return () => window.removeEventListener(EXPORT_REQUESTED_EVENT, listener);
}
