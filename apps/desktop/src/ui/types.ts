/**
 * Contrato de props de los módulos de pestaña.
 *
 * Los módulos completos (agentes A4-A8) reciben `active` para pausar
 * cálculos/plots cuando su pestaña no está visible, y pueden usar
 * `useWorkspace()` para `config`/`setTabConfig`.
 */
export interface TabModuleProps {
  /** `true` cuando la pestaña está visible. */
  active?: boolean;
  className?: string;
}
