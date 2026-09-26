import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

/** Temas disponibles (paridad con `legacy/themes/*.json`). */
export type ThemeName = "red" | "orange";
/** Modos de apariencia (paridad con `ctk.set_appearance_mode`). */
export type ThemeMode = "dark" | "light";

export const THEME_STORAGE_KEY = "openred.theme";
export const MODE_STORAGE_KEY = "openred.mode";

export const THEME_NAMES: ThemeName[] = ["red", "orange"];

export const DEFAULT_THEME: ThemeName = "red";
export const DEFAULT_MODE: ThemeMode = "dark";

export interface ThemeContextValue {
  theme: ThemeName;
  mode: ThemeMode;
  setTheme: (theme: ThemeName) => void;
  setMode: (mode: ThemeMode) => void;
  toggleMode: () => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

function isThemeName(value: unknown): value is ThemeName {
  return value === "red" || value === "orange";
}

function isThemeMode(value: unknown): value is ThemeMode {
  return value === "dark" || value === "light";
}

/** Lee tema y modo persistidos; si no hay o son inválidos, usa red + dark. */
export function readStoredTheme(): { theme: ThemeName; mode: ThemeMode } {
  let theme: unknown = null;
  let mode: unknown = null;
  try {
    theme = window.localStorage.getItem(THEME_STORAGE_KEY);
    mode = window.localStorage.getItem(MODE_STORAGE_KEY);
  } catch {
    // localStorage no disponible (p. ej. pruebas con storage bloqueado)
  }
  return {
    theme: isThemeName(theme) ? theme : DEFAULT_THEME,
    mode: isThemeMode(mode) ? mode : DEFAULT_MODE,
  };
}

/** Aplica `data-theme`/`data-mode` en `<html>` (los tokens CSS reaccionan). */
export function applyThemeAttributes(theme: ThemeName, mode: ThemeMode): void {
  const root = document.documentElement;
  root.dataset.theme = theme;
  root.dataset.mode = mode;
}

function persist(theme: ThemeName, mode: ThemeMode): void {
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
    window.localStorage.setItem(MODE_STORAGE_KEY, mode);
  } catch {
    // Persistencia best-effort.
  }
}

export interface ThemeProviderProps {
  children: ReactNode;
  initialTheme?: ThemeName;
  initialMode?: ThemeMode;
}

export function ThemeProvider({ children, initialTheme, initialMode }: ThemeProviderProps) {
  const stored = useMemo(() => readStoredTheme(), []);
  const [theme, setThemeState] = useState<ThemeName>(initialTheme ?? stored.theme);
  const [mode, setModeState] = useState<ThemeMode>(initialMode ?? stored.mode);

  useEffect(() => {
    applyThemeAttributes(theme, mode);
    persist(theme, mode);
  }, [theme, mode]);

  const setTheme = useCallback((next: ThemeName) => setThemeState(next), []);
  const setMode = useCallback((next: ThemeMode) => setModeState(next), []);
  const toggleMode = useCallback(
    () => setModeState((current) => (current === "dark" ? "light" : "dark")),
    [],
  );

  const value = useMemo<ThemeContextValue>(
    () => ({ theme, mode, setTheme, setMode, toggleMode }),
    [theme, mode, setTheme, setMode, toggleMode],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

/** Acceso al tema activo. Lanza si no hay `ThemeProvider` por encima. */
export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme debe usarse dentro de <ThemeProvider>");
  }
  return context;
}

/** Variante tolerante para componentes que también viven fuera del provider. */
export function useOptionalTheme(): ThemeContextValue | null {
  return useContext(ThemeContext);
}
