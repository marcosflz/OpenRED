/**
 * Globales de entorno. `__TAURI_INTERNALS__` solo existe cuando la app corre
 * dentro del webview de Tauri; su ausencia activa el backend de mocks
 * (`src/api/mock.ts`) para `npm run dev` y los tests de vitest.
 */
declare global {
  interface Window {
    __TAURI_INTERNALS__?: unknown;
  }
}

export {};
