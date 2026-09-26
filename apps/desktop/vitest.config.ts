import { defineConfig } from "vitest/config";

/**
 * Configuración de tests (jsdom + Testing Library).
 *
 * Nota: no se usa `@vitejs/plugin-react` porque vitest 2 instala su propio
 * Vite 5 anidado; esbuild transforma JSX con `jsx: "automatic"`.
 */
export default defineConfig({
  esbuild: { jsx: "automatic" },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
    css: true,
    restoreMocks: true,
  },
});
