import { cx } from "../utils/cx";

export interface SpinnerProps {
  /** Tamaño en píxeles (diámetro). */
  size?: number;
  /** Texto accesible. */
  label?: string;
  className?: string;
}

export function Spinner({ size = 16, label = "Cargando…", className }: SpinnerProps) {
  return (
    <span
      className={cx("or-spinner", className)}
      role="status"
      aria-label={label}
      style={{ width: size, height: size }}
    />
  );
}
